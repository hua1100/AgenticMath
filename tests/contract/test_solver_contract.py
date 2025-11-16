"""
Contract validation tests for Solver Agent.

Validates that Solver Agent follows the contract defined in
specs/001-multi-agent-problem-generator/contracts/solver-agent.md
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from src.agents.solver_agent import SolverAgent
from src.parsers.solver_parser import SolverAgentOutput


class TestSolverAgentContract:
    """Test suite validating Solver Agent contract compliance."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = Mock()
        client.chat_completion = Mock(return_value={
            "content": """###thought###
Step 1: Define variables
Let x = unknown

Step 2: Set up equation
2x + 3 = 11

Step 3: Solve
2x = 8
x = 4

###answer###
4
"""
        })
        return client

    @pytest.fixture
    def solver_agent(self, mock_llm_client):
        """Create Solver Agent with mock LLM client."""
        return SolverAgent(llm_client=mock_llm_client, db=None)

    def test_contract_input_accepts_question(self, solver_agent):
        """
        CONTRACT: Input must accept 'question' parameter.

        From solver-agent.md:
        class SolverAgentInput(BaseModel):
            question: str
            problem_id: Optional[UUID] = None
        """
        result = solver_agent.solve(question="Solve: 2x + 3 = 11")

        assert isinstance(result, SolverAgentOutput)

    def test_contract_input_accepts_problem_id(self, solver_agent):
        """
        CONTRACT: Input must accept optional 'problem_id' parameter.
        """
        problem_id = uuid4()
        result = solver_agent.solve(
            question="Solve: 2x + 3 = 11",
            problem_id=problem_id
        )

        assert isinstance(result, SolverAgentOutput)

    def test_contract_output_has_thought_process(self, solver_agent):
        """
        CONTRACT: Output must contain 'thought_process' field.

        From solver-agent.md:
        class SolverAgentOutput(BaseModel):
            thought_process: str  # Detailed step-by-step reasoning
        """
        result = solver_agent.solve(question="Solve: 2x + 3 = 11")

        assert hasattr(result, "thought_process")
        assert isinstance(result.thought_process, str)
        assert len(result.thought_process) > 0

    def test_contract_output_has_final_answer(self, solver_agent):
        """
        CONTRACT: Output must contain 'final_answer' field.

        From solver-agent.md:
        class SolverAgentOutput(BaseModel):
            final_answer: str  # Concise final answer
        """
        result = solver_agent.solve(question="Solve: 2x + 3 = 11")

        assert hasattr(result, "final_answer")
        assert isinstance(result.final_answer, str)
        assert len(result.final_answer) > 0

    def test_contract_output_has_intermediate_steps(self, solver_agent):
        """
        CONTRACT: Output may contain optional 'intermediate_steps' field.

        From solver-agent.md:
        class SolverAgentOutput(BaseModel):
            intermediate_steps: Optional[List[str]] = None
        """
        result = solver_agent.solve(question="Solve: 2x + 3 = 11")

        assert hasattr(result, "intermediate_steps")
        # Can be None or List[str]
        if result.intermediate_steps is not None:
            assert isinstance(result.intermediate_steps, list)

    def test_contract_output_format_sections(self, solver_agent):
        """
        CONTRACT: Raw LLM output must follow format:
        ###thought###
        <step-by-step reasoning>
        ###answer###
        <final answer>
        """
        result = solver_agent.solve(question="Solve: 2x + 3 = 11")

        # Verify output was successfully parsed (implies correct format)
        assert result.thought_process is not None
        assert result.final_answer is not None

    def test_contract_thought_shows_all_steps(self, solver_agent):
        """
        CONTRACT: thought_process must show ALL intermediate steps.

        From solver-agent.md FR-036:
        "Solver Agent MUST show all intermediate steps without skipping calculations"
        """
        result = solver_agent.solve(question="Solve: 2x + 3 = 11")

        # Should contain multiple steps
        thought = result.thought_process
        assert "Step" in thought or "step" in thought or "步驟" in thought
        # Should show intermediate calculations
        assert len(thought) > 50  # Substantial reasoning

    def test_contract_answer_is_concise(self, solver_agent):
        """
        CONTRACT: final_answer should be concise (number/fraction).

        From solver-agent.md:
        "Replace <final answer> with the concise final answer
        (e.g., a number or fraction), without units or extra words"
        """
        result = solver_agent.solve(question="Solve: 2x + 3 = 11")

        # Answer should be short and to the point
        assert len(result.final_answer) < 100
        # Should not contain full sentences
        assert not result.final_answer.startswith("The answer is")

    def test_contract_handles_empty_question(self, solver_agent):
        """
        CONTRACT: Must handle invalid input gracefully.
        """
        with pytest.raises(ValueError, match="question cannot be empty"):
            solver_agent.solve(question="")

    def test_contract_handles_too_long_question(self, solver_agent):
        """
        CONTRACT: Must handle very long questions.
        """
        long_question = "x " * 3000  # > 5000 chars
        with pytest.raises(ValueError, match="question too long"):
            solver_agent.solve(question=long_question)

    def test_contract_validation_non_empty_thought(self):
        """
        CONTRACT: thought_process must not be empty.
        """
        with pytest.raises(ValueError):
            SolverAgentOutput(
                thought_process="",
                final_answer="4"
            )

    def test_contract_validation_non_empty_answer(self):
        """
        CONTRACT: final_answer must not be empty.
        """
        with pytest.raises(ValueError):
            SolverAgentOutput(
                thought_process="Long enough reasoning process here",
                final_answer=""
            )


class TestSolverAgentContractExamples:
    """Test contract examples from solver-agent.md."""

    @pytest.fixture
    def mock_llm_client_rectangle_problem(self):
        """Mock LLM client with rectangle problem response."""
        client = Mock()
        client.chat_completion = Mock(return_value={
            "content": """###thought###
Step 1: Define variables and given information
- Let w = width of the garden (in meters)
- Length l = 2w + 3 (given: "3 meters more than twice its width")
- Perimeter P = 22 meters (given)

Step 2: Recall perimeter formula for rectangle
- Perimeter = 2(length + width)
- P = 2(l + w)

Step 3: Substitute the expression for length
- P = 2((2w + 3) + w)
- 22 = 2(2w + 3 + w)
- 22 = 2(3w + 3)

Step 4: Solve for width
- 22 = 6w + 6
- 22 - 6 = 6w
- 16 = 6w
- w = 16/6
- w = 8/3
- w ≈ 2.67 meters (rounded to two decimal places)

Step 5: Verification
- Width w = 8/3 meters
- Length l = 2(8/3) + 3 = 16/3 + 9/3 = 25/3 meters
- Perimeter = 2(25/3 + 8/3) = 2(33/3) = 2(11) = 22 meters ✓

The answer is 2.67 meters.

###answer###
2.67
"""
        })
        return client

    def test_contract_example_rectangle_problem(self, mock_llm_client_rectangle_problem):
        """
        CONTRACT EXAMPLE: Rectangle problem from solver-agent.md.

        Tests the exact example from the contract specification.
        """
        agent = SolverAgent(llm_client=mock_llm_client_rectangle_problem, db=None)

        result = agent.solve(
            question="A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places."
        )

        # Validate output structure
        assert result.thought_process is not None
        assert result.final_answer == "2.67"

        # Validate thought process contains all required steps
        thought = result.thought_process
        assert "Define variables" in thought or "变量" in thought
        assert "Perimeter" in thought or "周长" in thought
        assert "Substitute" in thought or "代入" in thought
        assert "Solve" in thought or "求解" in thought
        assert "Verification" in thought or "验证" in thought

        # Validate intermediate steps extracted
        if result.intermediate_steps:
            assert len(result.intermediate_steps) >= 5


class TestSolverAgentContractRequirements:
    """Test specific functional requirements from spec.md."""

    @pytest.fixture
    def mock_llm_client_multicase(self):
        """Mock LLM for multi-case problem."""
        client = Mock()
        client.chat_completion = Mock(return_value={
            "content": """###thought###
Step 1: Identify cases
We need to consider two cases: x ≥ 0 and x < 0

Step 2: Case 1 - When x ≥ 0
|x| = x
Equation becomes: x + 2 = 5
x = 3

Step 3: Case 2 - When x < 0
|x| = -x
Equation becomes: -x + 2 = 5
-x = 3
x = -3

Step 4: Verify both solutions
Case 1: |3| + 2 = 3 + 2 = 5 ✓
Case 2: |-3| + 2 = 3 + 2 = 5 ✓

###answer###
x = 3 or x = -3
"""
        })
        return client

    def test_fr037_multi_case_analysis(self, mock_llm_client_multicase):
        """
        FR-037: Solver Agent MUST list all cases/combinations for
        multi-case analysis problems.
        """
        agent = SolverAgent(llm_client=mock_llm_client_multicase, db=None)

        result = agent.solve(question="Solve: |x| + 2 = 5")

        thought = result.thought_process
        # Must show both cases
        assert "Case 1" in thought or "Case 2" in thought or "情况" in thought
        # Must verify both solutions
        assert "✓" in thought or "验证" in thought or "Verify" in thought

    def test_fr036_shows_intermediate_steps(self, mock_llm_client_rectangle_problem):
        """
        FR-036: Solver Agent MUST show all intermediate steps
        without skipping calculations.
        """
        agent = SolverAgent(llm_client=mock_llm_client_rectangle_problem, db=None)

        result = agent.solve(question="Rectangle problem")

        # Should have multiple intermediate steps
        assert result.intermediate_steps is not None
        assert len(result.intermediate_steps) >= 3

    def test_sc009_complete_step_by_step(self, mock_llm_client_rectangle_problem):
        """
        SC-009: 100% of solutions have complete step-by-step reasoning
        (no skipped steps, all intermediate calculations shown)
        """
        agent = SolverAgent(llm_client=mock_llm_client_rectangle_problem, db=None)

        result = agent.solve(question="Rectangle problem")

        # Thought process should be detailed
        assert len(result.thought_process) > 200
        # Should contain mathematical operations
        assert any(op in result.thought_process for op in ["+", "-", "*", "/", "="])
        # Should show work, not just final answer
        assert result.thought_process != result.final_answer
