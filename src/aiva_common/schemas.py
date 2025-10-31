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
