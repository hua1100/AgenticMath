"""
Agent module for LLM-based problem generation agents.

This module provides:
- LLM client for OpenAI GPT-4
- Rephrase Agent for problem escalation
- Review Agent for quality assessment
- Revise Agent for problem refinement
"""

from .llm_client import LLMClient, LLMConfig

__all__ = [
    "LLMClient",
    "LLMConfig",
]
