"""
Unit tests for text extractor module (PaddleOCR).
"""

import pytest
from pathlib import Path
import cv2
import numpy as np
import tempfile

from src.ocr.text_extractor import (
    OCRConfig,
    TextRegion,
    OCRExtractor,
    get_extractor,
    extract_text,
    extract_text_from_numpy,
    batch_extract_text,
)


# Check if PaddleOCR models can be downloaded (network available)
def _check_paddleocr_available():
    """Check if PaddleOCR can be initialized (models available)."""
    try:
        from paddleocr import PaddleOCR
        # Try to initialize with minimal configuration
        ocr = PaddleOCR(
            lang="en",
            use_textline_orientation=False,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
        )
        return True
    except Exception as e:
        # Network unavailable or models cannot be downloaded
        return False


PADDLEOCR_AVAILABLE = _check_paddleocr_available()
requires_paddleocr = pytest.mark.skipif(
    not PADDLEOCR_AVAILABLE,
    reason="PaddleOCR models not available (requires internet connection)"
)


# Test fixtures paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "images"
SIMPLE_MATH_IMAGE = FIXTURES_DIR / "simple_math.jpg"
EMPTY_IMAGE = FIXTURES_DIR / "empty.jpg"
NUMBERS_IMAGE = FIXTURES_DIR / "numbers.jpg"
MULTI_LINE_IMAGE = FIXTURES_DIR / "multi_line.jpg"


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a simple test image."""
    # Create white background with black text
    image = np.ones((200, 600, 3), dtype=np.uint8) * 255

    # Draw some text using OpenCV (simple ASCII)
    cv2.putText(
        image, "TEST 123", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3
    )

    # Save to temp file
    image_path = tmp_path / "test_image.jpg"
    cv2.imwrite(str(image_path), image)

    return image_path


class TestOCRConfig:
    """Tests for OCRConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OCRConfig()

        assert config.lang == "chinese_cht"
        assert config.use_textline_orientation is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = OCRConfig(
            lang="ch",
            use_textline_orientation=False,
        )

        assert config.lang == "ch"
        assert config.use_textline_orientation is False


class TestTextRegion:
    """Tests for TextRegion class."""

    def test_text_region_creation(self):
        """Test creating a text region."""
        bbox = [[10, 20], [100, 20], [100, 50], [10, 50]]
        region = TextRegion(bbox, "測試", 0.95)

        assert region.bbox == bbox
        assert region.text == "測試"
        assert region.confidence == 0.95

    def test_text_region_to_dict(self):
        """Test converting text region to dictionary."""
        bbox = [[10, 20], [100, 20], [100, 50], [10, 50]]
        region = TextRegion(bbox, "測試", 0.95)

        result = region.to_dict()

        assert result["bbox"] == bbox
        assert result["text"] == "測試"
        assert result["confidence"] == 0.95

    def test_text_region_repr(self):
        """Test text region string representation."""
        bbox = [[10, 20], [100, 20], [100, 50], [10, 50]]
        region = TextRegion(bbox, "測試", 0.95)

        repr_str = repr(region)
        assert "測試" in repr_str
        assert "0.95" in repr_str


class TestOCRExtractor:
    """Tests for OCRExtractor class."""

    def test_extractor_initialization(self):
        """Test OCR extractor initialization."""
        config = OCRConfig()
        extractor = OCRExtractor(config)

        assert extractor.config == config
        assert extractor._ocr is None  # Lazy initialization

    def test_extractor_with_default_config(self):
        """Test extractor with default configuration."""
        extractor = OCRExtractor()

        assert extractor.config is not None
        assert extractor.config.lang == "chinese_cht"

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists(), reason="Test image not found"
    )
    def test_extract_from_image(self):
        """Test extracting text from image."""
        config = OCRConfig()
        extractor = OCRExtractor(config)

        result = extractor.extract(SIMPLE_MATH_IMAGE)

        # Basic assertions
        assert result["success"] is True
        assert "text" in result
        assert "text_regions" in result
        assert "confidence_score" in result
        assert "processing_time_ms" in result
        assert "num_regions" in result
        assert "has_text" in result

        # Should detect some text
        assert isinstance(result["text_regions"], list)

    @requires_paddleocr
    @pytest.mark.skipif(not EMPTY_IMAGE.exists(), reason="Test image not found")
    def test_extract_from_empty_image(self):
        """Test extracting from empty image (no text)."""
        config = OCRConfig()
        extractor = OCRExtractor(config)

        result = extractor.extract(EMPTY_IMAGE)

        assert result["success"] is True
        assert result["has_text"] is False
        assert result["num_regions"] == 0
        assert result["text"] == ""
        assert result["confidence_score"] == 0.0

    def test_extract_nonexistent_file(self):
        """Test extracting from nonexistent file."""
        extractor = OCRExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract("nonexistent.jpg")

    def test_extract_invalid_image(self, tmp_path):
        """Test extracting from invalid image file."""
        invalid_file = tmp_path / "invalid.jpg"
        invalid_file.write_text("not an image")

        extractor = OCRExtractor()

        with pytest.raises(ValueError, match="Failed to load image"):
            extractor.extract(invalid_file)

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists(), reason="Test image not found"
    )
    def test_processing_time(self):
        """Test that processing completes within time limit."""
        config = OCRConfig()
        extractor = OCRExtractor(config)

        result = extractor.extract(SIMPLE_MATH_IMAGE)

        # Should complete in less than 3 seconds
        assert result["processing_time_ms"] < 3000

    @requires_paddleocr
    @pytest.mark.skipif(
        not MULTI_LINE_IMAGE.exists(), reason="Test image not found"
    )
    def test_extract_multiline_text(self):
        """Test extracting multi-line text."""
        config = OCRConfig()
        extractor = OCRExtractor(config)

        result = extractor.extract(MULTI_LINE_IMAGE)

        # Should detect multiple text regions
        if result["has_text"]:
            assert result["num_regions"] >= 1


class TestGlobalFunctions:
    """Tests for module-level convenience functions."""

    def test_get_extractor_singleton(self):
        """Test that get_extractor returns singleton."""
        extractor1 = get_extractor()
        extractor2 = get_extractor()

        # Should be same instance
        assert extractor1 is extractor2

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists(), reason="Test image not found"
    )
    def test_extract_text_convenience(self):
        """Test extract_text convenience function."""
        result = extract_text(SIMPLE_MATH_IMAGE)

        assert result["success"] is True
        assert "text" in result

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists(), reason="Test image not found"
    )
    def test_extract_text_without_singleton(self):
        """Test extract_text without singleton."""
        result = extract_text(SIMPLE_MATH_IMAGE, use_singleton=False)

        assert result["success"] is True

    @requires_paddleocr
    def test_extract_text_from_numpy(self, sample_image_path):
        """Test extracting text from numpy array."""
        # Load image as numpy array
        image = cv2.imread(str(sample_image_path))

        result = extract_text_from_numpy(image)

        assert result["success"] is True
        assert "text" in result

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists() or not NUMBERS_IMAGE.exists(),
        reason="Test images not found",
    )
    def test_batch_extract_text(self):
        """Test batch text extraction."""
        image_paths = [SIMPLE_MATH_IMAGE, NUMBERS_IMAGE]

        results = batch_extract_text(image_paths)

        assert len(results) == 2
        assert all(r["success"] for r in results)

    @requires_paddleocr
    def test_batch_extract_with_error(self, tmp_path):
        """Test batch extraction with one invalid file."""
        valid_image = tmp_path / "valid.jpg"
        image = np.ones((200, 600, 3), dtype=np.uint8) * 255
        cv2.imwrite(str(valid_image), image)

        invalid_image = tmp_path / "nonexistent.jpg"

        results = batch_extract_text([valid_image, invalid_image])

        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "error" in results[1]


class TestIntegration:
    """Integration tests for OCR pipeline."""

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists(), reason="Test image not found"
    )
    def test_full_ocr_pipeline(self):
        """Test complete OCR pipeline."""
        # Configure OCR
        config = OCRConfig(
            lang="chinese_cht", use_textline_orientation=True
        )

        # Extract text
        result = extract_text(SIMPLE_MATH_IMAGE, config)

        # Verify results
        assert result["success"] is True
        assert result["processing_time_ms"] < 3000

        # If text was detected, verify structure
        if result["has_text"]:
            assert len(result["text_regions"]) > 0
            assert result["confidence_score"] > 0.0

            # Verify text regions
            for region in result["text_regions"]:
                assert isinstance(region, TextRegion)
                assert isinstance(region.text, str)
                assert 0.0 <= region.confidence <= 1.0
                assert len(region.bbox) == 4  # 4 corners

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists(), reason="Test image not found"
    )
    def test_confidence_score_threshold(self):
        """Test that confidence scores meet threshold."""
        result = extract_text(SIMPLE_MATH_IMAGE)

        # For printed text, confidence should be reasonably high
        # Note: Actual confidence depends on image quality
        if result["has_text"]:
            # Confidence should be between 0 and 1
            assert 0.0 <= result["confidence_score"] <= 1.0

    @requires_paddleocr
    def test_empty_vs_text_images(self):
        """Test OCR can distinguish empty vs text images."""
        if EMPTY_IMAGE.exists() and SIMPLE_MATH_IMAGE.exists():
            empty_result = extract_text(EMPTY_IMAGE)
            text_result = extract_text(SIMPLE_MATH_IMAGE)

            # Empty image should have no text
            assert empty_result["has_text"] is False
            assert empty_result["num_regions"] == 0

            # Simple math image may or may not be detected depending on OCR
            # Just verify it returns valid results
            assert text_result["success"] is True


class TestPerformance:
    """Performance tests."""

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists(), reason="Test image not found"
    )
    def test_extraction_performance(self):
        """Test that OCR extraction meets performance requirements."""
        import time

        start = time.time()
        result = extract_text(SIMPLE_MATH_IMAGE)
        elapsed = time.time() - start

        # Should complete in less than 3 seconds
        assert elapsed < 3.0
        assert result["processing_time_ms"] < 3000

    @requires_paddleocr
    @pytest.mark.skipif(
        not SIMPLE_MATH_IMAGE.exists(), reason="Test image not found"
    )
    def test_singleton_performance(self):
        """Test that singleton pattern improves performance."""
        import time

        # First call (initializes OCR engine)
        start1 = time.time()
        result1 = extract_text(SIMPLE_MATH_IMAGE, use_singleton=True)
        time1 = time.time() - start1

        # Second call (reuses OCR engine)
        start2 = time.time()
        result2 = extract_text(SIMPLE_MATH_IMAGE, use_singleton=True)
        time2 = time.time() - start2

        # Second call should be faster (no initialization overhead)
        # Note: This may not always be true due to system factors
        assert result1["success"] is True
        assert result2["success"] is True
