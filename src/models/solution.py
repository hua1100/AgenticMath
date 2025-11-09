"""
Solution model for storing Solver Agent generated solutions.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from src.storage.database import Base
from src.models.types import GUID


class Solution(Base):
    """
    Represents a Solver Agent's generated solution with CoT reasoning.

    Attributes:
        id: Unique identifier
        problem_id: Reference to solved Problem
        thought_process: Detailed Chain-of-Thought reasoning
        final_answer: Concise final answer
        intermediate_steps: Parsed intermediate calculation steps (JSON array)
        created_at: When solution was generated
    """

    __tablename__ = "solutions"

    id = Column(GUID(), primary_key=True, default=uuid4, nullable=False)
    problem_id = Column(
        GUID(),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    thought_process = Column(String, nullable=False)
    final_answer = Column(String(500), nullable=False)
    intermediate_steps = Column(JSON, nullable=True)  # List of strings
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    problem = relationship("Problem", back_populates="solutions")

    def __repr__(self) -> str:
        return (
            f"<Solution(id={self.id}, "
            f"problem_id={self.problem_id}, "
            f"answer='{self.final_answer[:30]}...')>"
        )
