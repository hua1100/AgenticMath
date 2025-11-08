"""
Integration tests for OCR Pipeline.

These tests verify the complete OCR workflow:
upload → preprocess → OCR → diagram detection → database save
"""

import pytest
from pathlib import Path
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from src.ocr.ocr_pipeline import (
    OCRPipeline,
    OCRPipelineConfig,
    process_image,
)
from src.models.uploaded_image import UploadedImage, ImageFormat
from src.models.agent_execution import AgentExecution, AgentType


# Test fixtures paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "diagrams"
TRIANGLE_IMAGE = FIXTURES_DIR / "triangle.jpg"
NO_DIAGRAM_IMAGE = FIXTURES_DIR / "no_diagram.jpg"


class TestOCRPipelineConfig:
    """Tests for OCRPipelineConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OCRPipelineConfig()

        assert config.preprocessing_config is not None
        assert config.ocr_config is not None
        assert config.enable_diagram_analysis is True
        assert config.save_to_database is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = OCRPipelineConfig(
            enable_diagram_analysis=False,
            save_to_database=False,
        )

        assert config.enable_diagram_analysis is False
        assert config.save_to_database is False


class TestOCRPipeline:
    """Tests for OCRPipeline integration."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = OCRPipeline()

        assert pipeline.config is not None
        assert isinstance(pipeline.config, OCRPipelineConfig)

    def test_process_nonexistent_file(self):
        """Test processing nonexistent file returns error."""
        pipeline = OCRPipeline()
        image_id = uuid4()

        result = pipeline.process(
            image_id=image_id, file_path="/nonexistent/image.jpg", db=None
        )

        assert result["success"] is False
        assert result["error_code"] == "OCR_CORRUPTED_IMAGE"
        assert "not found" in result["error_message"]

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_process_success_without_database(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test successful processing without database save."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing
        mock_preprocess.return_value = {
            "success": True,
            "output_path": str(TRIANGLE_IMAGE),
            "applied_steps": ["rotation_corrected", "contrast_enhanced"],
        }

        # Mock OCR
        from src.ocr.text_extractor import TextRegion

        mock_extract.return_value = {
            "extracted_text": "求解方程式：在直角三角形 ABC 中",
            "confidence_score": 0.92,
            "text_regions": [
                TextRegion(
                    bbox=[[10, 20], [150, 20], [150, 45], [10, 45]],
                    text="求解方程式",
                    confidence=0.95,
                )
            ],
            "processing_time_ms": 1500,
        }

        # Mock diagram
        mock_diagram.return_value = {
            "contains_diagram": True,
            "diagram_description": "包含直角三角形",
            "diagram_regions": [
                {
                    "bbox": [[400, 100], [600, 100], [600, 300], [400, 300]],
                    "type": "geometric_figure",
                    "description": "三角形",
                }
            ],
            "diagram_analysis": {
                "diagram_type": "right_triangle",
                "key_concepts": ["pythagorean_theorem"],
                "features": {"vertices": ["A", "B", "C"]},
                "difficulty_indicators": {"complexity": "medium"},
            },
        }

        # Process without database
        config = OCRPipelineConfig(save_to_database=False)
        pipeline = OCRPipeline(config)
        image_id = uuid4()

        result = pipeline.process(
            image_id=image_id, file_path=TRIANGLE_IMAGE, db=None
        )

        # Verify success
        assert result["success"] is True
        assert result["extracted_text"] == "求解方程式：在直角三角形 ABC 中"
        assert result["confidence_score"] == 0.92
        assert result["contains_diagram"] is True
        assert result["diagram_analysis"] is not None
        assert len(result["text_regions"]) == 1

        # Verify contract format
        assert "ocr_engine" in result
        assert "ocr_version" in result
        assert "preprocessing_applied" in result
        assert "warnings" in result
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] >= 0  # Can be 0 with fast mocks

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_process_with_low_confidence_warning(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test that low confidence triggers warning."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing
        mock_preprocess.return_value = {
            "success": True,
            "output_path": str(TRIANGLE_IMAGE),
            "applied_steps": [],
        }

        # Mock OCR with LOW confidence
        from src.ocr.text_extractor import TextRegion

        mock_extract.return_value = {
            "extracted_text": "模糊文字",
            "confidence_score": 0.65,  # Low confidence
            "text_regions": [
                TextRegion(
                    bbox=[[10, 20], [150, 20], [150, 45], [10, 45]],
                    text="模糊文字",
                    confidence=0.65,
                )
            ],
            "processing_time_ms": 1500,
        }

        # Mock diagram
        mock_diagram.return_value = {
            "contains_diagram": False,
            "diagram_description": None,
            "diagram_regions": [],
            "diagram_analysis": None,
        }

        # Process
        config = OCRPipelineConfig(save_to_database=False)
        pipeline = OCRPipeline(config)
        image_id = uuid4()

        result = pipeline.process(
            image_id=image_id, file_path=TRIANGLE_IMAGE, db=None
        )

        # Verify warning is present
        assert result["success"] is True
        assert len(result["warnings"]) > 0
        assert any("信心度" in w for w in result["warnings"])

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_process_no_text_detected_error(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test that no text triggers error response."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing
        mock_preprocess.return_value = {
            "success": True,
            "output_path": str(TRIANGLE_IMAGE),
            "applied_steps": [],
        }

        # Mock OCR with NO text
        mock_extract.return_value = {
            "extracted_text": "",  # No text!
            "confidence_score": 0.0,
            "text_regions": [],
            "processing_time_ms": 1500,
        }

        # Mock diagram
        mock_diagram.return_value = {
            "contains_diagram": False,
            "diagram_description": None,
            "diagram_regions": [],
            "diagram_analysis": None,
        }

        # Process
        config = OCRPipelineConfig(save_to_database=False)
        pipeline = OCRPipeline(config)
        image_id = uuid4()

        result = pipeline.process(
            image_id=image_id, file_path=TRIANGLE_IMAGE, db=None
        )

        # Verify error response
        assert result["success"] is False
        assert result["error_code"] == "OCR_NO_TEXT_DETECTED"
        assert "無法辨識" in result["error_message"]

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_process_very_low_confidence_error(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test that very low confidence (<50%) triggers error."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing
        mock_preprocess.return_value = {
            "success": True,
            "output_path": str(TRIANGLE_IMAGE),
            "applied_steps": [],
        }

        # Mock OCR with VERY LOW confidence
        from src.ocr.text_extractor import TextRegion

        mock_extract.return_value = {
            "extracted_text": "???",
            "confidence_score": 0.45,  # Below 50% threshold
            "text_regions": [
                TextRegion(
                    bbox=[[10, 20], [150, 20], [150, 45], [10, 45]],
                    text="???",
                    confidence=0.45,
                )
            ],
            "processing_time_ms": 1500,
        }

        # Mock diagram
        mock_diagram.return_value = {
            "contains_diagram": False,
            "diagram_description": None,
            "diagram_regions": [],
            "diagram_analysis": None,
        }

        # Process
        config = OCRPipelineConfig(save_to_database=False)
        pipeline = OCRPipeline(config)
        image_id = uuid4()

        result = pipeline.process(
            image_id=image_id, file_path=TRIANGLE_IMAGE, db=None
        )

        # Verify error response
        assert result["success"] is False
        assert result["error_code"] == "OCR_LOW_CONFIDENCE"
        assert "信心度過低" in result["error_message"]

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_process_exception_handling(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test that exceptions are caught and returned as error response."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing to raise exception
        mock_preprocess.side_effect = Exception("Unexpected preprocessing error")

        # Process
        config = OCRPipelineConfig(save_to_database=False)
        pipeline = OCRPipeline(config)
        image_id = uuid4()

        result = pipeline.process(
            image_id=image_id, file_path=TRIANGLE_IMAGE, db=None
        )

        # Verify error response
        assert result["success"] is False
        assert result["error_code"] == "OCR_ENGINE_ERROR"
        assert "內部錯誤" in result["error_message"]

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_process_with_database_save(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test successful processing with database save."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing
        mock_preprocess.return_value = {
            "success": True,
            "output_path": str(TRIANGLE_IMAGE),
            "applied_steps": ["rotation_corrected"],
        }

        # Mock OCR
        from src.ocr.text_extractor import TextRegion

        mock_extract.return_value = {
            "extracted_text": "測試文字",
            "confidence_score": 0.90,
            "text_regions": [
                TextRegion(
                    bbox=[[10, 20], [150, 20], [150, 45], [10, 45]],
                    text="測試文字",
                    confidence=0.90,
                )
            ],
            "processing_time_ms": 1500,
        }

        # Mock diagram
        mock_diagram.return_value = {
            "contains_diagram": False,
            "diagram_description": None,
            "diagram_regions": [],
            "diagram_analysis": None,
        }

        # Create mock database session
        mock_db = Mock(spec=Session)
        image_id = uuid4()

        # Create mock UploadedImage record
        mock_uploaded_image = Mock(spec=UploadedImage)
        mock_uploaded_image.id = image_id
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_uploaded_image
        )

        # Process WITH database save
        config = OCRPipelineConfig(save_to_database=True)
        pipeline = OCRPipeline(config)

        result = pipeline.process(
            image_id=image_id, file_path=TRIANGLE_IMAGE, db=mock_db
        )

        # Verify success
        assert result["success"] is True

        # Verify database was queried for UploadedImage
        mock_db.query.assert_called()

        # Verify AgentExecution was added
        mock_db.add.assert_called()
        agent_execution_call = mock_db.add.call_args[0][0]
        assert isinstance(agent_execution_call, AgentExecution)
        assert agent_execution_call.agent_type == AgentType.OCR

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_process_database_save_missing_image_raises_error(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test that missing UploadedImage record raises error."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing
        mock_preprocess.return_value = {
            "success": True,
            "output_path": str(TRIANGLE_IMAGE),
            "applied_steps": [],
        }

        # Mock OCR
        from src.ocr.text_extractor import TextRegion

        mock_extract.return_value = {
            "extracted_text": "測試",
            "confidence_score": 0.90,
            "text_regions": [
                TextRegion(
                    bbox=[[10, 20], [150, 20], [150, 45], [10, 45]],
                    text="測試",
                    confidence=0.90,
                )
            ],
            "processing_time_ms": 1500,
        }

        # Mock diagram
        mock_diagram.return_value = {
            "contains_diagram": False,
            "diagram_description": None,
            "diagram_regions": [],
            "diagram_analysis": None,
        }

        # Create mock database session - UploadedImage NOT FOUND
        mock_db = Mock(spec=Session)
        image_id = uuid4()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None  # Not found!

        # Process
        config = OCRPipelineConfig(save_to_database=True)
        pipeline = OCRPipeline(config)

        result = pipeline.process(
            image_id=image_id, file_path=TRIANGLE_IMAGE, db=mock_db
        )

        # Should return error (not raise exception)
        assert result["success"] is False
        assert result["error_code"] == "OCR_ENGINE_ERROR"


class TestConvenienceFunction:
    """Tests for convenience function."""

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_process_image_convenience_function(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test process_image convenience function."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing
        mock_preprocess.return_value = {
            "success": True,
            "output_path": str(TRIANGLE_IMAGE),
            "applied_steps": [],
        }

        # Mock OCR
        from src.ocr.text_extractor import TextRegion

        mock_extract.return_value = {
            "extracted_text": "測試",
            "confidence_score": 0.90,
            "text_regions": [
                TextRegion(
                    bbox=[[10, 20], [150, 20], [150, 45], [10, 45]],
                    text="測試",
                    confidence=0.90,
                )
            ],
            "processing_time_ms": 1500,
        }

        # Mock diagram
        mock_diagram.return_value = {
            "contains_diagram": False,
            "diagram_description": None,
            "diagram_regions": [],
            "diagram_analysis": None,
        }

        # Process
        config = OCRPipelineConfig(save_to_database=False)
        image_id = uuid4()

        result = process_image(
            image_id=image_id, file_path=TRIANGLE_IMAGE, config=config, db=None
        )

        # Verify success
        assert result["success"] is True
        assert result["extracted_text"] == "測試"


class TestPerformance:
    """Performance tests for OCR pipeline."""

    @patch("src.ocr.ocr_pipeline.process_diagram_for_ocr")
    @patch("src.ocr.ocr_pipeline.extract_text")
    @patch("src.ocr.ocr_pipeline.preprocess_image")
    def test_pipeline_performance_under_5_seconds(
        self, mock_preprocess, mock_extract, mock_diagram
    ):
        """Test that pipeline completes in under 5 seconds."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock preprocessing (fast)
        mock_preprocess.return_value = {
            "success": True,
            "output_path": str(TRIANGLE_IMAGE),
            "applied_steps": [],
        }

        # Mock OCR (fast)
        from src.ocr.text_extractor import TextRegion

        mock_extract.return_value = {
            "extracted_text": "快速測試",
            "confidence_score": 0.90,
            "text_regions": [
                TextRegion(
                    bbox=[[10, 20], [150, 20], [150, 45], [10, 45]],
                    text="快速測試",
                    confidence=0.90,
                )
            ],
            "processing_time_ms": 1000,
        }

        # Mock diagram (fast)
        mock_diagram.return_value = {
            "contains_diagram": False,
            "diagram_description": None,
            "diagram_regions": [],
            "diagram_analysis": None,
        }

        # Process
        config = OCRPipelineConfig(save_to_database=False)
        pipeline = OCRPipeline(config)
        image_id = uuid4()

        result = pipeline.process(
            image_id=image_id, file_path=TRIANGLE_IMAGE, db=None
        )

        # Verify performance
        assert result["success"] is True
        assert result["processing_time_ms"] < 5000  # Under 5 seconds
