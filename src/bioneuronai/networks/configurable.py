"""Utilities for building configurable BioNeuron networks."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Callable, Dict, Iterable, List, MutableMapping, Sequence, Tuple, Type, Union

NeuronFactory = Callable[[int, Dict[str, Any]], Any]


def _qualname(obj: Any) -> str:
    return f"{obj.__module__}.{obj.__name__}"


def _load_known_neurons() -> Dict[str, Callable[[int, Dict[str, Any]], Any]]:
    mapping: Dict[str, Callable[[int, Dict[str, Any]], Any]] = {}
    try:  # pragma: no cover - optional dependency
        from ..core import BioNeuron  # type: ignore
    except Exception:  # pragma: no cover
        BioNeuron = None  # type: ignore
    else:  # pragma: no cover - executed in normal runtime
        mapping["BioNeuron"] = BioNeuron  # type: ignore[misc]
        mapping[_qualname(BioNeuron)] = BioNeuron  # type: ignore[misc]
    try:  # pragma: no cover - optional dependency
        from ..improved_core import ImprovedBioNeuron  # type: ignore
    except Exception:  # pragma: no cover
        ImprovedBioNeuron = None  # type: ignore
    else:  # pragma: no cover - executed in normal runtime
        mapping["ImprovedBioNeuron"] = ImprovedBioNeuron  # type: ignore[misc]
        mapping[_qualname(ImprovedBioNeuron)] = ImprovedBioNeuron  # type: ignore[misc]
    return mapping


KNOWN_NEURONS = _load_known_neurons()


@dataclass
class LayerConfig:
    """Configuration for a single network layer."""

    size: int
    neuron: Union[str, Type[Any], NeuronFactory]
    parameters: Dict[str, Any] = field(default_factory=dict)
    name: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        neuron_spec = self.neuron
        if callable(neuron_spec) and not isinstance(neuron_spec, type):
            raise ValueError("Cannot serialise callable neuron factories; use class or name instead.")
        if isinstance(neuron_spec, type):
            neuron_repr = _qualname(neuron_spec)
        else:
            neuron_repr = str(neuron_spec)
        return {
            "size": self.size,
            "neuron": neuron_repr,
            "parameters": dict(self.parameters),
            "name": self.name,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "LayerConfig":
        if "size" not in data or "neuron" not in data:
            raise ValueError("LayerConfig requires 'size' and 'neuron'.")
        neuron_spec: Union[str, Type[Any], NeuronFactory]
        neuron_spec = data["neuron"]
        return LayerConfig(
            size=int(data["size"]),
            neuron=neuron_spec,
            parameters=dict(data.get("parameters", {})),
            name=data.get("name"),
        )


@dataclass
class NetworkConfig:
    """Configuration for a configurable network."""

    input_dim: int
    layers: List[LayerConfig]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_dim": self.input_dim,
            "layers": [layer.to_dict() for layer in self.layers],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "NetworkConfig":
        if "input_dim" not in data or "layers" not in data:
            raise ValueError("NetworkConfig requires 'input_dim' and 'layers'.")
        layers = [LayerConfig.from_dict(layer) for layer in data["layers"]]
        return NetworkConfig(input_dim=int(data["input_dim"]), layers=layers, metadata=dict(data.get("metadata", {})))


def _resolve_neuron(
    neuron_spec: Union[str, Type[Any], NeuronFactory],
    custom_factories: MutableMapping[str, NeuronFactory] | None = None,
) -> NeuronFactory:
    if callable(neuron_spec) and not isinstance(neuron_spec, type):
        def _factory(num_inputs: int, params: Dict[str, Any]) -> Any:
            return neuron_spec(num_inputs=num_inputs, **params)  # type: ignore[misc]

        return _factory

    if isinstance(neuron_spec, type):
        def _factory(num_inputs: int, params: Dict[str, Any]) -> Any:
            return neuron_spec(num_inputs=num_inputs, **params)  # type: ignore[misc]

        return _factory

    if not isinstance(neuron_spec, str):
        raise TypeError(f"Unsupported neuron specification: {neuron_spec!r}")

    if custom_factories and neuron_spec in custom_factories:
        return custom_factories[neuron_spec]

    if neuron_spec in KNOWN_NEURONS:
        neuron_cls = KNOWN_NEURONS[neuron_spec]

        def _factory(num_inputs: int, params: Dict[str, Any]) -> Any:
            return neuron_cls(num_inputs=num_inputs, **params)

        return _factory

    if "." in neuron_spec:
        module_name, _, attr = neuron_spec.rpartition(".")
        module = import_module(module_name)
        neuron_cls = getattr(module, attr)
        if not callable(neuron_cls):
            raise TypeError(f"Resolved neuron '{neuron_spec}' is not callable.")

        def _factory(num_inputs: int, params: Dict[str, Any]) -> Any:
            return neuron_cls(num_inputs=num_inputs, **params)

        return _factory

    raise KeyError(f"Unknown neuron specification: {neuron_spec}")


class ConfigurableLayer:
    """A layer composed of configurable neurons."""

    def __init__(
        self,
        config: LayerConfig,
        input_dim: int,
        neuron_factories: MutableMapping[str, NeuronFactory] | None = None,
    ) -> None:
        self.config = config
        self.input_dim = input_dim
        self._factory = _resolve_neuron(config.neuron, neuron_factories)
        self.neurons = [self._factory(input_dim, dict(config.parameters)) for _ in range(config.size)]

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [float(neuron.forward(inputs)) for neuron in self.neurons]

    def learn(self, inputs: Sequence[float], outputs: Sequence[float], target: float | None = None) -> None:
        for neuron, output in zip(self.neurons, outputs):
            effective_target = target if target is not None else float(output)
            if hasattr(neuron, "hebbian_learn"):
                neuron.hebbian_learn(inputs, effective_target)  # type: ignore[attr-defined]
            elif hasattr(neuron, "improved_hebbian_learn"):
                neuron.improved_hebbian_learn(inputs, target=effective_target)  # type: ignore[attr-defined]
            elif hasattr(neuron, "learn"):
                neuron.learn(inputs, effective_target)  # type: ignore[attr-defined]
            else:  # pragma: no cover - safeguard
                raise AttributeError(f"Neuron {neuron!r} does not expose a supported learning method.")


class ConfigurableNetwork:
    """A sequential network composed of configurable layers."""

    def __init__(self, config: NetworkConfig, neuron_factories: MutableMapping[str, NeuronFactory] | None = None) -> None:
        self.config = config
        self.layers: List[ConfigurableLayer] = []
        input_dim = config.input_dim
        for layer_config in config.layers:
            layer = ConfigurableLayer(layer_config, input_dim, neuron_factories)
            self.layers.append(layer)
            input_dim = layer_config.size

    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[List[float]]]:
        layer_outputs: List[List[float]] = []
        current = list(inputs)
        for layer in self.layers:
            current = layer.forward(current)
            layer_outputs.append(current)
        final = layer_outputs[-1] if layer_outputs else current
        return final, layer_outputs

    def learn(self, inputs: Sequence[float]) -> Tuple[List[float], List[List[float]]]:
        final, layer_outputs = self.forward(inputs)
        previous_outputs: Sequence[float] = inputs
        if not layer_outputs:
            return final, layer_outputs
        for index, (layer, outputs) in enumerate(zip(self.layers, layer_outputs)):
            if index == len(layer_outputs) - 1:
                target_value = sum(final) / len(final) if final else 0.0
            else:
                next_outputs = layer_outputs[index + 1]
                target_value = sum(next_outputs) / len(next_outputs) if next_outputs else 0.0
            layer.learn(previous_outputs, outputs, target=target_value)
            previous_outputs = outputs
        return final, layer_outputs

    def to_config(self) -> NetworkConfig:
        return self.config


def _normalise_config(
    config: Union[NetworkConfig, Dict[str, Any]],
) -> NetworkConfig:
    if isinstance(config, NetworkConfig):
        return config
    if isinstance(config, dict):
        return NetworkConfig.from_dict(config)
    raise TypeError("Unsupported configuration type.")


def build_network(
    config: Union[NetworkConfig, Dict[str, Any]],
    neuron_factories: MutableMapping[str, NeuronFactory] | None = None,
) -> ConfigurableNetwork:
    """Build a :class:`ConfigurableNetwork` from the provided configuration."""

    normalised = _normalise_config(config)
    return ConfigurableNetwork(normalised, neuron_factories)


def config_from_layers(
    input_dim: int,
    layers: Iterable[Union[LayerConfig, Dict[str, Any]]],
) -> NetworkConfig:
    normalised_layers: List[LayerConfig] = []
    for layer in layers:
        if isinstance(layer, LayerConfig):
            normalised_layers.append(layer)
        elif isinstance(layer, dict):
            normalised_layers.append(LayerConfig.from_dict(layer))
        else:
            raise TypeError(f"Unsupported layer config: {layer!r}")
    return NetworkConfig(input_dim=input_dim, layers=normalised_layers)
