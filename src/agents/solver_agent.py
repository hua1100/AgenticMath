"""
Solver Agent for Generating Chain-of-Thought Solutions.

This agent generates detailed, step-by-step solutions to mathematical problems
using Chain-of-Thought (CoT) reasoning that demonstrates mathematical rigor
and pedagogical clarity.
"""

import logging
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from src.agents.llm_client import LLMClient
from src.prompts.solver_prompt import create_solver_prompt
from src.parsers.solver_parser import SolverParser, SolverAgentOutput, SolverParseError
from src.models.agent_execution import AgentExecution, AgentType
from src.models.solution import Solution

logger = logging.getLogger(__name__)


class SolverAgent:
    """
    Solver Agent for generating Chain-of-Thought (CoT) solutions.

    Generates detailed solutions showing:
    - Problem deconstruction with given data, variables, constraints
    - Clarification of any ambiguities
    - Step-by-step derivation with all intermediate calculations
    - Final calculation and answer

    Example:
        >>> agent = SolverAgent(llm_client=llm_client)
        >>> output = agent.solve("Solve for x: 2x + 3 = 11")
        >>> print(output.final_answer)
        4
        >>> print(len(output.intermediate_steps))
        5
    """

    def __init__(self, llm_client: LLMClient, db: Optional[Session] = None):
        """
        Initialize Solver Agent.

        Args:
            llm_client: LLM client for calling GPT-4
            db: Database session for logging. If None, logging is skipped.
        """
        self.llm_client = llm_client
        self.db = db
        self.parser = SolverParser()
        logger.info("Solver Agent initialized")

    def solve(
        self,
        question: str,
        problem_id: Optional[UUID] = None,
        language: str = "auto",
    ) -> SolverAgentOutput:
        """
        Generate a detailed solution for a math problem.

        Args:
            question: The math problem to solve
            problem_id: Optional problem ID for database reference
            language: Language hint ("en", "zh", or "auto")

        Returns:
            SolverAgentOutput with thought process and final answer

        Raises:
            ValueError: If input validation fails
            SolverParseError: If LLM output cannot be parsed
        """
        # Validate input
        self._validate_input(question)

        # Create prompt
        prompt = create_solver_prompt(question=question, language=language)

        logger.info(f"Calling LLM to solve problem{f' (ID: {problem_id})' if problem_id else ''}...")
        start_time = datetime.now()

        # Call LLM
        try:
            response = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for more consistent solutions
            )

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            raw_response = response["content"]

            logger.info(f"LLM response received in {execution_time_ms}ms")
            logger.debug(f"Raw response:\n{raw_response[:200]}...")

            # Parse output
            parsed_output = self.parser.parse(raw_response)

            # Validate output
            self._validate_output(parsed_output)

            logger.info(f"Solution generated successfully. Answer: {parsed_output.final_answer}")

            # Log to database if db session is available
            if self.db:
                execution_record = AgentExecution(
                    id=uuid4(),
                    agent_type=AgentType.SOLVER,
                    session_id=None,  # Will be set by pipeline if part of a session
                    input_data={
                        "question": question,
                        "problem_id": str(problem_id) if problem_id else None,
                    },
                    output_data={
                        "thought_process": parsed_output.thought_process,
                        "final_answer": parsed_output.final_answer,
                        "intermediate_steps": parsed_output.intermediate_steps,
                    },
                    prompt_template=prompt,
                    raw_llm_response=raw_response,
                    execution_time_ms=execution_time_ms,
                    created_at=datetime.utcnow(),
                )
                self.db.add(execution_record)
                try:
                    self.db.commit()
                    logger.debug(f"Logged Solver execution: {execution_record.id}")
                except Exception as e:
                    logger.error(f"Failed to log Solver execution: {e}")
                    self.db.rollback()

            return parsed_output

        except SolverParseError as e:
            logger.error(f"Failed to parse Solver output: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Solver Agent: {e}")
            raise

    def solve_and_save(
        self,
        question: str,
        problem_id: UUID,
        language: str = "auto",
    ) -> Solution:
        """
        Generate solution and save to database.

        Args:
            question: The math problem to solve
            problem_id: Problem ID for database reference
            language: Language hint ("en", "zh", or "auto")

        Returns:
            Solution database record

        Raises:
            ValueError: If db session is not available or validation fails
            SolverParseError: If LLM output cannot be parsed
        """
        if not self.db:
            raise ValueError("Database session is required for solve_and_save()")

        # Generate solution
        output = self.solve(question=question, problem_id=problem_id, language=language)

        # Create Solution record
        solution = Solution(
            id=uuid4(),
            problem_id=problem_id,
            thought_process=output.thought_process,
            final_answer=output.final_answer,
            intermediate_steps=output.intermediate_steps,
            created_at=datetime.utcnow(),
        )

        # Save to database
        self.db.add(solution)
        try:
            self.db.commit()
            logger.info(f"Solution saved to database: {solution.id}")
            return solution
        except Exception as e:
            logger.error(f"Failed to save solution: {e}")
            self.db.rollback()
            raise

    def _validate_input(self, question: str) -> None:
        """
        Validate solver input.

        Args:
            question: The math problem

        Raises:
            ValueError: If validation fails
        """
        if not question or not question.strip():
            raise ValueError("question cannot be empty")

        if len(question) > 5000:
            raise ValueError(f"question too long ({len(question)} chars, max 5000)")

    def _validate_output(self, output: SolverAgentOutput) -> None:
        """
        Validate solver output.

        Args:
            output: Parsed output

        Raises:
            ValueError: If validation fails
        """
        if not output.thought_process or len(output.thought_process.strip()) < 10:
            raise ValueError("thought_process is too short or empty")

        if not output.final_answer or len(output.final_answer.strip()) == 0:
            raise ValueError("final_answer is empty")
