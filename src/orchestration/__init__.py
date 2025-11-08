"""
Orchestration module for coordinating multi-agent workflows.

This module provides:
- Problem creation from OCR results
- Problem rephrase orchestration (CrewAI-based and custom)
- Quality control workflows
- Agent coordination
"""

from .problem_creator import (
    create_problem_from_ocr,
    ProblemCreator,
)
from .iteration_manager import (
    IterationManager,
    IterationResult,
)
from .rephrase_pipeline import (
    RephrasePipeline,
    PipelineResult,
)
from .crewai_pipeline import (
    CrewAIPipeline,
    AgentToolkit,
)


__all__ = [
    "create_problem_from_ocr",
    "ProblemCreator",
    "IterationManager",
    "IterationResult",
    "RephrasePipeline",
    "PipelineResult",
    "CrewAIPipeline",
    "AgentToolkit",
]
