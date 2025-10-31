"""Simplified base module definitions for testing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


default_id = "task"


class DetectionEngineProtocol(Protocol):
    def get_engine_name(self) -> str:  # pragma: no cover - interface stub
        ...


@dataclass
class BaseFunctionModule:
    name: str = "base"
