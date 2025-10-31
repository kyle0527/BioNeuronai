from __future__ import annotations
import importlib
import json
from pathlib import Path
from typing import List, Sequence, Tuple, Type
import numpy as np

from .base import BaseBioNeuron


class BioNeuron(BaseBioNeuron):
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
        super().__init__()
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

    # ------------------------------------------------------------------
    # Serialization hooks
    # ------------------------------------------------------------------
    def _serialize_state(self) -> dict:
        return {
            "config": {
                "num_inputs": self.num_inputs,
                "threshold": self.threshold,
                "learning_rate": self.learning_rate,
                "memory_len": self.memory_len,
            },
            "weights": self.weights.tolist(),
            "input_memory": [mem.tolist() for mem in self.input_memory],
        }

    @classmethod
    def _from_serialized_state(cls, state: dict) -> "BioNeuron":
        config = state.get("config", {})
        weights = state.get("weights", [])
        num_inputs = int(config.get("num_inputs", len(weights)))
        threshold = float(config.get("threshold", 0.8))
        learning_rate = float(config.get("learning_rate", 0.01))
        memory_len = int(config.get("memory_len", max(len(state.get("input_memory", [])), 1)))

        neuron = cls(
            num_inputs=num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
        )
        if weights:
            neuron.weights = np.asarray(weights, dtype=np.float32)
        input_memory = state.get("input_memory", [])
        neuron.input_memory = [np.asarray(mem, dtype=np.float32) for mem in input_memory][-neuron.memory_len :]
        return neuron

    def get_statistics(self) -> dict:
        return {
            "novelty_score": self.novelty_score(),
            "memory_length": len(self.input_memory),
            "threshold": self.threshold,
        }


class BioLayer:
    def __init__(
        self,
        n_neurons: int,
        input_dim: int,
        neuron_cls: Type[BaseBioNeuron] = BioNeuron,
        **neuron_kwargs,
    ) -> None:
        self.input_dim = input_dim
        self.neuron_cls = neuron_cls
        self.neuron_kwargs = neuron_kwargs
        self.neurons = [neuron_cls(input_dim, **neuron_kwargs) for _ in range(n_neurons)]

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [n.forward(inputs) for n in self.neurons]

    def learn(self, inputs: Sequence[float], outputs: Sequence[float]) -> None:
        for n, out in zip(self.neurons, outputs):
            n.hebbian_learn(inputs, out)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "neuron_cls": f"{self.neuron_cls.__module__}:{self.neuron_cls.__name__}",
            "neuron_kwargs": self.neuron_kwargs,
            "n_neurons": len(self.neurons),
            "input_dim": self.input_dim,
            "neurons": [neuron.to_dict() for neuron in self.neurons],
        }

    def load_state(self, data: dict) -> None:
        neurons_data = data.get("neurons", [])
        self.neurons = [BaseBioNeuron.from_dict(d) for d in neurons_data]
        cls_path = data.get("neuron_cls")
        if cls_path:
            module_name, _, class_name = cls_path.partition(":")
            try:
                module = importlib.import_module(module_name)
                self.neuron_cls = getattr(module, class_name)
            except (ImportError, AttributeError):  # pragma: no cover - defensive
                self.neuron_cls = BioNeuron
        self.neuron_kwargs = data.get("neuron_kwargs", {})
        self.input_dim = int(data.get("input_dim", self.input_dim))

    @classmethod
    def from_dict(cls, data: dict) -> "BioLayer":
        cls_path = data.get("neuron_cls")
        neuron_kwargs = data.get("neuron_kwargs", {})
        neurons_data = data.get("neurons", [])
        n_neurons = int(data.get("n_neurons", len(neurons_data)))

        neuron_cls: Type[BaseBioNeuron] = BioNeuron
        if cls_path:
            module_name, _, class_name = cls_path.partition(":")
            try:
                module = importlib.import_module(module_name)
                loaded_cls = getattr(module, class_name)
                if issubclass(loaded_cls, BaseBioNeuron):
                    neuron_cls = loaded_cls
            except (ImportError, AttributeError, TypeError):  # pragma: no cover - defensive
                neuron_cls = BioNeuron

        if neurons_data:
            input_dim = int(
                data.get(
                    "input_dim",
                    neurons_data[0]["state"].get("config", {}).get(
                        "num_inputs",
                        len(neurons_data[0]["state"].get("weights", [])),
                    ),
                )
            )
        else:
            input_dim = int(data.get("input_dim", 0))

        layer = cls(
            n_neurons=n_neurons,
            input_dim=input_dim,
            neuron_cls=neuron_cls,
            **neuron_kwargs,
        )
        if neurons_data:
            layer.neurons = [BaseBioNeuron.from_dict(d) for d in neurons_data]
        layer.neuron_kwargs = neuron_kwargs
        layer.input_dim = input_dim
        layer.neuron_cls = neuron_cls
        return layer


class BioNet:
    """Two-layer demo 2 -> 3 -> 3; returns (l2_out, l1_out)."""
    def __init__(self) -> None:
        self.layer1 = BioLayer(3, 2)
        self.layer2 = BioLayer(3, 3)

    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[float]]:
        l1_out = self.layer1.forward(inputs)
        l2_out = self.layer2.forward(l1_out)
        return l2_out, l1_out

    def learn(self, inputs: Sequence[float]) -> None:
        l2_out, l1_out = self.forward(inputs)
        target = float(sum(l2_out) / len(l2_out))
        self.layer2.learn(l1_out, [target] * 3)
        self.layer1.learn(inputs, l1_out)

    def get_layers(self) -> List[BioLayer]:
        layers: List[BioLayer] = []
        index = 1
        while True:
            layer = getattr(self, f"layer{index}", None)
            if layer is None:
                break
            layers.append(layer)
            index += 1
        return layers

    def to_dict(self) -> dict:
        return {
            "module": self.__class__.__module__,
            "class": self.__class__.__name__,
            "layers": [layer.to_dict() for layer in self.get_layers()],
        }

    def load_state(self, data: dict) -> None:
        layers_data = data.get("layers", [])
        if not layers_data:
            return

        current_layers = self.get_layers()
        updated_layers: List[BioLayer] = []
        for idx, state in enumerate(layers_data):
            if idx < len(current_layers):
                current_layers[idx].load_state(state)
                layer = current_layers[idx]
            else:
                layer = BioLayer.from_dict(state)
            updated_layers.append(layer)

        for idx, layer in enumerate(updated_layers, start=1):
            setattr(self, f"layer{idx}", layer)

        # Remove any leftover layers not present in the serialized state.
        extra_index = len(updated_layers) + 1
        while hasattr(self, f"layer{extra_index}"):
            delattr(self, f"layer{extra_index}")
            extra_index += 1

    def save(self, path: str | Path, state: dict | None = None) -> dict:
        target = Path(path)
        if target.parent:
            target.parent.mkdir(parents=True, exist_ok=True)
        if state is None:
            state = self.to_dict()
        target.write_text(json.dumps(state))
        return state

    @classmethod
    def load(cls, path: str | Path) -> "BioNet":
        source = Path(path)
        data = json.loads(source.read_text())
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "BioNet":
        module_name = data.get("module", cls.__module__)
        class_name = data.get("class", cls.__name__)

        try:
            if module_name == cls.__module__ and class_name == cls.__name__:
                net_cls = cls
            else:
                module = importlib.import_module(module_name)
                candidate = getattr(module, class_name)
                if issubclass(candidate, BioNet):
                    net_cls = candidate
                else:  # pragma: no cover - defensive
                    net_cls = cls
        except (ImportError, AttributeError, TypeError):  # pragma: no cover - defensive
            net_cls = cls

        network = net_cls()
        network.load_state(data)
        return network


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
