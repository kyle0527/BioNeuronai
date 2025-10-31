from __future__ import annotations
from typing import List, Sequence, Tuple

import numpy as np

from .neuron_base import LearningConfig, NeuronBase, NeuronProtocol


class BioNeuron(NeuronBase):
    """Bio-inspired neuron with short-term input memory and Hebbian update."""

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        *,
        seed: int | None = None,
        weight_decay: float = 0.0,
        adaptive_threshold: bool = False,
    ) -> None:
        super().__init__(
            num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
            config=LearningConfig(
                weight_decay=weight_decay,
                adaptive_threshold=adaptive_threshold,
            ),
        )

    def _activate(self, potential: float, _: np.ndarray) -> float:
        return min(1.0, potential) if potential >= self.threshold else 0.0

    def _compute_weight_update(
        self,
        vector: np.ndarray,
        target: float | None,
        enhanced: bool,
    ) -> np.ndarray:
        output = 0.0 if target is None else float(target)
        return self.learning_rate * vector * output


class BioLayer:
    def __init__(
        self,
        n_neurons: int,
        input_dim: int,
        *,
        neuron_cls: type[NeuronBase] = BioNeuron,
        neuron_kwargs: dict | None = None,
    ) -> None:
        params = neuron_kwargs or {}
        self.neurons: List[NeuronProtocol] = [
            neuron_cls(input_dim, **params) for _ in range(n_neurons)
        ]

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [n.forward(inputs) for n in self.neurons]

    def learn(
        self,
        inputs: Sequence[float],
        outputs: Sequence[float],
        *,
        enhanced: bool = False,
        targets: Sequence[float] | None = None,
    ) -> None:
        for idx, neuron in enumerate(self.neurons):
            signal = outputs[idx]
            if targets is not None:
                signal = targets[idx]
            neuron.learn(inputs, signal, enhanced=enhanced)


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
        self.layer2.learn(l1_out, l2_out, targets=[target] * len(l2_out))
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
