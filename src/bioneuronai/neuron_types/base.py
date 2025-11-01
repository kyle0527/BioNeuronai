"""Base abstractions for spiking neuron implementations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class NeuronState:
    """Container tracking the dynamic state of a spiking neuron."""

    membrane_potential: float
    refractory_time_remaining: float = 0.0
    spike: bool = False
    last_spike_time: float | None = None


class BaseSpikingNeuron(ABC):
    """Common interface shared by all neuron type implementations.

    Sub-classes implement :meth:`_integrate` to update the membrane potential
    dynamics based on the provided input current.
    """

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 1.0,
        rest_potential: float = 0.0,
        reset_potential: float | None = None,
        membrane_time_constant: float = 20.0,
        membrane_resistance: float = 1.0,
        refractory_period: float = 2.0,
        seed: int | None = None,
    ) -> None:
        if num_inputs <= 0:
            raise ValueError("num_inputs must be positive")
        if membrane_time_constant <= 0:
            raise ValueError("membrane_time_constant must be positive")
        if refractory_period < 0:
            raise ValueError("refractory_period cannot be negative")

        self.num_inputs = int(num_inputs)
        self.threshold = float(threshold)
        self.rest_potential = float(rest_potential)
        self.reset_potential = (
            float(reset_potential) if reset_potential is not None else self.rest_potential
        )
        self.membrane_time_constant = float(membrane_time_constant)
        self.membrane_resistance = float(membrane_resistance)
        self.refractory_period = float(refractory_period)
        self._rng = np.random.default_rng(seed)
        self.weights = self._rng.normal(0.0, 1.0, size=self.num_inputs).astype(np.float32)
        self.state = NeuronState(membrane_potential=self.rest_potential)
        self.time: float = 0.0

    def reset_state(self) -> None:
        """Reset the neuron to its resting state."""

        self.state = NeuronState(membrane_potential=self.rest_potential)
        self.time = 0.0

    def step(self, inputs: Sequence[float], dt: float = 1.0) -> bool:
        """Advance the neuron dynamics by ``dt`` and return spike state."""

        if len(inputs) != self.num_inputs:
            raise ValueError("inputs length mismatch")
        if dt <= 0:
            raise ValueError("dt must be positive")

        self.time += dt

        # handle refractory period
        if self.state.refractory_time_remaining > 0:
            self.state.refractory_time_remaining = max(
                0.0, self.state.refractory_time_remaining - dt
            )
            self.state.spike = False
            return False

        input_currents = np.asarray(inputs, dtype=np.float32)
        self.state.membrane_potential = self._integrate(
            self.state.membrane_potential, input_currents, dt
        )

        if self.state.membrane_potential >= self.threshold:
            self.state.spike = True
            self.state.last_spike_time = self.time
            self.state.membrane_potential = self.reset_potential
            self.state.refractory_time_remaining = self.refractory_period
        else:
            self.state.spike = False

        return self.state.spike

    @abstractmethod
    def _integrate(
        self, membrane_potential: float, inputs: np.ndarray, dt: float
    ) -> float:
        """Update the membrane potential given the input signal."""

    def effective_input(self, inputs: Sequence[float]) -> float:
        """Compute the weighted input current for the neuron."""

        return float(np.dot(self.weights, np.asarray(inputs, dtype=np.float32)))
