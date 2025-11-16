"""
Configuration Management System using Pydantic Settings.

Reads configuration from environment variables and .env file,
validates values, and provides defaults for all settings.
"""

import os
from typing import List, Optional
from pathlib import Path
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


class LLMSettings(BaseSettings):
    """LLM Configuration (GPT-4.1)."""

    api_key: str = Field(..., description="OpenAI API key")
    model: str = Field(default="gpt-4o", description="LLM model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=4096, ge=100, le=16000, description="Maximum tokens")
    timeout: int = Field(default=60, ge=10, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")

    model_config = ConfigDict(env_prefix="OPENAI_")

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key format."""
        if not v or v == "sk-your-api-key-here":
            raise ValueError("Valid OpenAI API key is required")
        if not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v


class OCRSettings(BaseSettings):
    """OCR Configuration (PaddleOCR)."""

    language: str = Field(default="chinese_cht", description="OCR language")
    use_gpu: bool = Field(default=False, description="Use GPU for OCR")
    use_angle_cls: bool = Field(default=True, description="Enable angle classification")
    confidence_threshold: float = Field(
        default=0.70, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
    auto_rotation: bool = Field(default=True, description="Enable auto rotation correction")
    noise_reduction: bool = Field(default=True, description="Enable noise reduction")
    contrast_enhancement: bool = Field(default=True, description="Enable contrast enhancement")
    enable_diagram_detection: bool = Field(default=True, description="Enable diagram detection")
    max_image_size_mb: int = Field(default=10, ge=1, le=50, description="Max image size in MB")
    processing_timeout: int = Field(
        default=30, ge=5, le=120, description="OCR processing timeout in seconds"
    )

    model_config = ConfigDict(env_prefix="OCR_")


class FileUploadSettings(BaseSettings):
    """File Upload Settings."""

    upload_dir: Path = Field(default=Path("./uploads"), description="Upload directory")
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="Max file size in MB")
    cleanup_after_processing: bool = Field(
        default=False, description="Cleanup files after processing"
    )
    retain_days: int = Field(default=30, ge=1, le=365, description="Days to retain files")

    model_config = ConfigDict(env_prefix="")

    @field_validator('upload_dir', mode='before')
    @classmethod
    def resolve_upload_dir(cls, v):
        """Resolve upload directory path."""
        if isinstance(v, str):
            path = Path(v)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            return path
        return v


class QualityControlSettings(BaseSettings):
    """Quality Control Settings."""

    quality_threshold: float = Field(
        default=4.5, ge=3.0, le=5.0, description="Quality score threshold"
    )
    max_revise_iterations: int = Field(
        default=5, ge=1, le=10, description="Maximum revise iterations"
    )
    enable_auto_revision: bool = Field(default=True, description="Enable auto revision")
    min_clarity_score: float = Field(
        default=4.0, ge=1.0, le=5.0, description="Minimum clarity score"
    )
    min_math_validity_score: float = Field(
        default=4.5, ge=1.0, le=5.0, description="Minimum math validity score"
    )

    model_config = ConfigDict(env_prefix="")

    @field_validator('quality_threshold')
    @classmethod
    def validate_threshold(cls, v):
        """Ensure threshold is within valid range."""
        if not (3.0 <= v <= 5.0):
            raise ValueError("quality_threshold must be between 3.0 and 5.0")
        return v


class EscalationSettings(BaseSettings):
    """Escalation Dimensions Settings."""

    default_escalation_dimensions: List[str] = Field(
        default=[
            "Multi-stage Transformation",
            "Cross-domain Integration",
            "Real-world Parameterization",
        ],
        description="Default escalation dimensions",
    )
    min_escalation_dimensions: int = Field(
        default=3, ge=1, le=7, description="Minimum escalation dimensions"
    )
    max_escalation_dimensions: int = Field(
        default=5, ge=1, le=7, description="Maximum escalation dimensions"
    )

    model_config = ConfigDict(env_prefix="")

    @field_validator('default_escalation_dimensions', mode='before')
    @classmethod
    def parse_dimensions(cls, v):
        """Parse comma-separated dimensions."""
        if isinstance(v, str):
            return [dim.strip() for dim in v.split(",") if dim.strip()]
        return v


class DatabaseSettings(BaseSettings):
    """Database Configuration."""

    url: str = Field(default="sqlite:///./agenticmath.db", description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL statements")
    pool_size: int = Field(default=5, ge=1, le=50, description="Connection pool size")
    max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow connections")
    pool_timeout: int = Field(default=30, ge=5, le=120, description="Pool timeout in seconds")

    model_config = ConfigDict(env_prefix="DATABASE_")


class LoggingSettings(BaseSettings):
    """Logging Configuration."""

    level: str = Field(default="info", description="Log level")
    file: Path = Field(default=Path("logs/agenticmath.log"), description="Log file path")
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="Max log file size")
    backup_count: int = Field(default=5, ge=1, le=50, description="Number of backup files")
    enable_agent_logging: bool = Field(default=True, description="Enable agent logging")
    enable_llm_logging: bool = Field(default=True, description="Enable LLM logging")

    model_config = ConfigDict(env_prefix="LOG_")

    @field_validator('level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        v_lower = v.lower()
        if v_lower not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_lower

    @field_validator('file', mode='before')
    @classmethod
    def resolve_log_file(cls, v):
        """Resolve log file path."""
        if isinstance(v, str):
            path = Path(v)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            # Create parent directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        return v


class PerformanceSettings(BaseSettings):
    """Performance Configuration."""

    enable_caching: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=3600, ge=60, le=86400, description="Cache TTL in seconds")
    enable_parallel_processing: bool = Field(
        default=True, description="Enable parallel processing"
    )
    max_concurrent_tasks: int = Field(
        default=5, ge=1, le=20, description="Maximum concurrent tasks"
    )

    model_config = ConfigDict(env_prefix="")


class APISettings(BaseSettings):
    """API Server Configuration (Optional)."""

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, ge=1000, le=65535, description="API port")
    workers: int = Field(default=4, ge=1, le=32, description="Number of workers")
    reload: bool = Field(default=False, description="Enable auto-reload")

    model_config = ConfigDict(env_prefix="API_")


class Settings(BaseSettings):
    """Main Settings - Aggregates all configuration sections."""

    # Global settings
    environment: str = Field(default="development", description="Environment (dev/prod)")
    debug: bool = Field(default=False, description="Debug mode")

    # Sub-settings
    llm: LLMSettings
    ocr: OCRSettings
    file_upload: FileUploadSettings
    quality_control: QualityControlSettings
    escalation: EscalationSettings
    database: DatabaseSettings
    logging: LoggingSettings
    performance: PerformanceSettings
    api: APISettings

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = ["development", "production", "testing"]
        if v.lower() not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v.lower()

    def __init__(self, **kwargs):
        """Initialize settings with nested models."""
        # Load from environment and .env file
        super().__init__(**kwargs)

    @classmethod
    def load_from_env(cls, env_file: Optional[str] = None) -> "Settings":
        """
        Load settings from environment variables and .env file.

        Args:
            env_file: Optional path to .env file (default: .env in project root)

        Returns:
            Settings instance
        """
        if env_file:
            env_path = Path(env_file)
        else:
            env_path = PROJECT_ROOT / ".env"

        # Create sub-settings first
        llm = LLMSettings(_env_file=env_path if env_path.exists() else None)
        ocr = OCRSettings(_env_file=env_path if env_path.exists() else None)
        file_upload = FileUploadSettings(_env_file=env_path if env_path.exists() else None)
        quality_control = QualityControlSettings(_env_file=env_path if env_path.exists() else None)
        escalation = EscalationSettings(_env_file=env_path if env_path.exists() else None)
        database = DatabaseSettings(_env_file=env_path if env_path.exists() else None)
        logging = LoggingSettings(_env_file=env_path if env_path.exists() else None)
        performance = PerformanceSettings(_env_file=env_path if env_path.exists() else None)
        api = APISettings(_env_file=env_path if env_path.exists() else None)

        # Load global settings
        environment = os.getenv("ENVIRONMENT", "development")
        debug = os.getenv("DEBUG", "false").lower() == "true"

        return cls(
            environment=environment,
            debug=debug,
            llm=llm,
            ocr=ocr,
            file_upload=file_upload,
            quality_control=quality_control,
            escalation=escalation,
            database=database,
            logging=logging,
            performance=performance,
            api=api,
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(reload: bool = False) -> Settings:
    """
    Get global settings instance (singleton pattern).

    Args:
        reload: Force reload settings from environment

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None or reload:
        _settings = Settings.load_from_env()
    return _settings


def override_settings(**kwargs) -> Settings:
    """
    Override specific settings at runtime.

    Args:
        **kwargs: Settings to override (e.g., quality_threshold=4.0)

    Returns:
        Updated settings instance

    Example:
        >>> settings = override_settings(quality_threshold=4.0)
        >>> settings.quality_control.quality_threshold
        4.0
    """
    global _settings
    settings = get_settings()

    # Update nested settings
    for key, value in kwargs.items():
        # Handle nested settings (e.g., "llm.temperature")
        if "." in key:
            section, attr = key.split(".", 1)
            if hasattr(settings, section):
                section_obj = getattr(settings, section)
                if hasattr(section_obj, attr):
                    setattr(section_obj, attr, value)
        # Handle top-level settings
        elif hasattr(settings, key):
            setattr(settings, key, value)

    return settings
