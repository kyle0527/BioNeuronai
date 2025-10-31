"""Configuration objects for security detection modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BaseDetectionConfig:
    """Shared configuration for security modules."""

    request_timeout: float = 15.0
    baseline_timeout: float = 10.0


@dataclass(slots=True)
class SQLiConfig(BaseDetectionConfig):
    max_column_count: int = 10


@dataclass(slots=True)
class IDORConfig(BaseDetectionConfig):
    max_test_ids: int = 10


@dataclass(slots=True)
class AuthConfig(BaseDetectionConfig):
    max_credentials: int = 15


__all__ = ["BaseDetectionConfig", "SQLiConfig", "IDORConfig", "AuthConfig"]
