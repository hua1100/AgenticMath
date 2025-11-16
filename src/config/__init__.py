"""
Configuration module for AgenticMath.

Provides centralized configuration management using Pydantic Settings.
"""

from .settings import (
    Settings,
    LLMSettings,
    OCRSettings,
    FileUploadSettings,
    QualityControlSettings,
    EscalationSettings,
    DatabaseSettings,
    LoggingSettings,
    PerformanceSettings,
    APISettings,
    get_settings,
    override_settings,
)

__all__ = [
    "Settings",
    "LLMSettings",
    "OCRSettings",
    "FileUploadSettings",
    "QualityControlSettings",
    "EscalationSettings",
    "DatabaseSettings",
    "LoggingSettings",
    "PerformanceSettings",
    "APISettings",
    "get_settings",
    "override_settings",
]
