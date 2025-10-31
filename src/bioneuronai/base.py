"""Base classes and serialization utilities for BioNeuronAI neurons."""

from __future__ import annotations

import importlib
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Type


class BaseBioNeuron(ABC):
    """Abstract base class providing serialization helpers for neurons."""

    serialization_version: int = 1

    def __init__(self) -> None:
        self._last_statistics: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the neuron into a Python dictionary."""

        state = self._serialize_state()
        statistics = self.get_statistics()
        self._last_statistics = statistics

        return {
            "module": self.__class__.__module__,
            "class": self.__class__.__name__,
            "version": self.serialization_version,
            "state": state,
            "statistics": statistics,
        }

    @classmethod
    def from_dict(cls: Type["BaseBioNeuron"], data: Dict[str, Any]) -> "BaseBioNeuron":
        """Instantiate a neuron from serialized data."""

        module_name = data.get("module", cls.__module__)
        class_name = data.get("class", cls.__name__)

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Unable to import module '{module_name}'") from exc

        try:
            neuron_cls = getattr(module, class_name)
        except AttributeError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Module '{module_name}' has no class '{class_name}'") from exc

        if not issubclass(neuron_cls, BaseBioNeuron):
            raise TypeError(f"{neuron_cls!r} is not a BaseBioNeuron subclass")

        state = data.get("state", {})
        statistics = data.get("statistics", {})

        neuron = neuron_cls._from_serialized_state(state)
        if statistics:
            neuron.apply_statistics(statistics)
        neuron._last_statistics = statistics
        return neuron

    def save(self, path: str | Path) -> None:
        """Persist the neuron state to disk."""

        target = Path(path)
        if target.parent:
            target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict()))

    @classmethod
    def load(cls: Type["BaseBioNeuron"], path: str | Path) -> "BaseBioNeuron":
        """Load a neuron from a serialized JSON file."""

        source = Path(path)
        data = json.loads(source.read_text())
        return cls.from_dict(data)

    # ------------------------------------------------------------------
    # Hooks for subclasses
    # ------------------------------------------------------------------
    @abstractmethod
    def _serialize_state(self) -> Dict[str, Any]:
        """Return the raw state (weights, memory, configuration)."""

    @classmethod
    @abstractmethod
    def _from_serialized_state(cls: Type["BaseBioNeuron"], state: Dict[str, Any]) -> "BaseBioNeuron":
        """Restore a neuron from the serialized raw state."""

    def get_statistics(self) -> Dict[str, Any]:
        """Return runtime statistics to be stored along with the state."""

        return {}

    def apply_statistics(self, statistics: Dict[str, Any]) -> None:
        """Hook called when restoring statistics from serialization."""

        self._last_statistics = statistics

    @property
    def last_statistics(self) -> Dict[str, Any]:
        """Return the statistics captured during the last serialization."""

        return dict(self._last_statistics)

