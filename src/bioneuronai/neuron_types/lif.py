"""Leaky integrate-and-fire neuron implementation."""
from __future__ import annotations

from typing import Sequence

import numpy as np

from .base import BaseSpikingNeuron


class LIFNeuron(BaseSpikingNeuron):
    """Classic leaky integrate-and-fire neuron with configurable dynamics."""

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 1.0,
        rest_potential: float = 0.0,
        reset_potential: float | None = None,
        membrane_time_constant: float = 20.0,
        membrane_resistance: float = 1.0,
        refractory_period: float = 2.0,
        input_scale: float = 1.0,
        seed: int | None = None,
    ) -> None:
        super().__init__(
            num_inputs=num_inputs,
            threshold=threshold,
            rest_potential=rest_potential,
            reset_potential=reset_potential,
            membrane_time_constant=membrane_time_constant,
            membrane_resistance=membrane_resistance,
            refractory_period=refractory_period,
            seed=seed,
        )
        self.input_scale = float(input_scale)

    def _integrate(
        self, membrane_potential: float, inputs: np.ndarray, dt: float
    ) -> float:
        weighted_input = self.input_scale * float(np.dot(self.weights, inputs))
        dv = (
            -(membrane_potential - self.rest_potential)
            + self.membrane_resistance * weighted_input
        )
        dv *= dt / self.membrane_time_constant
        return float(membrane_potential + dv)

    def drive(self, inputs: Sequence[float], dt: float = 1.0) -> bool:
        """Alias of :meth:`step` emphasising continuous drive semantics."""

        return self.step(inputs, dt=dt)
