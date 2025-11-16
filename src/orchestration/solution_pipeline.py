"""
Solution Generation Pipeline.

Generates Chain-of-Thought (CoT) solutions for math problems, supporting both
original seed problems and rephrased problems that pass quality review.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from src.agents.solver_agent import SolverAgent
from src.agents.llm_client import LLMClient
from src.models.problem import Problem
from src.models.solution import Solution

logger = logging.getLogger(__name__)


class SolutionPipeline:
    """
    Pipeline for generating solutions for math problems.

    Features:
    - Generates solutions for original and rephrased problems
    - Stores solutions in database
    - Links solutions to respective problems
    - Handles batch solution generation

    Example:
        >>> pipeline = SolutionPipeline(llm_client=llm_client, db=db)
        >>> solutions = pipeline.generate_solutions(
        ...     original_problem_id=uuid1,
        ...     rephrased_problem_id=uuid2
        ... )
        >>> len(solutions)
        2
    """

    def __init__(self, llm_client: LLMClient, db: Session):
        """
        Initialize Solution Pipeline.

        Args:
            llm_client: LLM client for Solver Agent
            db: Database session
        """
        self.llm_client = llm_client
        self.db = db
        self.solver_agent = SolverAgent(llm_client=llm_client, db=db)
        logger.info("Solution Pipeline initialized")

    def generate_solutions(
        self,
        original_problem_id: UUID,
        rephrased_problem_id: Optional[UUID] = None,
    ) -> List[Solution]:
        """
        Generate solutions for original and rephrased problems.

        Args:
            original_problem_id: ID of the original problem
            rephrased_problem_id: ID of the rephrased problem (optional)

        Returns:
            List of Solution records (1 or 2 solutions)

        Raises:
            ValueError: If problems not found or validation fails
        """
        solutions = []

        # Fetch original problem
        original_problem = self.db.query(Problem).filter(Problem.id == original_problem_id).first()
        if not original_problem:
            raise ValueError(f"Original problem not found: {original_problem_id}")

        logger.info(f"Generating solution for original problem: {original_problem_id}")

        # Generate solution for original problem
        try:
            original_solution = self.solver_agent.solve_and_save(
                question=original_problem.content,
                problem_id=original_problem.id,
            )
            solutions.append(original_solution)
            logger.info(f"Original problem solution saved: {original_solution.id}")
        except Exception as e:
            logger.error(f"Failed to generate solution for original problem: {e}")
            raise

        # Generate solution for rephrased problem if provided
        if rephrased_problem_id:
            rephrased_problem = self.db.query(Problem).filter(
                Problem.id == rephrased_problem_id
            ).first()
            if not rephrased_problem:
                logger.warning(f"Rephrased problem not found: {rephrased_problem_id}")
            else:
                logger.info(f"Generating solution for rephrased problem: {rephrased_problem_id}")
                try:
                    rephrased_solution = self.solver_agent.solve_and_save(
                        question=rephrased_problem.content,
                        problem_id=rephrased_problem.id,
                    )
                    solutions.append(rephrased_solution)
                    logger.info(f"Rephrased problem solution saved: {rephrased_solution.id}")
                except Exception as e:
                    logger.error(f"Failed to generate solution for rephrased problem: {e}")
                    # Don't re-raise - original solution was successful

        logger.info(f"Generated {len(solutions)} solution(s)")
        return solutions

    def generate_solution_for_problem(self, problem_id: UUID) -> Solution:
        """
        Generate solution for a single problem.

        Args:
            problem_id: ID of the problem to solve

        Returns:
            Solution record

        Raises:
            ValueError: If problem not found or validation fails
        """
        # Fetch problem
        problem = self.db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            raise ValueError(f"Problem not found: {problem_id}")

        logger.info(f"Generating solution for problem: {problem_id}")

        # Generate and save solution
        try:
            solution = self.solver_agent.solve_and_save(
                question=problem.content,
                problem_id=problem.id,
            )
            logger.info(f"Solution saved: {solution.id}")
            return solution
        except Exception as e:
            logger.error(f"Failed to generate solution: {e}")
            raise

    def generate_batch_solutions(self, problem_ids: List[UUID]) -> List[Solution]:
        """
        Generate solutions for multiple problems.

        Args:
            problem_ids: List of problem IDs

        Returns:
            List of Solution records (may be fewer than input if some fail)

        Note:
            Continues processing even if individual solutions fail.
            Check logs for any failures.
        """
        solutions = []

        logger.info(f"Generating solutions for {len(problem_ids)} problems")

        for i, problem_id in enumerate(problem_ids, 1):
            logger.info(f"Processing problem {i}/{len(problem_ids)}: {problem_id}")
            try:
                solution = self.generate_solution_for_problem(problem_id)
                solutions.append(solution)
            except Exception as e:
                logger.error(f"Failed to generate solution for problem {problem_id}: {e}")
                # Continue with next problem

        logger.info(f"Successfully generated {len(solutions)}/{len(problem_ids)} solutions")
        return solutions


def generate_solutions(
    llm_client: LLMClient,
    db: Session,
    original_problem_id: UUID,
    rephrased_problem_id: Optional[UUID] = None,
) -> List[Solution]:
    """
    Convenience function to generate solutions.

    Args:
        llm_client: LLM client for Solver Agent
        db: Database session
        original_problem_id: ID of the original problem
        rephrased_problem_id: ID of the rephrased problem (optional)

    Returns:
        List of Solution records

    Example:
        >>> solutions = generate_solutions(
        ...     llm_client=llm_client,
        ...     db=db,
        ...     original_problem_id=uuid1,
        ...     rephrased_problem_id=uuid2
        ... )
    """
    pipeline = SolutionPipeline(llm_client=llm_client, db=db)
    return pipeline.generate_solutions(
        original_problem_id=original_problem_id,
        rephrased_problem_id=rephrased_problem_id,
    )
