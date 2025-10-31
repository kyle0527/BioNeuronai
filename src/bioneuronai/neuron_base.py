from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Protocol, Sequence, runtime_checkable

import numpy as np


@runtime_checkable
class NeuronProtocol(Protocol):
    """Protocol describing the common neuron API used across the project."""

    num_inputs: int
    threshold: float
    learning_rate: float
    memory_len: int

    def forward(self, inputs: Sequence[float]) -> float:
        """Run a forward pass for the neuron and return the activation."""

    def learn(
        self,
        inputs: Sequence[float],
        target: Optional[float] = None,
        *,
        enhanced: bool = False,
    ) -> None:
        """Update the neuron weights according to the provided signals."""

    def novelty_score(self) -> float:
        """Return a heuristic novelty score for the neuron's recent activity."""


@dataclass
class LearningConfig:
    """Configuration flags shared by neuron implementations."""

    weight_decay: float = 0.0
    adaptive_threshold: bool = False


class NeuronBase(ABC):
    """Base class implementing shared neuron behaviour for BioNeuron variants."""

    weight_clip: tuple[float, float] = (0.0, 1.0)

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        *,
        seed: int | None = None,
        config: LearningConfig | None = None,
        weight_decay: float | None = None,
        adaptive_threshold: bool | None = None,
    ) -> None:
        self.num_inputs = int(num_inputs)
        rng = np.random.default_rng(seed)
        self.weights = rng.uniform(0.1, 0.9, self.num_inputs).astype(np.float32)
        self.threshold = float(threshold)
        self.learning_rate = float(learning_rate)
        self.memory_len = int(memory_len)

        cfg = config or LearningConfig()
        if weight_decay is not None:
            cfg.weight_decay = float(weight_decay)
        if adaptive_threshold is not None:
            cfg.adaptive_threshold = bool(adaptive_threshold)

        self.learning_config = cfg
        self.input_memory: List[np.ndarray] = []
        self.output_memory: List[float] = []

    # ------------------------------------------------------------------
    # Shared helpers
    def _as_array(self, inputs: Sequence[float]) -> np.ndarray:
        if len(inputs) != self.num_inputs:
            raise AssertionError("Input dimension mismatch")
        return np.asarray(inputs, dtype=np.float32)

    def _record_input(self, array: np.ndarray) -> None:
        self.input_memory.append(array)
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

    def _record_output(self, value: float) -> None:
        self.output_memory.append(float(value))
        if len(self.output_memory) > self.memory_len:
            self.output_memory.pop(0)

    def _clip_weights(self) -> None:
        low, high = self.weight_clip
        self.weights = np.clip(self.weights, low, high)

    # ------------------------------------------------------------------
    def forward(self, inputs: Sequence[float]) -> float:
        vector = self._as_array(inputs)
        self._record_input(vector)
        potential = float(np.dot(self.weights, vector))
        output = self._activate(potential, vector)
        self._record_output(output)
        self._after_forward(vector, output)
        return output

    def learn(
        self,
        inputs: Sequence[float],
        target: Optional[float] = None,
        *,
        enhanced: bool = False,
    ) -> None:
        vector = self._as_array(inputs)
        delta = self._compute_weight_update(vector, target, enhanced)
        if delta is None:
            return

        previous = self.weights.copy()
        self.weights = self.weights + delta
        decay = self.learning_config.weight_decay
        if decay:
            self.weights = self.weights - decay * previous

        self._clip_weights()

    # ------------------------------------------------------------------
    def novelty_score(self) -> float:
        if len(self.input_memory) < 2:
            return 0.0
        a, b = self.input_memory[-1], self.input_memory[-2]
        denom = np.maximum(1e-6, np.mean(np.abs(b)))
        score = float(np.clip(np.mean(np.abs(a - b)) / denom, 0.0, 5.0) / 5.0)
        return score

    # ------------------------------------------------------------------
    def _after_forward(self, _: np.ndarray, __: float) -> None:
        if self.learning_config.adaptive_threshold:
            self._adapt_threshold()

    def _adapt_threshold(self) -> None:
        """Hook for adaptive threshold updates."""

    @abstractmethod
    def _activate(self, potential: float, vector: np.ndarray) -> float:
        """Return the neuron output for a potential and input vector."""

    @abstractmethod
    def _compute_weight_update(
        self,
        vector: np.ndarray,
        target: Optional[float],
        enhanced: bool,
    ) -> np.ndarray | None:
        """Return the weight delta for the provided learning signal."""


__all__ = [
    "LearningConfig",
    "NeuronBase",
    "NeuronProtocol",
]

