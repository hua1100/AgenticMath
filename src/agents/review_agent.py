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
from uuid import uuid4
from sqlalchemy.orm import Session

from src.agents.llm_client import LLMClient
from src.prompts.review_prompt import create_review_prompt
from src.parsers.review_parser import ReviewParser, ReviewAgentOutput, ReviewParseError
from src.models.agent_execution import AgentExecution, AgentType

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

    def __init__(self, llm_client: LLMClient, db: Optional[Session] = None):
        """
        Initialize Review Agent.

        Args:
            llm_client: LLM client for calling GPT-4
            db: Database session for logging. If None, logging is skipped.
        """
        self.llm_client = llm_client
        self.db = db
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

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            raw_response = response["content"]

            logger.info(f"LLM response received in {execution_time_ms}ms")

            # Parse output
            parsed_output = self.parser.parse(raw_response)

            # Validate output
            self._validate_output(parsed_output)

            # Log to database if db session is available
            if self.db:
                execution_record = AgentExecution(
                    id=uuid4(),
                    agent_type=AgentType.REVIEW,
                    session_id=None,  # Will be set by pipeline if part of a session
                    input_data={
                        "rephrased_question": rephrased_question,
                    },
                    output_data={
                        "clarity_grammar_score": parsed_output.clarity_grammar_score,
                        "logical_coherence_score": parsed_output.logical_coherence_score,
                        "mathematical_validity_score": parsed_output.mathematical_validity_score,
                        "overall_score": parsed_output.overall_score,
                        "thought_process": parsed_output.thought_process,
                        "suggestions": parsed_output.suggestions,
                    },
                    prompt_template=prompt,
                    raw_llm_response=raw_response,
                    execution_time_ms=execution_time_ms,
                    llm_model=response.get("model", "gpt-4o"),
                )
                self.db.add(execution_record)
                self.db.commit()

                logger.info(
                    f"Review execution logged: {execution_record.id}, "
                    f"{execution_time_ms}ms"
                )

            logger.info(
                f"Review complete: Overall score {parsed_output.overall_score}/5.0, "
                f"{len(parsed_output.suggestions)} suggestions"
            )

            return parsed_output

        except ReviewParseError as e:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Failed to parse LLM output: {e}")
            logger.debug(f"Raw LLM response:\n{raw_response if 'raw_response' in locals() else 'N/A'}")

            # Log failure to database if available
            if self.db:
                try:
                    execution_record = AgentExecution(
                        id=uuid4(),
                        agent_type=AgentType.REVIEW,
                        session_id=None,
                        input_data={"rephrased_question": rephrased_question},
                        output_data={"error": str(e)},
                        prompt_template=prompt,
                        raw_llm_response=raw_response if 'raw_response' in locals() else None,
                        execution_time_ms=execution_time_ms,
                        llm_model="gpt-4o",
                    )
                    self.db.add(execution_record)
                    self.db.commit()
                except Exception as log_error:
                    logger.warning(f"Failed to log error to database: {log_error}")
            raise

        except Exception as e:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"LLM call failed: {e}")

            # Log failure to database if available
            if self.db:
                try:
                    execution_record = AgentExecution(
                        id=uuid4(),
                        agent_type=AgentType.REVIEW,
                        session_id=None,
                        input_data={"rephrased_question": rephrased_question},
                        output_data={"error": str(e)},
                        prompt_template=prompt,
                        raw_llm_response=None,
                        execution_time_ms=execution_time_ms,
                        llm_model="gpt-4o",
                    )
                    self.db.add(execution_record)
                    self.db.commit()
                except Exception as log_error:
                    logger.warning(f"Failed to log error to database: {log_error}")
            raise

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
