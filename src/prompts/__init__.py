"""
Prompt templates for LLM agents.
"""

from .rephrase_prompt import REPHRASE_PROMPT_TEMPLATE, create_rephrase_prompt
from .review_prompt import REVIEW_PROMPT_TEMPLATE, create_review_prompt

__all__ = [
    "REPHRASE_PROMPT_TEMPLATE",
    "create_rephrase_prompt",
    "REVIEW_PROMPT_TEMPLATE",
    "create_review_prompt",
]
