"""Configuration stubs for production security modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuthConfig:
    """Placeholder configuration for authentication hardening."""

    max_password_length: int = 128
    enable_token_checks: bool = True
    enforce_mfa: bool = True


@dataclass
class SQLiConfig:
    """Placeholder configuration for SQL injection detection."""

    timeout_seconds: float = 2.0
    enable_time_based: bool = True
    enable_boolean_based: bool = True


@dataclass
class IDORConfig:
    """Placeholder configuration for IDOR detection."""

    enable_horizontal_checks: bool = True
    enable_vertical_checks: bool = True
    audit_log_actions: bool = True
