"""
Problem model for storing mathematical problems at any stage.
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

from src.storage.database import Base
from src.models.types import GUID


class MathDomain(str, enum.Enum):
    """Mathematical domains."""

    ALGEBRA = "algebra"
    GEOMETRY = "geometry"
    CALCULUS = "calculus"
    PROBABILITY = "probability"
    NUMBER_THEORY = "number_theory"
    COMBINATORICS = "combinatorics"
    OTHER = "other"


class ProblemSource(str, enum.Enum):
    """Problem source stage."""

    ORIGINAL = "original"
    REPHRASED = "rephrased"
    REVISED = "revised"


class SourceType(str, enum.Enum):
    """Problem input method."""

    OCR = "ocr"
    MANUAL_TEXT = "manual_text"


class Problem(Base):
    """
    Represents a mathematical problem at any stage (original/rephrased/revised).

    Attributes:
        id: Unique identifier
        content: Full problem statement
        domain: Mathematical domain
        competencies: Required concepts/methods (JSON array)
        baseline_difficulty: Difficulty level 1-5
        source: Stage (original/rephrased/revised)
        source_type: Input method (OCR/manual text)
        parent_id: Reference to parent Problem
        uploaded_image_id: Reference to UploadedImage if from OCR
        created_at: When problem was created
        extra_metadata: Additional properties (JSON)
    """

    __tablename__ = "problems"

    id = Column(GUID(), primary_key=True, default=uuid4, nullable=False)
    content = Column(String, nullable=False)
    domain = Column(SQLEnum(MathDomain), nullable=False, index=True)
    competencies = Column(JSON, nullable=False)  # List of strings
    baseline_difficulty = Column(Integer, nullable=False)
    source = Column(SQLEnum(ProblemSource), nullable=False, index=True)
    source_type = Column(SQLEnum(SourceType), nullable=False, index=True)
    parent_id = Column(
        GUID(), ForeignKey("problems.id", ondelete="SET NULL"), nullable=True, index=True
    )
    uploaded_image_id = Column(
        GUID(),
        ForeignKey("uploaded_images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word

    # Relationships
    parent = relationship("Problem", remote_side=[id], backref="children")
    uploaded_image = relationship("UploadedImage", foreign_keys=[uploaded_image_id])
    quality_assessments = relationship(
        "QualityAssessment", back_populates="problem", cascade="all, delete-orphan"
    )
    solutions = relationship("Solution", back_populates="problem", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Problem(id={self.id}, "
            f"source={self.source.value}, "
            f"domain={self.domain.value}, "
            f"content='{self.content[:50]}...')>"
        )
