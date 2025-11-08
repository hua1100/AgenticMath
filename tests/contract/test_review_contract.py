"""
Contract tests for Review Agent.

Tests that Review Agent adheres to its contract specification:
- Input validation
- Output format parsing
- Score range validation [1.0, 5.0]
- Suggestion extraction
"""

import pytest
from unittest.mock import Mock

from src.agents.review_agent import ReviewAgent
from src.agents.llm_client import LLMClient
from src.parsers.review_parser import ReviewParser, ReviewParseError, ReviewAgentOutput


# ============================================================================
# Parser Contract Tests
# ============================================================================

def test_review_parser_success():
    """Test ReviewParser with valid LLM output."""
    raw_response = """
###thought###
Clarity & Grammar: The question is well-structured and grammatically correct. Units are specified (meters). Score: 4.5/5

Logical Coherence: The relationship between length and width is clearly defined (L = 2W + 3). The perimeter constraint is properly stated. All elements are logically connected. Score: 5.0/5

Mathematical Validity: The problem is solvable using the perimeter formula P = 2(L + W). Substituting L = 2W + 3 into 2(L + W) = 22 gives a linear equation in W. Score: 5.0/5

###rating_score###
[4.5, 5.0, 5.0]

###suggestions###
###Specific improvement 1###
Add explicit instruction to round the answer to a specific number of decimal places (e.g., "Express your answer to 2 decimal places")

###Specific improvement 2###
Consider specifying whether approximate or exact solutions are acceptable
"""

    parsed = ReviewParser.parse(raw_response)

    assert isinstance(parsed, ReviewAgentOutput)
    assert len(parsed.thought_process) > 50
    assert parsed.clarity_grammar_score == 4.5
    assert parsed.logical_coherence_score == 5.0
    assert parsed.mathematical_validity_score == 5.0
    assert parsed.overall_score == 4.83  # (4.5 + 5.0 + 5.0) / 3 = 4.833... -> 4.83
    assert len(parsed.suggestions) == 2
    assert "decimal places" in parsed.suggestions[0].lower()
    assert "approximate or exact" in parsed.suggestions[1].lower()


def test_review_parser_minimal_suggestions():
    """Test ReviewParser with no suggestions (perfect problem)."""
    raw_response = """
###thought###
This is a well-crafted problem with excellent clarity, logic, and mathematical validity. No improvements needed.

###rating_score###
[5.0, 5.0, 5.0]

###suggestions###
"""

    parsed = ReviewParser.parse(raw_response)

    assert parsed.clarity_grammar_score == 5.0
    assert parsed.logical_coherence_score == 5.0
    assert parsed.mathematical_validity_score == 5.0
    assert parsed.overall_score == 5.0
    assert len(parsed.suggestions) == 0


def test_review_parser_low_scores():
    """Test ReviewParser with low scores and many suggestions."""
    raw_response = """
###thought###
Clarity & Grammar: The question has grammatical errors and unclear phrasing. Score: 2.0/5

Logical Coherence: The problem has contradictory constraints and missing information. Score: 1.5/5

Mathematical Validity: The problem cannot be solved uniquely with given information. Score: 1.0/5

###rating_score###
[2.0, 1.5, 1.0]

###suggestions###
###Specific improvement 1###
Fix grammatical error in the second sentence

###Specific improvement 2###
Remove contradictory constraint about perimeter

###Specific improvement 3###
Add missing information about rectangle orientation

###Specific improvement 4###
Ensure the problem has a unique solution
"""

    parsed = ReviewParser.parse(raw_response)

    assert parsed.clarity_grammar_score == 2.0
    assert parsed.logical_coherence_score == 1.5
    assert parsed.mathematical_validity_score == 1.0
    assert parsed.overall_score == 1.5  # (2.0 + 1.5 + 1.0) / 3 = 1.5
    assert len(parsed.suggestions) == 4


def test_review_parser_missing_thought():
    """Test ReviewParser with missing thought section."""
    raw_response = """
###rating_score###
[4.0, 4.5, 5.0]

###suggestions###
###Specific improvement 1###
Add more context
"""

    with pytest.raises(ReviewParseError, match="Could not find ###thought### section"):
        ReviewParser.parse(raw_response)


def test_review_parser_missing_rating():
    """Test ReviewParser with missing rating section."""
    raw_response = """
###thought###
This is my analysis.

###suggestions###
###Specific improvement 1###
Add more context
"""

    with pytest.raises(ReviewParseError, match="Could not find ###rating_score### section"):
        ReviewParser.parse(raw_response)


def test_review_parser_invalid_rating_format():
    """Test ReviewParser with invalid rating format."""
    raw_response = """
###thought###
This is my analysis.

###rating_score###
[Not a valid JSON array]

###suggestions###
###Specific improvement 1###
Add more context
"""

    with pytest.raises(ReviewParseError, match="Failed to parse rating_score"):
        ReviewParser.parse(raw_response)


def test_review_parser_wrong_number_of_scores():
    """Test ReviewParser with wrong number of scores."""
    raw_response = """
###thought###
This is my analysis.

###rating_score###
[4.0, 5.0]

###suggestions###
###Specific improvement 1###
Add more context
"""

    with pytest.raises(ReviewParseError, match="Expected 3 scores, got 2"):
        ReviewParser.parse(raw_response)


def test_review_parser_score_clamping():
    """Test ReviewParser clamps out-of-range scores."""
    raw_response = """
###thought###
This is my analysis.

###rating_score###
[6.0, 0.5, 3.0]

###suggestions###
"""

    parsed = ReviewParser.parse(raw_response)

    # Scores should be clamped to [1.0, 5.0]
    assert parsed.clarity_grammar_score == 5.0  # 6.0 clamped to 5.0
    assert parsed.logical_coherence_score == 1.0  # 0.5 clamped to 1.0
    assert parsed.mathematical_validity_score == 3.0  # 3.0 unchanged


# ============================================================================
# Agent Contract Tests
# ============================================================================

def test_review_agent_input_validation():
    """Test ReviewAgent input validation."""
    mock_llm = Mock(spec=LLMClient)
    agent = ReviewAgent(llm_client=mock_llm)

    # Empty question
    with pytest.raises(ValueError, match="at least 20 characters"):
        agent.review("")

    # Too short question
    with pytest.raises(ValueError, match="at least 20 characters"):
        agent.review("Short question")

    # Valid question (should not raise)
    mock_llm.chat_completion.return_value = {
        "content": """
###thought###
Good problem with clear structure.

###rating_score###
[4.5, 5.0, 5.0]

###suggestions###
""",
        "usage": {"total_tokens": 100},
    }

    output = agent.review("A rectangular garden has a length that is 3 meters more than twice its width.")
    assert output.overall_score > 0


def test_review_agent_execution_with_mock():
    """Test ReviewAgent execution with mocked LLM."""
    mock_llm = Mock(spec=LLMClient)

    # Mock successful LLM response
    mock_llm.chat_completion.return_value = {
        "content": """
###thought###
Clarity & Grammar: Well-structured question with proper grammar. Units specified. Score: 4.5/5
Logical Coherence: All elements logically connected. Clear relationship between variables. Score: 5.0/5
Mathematical Validity: Problem is solvable using perimeter formula. Score: 5.0/5

###rating_score###
[4.5, 5.0, 5.0]

###suggestions###
###Specific improvement 1###
Add explicit rounding instruction for the final answer

###Specific improvement 2###
Consider adding a diagram reference for visual learners
""",
        "usage": {"total_tokens": 250},
    }

    agent = ReviewAgent(llm_client=mock_llm)
    output = agent.review(
        rephrased_question="A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter is 22 meters, find the width."
    )

    # Verify LLM was called
    assert mock_llm.chat_completion.call_count == 1
    call_args = mock_llm.chat_completion.call_args
    assert call_args[1]["temperature"] == 0.3  # Lower temp for consistent scoring

    # Verify output
    assert output.clarity_grammar_score == 4.5
    assert output.logical_coherence_score == 5.0
    assert output.mathematical_validity_score == 5.0
    assert output.overall_score == 4.83
    assert len(output.suggestions) == 2
    assert "rounding" in output.suggestions[0].lower()


def test_review_agent_chinese_support():
    """Test ReviewAgent handles Chinese text."""
    mock_llm = Mock(spec=LLMClient)

    # Mock LLM response in Chinese
    mock_llm.chat_completion.return_value = {
        "content": """
###thought###
清晰度與語法：問題結構清晰，語法正確。評分：4.5/5
邏輯連貫性：所有元素邏輯連貫。評分：5.0/5
數學有效性：問題可用周長公式求解。評分：5.0/5

###rating_score###
[4.5, 5.0, 5.0]

###suggestions###
###Specific improvement 1###
建議明確要求答案的小數位數

###Specific improvement 2###
考慮添加圖示說明
""",
        "usage": {"total_tokens": 200},
    }

    agent = ReviewAgent(llm_client=mock_llm)
    output = agent.review(
        rephrased_question="一個長方形花園的長度比寬度的兩倍多3米。如果周長為22米，求寬度。"
    )

    # Should parse successfully
    assert output.overall_score == 4.83
    assert len(output.suggestions) == 2


def test_review_agent_output_validation():
    """Test ReviewAgent validates output scores."""
    mock_llm = Mock(spec=LLMClient)

    # Mock response with very short thought process
    mock_llm.chat_completion.return_value = {
        "content": """
###thought###
Short

###rating_score###
[4.0, 4.0, 4.0]

###suggestions###
""",
        "usage": {"total_tokens": 50},
    }

    agent = ReviewAgent(llm_client=mock_llm)

    with pytest.raises(ValueError, match="thought_process must be at least 10 characters"):
        agent.review("A rectangular garden has a length that is 3 meters more than twice its width.")


# ============================================================================
# Edge Cases
# ============================================================================

def test_review_parser_case_insensitive():
    """Test ReviewParser is case-insensitive for section markers."""
    raw_response = """
###THOUGHT###
This is my analysis in different case.

###RATING_SCORE###
[4.0, 4.5, 5.0]

###SUGGESTIONS###
###specific improvement 1###
Add more details
"""

    parsed = ReviewParser.parse(raw_response)

    assert parsed.clarity_grammar_score == 4.0
    assert parsed.logical_coherence_score == 4.5
    assert parsed.mathematical_validity_score == 5.0
    assert len(parsed.suggestions) == 1


def test_review_parser_string_numbers():
    """Test ReviewParser handles string numbers in rating."""
    raw_response = """
###thought###
Analysis here.

###rating_score###
["4.0", "4.5", "5.0"]

###suggestions###
"""

    parsed = ReviewParser.parse(raw_response)

    # Should convert string numbers to floats
    assert parsed.clarity_grammar_score == 4.0
    assert parsed.logical_coherence_score == 4.5
    assert parsed.mathematical_validity_score == 5.0
