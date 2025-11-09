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
            # Support both English and Chinese
            difficulty_match = re.search(
                r"(?:Baseline Difficulty|基準難度)[:：]\s*(\d)",
                stage1_text,
                re.IGNORECASE
            )
            baseline_difficulty = int(difficulty_match.group(1)) if difficulty_match else 3

            # Extract applied dimensions from stage2
            # Support multiple formats:
            # 1. "1. Multi-stage Transformation: description"
            # 2. "1. Multi-stage Transformation（多階段轉換）: description"
            # 3. "1. 多階段轉換: description"
            # 4. "1. Multi-stage Transformation" (no colon)

            # First try: numbered list with English names (may have Chinese in parentheses)
            dimension_matches = re.findall(
                r"\d+\.\s*([A-Za-z][A-Za-z\s\-]+?)(?:（[^）]+）)?[:：]",
                stage2_text
            )

            # If no matches, try without colon
            if not dimension_matches:
                dimension_matches = re.findall(
                    r"\d+\.\s*([A-Za-z][A-Za-z\s\-]+?)(?:（[^）]+）)?(?:\n|$)",
                    stage2_text
                )

            # If still no matches, try matching known dimension keywords
            if not dimension_matches:
                known_dimensions = [
                    "Multi-stage Transformation",
                    "Cross-domain Integration",
                    "Real-world Parameterization",
                    "Conditional Branching",
                    "Inverse Problem Design",
                    "Uncertainty Integration",
                    "Optimization Extension",
                ]
                dimension_matches = [
                    dim for dim in known_dimensions
                    if dim.lower() in stage2_text.lower()
                ]

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

    Supports both English and Traditional Chinese formats.

    Args:
        question: The question text

    Returns:
        True if appears to be a math problem
    """
    # English keywords
    english_keywords = [
        "calculate", "find", "solve", "determine", "compute",
        "what is", "how many", "prove", "simplify",
        "x", "y", "equation", "number", "angle", "area", "volume",
        "perimeter", "cost", "total", "maximum", "minimum",
    ]

    # Chinese keywords (Traditional Chinese)
    chinese_keywords = [
        "求", "計算", "解", "證明", "判斷", "確定",
        "多少", "幾何", "代數", "方程", "數字", "角度",
        "面積", "體積", "周長", "成本", "總", "最大", "最小",
        "長方形", "正方形", "三角形", "圓", "問",
    ]

    question_lower = question.lower()

    # Check English keywords
    if any(keyword in question_lower for keyword in english_keywords):
        return True

    # Check Chinese keywords (case-insensitive not needed for Chinese)
    if any(keyword in question for keyword in chinese_keywords):
        return True

    return False
