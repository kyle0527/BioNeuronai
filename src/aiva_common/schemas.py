
"""Lightweight dataclass implementations for findings and tasks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .enums import Confidence, Severity, VulnerabilityType


@dataclass
class FunctionTaskTarget:
    url: str
    method: str = "GET"
    parameter: Optional[str] = None


@dataclass
class FunctionTaskPayload:
    task_id: str = "task"
    scan_id: str = "scan"
    target: FunctionTaskTarget = field(default_factory=FunctionTaskTarget)

"""Dataclass stubs used by the documentation build."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .enums import ModuleName, Topic, VulnerabilityType, Severity, Confidence


@dataclass
class FindingTarget:
    url: str
    parameter: str
    method: str


@dataclass
class FindingEvidence:
    payload: str
    response: str
    response_time_delta: float


@dataclass
class Vulnerability:
    name: VulnerabilityType
    severity: Severity
    confidence: Confidence


@dataclass

class FindingTarget:
    url: str
    parameter: Optional[str] = None
    method: str = "GET"


@dataclass
class FindingEvidence:
    payload: str
    response: str
    response_time_delta: float = 0.0


@dataclass


class FindingPayload:
    finding_id: str
    task_id: str
    scan_id: str
    status: str
    vulnerability: Vulnerability
    target: FindingTarget
    evidence: FindingEvidence



@dataclass
class FunctionTaskTarget:
    url: str
    method: str = "GET"
    headers: Optional[dict[str, str]] = None
    parameter: str = "input"


@dataclass
class FunctionTaskPayload:
    task_id: str
    scan_id: str
    topic: Topic
    module: ModuleName
    target: FunctionTaskTarget


__all__ = [
    "FindingTarget",
    "FindingEvidence",
    "Vulnerability",
    "FindingPayload",
    "FunctionTaskTarget",
    "FunctionTaskPayload",
]

