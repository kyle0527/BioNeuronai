"""Stub manager used by production detection engines during documentation builds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class UnifiedSmartDetectionManager:
    """Collects detection insights in an in-memory structure."""

    events: List[Dict[str, Any]] = field(default_factory=list)

    def record_event(self, event: Dict[str, Any]) -> None:
        """Record a detection event."""

        self.events.append(event)

    def summarize(self) -> Dict[str, Any]:
        """Return a lightweight summary of recorded events."""

        return {
            "total_events": len(self.events),
            "last_event": self.events[-1] if self.events else None,
        }
