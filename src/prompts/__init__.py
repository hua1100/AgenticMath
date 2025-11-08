"""
Prompt templates for LLM agents.
"""

from .rephrase_prompt import REPHRASE_PROMPT_TEMPLATE, create_rephrase_prompt

__all__ = [
    "REPHRASE_PROMPT_TEMPLATE",
    "create_rephrase_prompt",
]
