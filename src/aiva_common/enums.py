"""Enum definitions mimicking the original shared security interfaces."""

from __future__ import annotations

from enum import Enum


class Confidence(str, Enum):
    """Represents the confidence level of a finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Severity(str, Enum):
    """Represents the severity level of a finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VulnerabilityType(str, Enum):
    """Supported vulnerability types for the security modules."""

    SQLI = "sqli"
    IDOR = "idor"
    WEAK_AUTHENTICATION = "weak_authentication"
    ACCESS_CONTROL = "access_control"


class ModuleName(str, Enum):
    """Identifiers for security detection modules."""

    FUNC_SQLI = "func_sqli"
    FUNC_IDOR = "func_idor"
    FUNC_AUTH = "func_auth"


class Topic(str, Enum):
    """Represents queue or message bus topics for modules."""

    TASK_FUNCTION_SQLI = "task.function.sqli"
    TASK_FUNCTION_IDOR = "task.function.idor"
    TASK_FUNCTION_AUTH = "task.function.auth"


__all__ = [
    "Confidence",
    "Severity",
    "VulnerabilityType",
    "ModuleName",
    "Topic",
]
