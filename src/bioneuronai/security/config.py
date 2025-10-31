from __future__ import annotations

from dataclasses import dataclass

from .base import HTTPSettings, SecurityModuleConfig


@dataclass(slots=True)
class SQLiConfig(SecurityModuleConfig):
    """Configuration specific to SQL injection detection."""

    max_union_payloads: int = 20


@dataclass(slots=True)
class IDORConfig(SecurityModuleConfig):
    """Configuration specific to IDOR detection."""

    horizontal_id_variations: int = 8


@dataclass(slots=True)
class AuthConfig(SecurityModuleConfig):
    """Configuration specific to authentication hardening checks."""

    brute_force_delay: float = 0.3


__all__ = [
    "SQLiConfig",
    "IDORConfig",
    "AuthConfig",
]
