"""
UploadedImage model for storing photo upload and OCR results.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

from src.storage.database import Base


class ImageFormat(str, enum.Enum):
    """Supported image formats."""

    JPEG = "jpeg"
    PNG = "png"


class UploadedImage(Base):
    """
    Represents a photo uploaded by a student with OCR processing results.

    Attributes:
        id: Unique identifier
        file_path: Storage location of image file
        file_size: File size in bytes (max 10MB)
        file_format: Image format (JPEG or PNG)
        upload_timestamp: When photo was uploaded
        ocr_extracted_text: Text extracted by PaddleOCR
        ocr_confidence_score: Average confidence 0.0-1.0 from OCR
        contains_diagram: Whether diagram/chart was detected
        diagram_description: Description of detected diagram
        preprocessing_applied: List of preprocessing steps applied
        ocr_processing_time_ms: OCR processing time in milliseconds
        problem_id: Reference to Problem created from this image
        created_at: When record was created
    """

    __tablename__ = "uploaded_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    file_path = Column(String(500), nullable=False, unique=True, index=True)
    file_size = Column(Integer, nullable=False)
    file_format = Column(SQLEnum(ImageFormat), nullable=False)
    upload_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    ocr_extracted_text = Column(String, nullable=False)
    ocr_confidence_score = Column(Float, nullable=False, index=True)
    contains_diagram = Column(Boolean, nullable=False, default=False)
    diagram_description = Column(String(1000), nullable=True)
    preprocessing_applied = Column(JSON, nullable=False, default=list)
    ocr_processing_time_ms = Column(Integer, nullable=False)
    problem_id = Column(UUID(as_uuid=True), nullable=True)  # Will add FK later
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to Problem (one-to-one)
    # problem = relationship("Problem", back_populates="uploaded_image", uselist=False)

    def __repr__(self) -> str:
        return (
            f"<UploadedImage(id={self.id}, "
            f"file_path='{self.file_path}', "
            f"confidence={self.ocr_confidence_score:.2f})>"
        )
