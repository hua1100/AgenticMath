"""
Unit tests for diagram analyzer module.
"""

import pytest
from pathlib import Path
import cv2
import numpy as np
import json
from unittest.mock import Mock, patch, MagicMock
import os

from src.ocr.diagram_analyzer import (
    DiagramAnalyzer,
    DiagramAnalyzerConfig,
    DiagramAnalysis,
    analyze_diagram,
)
from src.ocr.diagram_detector import DiagramRegion


# Test fixtures paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "diagrams"
TRIANGLE_IMAGE = FIXTURES_DIR / "triangle.jpg"
CIRCLE_IMAGE = FIXTURES_DIR / "circle.jpg"
MATH_DIAGRAM_IMAGE = FIXTURES_DIR / "math_diagram.jpg"


class TestDiagramAnalysis:
    """Tests for DiagramAnalysis dataclass."""

    def test_diagram_analysis_creation(self):
        """Test DiagramAnalysis creation."""
        analysis = DiagramAnalysis(
            diagram_type="right_triangle",
            key_concepts=["pythagorean_theorem", "trigonometry"],
            features={
                "vertices": ["A", "B", "C"],
                "right_angle_at": "C",
                "labeled_sides": {"AB": "10", "AC": "6"},
            },
            difficulty_indicators={
                "has_labels": True,
                "requires_calculation": True,
                "complexity": "medium",
            },
            analysis_confidence=0.90
        )

        assert analysis.diagram_type == "right_triangle"
        assert len(analysis.key_concepts) == 2
        assert "pythagorean_theorem" in analysis.key_concepts
        assert analysis.features["vertices"] == ["A", "B", "C"]
        assert analysis.difficulty_indicators["complexity"] == "medium"
        assert analysis.analysis_confidence == 0.90

    def test_diagram_analysis_to_dict(self):
        """Test DiagramAnalysis to_dict conversion."""
        analysis = DiagramAnalysis(
            diagram_type="circle",
            key_concepts=["circle_properties", "radius"],
            features={
                "center": "O",
                "radius": "5",
            },
            difficulty_indicators={
                "has_labels": True,
                "complexity": "simple",
            },
            analysis_confidence=0.88
        )

        result = analysis.to_dict()

        assert result["diagram_type"] == "circle"
        assert result["key_concepts"] == ["circle_properties", "radius"]
        assert result["features"]["center"] == "O"
        assert result["difficulty_indicators"]["complexity"] == "simple"
        assert result["analysis_confidence"] == 0.88


class TestDiagramAnalyzerConfig:
    """Tests for DiagramAnalyzerConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DiagramAnalyzerConfig()

        assert config.openai_model == "gpt-4o"
        assert config.openai_max_tokens == 1000
        assert config.openai_temperature == 0.3
        assert config.max_image_size == 2048
        assert config.image_quality == "high"
        assert config.enable_vision_analysis is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            openai_model="gpt-4o-mini",
            openai_max_tokens=500,
            openai_temperature=0.5,
            max_image_size=1024,
            image_quality="low",
        )

        assert config.openai_api_key == "test-key"
        assert config.openai_model == "gpt-4o-mini"
        assert config.openai_max_tokens == 500
        assert config.openai_temperature == 0.5
        assert config.max_image_size == 1024
        assert config.image_quality == "low"

    def test_config_reads_env_var(self):
        """Test that config reads OPENAI_API_KEY from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-test-key"}):
            config = DiagramAnalyzerConfig()
            assert config.openai_api_key == "env-test-key"


class TestDiagramAnalyzer:
    """Tests for DiagramAnalyzer class."""

    def test_analyzer_initialization_with_disabled_vision(self):
        """Test analyzer initialization with vision analysis disabled."""
        config = DiagramAnalyzerConfig(enable_vision_analysis=False)
        analyzer = DiagramAnalyzer(config)

        assert analyzer.config.enable_vision_analysis is False

    @patch('src.ocr.diagram_analyzer.OPENAI_AVAILABLE', True)
    def test_analyzer_initialization_without_api_key_raises_error(self):
        """Test that initializing analyzer without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            config = DiagramAnalyzerConfig(enable_vision_analysis=True)

            with pytest.raises(ValueError, match="OpenAI API key not provided"):
                DiagramAnalyzer(config)

    @patch('src.ocr.diagram_analyzer.OPENAI_AVAILABLE', False)
    def test_analyzer_initialization_without_openai_raises_error(self):
        """Test that initializing analyzer without openai package raises error."""
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )

        with pytest.raises(ImportError, match="OpenAI package not installed"):
            DiagramAnalyzer(config)

    def test_load_image_success(self):
        """Test successful image loading."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=False
        )
        analyzer = DiagramAnalyzer(config)

        image = analyzer._load_image(TRIANGLE_IMAGE)

        assert image is not None
        assert isinstance(image, np.ndarray)
        assert len(image.shape) == 3  # Should be BGR image

    def test_load_image_not_found(self):
        """Test loading non-existent image raises error."""
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=False
        )
        analyzer = DiagramAnalyzer(config)

        with pytest.raises(FileNotFoundError):
            analyzer._load_image("/nonexistent/image.jpg")

    def test_crop_diagram(self):
        """Test diagram cropping."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=False
        )
        analyzer = DiagramAnalyzer(config)

        # Load test image
        image = analyzer._load_image(TRIANGLE_IMAGE)
        original_height, original_width = image.shape[:2]

        # Create diagram region (crop to half size)
        diagram_region = DiagramRegion(
            bbox=[
                [10, 10],
                [original_width // 2, 10],
                [original_width // 2, original_height // 2],
                [10, original_height // 2]
            ],
            type="geometric_figure",
            description="test",
            shape="triangle"
        )

        # Crop image
        cropped = analyzer._crop_diagram(image, diagram_region)

        # Verify crop size is smaller than original
        assert cropped.shape[0] < original_height
        assert cropped.shape[1] < original_width

    def test_encode_image(self):
        """Test image encoding to base64."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=False
        )
        analyzer = DiagramAnalyzer(config)

        # Load test image
        image = analyzer._load_image(TRIANGLE_IMAGE)

        # Encode
        encoded = analyzer._encode_image(image)

        # Verify format
        assert isinstance(encoded, str)
        assert encoded.startswith("data:image/png;base64,")
        assert len(encoded) > 100  # Should have substantial content

    def test_encode_large_image_is_resized(self):
        """Test that large images are resized during encoding."""
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=False,
            max_image_size=100  # Very small to force resize
        )
        analyzer = DiagramAnalyzer(config)

        # Create large test image
        large_image = np.zeros((500, 500, 3), dtype=np.uint8)

        # Encode
        encoded = analyzer._encode_image(large_image)

        # Should succeed without error
        assert isinstance(encoded, str)
        assert encoded.startswith("data:image/png;base64,")

    def test_analyze_with_vision_disabled_returns_none(self):
        """Test that analyze returns None when vision is disabled."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        config = DiagramAnalyzerConfig(enable_vision_analysis=False)
        analyzer = DiagramAnalyzer(config)

        result = analyzer.analyze(TRIANGLE_IMAGE)

        assert result is None

    @patch('src.ocr.diagram_analyzer.OPENAI_AVAILABLE', True)
    @patch('src.ocr.diagram_analyzer.OpenAI')
    def test_analyze_with_mocked_api(self, mock_openai_class):
        """Test analyze with mocked OpenAI API."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "diagram_type": "right_triangle",
            "key_concepts": ["pythagorean_theorem"],
            "features": {
                "vertices": ["A", "B", "C"],
                "right_angle_at": "C",
                "labeled_sides": {"AB": "10", "AC": "6"}
            },
            "difficulty_indicators": {
                "has_labels": True,
                "requires_calculation": True,
                "complexity": "medium"
            }
        })

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Create analyzer
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        analyzer = DiagramAnalyzer(config)

        # Analyze
        result = analyzer.analyze(TRIANGLE_IMAGE)

        # Verify result
        assert result is not None
        assert isinstance(result, DiagramAnalysis)
        assert result.diagram_type == "right_triangle"
        assert "pythagorean_theorem" in result.key_concepts
        assert result.features["vertices"] == ["A", "B", "C"]
        assert result.difficulty_indicators["complexity"] == "medium"
        assert result.analysis_confidence == 0.85

        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()

    @patch('src.ocr.diagram_analyzer.OPENAI_AVAILABLE', True)
    @patch('src.ocr.diagram_analyzer.OpenAI')
    def test_analyze_with_diagram_region(self, mock_openai_class):
        """Test analyze with specific diagram region cropping."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "diagram_type": "triangle",
            "key_concepts": ["geometry"],
            "features": {"vertices": ["A", "B", "C"]},
            "difficulty_indicators": {"complexity": "simple"}
        })

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Create analyzer
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        analyzer = DiagramAnalyzer(config)

        # Create diagram region
        diagram_region = DiagramRegion(
            bbox=[[10, 10], [200, 10], [200, 200], [10, 200]],
            type="geometric_figure",
            description="triangle",
            shape="triangle"
        )

        # Analyze
        result = analyzer.analyze(TRIANGLE_IMAGE, diagram_region)

        # Verify result
        assert result is not None
        assert result.diagram_type == "triangle"

    @patch('src.ocr.diagram_analyzer.OPENAI_AVAILABLE', True)
    @patch('src.ocr.diagram_analyzer.OpenAI')
    def test_analyze_handles_api_error_gracefully(self, mock_openai_class):
        """Test that analyze handles API errors gracefully."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock API error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        # Create analyzer
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        analyzer = DiagramAnalyzer(config)

        # Analyze - should not raise, should return None
        result = analyzer.analyze(TRIANGLE_IMAGE)

        assert result is None

    @patch('src.ocr.diagram_analyzer.OPENAI_AVAILABLE', True)
    @patch('src.ocr.diagram_analyzer.OpenAI')
    def test_analyze_handles_json_with_markdown_code_blocks(self, mock_openai_class):
        """Test that analyze handles JSON wrapped in markdown code blocks."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock response with markdown code blocks
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """```json
{
  "diagram_type": "circle",
  "key_concepts": ["circle_properties"],
  "features": {"radius": "5"},
  "difficulty_indicators": {"complexity": "simple"}
}
```"""

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Create analyzer
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        analyzer = DiagramAnalyzer(config)

        # Analyze
        result = analyzer.analyze(TRIANGLE_IMAGE)

        # Should successfully parse
        assert result is not None
        assert result.diagram_type == "circle"


class TestConvenienceFunction:
    """Tests for convenience function."""

    def test_analyze_diagram_with_vision_disabled(self):
        """Test analyze_diagram convenience function with vision disabled."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        config = DiagramAnalyzerConfig(enable_vision_analysis=False)
        result = analyze_diagram(TRIANGLE_IMAGE, config=config)

        assert result is None

    @patch('src.ocr.diagram_analyzer.OPENAI_AVAILABLE', True)
    @patch('src.ocr.diagram_analyzer.OpenAI')
    def test_analyze_diagram_with_mocked_api(self, mock_openai_class):
        """Test analyze_diagram convenience function with mocked API."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "diagram_type": "triangle",
            "key_concepts": ["geometry"],
            "features": {"vertices": ["A", "B", "C"]},
            "difficulty_indicators": {"complexity": "simple"}
        })

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Analyze
        config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        result = analyze_diagram(TRIANGLE_IMAGE, config=config)

        # Verify result
        assert result is not None
        assert isinstance(result, DiagramAnalysis)
        assert result.diagram_type == "triangle"
