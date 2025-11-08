"""
Contract tests for Rephrase Agent.

Tests that Rephrase Agent adheres to the contract specification defined in
specs/001-multi-agent-problem-generator/contracts/rephrase-agent.md
"""

import pytest
from unittest.mock import Mock, patch

from src.agents import RephraseAgent, VALID_ESCALATION_DIMENSIONS
from src.parsers.rephrase_parser import RephraseParser, RephraseParseError, RephraseAgentOutput


# Sample LLM response matching the contract format
SAMPLE_LLM_RESPONSE = """Stage 1 #Problem Deconstruction#:
Domain Identification: Algebra
Core Competencies: Linear equations, variable isolation, basic arithmetic
Baseline Difficulty: 1

Stage 2 #Escalation Protocol#:
1. Multi-stage Transformation: Convert to multi-step problem requiring perimeter calculation first
2. Cross-domain Integration: Combine algebra with basic geometry (perimeter formula)
3. Real-world Parameterization: Embed in garden/construction context with realistic constraints

Stage 3 #Finally Rewritten question#:
A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden in meters.
"""


def test_valid_escalation_dimensions():
    """Test that all valid escalation dimensions are defined."""
    assert len(VALID_ESCALATION_DIMENSIONS) == 7
    assert "Multi-stage Transformation" in VALID_ESCALATION_DIMENSIONS
    assert "Cross-domain Integration" in VALID_ESCALATION_DIMENSIONS
    assert "Real-world Parameterization" in VALID_ESCALATION_DIMENSIONS


def test_rephrase_parser_success():
    """Test RephraseParser successfully parses valid output."""
    parsed = RephraseParser.parse(SAMPLE_LLM_RESPONSE)

    # Verify all stages present
    assert "Domain Identification: Algebra" in parsed.stage1_problem_deconstruction
    assert "Multi-stage Transformation" in parsed.stage2_escalation_protocol
    assert "rectangular garden" in parsed.stage3_rewritten_question

    # Verify extracted metadata
    assert parsed.identified_domain == "Algebra"
    assert len(parsed.core_competencies) >= 1
    assert 1 <= parsed.baseline_difficulty <= 5
    assert len(parsed.applied_dimensions) >= 3
    assert "Multi-stage Transformation" in parsed.applied_dimensions


def test_rephrase_parser_missing_stage():
    """Test parser raises error if stage is missing."""
    invalid_response = """Stage 1 #Problem Deconstruction#:
Domain: Algebra

Stage 3 #Finally Rewritten question#:
Some question
"""
    with pytest.raises(RephraseParseError, match="Could not find Stage 2"):
        RephraseParser.parse(invalid_response)


def test_rephrase_agent_input_validation():
    """Test Rephrase Agent input validation."""
    agent = RephraseAgent()

    # Test minimum length validation
    with pytest.raises(ValueError, match="at least 10 characters"):
        agent.rephrase("Short", ["Multi-stage Transformation"] * 3)

    # Test minimum dimensions validation
    with pytest.raises(ValueError, match="at least 3 dimensions"):
        agent.rephrase("Valid problem content here", ["Multi-stage Transformation"])

    # Test invalid dimension names
    with pytest.raises(ValueError, match="Invalid escalation dimensions"):
        agent.rephrase(
            "Valid problem content here",
            ["Invalid Dimension", "Multi-stage Transformation", "Cross-domain Integration"]
        )


@patch("src.agents.rephrase_agent.LLMClient")
def test_rephrase_agent_success(mock_llm_class):
    """Test successful rephrase execution."""
    # Mock LLM response
    mock_llm = Mock()
    mock_llm.chat_completion.return_value = {
        "content": SAMPLE_LLM_RESPONSE,
        "usage": {"total_tokens": 500, "prompt_tokens": 200, "completion_tokens": 300},
        "finish_reason": "stop"
    }
    mock_llm_class.return_value = mock_llm

    # Create agent with mocked LLM
    agent = RephraseAgent(llm_client=mock_llm)

    # Execute rephrase
    result = agent.rephrase(
        problem_content="Solve for x: 2x + 3 = 11",
        escalation_dimensions=[
            "Multi-stage Transformation",
            "Cross-domain Integration",
            "Real-world Parameterization"
        ]
    )

    # Verify result
    assert result.identified_domain == "Algebra"
    assert len(result.applied_dimensions) >= 3
    assert len(result.stage3_rewritten_question) > 0
    assert "garden" in result.stage3_rewritten_question.lower()

    # Verify LLM was called
    mock_llm.chat_completion.assert_called_once()
    call_args = mock_llm.chat_completion.call_args[0][0]
    assert len(call_args) == 1
    assert "Stage 1 #Problem Deconstruction#" in call_args[0]["content"]


@patch("src.agents.rephrase_agent.LLMClient")
def test_rephrase_agent_with_database_logging(mock_llm_class):
    """Test that agent logs execution to database."""
    from unittest.mock import MagicMock

    # Mock LLM
    mock_llm = Mock()
    mock_llm.chat_completion.return_value = {
        "content": SAMPLE_LLM_RESPONSE,
        "usage": {"total_tokens": 500, "prompt_tokens": 200, "completion_tokens": 300},
        "finish_reason": "stop"
    }
    mock_llm_class.return_value = mock_llm

    # Mock database session
    mock_db = MagicMock()

    # Create agent with db
    agent = RephraseAgent(llm_client=mock_llm, db=mock_db)

    # Execute
    agent.rephrase(
        problem_content="Test problem for database logging",
        escalation_dimensions=["Multi-stage Transformation", "Cross-domain Integration", "Real-world Parameterization"]
    )

    # Verify database interactions
    assert mock_db.add.called
    assert mock_db.flush.called
    assert mock_db.commit.called


def test_parser_case_insensitive():
    """Test parser handles case variations."""
    response_lowercase = """stage 1 #problem deconstruction#:
Domain Identification: Geometry
Core Competencies: Area calculation
Baseline Difficulty: 2

stage 2 #escalation protocol#:
1. Multi-stage Transformation: Test
2. Cross-domain Integration: Test
3. Real-world Parameterization: Test

stage 3 #finally rewritten question#:
Find the area.
"""
    parsed = RephraseParser.parse(response_lowercase)
    assert parsed.identified_domain == "Geometry"
    assert len(parsed.applied_dimensions) == 3


def test_parser_extracts_chinese_competencies():
    """Test parser handles Chinese text in competencies."""
    response_chinese = """Stage 1 #Problem Deconstruction#:
Domain Identification: Algebra
Core Competencies: 線性方程, 變數隔離, 基本運算
Baseline Difficulty: 1

Stage 2 #Escalation Protocol#:
1. Multi-stage Transformation: 轉換
2. Cross-domain Integration: 整合
3. Real-world Parameterization: 參數化

Stage 3 #Finally Rewritten question#:
求解 x 的值？
"""
    parsed = RephraseParser.parse(response_chinese)
    assert len(parsed.core_competencies) == 3
    assert "線性方程" in parsed.core_competencies
