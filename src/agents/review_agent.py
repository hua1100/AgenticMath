"""
Review Agent for Quality Assessment of Mathematical Problems.

This agent evaluates rephrased math problems on three dimensions:
1. Clarity & Grammar (1-5)
2. Logical Coherence & Completeness (1-5)
3. Mathematical Validity & Solvability (1-5)

It provides detailed thought process, scores, and specific improvement suggestions.
"""

import logging
from typing import Optional
from datetime import datetime

from src.agents.llm_client import LLMClient
from src.prompts.review_prompt import create_review_prompt
from src.parsers.review_parser import ReviewParser, ReviewAgentOutput, ReviewParseError

logger = logging.getLogger(__name__)


class ReviewAgent:
    """
    Review Agent for quality assessment of mathematical problems.

    Evaluates problems on three dimensions:
    - Clarity & Grammar (1-5)
    - Logical Coherence & Completeness (1-5)
    - Mathematical Validity & Solvability (1-5)

    Example:
        >>> agent = ReviewAgent(llm_client=llm_client)
        >>> output = agent.review("A rectangular garden has length 3m more than twice its width...")
        >>> print(output.overall_score)
        4.3
        >>> print(output.suggestions)
        ["Add units to final answer", "Clarify if approximate solutions are acceptable"]
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Review Agent.

        Args:
            llm_client: LLM client for calling GPT-4
        """
        self.llm_client = llm_client
        self.parser = ReviewParser()
        logger.info("Review Agent initialized")

    def review(
        self,
        rephrased_question: str,
    ) -> ReviewAgentOutput:
        """
        Review a rephrased math problem for quality.

        Args:
            rephrased_question: The rephrased problem to review

        Returns:
            ReviewAgentOutput with scores and suggestions

        Raises:
            ValueError: If input validation fails
            ReviewParseError: If LLM output cannot be parsed
        """
        # Validate input
        self._validate_input(rephrased_question)

        # Create prompt
        prompt = create_review_prompt(rephrased_question=rephrased_question)

        logger.info("Calling LLM for review...")
        start_time = datetime.now()

        # Call LLM
        try:
            response = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for more consistent scoring
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        raw_response = response["content"]

        logger.info(f"LLM response received in {execution_time_ms}ms")

        # Parse output
        try:
            parsed_output = self.parser.parse(raw_response)
        except ReviewParseError as e:
            logger.error(f"Failed to parse LLM output: {e}")
            logger.debug(f"Raw LLM response:\n{raw_response}")
            raise

        # Validate output
        self._validate_output(parsed_output)

        logger.info(
            f"Review complete: Overall score {parsed_output.overall_score}/5.0, "
            f"{len(parsed_output.suggestions)} suggestions"
        )

        # TODO: Database logging
        # Note: AgentExecution model needs to be updated to support:
        # - output_data (JSON field for parsed output)
        # - prompt_template (text field)
        # - execution_time_ms (integer field)
        # Current focus: Core review functionality
        # Database integration to be completed in next iteration

        return parsed_output

    def _validate_input(self, rephrased_question: str) -> None:
        """
        Validate input parameters.

        Args:
            rephrased_question: The question to validate

        Raises:
            ValueError: If validation fails
        """
        if not rephrased_question or len(rephrased_question.strip()) < 20:
            raise ValueError(
                "rephrased_question must be at least 20 characters long"
            )

        # Check if question appears to be mathematical
        if not self._is_mathematical_question(rephrased_question):
            logger.warning(
                "Question does not appear to be mathematical - proceeding anyway"
            )

    def _is_mathematical_question(self, question: str) -> bool:
        """
        Check if question appears to be mathematical.

        Args:
            question: The question text

        Returns:
            True if appears to be a math question
        """
        math_keywords = [
            "calculate", "find", "solve", "determine", "compute",
            "what is", "how many", "prove", "simplify",
            "equation", "number", "angle", "area", "volume",
            "x", "y", "=", "+", "-", "*", "/",
            "求", "計算", "解", "證明", "方程"  # Chinese keywords
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in math_keywords)

    def _validate_output(self, output: ReviewAgentOutput) -> None:
        """
        Validate parsed output.

        Args:
            output: Parsed output to validate

        Raises:
            ValueError: If validation fails
        """
        # Check thought process is not empty
        if not output.thought_process or len(output.thought_process.strip()) < 10:
            raise ValueError("thought_process must be at least 10 characters")

        # Check scores are in valid range (Pydantic should handle this, but double-check)
        for score_name, score_value in [
            ("clarity_grammar_score", output.clarity_grammar_score),
            ("logical_coherence_score", output.logical_coherence_score),
            ("mathematical_validity_score", output.mathematical_validity_score),
            ("overall_score", output.overall_score),
        ]:
            if not (1.0 <= score_value <= 5.0):
                raise ValueError(
                    f"{score_name} {score_value} is out of valid range [1.0, 5.0]"
                )

        # Check overall score is reasonable (within 0.5 of average)
        avg_score = (
            output.clarity_grammar_score
            + output.logical_coherence_score
            + output.mathematical_validity_score
        ) / 3
        if abs(output.overall_score - avg_score) > 0.5:
            logger.warning(
                f"overall_score {output.overall_score} differs significantly from "
                f"average {avg_score:.2f}"
            )

        # Check suggestions are specific (if any)
        for i, suggestion in enumerate(output.suggestions):
            if len(suggestion.strip()) < 10:
                logger.warning(f"Suggestion {i+1} is too short: '{suggestion}'")

    def get_usage_stats(self):
        """
        Get LLM usage statistics.

        Returns:
            Dictionary with token usage and cost
        """
        return self.llm_client.get_usage_stats()
