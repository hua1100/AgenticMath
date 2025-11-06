"""
QualityAssessment model for storing Review Agent evaluations.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from src.storage.database import Base


class QualityAssessment(Base):
    """
    Represents a Review Agent's evaluation of a problem.

    Attributes:
        id: Unique identifier
        problem_id: Reference to evaluated Problem
        clarity_grammar_score: Score 1.0-5.0 for clarity & grammar
        logical_coherence_score: Score 1.0-5.0 for logical coherence
        mathematical_validity_score: Score 1.0-5.0 for math validity
        overall_score: Overall score 1.0-5.0
        thought_process: Detailed reasoning
        suggestions: List of improvement recommendations (JSON array)
        created_at: When assessment was performed
    """

    __tablename__ = "quality_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    problem_id = Column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clarity_grammar_score = Column(Float, nullable=False)
    logical_coherence_score = Column(Float, nullable=False)
    mathematical_validity_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False, index=True)
    thought_process = Column(String, nullable=False)
    suggestions = Column(JSON, nullable=False, default=list)  # List of strings
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    problem = relationship("Problem", back_populates="quality_assessments")

    def __repr__(self) -> str:
        return (
            f"<QualityAssessment(id={self.id}, "
            f"problem_id={self.problem_id}, "
            f"overall_score={self.overall_score:.2f})>"
        )
