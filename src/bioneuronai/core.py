from __future__ import annotations
from typing import List, Sequence, Type
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
    """Simple homogeneous layer used by legacy demos/tests."""

    def __init__(
        self,
        n_neurons: int,
        input_dim: int,
        *,
        neuron_type: Type[BioNeuron] | None = None,
        neuron_kwargs: dict | None = None,
    ) -> None:
        if n_neurons < 1:
            raise ValueError("BioLayer requires at least one neuron")
        neuron_cls: Type[BioNeuron] = neuron_type or BioNeuron
        params = dict(neuron_kwargs or {})
        self.neurons = [neuron_cls(input_dim, **params) for _ in range(n_neurons)]
        self.input_dim = input_dim

    def forward(self, inputs: Sequence[float]) -> List[float]:
        if len(inputs) != self.input_dim:
            raise ValueError(f"Expected {self.input_dim} inputs, got {len(inputs)}")
        return [float(n.forward(inputs)) for n in self.neurons]

    def learn(self, inputs: Sequence[float], outputs: Sequence[float]) -> None:
        if len(outputs) != len(self.neurons):
            raise ValueError("Outputs length must match number of neurons")
        for neuron, out in zip(self.neurons, outputs):
            if hasattr(neuron, "hebbian_learn"):
                neuron.hebbian_learn(inputs, out)
            elif hasattr(neuron, "improved_hebbian_learn"):
                neuron.improved_hebbian_learn(inputs, target=out)
            else:
                raise AttributeError(
                    f"Neuron {neuron!r} does not implement a supported learning rule"
                )


def cli_loop(argv: Sequence[str] | None = None) -> None:
    import argparse
    from pathlib import Path

    from .network import BioNet, BioNetConfig, LayerConfig, load_config

    parser = argparse.ArgumentParser(description="BioNeuronAI 互動式測試工具")
    parser.add_argument("--config", type=str, help="JSON 或 YAML 組態檔路徑")
    parser.add_argument(
        "--layer",
        action="append",
        dest="layers",
        help="手動定義層級，如 'BioNeuron:3' 或 'BioNeuron:2;ImprovedBioNeuron:1,adaptive_threshold=true'",
    )
    parser.add_argument("--input-dim", type=int, default=2, help="輸入維度 (未提供組態檔時使用)")
    parser.add_argument("--no-learn", action="store_true", help="僅前向傳播不更新權重")
    args = parser.parse_args(argv)

    if args.config:
        config = load_config(Path(args.config))
    else:
        layer_specs = args.layers or []
        if not layer_specs:
            print("未提供層級設定，使用預設 2 層 3-3 BioNeuron 網路")
            layer_specs = ["BioNeuron:3", "BioNeuron:3"]
        layers = [LayerConfig.from_cli(spec) for spec in layer_specs]
        config = BioNetConfig(input_dim=args.input_dim, layers=layers)

    net = BioNet(config)
    print("== BioNeuron CLI ==")
    print(net.summary())
    print("輸入 q 離開，或輸入以空白分隔的數字進行推論。")

    while True:
        try:
            raw = input(f"請輸入 {config.input_dim} 個數字：")
        except EOFError:
            break
        if raw.strip().lower() == "q":
            break
        try:
            values = [float(x) for x in raw.strip().split()]
        except ValueError:
            print("格式錯誤，請再輸入")
            continue
        if len(values) != config.input_dim:
            print(f"需要 {config.input_dim} 個數值，實際取得 {len(values)} 個")
            continue

        activations = net.forward(values)
        final_outputs = activations[-1]
        print(f"輸出：{[round(v, 4) for v in final_outputs]}")

        for idx, (layer, layer_outputs) in enumerate(zip(net.layers, activations), start=1):
            novelty_scores: List[float] = []
            for neuron in layer:
                if hasattr(neuron, "novelty_score"):
                    novelty_scores.append(float(neuron.novelty_score()))
                elif hasattr(neuron, "enhanced_novelty_score"):
                    novelty_scores.append(float(neuron.enhanced_novelty_score()))
            if novelty_scores:
                formatted = ", ".join(f"{score:.3f}" for score in novelty_scores)
                print(f"  第 {idx} 層新穎性：[{formatted}]")
            else:
                print(f"  第 {idx} 層輸出：{[round(v, 4) for v in layer_outputs]}")

        if args.no_learn:
            continue

        net.learn(values, activations)
        print("權重已更新。")


from .network import BioNet  # noqa: E402  # isort: skip
