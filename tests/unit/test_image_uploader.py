"""
Unit tests for image uploader module.
"""

import pytest
import os
import io
from pathlib import Path
from PIL import Image
from datetime import datetime

from src.ocr.image_uploader import (
    upload_image,
    validate_file_size,
    validate_file_format,
    generate_upload_path,
    delete_image,
    get_file_info,
    ImageUploadError,
    FileSizeError,
    FileFormatError,
    FileValidationError,
    ImageFormat,
    MAX_FILE_SIZE_BYTES,
)


@pytest.fixture
def sample_jpeg_bytes():
    """Create a sample JPEG image in memory."""
    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def sample_png_bytes():
    """Create a sample PNG image in memory."""
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def large_image_bytes():
    """Create a large image that exceeds size limit."""
    # Create large image with random noise (not compressible)
    import numpy as np

    # Create 11MB of random pixel data
    # 3000 x 3000 x 3 channels = 27,000,000 bytes (27MB uncompressed)
    random_pixels = np.random.randint(0, 256, (3000, 3000, 3), dtype=np.uint8)
    img = Image.fromarray(random_pixels, mode="RGB")
    buffer = io.BytesIO()
    # Use PNG to avoid JPEG compression
    img.save(buffer, format="PNG", compress_level=0)  # No compression
    return buffer.getvalue()


@pytest.fixture
def cleanup_uploads():
    """Cleanup test uploads after test."""
    yield
    # Cleanup logic can be added here if needed


class TestValidateFileSize:
    """Tests for validate_file_size function."""

    def test_valid_file_size(self):
        """Test validation passes for valid file size."""
        # Should not raise exception
        validate_file_size(1024)  # 1KB
        validate_file_size(5 * 1024 * 1024)  # 5MB

    def test_empty_file(self):
        """Test validation fails for empty file."""
        with pytest.raises(FileValidationError, match="File is empty"):
            validate_file_size(0)

    def test_negative_file_size(self):
        """Test validation fails for negative size."""
        with pytest.raises(FileValidationError, match="File is empty"):
            validate_file_size(-1)

    def test_oversized_file(self):
        """Test validation fails for file exceeding max size."""
        oversized = MAX_FILE_SIZE_BYTES + 1
        with pytest.raises(FileSizeError, match="exceeds maximum"):
            validate_file_size(oversized)


class TestValidateFileFormat:
    """Tests for validate_file_format function."""

    def test_valid_jpeg_format(self, sample_jpeg_bytes):
        """Test validation passes for valid JPEG."""
        format = validate_file_format("test.jpg", sample_jpeg_bytes)
        assert format == ImageFormat.JPEG

    def test_valid_jpeg_uppercase(self, sample_jpeg_bytes):
        """Test validation passes for .JPG extension."""
        format = validate_file_format("TEST.JPG", sample_jpeg_bytes)
        assert format == ImageFormat.JPEG

    def test_valid_png_format(self, sample_png_bytes):
        """Test validation passes for valid PNG."""
        format = validate_file_format("test.png", sample_png_bytes)
        assert format == ImageFormat.PNG

    def test_invalid_extension(self, sample_jpeg_bytes):
        """Test validation fails for unsupported extension."""
        with pytest.raises(FileFormatError, match="not supported"):
            validate_file_format("test.gif", sample_jpeg_bytes)

    def test_corrupted_image(self):
        """Test validation fails for corrupted image data."""
        with pytest.raises(FileValidationError, match="validation failed"):
            validate_file_format("test.jpg", b"not an image")

    def test_extension_mismatch(self, sample_png_bytes):
        """Test validation catches extension/content mismatch."""
        # PNG content with .jpg extension - should still work as PIL reads actual format
        format = validate_file_format("test.jpg", sample_png_bytes)
        assert format == ImageFormat.PNG  # Actual format detected


class TestGenerateUploadPath:
    """Tests for generate_upload_path function."""

    def test_generates_unique_paths(self):
        """Test that each call generates unique filename."""
        path1, rel1 = generate_upload_path(ImageFormat.JPEG)
        path2, rel2 = generate_upload_path(ImageFormat.JPEG)

        assert path1 != path2
        assert rel1 != rel2

    def test_year_month_structure(self):
        """Test that path includes YYYY/MM structure."""
        path, rel_path = generate_upload_path(ImageFormat.JPEG)

        now = datetime.utcnow()
        expected_prefix = now.strftime("%Y/%m")

        assert expected_prefix in str(rel_path)

    def test_correct_extension_jpeg(self):
        """Test that JPEG files get .jpg extension."""
        path, rel_path = generate_upload_path(ImageFormat.JPEG)
        assert path.suffix == ".jpg"

    def test_correct_extension_png(self):
        """Test that PNG files get .png extension."""
        path, rel_path = generate_upload_path(ImageFormat.PNG)
        assert path.suffix == ".png"


class TestUploadImage:
    """Tests for upload_image function."""

    def test_successful_jpeg_upload(self, sample_jpeg_bytes, cleanup_uploads):
        """Test successful JPEG upload."""
        result = upload_image(sample_jpeg_bytes, "test.jpg")

        assert result["success"] is True
        assert result["image_id"] is not None
        assert result["file_format"] == "jpeg"
        assert result["file_size"] == len(sample_jpeg_bytes)
        assert "file_path" in result
        assert isinstance(result["upload_timestamp"], datetime)

        # Verify file was actually saved
        full_path = Path(result["full_path"])
        assert full_path.exists()

        # Cleanup
        full_path.unlink()

    def test_successful_png_upload(self, sample_png_bytes, cleanup_uploads):
        """Test successful PNG upload."""
        result = upload_image(sample_png_bytes, "test.png")

        assert result["success"] is True
        assert result["file_format"] == "png"

        # Cleanup
        Path(result["full_path"]).unlink()

    def test_upload_with_file_object(self, sample_jpeg_bytes, cleanup_uploads):
        """Test upload with file-like object."""
        file_obj = io.BytesIO(sample_jpeg_bytes)
        result = upload_image(file_obj, "test.jpg")

        assert result["success"] is True

        # Cleanup
        Path(result["full_path"]).unlink()

    def test_upload_oversized_file(self, large_image_bytes):
        """Test upload fails for oversized file."""
        with pytest.raises(FileSizeError):
            upload_image(large_image_bytes, "large.jpg")

    def test_upload_invalid_format(self):
        """Test upload fails for invalid format."""
        with pytest.raises(FileFormatError):
            upload_image(b"not an image", "test.gif")

    def test_validation_only_mode(self, sample_jpeg_bytes):
        """Test validation-only mode doesn't save file."""
        result = upload_image(sample_jpeg_bytes, "test.jpg", validate_only=True)

        assert result["success"] is True
        assert result["validated"] is True
        assert "image_id" not in result  # No file saved, so no ID
        assert "file_path" not in result


class TestDeleteImage:
    """Tests for delete_image function."""

    def test_delete_existing_file(self, sample_jpeg_bytes):
        """Test deleting an existing file."""
        # First upload a file
        result = upload_image(sample_jpeg_bytes, "test.jpg")
        file_path = result["file_path"]

        # Verify it exists
        full_path = Path(result["full_path"])
        assert full_path.exists()

        # Delete it
        deleted = delete_image(file_path)
        assert deleted is True
        assert not full_path.exists()

    def test_delete_nonexistent_file(self):
        """Test deleting a file that doesn't exist."""
        deleted = delete_image("2025/11/nonexistent.jpg")
        assert deleted is False


class TestGetFileInfo:
    """Tests for get_file_info function."""

    def test_get_info_existing_file(self, sample_jpeg_bytes):
        """Test getting info for existing file."""
        # Upload a file
        result = upload_image(sample_jpeg_bytes, "test.jpg")
        file_path = result["file_path"]

        # Get info
        info = get_file_info(file_path)

        assert info is not None
        assert info["file_path"] == file_path
        assert info["file_size"] == len(sample_jpeg_bytes)
        assert info["exists"] is True
        assert "modified_time" in info

        # Cleanup
        delete_image(file_path)

    def test_get_info_nonexistent_file(self):
        """Test getting info for nonexistent file."""
        info = get_file_info("2025/11/nonexistent.jpg")
        assert info is None


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_upload_lifecycle(self, sample_jpeg_bytes):
        """Test complete upload → info → delete lifecycle."""
        # Upload
        result = upload_image(sample_jpeg_bytes, "lifecycle_test.jpg")
        assert result["success"] is True

        file_path = result["file_path"]
        image_id = result["image_id"]

        # Get info
        info = get_file_info(file_path)
        assert info is not None
        assert info["file_size"] == len(sample_jpeg_bytes)

        # Delete
        deleted = delete_image(file_path)
        assert deleted is True

        # Verify deleted
        info_after_delete = get_file_info(file_path)
        assert info_after_delete is None

    def test_multiple_uploads_same_file(self, sample_jpeg_bytes):
        """Test uploading same file multiple times generates unique paths."""
        result1 = upload_image(sample_jpeg_bytes, "same.jpg")
        result2 = upload_image(sample_jpeg_bytes, "same.jpg")

        assert result1["file_path"] != result2["file_path"]
        assert result1["image_id"] != result2["image_id"]

        # Cleanup
        delete_image(result1["file_path"])
        delete_image(result2["file_path"])
