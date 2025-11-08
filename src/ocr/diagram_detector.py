"""
Diagram detection module for identifying and describing geometric figures and charts in images.

This module provides functionality to:
1. Detect geometric shapes (triangles, circles, rectangles)
2. Identify chart/table regions using layout analysis
3. Generate descriptive text for detected diagrams
4. Return bounding boxes for all detected regions
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import cv2
import numpy as np
from dataclasses import dataclass
import time


@dataclass
class DiagramRegion:
    """Represents a detected diagram region."""

    bbox: List[List[int]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    type: str  # "geometric_figure", "chart", "table"
    description: str
    confidence: float = 0.0
    shape: Optional[str] = None  # "triangle", "circle", "rectangle", etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching contract."""
        result = {
            "bbox": self.bbox,
            "type": self.type,
            "description": self.description,
        }
        if self.confidence > 0:
            result["confidence"] = self.confidence
        if self.shape:
            result["shape"] = self.shape
        return result


class DiagramDetectorConfig:
    """Configuration for diagram detection."""

    def __init__(
        self,
        min_contour_area: int = 1000,
        approx_epsilon_ratio: float = 0.02,
        circle_circularity_threshold: float = 0.75,
        min_triangle_area: int = 500,
        min_rectangle_area: int = 800,
        detect_geometric_shapes: bool = True,
        detect_layout_regions: bool = False,  # 需要額外的模型
    ):
        """
        Initialize diagram detection configuration.

        Args:
            min_contour_area: Minimum contour area to consider
            approx_epsilon_ratio: Epsilon ratio for polygon approximation
            circle_circularity_threshold: Threshold for circle detection (0-1)
            min_triangle_area: Minimum area for triangle detection
            min_rectangle_area: Minimum area for rectangle detection
            detect_geometric_shapes: Enable geometric shape detection
            detect_layout_regions: Enable layout analysis (requires PP-Structure)
        """
        self.min_contour_area = min_contour_area
        self.approx_epsilon_ratio = approx_epsilon_ratio
        self.circle_circularity_threshold = circle_circularity_threshold
        self.min_triangle_area = min_triangle_area
        self.min_rectangle_area = min_rectangle_area
        self.detect_geometric_shapes = detect_geometric_shapes
        self.detect_layout_regions = detect_layout_regions


class DiagramDetector:
    """Detects and describes diagrams in images."""

    def __init__(self, config: Optional[DiagramDetectorConfig] = None):
        """
        Initialize diagram detector.

        Args:
            config: Configuration for diagram detection
        """
        self.config = config or DiagramDetectorConfig()

    def detect(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Detect diagrams in image.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with detection results:
            {
                "contains_diagram": bool,
                "diagram_description": str or None,
                "diagram_regions": [DiagramRegion, ...],
                "processing_time_ms": int,
                "detected_shapes": {"triangles": int, "circles": int, "rectangles": int}
            }
        """
        start_time = time.time()

        # Load image
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Detect diagram regions
        diagram_regions = []

        if self.config.detect_geometric_shapes:
            geometric_shapes = self._detect_geometric_shapes(image)
            diagram_regions.extend(geometric_shapes)

        # TODO: Layout analysis using PP-Structure (requires additional model)
        # if self.config.detect_layout_regions:
        #     layout_regions = self._detect_layout_regions(image)
        #     diagram_regions.extend(layout_regions)

        # Generate summary
        contains_diagram = len(diagram_regions) > 0
        diagram_description = self._generate_description(diagram_regions) if contains_diagram else None

        # Count detected shapes
        shape_counts = self._count_shapes(diagram_regions)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "contains_diagram": contains_diagram,
            "diagram_description": diagram_description,
            "diagram_regions": diagram_regions,
            "processing_time_ms": processing_time_ms,
            "detected_shapes": shape_counts,
        }

    def _detect_geometric_shapes(self, image: np.ndarray) -> List[DiagramRegion]:
        """
        Detect geometric shapes (triangles, circles, rectangles) in image.

        Args:
            image: Input image (BGR format)

        Returns:
            List of detected diagram regions
        """
        regions = []

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply binary threshold
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < self.config.min_contour_area:
                continue

            # Approximate polygon
            epsilon = self.config.approx_epsilon_ratio * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

            # Classify shape
            shape_info = self._classify_shape(approx, contour, area)

            if shape_info:
                region = DiagramRegion(
                    bbox=bbox,
                    type="geometric_figure",
                    description=shape_info["description"],
                    confidence=shape_info["confidence"],
                    shape=shape_info["shape"]
                )
                regions.append(region)

        return regions

    def _classify_shape(
        self,
        approx: np.ndarray,
        contour: np.ndarray,
        area: float
    ) -> Optional[Dict[str, Any]]:
        """
        Classify shape based on approximated polygon.

        Args:
            approx: Approximated polygon
            contour: Original contour
            area: Contour area

        Returns:
            Dictionary with shape info or None if not recognized
        """
        num_vertices = len(approx)

        # Triangle: 3 vertices
        if num_vertices == 3 and area >= self.config.min_triangle_area:
            return {
                "shape": "triangle",
                "description": "三角形",
                "confidence": 0.85
            }

        # Rectangle/Square: 4 vertices
        elif num_vertices == 4 and area >= self.config.min_rectangle_area:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h if h > 0 else 0

            if 0.95 <= aspect_ratio <= 1.05:
                return {
                    "shape": "square",
                    "description": "正方形",
                    "confidence": 0.88
                }
            else:
                return {
                    "shape": "rectangle",
                    "description": "矩形",
                    "confidence": 0.87
                }

        # Circle: many vertices + high circularity
        elif num_vertices > 6:
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0

            if circularity >= self.config.circle_circularity_threshold:
                return {
                    "shape": "circle",
                    "description": "圓形",
                    "confidence": 0.86
                }

        return None

    def _generate_description(self, regions: List[DiagramRegion]) -> str:
        """
        Generate text description for detected diagrams.

        Args:
            regions: List of detected diagram regions

        Returns:
            Text description of all diagrams
        """
        if not regions:
            return ""

        # Group by shape type
        shapes = {}
        for region in regions:
            shape = region.shape or "未知圖形"
            if shape not in shapes:
                shapes[shape] = 0
            shapes[shape] += 1

        # Generate description
        descriptions = []
        for shape, count in shapes.items():
            if count == 1:
                descriptions.append(f"包含{region.description}")
            else:
                descriptions.append(f"包含 {count} 個{region.description}")

        return "、".join(descriptions)

    def _count_shapes(self, regions: List[DiagramRegion]) -> Dict[str, int]:
        """
        Count detected shapes by type.

        Args:
            regions: List of detected diagram regions

        Returns:
            Dictionary with shape counts
        """
        counts = {
            "triangles": 0,
            "circles": 0,
            "rectangles": 0,
            "squares": 0,
            "other": 0,
        }

        for region in regions:
            shape = region.shape
            if shape == "triangle":
                counts["triangles"] += 1
            elif shape == "circle":
                counts["circles"] += 1
            elif shape == "rectangle":
                counts["rectangles"] += 1
            elif shape == "square":
                counts["squares"] += 1
            elif shape:
                counts["other"] += 1

        return counts


# Convenience function
def detect_diagrams(
    image_path: str | Path,
    config: Optional[DiagramDetectorConfig] = None
) -> Dict[str, Any]:
    """
    Detect diagrams in image (convenience function).

    Args:
        image_path: Path to image file
        config: Optional configuration

    Returns:
        Detection results dictionary
    """
    detector = DiagramDetector(config)
    return detector.detect(image_path)
