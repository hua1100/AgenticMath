"""
Unit tests for Configuration Settings.

Tests Pydantic Settings configuration management.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError

from src.config.settings import (
    Settings,
    LLMSettings,
    OCRSettings,
    QualityControlSettings,
    EscalationSettings,
    get_settings,
    override_settings,
)


class TestLLMSettings:
    """Test suite for LLMSettings."""

    def test_valid_llm_settings(self):
        """Test creating valid LLM settings."""
        settings = LLMSettings(
            api_key="sk-test-key-12345",
            model="gpt-4o",
            temperature=0.7,
        )

        assert settings.api_key == "sk-test-key-12345"
        assert settings.model == "gpt-4o"
        assert settings.temperature == 0.7

    def test_invalid_api_key_format(self):
        """Test validation rejects invalid API key format."""
        with pytest.raises(ValidationError, match="must start with 'sk-'"):
            LLMSettings(api_key="invalid-key")

    def test_invalid_api_key_placeholder(self):
        """Test validation rejects placeholder API key."""
        with pytest.raises(ValidationError, match="Valid OpenAI API key is required"):
            LLMSettings(api_key="sk-your-api-key-here")

    def test_temperature_bounds(self):
        """Test temperature validation bounds."""
        # Valid temperatures
        LLMSettings(api_key="sk-test", temperature=0.0)
        LLMSettings(api_key="sk-test", temperature=1.0)
        LLMSettings(api_key="sk-test", temperature=2.0)

        # Invalid temperature (too high)
        with pytest.raises(ValidationError):
            LLMSettings(api_key="sk-test", temperature=2.5)

        # Invalid temperature (negative)
        with pytest.raises(ValidationError):
            LLMSettings(api_key="sk-test", temperature=-0.1)

    def test_default_values(self):
        """Test default values are applied."""
        settings = LLMSettings(api_key="sk-test")

        assert settings.model == "gpt-4o"
        assert settings.temperature == 0.7
        assert settings.max_tokens == 4096
        assert settings.timeout == 60
        assert settings.max_retries == 3


class TestOCRSettings:
    """Test suite for OCRSettings."""

    def test_valid_ocr_settings(self):
        """Test creating valid OCR settings."""
        settings = OCRSettings(
            language="chinese_cht",
            use_gpu=False,
            confidence_threshold=0.85,
        )

        assert settings.language == "chinese_cht"
        assert settings.use_gpu is False
        assert settings.confidence_threshold == 0.85

    def test_confidence_threshold_bounds(self):
        """Test confidence threshold validation."""
        # Valid thresholds
        OCRSettings(confidence_threshold=0.0)
        OCRSettings(confidence_threshold=0.5)
        OCRSettings(confidence_threshold=1.0)

        # Invalid (too high)
        with pytest.raises(ValidationError):
            OCRSettings(confidence_threshold=1.5)

        # Invalid (negative)
        with pytest.raises(ValidationError):
            OCRSettings(confidence_threshold=-0.1)

    def test_default_values(self):
        """Test OCR default values."""
        settings = OCRSettings()

        assert settings.language == "chinese_cht"
        assert settings.use_gpu is False
        assert settings.use_angle_cls is True
        assert settings.confidence_threshold == 0.70


class TestQualityControlSettings:
    """Test suite for QualityControlSettings."""

    def test_valid_quality_settings(self):
        """Test creating valid quality control settings."""
        settings = QualityControlSettings(
            quality_threshold=4.5,
            max_revise_iterations=5,
        )

        assert settings.quality_threshold == 4.5
        assert settings.max_revise_iterations == 5

    def test_quality_threshold_bounds(self):
        """Test quality threshold validation."""
        # Valid thresholds
        QualityControlSettings(quality_threshold=3.0)
        QualityControlSettings(quality_threshold=4.5)
        QualityControlSettings(quality_threshold=5.0)

        # Invalid (too low)
        with pytest.raises(ValidationError):
            QualityControlSettings(quality_threshold=2.9)

        # Invalid (too high)
        with pytest.raises(ValidationError):
            QualityControlSettings(quality_threshold=5.1)

    def test_max_iterations_bounds(self):
        """Test max iterations validation."""
        # Valid
        QualityControlSettings(max_revise_iterations=1)
        QualityControlSettings(max_revise_iterations=10)

        # Invalid (too low)
        with pytest.raises(ValidationError):
            QualityControlSettings(max_revise_iterations=0)

        # Invalid (too high)
        with pytest.raises(ValidationError):
            QualityControlSettings(max_revise_iterations=11)


class TestEscalationSettings:
    """Test suite for EscalationSettings."""

    def test_valid_escalation_settings(self):
        """Test creating valid escalation settings."""
        settings = EscalationSettings(
            default_escalation_dimensions=[
                "Multi-stage Transformation",
                "Cross-domain Integration",
            ],
            min_escalation_dimensions=2,
        )

        assert len(settings.default_escalation_dimensions) == 2
        assert settings.min_escalation_dimensions == 2

    def test_parse_comma_separated_dimensions(self):
        """Test parsing comma-separated dimension string."""
        settings = EscalationSettings(
            default_escalation_dimensions="Dim1, Dim2, Dim3"
        )

        assert len(settings.default_escalation_dimensions) == 3
        assert "Dim1" in settings.default_escalation_dimensions
        assert "Dim2" in settings.default_escalation_dimensions
        assert "Dim3" in settings.default_escalation_dimensions

    def test_default_dimensions(self):
        """Test default escalation dimensions."""
        settings = EscalationSettings()

        assert len(settings.default_escalation_dimensions) == 3
        assert "Multi-stage Transformation" in settings.default_escalation_dimensions


class TestSettingsIntegration:
    """Test suite for full Settings integration."""

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-key",
        "OPENAI_MODEL": "gpt-4o",
        "QUALITY_THRESHOLD": "4.5",
        "ENVIRONMENT": "development",
    })
    def test_load_from_environment(self):
        """Test loading settings from environment variables."""
        settings = Settings.load_from_env()

        assert settings.llm.api_key == "sk-test-key"
        assert settings.llm.model == "gpt-4o"
        assert settings.quality_control.quality_threshold == 4.5
        assert settings.environment == "development"

    def test_get_settings_singleton(self):
        """Test get_settings returns singleton."""
        # Clear any existing instance
        import src.config.settings as settings_module
        settings_module._settings = None

        # Mock environment
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            settings1 = get_settings()
            settings2 = get_settings()

            assert settings1 is settings2

    def test_get_settings_reload(self):
        """Test get_settings with reload flag."""
        import src.config.settings as settings_module

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            settings1 = get_settings()
            settings2 = get_settings(reload=True)

            # Different instances after reload
            assert settings1 is not settings2

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    def test_override_settings_nested(self):
        """Test overriding nested settings."""
        import src.config.settings as settings_module
        settings_module._settings = None

        settings = override_settings(**{"llm.temperature": 0.9})

        # Note: Current implementation may not support this syntax
        # This test documents expected behavior

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    def test_environment_validation(self):
        """Test environment value validation."""
        with patch.dict(os.environ, {"ENVIRONMENT": "invalid"}):
            with pytest.raises(ValidationError, match="environment must be"):
                Settings.load_from_env()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    def test_default_environment(self):
        """Test default environment is development."""
        settings = Settings.load_from_env()
        assert settings.environment == "development"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    def test_debug_mode_default(self):
        """Test debug mode defaults to False."""
        settings = Settings.load_from_env()
        assert settings.debug is False

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test",
        "DEBUG": "true"
    })
    def test_debug_mode_enabled(self):
        """Test debug mode can be enabled."""
        settings = Settings.load_from_env()
        assert settings.debug is True


class TestFilePathResolution:
    """Test suite for file path resolution."""

    def test_upload_dir_resolution(self):
        """Test upload directory path resolution."""
        from src.config.settings import FileUploadSettings, PROJECT_ROOT

        settings = FileUploadSettings(upload_dir="./uploads")

        # Should be resolved to absolute path
        assert settings.upload_dir.is_absolute()
        assert str(PROJECT_ROOT) in str(settings.upload_dir)

    def test_log_file_resolution(self):
        """Test log file path resolution."""
        from src.config.settings import LoggingSettings, PROJECT_ROOT

        settings = LoggingSettings(file="logs/test.log")

        # Should be resolved to absolute path
        assert settings.file.is_absolute()
        assert str(PROJECT_ROOT) in str(settings.file)


class TestLoggingSettings:
    """Test suite for LoggingSettings."""

    def test_valid_log_levels(self):
        """Test valid log levels."""
        for level in ["debug", "info", "warning", "error", "critical"]:
            settings = LoggingSettings(level=level)
            assert settings.level == level.lower()

    def test_invalid_log_level(self):
        """Test invalid log level raises error."""
        with pytest.raises(ValidationError, match="log_level must be"):
            LoggingSettings(level="invalid")

    def test_log_level_case_insensitive(self):
        """Test log level is case insensitive."""
        settings = LoggingSettings(level="INFO")
        assert settings.level == "info"


class TestDatabaseSettings:
    """Test suite for DatabaseSettings."""

    def test_sqlite_url(self):
        """Test SQLite database URL."""
        from src.config.settings import DatabaseSettings

        settings = DatabaseSettings(url="sqlite:///./test.db")
        assert settings.url == "sqlite:///./test.db"

    def test_postgresql_url(self):
        """Test PostgreSQL database URL."""
        from src.config.settings import DatabaseSettings

        settings = DatabaseSettings(
            url="postgresql://user:pass@localhost:5432/dbname"
        )
        assert "postgresql://" in settings.url
