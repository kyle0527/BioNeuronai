from __future__ import annotations
from typing import List, Sequence, Tuple
import warnings

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

    def hebbian_learn(self, inputs: Sequence[float], output: float) -> None:
        x = np.asarray(inputs, dtype=np.float32)
        delta = self.learning_rate * x * float(output)
        np.add(self.weights, delta, out=self.weights, casting="unsafe")
        np.clip(self.weights, 0.0, 1.0, out=self.weights)

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

        x = np.asarray(inputs, dtype=np.float32)
        if x.ndim != 1 or x.shape[0] != self._weight_matrix.shape[1]:
            raise ValueError("輸入維度與層設定不符")

        potentials = self._weight_matrix @ x
        outputs: list[float] = []
        for idx, neuron in enumerate(self.neurons):
            outputs.append(neuron._finalize_potential(x, float(potentials[idx])))
        return outputs

    def learn(
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
