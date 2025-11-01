"""Anti-Hebbian neuron implementation."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .base import BaseBioNeuron


class AntiHebbNeuron(BaseBioNeuron):
    """Neuron that reduces weights on correlated activations."""

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.5,
        learning_rate: float = 0.02,
        memory_len: int = 5,
        seed: int | None = None,
        sensitivity: float = 3.0,
        inhibition_scale: float = 0.3,
        weight_bounds: tuple[float, float] = (0.0, 1.0),
    ) -> None:
        super().__init__(
            num_inputs=num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
        )
        self.sensitivity = float(sensitivity)
        self.inhibition_scale = float(inhibition_scale)
        self.weight_bounds = weight_bounds

    def forward(self, inputs: Sequence[float]) -> float:
        x = self._prepare_inputs(inputs)
        potential = float(np.dot(self.weights, x))
        centred = potential - self.threshold
        # Smooth inhibitory activation using a logistic curve.
        output = float(1.0 / (1.0 + np.exp(-self.sensitivity * centred)))
        self._update_memory(x, output)
        return output

    def learn(self, inputs: Sequence[float], target: float | None = None) -> None:
        x = self._prepare_inputs(inputs)
        output = (
            self.output_memory[-1]
            if target is None and self.output_memory
            else float(target) if target is not None else self.forward(inputs)
        )

        depression = self.learning_rate * x * output
        decorrelation = self.inhibition_scale * self.learning_rate * x * (1.0 - output)
        self.weights = np.clip(
            self.weights - depression + decorrelation,
            self.weight_bounds[0],
            self.weight_bounds[1],
        )

    def novelty_score(self) -> float:  # type: ignore[override]
        if not self.input_memory:
            return 0.0
        weight_var = float(np.var(self.weights))
        base = super().novelty_score()
        return float(np.clip(0.5 * base + 0.5 * min(1.0, weight_var), 0.0, 1.0))


__all__ = ["AntiHebbNeuron"]
