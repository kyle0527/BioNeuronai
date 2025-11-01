from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Type

from .core import BioNeuron
from .improved_core import ImprovedBioNeuron


@dataclass(slots=True)
class NeuronConfig:
    """Configuration for an individual neuron type in a layer."""

    type: str
    count: int = 1
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError("count must be >= 1 for NeuronConfig")


@dataclass(slots=True)
class LayerConfig:
    """Collection of neuron declarations that compose a single layer."""

    neurons: List[NeuronConfig]

    @property
    def size(self) -> int:
        return sum(neuron.count for neuron in self.neurons)

    @classmethod
    def from_cli(cls, specification: str) -> "LayerConfig":
        """Parse a layer specification from the CLI.

        Syntax: "TYPE[:count][,key=value,...];TYPE[:count][,key=value,...]"
        where semicolons separate neuron groups within the layer and commas
        define parameters for each neuron group. Boolean literals true/false
        and numbers are automatically coerced.
        """

        if not specification:
            raise ValueError("Layer specification cannot be empty")

        groups = []
        for raw_group in specification.split(";"):
            group = raw_group.strip()
            if not group:
                continue
            pieces = [piece.strip() for piece in group.split(",") if piece.strip()]
            if not pieces:
                continue

            header, *param_parts = pieces
            if ":" in header:
                neuron_type, count_str = header.split(":", 1)
                count = int(count_str)
            else:
                neuron_type = header
                count = 1

            params: Dict[str, Any] = {}
            for part in param_parts:
                if "=" not in part:
                    raise ValueError(f"Invalid parameter syntax: '{part}'")
                key, value = part.split("=", 1)
                params[key.strip()] = _coerce_scalar(value.strip())

            groups.append(NeuronConfig(type=neuron_type, count=count, params=params))

        if not groups:
            raise ValueError("Layer specification must declare at least one neuron group")

        return cls(neurons=groups)


@dataclass(slots=True)
class BioNetConfig:
    """Declarative description of a BioNet architecture."""

    input_dim: int
    layers: List[LayerConfig]

    def __post_init__(self) -> None:
        if self.input_dim < 1:
            raise ValueError("input_dim must be >= 1")
        if not self.layers:
            raise ValueError("BioNetConfig requires at least one layer")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BioNetConfig":
        input_dim = int(data.get("input_dim", 0))
        raw_layers = data.get("layers")
        if not isinstance(raw_layers, Iterable):
            raise ValueError("'layers' must be an iterable")
        layers: List[LayerConfig] = []
        for layer in raw_layers:
            if isinstance(layer, Mapping):
                neurons_data = layer.get("neurons", layer.get("units"))
                if neurons_data is None:
                    raise ValueError("Layer dictionary must contain 'neurons'")
            else:
                neurons_data = layer
            neurons = _parse_neuron_sequence(neurons_data)
            layers.append(LayerConfig(neurons=neurons))
        return cls(input_dim=input_dim, layers=layers)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_dim": self.input_dim,
            "layers": [
                {
                    "neurons": [
                        {
                            "type": neuron.type,
                            "count": neuron.count,
                            "params": neuron.params,
                        }
                        for neuron in layer.neurons
                    ]
                }
                for layer in self.layers
            ],
        }


class NetworkBuilder:
    """Constructs BioNet instances from BioNetConfig objects."""

    def __init__(self, registry: Optional[Mapping[str, Type]] = None) -> None:
        base_registry: Dict[str, Type] = {
            "bioneuron": BioNeuron,
            "improvedbioneuron": ImprovedBioNeuron,
        }
        if registry:
            for key, value in registry.items():
                base_registry[key.lower()] = value
        self._registry = base_registry

    def build(self, config: BioNetConfig) -> "BioNet":
        return BioNet(config=config, builder=self)

    def build_layers(self, config: BioNetConfig) -> List[List[Any]]:
        input_dim = config.input_dim
        layers: List[List[Any]] = []
        for layer_cfg in config.layers:
            neurons: List[Any] = []
            for neuron_cfg in layer_cfg.neurons:
                neuron_cls = self._resolve(neuron_cfg.type)
                for _ in range(neuron_cfg.count):
                    params = dict(neuron_cfg.params)
                    neuron = neuron_cls(num_inputs=input_dim, **params)
                    neurons.append(neuron)
            if not neurons:
                raise ValueError("Each layer must contain at least one neuron")
            layers.append(neurons)
            input_dim = len(neurons)
        return layers

    def _resolve(self, neuron_type: str) -> Type:
        key = neuron_type.lower()
        if key not in self._registry:
            raise KeyError(f"Unknown neuron type: {neuron_type}")
        return self._registry[key]


class BioNet:
    """Dynamic bio-inspired network assembled from a configuration."""

    def __init__(self, config: BioNetConfig, builder: Optional[NetworkBuilder] = None) -> None:
        self.config = config
        self._builder = builder or NetworkBuilder()
        self.layers = self._builder.build_layers(config)

    @property
    def layer_sizes(self) -> List[int]:
        return [len(layer) for layer in self.layers]

    def forward(self, inputs: Sequence[float]) -> List[List[float]]:
        activations: List[List[float]] = []
        current: List[float] = list(inputs)
        for layer in self.layers:
            layer_outputs = [float(neuron.forward(current)) for neuron in layer]
            activations.append(layer_outputs)
            current = layer_outputs
        return activations

    def learn(
        self,
        inputs: Sequence[float],
        activations: Optional[List[List[float]]] = None,
    ) -> List[List[float]]:
        if activations is None:
            activations = self.forward(inputs)

        prev_outputs: Sequence[float] = inputs
        for layer, outputs in zip(self.layers, activations):
            if len(layer) != len(outputs):
                raise ValueError("Mismatch between neurons and outputs during learning")
            for neuron, output in zip(layer, outputs):
                if hasattr(neuron, "hebbian_learn"):
                    neuron.hebbian_learn(prev_outputs, output)
                elif hasattr(neuron, "improved_hebbian_learn"):
                    neuron.improved_hebbian_learn(prev_outputs, target=output)
                else:
                    raise AttributeError(
                        f"Neuron {neuron!r} does not implement a supported learning rule"
                    )
            prev_outputs = outputs
        return activations

    def summary(self) -> str:
        lines = [f"Input dimension: {self.config.input_dim}"]
        for idx, layer in enumerate(self.layers, start=1):
            counts: Dict[str, int] = {}
            for neuron in layer:
                counts[type(neuron).__name__] = counts.get(type(neuron).__name__, 0) + 1
            parts = [f"{name} x{count}" for name, count in sorted(counts.items())]
            lines.append(f"Layer {idx}: {', '.join(parts)}")
        return "\n".join(lines)


def load_config(path: Path) -> BioNetConfig:
    data = _load_raw_config(path)
    return BioNetConfig.from_dict(data)


def _load_raw_config(path: Path) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(text)
    if suffix == ".json":
        return json.loads(text)
    raise ValueError("Unsupported configuration format. Use JSON or YAML.")


def _parse_neuron_sequence(data: Any) -> List[NeuronConfig]:
    neurons: List[NeuronConfig] = []
    if isinstance(data, Mapping):
        raise ValueError("Neuron sequence cannot be a mapping without wrapping list")
    for entry in data:
        if isinstance(entry, Mapping):
            neuron_type = entry.get("type") or entry.get("class")
            if neuron_type is None:
                raise ValueError("Neuron mapping requires a 'type'")
            count = int(entry.get("count", 1))
            params = dict(entry.get("params", {}))
            # Inline params defined at top level take precedence
            for key, value in entry.items():
                if key not in {"type", "class", "count", "params"}:
                    params[key] = value
            neurons.append(NeuronConfig(type=neuron_type, count=count, params=params))
        elif isinstance(entry, str):
            neurons.append(NeuronConfig(type=entry))
        else:
            raise TypeError(
                "Neuron declarations must be strings or mappings with a 'type' field"
            )
    if not neurons:
        raise ValueError("Layer must declare at least one neuron")
    return neurons


def _coerce_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
