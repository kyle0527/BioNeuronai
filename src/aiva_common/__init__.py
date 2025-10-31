"""Minimal stubs for aiva_common package used in tests."""
from .enums import Confidence, ModuleName, Severity, Topic, VulnerabilityType
from .schemas import (
    FindingEvidence,
    FindingPayload,
    FindingTarget,
    FunctionTaskPayload,
    FunctionTaskTarget,
    Vulnerability,
)
from .utils import get_logger, new_id

__all__ = [
    "Confidence",
    "ModuleName",
    "Severity",
    "Topic",
    "VulnerabilityType",
    "FindingEvidence",
    "FindingPayload",
    "FindingTarget",
    "FunctionTaskPayload",
    "FunctionTaskTarget",
    "Vulnerability",
    "get_logger",
    "new_id",
]
