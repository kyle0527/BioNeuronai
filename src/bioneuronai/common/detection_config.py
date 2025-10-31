"""Configuration stubs for detection modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class BaseDetectionConfig:
    """Common configuration values shared by detection modules."""

    timeout: float = 15.0
    max_retries: int = 2
    user_agents: Sequence[str] = field(
        default_factory=lambda: [
            "Mozilla/5.0 (compatible; BioNeuronAI/0.2; +https://github.com/kyle0527/BioNeuronai)",
        ]
    )


@dataclass
class AuthConfig(BaseDetectionConfig):
    """Authentication module tuning values."""

    weak_passwords: Sequence[str] = field(
        default_factory=lambda: [
            "admin", "password", "123456", "welcome", "letmein",
        ]
    )
    max_login_attempts: int = 20


@dataclass
class SQLiConfig(BaseDetectionConfig):
    """SQL injection module tuning values."""

    payload_limit: int = 50
    boolean_delay: float = 0.5


@dataclass
class IDORConfig(BaseDetectionConfig):
    """IDOR detection module tuning values."""

    id_range: int = 5
    privileged_paths: Sequence[str] = field(
        default_factory=lambda: [
            "/admin", "/dashboard", "/manage",
        ]
    )


__all__ = [
    "AuthConfig",
    "BaseDetectionConfig",
    "IDORConfig",
    "SQLiConfig",
]
