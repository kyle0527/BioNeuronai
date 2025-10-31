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
