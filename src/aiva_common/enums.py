
"""Minimal enum definitions for unit tests."""
from __future__ import annotations

from enum import Enum, IntEnum


class Confidence(IntEnum):
    """Confidence levels for findings."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Severity(IntEnum):
    """Severity levels for findings."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ModuleName(str, Enum):
    SQLI = "SQLI"
    IDOR = "IDOR"
    AUTH = "AUTH"


class Topic(str, Enum):
    APPLICATION = "application"
    DATABASE = "database"
    AUTHENTICATION = "authentication"


class VulnerabilityType(str, Enum):
    SQLI = "SQLI"
    IDOR = "IDOR"
    WEAK_AUTHENTICATION = "WEAK_AUTHENTICATION"

"""Enum stubs mirroring the public names used by security modules."""

from __future__ import annotations

from enum import Enum


class Confidence(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModuleName(str, Enum):
    AUTH = "auth"
    SQLI = "sqli"
    IDOR = "idor"
    CORE = "core"
    FUNC_AUTH = "function_auth"
    FUNC_SQLI = "function_sqli"
    FUNC_IDOR = "function_idor"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Topic(str, Enum):
    SECURITY = "security"
    OBSERVABILITY = "observability"
    NOVELTY = "novelty"
    TASK_FUNCTION_AUTH = "task_function_auth"
    TASK_FUNCTION_SQLI = "task_function_sqli"
    TASK_FUNCTION_IDOR = "task_function_idor"


class VulnerabilityType(str, Enum):
    WEAK_AUTHENTICATION = "weak_authentication"
    SQL_INJECTION = "sql_injection"
    INSECURE_DIRECT_OBJECT_REFERENCE = "insecure_direct_object_reference"
    ACCESS_CONTROL = "access_control"
    IDOR = "idor"


__all__ = [
    "Confidence",
    "ModuleName",
    "Severity",
    "Topic",
    "VulnerabilityType",
]

