"""
Text extraction with robust timeout using multiprocessing.

This module wraps PaddleOCR with process-based timeout to prevent hanging.
"""

import time
import multiprocessing as mp
from pathlib import Path
from typing import Dict, Any, Optional
import cv2

from .text_extractor import OCRConfig, TextRegion


def _run_ocr_in_process(image_path: str, config_dict: dict, result_queue: mp.Queue):
    """
    Run OCR in a separate process.

    This function will be executed in a child process and can be forcefully
    terminated if it hangs.
    """
    try:
        from paddleocr import PaddleOCR

        # Initialize OCR with config
        ocr = PaddleOCR(
            lang=config_dict['lang'],
            use_angle_cls=False,
            use_textline_orientation=False,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            text_det_thresh=config_dict['text_det_thresh'],
            text_det_box_thresh=config_dict['text_det_box_thresh'],
            text_recognition_batch_size=config_dict['text_recognition_batch_size'],
            show_log=False,
            use_gpu=False,
        )

        # Perform OCR
        result = ocr.ocr(image_path)

        # Put result in queue
        result_queue.put(('success', result))

    except Exception as e:
        result_queue.put(('error', str(e)))


class OCRExtractorWithTimeout:
    """PaddleOCR text extractor with robust timeout using multiprocessing."""

    def __init__(self, config: Optional[OCRConfig] = None, timeout: int = 60):
        """
        Initialize OCR extractor with timeout.

        Args:
            config: OCR configuration
            timeout: Timeout in seconds (default: 60)
        """
        self.config = config or OCRConfig()
        self.timeout = timeout

    def extract(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Extract text from image with timeout protection.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with extraction results or error
        """
        start_time = time.time()

        # Validate image file
        image_path = Path(image_path)
        if not image_path.exists():
            return {
                "success": False,
                "text": "",
                "text_regions": [],
                "confidence_score": 0.0,
                "processing_time_ms": 0,
                "num_regions": 0,
                "has_text": False,
                "error": f"Image file not found: {image_path}"
            }

        # Load image to verify it's valid
        image = cv2.imread(str(image_path))
        if image is None:
            return {
                "success": False,
                "text": "",
                "text_regions": [],
                "confidence_score": 0.0,
                "processing_time_ms": 0,
                "num_regions": 0,
                "has_text": False,
                "error": f"Failed to load image: {image_path}"
            }

        # Prepare config dict for subprocess
        config_dict = {
            'lang': self.config.lang,
            'text_det_thresh': self.config.text_det_thresh,
            'text_det_box_thresh': self.config.text_det_box_thresh,
            'text_recognition_batch_size': self.config.text_recognition_batch_size,
        }

        # Create queue for result
        result_queue = mp.Queue()

        # Start OCR in separate process
        process = mp.Process(
            target=_run_ocr_in_process,
            args=(str(image_path), config_dict, result_queue)
        )

        process.start()

        # Wait for result with timeout
        process.join(timeout=self.timeout)

        # Check if process is still alive (hung)
        if process.is_alive():
            # Process is still running - forcefully terminate it
            process.terminate()
            process.join(timeout=5)  # Give it 5 seconds to terminate gracefully

            if process.is_alive():
                # Still alive - kill it
                process.kill()
                process.join()

            return {
                "success": False,
                "text": "",
                "text_regions": [],
                "confidence_score": 0.0,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "num_regions": 0,
                "has_text": False,
                "error": f"OCR operation timed out after {self.timeout} seconds"
            }

        # Process completed - get result
        if not result_queue.empty():
            status, data = result_queue.get()

            if status == 'error':
                return {
                    "success": False,
                    "text": "",
                    "text_regions": [],
                    "confidence_score": 0.0,
                    "processing_time_ms": int((time.time() - start_time) * 1000),
                    "num_regions": 0,
                    "has_text": False,
                    "error": f"OCR error: {data}"
                }

            # Parse OCR result
            result = data
            text_regions = []
            all_text = []

            if result and result[0]:
                first_result = result[0]

                # Handle different result formats
                if isinstance(first_result, dict) and 'rec_texts' in first_result:
                    # New format
                    rec_texts = first_result.get('rec_texts', [])
                    rec_scores = first_result.get('rec_scores', [])
                    rec_polys = first_result.get('rec_polys', [])

                    for i in range(len(rec_texts)):
                        try:
                            text = rec_texts[i]
                            confidence = rec_scores[i] if i < len(rec_scores) else 0.0
                            bbox = rec_polys[i] if i < len(rec_polys) else []

                            if not text or not isinstance(text, str):
                                continue

                            if len(bbox) > 0:
                                bbox_int = [[int(x), int(y)] for x, y in bbox]
                            else:
                                bbox_int = [[0, 0], [100, 0], [100, 20], [0, 20]]

                            text_regions.append(TextRegion(bbox_int, text, confidence))
                            all_text.append(text)
                        except (IndexError, TypeError, ValueError):
                            continue
                else:
                    # Old format
                    for line in first_result:
                        try:
                            if not isinstance(line, (list, tuple)) or len(line) < 2:
                                continue

                            bbox = line[0]
                            text_data = line[1]

                            if isinstance(text_data, (list, tuple)) and len(text_data) >= 2:
                                text = str(text_data[0])
                                confidence = float(text_data[1])
                            else:
                                text = str(text_data)
                                confidence = 0.0

                            if not text:
                                continue

                            bbox_int = [[int(x), int(y)] for x, y in bbox]
                            text_regions.append(TextRegion(bbox_int, text, confidence))
                            all_text.append(text)
                        except (IndexError, TypeError, ValueError):
                            continue

            # Calculate average confidence
            if text_regions:
                avg_confidence = sum(r.confidence for r in text_regions) / len(text_regions)
            else:
                avg_confidence = 0.0

            processing_time_ms = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "text": "\n".join(all_text),
                "text_regions": text_regions,
                "confidence_score": avg_confidence,
                "processing_time_ms": processing_time_ms,
                "num_regions": len(text_regions),
                "has_text": len(text_regions) > 0
            }
        else:
            return {
                "success": False,
                "text": "",
                "text_regions": [],
                "confidence_score": 0.0,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "num_regions": 0,
                "has_text": False,
                "error": "OCR process completed but returned no result"
            }


def extract_text(
    image_path: str | Path,
    config: Optional[OCRConfig] = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Extract text from image with timeout (convenience function).

    Args:
        image_path: Path to image file
        config: OCR configuration
        timeout: Timeout in seconds

    Returns:
        Dictionary with extraction results
    """
    extractor = OCRExtractorWithTimeout(config=config, timeout=timeout)
    return extractor.extract(image_path)
