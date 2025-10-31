"""Shared base implementations for security function modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from aiva_common.enums import ModuleName
    from aiva_common.schemas import FindingPayload, FunctionTaskPayload

    from .detection_config import BaseDetectionConfig


class DetectionEngineProtocol(Protocol):
    """Protocol representing a detection engine used by function modules."""

    def get_engine_name(self) -> str:
        """Return the human-readable engine name."""

    async def detect(
        self,
        task: "FunctionTaskPayload",
        client: Any,
        smart_manager: Any,
    ) -> List["FindingPayload"]:
        """Run the detection routine and return findings."""


@dataclass
class BaseFunctionModule:
    """Minimal base class orchestrating detection engines.

    This stub is intentionally lightweight and focuses on keeping imports cheap
    while mirroring the interfaces expected by the production modules.
    """

    module_name: "ModuleName" | str
    config: "BaseDetectionConfig"
    detection_engines: Sequence[DetectionEngineProtocol]

    def __init__(
        self,
        module_name: "ModuleName" | str,
        config: "BaseDetectionConfig",
        detection_engines: Iterable[DetectionEngineProtocol],
    ) -> None:
        self.module_name = module_name
        self.config = config
        self.detection_engines = list(detection_engines)

    async def execute(
        self,
        task: "FunctionTaskPayload",
        client: Any,
        smart_manager: Any,
    ) -> List["FindingPayload"]:
        """Sequentially execute each detection engine and collect findings."""

        findings: List["FindingPayload"] = []
        for engine in self.detection_engines:
            result = await engine.detect(task, client, smart_manager)
            findings.extend(result)
        return findings

    # Backwards compatibility alias used by some call sites.
    async def run(
        self,
        task: "FunctionTaskPayload",
        client: Any,
        smart_manager: Any,
    ) -> List["FindingPayload"]:
        """Alias for :meth:`execute` to match historic APIs."""

        return await self.execute(task, client, smart_manager)
