"""Production IDOR detection module using the shared security base."""

from __future__ import annotations

from typing import Iterable

import httpx

from .base import (
    BaseSecurityModule,
    Confidence,
    DetectionEngineProtocol,
    FunctionTaskPayload,
    ModuleName,
    Severity,
    Topic,
    VulnerabilityType,
    create_finding,
    fetch_baseline_response,
    get_logger,
)
from .config import IDORConfig

logger = get_logger(__name__)


def _build_params(task: FunctionTaskPayload, candidate: str) -> dict[str, str]:
    parameter = task.target.parameter or "id"
    base_params = dict(task.metadata.get("base_params", {})) if task.metadata else {}
    base_params[parameter] = candidate
    return base_params


class ProductionHorizontalIDOREngine(DetectionEngineProtocol):
    """Detect horizontal IDOR by mutating identifiers."""

    def __init__(self, config: IDORConfig) -> None:
        self.config = config

    def get_engine_name(self) -> str:  # pragma: no cover - trivial
        return "Production Horizontal IDOR Detection Engine"

    async def detect(self, task, client, smart_manager) -> list:
        if not task.metadata or "base_params" not in task.metadata:
            return []

        base_id = task.metadata["base_params"].get(task.target.parameter or "id")
        baseline = await client.get(
            str(task.target.url),
            params=task.metadata["base_params"],
            timeout=self.config.http.timeout,
        )
        findings: list = []
        for candidate in self._candidate_ids(base_id):
            response = await client.get(
                str(task.target.url),
                params=_build_params(task, candidate),
                timeout=self.config.http.timeout,
            )
            ai_score = smart_manager.score_text_delta(baseline.text, response.text)
            content_changed = response.text != baseline.text
            if response.status_code == 200 and (smart_manager.is_anomalous(baseline.text, response.text) or content_changed):
                findings.append(
                    create_finding(
                        task,
                        task.target,
                        VulnerabilityType.IDOR,
                        Severity.MEDIUM,
                        Confidence.MEDIUM,
                        f"parameter={candidate}",
                        response.text[:200],
                        response.elapsed.total_seconds() if response.elapsed else None,
                        ai_score=ai_score,
                    )
                )
                break
        return findings

    def _candidate_ids(self, base_id: str | None) -> Iterable[str]:
        if base_id and base_id.isdigit():
            start = int(base_id)
            for offset in range(1, self.config.horizontal_id_variations + 1):
                yield str(start + offset)
        else:
            yield from ("admin", "test", "guest")


class ProductionVerticalIDOREngine(DetectionEngineProtocol):
    """Detect vertical IDOR by requesting elevated roles."""

    def __init__(self, config: IDORConfig) -> None:
        self.config = config

    def get_engine_name(self) -> str:  # pragma: no cover - trivial
        return "Production Vertical IDOR Detection Engine"

    async def detect(self, task, client, smart_manager) -> list:
        baseline = await fetch_baseline_response(client, task.target, self.config.http.timeout)
        if baseline is None:
            return []

        admin_headers = {"X-Role": "admin"}
        if task.target.headers:
            admin_headers.update(task.target.headers)

        response = await client.get(
            str(task.target.url),
            params=_build_params(task, task.metadata.get("privileged_id", "1")) if task.metadata else None,
            headers=admin_headers,
            timeout=self.config.http.timeout,
        )
        ai_score = smart_manager.score_text_delta(baseline.text, response.text)
        if response.status_code == 200 and "admin" in response.text.lower():
            return [
                create_finding(
                    task,
                    task.target,
                    VulnerabilityType.IDOR,
                    Severity.HIGH,
                    Confidence.HIGH,
                    "X-Role=admin",
                    response.text[:200],
                    response.elapsed.total_seconds() if response.elapsed else None,
                    ai_score=ai_score,
                )
            ]
        return []


class ProductionIDORModule(BaseSecurityModule):
    """Production IDOR detection module built on the shared base."""

    def __init__(self, config: IDORConfig | None = None) -> None:
        config = config or IDORConfig()
        detection_engines = [
            ProductionHorizontalIDOREngine(config),
            ProductionVerticalIDOREngine(config),
        ]
        super().__init__(ModuleName.FUNC_IDOR, config, detection_engines)

    def get_module_name(self) -> str:  # pragma: no cover - trivial
        return "Production IDOR Detection Module"

    def get_supported_vulnerability_types(self) -> list[VulnerabilityType]:  # pragma: no cover - trivial
        return [VulnerabilityType.IDOR]

    def get_topic(self) -> Topic:  # pragma: no cover - trivial
        return Topic.TASK_FUNCTION_IDOR

    def get_vulnerability_type(self) -> VulnerabilityType:  # pragma: no cover - trivial
        return VulnerabilityType.IDOR
