"""
Iteration Manager for Review-Revise Loop.

Orchestrates the iterative refinement of math problems through
repeated Review → Revise cycles until quality threshold is met
or maximum iterations are reached.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.agents.review_agent import ReviewAgent
from src.agents.revise_agent import ReviseAgent
from src.models.rephrase_session import SessionStatus
from src.models.quality_assessment import QualityAssessment

logger = logging.getLogger(__name__)


class IterationResult:
    """
    Result of Review-Revise iteration loop.

    Attributes:
        final_question: The final refined question
        final_score: Overall quality score of final question
        iteration_count: Number of iterations performed
        final_status: SUCCESS or MAX_ITERATIONS_EXCEEDED
        quality_assessments: List of all quality assessments performed
        revision_history: List of all revised questions
    """

    def __init__(
        self,
        final_question: str,
        final_score: float,
        iteration_count: int,
        final_status: SessionStatus,
        quality_assessments: List[Dict[str, Any]],
        revision_history: List[str],
    ):
        self.final_question = final_question
        self.final_score = final_score
        self.iteration_count = iteration_count
        self.final_status = final_status
        self.quality_assessments = quality_assessments
        self.revision_history = revision_history

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "final_question": self.final_question,
            "final_score": self.final_score,
            "iteration_count": self.iteration_count,
            "final_status": self.final_status.value,
            "quality_assessments": self.quality_assessments,
            "revision_history": self.revision_history,
        }


class IterationManager:
    """
    Manages Review-Revise iteration loop for problem quality improvement.

    Orchestrates iterative refinement by:
    1. Reviewing current question
    2. If score >= threshold: SUCCESS
    3. If score < threshold: Revise based on suggestions
    4. Repeat until threshold met or max iterations reached

    Example:
        >>> manager = IterationManager(
        ...     review_agent=review_agent,
        ...     revise_agent=revise_agent,
        ...     quality_threshold=4.5,
        ...     max_iterations=5
        ... )
        >>> result = manager.iterate_until_quality(
        ...     initial_question="A rectangular garden has length 3m more than twice width..."
        ... )
        >>> print(result.final_status)
        SessionStatus.SUCCESS
        >>> print(result.final_score)
        4.7
    """

    def __init__(
        self,
        review_agent: ReviewAgent,
        revise_agent: ReviseAgent,
        quality_threshold: float = 4.5,
        max_iterations: int = 5,
        db_session: Optional[Session] = None,
    ):
        """
        Initialize Iteration Manager.

        Args:
            review_agent: ReviewAgent for quality assessment
            revise_agent: ReviseAgent for problem improvement
            quality_threshold: Minimum acceptable score (default 4.5)
            max_iterations: Maximum iterations allowed (default 5)
            db_session: Optional database session for logging
        """
        self.review_agent = review_agent
        self.revise_agent = revise_agent
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
        self.db_session = db_session

        logger.info(
            f"IterationManager initialized: threshold={quality_threshold}, "
            f"max_iterations={max_iterations}"
        )

    def iterate_until_quality(
        self,
        initial_question: str,
        problem_id: Optional[str] = None,
    ) -> IterationResult:
        """
        Iterate Review → Revise loop until quality threshold met.

        Args:
            initial_question: Starting question (already rephrased)
            problem_id: Optional problem ID for database logging

        Returns:
            IterationResult with final question and metadata

        Raises:
            ValueError: If initial_question is invalid
        """
        if not initial_question or len(initial_question.strip()) < 20:
            raise ValueError("initial_question must be at least 20 characters")

        logger.info(
            f"Starting iteration loop: initial_question_length={len(initial_question)}"
        )

        current_question = initial_question
        iteration_count = 0
        quality_assessments: List[Dict[str, Any]] = []
        revision_history: List[str] = [initial_question]

        while iteration_count < self.max_iterations:
            iteration_count += 1
            logger.info(f"Iteration {iteration_count}/{self.max_iterations}")

            # Review current question
            try:
                review_output = self.review_agent.review(current_question)
            except Exception as e:
                logger.error(f"Review failed at iteration {iteration_count}: {e}")
                raise

            # Record quality assessment
            assessment_data = {
                "clarity_grammar_score": review_output.clarity_grammar_score,
                "logical_coherence_score": review_output.logical_coherence_score,
                "mathematical_validity_score": review_output.mathematical_validity_score,
                "overall_score": review_output.overall_score,
                "thought_process": review_output.thought_process,
                "suggestions": review_output.suggestions,
                "iteration": iteration_count,
            }
            quality_assessments.append(assessment_data)

            logger.info(
                f"Review complete: overall_score={review_output.overall_score:.2f}, "
                f"suggestions={len(review_output.suggestions)}"
            )

            # Save to database if session provided
            if self.db_session and problem_id:
                self._save_quality_assessment(
                    problem_id=problem_id,
                    review_output=review_output,
                )

            # Check if quality threshold met
            if review_output.overall_score >= self.quality_threshold:
                logger.info(
                    f"Quality threshold met: {review_output.overall_score:.2f} >= "
                    f"{self.quality_threshold}"
                )
                return IterationResult(
                    final_question=current_question,
                    final_score=review_output.overall_score,
                    iteration_count=iteration_count,
                    final_status=SessionStatus.SUCCESS,
                    quality_assessments=quality_assessments,
                    revision_history=revision_history,
                )

            # Check if we've reached max iterations
            if iteration_count >= self.max_iterations:
                logger.warning(
                    f"Max iterations reached: {iteration_count}/{self.max_iterations}, "
                    f"final_score={review_output.overall_score:.2f}"
                )
                return IterationResult(
                    final_question=current_question,
                    final_score=review_output.overall_score,
                    iteration_count=iteration_count,
                    final_status=SessionStatus.MAX_ITERATIONS_EXCEEDED,
                    quality_assessments=quality_assessments,
                    revision_history=revision_history,
                )

            # Revise question based on suggestions
            if not review_output.suggestions:
                logger.warning(
                    f"No suggestions provided at iteration {iteration_count}, "
                    "but score below threshold"
                )
                # If no suggestions but score is low, we can't improve further
                return IterationResult(
                    final_question=current_question,
                    final_score=review_output.overall_score,
                    iteration_count=iteration_count,
                    final_status=SessionStatus.MAX_ITERATIONS_EXCEEDED,
                    quality_assessments=quality_assessments,
                    revision_history=revision_history,
                )

            try:
                revise_output = self.revise_agent.revise(
                    rephrased_question=current_question,
                    suggestions=review_output.suggestions,
                )
            except Exception as e:
                logger.error(f"Revise failed at iteration {iteration_count}: {e}")
                raise

            # Update current question for next iteration
            current_question = revise_output.revised_question
            revision_history.append(current_question)

            logger.info(
                f"Revision complete: new_length={len(current_question)}, "
                f"notes_length={len(revise_output.revision_notes)}"
            )

        # Should not reach here due to the check inside the loop,
        # but handle as safety fallback
        logger.error("Unexpected loop exit condition")
        return IterationResult(
            final_question=current_question,
            final_score=quality_assessments[-1]["overall_score"] if quality_assessments else 0.0,
            iteration_count=iteration_count,
            final_status=SessionStatus.MAX_ITERATIONS_EXCEEDED,
            quality_assessments=quality_assessments,
            revision_history=revision_history,
        )

    def _save_quality_assessment(
        self,
        problem_id: str,
        review_output: Any,
    ) -> None:
        """
        Save quality assessment to database.

        Args:
            problem_id: Problem being assessed
            review_output: ReviewAgentOutput to save
        """
        try:
            assessment = QualityAssessment(
                problem_id=problem_id,
                clarity_grammar_score=review_output.clarity_grammar_score,
                logical_coherence_score=review_output.logical_coherence_score,
                mathematical_validity_score=review_output.mathematical_validity_score,
                overall_score=review_output.overall_score,
                thought_process=review_output.thought_process,
                suggestions=review_output.suggestions,
            )
            self.db_session.add(assessment)
            self.db_session.commit()
            logger.debug(f"Saved QualityAssessment: {assessment.id}")
        except Exception as e:
            logger.error(f"Failed to save QualityAssessment: {e}")
            self.db_session.rollback()
            # Don't raise - database logging is not critical
