"""
RephraseSession model for tracking complete rephrase workflows.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

from src.storage.database import Base
from src.models.types import GUID


class SessionStatus(str, enum.Enum):
    """Session completion status."""

    SUCCESS = "success"
    MAX_ITERATIONS_EXCEEDED = "max_iterations_exceeded"
    ERROR = "error"


class RephraseSession(Base):
    """
    Represents a complete rephrase workflow from original to final problem.

    Attributes:
        id: Unique identifier
        original_problem_id: Reference to original Problem
        final_problem_id: Reference to final accepted Problem
        escalation_dimensions: Applied complexity dimensions (JSON array)
        iteration_count: Number of review-revise cycles performed
        quality_threshold: Threshold used (default 4.5)
        final_status: Completion status
        created_at: When session started
        completed_at: When session finished
    """

    __tablename__ = "rephrase_sessions"

    id = Column(GUID(), primary_key=True, default=uuid4, nullable=False)
    original_problem_id = Column(
        GUID(),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    final_problem_id = Column(
        GUID(), ForeignKey("problems.id", ondelete="SET NULL"), nullable=True
    )
    escalation_dimensions = Column(JSON, nullable=False)  # List of strings
    iteration_count = Column(Integer, nullable=False, default=0)
    quality_threshold = Column(Float, nullable=False, default=4.5)
    final_status = Column(SQLEnum(SessionStatus), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    original_problem = relationship("Problem", foreign_keys=[original_problem_id])
    final_problem = relationship("Problem", foreign_keys=[final_problem_id])
    agent_executions = relationship(
        "AgentExecution", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<RephraseSession(id={self.id}, "
            f"status={self.final_status.value}, "
            f"iterations={self.iteration_count})>"
        )
