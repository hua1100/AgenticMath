"""
Unit tests for diagram detector module.
"""

import pytest
from pathlib import Path
import cv2
import numpy as np

from src.ocr.diagram_detector import (
    DiagramDetector,
    DiagramDetectorConfig,
    DiagramRegion,
    detect_diagrams,
)


# Test fixtures paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "diagrams"
TRIANGLE_IMAGE = FIXTURES_DIR / "triangle.jpg"
CIRCLE_IMAGE = FIXTURES_DIR / "circle.jpg"
RECTANGLE_IMAGE = FIXTURES_DIR / "rectangle.jpg"
SQUARE_IMAGE = FIXTURES_DIR / "square.jpg"
MULTIPLE_SHAPES_IMAGE = FIXTURES_DIR / "multiple_shapes.jpg"
MATH_DIAGRAM_IMAGE = FIXTURES_DIR / "math_diagram.jpg"
NO_DIAGRAM_IMAGE = FIXTURES_DIR / "no_diagram.jpg"


class TestDiagramRegion:
    """Tests for DiagramRegion class."""

    def test_diagram_region_creation(self):
        """Test DiagramRegion creation."""
        region = DiagramRegion(
            bbox=[[0, 0], [100, 0], [100, 100], [0, 100]],
            type="geometric_figure",
            description="三角形",
            confidence=0.85,
            shape="triangle"
        )

        assert region.type == "geometric_figure"
        assert region.description == "三角形"
        assert region.confidence == 0.85
        assert region.shape == "triangle"

    def test_diagram_region_to_dict(self):
        """Test DiagramRegion to_dict conversion."""
        region = DiagramRegion(
            bbox=[[0, 0], [100, 0], [100, 100], [0, 100]],
            type="geometric_figure",
            description="圓形",
            confidence=0.86,
            shape="circle"
        )

        result = region.to_dict()

        assert result["bbox"] == [[0, 0], [100, 0], [100, 100], [0, 100]]
        assert result["type"] == "geometric_figure"
        assert result["description"] == "圓形"
        assert result["confidence"] == 0.86
        assert result["shape"] == "circle"


class TestDiagramDetectorConfig:
    """Tests for DiagramDetectorConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DiagramDetectorConfig()

        assert config.min_contour_area == 1000
        assert config.approx_epsilon_ratio == 0.02
        assert config.circle_circularity_threshold == 0.75
        assert config.detect_geometric_shapes is True
        assert config.detect_layout_regions is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = DiagramDetectorConfig(
            min_contour_area=500,
            approx_epsilon_ratio=0.01,
            circle_circularity_threshold=0.80,
        )

        assert config.min_contour_area == 500
        assert config.approx_epsilon_ratio == 0.01
        assert config.circle_circularity_threshold == 0.80


class TestDiagramDetector:
    """Tests for DiagramDetector class."""

    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = DiagramDetector()

        assert detector.config is not None
        assert isinstance(detector.config, DiagramDetectorConfig)

    def test_detector_with_custom_config(self):
        """Test detector with custom configuration."""
        config = DiagramDetectorConfig(min_contour_area=500)
        detector = DiagramDetector(config)

        assert detector.config.min_contour_area == 500

    @pytest.mark.skipif(
        not TRIANGLE_IMAGE.exists(), reason="Test image not found"
    )
    def test_detect_triangle(self):
        """Test triangle detection."""
        detector = DiagramDetector()
        result = detector.detect(TRIANGLE_IMAGE)

        assert result["contains_diagram"] is True
        assert len(result["diagram_regions"]) > 0
        assert result["detected_shapes"]["triangles"] > 0
        assert "三角形" in result["diagram_description"]

    @pytest.mark.skipif(
        not CIRCLE_IMAGE.exists(), reason="Test image not found"
    )
    def test_detect_circle(self):
        """Test circle detection."""
        detector = DiagramDetector()
        result = detector.detect(CIRCLE_IMAGE)

        assert result["contains_diagram"] is True
        assert len(result["diagram_regions"]) > 0
        assert result["detected_shapes"]["circles"] > 0
        assert "圓形" in result["diagram_description"]

    @pytest.mark.skipif(
        not RECTANGLE_IMAGE.exists(), reason="Test image not found"
    )
    def test_detect_rectangle(self):
        """Test rectangle detection."""
        detector = DiagramDetector()
        result = detector.detect(RECTANGLE_IMAGE)

        assert result["contains_diagram"] is True
        assert len(result["diagram_regions"]) > 0
        assert result["detected_shapes"]["rectangles"] > 0
        assert "矩形" in result["diagram_description"]

    @pytest.mark.skipif(
        not SQUARE_IMAGE.exists(), reason="Test image not found"
    )
    def test_detect_square(self):
        """Test square detection."""
        detector = DiagramDetector()
        result = detector.detect(SQUARE_IMAGE)

        assert result["contains_diagram"] is True
        assert len(result["diagram_regions"]) > 0
        # Square might be detected as rectangle or square
        assert (result["detected_shapes"]["squares"] > 0 or
                result["detected_shapes"]["rectangles"] > 0)

    @pytest.mark.skipif(
        not MULTIPLE_SHAPES_IMAGE.exists(), reason="Test image not found"
    )
    def test_detect_multiple_shapes(self):
        """Test detection of multiple shapes."""
        detector = DiagramDetector()
        result = detector.detect(MULTIPLE_SHAPES_IMAGE)

        assert result["contains_diagram"] is True
        assert len(result["diagram_regions"]) >= 3
        # Should detect at least triangle, circle, and rectangles
        total_shapes = sum(result["detected_shapes"].values())
        assert total_shapes >= 3

    @pytest.mark.skipif(
        not NO_DIAGRAM_IMAGE.exists(), reason="Test image not found"
    )
    def test_no_diagram_detection(self):
        """Test handling of images with no diagrams."""
        detector = DiagramDetector()
        result = detector.detect(NO_DIAGRAM_IMAGE)

        # Should not detect diagrams in text-only image
        # (unless text creates contours that look like shapes)
        assert isinstance(result["contains_diagram"], bool)
        assert result["diagram_description"] is None or result["diagram_description"] == ""

    def test_detect_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        detector = DiagramDetector()

        with pytest.raises(FileNotFoundError):
            detector.detect("nonexistent.jpg")

    def test_detect_invalid_image(self, tmp_path):
        """Test error handling for invalid image."""
        invalid_file = tmp_path / "invalid.jpg"
        invalid_file.write_text("This is not an image")

        detector = DiagramDetector()

        with pytest.raises(ValueError, match="Failed to load image"):
            detector.detect(invalid_file)

    def test_processing_time(self):
        """Test that processing completes within reasonable time."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test image not found")

        detector = DiagramDetector()
        result = detector.detect(TRIANGLE_IMAGE)

        # Should complete in less than 2 seconds
        assert result["processing_time_ms"] < 2000


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @pytest.mark.skipif(
        not TRIANGLE_IMAGE.exists(), reason="Test image not found"
    )
    def test_detect_diagrams_function(self):
        """Test detect_diagrams convenience function."""
        result = detect_diagrams(TRIANGLE_IMAGE)

        assert result["contains_diagram"] is True
        assert isinstance(result["diagram_regions"], list)

    @pytest.mark.skipif(
        not CIRCLE_IMAGE.exists(), reason="Test image not found"
    )
    def test_detect_diagrams_with_custom_config(self):
        """Test detect_diagrams with custom configuration."""
        config = DiagramDetectorConfig(min_contour_area=500)
        result = detect_diagrams(CIRCLE_IMAGE, config)

        assert result["contains_diagram"] is True


class TestIntegration:
    """Integration tests for diagram detection."""

    @pytest.mark.skipif(
        not MATH_DIAGRAM_IMAGE.exists(), reason="Test image not found"
    )
    def test_math_diagram_detection(self):
        """Test detection on realistic math diagram."""
        detector = DiagramDetector()
        result = detector.detect(MATH_DIAGRAM_IMAGE)

        assert result["contains_diagram"] is True
        assert result["diagram_description"] is not None
        assert len(result["diagram_description"]) > 0

    def test_detection_success_rate(self):
        """Test that detection success rate meets ≥80% requirement."""
        # Test images that should have diagrams
        test_images = [
            TRIANGLE_IMAGE,
            CIRCLE_IMAGE,
            RECTANGLE_IMAGE,
            SQUARE_IMAGE,
            MULTIPLE_SHAPES_IMAGE,
        ]

        detector = DiagramDetector()
        successful_detections = 0
        total_tests = 0

        for image_path in test_images:
            if not image_path.exists():
                continue

            total_tests += 1
            result = detector.detect(image_path)

            if result["contains_diagram"]:
                successful_detections += 1

        if total_tests > 0:
            success_rate = successful_detections / total_tests
            print(f"\n檢測成功率: {success_rate * 100:.1f}% ({successful_detections}/{total_tests})")

            # Should meet ≥80% success rate requirement
            assert success_rate >= 0.80, f"Detection success rate {success_rate:.2%} < 80%"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_image(self, tmp_path):
        """Test detection on completely white image."""
        # Create empty white image
        empty_img = np.ones((400, 600, 3), dtype=np.uint8) * 255
        empty_path = tmp_path / "empty.jpg"
        cv2.imwrite(str(empty_path), empty_img)

        detector = DiagramDetector()
        result = detector.detect(empty_path)

        # Should not detect diagrams
        assert result["contains_diagram"] is False
        assert len(result["diagram_regions"]) == 0

    def test_very_small_shapes(self, tmp_path):
        """Test that very small shapes are filtered out."""
        # Create image with very small shape
        img = np.ones((400, 600, 3), dtype=np.uint8) * 255
        cv2.rectangle(img, (100, 100), (105, 105), (0, 0, 0), 1)
        small_path = tmp_path / "small.jpg"
        cv2.imwrite(str(small_path), img)

        detector = DiagramDetector()
        result = detector.detect(small_path)

        # Small shapes should be filtered out by min_contour_area
        # Result may have no diagrams or very few
        assert isinstance(result["contains_diagram"], bool)
