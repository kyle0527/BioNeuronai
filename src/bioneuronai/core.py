from __future__ import annotations
from typing import Any, List, MutableMapping, Sequence, Tuple
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
    def __init__(self, n_neurons: int, input_dim: int) -> None:
        self.neurons = [BioNeuron(input_dim) for _ in range(n_neurons)]

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [n.forward(inputs) for n in self.neurons]

    def learn(self, inputs: Sequence[float], outputs: Sequence[float]) -> None:
        for n, out in zip(self.neurons, outputs):
            n.hebbian_learn(inputs, out)


class BioNet:
    """Wrapper around :class:`ConfigurableNetwork` with a default topology."""

    def __init__(
        self,
        input_dim: int = 2,
        layer_configs: Sequence[Any] | None = None,
        network_config: Any | None = None,
        neuron_factories: MutableMapping[str, Any] | None = None,
    ) -> None:
        from .networks.configurable import LayerConfig, NetworkConfig, build_network

        if network_config is not None and layer_configs is not None:
            raise ValueError("Provide either 'layer_configs' or 'network_config', not both.")

        if network_config is None:
            if layer_configs is None:
                layer_configs = [
                    LayerConfig(size=3, neuron="BioNeuron"),
                    LayerConfig(size=3, neuron="BioNeuron"),
                ]
            normalised_layers: List[LayerConfig] = []
            for layer in layer_configs:
                if isinstance(layer, LayerConfig):
                    normalised_layers.append(layer)
                elif isinstance(layer, dict):
                    normalised_layers.append(LayerConfig.from_dict(layer))
                else:
                    raise TypeError(
                        "Layer configuration items must be LayerConfig instances or dictionaries."
                    )
            config_obj = NetworkConfig(input_dim=input_dim, layers=normalised_layers)
        else:
            if isinstance(network_config, dict):
                config_obj = NetworkConfig.from_dict(network_config)
            else:
                config_obj = network_config

        self._network = build_network(config_obj, neuron_factories)
        self.layers = self._network.layers
        self.layer1 = self.layers[0] if len(self.layers) > 0 else None
        self.layer2 = self.layers[1] if len(self.layers) > 1 else None

    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[List[float]]]:
        final, layer_outputs = self._network.forward(inputs)
        return final, layer_outputs

    def learn(self, inputs: Sequence[float]) -> Tuple[List[float], List[List[float]]]:
        return self._network.learn(inputs)

    def to_config(self):
        return self._network.to_config()


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
        outputs, _ = net.forward([a, b])
        print(f"\u8f38\u51fa：{outputs} | novelty={net.layer1.neurons[0].novelty_score():.3f}")
        net.learn([a, b])


# TODO: 之後若改 LIF + STDP，保留此 API，不破壞上層介面.
