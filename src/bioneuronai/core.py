from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any, List, Sequence, Tuple

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
        online_window: int | None = None,
        stability_coefficient: float = 0.05,
    ) -> None:
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
        self.input_memory.append(x)
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

        potential = float(np.dot(self.weights, x))
        return min(1.0, potential) if potential >= self.threshold else 0.0

    def hebbian_learn(self, inputs: Sequence[float], output: float) -> None:
        x = np.asarray(inputs, dtype=np.float32)
        delta = self.learning_rate * x * float(output)
        self.weights = np.clip(self.weights + delta, 0.0, 1.0)
        if self.online_window:
            self._apply_online_regularization()

    def novelty_score(self) -> float:
        """Simple novelty proxy: mean abs diff of last two inputs (0~1 scaled)."""
        if len(self.input_memory) < 2:
            return 0.0
        a, b = self.input_memory[-1], self.input_memory[-2]
        denom = np.maximum(1e-6, np.mean(np.abs(b)))
        score = float(np.clip(np.mean(np.abs(a - b)) / denom, 0.0, 5.0) / 5.0)
        return score

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


class BioLayer:
    def __init__(self, n_neurons: int, input_dim: int) -> None:
        self.neurons = [BioNeuron(input_dim) for _ in range(n_neurons)]

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [n.forward(inputs) for n in self.neurons]

    def learn(self, inputs: Sequence[float], outputs: Sequence[float]) -> None:
        for n, out in zip(self.neurons, outputs):
            n.hebbian_learn(inputs, out)

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

        try:
            a, b = map(float, s.split())
        except ValueError:
            print("格式錯誤，請再輸入")
            continue

        outputs, _ = net.forward([a, b])
        novelty = net.layer1.neurons[0].novelty_score()
        print(f"輸出：{[round(o, 3) for o in outputs]} | novelty={novelty:.3f}")
        net.learn([a, b])


    if args.save:
        try:
            net.save_state(args.save)
            print(f"狀態已保存至 {args.save}。")
        except OSError as exc:
            print(f"離開時保存失敗：{exc}")


# TODO: 之後若改 LIF + STDP，保留此 API，不破壞上層介面.
