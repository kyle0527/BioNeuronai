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
    metadata: dict[str, Any] = field(default_factory=dict)
