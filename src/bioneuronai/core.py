from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple, Type
import json
import numpy as np


class BioNeuron:
    """Bio-inspired neuron with short-term input memory and Hebbian update.
    (Minimal refactor of your original code; adds type hints and novelty_score.)
    """

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        self.num_inputs = num_inputs
        rng = np.random.default_rng(seed)
        self.weights = rng.uniform(0.1, 0.9, num_inputs).astype(np.float32)
        self.threshold = float(threshold)
        self.learning_rate = float(learning_rate)
        self.memory_len = int(memory_len)
        self.input_memory: List[np.ndarray] = []

    def forward(self, inputs: Sequence[float]) -> float:
        assert len(inputs) == self.num_inputs
        x = np.asarray(inputs, dtype=np.float32)

        # short-term memory
        self.input_memory.append(x)
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

        potential = float(np.dot(self.weights, x))
        return min(1.0, potential) if potential >= self.threshold else 0.0

    def hebbian_learn(self, inputs: Sequence[float], output: float) -> None:
        x = np.asarray(inputs, dtype=np.float32)
        delta = self.learning_rate * x * float(output)
        self.weights = np.clip(self.weights + delta, 0.0, 1.0)

    def novelty_score(self) -> float:
        """Simple novelty proxy: mean abs diff of last two inputs (0~1 scaled)."""
        if len(self.input_memory) < 2:
            return 0.0
        a, b = self.input_memory[-1], self.input_memory[-2]
        denom = np.maximum(1e-6, np.mean(np.abs(b)))
        score = float(np.clip(np.mean(np.abs(a - b)) / denom, 0.0, 5.0) / 5.0)
        return score


class BioLayer:
    def __init__(
        self,
        n_neurons: int,
        input_dim: int,
        *,
        neuron_cls: Type[BioNeuron] = BioNeuron,
        neuron_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        params = dict(neuron_kwargs or {})
        self.neurons = [neuron_cls(num_inputs=input_dim, **params) for _ in range(n_neurons)]

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [n.forward(inputs) for n in self.neurons]

    def learn(self, inputs: Sequence[float], outputs: Sequence[float]) -> None:
        for n, out in zip(self.neurons, outputs):
            n.hebbian_learn(inputs, out)


class NetworkBuilder:
    """Factory for constructing BioNet-like topologies from configuration."""

    def __init__(self, neuron_registry: Mapping[str, Type[BioNeuron]] | None = None) -> None:
        self.neuron_registry: Dict[str, Type[BioNeuron]] = {"BioNeuron": BioNeuron}
        if neuron_registry:
            self.neuron_registry.update(dict(neuron_registry))

    def register(self, name: str, neuron_cls: Type[BioNeuron]) -> None:
        self.neuron_registry[name] = neuron_cls

    def _resolve_neuron_class(self, neuron_type: Any) -> Type[BioNeuron]:
        if isinstance(neuron_type, type) and issubclass(neuron_type, BioNeuron):
            return neuron_type
        if isinstance(neuron_type, str):
            try:
                return self.neuron_registry[neuron_type]
            except KeyError as exc:
                known = ", ".join(sorted(self.neuron_registry))
                raise KeyError(f"Unknown neuron type '{neuron_type}'. Known: {known}") from exc
        raise TypeError("neuron_type must be a subclass of BioNeuron or registered name")

    def build_layers(self, config: Mapping[str, Any]) -> List[BioLayer]:
        input_dim = config.get("input_dim")
        if input_dim is None:
            raise ValueError("Configuration must define 'input_dim'.")

        layers_cfg = config.get("layers")
        if not isinstance(layers_cfg, Iterable):
            raise ValueError("Configuration must include iterable 'layers'.")

        layers: List[BioLayer] = []
        current_input_dim = int(input_dim)
        for layer_cfg in layers_cfg:
            if not isinstance(layer_cfg, Mapping):
                raise TypeError("Each layer configuration must be a mapping.")

            neuron_count = layer_cfg.get("size") or layer_cfg.get("n_neurons")
            if neuron_count is None:
                raise ValueError("Layer configuration missing 'size'/'n_neurons'.")

            neuron_type = layer_cfg.get("neuron_type", "BioNeuron")
            neuron_params = layer_cfg.get("params", {})
            neuron_cls = self._resolve_neuron_class(neuron_type)

            layer_input_dim = layer_cfg.get("input_dim", current_input_dim)
            if layer_input_dim is None:
                raise ValueError("Layer configuration missing 'input_dim'.")

            layer = BioLayer(
                int(neuron_count),
                int(layer_input_dim),
                neuron_cls=neuron_cls,
                neuron_kwargs=neuron_params,
            )
            layers.append(layer)
            current_input_dim = int(layer_cfg.get("output_dim", neuron_count))

        return layers


def _load_config(config: Mapping[str, Any] | str | Path | None) -> Mapping[str, Any]:
    if config is None:
        return {}
    if isinstance(config, Mapping):
        return config
    path = Path(config)
    data = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(data)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "PyYAML is required to load YAML configurations."
            ) from exc
        return yaml.safe_load(data)
    raise ValueError(f"Unsupported configuration format: {suffix}")


class BioNet:
    """Configurable bio-inspired feedforward network."""

    def __init__(
        self,
        config: Mapping[str, Any] | str | Path | None = None,
        *,
        builder: NetworkBuilder | None = None,
    ) -> None:
        builder = builder or NetworkBuilder()
        base_config: MutableMapping[str, Any] = {
            "input_dim": 2,
            "layers": [
                {"size": 3, "neuron_type": "BioNeuron"},
                {"size": 3, "neuron_type": "BioNeuron"},
            ],
        }
        user_config = _load_config(config)
        if user_config:
            base_config.update({k: v for k, v in user_config.items() if v is not None})

        self.layers = builder.build_layers(base_config)

    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[List[float]]]:
        layer_outputs: List[List[float]] = []
        current_inputs: Sequence[float] = inputs
        for layer in self.layers:
            current_inputs = layer.forward(current_inputs)
            layer_outputs.append(current_inputs)
        final_output = list(layer_outputs[-1]) if layer_outputs else list(inputs)
        return final_output, layer_outputs

    def learn(self, inputs: Sequence[float]) -> None:
        final_output, layer_outputs = self.forward(inputs)
        if not layer_outputs:
            return

        target_value = float(np.mean(final_output)) if final_output else 0.0
        prev_inputs: Sequence[float] = inputs
        for idx, (layer, outputs) in enumerate(zip(self.layers, layer_outputs)):
            if idx == len(self.layers) - 1:
                layer.learn(prev_inputs, [target_value] * len(outputs))
            else:
                layer.learn(prev_inputs, outputs)
            prev_inputs = outputs


def cli_loop() -> None:
    net = BioNet()
    print("== BioNeuron CLI ==")
    while True:
        s = input("請輸入兩個數字 (a b) 或 q 離開：")
        if s.lower() == "q":
            break
        try:
            a, b = map(float, s.strip().split())
        except ValueError:
            print("格式錯誤，請再輸入")
            continue
        final_output, layer_outputs = net.forward([a, b])
        novelty = (
            net.layers[0].neurons[0].novelty_score()
            if getattr(net, "layers", None)
            else 0.0
        )
        print(
            f"\u8f38\u51fa：{final_output}"
            f" | novelty={novelty:.3f}"
            f" | 第一層輸出={layer_outputs[0] if layer_outputs else []}"
        )
        net.learn([a, b])


# TODO: 之後若改 LIF + STDP，保留此 API，不破壞上層介面.
