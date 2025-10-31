"""Common utilities and protocols for security detection engines."""

from __future__ import annotations

import logging
from typing import Any, Mapping, Protocol, TYPE_CHECKING, runtime_checkable

import httpx

if TYPE_CHECKING:  # pragma: no cover - typing only
    from aiva_common.schemas import (
        FindingPayload,
        FunctionTaskPayload,
        FunctionTaskTarget,
    )
    from ..common.unified_smart_detection_manager import UnifiedSmartDetectionManager
else:  # pragma: no cover - fallback when optional deps are missing
    FindingPayload = Any
    FunctionTaskPayload = Any
    FunctionTaskTarget = Any
    UnifiedSmartDetectionManager = Any


@runtime_checkable
class DetectionEngineProtocol(Protocol):
    """Protocol shared by all detection engines."""

    def get_engine_name(self) -> str:
        """Return human readable engine name."""

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """Execute detection and return findings."""


def _coerce_method(method: str | None) -> str:
    return (method or "GET").upper()


def _stringify_url(url: Any) -> str:
    if hasattr(url, "__fspath__"):
        return str(url.__fspath__())
    return str(url)


async def send_target_request(
    client: httpx.AsyncClient,
    target: FunctionTaskTarget,
    *,
    params: Mapping[str, Any] | None = None,
    data: Mapping[str, Any] | None = None,
    follow_redirects: bool = False,
    timeout: float = 15.0,
) -> httpx.Response:
    """Send an HTTP request for the provided task target."""

    method = _coerce_method(getattr(target, "method", None))
    url = _stringify_url(getattr(target, "url", ""))

    if method == "GET":
        return await client.get(
            url,
            params=dict(params or {}),
            timeout=timeout,
            follow_redirects=follow_redirects,
        )
    if method == "POST":
        return await client.post(
            url,
            params=dict(params or {}),
            data=dict(data or {}),
            timeout=timeout,
            follow_redirects=follow_redirects,
        )

    return await client.request(
        method,
        url,
        params=dict(params or {}),
        data=dict(data or {}),
        timeout=timeout,
        follow_redirects=follow_redirects,
    )


async def send_parameter_payload_request(
    client: httpx.AsyncClient,
    target: FunctionTaskTarget,
    payload: Any,
    *,
    parameter_name: str | None = None,
    follow_redirects: bool = False,
    timeout: float = 15.0,
) -> httpx.Response:
    """Send a request placing the payload in the target parameter."""

    parameter = parameter_name or getattr(target, "parameter", None)
    if not parameter:
        raise ValueError("Target does not define a parameter for payload injection.")

    method = _coerce_method(getattr(target, "method", None))
    if method == "GET":
        params: Mapping[str, Any] | None = {parameter: payload}
        data = None
    else:
        params = None
        data = {parameter: payload}

    return await send_target_request(
        client,
        target,
        params=params,
        data=data,
        follow_redirects=follow_redirects,
        timeout=timeout,
    )


async def fetch_baseline_response(
    client: httpx.AsyncClient,
    target: FunctionTaskTarget,
    *,
    timeout: float = 10.0,
    follow_redirects: bool = False,
    logger: logging.Logger | None = None,
) -> httpx.Response | None:
    """Fetch a baseline response for comparison purposes."""

    try:
        return await send_target_request(
            client,
            target,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )
    except (httpx.HTTPError, OSError) as exc:
        if logger is not None:
            logger.error("無法獲取基準響應: %s", exc)
        return None

