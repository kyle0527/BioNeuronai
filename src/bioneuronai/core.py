from __future__ import annotations

from typing import List, Sequence, Tuple, Type

import numpy as np

from .neurons.base import BaseBioNeuron


class BioNeuron(BaseBioNeuron):
    """Bio-inspired neuron with short-term memory and Hebbian update."""

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        super().__init__(
            num_inputs=num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
        )

    def forward(self, inputs: Sequence[float]) -> float:
        x = self._prepare_inputs(inputs)
        potential = float(np.dot(self.weights, x))
        output = min(1.0, potential) if potential >= self.threshold else 0.0
        self._update_memory(x, output)
        return output

    def learn(self, inputs: Sequence[float], target: float | None = None) -> None:
        x = self._prepare_inputs(inputs)
        output = (
            self.output_memory[-1]
            if target is None and self.output_memory
            else float(target) if target is not None else self.forward(inputs)
        )
        delta = self.learning_rate * x * float(output)
        self.weights = np.clip(self.weights + delta, 0.0, 1.0)

    def hebbian_learn(self, inputs: Sequence[float], output: float) -> None:
        self.learn(inputs, output)


class BioLayer:
    """A collection of :class:`BaseBioNeuron` sharing the same input size."""

    def __init__(
        self,
        n_neurons: int,
        input_dim: int,
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

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [n.forward(inputs) for n in self.neurons]

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
        self.layer2.learn(l1_out, [target] * len(self.layer2.neurons))
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
        print(
            f"輸出：{outputs} | novelty={net.layer1.neurons[0].novelty_score():.3f}"
        )
        net.learn([a, b])


# TODO: 之後若改 LIF + STDP，保留此 API，不破壞上層介面.
