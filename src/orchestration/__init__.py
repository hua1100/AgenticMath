"""
Orchestration module for coordinating multi-agent workflows.

This module provides:
- Problem creation from OCR results
- Problem rephrase orchestration
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


__all__ = [
    "create_problem_from_ocr",
    "ProblemCreator",
    "IterationManager",
    "IterationResult",
    "RephrasePipeline",
    "PipelineResult",
]
