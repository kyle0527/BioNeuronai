"""Leaky integrate-and-fire neuron implementation."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .base import BaseBioNeuron


class LIFNeuron(BaseBioNeuron):
    """A leaky integrate-and-fire neuron compatible with :class:`BaseBioNeuron`.

    The neuron integrates weighted inputs into a membrane potential with a
    configurable leak factor. Once the potential surpasses the firing threshold
    the neuron emits a unit spike and enters a short refractory period.
    """

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
        leak: float = 0.2,
        refractory_period: int = 1,
        reset_potential: float = 0.0,
        weight_bounds: tuple[float, float] = (0.0, 1.5),
        depression: float = 0.01,
    ) -> None:
        super().__init__(
            num_inputs=num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
        )
        if not 0.0 <= leak < 1.0:
            raise ValueError("leak must be within [0, 1)")
        if refractory_period < 0:
            raise ValueError("refractory_period must be non-negative")

        self.leak = float(leak)
        self.refractory_period = int(refractory_period)
        self.reset_potential = float(reset_potential)
        self.weight_bounds = weight_bounds
        self.depression = float(depression)

        self.membrane_potential = float(self.reset_potential)
        self._refractory_timer = 0

    def forward(self, inputs: Sequence[float]) -> float:
        x = self._prepare_inputs(inputs)

        if self._refractory_timer > 0:
            self._refractory_timer -= 1
            self.membrane_potential = self.reset_potential
            output = 0.0
        else:
            drive = float(np.dot(self.weights, x))
            self.membrane_potential = (
                (1.0 - self.leak) * self.membrane_potential + drive
            )
            if self.membrane_potential >= self.threshold:
                output = 1.0
                self.membrane_potential = self.reset_potential
                if self.refractory_period:
                    self._refractory_timer = self.refractory_period
            else:
                output = max(0.0, self.membrane_potential / max(self.threshold, 1e-6))

        self._update_memory(x, output)
        return output

    def learn(self, inputs: Sequence[float], target: float | None = None) -> None:
        x = self._prepare_inputs(inputs)
        if target is None:
            output = self.output_memory[-1] if self.output_memory else self.forward(inputs)
        else:
            output = float(target)

        if output >= 1.0:
            delta = self.learning_rate * x
            self.weights = np.clip(
                self.weights + delta,
                self.weight_bounds[0],
                self.weight_bounds[1],
            )
        else:
            self.weights = np.clip(
                self.weights * (1.0 - self.depression),
                self.weight_bounds[0],
                self.weight_bounds[1],
            )

    def reset_state(self) -> None:  # type: ignore[override]
        super().reset_state()
        self.membrane_potential = float(self.reset_potential)
        self._refractory_timer = 0


__all__ = ["LIFNeuron"]
