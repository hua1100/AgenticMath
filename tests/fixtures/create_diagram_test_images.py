#!/usr/bin/env python
"""
Generate test images with geometric shapes for diagram detection testing.
"""

from pathlib import Path
import cv2
import numpy as np


def create_triangle_image(save_path: Path):
    """Create image with a triangle."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255

    # Draw triangle
    pts = np.array([[200, 100], [350, 300], [50, 300]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], True, (0, 0, 0), 3)

    cv2.imwrite(str(save_path), img)
    print(f"✅ Created: {save_path.name}")


def create_circle_image(save_path: Path):
    """Create image with a circle."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255

    # Draw circle
    cv2.circle(img, (300, 200), 100, (0, 0, 0), 3)

    cv2.imwrite(str(save_path), img)
    print(f"✅ Created: {save_path.name}")


def create_rectangle_image(save_path: Path):
    """Create image with a rectangle."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255

    # Draw rectangle
    cv2.rectangle(img, (150, 100), (450, 300), (0, 0, 0), 3)

    cv2.imwrite(str(save_path), img)
    print(f"✅ Created: {save_path.name}")


def create_square_image(save_path: Path):
    """Create image with a square."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255

    # Draw square
    cv2.rectangle(img, (200, 100), (400, 300), (0, 0, 0), 3)

    cv2.imwrite(str(save_path), img)
    print(f"✅ Created: {save_path.name}")


def create_multiple_shapes_image(save_path: Path):
    """Create image with multiple geometric shapes."""
    img = np.ones((500, 700, 3), dtype=np.uint8) * 255

    # Draw triangle
    pts = np.array([[100, 80], [180, 180], [20, 180]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], True, (0, 0, 0), 2)

    # Draw circle
    cv2.circle(img, (350, 130), 60, (0, 0, 0), 2)

    # Draw rectangle
    cv2.rectangle(img, (500, 80), (650, 180), (0, 0, 0), 2)

    # Draw square
    cv2.rectangle(img, (100, 280), (200, 380), (0, 0, 0), 2)

    cv2.imwrite(str(save_path), img)
    print(f"✅ Created: {save_path.name}")


def create_math_diagram_image(save_path: Path):
    """Create image simulating a math problem with diagram and text."""
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255

    # Add text (simulated)
    cv2.putText(
        img,
        "Triangle ABC:",
        (50, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2
    )

    # Draw right triangle
    pts = np.array([[200, 150], [500, 150], [200, 450]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], True, (0, 0, 0), 3)

    # Add labels
    cv2.putText(img, "A", (180, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "B", (510, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "C", (180, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    # Add measurements
    cv2.putText(img, "a = 10", (320, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.putText(img, "b = 6", (140, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    cv2.imwrite(str(save_path), img)
    print(f"✅ Created: {save_path.name}")


def create_no_diagram_image(save_path: Path):
    """Create image with text but no diagrams."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255

    # Add only text
    cv2.putText(
        img,
        "This is a text only image",
        (50, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2
    )

    cv2.imwrite(str(save_path), img)
    print(f"✅ Created: {save_path.name}")


def main():
    """Generate all test images."""
    print("=" * 70)
    print("生成圖表檢測測試圖片")
    print("=" * 70)
    print()

    # Create output directory
    output_dir = Path(__file__).parent / "diagrams"
    output_dir.mkdir(exist_ok=True)

    # Generate test images
    create_triangle_image(output_dir / "triangle.jpg")
    create_circle_image(output_dir / "circle.jpg")
    create_rectangle_image(output_dir / "rectangle.jpg")
    create_square_image(output_dir / "square.jpg")
    create_multiple_shapes_image(output_dir / "multiple_shapes.jpg")
    create_math_diagram_image(output_dir / "math_diagram.jpg")
    create_no_diagram_image(output_dir / "no_diagram.jpg")

    print()
    print("=" * 70)
    print(f"✅ 已生成 7 個測試圖片到 {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
