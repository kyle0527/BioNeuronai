"""Placeholder smart detection manager used in tests."""
from __future__ import annotations


class UnifiedSmartDetectionManager:
    """No-op implementation for tests."""

    async def record_event(self, *args, **kwargs) -> None:  # pragma: no cover
        return None
