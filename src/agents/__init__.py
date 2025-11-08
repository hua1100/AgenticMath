"""
Agent module for LLM-based problem generation agents.

This module provides:
- LLM client for OpenAI GPT-4
- Rephrase Agent for problem escalation
- Review Agent for quality assessment
- Revise Agent for problem refinement
"""

from .llm_client import LLMClient, LLMConfig
from .rephrase_agent import RephraseAgent, VALID_ESCALATION_DIMENSIONS
from .review_agent import ReviewAgent
from .revise_agent import ReviseAgent

__all__ = [
    "LLMClient",
    "LLMConfig",
    "RephraseAgent",
    "VALID_ESCALATION_DIMENSIONS",
    "ReviewAgent",
    "ReviseAgent",
]
