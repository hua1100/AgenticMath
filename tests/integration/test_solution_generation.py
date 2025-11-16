"""
Integration tests for Solution Generation Pipeline.

Tests the full workflow: Problem → Solver Agent → Solution → Database.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.solver_agent import SolverAgent
from src.agents.llm_client import LLMClient, LLMConfig
from src.orchestration.solution_pipeline import SolutionPipeline, generate_solutions
from src.models.problem import Problem, ProblemSource, SourceType, MathDomain
from src.models.solution import Solution
from src.storage.database import Base


@pytest.fixture
def mock_llm_response():
    """Standard mock LLM response."""
    return {
        "content": """###thought###
Step 1: Parse the equation
2x + 3 = 11

Step 2: Isolate x
2x = 11 - 3
2x = 8

Step 3: Solve for x
x = 8/2
x = 4

Step 4: Verify
2(4) + 3 = 8 + 3 = 11 ✓

###answer###
4
"""
    }


@pytest.fixture
def mock_llm_client(mock_llm_response):
    """Create mock LLM client."""
    client = Mock(spec=LLMClient)
    client.chat_completion = Mock(return_value=mock_llm_response)
    client.total_tokens_used = 1000
    client.total_cost_usd = 0.01
    return client


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def original_problem(test_db):
    """Create a test problem in database."""
    problem = Problem(
        id=uuid4(),
        content="Solve: 2x + 3 = 11",
        domain=MathDomain.ALGEBRA,
        competencies=["linear_equations"],
        baseline_difficulty=2,
        source=ProblemSource.ORIGINAL,
        source_type=SourceType.MANUAL,
    )
    test_db.add(problem)
    test_db.commit()
    return problem


@pytest.fixture
def rephrased_problem(test_db, original_problem):
    """Create a rephrased problem in database."""
    problem = Problem(
        id=uuid4(),
        content="A number increased by 3, then doubled, equals 11. Find the original number.",
        domain=MathDomain.ALGEBRA,
        competencies=["linear_equations", "word_problems"],
        baseline_difficulty=3,
        source=ProblemSource.REPHRASED,
        source_type=SourceType.GENERATED,
        parent_id=original_problem.id,
    )
    test_db.add(problem)
    test_db.commit()
    return problem


class TestSolverAgentWithDatabase:
    """Test Solver Agent with database integration."""

    def test_solve_and_save_creates_solution(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test solve_and_save creates Solution record."""
        agent = SolverAgent(llm_client=mock_llm_client, db=test_db)

        solution = agent.solve_and_save(
            question=original_problem.content,
            problem_id=original_problem.id,
        )

        # Verify solution was created
        assert solution.id is not None
        assert solution.problem_id == original_problem.id
        assert solution.final_answer == "4"
        assert "Step 1" in solution.thought_process

        # Verify it's in database
        db_solution = test_db.query(Solution).filter(
            Solution.id == solution.id
        ).first()
        assert db_solution is not None
        assert db_solution.final_answer == "4"

    def test_solve_and_save_without_db_raises_error(self, mock_llm_client):
        """Test solve_and_save raises error when no database session."""
        agent = SolverAgent(llm_client=mock_llm_client, db=None)

        with pytest.raises(ValueError, match="Database session is required"):
            agent.solve_and_save(
                question="Solve: x + 1 = 2",
                problem_id=uuid4(),
            )

    def test_multiple_solutions_for_same_problem(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test creating multiple solutions for same problem."""
        agent = SolverAgent(llm_client=mock_llm_client, db=test_db)

        # Create first solution
        solution1 = agent.solve_and_save(
            question=original_problem.content,
            problem_id=original_problem.id,
        )

        # Create second solution (e.g., different approach)
        solution2 = agent.solve_and_save(
            question=original_problem.content,
            problem_id=original_problem.id,
        )

        # Both should exist
        assert solution1.id != solution2.id
        solutions = test_db.query(Solution).filter(
            Solution.problem_id == original_problem.id
        ).all()
        assert len(solutions) == 2


class TestSolutionPipeline:
    """Test Solution Pipeline integration."""

    def test_generate_solutions_for_original_only(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test generating solution for original problem only."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        solutions = pipeline.generate_solutions(
            original_problem_id=original_problem.id,
            rephrased_problem_id=None,
        )

        # Should have 1 solution
        assert len(solutions) == 1
        assert solutions[0].problem_id == original_problem.id
        assert solutions[0].final_answer == "4"

    def test_generate_solutions_for_both_problems(
        self, mock_llm_client, test_db, original_problem, rephrased_problem
    ):
        """Test generating solutions for both original and rephrased."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        solutions = pipeline.generate_solutions(
            original_problem_id=original_problem.id,
            rephrased_problem_id=rephrased_problem.id,
        )

        # Should have 2 solutions
        assert len(solutions) == 2

        # Verify both problems have solutions
        problem_ids = {s.problem_id for s in solutions}
        assert original_problem.id in problem_ids
        assert rephrased_problem.id in problem_ids

    def test_generate_solutions_original_not_found(
        self, mock_llm_client, test_db
    ):
        """Test error when original problem not found."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        with pytest.raises(ValueError, match="Original problem not found"):
            pipeline.generate_solutions(
                original_problem_id=uuid4(),  # Non-existent ID
                rephrased_problem_id=None,
            )

    def test_generate_solutions_rephrased_not_found_continues(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test continues when rephrased problem not found."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        # Should not raise, only generate solution for original
        solutions = pipeline.generate_solutions(
            original_problem_id=original_problem.id,
            rephrased_problem_id=uuid4(),  # Non-existent ID
        )

        # Should still have 1 solution (original)
        assert len(solutions) == 1
        assert solutions[0].problem_id == original_problem.id

    def test_generate_solution_for_problem(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test generating solution for single problem."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        solution = pipeline.generate_solution_for_problem(original_problem.id)

        assert solution.problem_id == original_problem.id
        assert solution.final_answer == "4"

    def test_generate_batch_solutions(
        self, mock_llm_client, test_db, original_problem, rephrased_problem
    ):
        """Test generating solutions for multiple problems."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        problem_ids = [original_problem.id, rephrased_problem.id]
        solutions = pipeline.generate_batch_solutions(problem_ids)

        # Should generate 2 solutions
        assert len(solutions) == 2

        # Verify all problem IDs covered
        solution_problem_ids = {s.problem_id for s in solutions}
        assert solution_problem_ids == set(problem_ids)

    def test_generate_batch_solutions_continues_on_error(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test batch generation continues even if some fail."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        # Mix of valid and invalid IDs
        problem_ids = [
            original_problem.id,
            uuid4(),  # Invalid
            uuid4(),  # Invalid
        ]

        solutions = pipeline.generate_batch_solutions(problem_ids)

        # Should have 1 solution (only the valid one)
        assert len(solutions) == 1
        assert solutions[0].problem_id == original_problem.id


class TestConvenienceFunction:
    """Test convenience function."""

    def test_generate_solutions_convenience_function(
        self, mock_llm_client, test_db, original_problem, rephrased_problem
    ):
        """Test generate_solutions convenience function."""
        solutions = generate_solutions(
            llm_client=mock_llm_client,
            db=test_db,
            original_problem_id=original_problem.id,
            rephrased_problem_id=rephrased_problem.id,
        )

        assert len(solutions) == 2


class TestSolutionQuality:
    """Test solution quality and content."""

    def test_solution_has_intermediate_steps(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test solution includes intermediate steps."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        solution = pipeline.generate_solution_for_problem(original_problem.id)

        # Should have extracted intermediate steps
        assert solution.intermediate_steps is not None
        assert len(solution.intermediate_steps) >= 3
        assert any("Step" in step for step in solution.intermediate_steps)

    def test_solution_thought_process_detailed(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test solution has detailed thought process."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        solution = pipeline.generate_solution_for_problem(original_problem.id)

        # Thought process should be substantial
        assert len(solution.thought_process) > 100
        # Should contain mathematical reasoning
        assert "Step" in solution.thought_process
        assert "=" in solution.thought_process

    def test_solution_answer_is_concise(
        self, mock_llm_client, test_db, original_problem
    ):
        """Test solution answer is concise."""
        pipeline = SolutionPipeline(llm_client=mock_llm_client, db=test_db)

        solution = pipeline.generate_solution_for_problem(original_problem.id)

        # Answer should be short
        assert len(solution.final_answer) < 50
        # Should be just the number/value
        assert solution.final_answer == "4"


class TestErrorHandling:
    """Test error handling in solution generation."""

    def test_handles_llm_error_gracefully(self, test_db, original_problem):
        """Test handling LLM errors."""
        # Mock LLM that raises error
        mock_client = Mock(spec=LLMClient)
        mock_client.chat_completion = Mock(side_effect=Exception("LLM API error"))

        agent = SolverAgent(llm_client=mock_client, db=test_db)

        # Should raise the error
        with pytest.raises(Exception, match="LLM API error"):
            agent.solve_and_save(
                question=original_problem.content,
                problem_id=original_problem.id,
            )

    def test_handles_parse_error(self, test_db, original_problem):
        """Test handling parse errors."""
        # Mock LLM with invalid response
        mock_client = Mock(spec=LLMClient)
        mock_client.chat_completion = Mock(return_value={
            "content": "Invalid format - no sections"
        })

        agent = SolverAgent(llm_client=mock_client, db=test_db)

        # Should raise parse error
        with pytest.raises(Exception):
            agent.solve_and_save(
                question=original_problem.content,
                problem_id=original_problem.id,
            )
