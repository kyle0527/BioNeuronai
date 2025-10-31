from __future__ import annotations

import base64
import asyncio

import httpx

from bioneuronai.security import (
    FunctionTaskPayload,
    FunctionTaskTarget,
)
from bioneuronai.security.production_idor_module import ProductionIDORModule
from bioneuronai.security.production_sqli_module import ProductionSQLiModule
from bioneuronai.security.enhanced_auth_module import EnhancedAuthModule


def test_production_sqli_module_union_detection() -> None:
    async def _scenario() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if "UNION" in request.url.query:
                return httpx.Response(200, text="mysql version 8.0.1 user:root", headers={"X-Delay": "5"})
            return httpx.Response(200, text="public content")

        transport = httpx.MockTransport(handler)
        module = ProductionSQLiModule()
        task = FunctionTaskPayload(
            task_id="task",
            scan_id="scan",
            target=FunctionTaskTarget(url="https://example.com/search", method="GET", parameter="q"),
        )

        async with httpx.AsyncClient(transport=transport) as client:
            findings = await module.run(task, client)

        assert len(findings) == 1
        assert findings[0].vulnerability.name.value == "sqli"
        assert findings[0].evidence.ai_score is not None

    asyncio.run(_scenario())


def test_production_idor_module_horizontal_detection() -> None:
    async def _scenario() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            params = dict(request.url.params)
            user_id = params.get("user_id")
            if user_id == "1":
                return httpx.Response(200, text="account:user")
            if user_id == "2":
                return httpx.Response(200, text="account:admin")
            return httpx.Response(404, text="not found")

        transport = httpx.MockTransport(handler)
        module = ProductionIDORModule()
        task = FunctionTaskPayload(
            task_id="task",
            scan_id="scan",
            target=FunctionTaskTarget(url="https://example.com/account", method="GET", parameter="user_id"),
            metadata={"base_params": {"user_id": "1"}},
        )

        async with httpx.AsyncClient(transport=transport) as client:
            findings = await module.run(task, client)

        assert len(findings) == 1
        assert findings[0].vulnerability.name.value == "idor"
        assert "admin" in findings[0].evidence.response

    asyncio.run(_scenario())


def test_enhanced_auth_module_weak_credentials_detection() -> None:
    async def _scenario() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST":
                data = dict(x.split("=") for x in request.content.decode().split("&")) if request.content else {}
                if data.get("username") == "admin" and data.get("password") == "admin":
                    return httpx.Response(200, text="Welcome admin", headers={"X-Auth": "ok"})
                if data.get("mfa_code") == "000000":
                    return httpx.Response(200, text="MFA bypass")
                return httpx.Response(401, text="denied")
            return httpx.Response(200, text="login page")

        transport = httpx.MockTransport(handler)
        module = EnhancedAuthModule()
        task = FunctionTaskPayload(
            task_id="task",
            scan_id="scan",
            target=FunctionTaskTarget(url="https://example.com/login", method="POST"),
            metadata={
                "username_field": "username",
                "password_field": "password",
            },
        )

        async with httpx.AsyncClient(transport=transport) as client:
            findings = await module.run(task, client)

        assert any(f.vulnerability.name.value == "weak_authentication" for f in findings)

    asyncio.run(_scenario())


def test_enhanced_auth_module_token_detection() -> None:
    async def _scenario() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                token = base64.b64encode(b"admin:debug").decode()
                return httpx.Response(200, text="token endpoint", headers={"X-Debug-Token": token})
            return httpx.Response(200, text="ok")

        transport = httpx.MockTransport(handler)
        module = EnhancedAuthModule()
        task = FunctionTaskPayload(
            task_id="task",
            scan_id="scan",
            target=FunctionTaskTarget(url="https://example.com/token", method="GET"),
            metadata={},
        )

        async with httpx.AsyncClient(transport=transport) as client:
            findings = await module.run(task, client)

        assert any(f.vulnerability.name.value == "token_misconfiguration" for f in findings)

    asyncio.run(_scenario())
