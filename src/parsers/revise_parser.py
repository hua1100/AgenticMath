"""
Parser for Revise Agent structured output.

Parses LLM response in the format:
###revised_question###
<improved full question>

###revision_notes###
<Specific revision note>
"""

import re
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ReviseAgentOutput(BaseModel):
    """
    Structured output from Revise Agent.

    Attributes:
        revised_question: The improved question after applying suggestions
        revision_notes: Explanation of what was changed and why
    """
    revised_question: str = Field(..., min_length=1)
    revision_notes: str = Field(default="")


class ReviseParseError(Exception):
    """Raised when Revise Agent output cannot be parsed."""
    pass


class ReviseParser:
    """
    Parser for Revise Agent's structured output.

    Example:
        >>> raw_response = '''
        ... ###revised_question###
        ... A rectangular garden has a length that is 3 meters more than twice its width.
        ... If the perimeter is 22 meters, find the width. Express your answer as a decimal
        ... rounded to two decimal places.
        ...
        ... ###revision_notes###
        ... Added explicit answer format requirement to address clarity suggestion.
        ... Preserved all mathematical constraints.
        ... '''
        >>> parser = ReviseParser()
        >>> output = parser.parse(raw_response)
        >>> print(output.revised_question)
        A rectangular garden has a length that is 3 meters more than twice its width...
    """

    @staticmethod
    def parse(raw_response: str) -> ReviseAgentOutput:
        """
        Parse Revise Agent's structured response.

        Args:
            raw_response: Raw LLM output string

        Returns:
            ReviseAgentOutput with parsed fields

        Raises:
            ReviseParseError: If required sections are missing or malformed
        """
        if not raw_response or not raw_response.strip():
            raise ReviseParseError("Empty response received")

        # Extract revised_question section
        question_match = re.search(
            r"###revised_question###\s*\n(.*?)(?=###revision_notes###|$)",
            raw_response,
            re.DOTALL | re.IGNORECASE
        )

        if not question_match:
            raise ReviseParseError("Could not find ###revised_question### section")

        revised_question = question_match.group(1).strip()

        if not revised_question:
            raise ReviseParseError("revised_question section is empty")

        # Extract revision_notes section (optional)
        notes_match = re.search(
            r"###revision_notes###\s*\n(.*?)$",
            raw_response,
            re.DOTALL | re.IGNORECASE
        )

        revision_notes = notes_match.group(1).strip() if notes_match else ""

        logger.info(
            f"Successfully parsed revise output: "
            f"question length={len(revised_question)}, "
            f"notes length={len(revision_notes)}"
        )

        return ReviseAgentOutput(
            revised_question=revised_question,
            revision_notes=revision_notes
        )


def validate_mathematical_preservation(original: str, revised: str) -> bool:
    """
    Check that revision preserves mathematical content.

    Ensures that key mathematical elements (numbers, variables, keywords)
    are preserved in the revised question.

    Args:
        original: Original question
        revised: Revised question

    Returns:
        True if mathematical content is preserved, False otherwise

    Example:
        >>> original = "A rectangle has length 2w+3 and perimeter 22. Find w."
        >>> revised = "A rectangle has length that is 3 more than twice its width. Perimeter is 22 meters. Find the width."
        >>> validate_mathematical_preservation(original, revised)
        True
    """
    # Extract numbers from both
    original_numbers = set(re.findall(r'\d+(?:\.\d+)?', original))
    revised_numbers = set(re.findall(r'\d+(?:\.\d+)?', revised))

    # Numbers should be mostly preserved (allow small additions for clarification)
    removed_numbers = original_numbers - revised_numbers
    if len(removed_numbers) > 1:
        logger.warning(
            f"Revision removed multiple numbers: {removed_numbers}, "
            "may have changed mathematical intent"
        )
        return False

    # Mathematical keywords should be preserved
    math_keywords = [
        'find', 'calculate', 'solve', 'determine', 'compute',
        'prove', 'simplify', 'evaluate', 'derive',
        '求', '計算', '解', '證明', '化簡'  # Chinese keywords
    ]
    original_has_keywords = any(kw in original.lower() for kw in math_keywords)
    revised_has_keywords = any(kw in revised.lower() for kw in math_keywords)

    if original_has_keywords and not revised_has_keywords:
        logger.warning("Revision removed mathematical action verbs")
        return False

    return True


def validate_revision_changes(original: str, revised: str) -> bool:
    """
    Validate that the revision actually made changes.

    Args:
        original: Original question
        revised: Revised question

    Returns:
        True if changes were made, False if identical

    Example:
        >>> original = "Find the width."
        >>> revised = "Find the width of the rectangle."
        >>> validate_revision_changes(original, revised)
        True
    """
    # Basic check: strings should be different
    if original.strip() == revised.strip():
        logger.warning("Revision is identical to original")
        return False

    return True


def validate_revision_length(original: str, revised: str, max_change_ratio: float = 1.5) -> bool:
    """
    Validate that revision length is within acceptable range.

    Ensures revision doesn't drastically change problem length,
    which might indicate changed intent.

    Args:
        original: Original question
        revised: Revised question
        max_change_ratio: Maximum allowed length change ratio (default 1.5 = ±150%)

    Returns:
        True if length change is acceptable, False otherwise

    Example:
        >>> original = "A rectangle has length 2w+3 and perimeter 22. Find w."
        >>> revised = "A rectangle has length that is 3 more than twice its width. If the perimeter is 22 meters, find the width. Express your answer as a decimal."
        >>> validate_revision_length(original, revised)
        True
    """
    original_len = len(original)
    revised_len = len(revised)

    if original_len == 0:
        return revised_len > 0

    length_change_ratio = abs(revised_len - original_len) / original_len

    if length_change_ratio > max_change_ratio:
        logger.warning(
            f"Revision length changed by {length_change_ratio:.1%}, "
            f"exceeds max allowed {max_change_ratio:.0%}"
        )
        return False

    return True
