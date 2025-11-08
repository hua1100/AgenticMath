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


__all__ = [
    "create_problem_from_ocr",
    "ProblemCreator",
]
