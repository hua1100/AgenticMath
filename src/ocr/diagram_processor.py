"""
Diagram processing module that combines detection and analysis.

This module provides a unified interface for:
1. Detecting diagrams in images (OpenCV - fast & free)
2. Analyzing diagrams when detected (GPT-4 Vision - only when needed)
3. Cost optimization: Only call Vision LLM when diagrams exist
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import time

from .diagram_detector import (
    DiagramDetector,
    DiagramDetectorConfig,
    DiagramRegion,
)
from .diagram_analyzer import (
    DiagramAnalyzer,
    DiagramAnalyzerConfig,
    DiagramAnalysis,
)


class DiagramProcessorConfig:
    """Configuration for diagram processing."""

    def __init__(
        self,
        # Detector config
        detector_config: Optional[DiagramDetectorConfig] = None,
        # Analyzer config
        analyzer_config: Optional[DiagramAnalyzerConfig] = None,
        # Processing options
        enable_deep_analysis: bool = True,
        analyze_all_regions: bool = False,  # If False, only analyze first/largest region
        min_regions_for_analysis: int = 1,  # Minimum diagram regions to trigger analysis
    ):
        """
        Initialize diagram processor configuration.

        Args:
            detector_config: Configuration for diagram detection
            analyzer_config: Configuration for diagram analysis
            enable_deep_analysis: Enable GPT-4 Vision analysis (if False, detection only)
            analyze_all_regions: Analyze all detected regions or just first one
            min_regions_for_analysis: Minimum number of regions to trigger analysis
        """
        self.detector_config = detector_config or DiagramDetectorConfig()
        self.analyzer_config = analyzer_config or DiagramAnalyzerConfig()
        self.enable_deep_analysis = enable_deep_analysis
        self.analyze_all_regions = analyze_all_regions
        self.min_regions_for_analysis = min_regions_for_analysis


class DiagramProcessor:
    """
    Processes diagrams in images with two-stage approach:
    1. Fast detection using OpenCV
    2. Deep analysis using Vision LLM (only when diagrams detected)
    """

    def __init__(self, config: Optional[DiagramProcessorConfig] = None):
        """
        Initialize diagram processor.

        Args:
            config: Configuration for processing
        """
        self.config = config or DiagramProcessorConfig()

        # Initialize detector (always needed)
        self.detector = DiagramDetector(self.config.detector_config)

        # Initialize analyzer (only if deep analysis is enabled)
        self.analyzer = None
        if self.config.enable_deep_analysis:
            self.analyzer = DiagramAnalyzer(self.config.analyzer_config)

    def process(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Process image to detect and analyze diagrams.

        This implements the cost optimization strategy:
        1. Detect diagrams using OpenCV (free, fast)
        2. Only if diagrams detected, analyze using Vision LLM (paid, accurate)

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with detection and analysis results:
            {
                "contains_diagram": bool,
                "diagram_description": str or None,
                "diagram_regions": [DiagramRegion, ...],
                "diagram_analysis": DiagramAnalysis or None,  # Only if deep analysis enabled
                "processing_time_ms": int,
                "detected_shapes": {"triangles": int, ...},
                "analysis_performed": bool,  # Whether Vision LLM was called
            }
        """
        start_time = time.time()

        # Stage 1: Detect diagrams using OpenCV
        detection_result = self.detector.detect(image_path)

        # Initialize result
        result = {
            "contains_diagram": detection_result["contains_diagram"],
            "diagram_description": detection_result["diagram_description"],
            "diagram_regions": detection_result["diagram_regions"],
            "detected_shapes": detection_result["detected_shapes"],
            "diagram_analysis": None,
            "analysis_performed": False,
        }

        # Stage 2: Deep analysis (only if diagrams detected and enabled)
        if (
            self.config.enable_deep_analysis
            and detection_result["contains_diagram"]
            and len(detection_result["diagram_regions"]) >= self.config.min_regions_for_analysis
        ):
            # Analyze diagram(s)
            if self.config.analyze_all_regions:
                # Analyze all regions
                analyses = []
                for region in detection_result["diagram_regions"]:
                    analysis = self.analyzer.analyze(image_path, region)
                    if analysis:
                        analyses.append(analysis)

                # Use first successful analysis
                result["diagram_analysis"] = analyses[0] if analyses else None
                result["analysis_performed"] = len(analyses) > 0

            else:
                # Analyze only first/largest region
                # For now, use first region (could be enhanced to find largest)
                first_region = detection_result["diagram_regions"][0]
                analysis = self.analyzer.analyze(image_path, first_region)

                result["diagram_analysis"] = analysis
                result["analysis_performed"] = analysis is not None

        # Calculate total processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        result["processing_time_ms"] = processing_time_ms

        return result

    def process_to_contract_format(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Process image and return result in OCR contract format.

        This formats the output to match the image-extraction-agent.md contract.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary matching the contract output format with:
            - contains_diagram: bool
            - diagram_description: str or None
            - diagram_regions: [dict, ...]
            - diagram_analysis: dict or None
        """
        result = self.process(image_path)

        # Convert to contract format
        contract_result = {
            "contains_diagram": result["contains_diagram"],
            "diagram_description": result["diagram_description"],
            "diagram_regions": [r.to_dict() for r in result["diagram_regions"]],
        }

        # Add diagram_analysis if available
        if result["diagram_analysis"]:
            contract_result["diagram_analysis"] = result["diagram_analysis"].to_dict()
        else:
            contract_result["diagram_analysis"] = None

        return contract_result


# Convenience function
def process_diagram(
    image_path: str | Path,
    config: Optional[DiagramProcessorConfig] = None
) -> Dict[str, Any]:
    """
    Process diagram in image (convenience function).

    Args:
        image_path: Path to image file
        config: Optional configuration

    Returns:
        Processing results dictionary
    """
    processor = DiagramProcessor(config)
    return processor.process(image_path)


def process_diagram_for_ocr(
    image_path: str | Path,
    enable_deep_analysis: bool = True,
    openai_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process diagram for OCR pipeline (convenience function).

    This is the main function to be used by the OCR pipeline.
    It returns results in the contract format.

    Args:
        image_path: Path to image file
        enable_deep_analysis: Whether to use Vision LLM analysis
        openai_api_key: OpenAI API key (optional, uses env var if not provided)

    Returns:
        Results in contract format with diagram_analysis
    """
    # Configure
    analyzer_config = DiagramAnalyzerConfig(
        openai_api_key=openai_api_key,
        enable_vision_analysis=enable_deep_analysis,
    )

    config = DiagramProcessorConfig(
        analyzer_config=analyzer_config,
        enable_deep_analysis=enable_deep_analysis,
    )

    # Process
    processor = DiagramProcessor(config)
    return processor.process_to_contract_format(image_path)
