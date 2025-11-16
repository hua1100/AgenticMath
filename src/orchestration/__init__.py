"""
Orchestration module for coordinating multi-agent workflows.

This module provides:
- Problem creation from OCR results
- Problem rephrase orchestration (CrewAI-based and custom)
- Quality control workflows
- Solution generation pipeline
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
from .solution_pipeline import (
    SolutionPipeline,
    generate_solutions,
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
    "SolutionPipeline",
    "generate_solutions",
]
