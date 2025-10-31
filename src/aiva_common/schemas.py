"""Lightweight schema objects for security detection modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import Confidence, Severity, VulnerabilityType


@dataclass(slots=True)
class FunctionTaskTarget:
    """Represents the HTTP target to probe."""

    url: str
    method: str = "GET"
    parameter: str | None = None
    headers: dict[str, str] | None = None
    body: dict[str, Any] | None = None


@dataclass(slots=True)
class FunctionTaskPayload:
    """Task payload passed into detection modules."""

    task_id: str
    scan_id: str
    target: FunctionTaskTarget
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FindingTarget:
    """Information about the vulnerable target."""

    url: str
    parameter: str | None
    method: str


@dataclass(slots=True)
class Vulnerability:
    """Represents the vulnerability classification of a finding."""

    name: VulnerabilityType
    severity: Severity
    confidence: Confidence


@dataclass(slots=True)
class FindingEvidence:
    """Evidence associated with a detection finding."""

    payload: str
    response: str
    response_time_delta: float | None = None


@dataclass(slots=True)
class FindingPayload:
    """Serialized result returned by detection modules."""

    finding_id: str
    task_id: str
    scan_id: str
    status: str
    vulnerability: Vulnerability
    target: FindingTarget
    evidence: FindingEvidence


__all__ = [
    "FunctionTaskTarget",
    "FunctionTaskPayload",
    "FindingTarget",
    "Vulnerability",
    "FindingEvidence",
    "FindingPayload",
]
