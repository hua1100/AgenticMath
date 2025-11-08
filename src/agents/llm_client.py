"""
LLM Client for OpenAI GPT-4 with retry logic and cost tracking.

This module provides a robust client for interacting with OpenAI's GPT-4 models,
including exponential backoff retry, rate limiting handling, and token usage tracking.
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from openai import OpenAI, RateLimitError, APIError, APIConnectionError

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""

    model: str = "gpt-4o"  # or "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    max_retries: int = 3
    retry_base_delay: float = 1.0  # seconds
    retry_max_delay: float = 60.0  # seconds
    api_key: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")


class LLMClient:
    """
    OpenAI GPT-4 client with retry logic and token tracking.

    Features:
    - Exponential backoff retry for transient errors
    - Rate limit handling (429 errors)
    - Token usage tracking for cost management
    - Configurable temperature and max_tokens
    - Support for both gpt-4o and gpt-4-turbo models

    Example:
        >>> client = LLMClient()
        >>> response = client.chat_completion(
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )
        >>> print(response["content"])
        >>> print(f"Tokens used: {response['usage']}")
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM client.

        Args:
            config: LLM configuration. If None, uses defaults with API key from env.
        """
        self.config = config or LLMConfig()

        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key must be provided via config or OPENAI_API_KEY env var"
            )

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)

        # Track token usage
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0

        logger.info(f"Initialized LLM client with model: {self.config.model}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate chat completion with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override config temperature
            max_tokens: Override config max_tokens
            **kwargs: Additional arguments to pass to OpenAI API

        Returns:
            Dictionary with:
            {
                "content": str,  # Generated text
                "role": str,  # "assistant"
                "model": str,  # Model used
                "usage": {
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int
                },
                "finish_reason": str,  # "stop", "length", etc.
            }

        Raises:
            APIError: If all retries fail
        """
        temp = temperature if temperature is not None else self.config.temperature
        max_tok = max_tokens if max_tokens is not None else self.config.max_tokens

        attempt = 0
        last_exception = None

        while attempt <= self.config.max_retries:
            try:
                # Make API call
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=max_tok,
                    **kwargs,
                )

                # Extract response
                choice = response.choices[0]
                content = choice.message.content
                usage = response.usage

                # Track token usage
                total_tokens = usage.total_tokens
                self.total_tokens_used += total_tokens

                # Estimate cost (approximate pricing for gpt-4o/gpt-4-turbo)
                # GPT-4o: ~$5/1M prompt tokens, ~$15/1M completion tokens
                # GPT-4-turbo: ~$10/1M prompt tokens, ~$30/1M completion tokens
                if "gpt-4o" in self.config.model:
                    cost = (usage.prompt_tokens * 5 + usage.completion_tokens * 15) / 1_000_000
                else:  # gpt-4-turbo
                    cost = (usage.prompt_tokens * 10 + usage.completion_tokens * 30) / 1_000_000
                self.total_cost_usd += cost

                logger.info(
                    f"LLM call successful: {total_tokens} tokens, "
                    f"~${cost:.6f}, finish_reason={choice.finish_reason}"
                )

                return {
                    "content": content,
                    "role": "assistant",
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": total_tokens,
                    },
                    "finish_reason": choice.finish_reason,
                }

            except RateLimitError as e:
                # Rate limit hit (429), retry with exponential backoff
                last_exception = e
                attempt += 1

                if attempt > self.config.max_retries:
                    logger.error(f"Rate limit exceeded after {self.config.max_retries} retries")
                    raise

                delay = min(
                    self.config.retry_base_delay * (2 ** (attempt - 1)),
                    self.config.retry_max_delay,
                )
                logger.warning(
                    f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt}/{self.config.max_retries})"
                )
                time.sleep(delay)

            except (APIError, APIConnectionError) as e:
                # Transient API errors, retry
                last_exception = e
                attempt += 1

                if attempt > self.config.max_retries:
                    logger.error(f"API error after {self.config.max_retries} retries: {e}")
                    raise

                delay = min(
                    self.config.retry_base_delay * (2 ** (attempt - 1)),
                    self.config.retry_max_delay,
                )
                logger.warning(
                    f"API error, retrying in {delay:.1f}s (attempt {attempt}/{self.config.max_retries}): {e}"
                )
                time.sleep(delay)

            except Exception as e:
                # Non-retryable error, fail immediately
                logger.error(f"Non-retryable error: {e}")
                raise

        # Should not reach here, but just in case
        raise last_exception

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get token usage statistics.

        Returns:
            Dictionary with:
            {
                "total_tokens": int,
                "total_cost_usd": float,
                "model": str
            }
        """
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost_usd": self.total_cost_usd,
            "model": self.config.model,
        }

    def reset_usage_stats(self):
        """Reset token usage tracking."""
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        logger.info("Usage stats reset")
