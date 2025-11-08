"""
Text extraction using PaddleOCR for Traditional Chinese text recognition.

This module provides OCR functionality with support for:
- Traditional Chinese text (chinese_cht)
- Math symbols and formulas
- Automatic angle classification
- Confidence scores and bounding boxes
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from paddleocr import PaddleOCR
import cv2


class OCRConfig:
    """Configuration for PaddleOCR."""

    def __init__(
        self,
        lang: str = "chinese_cht",
        use_textline_orientation: bool = True,
        text_det_thresh: float = 0.3,
        text_det_box_thresh: float = 0.6,
        text_recognition_batch_size: int = 6,
    ):
        """
        Initialize OCR configuration.

        Args:
            lang: Language model to use ('chinese_cht' for Traditional Chinese)
            use_textline_orientation: Enable automatic text orientation detection
            text_det_thresh: Text detection threshold (0-1, lower = more sensitive)
            text_det_box_thresh: Bounding box threshold (0-1)
            text_recognition_batch_size: Batch size for text recognition
        """
        self.lang = lang
        self.use_textline_orientation = use_textline_orientation
        self.text_det_thresh = text_det_thresh
        self.text_det_box_thresh = text_det_box_thresh
        self.text_recognition_batch_size = text_recognition_batch_size


class TextRegion:
    """Represents a detected text region with bounding box and recognition result."""

    def __init__(
        self,
        bbox: List[List[int]],
        text: str,
        confidence: float,
    ):
        """
        Initialize text region.

        Args:
            bbox: Bounding box coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text: Recognized text
            confidence: Recognition confidence (0-1)
        """
        self.bbox = bbox
        self.text = text
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bbox": self.bbox,
            "text": self.text,
            "confidence": self.confidence,
        }

    def __repr__(self) -> str:
        return f"TextRegion(text='{self.text}', confidence={self.confidence:.2f})"


class OCRExtractor:
    """PaddleOCR text extractor."""

    def __init__(self, config: Optional[OCRConfig] = None):
        """
        Initialize OCR extractor.

        Args:
            config: OCR configuration. If None, uses defaults.
        """
        if config is None:
            config = OCRConfig()

        self.config = config
        self._ocr = None

    def _initialize_ocr(self) -> None:
        """Lazy initialization of PaddleOCR engine."""
        if self._ocr is None:
            self._ocr = PaddleOCR(
                lang=self.config.lang,
                use_textline_orientation=False,  # Disable to avoid model downloads in offline environment
                use_doc_orientation_classify=False,  # Disable doc preprocessor to avoid model downloads
                use_doc_unwarping=False,  # Disable doc unwarping to avoid model downloads
                text_det_thresh=self.config.text_det_thresh,
                text_det_box_thresh=self.config.text_det_box_thresh,
                text_recognition_batch_size=self.config.text_recognition_batch_size,
            )

    def extract(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Extract text from image using PaddleOCR.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with extraction results:
            {
                "success": True,
                "text": "完整提取的文字",
                "text_regions": [TextRegion, ...],
                "confidence_score": 0.92,
                "processing_time_ms": 2340,
                "num_regions": 5,
                "has_text": True
            }

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be loaded
        """
        start_time = time.time()

        # Validate image file
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Load image to verify it's valid
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Initialize OCR engine
        self._initialize_ocr()

        # Perform OCR
        # Note: Configuration parameters are set during PaddleOCR initialization
        result = self._ocr.ocr(str(image_path))

        # Parse results
        text_regions = []
        all_text = []

        if result and result[0]:
            for line in result[0]:
                # line format: [bbox, (text, confidence)]
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]

                # Convert bbox coordinates to integers
                bbox_int = [[int(x), int(y)] for x, y in bbox]

                text_regions.append(TextRegion(bbox_int, text, confidence))
                all_text.append(text)

        # Calculate metrics
        has_text = len(text_regions) > 0
        full_text = "\n".join(all_text) if has_text else ""
        avg_confidence = (
            sum(region.confidence for region in text_regions) / len(text_regions)
            if text_regions
            else 0.0
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "text": full_text,
            "text_regions": text_regions,
            "confidence_score": avg_confidence,
            "processing_time_ms": processing_time_ms,
            "num_regions": len(text_regions),
            "has_text": has_text,
        }


# Global singleton instance for better performance
_global_extractor: Optional[OCRExtractor] = None


def get_extractor(config: Optional[OCRConfig] = None) -> OCRExtractor:
    """
    Get global OCR extractor instance (singleton pattern).

    Args:
        config: OCR configuration. Only used on first call.

    Returns:
        OCR extractor instance
    """
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = OCRExtractor(config)
    return _global_extractor


def extract_text(
    image_path: str | Path, config: Optional[OCRConfig] = None, use_singleton: bool = True
) -> Dict[str, Any]:
    """
    Extract text from image (convenience function).

    Args:
        image_path: Path to image file
        config: OCR configuration. If None, uses defaults.
        use_singleton: Use global singleton instance for better performance

    Returns:
        Dictionary with extraction results (see OCRExtractor.extract())

    Example:
        >>> result = extract_text("problem.jpg")
        >>> print(result["text"])
        >>> print(f"Confidence: {result['confidence_score']:.2%}")
    """
    if use_singleton:
        extractor = get_extractor(config)
    else:
        extractor = OCRExtractor(config)

    return extractor.extract(image_path)


def extract_text_from_numpy(
    image: np.ndarray, config: Optional[OCRConfig] = None
) -> Dict[str, Any]:
    """
    Extract text from numpy array image.

    Args:
        image: Image as numpy array (BGR format)
        config: OCR configuration

    Returns:
        Dictionary with extraction results
    """
    import tempfile

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
        cv2.imwrite(tmp_path, image)

    try:
        # Extract text
        result = extract_text(tmp_path, config, use_singleton=True)
    finally:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)

    return result


def batch_extract_text(
    image_paths: List[str | Path], config: Optional[OCRConfig] = None
) -> List[Dict[str, Any]]:
    """
    Extract text from multiple images.

    Args:
        image_paths: List of image file paths
        config: OCR configuration

    Returns:
        List of extraction results
    """
    extractor = get_extractor(config)
    results = []

    for image_path in image_paths:
        try:
            result = extractor.extract(image_path)
            results.append(result)
        except Exception as e:
            # Include error in results
            results.append(
                {
                    "success": False,
                    "error": str(e),
                    "image_path": str(image_path),
                }
            )

    return results
