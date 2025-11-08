"""
Contract tests for Revise Agent.

Tests that Revise Agent adheres to its contract specification:
- Input validation
- Output format parsing
- Mathematical preservation
- Revision validation
"""

import pytest
from unittest.mock import Mock

from src.agents.revise_agent import ReviseAgent
from src.agents.llm_client import LLMClient
from src.parsers.revise_parser import (
    ReviseParser,
    ReviseParseError,
    ReviseAgentOutput,
    validate_mathematical_preservation,
    validate_revision_changes,
    validate_revision_length,
)


# ============================================================================
# Parser Contract Tests
# ============================================================================

def test_revise_parser_success():
    """Test ReviseParser with valid LLM output."""
    raw_response = """
###revised_question###
A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places, including units (meters) in your final answer.

###revision_notes###
Added explicit answer format requirement ('decimal rounded to two decimal places') to address clarity suggestion. Included unit specification for final answer. Preserved all mathematical constraints and relationships from original problem.
"""

    parsed = ReviseParser.parse(raw_response)

    assert isinstance(parsed, ReviseAgentOutput)
    assert len(parsed.revised_question) > 50
    assert "decimal" in parsed.revised_question.lower()
    assert "two decimal places" in parsed.revised_question.lower()
    assert len(parsed.revision_notes) > 50
    assert "preserved" in parsed.revision_notes.lower()


def test_revise_parser_minimal_notes():
    """Test ReviseParser with minimal revision notes."""
    raw_response = """
###revised_question###
A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter is 22 meters, find the width in meters. Express your answer as a decimal.

###revision_notes###
Added answer format specification.
"""

    parsed = ReviseParser.parse(raw_response)

    assert len(parsed.revised_question) > 0
    assert len(parsed.revision_notes) > 0
    assert "format" in parsed.revision_notes.lower()


def test_revise_parser_no_notes():
    """Test ReviseParser with missing revision notes section."""
    raw_response = """
###revised_question###
A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter is 22 meters, find the width. Express as decimal.
"""

    parsed = ReviseParser.parse(raw_response)

    # Notes are optional
    assert len(parsed.revised_question) > 0
    assert parsed.revision_notes == ""


def test_revise_parser_missing_question():
    """Test ReviseParser with missing revised_question section."""
    raw_response = """
###revision_notes###
Made some improvements.
"""

    with pytest.raises(ReviseParseError, match="Could not find ###revised_question### section"):
        ReviseParser.parse(raw_response)


def test_revise_parser_empty_question():
    """Test ReviseParser with empty revised_question section."""
    raw_response = """
###revised_question###

###revision_notes###
Made improvements.
"""

    with pytest.raises(ReviseParseError, match="revised_question section is empty"):
        ReviseParser.parse(raw_response)


def test_revise_parser_empty_response():
    """Test ReviseParser with completely empty response."""
    with pytest.raises(ReviseParseError, match="Empty response received"):
        ReviseParser.parse("")


def test_revise_parser_case_insensitive():
    """Test ReviseParser is case-insensitive for section markers."""
    raw_response = """
###REVISED_QUESTION###
A rectangular garden has length 3m more than twice width. Perimeter is 22m. Find width as decimal.

###REVISION_NOTES###
Added format specification.
"""

    parsed = ReviseParser.parse(raw_response)

    assert len(parsed.revised_question) > 0
    assert len(parsed.revision_notes) > 0


# ============================================================================
# Validation Function Tests
# ============================================================================

def test_validate_mathematical_preservation_success():
    """Test mathematical preservation with valid revision."""
    original = "A rectangle has length 2w+3 and perimeter 22. Find w."
    revised = "A rectangle has a length that is 3 more than twice its width. If the perimeter is 22 meters, find the width w."

    assert validate_mathematical_preservation(original, revised) is True


def test_validate_mathematical_preservation_removed_numbers():
    """Test mathematical preservation fails when numbers are removed."""
    original = "A rectangle has length 2w+3 and perimeter 22. Find w."
    revised = "A rectangle has some length. Find the width."

    # Should fail - removed multiple numbers (2, 3, 22)
    assert validate_mathematical_preservation(original, revised) is False


def test_validate_mathematical_preservation_removed_keywords():
    """Test mathematical preservation fails when keywords are removed."""
    original = "Find the width of a rectangle with perimeter 22."
    revised = "A rectangle with perimeter 22."

    # Should fail - removed "find" keyword
    assert validate_mathematical_preservation(original, revised) is False


def test_validate_mathematical_preservation_chinese():
    """Test mathematical preservation with Chinese keywords."""
    original = "求寬度，如果長方形周長為22米。"
    revised = "如果長方形周長為22米，請求出寬度。"

    assert validate_mathematical_preservation(original, revised) is True


def test_validate_revision_changes_success():
    """Test revision changes validation with actual changes."""
    original = "Find the width."
    revised = "Find the width of the rectangle."

    assert validate_revision_changes(original, revised) is True


def test_validate_revision_changes_identical():
    """Test revision changes validation fails when identical."""
    original = "Find the width of the rectangle."
    revised = "Find the width of the rectangle."

    assert validate_revision_changes(original, revised) is False


def test_validate_revision_length_acceptable():
    """Test revision length validation with acceptable change."""
    original = "A rectangle has length 2w+3 and perimeter 22. Find w."
    revised = "A rectangle has length that is 3 more than twice its width. If perimeter is 22 meters, find the width. Express as decimal."

    # Length change is within 50%
    assert validate_revision_length(original, revised) is True


def test_validate_revision_length_excessive():
    """Test revision length validation fails with excessive change."""
    original = "Find w."
    revised = "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places."

    # Length increased by more than 50%
    assert validate_revision_length(original, revised) is False


# ============================================================================
# Agent Contract Tests
# ============================================================================

def test_revise_agent_input_validation_empty_question():
    """Test ReviseAgent validates empty question."""
    mock_llm = Mock(spec=LLMClient)
    agent = ReviseAgent(llm_client=mock_llm)

    with pytest.raises(ValueError, match="at least 20 characters"):
        agent.revise("", ["Add format"])


def test_revise_agent_input_validation_short_question():
    """Test ReviseAgent validates short question."""
    mock_llm = Mock(spec=LLMClient)
    agent = ReviseAgent(llm_client=mock_llm)

    with pytest.raises(ValueError, match="at least 20 characters"):
        agent.revise("Find x.", ["Add context"])


def test_revise_agent_input_validation_empty_suggestions():
    """Test ReviseAgent validates empty suggestions list."""
    mock_llm = Mock(spec=LLMClient)
    agent = ReviseAgent(llm_client=mock_llm)

    with pytest.raises(ValueError, match="at least 1 suggestion"):
        agent.revise("A rectangular garden has length 3m more than twice width.", [])


def test_revise_agent_input_validation_empty_suggestion_item():
    """Test ReviseAgent validates empty suggestion items."""
    mock_llm = Mock(spec=LLMClient)
    agent = ReviseAgent(llm_client=mock_llm)

    with pytest.raises(ValueError, match="Suggestion .* is empty"):
        agent.revise(
            "A rectangular garden has length 3m more than twice width.",
            ["Add format", "", "Add units"]
        )


def test_revise_agent_execution_with_mock():
    """Test ReviseAgent execution with mocked LLM."""
    mock_llm = Mock(spec=LLMClient)

    # Mock successful LLM response
    mock_llm.chat_completion.return_value = {
        "content": """
###revised_question###
A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places, including units (meters) in your final answer.

###revision_notes###
Added explicit answer format requirement ('decimal rounded to two decimal places') to address clarity suggestion. Included unit specification for final answer. Preserved all mathematical constraints and relationships: length = 2×width + 3 meters, perimeter = 22 meters.
""",
        "usage": {"total_tokens": 300},
    }

    agent = ReviseAgent(llm_client=mock_llm)
    output = agent.revise(
        rephrased_question="A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter is 22 meters, find the width.",
        suggestions=[
            "Explicitly state answer format: 'Express as decimal rounded to two decimal places'",
            "Add units clarification for final answer"
        ]
    )

    # Verify LLM was called
    assert mock_llm.chat_completion.call_count == 1
    call_args = mock_llm.chat_completion.call_args
    assert call_args[1]["temperature"] == 0.3

    # Verify output
    assert "decimal" in output.revised_question.lower()
    assert "two decimal places" in output.revised_question.lower()
    assert len(output.revision_notes) > 50
    assert "preserved" in output.revision_notes.lower()


def test_revise_agent_chinese_support():
    """Test ReviseAgent handles Chinese text."""
    mock_llm = Mock(spec=LLMClient)

    # Mock LLM response in Chinese
    mock_llm.chat_completion.return_value = {
        "content": """
###revised_question###
一個長方形花園的長度比寬度的兩倍多3米。如果周長為22米，求寬度。請將答案表示為四捨五入到小數點後兩位的十進制數，並包含單位（米）。

###revision_notes###
添加了明確的答案格式要求（"小數點後兩位的十進制數"）以提高清晰度。包含了最終答案的單位說明。保留了所有數學約束和關係。
""",
        "usage": {"total_tokens": 250},
    }

    agent = ReviseAgent(llm_client=mock_llm)
    output = agent.revise(
        rephrased_question="一個長方形花園的長度比寬度的兩倍多3米。如果周長為22米，求寬度。",
        suggestions=["添加答案格式說明", "包含單位要求"]
    )

    # Should parse successfully
    assert len(output.revised_question) > 50
    assert len(output.revision_notes) > 20


def test_revise_agent_output_validation_no_changes():
    """Test ReviseAgent validates that changes were made."""
    mock_llm = Mock(spec=LLMClient)

    # Mock response with identical question
    mock_llm.chat_completion.return_value = {
        "content": """
###revised_question###
A rectangular garden has a length that is 3 meters more than twice its width.

###revision_notes###
No changes needed.
""",
        "usage": {"total_tokens": 100},
    }

    agent = ReviseAgent(llm_client=mock_llm)

    with pytest.raises(ValueError, match="identical to original"):
        agent.revise(
            rephrased_question="A rectangular garden has a length that is 3 meters more than twice its width.",
            suggestions=["Add format specification"]
        )


def test_revise_agent_output_validation_removed_math():
    """Test ReviseAgent validates mathematical preservation."""
    mock_llm = Mock(spec=LLMClient)

    # Mock response that removed mathematical content
    mock_llm.chat_completion.return_value = {
        "content": """
###revised_question###
A garden has some dimensions. Calculate something.

###revision_notes###
Simplified the question.
""",
        "usage": {"total_tokens": 100},
    }

    agent = ReviseAgent(llm_client=mock_llm)

    with pytest.raises(ValueError, match="failed to preserve mathematical content"):
        agent.revise(
            rephrased_question="A rectangular garden has length 2w+3 and perimeter 22. Find w.",
            suggestions=["Clarify the question"]
        )


def test_revise_agent_output_validation_excessive_length():
    """Test ReviseAgent validates length change."""
    mock_llm = Mock(spec=LLMClient)

    # Mock response that drastically increased length
    mock_llm.chat_completion.return_value = {
        "content": """
###revised_question###
A rectangular garden, which is a four-sided polygon with opposite sides equal and all angles being right angles, has a length measurement that can be expressed as being exactly 3 meters (where a meter is defined as the distance traveled by light in vacuum in 1/299,792,458 of a second) more than exactly twice (meaning two times, or doubled) its width measurement. Furthermore, if we consider the total perimeter, which is the sum of all four sides of this rectangular garden, and this perimeter equals exactly 22 meters, then we ask you to calculate, determine, and find the precise numerical value of the width of this garden, expressed as a decimal number rounded to exactly two decimal places after the decimal point.

###revision_notes###
Made the question much more detailed and explicit.
""",
        "usage": {"total_tokens": 200},
    }

    agent = ReviseAgent(llm_client=mock_llm)

    with pytest.raises(ValueError, match="length changed by more than 150%"):
        agent.revise(
            rephrased_question="Find the width of a rectangle.",
            suggestions=["Add more context"]
        )


# ============================================================================
# Edge Cases
# ============================================================================

def test_revise_parser_multiline_question():
    """Test ReviseParser handles multiline questions."""
    raw_response = """
###revised_question###
A rectangular garden has a length that is 3 meters
more than twice its width. If the perimeter of the
garden is 22 meters, find the width.

Express your answer as a decimal rounded to two
decimal places.

###revision_notes###
Added line breaks for readability and answer format.
"""

    parsed = ReviseParser.parse(raw_response)

    assert "3 meters" in parsed.revised_question
    assert "22 meters" in parsed.revised_question
    assert "decimal" in parsed.revised_question.lower()


def test_validate_mathematical_preservation_added_numbers():
    """Test mathematical preservation allows adding numbers for clarification."""
    original = "A rectangle has some dimensions. Find the width."
    revised = "A rectangle has length 3m more than twice width. Perimeter is 22m. Find width."

    # Should pass - adding numbers is OK
    assert validate_mathematical_preservation(original, revised) is True
