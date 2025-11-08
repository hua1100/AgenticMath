"""
Integration tests for Full Rephrase Pipeline.

Tests the complete workflow: Rephrase → Review → (Revise loop) → Final Problem
with database persistence of RephraseSession, Problems, and quality tracking.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from src.orchestration.rephrase_pipeline import RephrasePipeline, PipelineResult
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
    source: ProblemSource = ProblemSource.ORIGINAL,
) -> Problem:
    """Create a mock Problem instance."""
    problem = Problem(
        id=uuid4(),
        content=content,
        domain=domain,
        competencies=["linear_equations", "problem_solving"],
        baseline_difficulty=3,
        source=source,
        source_type=SourceType.OCR,
    )
    return problem


def create_mock_rephrase_output(
    rewritten_question: str = "Rephrased question with complexity",
) -> RephraseAgentOutput:
    """Create a mock RephraseAgentOutput."""
    return RephraseAgentOutput(
        stage1_problem_deconstruction="Problem analysis",
        stage2_escalation_protocol="Escalation strategy",
        stage3_rewritten_question=rewritten_question,
        identified_domain="Algebra",
        core_competencies=["linear_equations", "multi_step_reasoning"],
        baseline_difficulty=4,
        applied_dimensions=["Multi-stage Transformation", "Real-world Parameterization", "Conditional Branching"],
    )


def create_mock_review_output(
    overall_score: float,
    suggestions: list = None,
) -> ReviewAgentOutput:
    """Create a mock ReviewAgentOutput."""
    if suggestions is None:
        suggestions = []

    return ReviewAgentOutput(
        thought_process="Quality analysis",
        clarity_grammar_score=overall_score,
        logical_coherence_score=overall_score,
        mathematical_validity_score=overall_score,
        overall_score=overall_score,
        suggestions=suggestions,
    )


def create_mock_revise_output(revised_question: str) -> ReviseAgentOutput:
    """Create a mock ReviseAgentOutput."""
    return ReviseAgentOutput(
        revised_question=revised_question,
        revision_notes="Applied improvements",
    )


# ============================================================================
# Success Cases
# ============================================================================

@patch('src.agents.revise_agent.ReviseAgent')
@patch('src.agents.review_agent.ReviewAgent')
@patch('src.agents.rephrase_agent.RephraseAgent')
def test_pipeline_success_no_revisions(
    mock_rephrase_agent_class,
    mock_review_agent_class,
    mock_revise_agent_class,
):
    """Test pipeline succeeds without needing revisions."""
    # Mock database session
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    # Mock Rephrase Agent
    mock_rephrase_agent = Mock()
    mock_rephrase_agent_class.return_value = mock_rephrase_agent
    mock_rephrase_agent.rephrase.return_value = create_mock_rephrase_output(
        "A well-rephrased complex problem that already meets quality standards."
    )

    # Mock Review Agent - high score, no revisions needed
    mock_review_agent = Mock()
    mock_review_agent_class.return_value = mock_review_agent
    mock_review_agent.review.return_value = create_mock_review_output(
        overall_score=4.7,
        suggestions=[],
    )

    # Create pipeline
    pipeline = RephrasePipeline(
        llm_client=mock_llm,
        db_session=mock_db,
        quality_threshold=4.5,
        max_iterations=5,
    )

    # Create original problem
    original_problem = create_mock_problem()

    # Execute
    result = pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=["Multi-stage Transformation", "Real-world Parameterization", "Conditional Branching"],
    )

    # Verify result
    assert isinstance(result, PipelineResult)
    assert result.final_status == SessionStatus.SUCCESS
    assert result.final_score == 4.7
    assert result.iteration_count == 1  # Only one review, no revisions
    assert len(result.escalation_dimensions) == 3

    # Verify rephrase was called
    assert mock_rephrase_agent.rephrase.call_count == 1

    # Verify review was called once
    assert mock_review_agent.review.call_count == 1

    # Verify database operations
    assert mock_db.add.call_count >= 2  # Session + rephrased problem
    assert mock_db.commit.call_count >= 1  # At least one commit
    assert mock_db.flush.call_count >= 1


@patch('src.agents.revise_agent.ReviseAgent')
@patch('src.agents.review_agent.ReviewAgent')
@patch('src.agents.rephrase_agent.RephraseAgent')
def test_pipeline_success_with_revisions(
    mock_rephrase_agent_class,
    mock_review_agent_class,
    mock_revise_agent_class,
):
    """Test pipeline succeeds after multiple revisions."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    # Mock Rephrase Agent
    mock_rephrase_agent = Mock()
    mock_rephrase_agent_class.return_value = mock_rephrase_agent
    mock_rephrase_agent.rephrase.return_value = create_mock_rephrase_output(
        "Initial rephrased problem needing improvements."
    )

    # Mock Review Agent - first low, then high
    mock_review_agent = Mock()
    mock_review_agent_class.return_value = mock_review_agent
    mock_review_agent.review.side_effect = [
        create_mock_review_output(3.5, ["Add answer format"]),
        create_mock_review_output(4.2, ["Add units"]),
        create_mock_review_output(4.6, []),
    ]

    # Mock Revise Agent
    mock_revise_agent = Mock()
    mock_revise_agent_class.return_value = mock_revise_agent
    mock_revise_agent.revise.side_effect = [
        create_mock_revise_output("Improved problem v1."),
        create_mock_revise_output("Improved problem v2 with all fixes."),
    ]

    # Create pipeline
    pipeline = RephrasePipeline(
        llm_client=mock_llm,
        db_session=mock_db,
        quality_threshold=4.5,
        max_iterations=5,
    )

    original_problem = create_mock_problem()

    # Execute
    result = pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=["Multi-stage Transformation", "Real-world Parameterization", "Conditional Branching"],
    )

    # Verify result
    assert result.final_status == SessionStatus.SUCCESS
    assert result.final_score == 4.6
    assert result.iteration_count == 3  # 3 reviews, 2 revisions

    # Verify calls
    assert mock_rephrase_agent.rephrase.call_count == 1
    assert mock_review_agent.review.call_count == 3
    assert mock_revise_agent.revise.call_count == 2

    # Verify revised problem was created
    assert mock_db.add.call_count >= 3  # Session + rephrased + revised


@patch('src.agents.revise_agent.ReviseAgent')
@patch('src.agents.review_agent.ReviewAgent')
@patch('src.agents.rephrase_agent.RephraseAgent')
def test_pipeline_max_iterations_exceeded(
    mock_rephrase_agent_class,
    mock_review_agent_class,
    mock_revise_agent_class,
):
    """Test pipeline stops at max iterations."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    # Mock Rephrase Agent
    mock_rephrase_agent = Mock()
    mock_rephrase_agent_class.return_value = mock_rephrase_agent
    mock_rephrase_agent.rephrase.return_value = create_mock_rephrase_output(
        "Problem that won't reach threshold."
    )

    # Mock Review Agent - always below threshold
    mock_review_agent = Mock()
    mock_review_agent_class.return_value = mock_review_agent
    mock_review_agent.review.return_value = create_mock_review_output(
        3.5,
        ["Improve clarity"],
    )

    # Mock Revise Agent
    mock_revise_agent = Mock()
    mock_revise_agent_class.return_value = mock_revise_agent
    mock_revise_agent.revise.return_value = create_mock_revise_output(
        "Slightly improved but still not good enough."
    )

    # Create pipeline with low max_iterations
    pipeline = RephrasePipeline(
        llm_client=mock_llm,
        db_session=mock_db,
        quality_threshold=4.5,
        max_iterations=3,
    )

    original_problem = create_mock_problem()

    # Execute
    result = pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=["Multi-stage Transformation", "Real-world Parameterization", "Conditional Branching"],
    )

    # Verify result
    assert result.final_status == SessionStatus.MAX_ITERATIONS_EXCEEDED
    assert result.final_score == 3.5
    assert result.iteration_count == 3


# ============================================================================
# Validation Tests
# ============================================================================

def test_pipeline_invalid_problem():
    """Test pipeline validates problem input."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    pipeline = RephrasePipeline(
        llm_client=mock_llm,
        db_session=mock_db,
    )

    # Invalid problem (no content)
    invalid_problem = create_mock_problem()
    invalid_problem.content = None

    with pytest.raises(ValueError, match="must have content"):
        pipeline.process(
            original_problem=invalid_problem,
            escalation_dimensions=["Dimension1", "Dimension2", "Dimension3"],
        )


def test_pipeline_insufficient_dimensions():
    """Test pipeline validates escalation dimensions."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    pipeline = RephrasePipeline(
        llm_client=mock_llm,
        db_session=mock_db,
    )

    original_problem = create_mock_problem()

    # Too few dimensions
    with pytest.raises(ValueError, match="at least 3 dimensions"):
        pipeline.process(
            original_problem=original_problem,
            escalation_dimensions=["Dimension1", "Dimension2"],  # Only 2
        )


# ============================================================================
# Result Conversion Tests
# ============================================================================

def test_pipeline_result_to_dict():
    """Test PipelineResult.to_dict() conversion."""
    session_id = uuid4()
    original_id = uuid4()
    final_id = uuid4()

    result = PipelineResult(
        session_id=session_id,
        original_problem_id=original_id,
        final_problem_id=final_id,
        final_status=SessionStatus.SUCCESS,
        final_question="Final question",
        final_score=4.7,
        iteration_count=2,
        total_time_ms=15000,
        escalation_dimensions=["Dim1", "Dim2", "Dim3"],
    )

    result_dict = result.to_dict()

    assert result_dict["session_id"] == str(session_id)
    assert result_dict["original_problem_id"] == str(original_id)
    assert result_dict["final_problem_id"] == str(final_id)
    assert result_dict["final_status"] == "success"
    assert result_dict["final_question"] == "Final question"
    assert result_dict["final_score"] == 4.7
    assert result_dict["iteration_count"] == 2
    assert result_dict["total_time_ms"] == 15000
    assert len(result_dict["escalation_dimensions"]) == 3


# ============================================================================
# Database Integration Tests
# ============================================================================

@patch('src.agents.revise_agent.ReviseAgent')
@patch('src.agents.review_agent.ReviewAgent')
@patch('src.agents.rephrase_agent.RephraseAgent')
def test_pipeline_creates_rephrase_session(
    mock_rephrase_agent_class,
    mock_review_agent_class,
    mock_revise_agent_class,
):
    """Test pipeline creates RephraseSession record."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    # Mock agents
    mock_rephrase_agent = Mock()
    mock_rephrase_agent_class.return_value = mock_rephrase_agent
    mock_rephrase_agent.rephrase.return_value = create_mock_rephrase_output()

    mock_review_agent = Mock()
    mock_review_agent_class.return_value = mock_review_agent
    mock_review_agent.review.return_value = create_mock_review_output(4.7)

    pipeline = RephrasePipeline(
        llm_client=mock_llm,
        db_session=mock_db,
        quality_threshold=4.5,
    )

    original_problem = create_mock_problem()

    result = pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=["Dim1", "Dim2", "Dim3"],
    )

    # Verify session was created
    assert result.session_id is not None
    assert result.original_problem_id == original_problem.id

    # Verify database operations
    assert mock_db.add.called
    assert mock_db.commit.called


@patch('src.agents.revise_agent.ReviseAgent')
@patch('src.agents.review_agent.ReviewAgent')
@patch('src.agents.rephrase_agent.RephraseAgent')
def test_pipeline_links_problems_via_parent_id(
    mock_rephrase_agent_class,
    mock_review_agent_class,
    mock_revise_agent_class,
):
    """Test pipeline links problems via parent_id."""
    mock_db = MagicMock()
    mock_llm = Mock(spec=LLMClient)

    # Track created problems
    created_problems = []

    def mock_add(obj):
        if isinstance(obj, Problem):
            created_problems.append(obj)

    mock_db.add.side_effect = mock_add

    # Mock agents
    mock_rephrase_agent = Mock()
    mock_rephrase_agent_class.return_value = mock_rephrase_agent
    mock_rephrase_agent.rephrase.return_value = create_mock_rephrase_output()

    mock_review_agent = Mock()
    mock_review_agent_class.return_value = mock_review_agent
    mock_review_agent.review.side_effect = [
        create_mock_review_output(3.5, ["Fix"]),
        create_mock_review_output(4.7),
    ]

    mock_revise_agent = Mock()
    mock_revise_agent_class.return_value = mock_revise_agent
    mock_revise_agent.revise.return_value = create_mock_revise_output("Revised")

    pipeline = RephrasePipeline(
        llm_client=mock_llm,
        db_session=mock_db,
        quality_threshold=4.5,
    )

    original_problem = create_mock_problem()

    pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=["Dim1", "Dim2", "Dim3"],
    )

    # Verify problem chain
    # Should have: rephrased (parent=original) + revised (parent=rephrased)
    assert len(created_problems) >= 2

    # First created is rephrased
    rephrased = created_problems[0]
    assert rephrased.source == ProblemSource.REPHRASED
    assert rephrased.parent_id == original_problem.id

    # Second created is revised
    if len(created_problems) > 1:
        revised = created_problems[1]
        assert revised.source == ProblemSource.REVISED
        assert revised.parent_id == rephrased.id
