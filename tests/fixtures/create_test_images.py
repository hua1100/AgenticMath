"""
Create test images with Chinese text for OCR testing.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "images"
OUTPUT_DIR.mkdir(exist_ok=True)


def create_simple_text_image(text: str, filename: str, size=(800, 200)):
    """Create a simple white image with black text."""
    # Create white background
    image = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(image)

    # Use default font (no Chinese support, but good for ASCII)
    # For actual Chinese, would need to install Chinese font
    # For testing, we'll use simple ASCII text
    try:
        # Try to use a system font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        # Fall back to default
        font = ImageFont.load_default()

    # Draw text
    draw.text((50, 80), text, fill="black", font=font)

    # Save
    output_path = OUTPUT_DIR / filename
    image.save(output_path)
    print(f"Created: {output_path}")


def create_simple_math_problem():
    """Create a simple math problem image using ASCII."""
    text = "Solve for x: 2x + 3 = 11"
    create_simple_text_image(text, "simple_math.jpg")


def create_empty_image():
    """Create an empty white image (no text)."""
    image = Image.new("RGB", (800, 200), color="white")
    output_path = OUTPUT_DIR / "empty.jpg"
    image.save(output_path)
    print(f"Created: {output_path}")


def create_number_image():
    """Create an image with numbers."""
    text = "123 + 456 = 579"
    create_simple_text_image(text, "numbers.jpg")


def create_multi_line_image():
    """Create an image with multiple lines."""
    # Create white background
    image = Image.new("RGB", (800, 400), color="white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        font = ImageFont.load_default()

    lines = ["Line 1: x + y = 10", "Line 2: x - y = 2", "Line 3: Solve for x and y"]

    y_offset = 80
    for line in lines:
        draw.text((50, y_offset), line, fill="black", font=font)
        y_offset += 60

    output_path = OUTPUT_DIR / "multi_line.jpg"
    image.save(output_path)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    print("Creating test images...")
    create_simple_math_problem()
    create_empty_image()
    create_number_image()
    create_multi_line_image()
    print("Done!")
