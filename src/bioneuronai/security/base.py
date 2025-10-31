"""Base detection module shared by production security modules."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Protocol, Sequence

import httpx

from aiva_common.enums import ModuleName
from aiva_common.schemas import (
    FindingEvidence,
    FindingPayload,
    FindingTarget,
    FunctionTaskPayload,
    FunctionTaskTarget,
    Vulnerability,
)
from aiva_common.utils import get_logger, new_id

from .config import BaseDetectionConfig
from .manager import UnifiedSmartDetectionManager


class DetectionEngineProtocol(Protocol):
    """Protocol that all detection engines must follow."""

    def get_engine_name(self) -> str:
        ...

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: "UnifiedSmartDetectionManager",
    ) -> list[FindingPayload]:
        ...


class BaseDetectionModule:
    """Provides HTTP helpers, baseline fetching and result serialization."""

    def __init__(
        self,
        module_name: ModuleName,
        config: BaseDetectionConfig,
        detection_engines: Sequence[DetectionEngineProtocol],
    ) -> None:
        self.module_name = module_name
        self.config = config
        self.detection_engines: tuple[DetectionEngineProtocol, ...] = tuple(detection_engines)
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.smart_manager = UnifiedSmartDetectionManager(self)

        for engine in self.detection_engines:
            self.smart_manager.register_engine(engine)

    async def execute_detection(
        self, task: FunctionTaskPayload, client: httpx.AsyncClient | None = None
    ) -> list[FindingPayload]:
        """Execute all engines against the provided task."""

        async with self._client_context(client) as http_client:
            return await self.smart_manager.run_all(task, http_client)

    # HTTP helpers -----------------------------------------------------
    @asynccontextmanager
    async def _client_context(
        self, client: httpx.AsyncClient | None
    ) -> AsyncIterator[httpx.AsyncClient]:
        if client is not None:
            yield client
        else:  # pragma: no cover - simple wrapper
            async with httpx.AsyncClient(timeout=self.config.request_timeout) as new_client:
                yield new_client

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
        follow_redirects: bool | None = None,
    ) -> httpx.Response:
        """Send an HTTP request using shared defaults."""

        request_method = (method or target.method or "GET").upper()
        url = str(target.url)
        request_timeout = timeout or self.config.request_timeout

        request_params = dict(params or {})
        request_data = dict(data or {})
        if payload is not None and target.parameter:
            if request_method == "GET":
                request_params.setdefault(target.parameter, payload)
            else:
                request_data.setdefault(target.parameter, payload)

        if not request_data and target.body and request_method != "GET":
            request_data = dict(target.body)

        combined_headers = {}
        if target.headers:
            combined_headers.update(target.headers)
        if headers:
            combined_headers.update(headers)

        if request_method == "GET":
            return await client.get(
                url,
                params=request_params or None,
                headers=combined_headers or None,
                timeout=request_timeout,
                cookies=cookies,
                follow_redirects=follow_redirects,
            )
        elif request_method == "POST":
            return await client.post(
                url,
                data=request_data or None,
                headers=combined_headers or None,
                timeout=request_timeout,
                cookies=cookies,
                follow_redirects=follow_redirects,
            )
        else:
            return await client.request(
                request_method,
                url,
                params=request_params or None,
                data=request_data or None,
                headers=combined_headers or None,
                timeout=request_timeout,
                cookies=cookies,
                follow_redirects=follow_redirects,
            )

    async def get_baseline_response(
        self, client: httpx.AsyncClient, target: FunctionTaskTarget
    ) -> httpx.Response | None:
        """Fetch a baseline response for comparison purposes."""

        try:
            return await self.send_request(
                client,
                target,
                timeout=self.config.baseline_timeout,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("無法獲取基準響應: %s", exc)
            return None

    # Serialization ----------------------------------------------------
    def serialize_finding(
        self,
        task: FunctionTaskPayload,
        *,
        vulnerability: Vulnerability,
        evidence: FindingEvidence,
        target: FindingTarget,
        status: str = "detected",
    ) -> FindingPayload:
        """Serialize a finding with consistent structure."""

        return FindingPayload(
            finding_id=new_id("finding"),
            task_id=task.task_id,
            scan_id=task.scan_id,
            status=status,
            vulnerability=vulnerability,
            target=target,
            evidence=evidence,
        )


__all__ = ["BaseDetectionModule", "DetectionEngineProtocol"]
