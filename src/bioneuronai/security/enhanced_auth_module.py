"""Authentication hardening module backed by the shared security base."""

from __future__ import annotations

from typing import Iterable

import base64
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
from .config import AuthConfig

logger = get_logger(__name__)


class WeakCredentialEngine(DetectionEngineProtocol):
    """Detect common weak credentials against a login form."""

    def __init__(self, config: AuthConfig) -> None:
        self.config = config

    def get_engine_name(self) -> str:  # pragma: no cover - trivial
        return "Weak Credential Detection Engine"

    async def detect(self, task, client, smart_manager) -> list:
        if not task.metadata:
            return []

        username_field = task.metadata.get("username_field", "username")
        password_field = task.metadata.get("password_field", "password")
        base_payload = dict(task.metadata.get("base_payload", {}))

        for username, password in self._credential_pool():
            payload = base_payload | {username_field: username, password_field: password}
            response = await client.post(
                str(task.target.url),
                data=payload,
                timeout=self.config.http.timeout,
                follow_redirects=True,
            )
            ai_score = smart_manager.score_text_delta("", response.text)
            if response.status_code == 200 and ("welcome" in response.text.lower() or response.headers.get("X-Auth") == "ok"):
                return [
                    create_finding(
                        task,
                        task.target,
                        VulnerabilityType.WEAK_AUTHENTICATION,
                        Severity.HIGH,
                        Confidence.HIGH,
                        f"{username}:{password}",
                        response.text[:200],
                        response.elapsed.total_seconds() if response.elapsed else None,
                        ai_score=ai_score,
                    )
                ]
        return []

    def _credential_pool(self) -> Iterable[tuple[str, str]]:
        return [
            ("admin", "admin"),
            ("admin", "password"),
            ("root", "toor"),
            ("user", "user"),
        ]


class MultiFactorBypassEngine(DetectionEngineProtocol):
    """Detect missing or bypassable multi-factor enforcement."""

    def __init__(self, config: AuthConfig) -> None:
        self.config = config

    def get_engine_name(self) -> str:  # pragma: no cover - trivial
        return "Multi-factor Bypass Detection Engine"

    async def detect(self, task, client, smart_manager) -> list:
        baseline = await fetch_baseline_response(client, task.target, self.config.http.timeout)
        if baseline is None:
            return []

        payload = {"mfa_code": "000000"}
        response = await client.post(
            str(task.target.url),
            data=payload,
            timeout=self.config.http.timeout,
        )
        ai_score = smart_manager.score_text_delta(baseline.text, response.text)
        if response.status_code == 200 and "mfa bypass" in response.text.lower():
            return [
                create_finding(
                    task,
                    task.target,
                    VulnerabilityType.MULTI_FACTOR_BYPASS,
                    Severity.MEDIUM,
                    Confidence.MEDIUM,
                    "mfa_code=000000",
                    response.text[:200],
                    response.elapsed.total_seconds() if response.elapsed else None,
                    ai_score=ai_score,
                )
            ]
        return []


class TokenMisconfigurationEngine(DetectionEngineProtocol):
    """Detect weakly encoded or leaked tokens."""

    def __init__(self, config: AuthConfig) -> None:
        self.config = config

    def get_engine_name(self) -> str:  # pragma: no cover - trivial
        return "Token Misconfiguration Detection Engine"

    async def detect(self, task, client, smart_manager) -> list:
        response = await client.get(
            str(task.target.url),
            timeout=self.config.http.timeout,
        )
        token = response.headers.get("X-Debug-Token")
        if not token:
            return []

        try:
            decoded = base64.b64decode(token).decode()
        except Exception:
            return []

        ai_score = smart_manager.score_text_delta("", decoded)
        if "admin" in decoded.lower():
            return [
                create_finding(
                    task,
                    task.target,
                    VulnerabilityType.TOKEN_MISCONFIGURATION,
                    Severity.MEDIUM,
                    Confidence.MEDIUM,
                    token,
                    decoded[:200],
                    response.elapsed.total_seconds() if response.elapsed else None,
                    ai_score=ai_score,
                )
            ]
        return []


class EnhancedAuthModule(BaseSecurityModule):
    """Authentication detection module composed of multiple engines."""

    def __init__(self, config: AuthConfig | None = None) -> None:
        config = config or AuthConfig()
        detection_engines = [
            WeakCredentialEngine(config),
            MultiFactorBypassEngine(config),
            TokenMisconfigurationEngine(config),
        ]
        super().__init__(ModuleName.FUNC_AUTH, config, detection_engines)

    def get_module_name(self) -> str:  # pragma: no cover - trivial
        return "Enhanced Authentication Detection Module"

    def get_supported_vulnerability_types(self) -> list[VulnerabilityType]:  # pragma: no cover - trivial
        return [
            VulnerabilityType.WEAK_AUTHENTICATION,
            VulnerabilityType.MULTI_FACTOR_BYPASS,
            VulnerabilityType.TOKEN_MISCONFIGURATION,
        ]

    def get_topic(self) -> Topic:  # pragma: no cover - trivial
        return Topic.TASK_FUNCTION_AUTH

    def get_vulnerability_type(self) -> VulnerabilityType:  # pragma: no cover - trivial
        return VulnerabilityType.WEAK_AUTHENTICATION
