"""Neuron type registry exposing high-level constructors."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .base import BaseSpikingNeuron
from .lif import LIFNeuron
from .stdp import STDPNeuron

NeuronFactory = Callable[..., BaseSpikingNeuron]


class NeuronRegistry(dict[str, NeuronFactory]):
    """Simple registry mapping names to neuron factory callables."""

    def register(self, name: str, factory: NeuronFactory) -> None:
        key = name.lower()
        if key in self:
            raise ValueError(f"Neuron type '{name}' already registered")
        self[key] = factory

    def create(self, name: str, **kwargs: Any) -> BaseSpikingNeuron:
        key = name.lower()
        if key not in self:
            raise KeyError(f"Neuron type '{name}' not found")
        return self[key](**kwargs)

    def register_from_config(self, config: Mapping[str, Any]) -> dict[str, BaseSpikingNeuron]:
        """Create neurons from a configuration mapping and register them."""

        created: dict[str, BaseSpikingNeuron] = {}
        neurons_cfg = config.get("neurons", [])
        if not isinstance(neurons_cfg, list):
            raise TypeError("config['neurons'] must be a list")
        for entry in neurons_cfg:
            if not isinstance(entry, Mapping):
                raise TypeError("Each neuron config must be a mapping")
            name = entry.get("name")
            if not name:
                raise ValueError("Neuron config requires a 'name'")
            neuron_type = entry.get("type")
            if not neuron_type:
                raise ValueError("Neuron config requires a 'type'")
            params = dict(entry.get("params", {}))
            created[name] = self.create(neuron_type, **params)
        return created


NEURON_REGISTRY = NeuronRegistry()
NEURON_REGISTRY.register("lif", lambda **kwargs: LIFNeuron(**kwargs))
NEURON_REGISTRY.register("stdp", lambda **kwargs: STDPNeuron(**kwargs))

__all__ = [
    "BaseSpikingNeuron",
    "LIFNeuron",
    "STDPNeuron",
    "NEURON_REGISTRY",
]
