"""Lightweight stubs for security module orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Protocol


class DetectionEngineProtocol(Protocol):
    """Protocol describing detection engine hooks used by security modules."""

    def get_engine_name(self) -> str: ...

    async def detect(self, *args: Any, **kwargs: Any) -> Iterable[Any]: ...


@dataclass
class BaseFunctionModule:
    """Base orchestration class for detection engines.

    The implementation here is intentionally lightweight so that documentation
    builds can import production modules without pulling in private dependencies.
    """

    module_name: Any
    config: Any
    detection_engines: List[DetectionEngineProtocol] = field(default_factory=list)

    async def run_detection(self, *args: Any, **kwargs: Any) -> List[Any]:
        """Execute all registered engines and aggregate their findings."""

        findings: List[Any] = []
        for engine in self.detection_engines:
            detect = getattr(engine, "detect", None)
            if callable(detect):
                try:
                    engine_findings = await detect(*args, **kwargs)
                    if engine_findings:
                        findings.extend(engine_findings)
                except Exception:
                    # Production modules handle logging; the stub swallows errors.
                    continue
        return findings
