"""
Parser for Review Agent structured output.

Parses the format:
- ###thought### - Analytical reasoning
- ###rating_score### - [score1, score2, score3]
- ###suggestions### - ###Specific improvement N###
"""

import re
import json
import logging
from typing import List
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ReviewParseError(Exception):
    """Raised when Review Agent output cannot be parsed."""
    pass


class ReviewAgentOutput(BaseModel):
    """Parsed output from Review Agent."""

    thought_process: str = Field(..., description="Analytical reasoning for each criterion")
    clarity_grammar_score: float = Field(..., ge=1.0, le=5.0, description="Clarity & Grammar score")
    logical_coherence_score: float = Field(..., ge=1.0, le=5.0, description="Logical Coherence score")
    mathematical_validity_score: float = Field(..., ge=1.0, le=5.0, description="Mathematical Validity score")
    overall_score: float = Field(..., ge=1.0, le=5.0, description="Overall average score")
    suggestions: List[str] = Field(default_factory=list, description="Specific improvement suggestions")

    @field_validator('overall_score')
    @classmethod
    def validate_overall_score(cls, v, info):
        """Ensure overall score is reasonable."""
        if not (1.0 <= v <= 5.0):
            raise ValueError(f"overall_score {v} must be between 1.0 and 5.0")
        return v


class ReviewParser:
    """Parser for Review Agent's structured response."""

    @staticmethod
    def parse(raw_response: str) -> ReviewAgentOutput:
        """
        Parse Review Agent's structured response.

        Args:
            raw_response: Raw text from LLM

        Returns:
            Parsed ReviewAgentOutput

        Raises:
            ReviewParseError: If parsing fails
        """
        try:
            # Extract thought process
            thought_match = re.search(
                r"###thought###\s*\n(.*?)(?=###rating_score###|$)",
                raw_response,
                re.DOTALL | re.IGNORECASE
            )
            if not thought_match:
                raise ReviewParseError("Could not find ###thought### section")
            thought_process = thought_match.group(1).strip()

            # Extract rating scores
            rating_match = re.search(
                r"###rating_score###\s*\n(\[.*?\])",
                raw_response,
                re.DOTALL | re.IGNORECASE
            )
            if not rating_match:
                raise ReviewParseError("Could not find ###rating_score### section")

            rating_text = rating_match.group(1)
            try:
                # Parse the list - handle both string numbers and floats
                scores = json.loads(rating_text)
                if len(scores) != 3:
                    raise ReviewParseError(f"Expected 3 scores, got {len(scores)}")

                clarity_score = float(scores[0])
                logical_score = float(scores[1])
                validity_score = float(scores[2])

                # Validate range with clamping
                clarity_score = ReviewParser._clamp_score(clarity_score, "clarity")
                logical_score = ReviewParser._clamp_score(logical_score, "logical")
                validity_score = ReviewParser._clamp_score(validity_score, "validity")

            except (json.JSONDecodeError, ValueError) as e:
                raise ReviewParseError(f"Failed to parse rating_score: {e}")

            # Calculate overall score (average)
            overall_score = round((clarity_score + logical_score + validity_score) / 3, 2)

            # Extract suggestions
            suggestions_match = re.search(
                r"###suggestions###\s*\n(.*?)$",
                raw_response,
                re.DOTALL | re.IGNORECASE
            )
            suggestions_text = suggestions_match.group(1).strip() if suggestions_match else ""

            # Parse individual suggestions (###Specific improvement N###)
            suggestion_items = re.findall(
                r"###Specific improvement \d+###\s*\n(.*?)(?=###Specific improvement \d+###|$)",
                suggestions_text,
                re.DOTALL | re.IGNORECASE
            )
            suggestions = [s.strip() for s in suggestion_items if s.strip()]

            return ReviewAgentOutput(
                thought_process=thought_process,
                clarity_grammar_score=clarity_score,
                logical_coherence_score=logical_score,
                mathematical_validity_score=validity_score,
                overall_score=overall_score,
                suggestions=suggestions
            )

        except Exception as e:
            if isinstance(e, ReviewParseError):
                raise
            raise ReviewParseError(f"Failed to parse review output: {str(e)}") from e

    @staticmethod
    def _clamp_score(score: float, name: str) -> float:
        """Clamp score to valid range [1.0, 5.0] with warning."""
        if score < 1.0 or score > 5.0:
            logger.warning(f"{name} score {score} out of range, clamping to [1.0, 5.0]")
            return max(1.0, min(5.0, score))
        return score


def is_valid_mathematical_question(question: str) -> bool:
    """
    Check if question appears to be mathematical.

    Args:
        question: The question text

    Returns:
        True if appears to be a math question
    """
    if len(question) < 20:
        return False

    math_keywords = [
        "calculate", "find", "solve", "determine", "compute",
        "what is", "how many", "prove", "simplify",
        "equation", "number", "angle", "area", "volume",
        "x", "y", "=", "+", "-", "*", "/",
        "求", "計算", "解", "證明", "方程"  # Chinese keywords
    ]
    return any(keyword in question.lower() for keyword in math_keywords)
