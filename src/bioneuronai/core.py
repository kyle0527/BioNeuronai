from __future__ import annotations
from typing import List, Sequence, Tuple

from typing import List, Sequence, Tuple

import numpy as np

from .neurons.base import (
    BaseNeuron,
    HebbianLearningStrategy,
    LearningStrategy,
    NoOpThresholdStrategy,
)


class BioNeuron(BaseNeuron):
    """Bio-inspired neuron with short-term input memory and Hebbian update."""

from typing import List, Sequence, Type

import numpy as np

try:
    from numba import njit

    @njit(cache=True)
    def _numba_batch_hebbian(
        weights: np.ndarray,
        inputs_batch: np.ndarray,
        outputs_batch: np.ndarray,
        learning_rates: np.ndarray,
    ) -> None:
        """Numba 加速的 Hebbian 批次更新，確保 in-place 操作。"""

        batch_size = inputs_batch.shape[0]
        n_neurons = weights.shape[0]
        n_inputs = weights.shape[1]

        for b in range(batch_size):
            for j in range(n_neurons):
                lr = learning_rates[j]
                out = outputs_batch[b, j]
                for i in range(n_inputs):
                    updated = weights[j, i] + lr * inputs_batch[b, i] * out
                    if updated < 0.0:
                        updated = 0.0
                    elif updated > 1.0:
                        updated = 1.0
                    weights[j, i] = updated

except ImportError:  # pragma: no cover - numba 為可選依賴
    njit = None
    _numba_batch_hebbian = None


from .base import BaseBioNeuron



class BioNeuron:
    """Bio-inspired neuron with short-term memory and Hebbian updates.

    生物啟發神經元，具備短期記憶與 Hebbian 權重更新機制。


    """


    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
        *,
        learning_strategy: LearningStrategy | None = None,
    ) -> None:
        online_window: int | None = None,
        stability_coefficient: float = 0.05,
    ) -> None:

        super().__init__(
            num_inputs=num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
            learning_strategy=learning_strategy
            or HebbianLearningStrategy(learning_rate),
            threshold_strategy=NoOpThresholdStrategy(),
        )

    def hebbian_learn(self, inputs: Sequence[float], output: float) -> None:
        self.learn(inputs, output)
        )

        super().__init__()
        self.num_inputs = num_inputs
        rng = np.random.default_rng(seed)
        self.weights = rng.uniform(0.1, 0.9, num_inputs).astype(np.float32)
        self.threshold = float(threshold)
        self.learning_rate = float(learning_rate)
        self.memory_len = int(memory_len)
        self.input_memory: List[np.ndarray] = []
        self.online_window = (
            int(online_window) if online_window and online_window > 0 else None
        )
        self.stability_coefficient = float(np.clip(stability_coefficient, 0.0, 1.0))
        self.baseline_weights = self.weights.copy()

    def forward(self, inputs: Sequence[float]) -> float:

        assert len(inputs) == self.num_inputs
        x = np.asarray(inputs, dtype=np.float32)

        # short-term memory
        self._remember_input(x)

        potential = float(np.dot(self.weights, x))
        activated = potential >= self.threshold
        self._record_activation(activated)
        return min(1.0, potential) if activated else 0.0

    def hebbian_learn(self, inputs: Sequence[float], output: float | None = None, **_: object) -> None:
        if output is None:
            raise ValueError("BioNeuron.hebbian_learn requires a numeric output value")
        x = np.asarray(inputs, dtype=np.float32)
        delta = self.learning_rate * x * float(output)
        self.weights = self.weights + delta
        self._clip_weights(min_value=0.0, max_value=1.0)

        potential = float(np.dot(self.weights, x))
        return self._finalize_potential(x, potential)

    def _finalize_potential(self, x: np.ndarray, potential: float) -> float:
        """Finalize activation given a precomputed membrane potential."""

        # numpy 向量化流程會重複使用輸入，因此需要複製以避免共享引用被修改
        self.input_memory.append(x.copy())
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

        if potential >= self.threshold:
            return min(1.0, potential)
        return 0.0


    def learn(self, inputs: Sequence[float], target: float | None = None) -> None:
        x = self._prepare_inputs(inputs)
        output = (
            self.output_memory[-1]
            if target is None and self.output_memory
            else float(target) if target is not None else self.forward(inputs)
        )
        delta = self.learning_rate * x * float(output)

        self.weights = np.clip(self.weights + delta, 0.0, 1.0)
        if self.online_window:
            self._apply_online_regularization()

    def hebbian_learn(self, inputs: Sequence[float], output: float) -> None:
        self.learn(inputs, output)

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


    def configure_online_learning(
        self, window_size: int | None, stability_coefficient: float | None = None
    ) -> None:
        """Enable/disable online learning safeguards."""
        self.online_window = (
            int(window_size) if window_size and window_size > 0 else None
        )
        if stability_coefficient is not None:
            self.stability_coefficient = float(
                np.clip(stability_coefficient, 0.0, 1.0)
            )

    def online_learn(self, inputs: Sequence[float], target: float | None = None) -> float:
        """Convenience wrapper for forward + Hebbian update with stability control."""
        output = self.forward(inputs)
        teaching_signal = target if target is not None else output
        self.hebbian_learn(inputs, teaching_signal)
        return output

    def save_state(self, path: str | Path) -> None:
        """Persist the neuron parameters and memory using ``numpy.savez``."""
        path = Path(path)
        memory_array = self._memory_array()
        np.savez_compressed(
            path,
            num_inputs=np.array([self.num_inputs], dtype=np.int32),
            threshold=np.array([self.threshold], dtype=np.float32),
            learning_rate=np.array([self.learning_rate], dtype=np.float32),
            memory_len=np.array([self.memory_len], dtype=np.int32),
            weights=self.weights.astype(np.float32),
            input_memory=memory_array,
            online_window=np.array(
                [self.online_window if self.online_window is not None else -1],
                dtype=np.int32,
            ),
            stability_coefficient=np.array(
                [self.stability_coefficient], dtype=np.float32
            ),
            baseline_weights=self.baseline_weights.astype(np.float32),
        )

    @classmethod
    def load_state(cls, path: str | Path) -> "BioNeuron":
        """Load a neuron instance from ``numpy.savez`` persistence."""
        data = np.load(Path(path), allow_pickle=False)
        num_inputs = int(data["num_inputs"][0])
        threshold = float(data["threshold"][0])
        learning_rate = float(data["learning_rate"][0])
        memory_len = int(data["memory_len"][0])
        online_window = int(data["online_window"][0])
        stability_coefficient = float(data["stability_coefficient"][0])



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


            online_window=online_window if online_window > 0 else None,
            stability_coefficient=stability_coefficient,
        )
        neuron.weights = data["weights"].astype(np.float32)
        neuron.threshold = threshold
        neuron.learning_rate = learning_rate
        neuron.memory_len = memory_len
        neuron.baseline_weights = data["baseline_weights"].astype(np.float32)

        memory_array = data["input_memory"]
        neuron.input_memory = cls._memory_from_array(memory_array)
        return neuron

    def _apply_online_regularization(self) -> None:
        if not self.input_memory:
            return
        window_size = self.online_window or len(self.input_memory)
        recent_inputs = np.asarray(self.input_memory[-window_size:], dtype=np.float32)
        activity_level = float(np.clip(np.mean(np.abs(recent_inputs)), 0.0, 1.0))
        self.baseline_weights = (
            (1.0 - self.stability_coefficient) * self.baseline_weights
            + self.stability_coefficient * self.weights
        )
        mix = self.stability_coefficient * (1.0 - 0.5 * activity_level)
        mix = float(np.clip(mix / max(1, window_size), 0.0, 0.25))
        self.weights = np.clip(
            (1.0 - mix) * self.weights + mix * self.baseline_weights,
            0.0,
            1.0,
        )

    def _memory_array(self) -> np.ndarray:
        if not self.input_memory:
            return np.empty((0, self.num_inputs), dtype=np.float32)
        return np.stack(self.input_memory).astype(np.float32)

    @staticmethod
    def _memory_from_array(array: np.ndarray) -> List[np.ndarray]:
        if array.size == 0:
            return []
        return [array[i].astype(np.float32) for i in range(array.shape[0])]



    def learn(self, inputs: Sequence[float], target: float | None = None) -> float:
        """Public learning hook that keeps compatibility with the base API."""

        output = self.forward(inputs) if target is None else float(target)
        self.hebbian_learn(inputs, output)
        return output


    def novelty_score(self) -> float:
        """Return a 0~1 novelty score based on the last two inputs.

        透過最近兩筆輸入的平均差異取得 0~1 範圍的新穎性分數。
        """
        if len(self.input_memory) < 2:
            return 0.0
        a, b = self.input_memory[-1], self.input_memory[-2]
        denom = np.maximum(1e-6, np.mean(np.abs(b)))
        score = float(np.clip(np.mean(np.abs(a - b)) / denom, 0.0, 5.0) / 5.0)
        return score



class BioLayer:

        self,
        n_neurons: int,
        input_dim: int,

        use_vectorized: bool = True,
        accelerator: str | None = None,
    ) -> None:
        self.neurons = [BioNeuron(input_dim) for _ in range(n_neurons)]
        self.use_vectorized = use_vectorized
        self._weight_matrix = np.stack([n.weights for n in self.neurons]).astype(np.float32)
        self._bind_weight_matrix()

        allowed_accelerators = {None, "numba"}
        if accelerator not in allowed_accelerators:
            warnings.warn(
                f"未知的 accelerator '{accelerator}'，將回退為純 NumPy 實作。",
                RuntimeWarning,
            )
            accelerator = None

        if accelerator == "numba" and _numba_batch_hebbian is None:
            warnings.warn(
                "未安裝 numba，BioLayer 將回退為 NumPy 批次更新。",
                RuntimeWarning,
            )
            accelerator = None

        self._accelerator = accelerator

    def _bind_weight_matrix(self) -> None:
        for idx, neuron in enumerate(self.neurons):
            neuron.weights = self._weight_matrix[idx]

    def _get_learning_rates(self) -> np.ndarray:
        return np.asarray([n.learning_rate for n in self.neurons], dtype=np.float32)

    def forward(
        self,
        inputs: Sequence[float],
        *,
        use_vectorized: bool | None = None,
    ) -> List[float]:
        vectorized = self.use_vectorized if use_vectorized is None else use_vectorized
        if not vectorized:
            return [n.forward(inputs) for n in self.neurons]


        *,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        rng = np.random.default_rng(seed)
        self.neurons = []
        for _ in range(n_neurons):
            neuron_seed = None if seed is None else int(rng.integers(0, 1_000_000))
            self.neurons.append(
                BioNeuron(
                    input_dim,
                    threshold=threshold,
                    learning_rate=learning_rate,
                    memory_len=memory_len,
                    seed=neuron_seed,
                )
            )

        neuron_cls: Type[BaseBioNeuron] = BioNeuron,

        neuron_kwargs: dict | None = None,
    ) -> None:
        if n_neurons <= 0:
            raise ValueError("n_neurons must be positive")
        if input_dim <= 0:
            raise ValueError("input_dim must be positive")

        neuron_kwargs = neuron_kwargs or {}
        self.neurons: List[BaseBioNeuron] = [
            neuron_cls(num_inputs=input_dim, **neuron_kwargs) for _ in range(n_neurons)
        ]

        **neuron_kwargs,
    ) -> None:
        self.input_dim = input_dim
        self.neuron_cls = neuron_cls
        self.neuron_kwargs = neuron_kwargs
        self.neurons = [neuron_cls(input_dim, **neuron_kwargs) for _ in range(n_neurons)]




        x = np.asarray(inputs, dtype=np.float32)
        if x.ndim != 1 or x.shape[0] != self._weight_matrix.shape[1]:
            raise ValueError("輸入維度與層設定不符")

        potentials = self._weight_matrix @ x
        outputs: list[float] = []
        for idx, neuron in enumerate(self.neurons):
            outputs.append(neuron._finalize_potential(x, float(potentials[idx])))
        return outputs


        self,
        inputs: Sequence[float] | Sequence[Sequence[float]],
        outputs: Sequence[float] | Sequence[Sequence[float]],
        *,
        use_vectorized: bool | None = None,
    ) -> None:
        vectorized = self.use_vectorized if use_vectorized is None else use_vectorized

        inputs_arr = np.asarray(inputs, dtype=np.float32)
        outputs_arr = np.asarray(outputs, dtype=np.float32)

        if inputs_arr.ndim == 1:
            inputs_arr = inputs_arr.reshape(1, -1)
        if outputs_arr.ndim == 1:
            outputs_arr = outputs_arr.reshape(1, -1)

        if inputs_arr.shape[1] != self._weight_matrix.shape[1]:
            raise ValueError("輸入維度與層設定不符")
        if outputs_arr.shape[1] != len(self.neurons):
            raise ValueError("輸出向量長度必須等於神經元數量")
        if inputs_arr.shape[0] != outputs_arr.shape[0]:
            raise ValueError("輸入與輸出批次大小不一致")

        if not vectorized:
            for sample_inputs, sample_outputs in zip(inputs_arr, outputs_arr):
                for neuron, out in zip(self.neurons, sample_outputs):
                    neuron.hebbian_learn(sample_inputs, float(out))
            return

        learning_rates = self._get_learning_rates()

        if self._accelerator == "numba" and _numba_batch_hebbian is not None:
            _numba_batch_hebbian(self._weight_matrix, inputs_arr, outputs_arr, learning_rates)
        else:
            delta = outputs_arr.T @ inputs_arr
            delta *= learning_rates[:, None]
            np.add(self._weight_matrix, delta, out=self._weight_matrix, casting="unsafe")

        np.clip(self._weight_matrix, 0.0, 1.0, out=self._weight_matrix)


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


    def configure_online_learning(
        self, window_size: int | None, stability_coefficient: float | None = None
    ) -> None:
        for neuron in self.neurons:
            neuron.configure_online_learning(window_size, stability_coefficient)

    def _collect_state(self) -> dict[str, Any]:
        weights = np.stack([n.weights for n in self.neurons]).astype(np.float32)
        baseline_weights = (
            np.stack([n.baseline_weights for n in self.neurons]).astype(np.float32)
        )
        thresholds = np.array([n.threshold for n in self.neurons], dtype=np.float32)
        learning_rates = np.array(
            [n.learning_rate for n in self.neurons], dtype=np.float32
        )
        memory_len = np.array([n.memory_len for n in self.neurons], dtype=np.int32)
        online_window = np.array(
            [n.online_window if n.online_window is not None else -1 for n in self.neurons],
            dtype=np.int32,
        )
        stability = np.array(
            [n.stability_coefficient for n in self.neurons], dtype=np.float32
        )
        num_inputs = np.array([n.num_inputs for n in self.neurons], dtype=np.int32)
        input_memory = np.array([n._memory_array() for n in self.neurons], dtype=object)
        return {
            "weights": weights,
            "baseline_weights": baseline_weights,
            "thresholds": thresholds,
            "learning_rates": learning_rates,
            "memory_len": memory_len,
            "online_window": online_window,
            "stability": stability,
            "num_inputs": num_inputs,
            "input_memory": input_memory,
        }

    def _restore_state(self, state: dict[str, Any]) -> None:
        weights = state["weights"]
        baseline_weights = state["baseline_weights"]
        thresholds = state["thresholds"]
        learning_rates = state["learning_rates"]
        memory_len = state["memory_len"]
        online_window = state["online_window"]
        stability = state["stability"]
        num_inputs = state["num_inputs"]
        input_memory = state["input_memory"]

        if len(self.neurons) != weights.shape[0]:
            raise ValueError("State does not match layer neuron count")

        for idx, neuron in enumerate(self.neurons):
            if neuron.num_inputs != int(num_inputs[idx]):
                raise ValueError("State input dimensions do not match")
            neuron.weights = weights[idx].astype(np.float32)
            neuron.baseline_weights = baseline_weights[idx].astype(np.float32)
            neuron.threshold = float(thresholds[idx])
            neuron.learning_rate = float(learning_rates[idx])
            neuron.memory_len = int(memory_len[idx])
            window = int(online_window[idx])
            neuron.online_window = window if window > 0 else None
            neuron.stability_coefficient = float(stability[idx])
            mem_array = input_memory[idx]
            neuron.input_memory = BioNeuron._memory_from_array(mem_array)



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


    """Two-layer demo 2 -> 3 -> 3; returns (l2_out, l1_out)."""


    def __init__(
        self,
        *,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        self.layer1 = BioLayer(
            3,
            2,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
        )
        self.layer2 = BioLayer(
            3,
            3,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=None if seed is None else seed + 1,
        )



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


    def configure_online_learning(
        self, window_size: int | None, stability_coefficient: float | None = None
    ) -> None:
        self.layer1.configure_online_learning(window_size, stability_coefficient)
        self.layer2.configure_online_learning(window_size, stability_coefficient)

    def save_state(self, path: str | Path) -> None:
        data = {}
        for idx, layer in enumerate((self.layer1, self.layer2), start=1):
            prefix = f"layer{idx}"
            layer_state = layer._collect_state()
            for key, value in layer_state.items():
                data[f"{prefix}_{key}"] = value
        np.savez_compressed(path, **data)

    @classmethod
    def load_state(cls, path: str | Path) -> "BioNet":
        data = np.load(Path(path), allow_pickle=True)
        net = cls()
        for idx, layer in enumerate((net.layer1, net.layer2), start=1):
            prefix = f"layer{idx}_"
            layer_state = {
                key[len(prefix) :]: data[key]
                for key in data.files
                if key.startswith(prefix)
            }
            layer._restore_state(layer_state)
        return net


def cli_loop(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="BioNeuronAI 互動式 CLI")
    parser.add_argument("--load", type=Path, help="從檔案載入網路狀態")
    parser.add_argument("--save", type=Path, help="離開時將網路狀態保存至檔案")
    parser.add_argument(
        "--online-window",
        type=int,
        default=0,
        help="啟用在線學習模式並設定滑動窗口大小 (0 表示關閉)",
    )
    parser.add_argument(
        "--stability",
        type=float,
        default=0.05,
        help="在線學習穩定性係數 (0-1, 越大越強)",
    )
    args = parser.parse_args(argv)

    if args.load:
        try:
            net = BioNet.load_state(args.load)
            print(f"已從 {args.load} 載入網路狀態。")
        except OSError as exc:
            print(f"載入失敗：{exc}. 使用預設網路。")
            net = BioNet()
    else:
        net = BioNet()

    if args.online_window:
        net.configure_online_learning(args.online_window, args.stability)

    def average_novelty(self) -> float:
        values = [n.novelty_score() for n in self.layer1.neurons]
        if not values:
            return 0.0
        return float(np.mean(values))


    def collect_weights(self) -> List[List[float]]:
        return [n.weights.astype(float).tolist() for n in self.layer1.neurons]


@dataclass
class CLIState:
    net: BioNet
    novelty_history: List[float]

    def register_inputs(self, inputs: Sequence[float]) -> Tuple[List[float], float]:
        outputs, _ = self.net.forward(inputs)
        self.net.learn(inputs)
        novelty = self.net.average_novelty()
        self.novelty_history.append(novelty)
        return outputs, novelty


app = typer.Typer(help="BioNeuron demo CLI with batch and interactive modes")


def _parse_inputs(raw_values: Iterable[str]) -> List[float]:
    values = [float(v) for v in raw_values]
    if len(values) != 2:
        raise typer.BadParameter("需要正好兩個數字作為輸入")
    return values


def _get_state(ctx: typer.Context) -> CLIState:
    if ctx.obj is None:
        raise typer.BadParameter("CLI state 尚未初始化")
    return ctx.obj


@app.callback()
def main(
    ctx: typer.Context,
    threshold: float = typer.Option(0.8, min=0.0, max=1.5, help="觸發閾值"),
    learning_rate: float = typer.Option(
        0.01, min=0.0, max=1.0, help="Hebbian 學習速率"
    ),
    memory_len: int = typer.Option(5, min=1, max=20, help="輸入記憶長度"),
    seed: int | None = typer.Option(None, help="隨機權重種子"),
) -> None:
    """配置並初始化 BioNet 實例。"""

    ctx.ensure_object(dict)
    ctx.obj = CLIState(
        net=BioNet(
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
        ),
        novelty_history=[],
    )


def _format_stats(state: CLIState) -> str:
    weights = state.net.collect_weights()
    threshold = state.net.layer1.neurons[0].threshold if state.net.layer1.neurons else 0.0
    avg_novelty = state.net.average_novelty()
    lines = [
        "=== BioNeuron 統計 ===",
        f"觸發閾值: {threshold:.3f}",
        f"平均新穎性: {avg_novelty:.3f}",
        "權重 (第一層):",
    ]
    for idx, weight_vector in enumerate(weights, start=1):
        weight_str = ", ".join(f"{w:.3f}" for w in weight_vector)
        lines.append(f"  神經元 {idx}: [{weight_str}]")
    return "\n".join(lines)


def _process_line(state: CLIState, line: str) -> Tuple[List[float], float]:
    tokens = [token for token in line.replace(",", " ").split() if token]
    if not tokens:
        raise ValueError("空白行")
    values = _parse_inputs(tokens)
    return state.register_inputs(values)


def _run_batch(ctx: typer.Context, source: Iterable[str]) -> None:
    state = _get_state(ctx)
    for idx, raw in enumerate(source, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            outputs, novelty = _process_line(state, line)
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"第 {idx} 行發生錯誤: {exc}", err=True)
            continue
        typer.echo(
            f"輸入 {line} -> 輸出: {[round(o, 3) for o in outputs]}, 新穎性: {novelty:.3f}"
        )


@app.command(help="讀取批次輸入檔並逐行推論")
def batch(
    ctx: typer.Context,
    file: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
) -> None:
    """Process a file containing two-number inputs per line."""

    with file.open("r", encoding="utf-8") as fh:
        _run_batch(ctx, fh)


@app.command(help="進入互動式選單")
def interactive(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    typer.echo("== BioNeuron 互動選單 ==")
    while True:
        typer.echo("[1] 單筆推論  [2] 查看統計  [3] 載入批次檔  [q] 離開")
        choice = typer.prompt("請選擇操作").strip().lower()
        if choice in {"q", "quit", "exit"}:
            typer.echo("已離開互動模式")
            break
        if choice == "1":
            payload = typer.prompt("輸入兩個數字 (a b)")
            try:
                outputs, novelty = _process_line(state, payload)
            except Exception as exc:  # noqa: BLE001
                typer.secho(f"輸入錯誤: {exc}", fg=typer.colors.RED)
                continue
            typer.secho(
                f"輸出: {[round(o, 3) for o in outputs]} | 平均新穎性: {novelty:.3f}",
                fg=typer.colors.GREEN,
            )
        elif choice == "2":
            typer.echo(_format_stats(state))
        elif choice == "3":
            path_input = typer.prompt("請輸入批次檔路徑")
            path = Path(path_input).expanduser()
            if not path.exists() or not path.is_file():
                typer.secho("找不到批次檔案", fg=typer.colors.RED)
                continue
            with path.open("r", encoding="utf-8") as fh:
                _run_batch(ctx, fh)
        else:
            typer.secho("未知選項，請再試一次", fg=typer.colors.YELLOW)


@app.command(help="顯示權重與新穎性統計")
def stats(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    typer.echo(_format_stats(state))



def cli_loop() -> None:

    app()

    print("== BioNeuron CLI ==")
    print("輸入 'save <path>' 保存、'load <path>' 重新載入、'q' 離開。")
    while True:
        s = input("請輸入兩個數字 (a b)：").strip()
        if not s:
            continue
        lower = s.lower()
        if lower == "q":
            break
        if lower.startswith("save "):
            dest = Path(s.split(maxsplit=1)[1])
            try:
                net.save_state(dest)
                print(f"狀態已保存至 {dest}。")
            except OSError as exc:
                print(f"保存失敗：{exc}")
            continue
        if lower.startswith("load "):
            src = Path(s.split(maxsplit=1)[1])
            try:
                net = BioNet.load_state(src)
                if args.online_window:
                    net.configure_online_learning(args.online_window, args.stability)
                print(f"成功載入 {src}。")
            except (OSError, ValueError) as exc:
                print(f"載入失敗：{exc}")
            continue



    if args.save:
        try:
            net.save_state(args.save)
            print(f"狀態已保存至 {args.save}。")
        except OSError as exc:
            print(f"離開時保存失敗：{exc}")



# TODO: 若改 LIF + STDP，需維持此 API 以避免破壞上層介面 /
# TODO: Preserve API when migrating to LIF + STDP implementations.

from .network import BioNet  # noqa: E402  # isort: skip
