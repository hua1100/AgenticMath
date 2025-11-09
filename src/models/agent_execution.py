"""
AgentExecution model for storing agent invocation history for traceability.
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

from src.storage.database import Base
from src.models.types import GUID


class AgentType(str, enum.Enum):
    """Agent types in the system."""

    OCR = "ocr"
    REPHRASE = "rephrase"
    REVIEW = "review"
    REVISE = "revise"
    SOLVER = "solver"


class AgentExecution(Base):
    """
    Represents a single agent invocation for complete traceability.

    Attributes:
        id: Unique identifier
        agent_type: Type of agent (OCR/REPHRASE/REVIEW/REVISE/SOLVER)
        session_id: Reference to RephraseSession (null for standalone calls)
        input_data: Agent input (JSON)
        output_data: Agent output (JSON)
        prompt_template: Full prompt sent to LLM
        raw_llm_response: Unparsed LLM response (null for OCR)
        execution_time_ms: Time taken in milliseconds
        llm_model: LLM model used (null for OCR)
        created_at: When execution occurred
    """

    __tablename__ = "agent_executions"

    id = Column(GUID(), primary_key=True, default=uuid4, nullable=False)
    agent_type = Column(SQLEnum(AgentType), nullable=False, index=True)
    session_id = Column(
        GUID(),
        ForeignKey("rephrase_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    prompt_template = Column(String, nullable=False)
    raw_llm_response = Column(String, nullable=True)  # Null for OCR
    execution_time_ms = Column(Integer, nullable=False)
    llm_model = Column(String(100), nullable=True)  # Null for OCR
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("RephraseSession", back_populates="agent_executions")

    def __repr__(self) -> str:
        return (
            f"<AgentExecution(id={self.id}, "
            f"type={self.agent_type.value}, "
            f"time={self.execution_time_ms}ms)>"
        )
