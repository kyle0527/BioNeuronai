"""Minimal httpx stubs for unit testing without external dependency."""
from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, Optional


class Request:
    def __init__(self, method: str, url: str) -> None:
        self.method = method
        self.url = url


class Response:
    def __init__(
        self,
        status_code: int,
        *,
        text: str = "",
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        elapsed: float = 0.0,
        request: Request | None = None,
    ) -> None:
        self.status_code = status_code
        self._text = text
        self.headers = headers or {}
        self.cookies = cookies or {}
        self._elapsed = _dt.timedelta(seconds=elapsed)
        self.request = request or Request("GET", "http://localhost")

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    @property
    def elapsed(self) -> _dt.timedelta:
        return self._elapsed

    @elapsed.setter
    def elapsed(self, value: _dt.timedelta) -> None:
        self._elapsed = value

    def json(self) -> Any:
        raise NotImplementedError("JSON parsing not implemented in stub")


class AsyncClient:
    async def get(self, *args: Any, **kwargs: Any) -> Response:
        raise NotImplementedError("HTTP requests are not supported in the stub")

    async def post(self, *args: Any, **kwargs: Any) -> Response:
        raise NotImplementedError("HTTP requests are not supported in the stub")

    async def request(self, *args: Any, **kwargs: Any) -> Response:
        raise NotImplementedError("HTTP requests are not supported in the stub")

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None
