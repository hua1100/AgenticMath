"""
Unit tests for image preprocessor module.
"""

import pytest
import cv2
import numpy as np
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont

from src.ocr.image_preprocessor import (
    PreprocessingConfig,
    detect_rotation_angle,
    rotate_image,
    apply_noise_reduction,
    apply_contrast_enhancement,
    preprocess_image,
    save_preprocessed_image,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image():
    """Create a simple test image with horizontal lines."""
    # Create white background
    image = np.ones((400, 600, 3), dtype=np.uint8) * 255

    # Draw some horizontal black lines (simulating text)
    for y in range(100, 300, 40):
        cv2.line(image, (50, y), (550, y), (0, 0, 0), 2)

    return image


@pytest.fixture
def rotated_image():
    """Create a test image rotated by 5 degrees."""
    # Create base image
    image = np.ones((400, 600, 3), dtype=np.uint8) * 255

    # Draw horizontal lines
    for y in range(100, 300, 40):
        cv2.line(image, (50, y), (550, y), (0, 0, 0), 2)

    # Rotate by 5 degrees
    center = (300, 200)
    rotation_matrix = cv2.getRotationMatrix2D(center, 5, 1.0)
    rotated = cv2.warpAffine(image, rotation_matrix, (600, 400))

    return rotated


@pytest.fixture
def noisy_image():
    """Create a test image with noise."""
    image = np.ones((400, 600, 3), dtype=np.uint8) * 255

    # Draw some lines
    for y in range(100, 300, 40):
        cv2.line(image, (50, y), (550, y), (0, 0, 0), 2)

    # Add Gaussian noise
    noise = np.random.normal(0, 25, image.shape).astype(np.uint8)
    noisy = cv2.add(image, noise)

    return noisy


@pytest.fixture
def low_contrast_image():
    """Create a test image with low contrast."""
    # Gray background instead of white
    image = np.ones((400, 600, 3), dtype=np.uint8) * 180

    # Draw gray lines instead of black
    for y in range(100, 300, 40):
        cv2.line(image, (50, y), (550, y), (100, 100, 100), 2)

    return image


@pytest.fixture
def sample_image_file(temp_dir, sample_image):
    """Save sample image to temporary file."""
    image_path = temp_dir / "sample.jpg"
    cv2.imwrite(str(image_path), sample_image)
    return image_path


class TestPreprocessingConfig:
    """Tests for PreprocessingConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PreprocessingConfig()

        assert config.auto_rotation is True
        assert config.noise_reduction is True
        assert config.contrast_enhancement is True
        assert config.rotation_tolerance == 15.0
        assert config.denoise_strength == 10

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PreprocessingConfig(
            auto_rotation=False, noise_reduction=True, contrast_enhancement=False, denoise_strength=20
        )

        assert config.auto_rotation is False
        assert config.noise_reduction is True
        assert config.contrast_enhancement is False
        assert config.denoise_strength == 20


class TestDetectRotationAngle:
    """Tests for detect_rotation_angle function."""

    def test_no_rotation(self, sample_image):
        """Test detection on non-rotated image."""
        angle = detect_rotation_angle(sample_image)

        # Should detect very small or zero rotation
        assert abs(angle) < 2.0

    def test_rotated_image(self, rotated_image):
        """Test detection on rotated image."""
        angle = detect_rotation_angle(rotated_image)

        # Should detect rotation close to 5 degrees
        # Allow some tolerance due to detection algorithm
        assert 3.0 <= abs(angle) <= 7.0

    def test_empty_image(self):
        """Test detection on empty/blank image."""
        blank = np.ones((400, 600, 3), dtype=np.uint8) * 255
        angle = detect_rotation_angle(blank)

        # Should return 0 when no lines detected
        assert angle == 0.0

    def test_grayscale_image(self, sample_image):
        """Test detection works on grayscale images."""
        gray = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)
        angle = detect_rotation_angle(gray)

        # Should work with grayscale
        assert isinstance(angle, float)
        assert abs(angle) < 2.0


class TestRotateImage:
    """Tests for rotate_image function."""

    def test_rotate_positive_angle(self, sample_image):
        """Test rotation by positive angle."""
        rotated = rotate_image(sample_image, 10.0)

        # Image should be rotated (dimensions may change)
        assert rotated.shape[0] != sample_image.shape[0] or rotated.shape[1] != sample_image.shape[1]

    def test_rotate_negative_angle(self, sample_image):
        """Test rotation by negative angle."""
        rotated = rotate_image(sample_image, -10.0)

        assert rotated is not None
        assert len(rotated.shape) == 3

    def test_rotate_zero_angle(self, sample_image):
        """Test rotation by zero angle (should return original)."""
        rotated = rotate_image(sample_image, 0.0)

        # Should return original image when angle is zero
        np.testing.assert_array_equal(rotated, sample_image)

    def test_rotate_small_angle_skipped(self, sample_image):
        """Test very small angles are skipped."""
        rotated = rotate_image(sample_image, 0.05)

        # Small angle should be skipped
        np.testing.assert_array_equal(rotated, sample_image)


class TestApplyNoiseReduction:
    """Tests for apply_noise_reduction function."""

    def test_denoise_color_image(self, noisy_image):
        """Test denoising on color image."""
        denoised = apply_noise_reduction(noisy_image, strength=10)

        assert denoised.shape == noisy_image.shape
        # Denoised image should have less variation
        assert np.std(denoised) < np.std(noisy_image)

    def test_denoise_grayscale_image(self, noisy_image):
        """Test denoising on grayscale image."""
        gray_noisy = cv2.cvtColor(noisy_image, cv2.COLOR_BGR2GRAY)
        denoised = apply_noise_reduction(gray_noisy, strength=10)

        assert denoised.shape == gray_noisy.shape
        assert len(denoised.shape) == 2  # Still grayscale

    def test_denoise_strength(self, noisy_image):
        """Test different denoising strengths."""
        weak = apply_noise_reduction(noisy_image, strength=5)
        strong = apply_noise_reduction(noisy_image, strength=20)

        # Strong denoising should be smoother
        assert np.std(strong) < np.std(weak)


class TestApplyContrastEnhancement:
    """Tests for apply_contrast_enhancement function."""

    def test_enhance_color_image(self, low_contrast_image):
        """Test contrast enhancement on color image."""
        enhanced = apply_contrast_enhancement(low_contrast_image, use_clahe=True)

        assert enhanced.shape == low_contrast_image.shape

        # Enhanced image should have wider value range
        original_range = np.max(low_contrast_image) - np.min(low_contrast_image)
        enhanced_range = np.max(enhanced) - np.min(enhanced)
        assert enhanced_range >= original_range

    def test_enhance_grayscale_image(self, low_contrast_image):
        """Test contrast enhancement on grayscale image."""
        gray = cv2.cvtColor(low_contrast_image, cv2.COLOR_BGR2GRAY)
        enhanced = apply_contrast_enhancement(gray, use_clahe=True)

        assert enhanced.shape == gray.shape
        assert len(enhanced.shape) == 2  # Still grayscale

    def test_clahe_vs_standard(self, low_contrast_image):
        """Test CLAHE vs standard histogram equalization."""
        clahe_enhanced = apply_contrast_enhancement(low_contrast_image, use_clahe=True)
        standard_enhanced = apply_contrast_enhancement(low_contrast_image, use_clahe=False)

        # Both should enhance contrast
        assert clahe_enhanced.shape == standard_enhanced.shape
        # Results will differ but both should be valid


class TestPreprocessImage:
    """Tests for preprocess_image function."""

    def test_preprocess_with_default_config(self, sample_image_file):
        """Test preprocessing with default configuration."""
        result = preprocess_image(sample_image_file)

        assert result["success"] is True
        assert "preprocessed_image" in result
        assert "preprocessing_applied" in result
        assert "processing_time_ms" in result

        # All default steps should be applied
        assert "rotation_corrected" in result["preprocessing_applied"] or result["rotation_angle"] == 0.0
        assert "noise_reduced" in result["preprocessing_applied"]
        assert "contrast_enhanced" in result["preprocessing_applied"]

    def test_preprocess_processing_time(self, sample_image_file):
        """Test that processing time is under 1 second."""
        result = preprocess_image(sample_image_file)

        # Should complete in less than 1000ms
        assert result["processing_time_ms"] < 1000

    def test_preprocess_rotation_only(self, sample_image_file):
        """Test preprocessing with only rotation enabled."""
        config = PreprocessingConfig(auto_rotation=True, noise_reduction=False, contrast_enhancement=False)

        result = preprocess_image(sample_image_file, config)

        assert result["success"] is True
        # Only rotation should be in applied steps (if rotation detected)
        assert "noise_reduced" not in result["preprocessing_applied"]
        assert "contrast_enhanced" not in result["preprocessing_applied"]

    def test_preprocess_no_rotation(self, sample_image_file):
        """Test preprocessing without rotation correction."""
        config = PreprocessingConfig(auto_rotation=False, noise_reduction=True, contrast_enhancement=True)

        result = preprocess_image(sample_image_file, config)

        assert "rotation_corrected" not in result["preprocessing_applied"]
        assert result["rotation_angle"] == 0.0

    def test_preprocess_nonexistent_file(self, temp_dir):
        """Test preprocessing with nonexistent file."""
        nonexistent = temp_dir / "nonexistent.jpg"

        with pytest.raises(FileNotFoundError):
            preprocess_image(nonexistent)

    def test_preprocess_invalid_file(self, temp_dir):
        """Test preprocessing with invalid image file."""
        invalid_file = temp_dir / "invalid.jpg"
        invalid_file.write_text("not an image")

        with pytest.raises(ValueError, match="Failed to load image"):
            preprocess_image(invalid_file)

    def test_preprocess_preserves_image_quality(self, sample_image_file):
        """Test that preprocessing doesn't destroy image."""
        result = preprocess_image(sample_image_file)

        image = result["preprocessed_image"]

        # Image should still be valid
        assert image is not None
        assert len(image.shape) == 3  # Color image
        assert image.shape[2] == 3  # 3 channels (BGR)
        assert image.dtype == np.uint8

    def test_preprocess_size_change(self, temp_dir):
        """Test that rotation may change image size."""
        # Create a rotated image
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255
        for y in range(100, 300, 40):
            cv2.line(image, (50, y), (550, y), (0, 0, 0), 2)

        # Rotate by 10 degrees
        center = (300, 200)
        rotation_matrix = cv2.getRotationMatrix2D(center, 10, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (600, 400))

        image_path = temp_dir / "rotated.jpg"
        cv2.imwrite(str(image_path), rotated)

        result = preprocess_image(image_path)

        # Size may change due to rotation correction
        original_size = result["original_size"]
        preprocessed_size = result["preprocessed_size"]

        assert isinstance(original_size, tuple)
        assert isinstance(preprocessed_size, tuple)


class TestSavePreprocessedImage:
    """Tests for save_preprocessed_image function."""

    def test_save_preprocessed_image(self, sample_image_file, temp_dir):
        """Test saving preprocessed image."""
        result = preprocess_image(sample_image_file)
        output_path = temp_dir / "preprocessed.jpg"

        save_preprocessed_image(result, output_path)

        # Verify file was created
        assert output_path.exists()

        # Verify it's a valid image
        loaded = cv2.imread(str(output_path))
        assert loaded is not None

    def test_save_creates_directory(self, sample_image_file, temp_dir):
        """Test that save creates output directory if needed."""
        result = preprocess_image(sample_image_file)
        output_path = temp_dir / "subdir" / "preprocessed.jpg"

        # Directory doesn't exist yet
        assert not output_path.parent.exists()

        save_preprocessed_image(result, output_path)

        # Directory should be created
        assert output_path.parent.exists()
        assert output_path.exists()


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_preprocessing_pipeline(self, temp_dir):
        """Test complete preprocessing pipeline."""
        # Create a realistic test image with text-like content
        image = np.ones((800, 1200, 3), dtype=np.uint8) * 240

        # Add some noise
        noise = np.random.normal(0, 15, image.shape).astype(np.int16)
        image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # Draw some lines (simulating text)
        for y in range(200, 600, 60):
            cv2.line(image, (100, y), (1100, y), (50, 50, 50), 3)

        # Rotate slightly
        center = (600, 400)
        rotation_matrix = cv2.getRotationMatrix2D(center, 3, 1.0)
        image = cv2.warpAffine(image, rotation_matrix, (1200, 800))

        # Save to file
        image_path = temp_dir / "test_image.jpg"
        cv2.imwrite(str(image_path), image)

        # Preprocess
        result = preprocess_image(image_path)

        # Verify results
        assert result["success"] is True
        assert result["processing_time_ms"] < 1000
        assert len(result["preprocessing_applied"]) >= 2  # At least 2 steps

        # Save preprocessed image
        output_path = temp_dir / "preprocessed.jpg"
        save_preprocessed_image(result, output_path)

        assert output_path.exists()

    def test_batch_preprocessing(self, temp_dir):
        """Test preprocessing multiple images."""
        # Create multiple test images
        image_paths = []
        for i in range(3):
            image = np.ones((400, 600, 3), dtype=np.uint8) * 255
            for y in range(100, 300, 40):
                cv2.line(image, (50, y), (550, y), (0, 0, 0), 2)

            path = temp_dir / f"image_{i}.jpg"
            cv2.imwrite(str(path), image)
            image_paths.append(path)

        # Preprocess all images
        results = []
        total_time = 0
        for path in image_paths:
            result = preprocess_image(path)
            results.append(result)
            total_time += result["processing_time_ms"]

        # Verify all succeeded
        assert all(r["success"] for r in results)

        # Average time should still be under 1 second
        avg_time = total_time / len(results)
        assert avg_time < 1000
