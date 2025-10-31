"""Stub implementation of the unified smart detection manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Tuple


@dataclass
class UnifiedSmartDetectionManager:
    """Collects emitted events during security scans.

    This placeholder keeps track of emitted events for documentation and unit
    testing purposes. Real deployments should replace it with the production
    orchestration layer.
    """

    events: List[Tuple[str, Any]] = field(default_factory=list)

    async def emit(self, event_type: str, payload: Any | None = None) -> None:
        """Record an asynchronous event notification."""

        self.events.append((event_type, payload))

    def record(self, event_type: str, payload: Any | None = None) -> None:
        """Synchronous helper mirroring the async :meth:`emit` method."""

        self.events.append((event_type, payload))
