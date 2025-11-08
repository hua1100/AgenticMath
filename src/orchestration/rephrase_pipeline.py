"""
Full Rephrase Pipeline for Problem Complexity Escalation.

Orchestrates the complete workflow:
1. Rephrase original problem with escalation dimensions
2. Review rephrased problem for quality
3. Iteratively revise until quality threshold met
4. Track all steps in database (RephraseSession, Problems, AgentExecutions)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from src.agents.rephrase_agent import RephraseAgent
from src.agents.llm_client import LLMClient
from src.orchestration.iteration_manager import IterationManager
from src.models.problem import Problem, ProblemSource, MathDomain, SourceType
from src.models.rephrase_session import RephraseSession, SessionStatus
from src.models.agent_execution import AgentExecution, AgentType

logger = logging.getLogger(__name__)


class PipelineResult:
    """
    Result of complete rephrase pipeline execution.

    Attributes:
        session_id: RephraseSession UUID
        original_problem_id: Original Problem UUID
        final_problem_id: Final Problem UUID
        final_status: SUCCESS or MAX_ITERATIONS_EXCEEDED
        final_question: Final refined question text
        final_score: Final quality score
        iteration_count: Number of review-revise iterations
        total_time_ms: Total pipeline execution time
        escalation_dimensions: Applied complexity dimensions
    """

    def __init__(
        self,
        session_id: UUID,
        original_problem_id: UUID,
        final_problem_id: UUID,
        final_status: SessionStatus,
        final_question: str,
        final_score: float,
        iteration_count: int,
        total_time_ms: int,
        escalation_dimensions: List[str],
    ):
        self.session_id = session_id
        self.original_problem_id = original_problem_id
        self.final_problem_id = final_problem_id
        self.final_status = final_status
        self.final_question = final_question
        self.final_score = final_score
        self.iteration_count = iteration_count
        self.total_time_ms = total_time_ms
        self.escalation_dimensions = escalation_dimensions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "session_id": str(self.session_id),
            "original_problem_id": str(self.original_problem_id),
            "final_problem_id": str(self.final_problem_id),
            "final_status": self.final_status.value,
            "final_question": self.final_question,
            "final_score": self.final_score,
            "iteration_count": self.iteration_count,
            "total_time_ms": self.total_time_ms,
            "escalation_dimensions": self.escalation_dimensions,
        }


class RephrasePipeline:
    """
    Complete pipeline for problem rephrase with quality control.

    Orchestrates: Rephrase → Review → (Revise loop) → Final Problem

    Example:
        >>> pipeline = RephrasePipeline(
        ...     llm_client=llm_client,
        ...     db_session=db_session,
        ...     quality_threshold=4.5,
        ...     max_iterations=5
        ... )
        >>> result = pipeline.process(
        ...     original_problem=problem,
        ...     escalation_dimensions=["Multi-stage Transformation", "Real-world Parameterization"]
        ... )
        >>> print(result.final_status)
        SessionStatus.SUCCESS
    """

    def __init__(
        self,
        llm_client: LLMClient,
        db_session: Session,
        quality_threshold: float = 4.5,
        max_iterations: int = 5,
    ):
        """
        Initialize Rephrase Pipeline.

        Args:
            llm_client: LLM client for all agents
            db_session: Database session for persistence
            quality_threshold: Minimum quality score (default 4.5)
            max_iterations: Maximum review-revise iterations (default 5)
        """
        self.llm_client = llm_client
        self.db_session = db_session
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations

        logger.info(
            f"RephrasePipeline initialized: threshold={quality_threshold}, "
            f"max_iterations={max_iterations}"
        )

    def process(
        self,
        original_problem: Problem,
        escalation_dimensions: List[str],
    ) -> PipelineResult:
        """
        Execute complete rephrase pipeline.

        Args:
            original_problem: Original Problem record from database
            escalation_dimensions: List of complexity dimensions to apply

        Returns:
            PipelineResult with final problem and metadata

        Raises:
            ValueError: If inputs are invalid
        """
        pipeline_start = datetime.now()

        # Validate inputs
        if not original_problem or not original_problem.content:
            raise ValueError("original_problem must have content")
        if not escalation_dimensions or len(escalation_dimensions) < 3:
            raise ValueError("escalation_dimensions must have at least 3 dimensions")

        logger.info(
            f"Starting pipeline for problem {original_problem.id}: "
            f"dimensions={escalation_dimensions}"
        )

        # Create RephraseSession
        session = RephraseSession(
            id=uuid4(),
            original_problem_id=original_problem.id,
            escalation_dimensions=escalation_dimensions,
            iteration_count=0,
            quality_threshold=self.quality_threshold,
            final_status=SessionStatus.ERROR,  # Will update later
            created_at=datetime.utcnow(),
        )
        self.db_session.add(session)
        self.db_session.flush()  # Get session.id

        try:
            # Step 1: Rephrase
            rephrased_problem = self._execute_rephrase(
                original_problem=original_problem,
                escalation_dimensions=escalation_dimensions,
                session_id=session.id,
            )

            # Step 2: Review-Revise Loop
            from src.agents.review_agent import ReviewAgent
            from src.agents.revise_agent import ReviseAgent

            review_agent = ReviewAgent(llm_client=self.llm_client)
            revise_agent = ReviseAgent(llm_client=self.llm_client)

            iteration_manager = IterationManager(
                review_agent=review_agent,
                revise_agent=revise_agent,
                quality_threshold=self.quality_threshold,
                max_iterations=self.max_iterations,
                db_session=self.db_session,
            )

            iteration_result = iteration_manager.iterate_until_quality(
                initial_question=rephrased_problem.content,
                problem_id=str(rephrased_problem.id),
            )

            # Step 3: Create final problem if revised
            if iteration_result.iteration_count > 1:
                # Question was revised, create new Problem record
                final_problem = self._create_revised_problem(
                    rephrased_problem=rephrased_problem,
                    final_question=iteration_result.final_question,
                )
            else:
                # No revisions needed, use rephrased problem as final
                final_problem = rephrased_problem

            # Step 4: Update session
            session.final_problem_id = final_problem.id
            session.iteration_count = iteration_result.iteration_count
            session.final_status = iteration_result.final_status
            session.completed_at = datetime.utcnow()

            self.db_session.commit()

            total_time_ms = int((datetime.now() - pipeline_start).total_seconds() * 1000)

            logger.info(
                f"Pipeline completed: session={session.id}, "
                f"status={session.final_status.value}, "
                f"iterations={session.iteration_count}, "
                f"time={total_time_ms}ms"
            )

            return PipelineResult(
                session_id=session.id,
                original_problem_id=original_problem.id,
                final_problem_id=final_problem.id,
                final_status=session.final_status,
                final_question=final_problem.content,
                final_score=iteration_result.final_score,
                iteration_count=session.iteration_count,
                total_time_ms=total_time_ms,
                escalation_dimensions=escalation_dimensions,
            )

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            session.final_status = SessionStatus.ERROR
            session.completed_at = datetime.utcnow()
            self.db_session.rollback()
            raise

    def _execute_rephrase(
        self,
        original_problem: Problem,
        escalation_dimensions: List[str],
        session_id: UUID,
    ) -> Problem:
        """
        Execute Rephrase Agent and create rephrased Problem.

        Args:
            original_problem: Original problem
            escalation_dimensions: Complexity dimensions
            session_id: Current session ID

        Returns:
            New Problem record with rephrased content
        """
        from src.agents.rephrase_agent import RephraseAgent

        logger.info("Executing Rephrase Agent...")
        start_time = datetime.now()

        rephrase_agent = RephraseAgent(llm_client=self.llm_client)

        # Execute rephrase
        rephrase_output = rephrase_agent.rephrase(
            problem_content=original_problem.content,
            escalation_dimensions=escalation_dimensions,
        )

        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Create rephrased Problem
        rephrased_problem = Problem(
            id=uuid4(),
            content=rephrase_output.stage3_rewritten_question,
            domain=original_problem.domain,
            competencies=rephrase_output.core_competencies,
            baseline_difficulty=rephrase_output.baseline_difficulty,
            source=ProblemSource.REPHRASED,
            source_type=original_problem.source_type,
            parent_id=original_problem.id,
            created_at=datetime.utcnow(),
            extra_metadata={
                "escalation_dimensions": rephrase_output.applied_dimensions,
                "domain_identified": rephrase_output.identified_domain,
            },
        )
        self.db_session.add(rephrased_problem)
        self.db_session.flush()

        # Log AgentExecution
        # Note: Full AgentExecution logging would be implemented here
        # For now, focusing on core pipeline functionality

        logger.info(
            f"Rephrase complete: problem={rephrased_problem.id}, "
            f"time={execution_time_ms}ms"
        )

        return rephrased_problem

    def _create_revised_problem(
        self,
        rephrased_problem: Problem,
        final_question: str,
    ) -> Problem:
        """
        Create final revised Problem record.

        Args:
            rephrased_problem: Rephrased problem (parent)
            final_question: Final revised question text

        Returns:
            New Problem record with revised content
        """
        revised_problem = Problem(
            id=uuid4(),
            content=final_question,
            domain=rephrased_problem.domain,
            competencies=rephrased_problem.competencies,
            baseline_difficulty=rephrased_problem.baseline_difficulty,
            source=ProblemSource.REVISED,
            source_type=rephrased_problem.source_type,
            parent_id=rephrased_problem.id,
            created_at=datetime.utcnow(),
        )
        self.db_session.add(revised_problem)
        self.db_session.flush()

        logger.info(f"Created revised problem: {revised_problem.id}")

        return revised_problem
