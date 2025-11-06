"""
Image uploader with validation for photo uploads.

This module handles image file uploads, validates format and size,
and stores files in organized directory structure.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import BinaryIO, Dict, Any, Optional
from PIL import Image
import io

from src.models.uploaded_image import ImageFormat


# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Supported formats
ALLOWED_FORMATS = {
    "image/jpeg": ImageFormat.JPEG,
    "image/jpg": ImageFormat.JPEG,
    "image/png": ImageFormat.PNG,
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class ImageUploadError(Exception):
    """Base exception for image upload errors."""

    pass


class FileSizeError(ImageUploadError):
    """Raised when file size exceeds maximum."""

    pass


class FileFormatError(ImageUploadError):
    """Raised when file format is not supported."""

    pass


class FileValidationError(ImageUploadError):
    """Raised when file fails validation."""

    pass


def validate_file_size(file_size: int) -> None:
    """
    Validate that file size is within allowed limits.

    Args:
        file_size: Size of file in bytes

    Raises:
        FileSizeError: If file size exceeds maximum
    """
    if file_size <= 0:
        raise FileValidationError("File is empty")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise FileSizeError(
            f"File size {file_size / 1024 / 1024:.2f}MB exceeds maximum "
            f"{MAX_FILE_SIZE_MB}MB"
        )


def validate_file_format(filename: str, file_bytes: bytes) -> ImageFormat:
    """
    Validate that file is a supported image format.

    Args:
        filename: Original filename
        file_bytes: File content as bytes

    Returns:
        ImageFormat enum value (JPEG or PNG)

    Raises:
        FileFormatError: If format is not supported
        FileValidationError: If file is corrupted or invalid
    """
    # Check file extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileFormatError(
            f"File extension '{ext}' not supported. " f"Allowed: {ALLOWED_EXTENSIONS}"
        )

    # Verify file is actually an image using PIL
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()  # Verify it's a valid image

        # Map PIL format to our ImageFormat enum
        pil_format = image.format.lower()
        if pil_format == "jpeg" or pil_format == "jpg":
            return ImageFormat.JPEG
        elif pil_format == "png":
            return ImageFormat.PNG
        else:
            raise FileFormatError(f"Image format '{pil_format}' not supported")

    except Exception as e:
        raise FileValidationError(f"File validation failed: {str(e)}")


def generate_upload_path(file_format: ImageFormat) -> tuple[Path, str]:
    """
    Generate upload path with YYYY/MM directory structure and unique filename.

    Args:
        file_format: Image format (JPEG or PNG)

    Returns:
        Tuple of (full_path, relative_path)
        - full_path: Absolute path to save file
        - relative_path: Relative path for database storage
    """
    # Get current date for directory structure
    now = datetime.utcnow()
    year_month_dir = now.strftime("%Y/%m")

    # Generate unique filename
    unique_id = uuid4()
    extension = "jpg" if file_format == ImageFormat.JPEG else "png"
    filename = f"{unique_id}.{extension}"

    # Create full path
    upload_base = Path(UPLOAD_DIR)
    date_dir = upload_base / year_month_dir
    full_path = date_dir / filename

    # Relative path for database
    relative_path = f"{year_month_dir}/{filename}"

    return full_path, relative_path


def save_file(file_bytes: bytes, destination: Path) -> None:
    """
    Save file bytes to destination path.

    Args:
        file_bytes: File content as bytes
        destination: Full path to save file

    Raises:
        IOError: If file cannot be saved
    """
    # Create directory if it doesn't exist
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    try:
        with open(destination, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        raise IOError(f"Failed to save file: {str(e)}")


def upload_image(
    file_content: bytes | BinaryIO, filename: str, validate_only: bool = False
) -> Dict[str, Any]:
    """
    Upload and validate an image file.

    This function:
    1. Validates file format and size
    2. Generates unique filename with YYYY/MM directory structure
    3. Saves file to disk
    4. Returns upload metadata for database record creation

    Args:
        file_content: File content as bytes or file-like object
        filename: Original filename
        validate_only: If True, only validate without saving file

    Returns:
        Dictionary with upload result:
        {
            "success": True,
            "image_id": "uuid-string",
            "file_path": "2025/11/uuid.jpg",
            "file_size": 2458693,
            "file_format": "jpeg",
            "upload_timestamp": datetime,
            "message": "Image uploaded successfully"
        }

    Raises:
        ImageUploadError: If upload fails for any reason
        FileSizeError: If file size exceeds limit
        FileFormatError: If file format not supported
        FileValidationError: If file validation fails
    """
    # Convert file-like object to bytes if needed
    if isinstance(file_content, BinaryIO) or hasattr(file_content, "read"):
        file_bytes = file_content.read()
    else:
        file_bytes = file_content

    # Validate file size
    file_size = len(file_bytes)
    validate_file_size(file_size)

    # Validate file format
    file_format = validate_file_format(filename, file_bytes)

    # If validation-only mode, stop here
    if validate_only:
        return {
            "success": True,
            "validated": True,
            "file_size": file_size,
            "file_format": file_format.value,
            "message": "File validation passed",
        }

    # Generate upload path
    full_path, relative_path = generate_upload_path(file_format)

    # Save file
    try:
        save_file(file_bytes, full_path)
    except IOError as e:
        raise ImageUploadError(f"Failed to save file: {str(e)}")

    # Generate image_id
    image_id = str(uuid4())

    # Return upload metadata
    return {
        "success": True,
        "image_id": image_id,
        "file_path": relative_path,
        "full_path": str(full_path.absolute()),
        "file_size": file_size,
        "file_format": file_format.value,
        "upload_timestamp": datetime.utcnow(),
        "message": "Image uploaded successfully",
    }


def delete_image(file_path: str) -> bool:
    """
    Delete an uploaded image file.

    Args:
        file_path: Relative path to image file (e.g., "2025/11/uuid.jpg")

    Returns:
        True if file was deleted, False if file doesn't exist

    Raises:
        IOError: If file deletion fails
    """
    full_path = Path(UPLOAD_DIR) / file_path

    if not full_path.exists():
        return False

    try:
        full_path.unlink()
        return True
    except Exception as e:
        raise IOError(f"Failed to delete file: {str(e)}")


def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Get information about an uploaded file.

    Args:
        file_path: Relative path to image file

    Returns:
        Dictionary with file info, or None if file doesn't exist
    """
    full_path = Path(UPLOAD_DIR) / file_path

    if not full_path.exists():
        return None

    stat = full_path.stat()

    return {
        "file_path": file_path,
        "full_path": str(full_path.absolute()),
        "file_size": stat.st_size,
        "exists": True,
        "modified_time": datetime.fromtimestamp(stat.st_mtime),
    }
