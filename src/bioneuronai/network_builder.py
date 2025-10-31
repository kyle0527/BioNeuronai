"""Utilities to construct networks from configuration dictionaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, MutableMapping, Sequence, Tuple, Type

from .core import BioNeuron
from .neurons.base import BaseBioNeuron
from .neurons.lif import LIFNeuron
from .neurons.anti_hebb import AntiHebbNeuron


@dataclass
class BuiltLayer:
    neurons: List[BaseBioNeuron]

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [neuron.forward(inputs) for neuron in self.neurons]

    def learn(
        self,
        inputs: Sequence[float],
        outputs: Sequence[float] | None = None,
    ) -> None:
        if outputs is not None and len(outputs) != len(self.neurons):
            raise ValueError("outputs length must match number of neurons")

        for idx, neuron in enumerate(self.neurons):
            target = outputs[idx] if outputs is not None else None
            neuron.learn(inputs, target)


class BuiltNetwork:
    """A simple feed-forward network assembled by :class:`NetworkBuilder`."""

    def __init__(self, layers: List[BuiltLayer]) -> None:
        self.layers = layers

    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[List[float]]]:
        activations: List[List[float]] = []
        current = list(inputs)
        for layer in self.layers:
            current = layer.forward(current)
            activations.append(current)
        final_output = activations[-1] if activations else []
        return final_output, activations

    def learn(
        self,
        inputs: Sequence[float],
        targets: Sequence[Sequence[float]] | None = None,
    ) -> None:
        current = list(inputs)
        per_layer_outputs: List[List[float]] = []
        for layer in self.layers:
            current = layer.forward(current)
            per_layer_outputs.append(current)

        prev_inputs = list(inputs)
        for idx, (layer, outputs) in enumerate(zip(self.layers, per_layer_outputs)):
            layer_targets = None
            if targets is not None:
                if idx >= len(targets):
                    raise ValueError("targets length must match number of layers")
                layer_targets = list(targets[idx])
                if len(layer_targets) != len(layer.neurons):
                    raise ValueError(
                        "targets for layer must match number of neurons in that layer"
                    )
            layer.learn(prev_inputs, layer_targets)
            prev_inputs = outputs

        if targets is not None and len(targets) != len(self.layers):
            raise ValueError("targets length must match number of layers")


class NetworkBuilder:
    """Factory class that can register neuron types and build networks."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[BaseBioNeuron]] = {}
        self.register_neuron_type("bio", BioNeuron)
        self.register_neuron_type("lif", LIFNeuron)
        self.register_neuron_type("anti_hebb", AntiHebbNeuron)

    def register_neuron_type(self, name: str, neuron_cls: Type[BaseBioNeuron]) -> None:
        if not issubclass(neuron_cls, BaseBioNeuron):
            raise TypeError("neuron_cls must subclass BaseBioNeuron")
        self._registry[name] = neuron_cls

    def get_registered_types(self) -> Dict[str, Type[BaseBioNeuron]]:
        return dict(self._registry)

    def build_layer(
        self,
        neuron_type: str,
        *,
        input_dim: int,
        count: int,
        params: MutableMapping[str, object] | None = None,
    ) -> BuiltLayer:
        if neuron_type not in self._registry:
            raise KeyError(f"Unknown neuron type: {neuron_type}")
        neuron_cls = self._registry[neuron_type]
        params = dict(params or {})
        neurons = [
            neuron_cls(num_inputs=input_dim, **params) for _ in range(count)
        ]
        return BuiltLayer(neurons)

    def build_from_config(self, config: MutableMapping[str, object]) -> BuiltNetwork:
        try:
            input_dim = int(config["input_dim"])
            layer_configs = list(config["layers"])
        except KeyError as exc:
            raise KeyError("Configuration requires 'input_dim' and 'layers'") from exc

        layers: List[BuiltLayer] = []
        current_dim = input_dim
        for layer_conf in layer_configs:
            neuron_type = layer_conf["type"]
            count = int(layer_conf["count"])
            params = layer_conf.get("params", {})
            layer = self.build_layer(
                neuron_type,
                input_dim=current_dim,
                count=count,
                params=params,
            )
            layers.append(layer)
            current_dim = count
        return BuiltNetwork(layers)


__all__ = ["NetworkBuilder", "BuiltNetwork", "BuiltLayer"]
