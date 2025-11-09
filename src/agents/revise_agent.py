"""
Revise Agent for Mathematical Problem Improvement.

This agent improves rephrased math problems based on specific suggestions
from the Review Agent, addressing quality issues while preserving mathematical intent.
"""

import logging
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session

from src.agents.llm_client import LLMClient
from src.prompts.revise_prompt import create_revise_prompt
from src.parsers.revise_parser import (
    ReviseParser,
    ReviseAgentOutput,
    ReviseParseError,
    validate_mathematical_preservation,
    validate_revision_changes,
    validate_revision_length,
)
from src.models.agent_execution import AgentExecution, AgentType

logger = logging.getLogger(__name__)


class ReviseAgent:
    """
    Revise Agent for improving mathematical problems.

    Takes a rephrased question and specific improvement suggestions,
    then produces an improved version while preserving mathematical intent.

    Example:
        >>> agent = ReviseAgent(llm_client=llm_client)
        >>> output = agent.revise(
        ...     rephrased_question="A rectangular garden has length 3m more than twice width. Perimeter is 22m. Find width.",
        ...     suggestions=[
        ...         "Explicitly state answer format: 'Express as decimal rounded to 2 places'",
        ...         "Add units clarification for final answer"
        ...     ]
        ... )
        >>> print(output.revised_question)
        A rectangular garden has a length that is 3 meters more than twice its width.
        If the perimeter is 22 meters, find the width. Express your answer as a decimal
        rounded to two decimal places, with units.
    """

    def __init__(self, llm_client: LLMClient, db: Optional[Session] = None):
        """
        Initialize Revise Agent.

        Args:
            llm_client: LLM client for calling GPT-4
            db: Database session for logging. If None, logging is skipped.
        """
        self.llm_client = llm_client
        self.db = db
        self.parser = ReviseParser()
        logger.info("Revise Agent initialized")

    def revise(
        self,
        rephrased_question: str,
        suggestions: List[str],
    ) -> ReviseAgentOutput:
        """
        Revise a math problem based on improvement suggestions.

        Args:
            rephrased_question: The problem to improve
            suggestions: List of specific improvements from Review Agent

        Returns:
            ReviseAgentOutput with revised question and notes

        Raises:
            ValueError: If input validation fails
            ReviseParseError: If LLM output cannot be parsed
        """
        # Validate input
        self._validate_input(rephrased_question, suggestions)

        # Create prompt
        prompt = create_revise_prompt(
            rephrased_question=rephrased_question,
            suggestions=suggestions
        )

        logger.info(f"Calling LLM for revision with {len(suggestions)} suggestions...")
        start_time = datetime.now()

        # Call LLM
        try:
            response = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for consistent improvements
            )

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            raw_response = response["content"]

            logger.info(f"LLM response received in {execution_time_ms}ms")

            # Parse output
            parsed_output = self.parser.parse(raw_response)

            # Validate output
            self._validate_output(
                original=rephrased_question,
                revised=parsed_output.revised_question,
                notes=parsed_output.revision_notes
            )

            # Log to database if db session is available
            if self.db:
                execution_record = AgentExecution(
                    id=uuid4(),
                    agent_type=AgentType.REVISE,
                    session_id=None,  # Will be set by pipeline if part of a session
                    input_data={
                        "rephrased_question": rephrased_question,
                        "suggestions": suggestions,
                    },
                    output_data={
                        "revised_question": parsed_output.revised_question,
                        "revision_notes": parsed_output.revision_notes,
                    },
                    prompt_template=prompt,
                    raw_llm_response=raw_response,
                    execution_time_ms=execution_time_ms,
                    llm_model=response.get("model", "gpt-4o"),
                )
                self.db.add(execution_record)
                self.db.commit()

                logger.info(
                    f"Revise execution logged: {execution_record.id}, "
                    f"{execution_time_ms}ms"
                )

            logger.info(
                f"Revision complete: "
                f"question length {len(rephrased_question)} -> {len(parsed_output.revised_question)}, "
                f"notes length {len(parsed_output.revision_notes)}"
            )

            return parsed_output

        except ReviseParseError as e:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Failed to parse LLM output: {e}")
            logger.debug(f"Raw LLM response:\n{raw_response if 'raw_response' in locals() else 'N/A'}")

            # Log failure to database if available
            if self.db:
                try:
                    execution_record = AgentExecution(
                        id=uuid4(),
                        agent_type=AgentType.REVISE,
                        session_id=None,
                        input_data={
                            "rephrased_question": rephrased_question,
                            "suggestions": suggestions,
                        },
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
                        agent_type=AgentType.REVISE,
                        session_id=None,
                        input_data={
                            "rephrased_question": rephrased_question,
                            "suggestions": suggestions,
                        },
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

    def _validate_input(self, rephrased_question: str, suggestions: List[str]) -> None:
        """
        Validate input parameters.

        Args:
            rephrased_question: The question to validate
            suggestions: The suggestions to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate question
        if not rephrased_question or len(rephrased_question.strip()) < 20:
            raise ValueError(
                "rephrased_question must be at least 20 characters long"
            )

        # Validate suggestions
        if not suggestions or len(suggestions) == 0:
            raise ValueError(
                "suggestions must be a non-empty list (at least 1 suggestion)"
            )

        # Validate each suggestion is non-empty
        for i, suggestion in enumerate(suggestions):
            if not suggestion or len(suggestion.strip()) == 0:
                raise ValueError(
                    f"Suggestion {i+1} is empty - all suggestions must be non-empty strings"
                )

        logger.debug(
            f"Input validation passed: "
            f"question length={len(rephrased_question)}, "
            f"suggestions count={len(suggestions)}"
        )

    def _validate_output(
        self,
        original: str,
        revised: str,
        notes: str
    ) -> None:
        """
        Validate parsed output.

        Args:
            original: Original question
            revised: Revised question
            notes: Revision notes

        Raises:
            ValueError: If validation fails
        """
        # Check revised question is not empty
        if not revised or len(revised.strip()) == 0:
            raise ValueError("revised_question is empty")

        # Check that changes were made
        if not validate_revision_changes(original, revised):
            raise ValueError(
                "revised_question is identical to original - no improvements made"
            )

        # Check mathematical preservation
        if not validate_mathematical_preservation(original, revised):
            raise ValueError(
                "revised_question failed to preserve mathematical content - "
                "key numbers or mathematical keywords were removed"
            )

        # Check length change is reasonable
        if not validate_revision_length(original, revised, max_change_ratio=1.5):
            raise ValueError(
                "revised_question length changed by more than 150% - "
                "may have changed mathematical intent"
            )

        # Check revision notes are provided (warning only)
        if not notes or len(notes.strip()) < 20:
            logger.warning(
                f"revision_notes is very short ({len(notes)} chars) - "
                "should explain what was changed"
            )

        logger.debug("Output validation passed")

    def get_usage_stats(self):
        """
        Get LLM usage statistics.

        Returns:
            Dictionary with token usage and cost
        """
        return self.llm_client.get_usage_stats()
