"""
Unit tests for diagram processor module (integration of detector + analyzer).
"""

import pytest
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock

from src.ocr.diagram_processor import (
    DiagramProcessor,
    DiagramProcessorConfig,
    process_diagram,
    process_diagram_for_ocr,
)
from src.ocr.diagram_detector import DiagramRegion
from src.ocr.diagram_analyzer import DiagramAnalysis


# Test fixtures paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "diagrams"
TRIANGLE_IMAGE = FIXTURES_DIR / "triangle.jpg"
NO_DIAGRAM_IMAGE = FIXTURES_DIR / "no_diagram.jpg"


class TestDiagramProcessorConfig:
    """Tests for DiagramProcessorConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DiagramProcessorConfig()

        assert config.detector_config is not None
        assert config.analyzer_config is not None
        assert config.enable_deep_analysis is True
        assert config.analyze_all_regions is False
        assert config.min_regions_for_analysis == 1

    def test_custom_config(self):
        """Test custom configuration."""
        config = DiagramProcessorConfig(
            enable_deep_analysis=False,
            analyze_all_regions=True,
            min_regions_for_analysis=2,
        )

        assert config.enable_deep_analysis is False
        assert config.analyze_all_regions is True
        assert config.min_regions_for_analysis == 2


class TestDiagramProcessor:
    """Tests for DiagramProcessor class."""

    def test_processor_initialization_with_deep_analysis(self):
        """Test processor initialization with deep analysis enabled."""
        config = DiagramProcessorConfig(enable_deep_analysis=False)
        processor = DiagramProcessor(config)

        assert processor.detector is not None
        assert processor.analyzer is None  # Not initialized when disabled

    def test_processor_initialization_without_deep_analysis(self):
        """Test processor initialization without deep analysis."""
        # This will fail without API key, so disable vision analysis
        from src.ocr.diagram_analyzer import DiagramAnalyzerConfig

        analyzer_config = DiagramAnalyzerConfig(enable_vision_analysis=False)
        config = DiagramProcessorConfig(
            analyzer_config=analyzer_config,
            enable_deep_analysis=False
        )
        processor = DiagramProcessor(config)

        assert processor.detector is not None
        assert processor.analyzer is None

    def test_process_image_without_diagram(self):
        """Test processing image without diagram."""
        if not NO_DIAGRAM_IMAGE.exists():
            pytest.skip("Test fixture not found")

        config = DiagramProcessorConfig(enable_deep_analysis=False)
        processor = DiagramProcessor(config)

        result = processor.process(NO_DIAGRAM_IMAGE)

        assert result["contains_diagram"] is False
        assert result["diagram_description"] is None
        assert len(result["diagram_regions"]) == 0
        assert result["diagram_analysis"] is None
        assert result["analysis_performed"] is False
        assert result["processing_time_ms"] > 0

    @patch('src.ocr.diagram_processor.DiagramDetector')
    def test_process_with_detection_only(self, mock_detector_class):
        """Test processing with detection only (no deep analysis)."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock detector response
        mock_detector = Mock()
        mock_detector.detect.return_value = {
            "contains_diagram": True,
            "diagram_description": "包含三角形",
            "diagram_regions": [
                DiagramRegion(
                    bbox=[[0, 0], [100, 0], [100, 100], [0, 100]],
                    type="geometric_figure",
                    description="三角形",
                    shape="triangle",
                    confidence=0.85,
                )
            ],
            "detected_shapes": {"triangles": 1, "circles": 0, "rectangles": 0},
            "processing_time_ms": 100,
        }
        mock_detector_class.return_value = mock_detector

        # Process with deep analysis disabled
        config = DiagramProcessorConfig(enable_deep_analysis=False)
        processor = DiagramProcessor(config)

        result = processor.process(TRIANGLE_IMAGE)

        # Verify detector was called
        mock_detector.detect.assert_called_once()

        # Verify result
        assert result["contains_diagram"] is True
        assert result["diagram_analysis"] is None
        assert result["analysis_performed"] is False

    @patch('src.ocr.diagram_processor.DiagramAnalyzer')
    @patch('src.ocr.diagram_processor.DiagramDetector')
    def test_process_with_deep_analysis(self, mock_detector_class, mock_analyzer_class):
        """Test processing with deep analysis enabled."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock detector response
        mock_detector = Mock()
        test_region = DiagramRegion(
            bbox=[[0, 0], [100, 0], [100, 100], [0, 100]],
            type="geometric_figure",
            description="三角形",
            shape="triangle",
            confidence=0.85,
        )
        mock_detector.detect.return_value = {
            "contains_diagram": True,
            "diagram_description": "包含三角形",
            "diagram_regions": [test_region],
            "detected_shapes": {"triangles": 1, "circles": 0, "rectangles": 0},
            "processing_time_ms": 100,
        }
        mock_detector_class.return_value = mock_detector

        # Mock analyzer response
        mock_analyzer = Mock()
        test_analysis = DiagramAnalysis(
            diagram_type="right_triangle",
            key_concepts=["pythagorean_theorem"],
            features={"vertices": ["A", "B", "C"]},
            difficulty_indicators={"complexity": "medium"},
            analysis_confidence=0.90,
        )
        mock_analyzer.analyze.return_value = test_analysis
        mock_analyzer_class.return_value = mock_analyzer

        # Process with deep analysis enabled
        from src.ocr.diagram_analyzer import DiagramAnalyzerConfig

        analyzer_config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        config = DiagramProcessorConfig(
            analyzer_config=analyzer_config,
            enable_deep_analysis=True,
        )
        processor = DiagramProcessor(config)

        result = processor.process(TRIANGLE_IMAGE)

        # Verify both detector and analyzer were called
        mock_detector.detect.assert_called_once()
        mock_analyzer.analyze.assert_called_once()

        # Verify result
        assert result["contains_diagram"] is True
        assert result["diagram_analysis"] is not None
        assert result["diagram_analysis"].diagram_type == "right_triangle"
        assert result["analysis_performed"] is True

    @patch('src.ocr.diagram_processor.DiagramAnalyzer')
    @patch('src.ocr.diagram_processor.DiagramDetector')
    def test_process_cost_optimization_no_diagrams(self, mock_detector_class, mock_analyzer_class):
        """Test that analyzer is NOT called when no diagrams detected (cost optimization)."""
        if not NO_DIAGRAM_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock detector response - NO diagrams
        mock_detector = Mock()
        mock_detector.detect.return_value = {
            "contains_diagram": False,
            "diagram_description": None,
            "diagram_regions": [],
            "detected_shapes": {"triangles": 0, "circles": 0, "rectangles": 0},
            "processing_time_ms": 100,
        }
        mock_detector_class.return_value = mock_detector

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Process
        from src.ocr.diagram_analyzer import DiagramAnalyzerConfig

        analyzer_config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        config = DiagramProcessorConfig(
            analyzer_config=analyzer_config,
            enable_deep_analysis=True,
        )
        processor = DiagramProcessor(config)

        result = processor.process(NO_DIAGRAM_IMAGE)

        # Verify detector was called but analyzer was NOT
        mock_detector.detect.assert_called_once()
        mock_analyzer.analyze.assert_not_called()  # KEY: No API call when no diagrams!

        # Verify result
        assert result["contains_diagram"] is False
        assert result["diagram_analysis"] is None
        assert result["analysis_performed"] is False

    @patch('src.ocr.diagram_processor.DiagramAnalyzer')
    @patch('src.ocr.diagram_processor.DiagramDetector')
    def test_process_with_min_regions_threshold(self, mock_detector_class, mock_analyzer_class):
        """Test that analyzer requires minimum number of regions."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock detector response - only 1 region
        mock_detector = Mock()
        test_region = DiagramRegion(
            bbox=[[0, 0], [100, 0], [100, 100], [0, 100]],
            type="geometric_figure",
            description="三角形",
            shape="triangle",
        )
        mock_detector.detect.return_value = {
            "contains_diagram": True,
            "diagram_description": "包含三角形",
            "diagram_regions": [test_region],  # Only 1 region
            "detected_shapes": {"triangles": 1},
            "processing_time_ms": 100,
        }
        mock_detector_class.return_value = mock_detector

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Process with min_regions_for_analysis = 2
        from src.ocr.diagram_analyzer import DiagramAnalyzerConfig

        analyzer_config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        config = DiagramProcessorConfig(
            analyzer_config=analyzer_config,
            enable_deep_analysis=True,
            min_regions_for_analysis=2,  # Require at least 2 regions
        )
        processor = DiagramProcessor(config)

        result = processor.process(TRIANGLE_IMAGE)

        # Analyzer should NOT be called (only 1 region, need 2)
        mock_analyzer.analyze.assert_not_called()

        # Verify result
        assert result["analysis_performed"] is False

    def test_process_to_contract_format(self):
        """Test processing to OCR contract format."""
        if not NO_DIAGRAM_IMAGE.exists():
            pytest.skip("Test fixture not found")

        config = DiagramProcessorConfig(enable_deep_analysis=False)
        processor = DiagramProcessor(config)

        result = processor.process_to_contract_format(NO_DIAGRAM_IMAGE)

        # Verify contract format
        assert "contains_diagram" in result
        assert "diagram_description" in result
        assert "diagram_regions" in result
        assert "diagram_analysis" in result

        # diagram_regions should be list of dicts (not DiagramRegion objects)
        assert isinstance(result["diagram_regions"], list)

    @patch('src.ocr.diagram_processor.DiagramAnalyzer')
    @patch('src.ocr.diagram_processor.DiagramDetector')
    def test_process_to_contract_format_with_analysis(self, mock_detector_class, mock_analyzer_class):
        """Test contract format includes diagram_analysis when available."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock detector
        mock_detector = Mock()
        test_region = DiagramRegion(
            bbox=[[0, 0], [100, 0], [100, 100], [0, 100]],
            type="geometric_figure",
            description="三角形",
            shape="triangle",
        )
        mock_detector.detect.return_value = {
            "contains_diagram": True,
            "diagram_description": "包含三角形",
            "diagram_regions": [test_region],
            "detected_shapes": {"triangles": 1},
            "processing_time_ms": 100,
        }
        mock_detector_class.return_value = mock_detector

        # Mock analyzer
        mock_analyzer = Mock()
        test_analysis = DiagramAnalysis(
            diagram_type="right_triangle",
            key_concepts=["pythagorean_theorem"],
            features={"vertices": ["A", "B", "C"]},
            difficulty_indicators={"complexity": "medium"},
        )
        mock_analyzer.analyze.return_value = test_analysis
        mock_analyzer_class.return_value = mock_analyzer

        # Process
        from src.ocr.diagram_analyzer import DiagramAnalyzerConfig

        analyzer_config = DiagramAnalyzerConfig(
            openai_api_key="test-key",
            enable_vision_analysis=True
        )
        config = DiagramProcessorConfig(
            analyzer_config=analyzer_config,
            enable_deep_analysis=True,
        )
        processor = DiagramProcessor(config)

        result = processor.process_to_contract_format(TRIANGLE_IMAGE)

        # Verify diagram_analysis is a dict (not DiagramAnalysis object)
        assert result["diagram_analysis"] is not None
        assert isinstance(result["diagram_analysis"], dict)
        assert result["diagram_analysis"]["diagram_type"] == "right_triangle"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_process_diagram_without_analysis(self):
        """Test process_diagram convenience function."""
        if not NO_DIAGRAM_IMAGE.exists():
            pytest.skip("Test fixture not found")

        config = DiagramProcessorConfig(enable_deep_analysis=False)
        result = process_diagram(NO_DIAGRAM_IMAGE, config=config)

        assert "contains_diagram" in result
        assert result["contains_diagram"] is False

    def test_process_diagram_for_ocr_without_analysis(self):
        """Test process_diagram_for_ocr with analysis disabled."""
        if not NO_DIAGRAM_IMAGE.exists():
            pytest.skip("Test fixture not found")

        result = process_diagram_for_ocr(
            NO_DIAGRAM_IMAGE,
            enable_deep_analysis=False
        )

        # Verify contract format
        assert "contains_diagram" in result
        assert "diagram_regions" in result
        assert "diagram_analysis" in result
        assert isinstance(result["diagram_regions"], list)

    @patch('src.ocr.diagram_processor.DiagramAnalyzer')
    @patch('src.ocr.diagram_processor.DiagramDetector')
    def test_process_diagram_for_ocr_with_analysis(self, mock_detector_class, mock_analyzer_class):
        """Test process_diagram_for_ocr with analysis enabled."""
        if not TRIANGLE_IMAGE.exists():
            pytest.skip("Test fixture not found")

        # Mock detector
        mock_detector = Mock()
        test_region = DiagramRegion(
            bbox=[[0, 0], [100, 0], [100, 100], [0, 100]],
            type="geometric_figure",
            description="三角形",
            shape="triangle",
        )
        mock_detector.detect.return_value = {
            "contains_diagram": True,
            "diagram_description": "包含三角形",
            "diagram_regions": [test_region],
            "detected_shapes": {"triangles": 1},
            "processing_time_ms": 100,
        }
        mock_detector_class.return_value = mock_detector

        # Mock analyzer
        mock_analyzer = Mock()
        test_analysis = DiagramAnalysis(
            diagram_type="triangle",
            key_concepts=["geometry"],
            features={"vertices": ["A", "B", "C"]},
            difficulty_indicators={"complexity": "simple"},
        )
        mock_analyzer.analyze.return_value = test_analysis
        mock_analyzer_class.return_value = mock_analyzer

        # Process
        result = process_diagram_for_ocr(
            TRIANGLE_IMAGE,
            enable_deep_analysis=True,
            openai_api_key="test-key"
        )

        # Verify result
        assert result["contains_diagram"] is True
        assert result["diagram_analysis"] is not None
        assert result["diagram_analysis"]["diagram_type"] == "triangle"
