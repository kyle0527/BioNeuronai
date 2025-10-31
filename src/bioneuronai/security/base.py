from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Protocol, Sequence

import httpx


class Confidence(str, Enum):
    """Confidence levels for detections."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Severity(str, Enum):
    """Severity levels for security findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VulnerabilityType(str, Enum):
    """Supported vulnerability categories."""

    SQLI = "sqli"
    IDOR = "idor"
    WEAK_AUTHENTICATION = "weak_authentication"
    MULTI_FACTOR_BYPASS = "multi_factor_bypass"
    TOKEN_MISCONFIGURATION = "token_misconfiguration"
    SESSION_PREDICTABLE = "session_predictable"


class ModuleName(str, Enum):
    """Logical names for BioNeuronAI security modules."""

    FUNC_SQLI = "func_sqli"
    FUNC_IDOR = "func_idor"
    FUNC_AUTH = "func_auth"


class Topic(str, Enum):
    """Topics used by orchestration pipelines."""

    TASK_FUNCTION_SQLI = "task_function_sqli"
    TASK_FUNCTION_IDOR = "task_function_idor"
    TASK_FUNCTION_AUTH = "task_function_auth"


@dataclass(slots=True)
class FunctionTaskTarget:
    """Represents the HTTP target that a detection engine should probe."""

    url: str
    method: str = "GET"
    parameter: str | None = None
    headers: dict[str, str] | None = None
    body: dict[str, Any] | None = None


@dataclass(slots=True)
class FunctionTaskPayload:
    """Payload delivered to a security module from the orchestration layer."""

    task_id: str
    scan_id: str
    target: FunctionTaskTarget
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class FindingTarget:
    """Target metadata returned with a finding."""

    url: str
    parameter: str | None
    method: str


@dataclass(slots=True)
class FindingEvidence:
    """Evidence associated with a finding."""

    payload: str
    response: str
    response_time_delta: float | None = None
    ai_score: float | None = None


@dataclass(slots=True)
class Vulnerability:
    """High level vulnerability description."""

    name: VulnerabilityType
    severity: Severity
    confidence: Confidence


@dataclass(slots=True)
class FindingPayload:
    """Full finding returned by a detection engine."""

    finding_id: str
    task_id: str
    scan_id: str
    status: str
    vulnerability: Vulnerability
    target: FindingTarget
    evidence: FindingEvidence


class DetectionEngineProtocol(Protocol):
    """Protocol implemented by security detection engines."""

    def get_engine_name(self) -> str:
        ...

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: "BioNeuronAIAnalyzer",
    ) -> list[FindingPayload]:
        ...


class BioNeuronAIAnalyzer:
    """Shared anomaly analysis helper for detection engines."""

    def __init__(self, anomaly_threshold: float = 0.6, novelty_threshold: float = 0.3) -> None:
        self.anomaly_threshold = anomaly_threshold
        self.novelty_threshold = novelty_threshold
        self._recent_scores: list[float] = []

    def score_text_delta(self, baseline: str | None, candidate: str) -> float:
        """Return a 0-1 score based on length deltas between texts."""

        if baseline is None:
            return 1.0
        base_len = max(len(baseline), 1)
        diff = abs(len(candidate) - len(baseline)) / base_len
        score = min(diff, 1.0)
        self._recent_scores.append(score)
        if len(self._recent_scores) > 10:
            self._recent_scores.pop(0)
        return score

    def is_anomalous(self, baseline: str | None, candidate: str) -> bool:
        return self.score_text_delta(baseline, candidate) >= self.anomaly_threshold

    def novelty_score(self) -> float:
        if len(self._recent_scores) < 2:
            return 0.0
        return abs(self._recent_scores[-1] - self._recent_scores[-2])

    def is_novel(self) -> bool:
        return self.novelty_score() >= self.novelty_threshold


def get_logger(name: str) -> logging.Logger:
    """Return a module level logger configured for BioNeuronAI."""

    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)


def new_id(prefix: str) -> str:
    """Generate a deterministic looking identifier."""

    return f"{prefix}_{uuid.uuid4().hex}"


@dataclass(slots=True)
class HTTPSettings:
    """Reusable HTTP configuration."""

    timeout: float = 15.0
    verify_ssl: bool = True
    headers: dict[str, str] | None = None

    def as_kwargs(self) -> dict[str, Any]:
        return {
            "timeout": httpx.Timeout(self.timeout),
            "verify": self.verify_ssl,
            "headers": self.headers,
        }


@dataclass(slots=True)
class SecurityModuleConfig:
    """Base configuration shared by every security module."""

    http: HTTPSettings = field(default_factory=HTTPSettings)
    anomaly_threshold: float = 0.6
    novelty_threshold: float = 0.3

    def create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**self.http.as_kwargs())


async def fetch_baseline_response(
    client: httpx.AsyncClient,
    target: FunctionTaskTarget,
    timeout: float,
) -> httpx.Response | None:
    """Fetch a baseline response for a target using its configured method."""

    try:
        if target.method.upper() == "GET":
            return await client.get(str(target.url), timeout=timeout)
        if target.method.upper() == "POST":
            return await client.post(str(target.url), data=target.body, timeout=timeout)
        return await client.request(
            target.method.upper(),
            str(target.url),
            data=target.body,
            timeout=timeout,
        )
    except httpx.HTTPError:
        return None


def create_finding(
    task: FunctionTaskPayload,
    target: FunctionTaskTarget,
    vulnerability_type: VulnerabilityType,
    severity: Severity,
    confidence: Confidence,
    evidence_payload: str,
    response_snippet: str,
    response_time_delta: float | None,
    ai_score: float | None = None,
) -> FindingPayload:
    """Convenience helper to build a finding payload."""

    evidence = FindingEvidence(
        payload=evidence_payload,
        response=response_snippet,
        response_time_delta=response_time_delta,
        ai_score=ai_score,
    )

    finding = FindingPayload(
        finding_id=new_id("finding"),
        task_id=task.task_id,
        scan_id=task.scan_id,
        status="detected",
        vulnerability=Vulnerability(
            name=vulnerability_type,
            severity=severity,
            confidence=confidence,
        ),
        target=FindingTarget(
            url=str(target.url),
            parameter=target.parameter,
            method=target.method,
        ),
        evidence=evidence,
    )
    return finding


class BaseSecurityModule:
    """Shared orchestration logic for BioNeuronAI security modules."""

    def __init__(
        self,
        module_name: ModuleName,
        config: SecurityModuleConfig,
        detection_engines: Sequence[DetectionEngineProtocol],
    ) -> None:
        self.module_name = module_name
        self.config = config
        self.detection_engines = list(detection_engines)
        self.logger = get_logger(f"bioneuronai.security.{self.module_name.value}")
        self.smart_manager = BioNeuronAIAnalyzer(
            anomaly_threshold=config.anomaly_threshold,
            novelty_threshold=config.novelty_threshold,
        )

    async def run(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient | None = None,
    ) -> list[FindingPayload]:
        """Execute all detection engines and return aggregated findings."""

        should_close = False
        if client is None:
            client = self.config.create_client()
            should_close = True

        findings: list[FindingPayload] = []
        try:
            for engine in self.detection_engines:
                self.logger.debug("Running detection engine %s", engine.get_engine_name())
                engine_findings = await engine.detect(task, client, self.smart_manager)
                findings.extend(engine_findings)
        finally:
            if should_close:
                await client.aclose()

        return findings

    async def gather_findings(
        self,
        tasks: Iterable[FunctionTaskPayload],
    ) -> list[FindingPayload]:
        """Execute multiple tasks sequentially using a shared client."""

        async with self.config.create_client() as client:
            results: list[FindingPayload] = []
            for task in tasks:
                results.extend(await self.run(task, client=client))
            return results


__all__ = [
    "BaseSecurityModule",
    "BioNeuronAIAnalyzer",
    "Confidence",
    "DetectionEngineProtocol",
    "FindingEvidence",
    "FindingPayload",
    "FindingTarget",
    "FunctionTaskPayload",
    "FunctionTaskTarget",
    "HTTPSettings",
    "ModuleName",
    "SecurityModuleConfig",
    "Severity",
    "Topic",
    "Vulnerability",
    "VulnerabilityType",
    "create_finding",
    "fetch_baseline_response",
    "get_logger",
    "new_id",
]
