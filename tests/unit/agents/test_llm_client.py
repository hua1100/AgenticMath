"""
Unit tests for LLM Client.

Tests LLM client with mocked OpenAI API to avoid actual API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import RateLimitError, APIError

from src.agents.llm_client import LLMClient, LLMConfig


@pytest.fixture
def mock_openai_response():
    """Mock successful OpenAI API response."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message.content = "Test response"
    response.choices[0].finish_reason = "stop"
    response.model = "gpt-4o"
    response.usage = Mock()
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 20
    response.usage.total_tokens = 30
    return response


@pytest.fixture
def llm_client():
    """Create LLM client with test API key."""
    config = LLMConfig(api_key="test-api-key")
    return LLMClient(config=config)


def test_llm_config_validation():
    """Test LLM configuration validation."""
    # Valid config
    config = LLMConfig(temperature=0.7, max_tokens=100)
    assert config.temperature == 0.7
    assert config.max_tokens == 100

    # Invalid temperature
    with pytest.raises(ValueError, match="temperature must be between 0 and 2"):
        LLMConfig(temperature=-0.1)

    with pytest.raises(ValueError, match="temperature must be between 0 and 2"):
        LLMConfig(temperature=2.1)

    # Invalid max_tokens
    with pytest.raises(ValueError, match="max_tokens must be positive"):
        LLMConfig(max_tokens=0)

    # Invalid max_retries
    with pytest.raises(ValueError, match="max_retries must be non-negative"):
        LLMConfig(max_retries=-1)


def test_llm_client_initialization():
    """Test LLM client initialization."""
    # With API key in config
    config = LLMConfig(api_key="test-key")
    client = LLMClient(config=config)
    assert client.config.model == "gpt-4o"
    assert client.total_tokens_used == 0
    assert client.total_cost_usd == 0.0

    # Without API key should raise error
    with patch.dict("os.environ", {}, clear=True):
        config = LLMConfig()
        with pytest.raises(ValueError, match="OpenAI API key must be provided"):
            LLMClient(config=config)


@patch("src.agents.llm_client.OpenAI")
def test_chat_completion_success(mock_openai_class, llm_client, mock_openai_response):
    """Test successful chat completion."""
    # Mock OpenAI client
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai_class.return_value = mock_client
    llm_client.client = mock_client

    # Make request
    messages = [{"role": "user", "content": "Hello"}]
    response = llm_client.chat_completion(messages)

    # Verify response
    assert response["content"] == "Test response"
    assert response["role"] == "assistant"
    assert response["model"] == "gpt-4o"
    assert response["usage"]["total_tokens"] == 30
    assert response["finish_reason"] == "stop"

    # Verify token tracking
    assert llm_client.total_tokens_used == 30
    assert llm_client.total_cost_usd > 0

    # Verify API called with correct parameters
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=None,
    )


@patch("src.agents.llm_client.OpenAI")
@patch("time.sleep")  # Mock sleep to speed up test
def test_chat_completion_rate_limit_retry(mock_sleep, mock_openai_class, llm_client, mock_openai_response):
    """Test retry logic for rate limit errors."""
    # Mock OpenAI client
    mock_client = Mock()

    # Create proper RateLimitError with required parameters
    mock_response = Mock()
    mock_response.status_code = 429
    rate_limit_error = RateLimitError("Rate limit exceeded", response=mock_response, body=None)

    # Fail twice with rate limit, then succeed
    mock_client.chat.completions.create.side_effect = [
        rate_limit_error,
        rate_limit_error,
        mock_openai_response,
    ]
    mock_openai_class.return_value = mock_client
    llm_client.client = mock_client

    # Make request
    messages = [{"role": "user", "content": "Hello"}]
    response = llm_client.chat_completion(messages)

    # Verify eventual success
    assert response["content"] == "Test response"

    # Verify retry logic
    assert mock_client.chat.completions.create.call_count == 3
    assert mock_sleep.call_count == 2  # Slept twice before retrying


@patch("src.agents.llm_client.OpenAI")
@patch("time.sleep")
def test_chat_completion_max_retries_exceeded(mock_sleep, mock_openai_class, llm_client):
    """Test that max retries are respected."""
    # Mock OpenAI client
    mock_client = Mock()

    # Create proper RateLimitError
    mock_response = Mock()
    mock_response.status_code = 429
    rate_limit_error = RateLimitError("Rate limit exceeded", response=mock_response, body=None)

    # Always fail with rate limit
    mock_client.chat.completions.create.side_effect = rate_limit_error
    mock_openai_class.return_value = mock_client
    llm_client.client = mock_client

    # Make request - should fail after max retries
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(RateLimitError):
        llm_client.chat_completion(messages)

    # Verify retries (1 initial + 3 retries = 4 total attempts)
    assert mock_client.chat.completions.create.call_count == 4


@patch("src.agents.llm_client.OpenAI")
def test_chat_completion_non_retryable_error(mock_openai_class, llm_client):
    """Test that non-retryable errors fail immediately."""
    # Mock OpenAI client
    mock_client = Mock()

    # Fail with non-retryable error
    mock_client.chat.completions.create.side_effect = ValueError("Invalid input")
    mock_openai_class.return_value = mock_client
    llm_client.client = mock_client

    # Make request - should fail immediately without retries
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(ValueError, match="Invalid input"):
        llm_client.chat_completion(messages)

    # Verify no retries
    assert mock_client.chat.completions.create.call_count == 1


@patch("src.agents.llm_client.OpenAI")
def test_custom_temperature_and_max_tokens(mock_openai_class, llm_client, mock_openai_response):
    """Test custom temperature and max_tokens override."""
    # Mock OpenAI client
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai_class.return_value = mock_client
    llm_client.client = mock_client

    # Make request with custom parameters
    messages = [{"role": "user", "content": "Hello"}]
    llm_client.chat_completion(messages, temperature=0.9, max_tokens=200)

    # Verify custom parameters passed to API
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        messages=messages,
        temperature=0.9,
        max_tokens=200,
    )


def test_usage_stats(llm_client):
    """Test usage statistics tracking."""
    # Initial stats
    stats = llm_client.get_usage_stats()
    assert stats["total_tokens"] == 0
    assert stats["total_cost_usd"] == 0.0
    assert stats["model"] == "gpt-4o"

    # Manually update (simulating API calls)
    llm_client.total_tokens_used = 1000
    llm_client.total_cost_usd = 0.05

    stats = llm_client.get_usage_stats()
    assert stats["total_tokens"] == 1000
    assert stats["total_cost_usd"] == 0.05

    # Reset stats
    llm_client.reset_usage_stats()
    stats = llm_client.get_usage_stats()
    assert stats["total_tokens"] == 0
    assert stats["total_cost_usd"] == 0.0


@patch("src.agents.llm_client.OpenAI")
def test_cost_estimation_gpt4o(mock_openai_class, mock_openai_response):
    """Test cost estimation for gpt-4o model."""
    config = LLMConfig(model="gpt-4o", api_key="test-key")
    client = LLMClient(config=config)

    # Mock OpenAI client
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai_class.return_value = mock_client
    client.client = mock_client

    # Make request
    client.chat_completion([{"role": "user", "content": "Test"}])

    # Verify cost calculation (gpt-4o: $5/1M prompt + $15/1M completion)
    # 10 prompt tokens * $5/1M + 20 completion tokens * $15/1M
    expected_cost = (10 * 5 + 20 * 15) / 1_000_000
    assert abs(client.total_cost_usd - expected_cost) < 0.000001


@patch("src.agents.llm_client.OpenAI")
def test_cost_estimation_gpt4_turbo(mock_openai_class, mock_openai_response):
    """Test cost estimation for gpt-4-turbo model."""
    config = LLMConfig(model="gpt-4-turbo", api_key="test-key")
    client = LLMClient(config=config)

    # Mock OpenAI client
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai_class.return_value = mock_client
    client.client = mock_client

    # Make request
    client.chat_completion([{"role": "user", "content": "Test"}])

    # Verify cost calculation (gpt-4-turbo: $10/1M prompt + $30/1M completion)
    # 10 prompt tokens * $10/1M + 20 completion tokens * $30/1M
    expected_cost = (10 * 10 + 20 * 30) / 1_000_000
    assert abs(client.total_cost_usd - expected_cost) < 0.000001
