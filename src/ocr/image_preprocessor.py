"""
Image preprocessing pipeline for improving OCR accuracy.

This module provides image preprocessing functions including:
- Rotation correction (auto-detect and fix skewed images)
- Noise reduction (remove scan/photo artifacts)
- Contrast enhancement (improve text visibility)
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image
import time


class PreprocessingConfig:
    """Configuration for image preprocessing."""

    def __init__(
        self,
        auto_rotation: bool = True,
        noise_reduction: bool = True,
        contrast_enhancement: bool = True,
        rotation_tolerance: float = 15.0,
        denoise_strength: int = 10,
    ):
        """
        Initialize preprocessing configuration.

        Args:
            auto_rotation: Enable automatic rotation correction
            noise_reduction: Enable noise reduction
            contrast_enhancement: Enable contrast enhancement
            rotation_tolerance: Maximum rotation angle to correct (degrees)
            denoise_strength: Strength of denoising (1-30, higher = stronger)
        """
        self.auto_rotation = auto_rotation
        self.noise_reduction = noise_reduction
        self.contrast_enhancement = contrast_enhancement
        self.rotation_tolerance = rotation_tolerance
        self.denoise_strength = denoise_strength


def detect_rotation_angle(image: np.ndarray) -> float:
    """
    Detect rotation angle of text in image using Hough Line Transform.

    This function:
    1. Converts image to grayscale
    2. Applies edge detection
    3. Detects lines using Hough transform
    4. Calculates median angle of detected lines

    Args:
        image: Input image as numpy array (BGR or grayscale)

    Returns:
        Detected rotation angle in degrees (-15 to +15)
        Returns 0.0 if no rotation detected
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Apply edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines using Hough Line Transform
    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10
    )

    if lines is None or len(lines) == 0:
        return 0.0

    # Calculate angles of all detected lines
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # Calculate angle in degrees
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        angles.append(angle)

    # Get median angle (more robust than mean)
    median_angle = np.median(angles)

    # Normalize angle to -15 to +15 range
    # If angle is close to 90 or -90, it's likely vertical text
    if abs(median_angle) > 45:
        # Adjust to horizontal reference
        if median_angle > 0:
            median_angle = median_angle - 90
        else:
            median_angle = median_angle + 90

    # Limit to ±15 degrees
    median_angle = np.clip(median_angle, -15, 15)

    return median_angle


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    Rotate image by specified angle.

    Args:
        image: Input image as numpy array
        angle: Rotation angle in degrees (positive = counterclockwise)

    Returns:
        Rotated image
    """
    if abs(angle) < 0.1:  # Skip rotation if angle is negligible
        return image

    # Get image dimensions
    height, width = image.shape[:2]
    center = (width // 2, height // 2)

    # Calculate rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Calculate new bounding dimensions
    cos = np.abs(rotation_matrix[0, 0])
    sin = np.abs(rotation_matrix[0, 1])
    new_width = int((height * sin) + (width * cos))
    new_height = int((height * cos) + (width * sin))

    # Adjust rotation matrix for new dimensions
    rotation_matrix[0, 2] += (new_width / 2) - center[0]
    rotation_matrix[1, 2] += (new_height / 2) - center[1]

    # Perform rotation
    rotated = cv2.warpAffine(
        image, rotation_matrix, (new_width, new_height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    return rotated


def apply_noise_reduction(image: np.ndarray, strength: int = 10) -> np.ndarray:
    """
    Apply noise reduction to image.

    Uses Non-local Means Denoising which is effective for:
    - Photo noise from camera sensors
    - JPEG compression artifacts
    - Scan artifacts

    Args:
        image: Input image as numpy array (BGR or grayscale)
        strength: Denoising strength (1-30, higher = stronger but slower)

    Returns:
        Denoised image
    """
    if len(image.shape) == 3:
        # Color image - use fastNlMeansDenoisingColored
        denoised = cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h=strength,  # Filter strength for luminance
            hColor=strength,  # Filter strength for color
            templateWindowSize=7,
            searchWindowSize=21,
        )
    else:
        # Grayscale image - use fastNlMeansDenoising
        denoised = cv2.fastNlMeansDenoising(image, None, h=strength, templateWindowSize=7, searchWindowSize=21)

    return denoised


def apply_contrast_enhancement(image: np.ndarray, use_clahe: bool = True) -> np.ndarray:
    """
    Apply contrast enhancement to improve text visibility.

    Args:
        image: Input image as numpy array (BGR or grayscale)
        use_clahe: If True, use CLAHE (Contrast Limited Adaptive Histogram
                   Equalization), otherwise use standard histogram equalization

    Returns:
        Contrast-enhanced image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        # Convert to LAB color space for better results
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
    else:
        l_channel = image.copy()
        a_channel = None
        b_channel = None

    # Apply enhancement to luminance channel
    if use_clahe:
        # CLAHE - better for local contrast, prevents over-enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_l = clahe.apply(l_channel)
    else:
        # Standard histogram equalization
        enhanced_l = cv2.equalizeHist(l_channel)

    # Merge channels back if color image
    if len(image.shape) == 3:
        enhanced_lab = cv2.merge([enhanced_l, a_channel, b_channel])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    else:
        enhanced = enhanced_l

    return enhanced


def preprocess_image(
    image_path: str | Path, config: Optional[PreprocessingConfig] = None
) -> Dict[str, Any]:
    """
    Apply complete preprocessing pipeline to an image.

    This function applies the following steps (based on config):
    1. Load image
    2. Detect and correct rotation
    3. Apply noise reduction
    4. Enhance contrast
    5. Save preprocessing metadata

    Args:
        image_path: Path to input image file
        config: Preprocessing configuration. If None, uses defaults.

    Returns:
        Dictionary with preprocessing results:
        {
            "success": True,
            "preprocessed_image": np.ndarray,
            "preprocessing_applied": ["rotation_corrected", "noise_reduced", ...],
            "rotation_angle": 2.5,  # degrees
            "processing_time_ms": 850,
            "original_size": (1200, 800),
            "preprocessed_size": (1250, 820)
        }

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image cannot be loaded
    """
    if config is None:
        config = PreprocessingConfig()

    start_time = time.time()

    # Load image
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    original_size = (image.shape[1], image.shape[0])  # (width, height)
    preprocessing_applied: List[str] = []
    rotation_angle = 0.0

    # Step 1: Rotation correction
    if config.auto_rotation:
        rotation_angle = detect_rotation_angle(image)
        if abs(rotation_angle) > 0.1:  # Only rotate if angle is significant
            image = rotate_image(image, rotation_angle)
            preprocessing_applied.append("rotation_corrected")

    # Step 2: Noise reduction
    if config.noise_reduction:
        image = apply_noise_reduction(image, strength=config.denoise_strength)
        preprocessing_applied.append("noise_reduced")

    # Step 3: Contrast enhancement
    if config.contrast_enhancement:
        image = apply_contrast_enhancement(image, use_clahe=True)
        preprocessing_applied.append("contrast_enhanced")

    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    preprocessed_size = (image.shape[1], image.shape[0])  # (width, height)

    return {
        "success": True,
        "preprocessed_image": image,
        "preprocessing_applied": preprocessing_applied,
        "rotation_angle": float(rotation_angle),
        "processing_time_ms": processing_time_ms,
        "original_size": original_size,
        "preprocessed_size": preprocessed_size,
    }


def save_preprocessed_image(preprocessed_result: Dict[str, Any], output_path: str | Path) -> None:
    """
    Save preprocessed image to disk.

    Args:
        preprocessed_result: Result dictionary from preprocess_image()
        output_path: Path to save preprocessed image

    Raises:
        IOError: If image cannot be saved
    """
    image = preprocessed_result["preprocessed_image"]
    output_path = Path(output_path)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save image
    success = cv2.imwrite(str(output_path), image)
    if not success:
        raise IOError(f"Failed to save preprocessed image to: {output_path}")
