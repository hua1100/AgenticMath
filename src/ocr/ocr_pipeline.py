"""
OCR Pipeline for orchestrating photo upload → preprocessing → text extraction → diagram analysis.

This module provides a complete end-to-end OCR pipeline matching the
image-extraction-agent.md contract specification.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from .image_preprocessor import preprocess_image, PreprocessingConfig
from .text_extractor import extract_text, OCRConfig
from .diagram_processor import process_diagram_for_ocr
from src.models.uploaded_image import UploadedImage
from src.models.agent_execution import AgentExecution, AgentType
from src.storage.database import get_db


class OCRPipelineConfig:
    """Configuration for OCR pipeline."""

    def __init__(
        self,
        preprocessing_config: Optional[PreprocessingConfig] = None,
        ocr_config: Optional[OCRConfig] = None,
        enable_diagram_analysis: bool = True,
        openai_api_key: Optional[str] = None,
        save_to_database: bool = True,
    ):
        """
        Initialize OCR pipeline configuration.

        Args:
            preprocessing_config: Configuration for image preprocessing
            ocr_config: Configuration for OCR text extraction
            enable_diagram_analysis: Enable GPT-4 Vision diagram analysis
            openai_api_key: OpenAI API key for diagram analysis
            save_to_database: Save results to database
        """
        self.preprocessing_config = preprocessing_config or PreprocessingConfig()
        self.ocr_config = ocr_config or OCRConfig()
        self.enable_diagram_analysis = enable_diagram_analysis
        self.openai_api_key = openai_api_key
        self.save_to_database = save_to_database


class OCRPipeline:
    """
    Complete OCR pipeline that orchestrates all processing steps.

    Pipeline stages:
    1. Image preprocessing (rotation correction, noise reduction, contrast enhancement)
    2. Text extraction using PaddleOCR
    3. Diagram detection and analysis
    4. Database persistence (UploadedImage, AgentExecution)
    """

    def __init__(self, config: Optional[OCRPipelineConfig] = None):
        """
        Initialize OCR pipeline.

        Args:
            config: Pipeline configuration. If None, uses defaults.
        """
        self.config = config or OCRPipelineConfig()

    def process(
        self,
        image_id: str | UUID,
        file_path: str | Path,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Process an image through the complete OCR pipeline.

        This method orchestrates:
        1. Image preprocessing
        2. Text extraction (OCR)
        3. Diagram detection and analysis
        4. Database updates

        Args:
            image_id: Unique identifier for the uploaded image
            file_path: Path to the image file
            db: Optional database session (if None and save_to_database=True, creates one)

        Returns:
            Dictionary matching image-extraction-agent.md contract:
            {
                "success": bool,
                "extracted_text": str,
                "confidence_score": float,
                "contains_diagram": bool,
                "diagram_description": str or None,
                "text_regions": [dict, ...],
                "diagram_regions": [dict, ...],
                "diagram_analysis": dict or None,
                "preprocessing_applied": [str, ...],
                "processing_time_ms": int,
                "ocr_engine": "paddleocr",
                "ocr_version": "2.7.0",
                "warnings": [str, ...]
            }

            Or on error:
            {
                "success": False,
                "error_code": str,
                "error_message": str,
                "extracted_text": "",
                "confidence_score": 0.0,
                "contains_diagram": False,
                "warnings": [str, ...],
                "processing_time_ms": int
            }
        """
        start_time = time.time()

        # Convert to proper types
        if isinstance(image_id, str):
            image_id = UUID(image_id)
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            return self._error_response(
                error_code="OCR_CORRUPTED_IMAGE",
                error_message=f"Image file not found: {file_path}",
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        try:
            # Stage 1: Image Preprocessing
            preprocess_start = time.time()
            preprocessing_result = preprocess_image(
                str(file_path), config=self.config.preprocessing_config
            )
            preprocessing_time_ms = int((time.time() - preprocess_start) * 1000)

            preprocessed_path = preprocessing_result["output_path"]
            preprocessing_applied = preprocessing_result["applied_steps"]

            # Stage 2: Text Extraction (OCR)
            ocr_start = time.time()
            ocr_result = extract_text(
                str(preprocessed_path), config=self.config.ocr_config
            )
            ocr_time_ms = int((time.time() - ocr_start) * 1000)

            # Stage 3: Diagram Detection and Analysis
            diagram_start = time.time()
            diagram_result = process_diagram_for_ocr(
                str(preprocessed_path),
                enable_deep_analysis=self.config.enable_diagram_analysis,
                openai_api_key=self.config.openai_api_key,
            )
            diagram_time_ms = int((time.time() - diagram_start) * 1000)

            # Calculate total processing time
            total_time_ms = int((time.time() - start_time) * 1000)

            # Build result matching contract format
            result = {
                "success": True,
                "extracted_text": ocr_result["extracted_text"],
                "confidence_score": ocr_result["confidence_score"],
                "contains_diagram": diagram_result["contains_diagram"],
                "diagram_description": diagram_result.get("diagram_description"),
                "text_regions": [r.to_dict() for r in ocr_result["text_regions"]],
                "diagram_regions": diagram_result.get("diagram_regions", []),
                "diagram_analysis": diagram_result.get("diagram_analysis"),
                "preprocessing_applied": preprocessing_applied,
                "processing_time_ms": total_time_ms,
                "ocr_engine": "paddleocr",
                "ocr_version": "2.7.0",
                "warnings": [],
            }

            # Add warnings based on confidence
            if ocr_result["confidence_score"] < 0.70:
                result["warnings"].append(
                    f"圖片品質過低，信心度 < 70% (actual: {ocr_result['confidence_score']:.0%})"
                )

            if len(ocr_result["text_regions"]) == 0:
                result["warnings"].append("未檢測到任何文字區域")

            # Check if OCR failed completely
            if not result["extracted_text"] or result["confidence_score"] < 0.50:
                return self._error_response(
                    error_code="OCR_NO_TEXT_DETECTED" if not result["extracted_text"] else "OCR_LOW_CONFIDENCE",
                    error_message="無法辨識照片中的文字內容，請確認照片清晰且包含可辨識的文字。"
                    if not result["extracted_text"]
                    else f"辨識信心度過低（{result['confidence_score']:.0%}），請重新拍攝更清晰的照片。",
                    processing_time_ms=total_time_ms,
                    warnings=result["warnings"],
                )

            # Stage 4: Database Persistence (if enabled)
            if self.config.save_to_database:
                should_close_db = False
                if db is None:
                    db = next(get_db())
                    should_close_db = True

                try:
                    self._save_to_database(
                        db=db,
                        image_id=image_id,
                        file_path=file_path,
                        result=result,
                        processing_time_ms=total_time_ms,
                    )

                    # Commit if we created the session
                    if should_close_db:
                        db.commit()
                finally:
                    if should_close_db:
                        db.close()

            return result

        except Exception as e:
            # Handle unexpected errors
            error_time_ms = int((time.time() - start_time) * 1000)
            return self._error_response(
                error_code="OCR_ENGINE_ERROR",
                error_message=f"OCR 引擎內部錯誤: {str(e)}",
                processing_time_ms=error_time_ms,
            )

    def _error_response(
        self,
        error_code: str,
        error_message: str,
        processing_time_ms: int,
        warnings: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Build error response matching contract format.

        Args:
            error_code: Error code from contract
            error_message: Human-readable error message
            processing_time_ms: Time spent processing
            warnings: Optional warnings list

        Returns:
            Error response dictionary
        """
        return {
            "success": False,
            "error_code": error_code,
            "error_message": error_message,
            "extracted_text": "",
            "confidence_score": 0.0,
            "contains_diagram": False,
            "warnings": warnings or [],
            "processing_time_ms": processing_time_ms,
        }

    def _save_to_database(
        self,
        db: Session,
        image_id: UUID,
        file_path: Path,
        result: Dict[str, Any],
        processing_time_ms: int,
    ) -> None:
        """
        Save OCR results to database.

        Args:
            db: Database session
            image_id: Image ID
            file_path: Path to image file
            result: OCR result dictionary
            processing_time_ms: Total processing time
        """
        # Get or create UploadedImage record
        uploaded_image = db.query(UploadedImage).filter_by(id=image_id).first()

        if uploaded_image:
            # Update existing record
            uploaded_image.ocr_extracted_text = result["extracted_text"]
            uploaded_image.ocr_confidence_score = result["confidence_score"]
            uploaded_image.contains_diagram = result["contains_diagram"]
            uploaded_image.diagram_description = result.get("diagram_description")
            uploaded_image.preprocessing_applied = result["preprocessing_applied"]
            uploaded_image.ocr_processing_time_ms = processing_time_ms
        else:
            # This shouldn't happen in normal flow, but handle it
            # In production, image record should be created during upload
            raise ValueError(
                f"UploadedImage record not found for image_id={image_id}. "
                "Image must be uploaded before OCR processing."
            )

        # Create AgentExecution record for traceability
        agent_execution = AgentExecution(
            agent_type=AgentType.OCR,
            session_id=None,  # OCR is standalone, not part of rephrase session
            input_data={
                "image_id": str(image_id),
                "file_path": str(file_path),
                "preprocessing_config": {
                    "auto_rotation": self.config.preprocessing_config.auto_rotation,
                    "noise_reduction": self.config.preprocessing_config.noise_reduction,
                    "contrast_enhancement": self.config.preprocessing_config.contrast_enhancement,
                },
                "ocr_config": {
                    "language": self.config.ocr_config.lang,
                    "use_textline_orientation": self.config.ocr_config.use_textline_orientation,
                },
            },
            output_data=result,
            prompt_template="N/A (OCR does not use LLM prompts)",
            raw_llm_response=None,  # OCR doesn't use LLM (diagram analysis is separate)
            execution_time_ms=processing_time_ms,
            llm_model=None,  # No LLM for OCR
        )

        db.add(agent_execution)


# Convenience function
def process_image(
    image_id: str | UUID,
    file_path: str | Path,
    config: Optional[OCRPipelineConfig] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Process an image through the OCR pipeline (convenience function).

    Args:
        image_id: Unique identifier for the uploaded image
        file_path: Path to the image file
        config: Optional pipeline configuration
        db: Optional database session

    Returns:
        OCR result dictionary matching contract format
    """
    pipeline = OCRPipeline(config)
    return pipeline.process(image_id, file_path, db)
