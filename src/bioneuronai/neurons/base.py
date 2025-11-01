"""Base primitives for BioNeuronAI neuron implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

import numpy as np


class BaseBioNeuron(ABC):
    """Common interface for all BioNeuron variants.

    The base class stores shared hyper-parameters, handles short-term memory
    bookkeeping and implements a default novelty score that measures the
    difference between the two most recent inputs. Concrete subclasses only
    need to implement :meth:`forward` and :meth:`learn`.
    """

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        if num_inputs <= 0:
            raise ValueError("num_inputs must be positive")

        self.num_inputs = int(num_inputs)
        self.threshold = float(threshold)
        self.learning_rate = float(learning_rate)
        self.memory_len = int(memory_len)
        self._rng = np.random.default_rng(seed)

        self.weights = self._init_weights().astype(np.float32)
        self.input_memory: List[np.ndarray] = []
        self.output_memory: List[float] = []

    def _init_weights(self) -> np.ndarray:
        """Return the initial weight vector.

        Sub-classes can override this for custom initialisation strategies.
        """

        return self._rng.uniform(0.1, 0.9, self.num_inputs)

    def _prepare_inputs(self, inputs: Sequence[float]) -> np.ndarray:
        if len(inputs) != self.num_inputs:
            raise ValueError(
                f"Expected {self.num_inputs} inputs, received {len(inputs)}"
            )
        return np.asarray(inputs, dtype=np.float32)

    def _update_memory(self, inputs: np.ndarray, output: float) -> None:
        self.input_memory.append(inputs)
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

        self.output_memory.append(float(output))
        if len(self.output_memory) > self.memory_len:
            self.output_memory.pop(0)

    def novelty_score(self) -> float:
        """Default novelty score: mean absolute change between the last inputs."""

        if len(self.input_memory) < 2:
            return 0.0
        a, b = self.input_memory[-1], self.input_memory[-2]
        denom = np.maximum(1e-6, np.mean(np.abs(b)))
        score = float(np.clip(np.mean(np.abs(a - b)) / denom, 0.0, 5.0) / 5.0)
        return score

    def reset_state(self) -> None:
        """Clears the rolling memories kept for novelty computation."""

        self.input_memory.clear()
        self.output_memory.clear()

    @abstractmethod
    def forward(self, inputs: Sequence[float]) -> float:
        """Run a forward pass and return the activation/spike value."""

    @abstractmethod
    def learn(self, inputs: Sequence[float], target: float | None = None) -> None:
        """Apply the neuron-specific learning rule."""


__all__ = ["BaseBioNeuron"]
