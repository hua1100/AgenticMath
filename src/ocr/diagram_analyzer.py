"""
Diagram analysis module for deep semantic understanding of mathematical diagrams.

This module provides functionality to:
1. Crop diagram regions from images
2. Use GPT-4 Vision to analyze diagram content
3. Extract structured information (type, concepts, features, difficulty)
4. Provide analysis only when diagrams are detected (cost optimization)
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import base64
import json
import os
from io import BytesIO
from dataclasses import dataclass
import time

# OpenAI imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # Make it available for mocking even when not installed

# Import detector types
from .diagram_detector import DiagramRegion


@dataclass
class DiagramAnalysis:
    """Represents the deep analysis of a diagram."""

    diagram_type: str
    key_concepts: List[str]
    features: Dict[str, Any]
    difficulty_indicators: Dict[str, Any]
    analysis_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching contract."""
        result = {
            "diagram_type": self.diagram_type,
            "key_concepts": self.key_concepts,
            "features": self.features,
            "difficulty_indicators": self.difficulty_indicators,
        }
        if self.analysis_confidence > 0:
            result["analysis_confidence"] = self.analysis_confidence
        return result


class DiagramAnalyzerConfig:
    """Configuration for diagram analysis."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o",
        openai_max_tokens: int = 1000,
        openai_temperature: float = 0.3,
        max_image_size: int = 2048,
        image_quality: str = "high",
        enable_vision_analysis: bool = True,
    ):
        """
        Initialize diagram analyzer configuration.

        Args:
            openai_api_key: OpenAI API key (if None, will use env var OPENAI_API_KEY)
            openai_model: Model to use for vision analysis (default: gpt-4o)
            openai_max_tokens: Maximum tokens for response
            openai_temperature: Temperature for generation (lower = more deterministic)
            max_image_size: Maximum image dimension (will resize if larger)
            image_quality: Image quality for encoding ("high" or "low")
            enable_vision_analysis: Enable Vision LLM analysis (if False, returns basic analysis)
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_model = openai_model
        self.openai_max_tokens = openai_max_tokens
        self.openai_temperature = openai_temperature
        self.max_image_size = max_image_size
        self.image_quality = image_quality
        self.enable_vision_analysis = enable_vision_analysis


class DiagramAnalyzer:
    """Analyzes mathematical diagrams using GPT-4 Vision."""

    # Vision analysis prompt template
    VISION_PROMPT = """請分析這個數學圖表，提供以下資訊：

1. **圖形類型**（diagram_type）：
   - 例如：right_triangle（直角三角形）、equilateral_triangle（等邊三角形）
   - isosceles_triangle（等腰三角形）、circle（圓形）、rectangle（矩形）
   - parabola（拋物線）、coordinate_plane（座標平面）等

2. **數學考點**（key_concepts）：
   - 例如：pythagorean_theorem（畢氏定理）、trigonometry（三角函數）
   - similarity（相似形）、congruence（全等）、circle_properties（圓的性質）等
   - 以英文關鍵字陣列形式提供

3. **圖表特徵**（features）：
   - vertices: 頂點標註（如 ["A", "B", "C"]）
   - labeled_sides: 已標註的邊長（如 {"AB": "10", "AC": "6"}）
   - labeled_angles: 已標註的角度（如 {"∠C": "90°"}）
   - unlabeled_sides: 未標註的邊（如 ["BC"]）
   - special_markers: 特殊標記（如 right_angle_at: "C"）
   - 其他相關特徵

4. **難度指標**（difficulty_indicators）：
   - has_labels: 是否有標註（boolean）
   - requires_calculation: 是否需要計算（boolean）
   - complexity: 複雜度（"simple", "medium", "complex"）
   - num_unknowns: 未知數數量（integer）

**重要**：請以 JSON 格式回答，不要包含任何其他文字。

範例輸出格式：
{
  "diagram_type": "right_triangle",
  "key_concepts": ["pythagorean_theorem", "trigonometry"],
  "features": {
    "vertices": ["A", "B", "C"],
    "right_angle_at": "C",
    "labeled_sides": {"AB": "10", "AC": "6"},
    "labeled_angles": {"∠C": "90°"},
    "unlabeled_sides": ["BC"]
  },
  "difficulty_indicators": {
    "has_labels": true,
    "requires_calculation": true,
    "complexity": "medium",
    "num_unknowns": 1
  }
}"""

    def __init__(self, config: Optional[DiagramAnalyzerConfig] = None):
        """
        Initialize diagram analyzer.

        Args:
            config: Configuration for diagram analysis
        """
        self.config = config or DiagramAnalyzerConfig()

        # Initialize OpenAI client if available
        if self.config.enable_vision_analysis:
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install openai>=1.10.0"
                )

            if not self.config.openai_api_key:
                raise ValueError(
                    "OpenAI API key not provided. "
                    "Set OPENAI_API_KEY environment variable or pass to config."
                )

            self.client = OpenAI(api_key=self.config.openai_api_key)

    def analyze(
        self,
        image_path: str | Path,
        diagram_region: Optional[DiagramRegion] = None
    ) -> Optional[DiagramAnalysis]:
        """
        Analyze a diagram using GPT-4 Vision.

        Args:
            image_path: Path to the image file
            diagram_region: Optional diagram region to crop (if None, uses full image)

        Returns:
            DiagramAnalysis object or None if analysis fails
        """
        if not self.config.enable_vision_analysis:
            return None

        start_time = time.time()

        # Load and crop image if region is specified
        image = self._load_image(image_path)

        if diagram_region:
            image = self._crop_diagram(image, diagram_region)

        # Encode image for API
        encoded_image = self._encode_image(image)

        # Call Vision API
        try:
            analysis_dict = self._call_vision_api(encoded_image)

            # Parse response
            analysis = DiagramAnalysis(
                diagram_type=analysis_dict.get("diagram_type", "unknown"),
                key_concepts=analysis_dict.get("key_concepts", []),
                features=analysis_dict.get("features", {}),
                difficulty_indicators=analysis_dict.get("difficulty_indicators", {}),
                analysis_confidence=0.85  # Default confidence for successful analysis
            )

            return analysis

        except Exception as e:
            # Log error but don't raise - allow processing to continue
            print(f"Warning: Diagram analysis failed: {e}")
            return None

    def _load_image(self, image_path: str | Path) -> np.ndarray:
        """
        Load image from path.

        Args:
            image_path: Path to image file

        Returns:
            Image as numpy array (BGR format)
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image = cv2.imread(str(image_path))

        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        return image

    def _crop_diagram(
        self,
        image: np.ndarray,
        diagram_region: DiagramRegion
    ) -> np.ndarray:
        """
        Crop diagram region from image.

        Args:
            image: Full image (BGR format)
            diagram_region: Diagram region with bbox

        Returns:
            Cropped image containing only the diagram
        """
        # Extract bbox coordinates
        # bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        bbox = diagram_region.bbox

        # Get min/max x and y coordinates
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]

        x_min = max(0, min(x_coords))
        y_min = max(0, min(y_coords))
        x_max = min(image.shape[1], max(x_coords))
        y_max = min(image.shape[0], max(y_coords))

        # Crop image
        cropped = image[y_min:y_max, x_min:x_max]

        return cropped

    def _encode_image(self, image: np.ndarray) -> str:
        """
        Encode image to base64 string for API.

        Args:
            image: Image as numpy array (BGR format)

        Returns:
            Base64-encoded image string with data URL prefix
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize if too large
        height, width = image_rgb.shape[:2]
        max_size = self.config.max_image_size

        if max(height, width) > max_size:
            scale = max_size / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image_rgb = cv2.resize(image_rgb, (new_width, new_height))

        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)

        # Encode to base64
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        return f"data:image/png;base64,{base64_image}"

    def _call_vision_api(self, encoded_image: str) -> Dict[str, Any]:
        """
        Call GPT-4 Vision API for diagram analysis.

        Args:
            encoded_image: Base64-encoded image with data URL prefix

        Returns:
            Parsed analysis dictionary
        """
        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.VISION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": encoded_image,
                                "detail": self.config.image_quality
                            }
                        }
                    ]
                }
            ],
            max_tokens=self.config.openai_max_tokens,
            temperature=self.config.openai_temperature,
        )

        # Extract response content
        content = response.choices[0].message.content

        # Parse JSON response
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        analysis = json.loads(content)

        return analysis


# Convenience function
def analyze_diagram(
    image_path: str | Path,
    diagram_region: Optional[DiagramRegion] = None,
    config: Optional[DiagramAnalyzerConfig] = None
) -> Optional[DiagramAnalysis]:
    """
    Analyze a diagram in an image (convenience function).

    Args:
        image_path: Path to image file
        diagram_region: Optional diagram region to crop
        config: Optional configuration

    Returns:
        DiagramAnalysis object or None if analysis fails
    """
    analyzer = DiagramAnalyzer(config)
    return analyzer.analyze(image_path, diagram_region)
