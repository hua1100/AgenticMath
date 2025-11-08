"""
Integration tests for Review-Revise iteration loop.

Tests the IterationManager orchestration of Review → Revise cycles
until quality threshold is met or maximum iterations are reached.
"""

import pytest
from unittest.mock import Mock, MagicMock

from src.orchestration.iteration_manager import IterationManager, IterationResult
from src.agents.review_agent import ReviewAgent
from src.agents.revise_agent import ReviseAgent
from src.parsers.review_parser import ReviewAgentOutput
from src.parsers.revise_parser import ReviseAgentOutput
from src.models.rephrase_session import SessionStatus


# ============================================================================
# Mock Helpers
# ============================================================================

def create_mock_review_output(
    overall_score: float,
    suggestions: list = None,
) -> ReviewAgentOutput:
    """Create a mock ReviewAgentOutput."""
    if suggestions is None:
        suggestions = []

    return ReviewAgentOutput(
        thought_process="Analysis of the problem quality",
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
        revision_notes="Applied suggested improvements",
    )


# ============================================================================
# Success Cases
# ============================================================================

def test_iteration_manager_success_first_try():
    """Test IterationManager succeeds on first iteration."""
    # Mock agents
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    # First review scores above threshold
    mock_review_agent.review.return_value = create_mock_review_output(
        overall_score=4.7,
        suggestions=[],
    )

    # Create manager
    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.5,
        max_iterations=5,
    )

    # Execute
    result = manager.iterate_until_quality(
        initial_question="A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter is 22 meters, find the width.",
    )

    # Verify
    assert result.final_status == SessionStatus.SUCCESS
    assert result.final_score == 4.7
    assert result.iteration_count == 1
    assert len(result.quality_assessments) == 1
    assert len(result.revision_history) == 1  # Only initial question

    # Review should be called once
    assert mock_review_agent.review.call_count == 1

    # Revise should NOT be called (score already above threshold)
    assert mock_revise_agent.revise.call_count == 0


def test_iteration_manager_success_after_revisions():
    """Test IterationManager succeeds after multiple revisions."""
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    # First 2 reviews below threshold, third above
    mock_review_agent.review.side_effect = [
        create_mock_review_output(
            overall_score=3.5,
            suggestions=["Add answer format specification"],
        ),
        create_mock_review_output(
            overall_score=4.0,
            suggestions=["Add units clarification"],
        ),
        create_mock_review_output(
            overall_score=4.6,
            suggestions=[],
        ),
    ]

    # Revise returns improved questions
    mock_revise_agent.revise.side_effect = [
        create_mock_revise_output(
            "A rectangular garden has length 3m more than twice width. Perimeter is 22m. Find width. Express as decimal."
        ),
        create_mock_revise_output(
            "A rectangular garden has length 3m more than twice width. Perimeter is 22m. Find width in meters. Express as decimal rounded to 2 places."
        ),
    ]

    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.5,
        max_iterations=5,
    )

    result = manager.iterate_until_quality(
        initial_question="A rectangular garden has length 3m more than twice width. Perimeter is 22m. Find width.",
    )

    # Verify success after 3 iterations (2 revisions)
    assert result.final_status == SessionStatus.SUCCESS
    assert result.final_score == 4.6
    assert result.iteration_count == 3
    assert len(result.quality_assessments) == 3
    assert len(result.revision_history) == 3  # Initial + 2 revisions

    # Verify calls
    assert mock_review_agent.review.call_count == 3
    assert mock_revise_agent.revise.call_count == 2


# ============================================================================
# Max Iterations Cases
# ============================================================================

def test_iteration_manager_max_iterations_exceeded():
    """Test IterationManager stops at max iterations."""
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    # All reviews below threshold
    mock_review_agent.review.return_value = create_mock_review_output(
        overall_score=3.5,
        suggestions=["Improve clarity"],
    )

    # Revise returns slightly improved questions
    mock_revise_agent.revise.return_value = create_mock_revise_output(
        "A slightly improved question that still doesn't meet threshold.",
    )

    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.5,
        max_iterations=3,  # Lower limit for testing
    )

    result = manager.iterate_until_quality(
        initial_question="A poorly worded math problem that needs multiple revisions.",
    )

    # Verify max iterations reached
    assert result.final_status == SessionStatus.MAX_ITERATIONS_EXCEEDED
    assert result.final_score == 3.5
    assert result.iteration_count == 3
    assert len(result.quality_assessments) == 3
    assert len(result.revision_history) == 3  # Initial + 2 revisions (not 3 because last iteration stops)

    # Verify calls
    assert mock_review_agent.review.call_count == 3
    assert mock_revise_agent.revise.call_count == 2  # Max iterations prevents last revise


def test_iteration_manager_no_suggestions():
    """Test IterationManager handles case with no suggestions."""
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    # Review scores below threshold but provides no suggestions
    mock_review_agent.review.return_value = create_mock_review_output(
        overall_score=4.0,
        suggestions=[],  # No suggestions!
    )

    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.5,
        max_iterations=5,
    )

    result = manager.iterate_until_quality(
        initial_question="A rectangular garden problem with some issues.",
    )

    # Should stop early because no suggestions means can't improve
    assert result.final_status == SessionStatus.MAX_ITERATIONS_EXCEEDED
    assert result.final_score == 4.0
    assert result.iteration_count == 1
    assert len(result.quality_assessments) == 1

    # Revise should NOT be called (no suggestions)
    assert mock_revise_agent.revise.call_count == 0


# ============================================================================
# Validation and Error Cases
# ============================================================================

def test_iteration_manager_invalid_initial_question():
    """Test IterationManager validates initial question."""
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.5,
        max_iterations=5,
    )

    # Empty question
    with pytest.raises(ValueError, match="at least 20 characters"):
        manager.iterate_until_quality(initial_question="")

    # Too short question
    with pytest.raises(ValueError, match="at least 20 characters"):
        manager.iterate_until_quality(initial_question="Find x.")


def test_iteration_manager_review_failure():
    """Test IterationManager handles review agent failure."""
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    # Review raises exception
    mock_review_agent.review.side_effect = Exception("LLM API error")

    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.5,
        max_iterations=5,
    )

    # Should propagate exception
    with pytest.raises(Exception, match="LLM API error"):
        manager.iterate_until_quality(
            initial_question="A rectangular garden problem.",
        )


def test_iteration_manager_revise_failure():
    """Test IterationManager handles revise agent failure."""
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    # First review below threshold
    mock_review_agent.review.return_value = create_mock_review_output(
        overall_score=3.5,
        suggestions=["Improve clarity"],
    )

    # Revise raises exception
    mock_revise_agent.revise.side_effect = Exception("Validation error")

    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.5,
        max_iterations=5,
    )

    # Should propagate exception
    with pytest.raises(Exception, match="Validation error"):
        manager.iterate_until_quality(
            initial_question="A rectangular garden problem.",
        )


# ============================================================================
# Result Conversion
# ============================================================================

def test_iteration_result_to_dict():
    """Test IterationResult.to_dict() conversion."""
    result = IterationResult(
        final_question="Final improved question",
        final_score=4.7,
        iteration_count=3,
        final_status=SessionStatus.SUCCESS,
        quality_assessments=[
            {"overall_score": 3.5, "suggestions": ["Fix A"]},
            {"overall_score": 4.2, "suggestions": ["Fix B"]},
            {"overall_score": 4.7, "suggestions": []},
        ],
        revision_history=["Question v1", "Question v2", "Question v3"],
    )

    result_dict = result.to_dict()

    assert result_dict["final_question"] == "Final improved question"
    assert result_dict["final_score"] == 4.7
    assert result_dict["iteration_count"] == 3
    assert result_dict["final_status"] == "success"
    assert len(result_dict["quality_assessments"]) == 3
    assert len(result_dict["revision_history"]) == 3


# ============================================================================
# Configuration Tests
# ============================================================================

def test_iteration_manager_custom_threshold():
    """Test IterationManager with custom quality threshold."""
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    # Score is 4.3 (would fail default 4.5, but pass 4.0)
    mock_review_agent.review.return_value = create_mock_review_output(
        overall_score=4.3,
        suggestions=[],
    )

    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.0,  # Lower threshold
        max_iterations=5,
    )

    result = manager.iterate_until_quality(
        initial_question="A rectangular garden problem.",
    )

    # Should succeed with lower threshold
    assert result.final_status == SessionStatus.SUCCESS
    assert result.final_score == 4.3


def test_iteration_manager_single_iteration_limit():
    """Test IterationManager with max_iterations=1."""
    mock_review_agent = Mock(spec=ReviewAgent)
    mock_revise_agent = Mock(spec=ReviseAgent)

    # Score below threshold
    mock_review_agent.review.return_value = create_mock_review_output(
        overall_score=3.5,
        suggestions=["Improve"],
    )

    manager = IterationManager(
        review_agent=mock_review_agent,
        revise_agent=mock_revise_agent,
        quality_threshold=4.5,
        max_iterations=1,  # Only 1 iteration allowed
    )

    result = manager.iterate_until_quality(
        initial_question="A rectangular garden problem.",
    )

    # Should reach max iterations immediately
    assert result.final_status == SessionStatus.MAX_ITERATIONS_EXCEEDED
    assert result.iteration_count == 1
    assert mock_review_agent.review.call_count == 1
    assert mock_revise_agent.revise.call_count == 0  # No revision because max reached
