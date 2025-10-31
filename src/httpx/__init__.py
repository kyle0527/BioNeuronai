from __future__ import annotations

import asyncio
import urllib.parse
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


class HTTPError(Exception):
    """Base HTTP error used by the simplified httpx stub."""


class Timeout:
    """Placeholder timeout configuration."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout


@dataclass
class _Elapsed:
    seconds: float

    def total_seconds(self) -> float:
        return self.seconds


class Response:
    """Minimal HTTP response representation."""

    def __init__(self, status_code: int = 200, text: str = "", headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.elapsed = _Elapsed(0.001)


class URL:
    """Utility class used by the mock transport to inspect requests."""

    def __init__(self, raw: str) -> None:
        self._raw = raw
        self._parsed = urllib.parse.urlparse(raw)

    def __str__(self) -> str:
        return self._raw

    @property
    def params(self) -> dict[str, str]:
        return dict(urllib.parse.parse_qsl(self._parsed.query))

    @property
    def query(self) -> str:
        return self._parsed.query


class Request:
    """Request object passed to MockTransport handlers."""

    def __init__(self, method: str, url: str, headers: dict[str, str], content: bytes) -> None:
        self.method = method.upper()
        self.url = URL(url)
        self.headers = headers
        self.content = content


Handler = Callable[[Request], Awaitable[Response] | Response]


class MockTransport:
    """Transport that routes requests to an in-memory handler."""

    def __init__(self, handler: Handler) -> None:
        self._handler = handler

    async def handle_async_request(self, request: Request) -> Response:
        result = self._handler(request)
        if asyncio.iscoroutine(result):
            result = await result
        return result


def _encode_params(params: dict[str, Any] | None) -> str:
    if not params:
        return ""
    return urllib.parse.urlencode(params, doseq=True)


class AsyncClient:
    """Very small subset of httpx.AsyncClient."""

    def __init__(
        self,
        *,
        transport: MockTransport | None = None,
        timeout: Timeout | float | None = None,
        headers: dict[str, str] | None = None,
        verify: bool | None = None,
    ) -> None:
        self._transport = transport
        self._headers = headers or {}
        self._verify = verify
        self._timeout = timeout

    async def __aenter__(self) -> "AsyncClient":  # pragma: no cover - trivial
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        await self.aclose()

    async def aclose(self) -> None:  # pragma: no cover - trivial
        return None

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | Timeout | None = None,
        follow_redirects: bool | None = None,
    ) -> Response:
        return await self._request(
            "GET",
            url,
            params=params,
            headers=headers,
        )

    async def post(
        self,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | Timeout | None = None,
        follow_redirects: bool | None = None,
    ) -> Response:
        return await self._request(
            "POST",
            url,
            data=data,
            headers=headers,
        )

    async def request(
        self,
        method: str,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | Timeout | None = None,
        follow_redirects: bool | None = None,
    ) -> Response:
        return await self._request(method, url, data=data, params=params, headers=headers)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        if self._transport is None:
            raise HTTPError("No transport configured for AsyncClient")

        query = _encode_params(params)
        final_url = url
        if query:
            separator = "&" if urllib.parse.urlparse(url).query else "?"
            final_url = f"{url}{separator}{query}"

        encoded_body = _encode_params(data).encode()
        merged_headers = self._headers | (headers or {})
        request = Request(method, final_url, merged_headers, encoded_body)
        return await self._transport.handle_async_request(request)


__all__ = [
    "AsyncClient",
    "HTTPError",
    "MockTransport",
    "Request",
    "Response",
    "Timeout",
    "URL",
]
