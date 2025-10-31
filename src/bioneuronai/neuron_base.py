"""Base abstractions for BioNeuron variants."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

import numpy as np


class BaseBioNeuron(ABC):
    """Abstract base class describing the BioNeuron interface.

    This class encapsulates common attributes such as weight initialization,
    short-term memory buffers, and accounting statistics that are shared across
    different neuron implementations. Sub-classes are expected to implement the
    concrete ``forward``/``hebbian_learn``/``novelty_score`` behaviours.
    """

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        self.num_inputs = int(num_inputs)
        self.threshold = float(threshold)
        self.learning_rate = float(learning_rate)
        self.memory_len = int(memory_len)

        self._rng = np.random.default_rng(seed)
        self.weights = self._init_weights(self.num_inputs)

        self.input_memory: List[np.ndarray] = []
        self.activation_count = 0
        self.total_inputs = 0

    # ------------------------------------------------------------------
    # Common helpers
    def _init_weights(self, num_inputs: int) -> np.ndarray:
        """Initialise weights using a uniform distribution."""

        return self._rng.uniform(0.1, 0.9, num_inputs).astype(np.float32)

    def _remember_input(self, x: np.ndarray) -> None:
        """Append an input vector to the short-term memory buffer."""

        self.input_memory.append(x)
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

    def _clip_weights(self, *, min_value: float, max_value: float) -> None:
        """In-place clip of the weight vector to the provided bounds."""

        self.weights = np.clip(self.weights, min_value, max_value)

    def _record_activation(self, activated: bool) -> None:
        """Update activation statistics shared by subclasses."""

        if activated:
            self.activation_count += 1
        self.total_inputs += 1

    # ------------------------------------------------------------------
    # Interface definition
    @abstractmethod
    def forward(self, inputs: Sequence[float]) -> float:
        """Compute the neuron response for the provided inputs."""

    @abstractmethod
    def hebbian_learn(
        self,
        inputs: Sequence[float],
        output: float | None = None,
        **kwargs,
    ) -> None:
        """Update the neuron parameters following a Hebbian-style rule."""

    @abstractmethod
    def novelty_score(self) -> float:
        """Return a normalised novelty estimate."""


__all__ = ["BaseBioNeuron"]

