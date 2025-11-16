"""
Parser for Solver Agent structured output.

Parses the format:
- ###thought### - Step-by-step reasoning process
- ###answer### - Final answer
"""

import re
import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SolverParseError(Exception):
    """Raised when Solver Agent output cannot be parsed."""
    pass


class SolverAgentOutput(BaseModel):
    """Parsed output from Solver Agent."""

    thought_process: str = Field(
        ...,
        description="Detailed step-by-step reasoning process with all intermediate calculations"
    )
    final_answer: str = Field(
        ...,
        description="Concise final answer (number, fraction, or expression)"
    )
    intermediate_steps: Optional[List[str]] = Field(
        default=None,
        description="Extracted intermediate calculation steps for structured access"
    )

    @field_validator('thought_process')
    @classmethod
    def validate_thought_process(cls, v):
        """Ensure thought process is non-empty."""
        if not v or len(v.strip()) < 10:
            raise ValueError("thought_process must be a detailed explanation (at least 10 characters)")
        return v

    @field_validator('final_answer')
    @classmethod
    def validate_final_answer(cls, v):
        """Ensure final answer is non-empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError("final_answer cannot be empty")
        return v


class SolverParser:
    """Parser for Solver Agent's structured response."""

    @staticmethod
    def parse(raw_response: str) -> SolverAgentOutput:
        """
        Parse Solver Agent's structured response.

        Expected format:
            ###thought###
            <step-by-step reasoning>

            ###answer###
            <final answer>

        Args:
            raw_response: Raw text from LLM

        Returns:
            Parsed SolverAgentOutput

        Raises:
            SolverParseError: If parsing fails

        Example:
            >>> response = "###thought###\\nStep 1: ...\\n###answer###\\n42"
            >>> output = SolverParser.parse(response)
            >>> print(output.final_answer)
            42
        """
        try:
            # Extract thought process
            thought_match = re.search(
                r"###thought###\s*\n(.*?)(?=###answer###|$)",
                raw_response,
                re.DOTALL | re.IGNORECASE
            )
            if not thought_match:
                raise SolverParseError("Could not find ###thought### section")
            thought_process = thought_match.group(1).strip()

            if not thought_process:
                raise SolverParseError("###thought### section is empty")

            # Extract final answer
            answer_match = re.search(
                r"###answer###\s*\n(.*?)$",
                raw_response,
                re.DOTALL | re.IGNORECASE
            )
            if not answer_match:
                raise SolverParseError("Could not find ###answer### section")
            final_answer = answer_match.group(1).strip()

            if not final_answer:
                raise SolverParseError("###answer### section is empty")

            # Extract intermediate steps (optional)
            intermediate_steps = SolverParser._extract_intermediate_steps(thought_process)

            return SolverAgentOutput(
                thought_process=thought_process,
                final_answer=final_answer,
                intermediate_steps=intermediate_steps
            )

        except SolverParseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing Solver output: {e}")
            logger.debug(f"Raw response:\n{raw_response}")
            raise SolverParseError(f"Failed to parse Solver Agent output: {e}")

    @staticmethod
    def _extract_intermediate_steps(thought_process: str) -> Optional[List[str]]:
        """
        Extract intermediate calculation steps from thought process.

        Looks for numbered steps (Step 1:, Step 2:, etc.) or other common patterns.

        Args:
            thought_process: The detailed reasoning text

        Returns:
            List of step descriptions, or None if no clear steps found

        Example:
            >>> thought = "Step 1: Define variables\\nStep 2: Solve equation"
            >>> steps = SolverParser._extract_intermediate_steps(thought)
            >>> len(steps)
            2
        """
        try:
            # Pattern 1: Numbered steps with "Step N:"
            step_pattern = r"(?:^|\n)(?:Step|步驟)\s*(\d+)[:.：](.*?)(?=(?:\n(?:Step|步驟)\s*\d+[:.：])|$)"
            matches = re.findall(step_pattern, thought_process, re.MULTILINE | re.DOTALL)

            if matches:
                steps = [f"Step {num}: {desc.strip()}" for num, desc in matches]
                return steps if len(steps) > 0 else None

            # Pattern 2: Bulleted list with dashes or asterisks
            bullet_pattern = r"(?:^|\n)\s*[-*•]\s*(.+?)(?=(?:\n\s*[-*•])|$)"
            matches = re.findall(bullet_pattern, thought_process, re.MULTILINE)

            if matches and len(matches) >= 2:
                return [m.strip() for m in matches if m.strip()]

            # Pattern 3: Lines with numbered format (1., 2., etc.)
            numbered_pattern = r"(?:^|\n)\s*(\d+)\.\s*(.+?)(?=(?:\n\s*\d+\.)|$)"
            matches = re.findall(numbered_pattern, thought_process, re.MULTILINE | re.DOTALL)

            if matches and len(matches) >= 2:
                return [f"{num}. {desc.strip()}" for num, desc in matches]

            # No clear step structure found
            return None

        except Exception as e:
            logger.warning(f"Failed to extract intermediate steps: {e}")
            return None


def parse_solver_output(raw_response: str) -> SolverAgentOutput:
    """
    Convenience function to parse Solver Agent output.

    Args:
        raw_response: Raw text from LLM

    Returns:
        Parsed SolverAgentOutput

    Raises:
        SolverParseError: If parsing fails
    """
    return SolverParser.parse(raw_response)
