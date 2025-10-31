import asyncio
import logging

import httpx
from bioneuronai.security.base import (
    fetch_baseline_response,
    send_parameter_payload_request,
    send_target_request,
)


class DummyTarget:
    def __init__(self, url: str, method: str = "GET", parameter: str | None = None) -> None:
        self.url = url
        self.method = method
        self.parameter = parameter


def test_send_target_request_get_includes_params() -> None:
    captured: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["query"] = request.url.query.decode()
        return httpx.Response(200, text="ok")

    async def runner() -> httpx.Response:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            target = DummyTarget("https://example.com/search", method="GET")
            return await send_target_request(
                client,
                target,
                params={"q": "test"},
                follow_redirects=True,
            )

    response = asyncio.run(runner())

    assert response.status_code == 200
    assert captured["method"] == "GET"
    assert captured["query"] == "q=test"


def test_send_parameter_payload_request_post_injects_body() -> None:
    captured: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["content"] = request.content.decode()
        return httpx.Response(201, text="created")

    async def runner() -> httpx.Response:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            target = DummyTarget(
                "https://example.com/login", method="POST", parameter="username"
            )
            return await send_parameter_payload_request(
                client,
                target,
                "admin",
                timeout=5.0,
            )

    response = asyncio.run(runner())

    assert response.status_code == 201
    assert captured["method"] == "POST"
    assert "username=admin" in captured["content"]


def test_fetch_baseline_response_handles_errors(caplog) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("boom")

    async def runner() -> httpx.Response | None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            target = DummyTarget("https://example.com/profile", method="GET")
            caplog.set_level(logging.ERROR)
            return await fetch_baseline_response(
                client, target, logger=logging.getLogger("test")
            )

    response = asyncio.run(runner())

    assert response is None
    assert any("無法獲取基準響應" in message for message in caplog.messages)
