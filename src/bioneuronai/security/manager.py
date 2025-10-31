"""Unified manager coordinating detection engines."""

from __future__ import annotations

from collections.abc import Iterable
from typing import List

import httpx

from aiva_common.schemas import FindingPayload, FunctionTaskPayload, FunctionTaskTarget

from .utils import log_detection_error

if False:  # pragma: no cover - circular import hints
    from .base import BaseDetectionModule, DetectionEngineProtocol


class UnifiedSmartDetectionManager:
    """Runtime container for detection engines with shared helpers."""

    def __init__(self, module: "BaseDetectionModule") -> None:
        self._module = module
        self._engines: List["DetectionEngineProtocol"] = []

    @property
    def logger(self):  # pragma: no cover - trivial
        return self._module.logger

    def register_engine(self, engine: "DetectionEngineProtocol") -> None:
        """Register a new detection engine."""

        self._engines.append(engine)

    async def run_all(
        self, task: FunctionTaskPayload, client: httpx.AsyncClient
    ) -> list[FindingPayload]:
        """Execute all registered engines and merge their findings."""

        findings: list[FindingPayload] = []
        for engine in self._engines:
            try:
                engine_findings = await engine.detect(task, client, self)
            except Exception as exc:  # pragma: no cover - defensive safety
                log_detection_error(self.logger, engine.get_engine_name(), exc)
                continue
            if engine_findings:
                findings.extend(engine_findings)
        return findings

    # Shared helpers -----------------------------------------------------
    async def send_request(
        self,
        client: httpx.AsyncClient,
        target: FunctionTaskTarget,
        *,
        payload: str | None = None,
        method: str | None = None,
        data: dict | None = None,
        params: dict | None = None,
        timeout: float | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
    ) -> httpx.Response:
        return await self._module.send_request(
            client,
            target,
            payload=payload,
            method=method,
            data=data,
            params=params,
            timeout=timeout,
            headers=headers,
            cookies=cookies,
        )

    async def get_baseline_response(
        self, client: httpx.AsyncClient, target: FunctionTaskTarget
    ) -> httpx.Response | None:
        return await self._module.get_baseline_response(client, target)

    def serialize_finding(
        self,
        task: FunctionTaskPayload,
        *,
        vulnerability,
        evidence,
        target,
        status: str = "detected",
    ) -> FindingPayload:
        return self._module.serialize_finding(
            task, vulnerability=vulnerability, evidence=evidence, target=target, status=status
        )

    def engines(self) -> Iterable["DetectionEngineProtocol"]:  # pragma: no cover - helper
        return tuple(self._engines)
