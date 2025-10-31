from __future__ import annotations
from typing import List, Sequence, Tuple
import numpy as np


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

        # short-term memory / 短期記憶佇列
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
    def __init__(self, n_neurons: int, input_dim: int) -> None:
        self.neurons = [BioNeuron(input_dim) for _ in range(n_neurons)]

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [n.forward(inputs) for n in self.neurons]

    def learn(self, inputs: Sequence[float], outputs: Sequence[float]) -> None:
        for n, out in zip(self.neurons, outputs):
            n.hebbian_learn(inputs, out)


class BioNet:
    """Two-layer demo network (2 → 3 → 3) returning ``(l2_out, l1_out)``.

    雙層範例網路，回傳二層與一層的輸出結果。
    """
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
    """Interactive bilingual CLI for probing the demo network.

    提供 `[ZH]/[EN]` 雙語互動介面以體驗範例網路。
    """

    net = BioNet()
    print("== BioNeuron CLI [ZH/EN] ==")
    while True:
        s = input("[ZH] 請輸入兩個數字 (a b) 或 q 離開 / [EN] Enter two numbers or q to quit: ")
        if s.lower() == "q":
            break
        try:
            a, b = map(float, s.strip().split())
        except ValueError:
            print("[ZH] 格式錯誤，請再輸入 / [EN] Invalid format, please retry.")
            continue
        outputs, _ = net.forward([a, b])
        novelty = net.layer1.neurons[0].novelty_score()
        print(
            f"[ZH] 輸出：{outputs}｜新穎性={novelty:.3f} / "
            f"[EN] Output: {outputs} | Novelty={novelty:.3f}"
        )
        net.learn([a, b])


# TODO: 若改 LIF + STDP，需維持此 API 以避免破壞上層介面 /
# TODO: Preserve API when migrating to LIF + STDP implementations.
