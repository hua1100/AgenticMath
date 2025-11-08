"""
Integration tests for CrewAI Pipeline.

Tests the CrewAI-based orchestration workflow:
- Rephrase using existing agents wrapped as tools
- Review-Revise loop using IterationManager
- Database persistence of sessions and problems
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from src.orchestration.crewai_pipeline import CrewAIPipeline, AgentToolkit
from src.agents.llm_client import LLMClient
from src.models.problem import Problem, ProblemSource, MathDomain, SourceType
from src.models.rephrase_session import SessionStatus
from src.parsers.rephrase_parser import RephraseAgentOutput
from src.parsers.review_parser import ReviewAgentOutput
from src.parsers.revise_parser import ReviseAgentOutput


# ============================================================================
# Mock Helpers
# ============================================================================

def create_mock_problem(
    content: str = "Original problem content",
    domain: MathDomain = MathDomain.ALGEBRA,
) -> Problem:
    """Create a mock Problem instance."""
    problem = Problem(
        id=uuid4(),
        content=content,
        domain=domain,
        competencies=["linear_equations"],
        baseline_difficulty=2,
        source=ProblemSource.ORIGINAL,
        source_type=SourceType.OCR,
    )
    return problem


def create_mock_rephrase_output() -> RephraseAgentOutput:
    """Create a mock RephraseAgentOutput."""
    return RephraseAgentOutput(
        stage1_problem_deconstruction="Analysis",
        stage2_escalation_protocol="Strategy",
        stage3_rewritten_question="Complex rephrased problem with multiple stages and conditions.",
        identified_domain="Algebra",
        core_competencies=["linear_equations", "multi_step_reasoning"],
        baseline_difficulty=4,
        applied_dimensions=["Multi-stage Transformation", "Real-world Parameterization", "Conditional Branching"],
    )


def create_mock_review_output(score: float, suggestions: list = None) -> ReviewAgentOutput:
    """Create a mock ReviewAgentOutput."""
    return ReviewAgentOutput(
        thought_process="Quality analysis",
        clarity_grammar_score=score,
        logical_coherence_score=score,
        mathematical_validity_score=score,
        overall_score=score,
        suggestions=suggestions or [],
    )


def create_mock_revise_output(question: str) -> ReviseAgentOutput:
    """Create a mock ReviseAgentOutput."""
    return ReviseAgentOutput(
        revised_question=question,
        revision_notes="Applied improvements based on suggestions",
    )


# ============================================================================
# Success Cases
# ============================================================================

def test_crewai_pipeline_success_no_revisions():
    """Test CrewAI pipeline succeeds without needing revisions."""
    # Mock database
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    # Create pipeline
    pipeline = CrewAIPipeline(
        llm_client=mock_llm,
        db_session=mock_db,
        quality_threshold=4.5,
        max_iterations=5,
    )

    # Mock the agents in the toolkit
    pipeline.toolkit.rephrase_agent.rephrase = Mock(return_value=create_mock_rephrase_output())
    pipeline.toolkit.review_agent.review = Mock(return_value=create_mock_review_output(4.7, []))

    # Create original problem
    original_problem = create_mock_problem()

    # Execute
    result = pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=["Multi-stage Transformation", "Real-world Parameterization", "Conditional Branching"],
    )

    # Verify result
    assert result["session_id"] is not None
    assert result["final_status"] == "success"
    assert result["final_score"] == 4.7
    assert result["iteration_count"] == 1
    assert len(result["escalation_dimensions"]) == 3

    # Verify agents were called
    assert pipeline.toolkit.rephrase_agent.rephrase.call_count == 1
    assert pipeline.toolkit.review_agent.review.call_count == 1

    # Verify database operations
    assert mock_db.add.call_count >= 2  # Session + rephrased problem
    assert mock_db.commit.called


def test_crewai_pipeline_success_with_revisions():
    """Test CrewAI pipeline succeeds after revisions."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    # Create pipeline
    pipeline = CrewAIPipeline(
        llm_client=mock_llm,
        db_session=mock_db,
        quality_threshold=4.5,
        max_iterations=5,
    )

    # Mock the agents in the toolkit
    pipeline.toolkit.rephrase_agent.rephrase = Mock(return_value=create_mock_rephrase_output())
    pipeline.toolkit.review_agent.review = Mock(side_effect=[
        create_mock_review_output(3.5, ["Add units"]),
        create_mock_review_output(4.6, []),
    ])
    pipeline.toolkit.revise_agent.revise = Mock(return_value=create_mock_revise_output("Improved problem with units."))

    original_problem = create_mock_problem()

    # Execute
    result = pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=["Multi-stage Transformation", "Real-world Parameterization", "Conditional Branching"],
    )

    # Verify result
    assert result["final_status"] == "success"
    assert result["final_score"] == 4.6
    assert result["iteration_count"] == 2  # 2 reviews, 1 revision

    # Verify calls
    assert pipeline.toolkit.rephrase_agent.rephrase.call_count == 1
    assert pipeline.toolkit.review_agent.review.call_count == 2
    assert pipeline.toolkit.revise_agent.revise.call_count == 1

    # Verify revised problem was created
    assert mock_db.add.call_count >= 3  # Session + rephrased + revised


# ============================================================================
# Validation Tests
# ============================================================================

def test_crewai_pipeline_invalid_problem():
    """Test CrewAI pipeline validates problem input."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    pipeline = CrewAIPipeline(
        llm_client=mock_llm,
        db_session=mock_db,
    )

    # Invalid problem (no content)
    invalid_problem = create_mock_problem()
    invalid_problem.content = None

    with pytest.raises(ValueError, match="must have content"):
        pipeline.process(
            original_problem=invalid_problem,
            escalation_dimensions=["Dim1", "Dim2", "Dim3"],
        )


def test_crewai_pipeline_insufficient_dimensions():
    """Test CrewAI pipeline validates escalation dimensions."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    pipeline = CrewAIPipeline(
        llm_client=mock_llm,
        db_session=mock_db,
    )

    original_problem = create_mock_problem()

    # Too few dimensions
    with pytest.raises(ValueError, match="at least 3 dimensions"):
        pipeline.process(
            original_problem=original_problem,
            escalation_dimensions=["Dim1", "Dim2"],  # Only 2
        )


# ============================================================================
# AgentToolkit Tests
# ============================================================================

def test_agent_toolkit_initialization():
    """Test AgentToolkit initializes with all agents."""
    mock_llm = Mock(spec=LLMClient)

    toolkit = AgentToolkit(llm_client=mock_llm)

    assert toolkit.rephrase_agent is not None
    assert toolkit.review_agent is not None
    assert toolkit.revise_agent is not None
