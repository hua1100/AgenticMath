"""
OCR module for text and diagram extraction from images.

This module provides:
- Text extraction using PaddleOCR
- Diagram detection using OpenCV
- Diagram analysis using GPT-4 Vision
- Image preprocessing and uploading
"""

# Text extraction
from .text_extractor import (
    extract_text,
    TextRegion,
    OCRConfig,
)

# Diagram detection
from .diagram_detector import (
    detect_diagrams,
    DiagramDetector,
    DiagramDetectorConfig,
    DiagramRegion,
)

# Diagram analysis
from .diagram_analyzer import (
    analyze_diagram,
    DiagramAnalyzer,
    DiagramAnalyzerConfig,
    DiagramAnalysis,
)

# Integrated diagram processing (recommended)
from .diagram_processor import (
    process_diagram,
    process_diagram_for_ocr,
    DiagramProcessor,
    DiagramProcessorConfig,
)

# Complete OCR pipeline (recommended for production)
from .ocr_pipeline import (
    process_image,
    OCRPipeline,
    OCRPipelineConfig,
)

# Image preprocessing
from .image_preprocessor import (
    preprocess_image,
    PreprocessingConfig,
)

# Image uploading
from .image_uploader import (
    upload_image,
)


__all__ = [
    # Complete OCR pipeline (PRIMARY - recommended for production)
    "process_image",
    "OCRPipeline",
    "OCRPipelineConfig",
    # Text extraction
    "extract_text",
    "TextRegion",
    "OCRConfig",
    # Diagram detection
    "detect_diagrams",
    "DiagramDetector",
    "DiagramDetectorConfig",
    "DiagramRegion",
    # Diagram analysis
    "analyze_diagram",
    "DiagramAnalyzer",
    "DiagramAnalyzerConfig",
    "DiagramAnalysis",
    # Integrated diagram processing
    "process_diagram",
    "process_diagram_for_ocr",
    "DiagramProcessor",
    "DiagramProcessorConfig",
    # Image preprocessing
    "preprocess_image",
    "PreprocessingConfig",
    # Image uploading
    "upload_image",
]
