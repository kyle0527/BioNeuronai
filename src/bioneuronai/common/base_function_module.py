"""Light-weight base classes for production function modules."""

from __future__ import annotations

import asyncio
from typing import Iterable, List, Protocol

from .unified_smart_detection_manager import UnifiedSmartDetectionManager


class DetectionEngineProtocol(Protocol):
    """Simplified protocol used by production modules during testing."""

    def get_engine_name(self) -> str: ...

    async def detect(
        self,
        task,
        client,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> List:
        ...


class BaseFunctionModule:
    """Minimal orchestration harness shared by the production modules."""

    def __init__(self, module_name, config, detection_engines: Iterable[DetectionEngineProtocol]):
        self.module_name = module_name
        self.config = config
        self.detection_engines = list(detection_engines)

    async def run_detection(self, task, client, smart_manager: UnifiedSmartDetectionManager):
        findings: list = []
        for engine in self.detection_engines:
            engine_findings = await engine.detect(task, client, smart_manager)
            findings.extend(engine_findings)
        return findings

    async def execute_with_timeout(self, coro, timeout: float):
        return await asyncio.wait_for(coro, timeout=timeout)


__all__ = [
    "BaseFunctionModule",
    "DetectionEngineProtocol",
]
