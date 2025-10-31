"""Production ready SQL injection detection module."""

from __future__ import annotations

import asyncio
from typing import Iterable

import httpx

from .base import (
    BaseSecurityModule,
    Confidence,
    DetectionEngineProtocol,
    FunctionTaskPayload,
    FunctionTaskTarget,
    ModuleName,
    Severity,
    Topic,
    VulnerabilityType,
    create_finding,
    fetch_baseline_response,
    get_logger,
)
from .config import SQLiConfig

logger = get_logger(__name__)


class _SQLiEngine(DetectionEngineProtocol):
    """Shared helpers for SQLi engines."""

    def __init__(self, config: SQLiConfig) -> None:
        self.config = config

    async def _send_payload(
        self,
        target: FunctionTaskTarget,
        client: httpx.AsyncClient,
        payload: str,
    ) -> httpx.Response:
        if target.method.upper() == "GET":
            params = {target.parameter or "q": payload}
            return await client.get(str(target.url), params=params, timeout=self.config.http.timeout)
        data = target.body.copy() if target.body else {}
        if target.parameter:
            data[target.parameter] = payload
        else:
            data.setdefault("payload", payload)
        return await client.post(str(target.url), data=data, timeout=self.config.http.timeout)


class ProductionUnionSQLiEngine(_SQLiEngine):
    """Union-based SQLi detection."""

    def get_engine_name(self) -> str:  # pragma: no cover - trivial
        return "Production Union-based SQLi Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager,
    ) -> list:
        baseline = await fetch_baseline_response(client, task.target, self.config.http.timeout)
        if baseline is None:
            return []

        for payload in self._union_payloads():
            response = await self._send_payload(task.target, client, payload)
            ai_score = smart_manager.score_text_delta(baseline.text, response.text)
            evidence_snippet = response.text[:200]

            if "sql" in response.text.lower() or smart_manager.is_anomalous(baseline.text, response.text):
                finding = create_finding(
                    task,
                    task.target,
                    VulnerabilityType.SQLI,
                    Severity.MEDIUM,
                    Confidence.HIGH if "version" in response.text.lower() else Confidence.MEDIUM,
                    payload,
                    f"Detected SQLi response: {evidence_snippet}",
                    response.elapsed.total_seconds() if response.elapsed else None,
                    ai_score=ai_score,
                )
                return [finding]
        return []

    def _union_payloads(self) -> Iterable[str]:
        base_payloads = [
            "' UNION SELECT 1,2,3--",
            "' UNION ALL SELECT version(),user(),database()--",
            "') UNION SELECT @@version, user(), database()--",
        ]
        if self.config.max_union_payloads <= len(base_payloads):
            return base_payloads[: self.config.max_union_payloads]
        return base_payloads


class ProductionBooleanSQLiEngine(_SQLiEngine):
    """Boolean-based SQLi detection."""

    def get_engine_name(self) -> str:  # pragma: no cover - trivial
        return "Production Boolean-based SQLi Detection Engine"

    async def detect(self, task, client, smart_manager) -> list:
        baseline = await fetch_baseline_response(client, task.target, self.config.http.timeout)
        if baseline is None:
            return []

        for true_payload, false_payload in self._boolean_pairs():
            true_response = await self._send_payload(task.target, client, true_payload)
            await asyncio.sleep(0)
            false_response = await self._send_payload(task.target, client, false_payload)

            ai_score = smart_manager.score_text_delta(false_response.text, true_response.text)
            if true_response.status_code != false_response.status_code or smart_manager.is_anomalous(false_response.text, true_response.text):
                finding = create_finding(
                    task,
                    task.target,
                    VulnerabilityType.SQLI,
                    Severity.LOW,
                    Confidence.MEDIUM,
                    f"TRUE: {true_payload} | FALSE: {false_payload}",
                    f"Boolean SQLi divergence observed (ai_score={ai_score:.2f})",
                    max(
                        true_response.elapsed.total_seconds() if true_response.elapsed else 0.0,
                        false_response.elapsed.total_seconds() if false_response.elapsed else 0.0,
                    ),
                    ai_score=ai_score,
                )
                return [finding]
        return []

    def _boolean_pairs(self) -> Iterable[tuple[str, str]]:
        return [
            ("' OR '1'='1'--", "' OR '1'='2'--"),
            ("' AND 1=1--", "' AND 1=2--"),
        ]


class ProductionTimeSQLiEngine(_SQLiEngine):
    """Time-based SQLi detection."""

    def get_engine_name(self) -> str:  # pragma: no cover - trivial
        return "Production Time-based SQLi Detection Engine"

    async def detect(self, task, client, smart_manager) -> list:
        baseline = await fetch_baseline_response(client, task.target, self.config.http.timeout)
        if baseline is None:
            return []

        for payload, expected_delay in self._payloads():
            response = await self._send_payload(task.target, client, payload)
            header_delay = float(response.headers.get("X-Delay", 0.0))
            ai_score = smart_manager.score_text_delta(baseline.text, response.text)
            if header_delay >= expected_delay or smart_manager.is_anomalous(baseline.text, response.text):
                finding = create_finding(
                    task,
                    task.target,
                    VulnerabilityType.SQLI,
                    Severity.MEDIUM,
                    Confidence.HIGH,
                    payload,
                    "Time-based anomaly detected",
                    response.elapsed.total_seconds() if response.elapsed else None,
                    ai_score=ai_score,
                )
                return [finding]
        return []

    def _payloads(self) -> Iterable[tuple[str, float]]:
        return [
            ("' OR SLEEP(5)--", 5.0),
            ("'; WAITFOR DELAY '00:00:05'--", 5.0),
        ]


class ProductionSQLiModule(BaseSecurityModule):
    """Production SQL injection detection module."""

    def __init__(self, config: SQLiConfig | None = None) -> None:
        config = config or SQLiConfig()
        detection_engines = [
            ProductionUnionSQLiEngine(config),
            ProductionBooleanSQLiEngine(config),
            ProductionTimeSQLiEngine(config),
        ]
        super().__init__(ModuleName.FUNC_SQLI, config, detection_engines)

    def get_module_name(self) -> str:  # pragma: no cover - trivial
        return "Production SQL Injection Detection Module"

    def get_supported_vulnerability_types(self) -> list[VulnerabilityType]:  # pragma: no cover - trivial
        return [VulnerabilityType.SQLI]

    def get_topic(self) -> Topic:  # pragma: no cover - trivial
        return Topic.TASK_FUNCTION_SQLI

    def get_vulnerability_type(self) -> VulnerabilityType:  # pragma: no cover - trivial
        return VulnerabilityType.SQLI
