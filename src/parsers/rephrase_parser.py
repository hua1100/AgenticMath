"""
Parser for Rephrase Agent structured output.

Parses the 3-stage format:
- Stage 1: Problem Deconstruction
- Stage 2: Escalation Protocol
- Stage 3: Finally Rewritten question
"""

import re
from typing import List
from pydantic import BaseModel, Field


class RephraseParseError(Exception):
    """Raised when Rephrase Agent output cannot be parsed."""
    pass


class RephraseAgentOutput(BaseModel):
    """Parsed output from Rephrase Agent."""

    stage1_problem_deconstruction: str = Field(..., description="Problem deconstruction analysis")
    stage2_escalation_protocol: str = Field(..., description="Escalation strategy")
    stage3_rewritten_question: str = Field(..., description="The rephrased problem")

    # Extracted from stage1
    identified_domain: str = Field(..., description="Math domain (Algebra/Geometry/etc.)")
    core_competencies: List[str] = Field(..., description="Required competencies")
    baseline_difficulty: int = Field(..., ge=1, le=5, description="Difficulty 1-5")

    # Extracted from stage2
    applied_dimensions: List[str] = Field(..., description="Applied escalation dimensions")


class RephraseParser:
    """Parser for Rephrase Agent's structured response."""

    @staticmethod
    def parse(raw_response: str) -> RephraseAgentOutput:
        """
        Parse Rephrase Agent's 3-stage structured response.

        Args:
            raw_response: Raw text from LLM

        Returns:
            Parsed RephraseAgentOutput

        Raises:
            RephraseParseError: If parsing fails
        """
        try:
            # Extract stage 1
            stage1_match = re.search(
                r"Stage 1 #Problem Deconstruction#:\s*\n(.*?)(?=Stage 2|$)",
                raw_response,
                re.DOTALL | re.IGNORECASE
            )
            if not stage1_match:
                raise RephraseParseError("Could not find Stage 1 #Problem Deconstruction#")
            stage1_text = stage1_match.group(1).strip()

            # Extract stage 2
            stage2_match = re.search(
                r"Stage 2 #Escalation Protocol#:\s*\n(.*?)(?=Stage 3|$)",
                raw_response,
                re.DOTALL | re.IGNORECASE
            )
            if not stage2_match:
                raise RephraseParseError("Could not find Stage 2 #Escalation Protocol#")
            stage2_text = stage2_match.group(1).strip()

            # Extract stage 3
            stage3_match = re.search(
                r"Stage 3 #Finally Rewritten question#:\s*\n(.*?)$",
                raw_response,
                re.DOTALL | re.IGNORECASE
            )
            if not stage3_match:
                raise RephraseParseError("Could not find Stage 3 #Finally Rewritten question#")
            stage3_text = stage3_match.group(1).strip()

            # Extract domain from stage1
            domain_match = re.search(r"Domain Identification:\s*(\w+)", stage1_text, re.IGNORECASE)
            identified_domain = domain_match.group(1) if domain_match else "Unknown"

            # Extract competencies from stage1
            competencies_match = re.search(
                r"Core Competencies:\s*(.*?)(?=\n|Baseline Difficulty|$)",
                stage1_text,
                re.DOTALL | re.IGNORECASE
            )
            if competencies_match:
                competencies_text = competencies_match.group(1).strip()
                # Split by comma or newline
                core_competencies = [
                    c.strip() for c in re.split(r'[,\n]', competencies_text)
                    if c.strip()
                ]
            else:
                core_competencies = ["mathematical_reasoning"]

            # Extract baseline difficulty from stage1
            difficulty_match = re.search(r"Baseline Difficulty:\s*(\d)", stage1_text, re.IGNORECASE)
            baseline_difficulty = int(difficulty_match.group(1)) if difficulty_match else 3

            # Extract applied dimensions from stage2
            # Look for numbered list items
            dimension_matches = re.findall(r"\d+\.\s+([^:]+):", stage2_text)
            applied_dimensions = [dim.strip() for dim in dimension_matches] if dimension_matches else []

            return RephraseAgentOutput(
                stage1_problem_deconstruction=stage1_text,
                stage2_escalation_protocol=stage2_text,
                stage3_rewritten_question=stage3_text,
                identified_domain=identified_domain,
                core_competencies=core_competencies,
                baseline_difficulty=baseline_difficulty,
                applied_dimensions=applied_dimensions
            )

        except Exception as e:
            if isinstance(e, RephraseParseError):
                raise
            raise RephraseParseError(f"Failed to parse rephrase output: {str(e)}") from e


def is_valid_mathematical_problem(question: str) -> bool:
    """
    Check if question is a valid mathematical problem.

    Args:
        question: The question text

    Returns:
        True if appears to be a math problem
    """
    math_keywords = [
        "calculate", "find", "solve", "determine", "compute",
        "what is", "how many", "prove", "simplify",
        "x", "y", "equation", "number", "angle", "area", "volume",
        "求", "計算", "解", "證明"  # Chinese keywords
    ]
    return any(keyword in question.lower() for keyword in math_keywords)
