from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional, Protocol, Sequence
"""Base primitives for BioNeuronAI neuron implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

import numpy as np


Array = np.ndarray


class LearningStrategy(Protocol):
    """Strategy interface for updating neuron weights."""

    def update(
        self,
        neuron: "BaseNeuron",
        inputs: Array,
        outputs: Array,
        targets: Optional[Array] = None,
    ) -> None:
        ...


class ThresholdStrategy(Protocol):
    """Strategy interface for adapting neuron thresholds."""

    def adjust(
        self,
        neuron: "BaseNeuron",
        inputs: Array,
        potentials: Array,
        outputs: Array,
    ) -> None:
        ...

    def reset(self, neuron: "BaseNeuron") -> None:
        ...


@dataclass
class NoOpThresholdStrategy:
    """A threshold strategy that performs no adaptation."""

    def adjust(
        self,
        neuron: "BaseNeuron",
        inputs: Array,
        potentials: Array,
        outputs: Array,
    ) -> None:
        return

    def reset(self, neuron: "BaseNeuron") -> None:
        return


@dataclass
class HebbianLearningStrategy:
    """Classic Hebbian learning with optional clipping."""

    learning_rate: float
    min_weight: float = 0.0
    max_weight: float = 1.0

    def update(
        self,
        neuron: "BaseNeuron",
        inputs: Array,
        outputs: Array,
        targets: Optional[Array] = None,
    ) -> None:
        _ = targets  # Unused in the vanilla Hebbian rule
        # Equivalent to processing each sample sequentially but vectorised.
        delta = inputs * outputs[:, None]
        weight_update = self.learning_rate * delta.mean(axis=0)
        neuron.weights = np.clip(
            neuron.weights + weight_update,
            self.min_weight,
            self.max_weight,
        )


@dataclass
class AdaptiveThresholdStrategy:
    """Adjust the neuron's firing threshold based on recent activations."""

    target_activation: float = 0.3
    tolerance: float = 0.1
    increase_factor: float = 1.05
    decrease_factor: float = 0.95
    min_threshold: float = 0.1
    max_threshold: float = 2.0
    window: int = 5

    def adjust(
        self,
        neuron: "BaseNeuron",
        inputs: Array,
        potentials: Array,
        outputs: Array,
    ) -> None:
        if len(neuron.output_memory) < self.window:
            return
        recent = np.array(neuron.output_memory)[-self.window :]
        recent_avg = float(np.mean(recent))

        if recent_avg > self.target_activation + self.tolerance:
            neuron.threshold = min(
                self.max_threshold,
                neuron.threshold * self.increase_factor,
            )
        elif recent_avg < self.target_activation - self.tolerance:
            neuron.threshold = max(
                self.min_threshold,
                neuron.threshold * self.decrease_factor,
            )

        if hasattr(neuron, "threshold_history"):
            neuron.threshold_history.append(neuron.threshold)

    def reset(self, neuron: "BaseNeuron") -> None:
        if hasattr(neuron, "threshold_history"):
            neuron.threshold_history.clear()


@dataclass
class WeightDecayHebbianStrategy:
    """Hebbian learning that supports supervision and weight decay."""

    learning_rate: float
    weight_decay: float = 0.0
    min_weight: float = 0.0
    max_weight: float = 2.0

    def update(
        self,
        neuron: "BaseNeuron",
        inputs: Array,
        outputs: Array,
        targets: Optional[Array] = None,
    ) -> None:
        if targets is not None:
            error = targets - outputs
            delta = error[:, None] * (targets[:, None] + 0.1) * inputs
        else:
            delta = inputs * outputs[:, None]

        weight_update = self.learning_rate * delta.mean(axis=0)
        neuron.weights = np.clip(
            neuron.weights + weight_update - self.weight_decay * neuron.weights,
            self.min_weight,
            self.max_weight,
        )


class BaseNeuron:
    """Base class for bio-inspired neurons with pluggable strategies."""
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
        seed: Optional[int] = None,
        *,
        learning_strategy: Optional[LearningStrategy] = None,
        threshold_strategy: Optional[ThresholdStrategy] = None,
    ) -> None:
        self.num_inputs = int(num_inputs)
        rng = np.random.default_rng(seed)
        self.weights = rng.uniform(0.1, 0.9, self.num_inputs).astype(np.float32)
        self._learning_rate = float(learning_rate)
        self.initial_threshold = float(threshold)
        self.threshold = float(threshold)
        self.memory_len = int(memory_len)
        self.input_memory: Deque[np.ndarray] = deque(maxlen=self.memory_len)
        self.output_memory: Deque[float] = deque(maxlen=self.memory_len)
        self.learning_strategy = learning_strategy or HebbianLearningStrategy(
            self._learning_rate
        )
        self.threshold_strategy = threshold_strategy or NoOpThresholdStrategy()
        self._sync_learning_rate()

    # ------------------------------------------------------------------
    # Forward APIs
    # ------------------------------------------------------------------
    def forward(self, inputs: Array | Sequence[float]) -> float:
        batch_inputs = np.asarray(inputs, dtype=np.float32).reshape(1, -1)
        return float(self.forward_batch(batch_inputs)[0])

    def forward_batch(self, inputs: Array) -> Array:
        arr = np.asarray(inputs, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[1] != self.num_inputs:
            raise ValueError(
                f"inputs must have shape (batch, {self.num_inputs}); got {arr.shape}"
            )

        self._update_input_memory(arr)
        potentials = arr @ self.weights
        outputs = self.activation(potentials)
        self._update_output_memory(outputs)
        self.threshold_strategy.adjust(self, arr, potentials, outputs)
        self._post_forward(arr, potentials, outputs)
        return outputs

    # ------------------------------------------------------------------
    # Learning APIs
    # ------------------------------------------------------------------
    def learn(
        self,
        inputs: Array | Sequence[float],
        output: Optional[float] = None,
        *,
        target: Optional[float] = None,
    ) -> None:
        batch_inputs = np.asarray(inputs, dtype=np.float32).reshape(1, -1)
        outputs = None if output is None else np.asarray([output], dtype=np.float32)
        targets = None if target is None else np.asarray([target], dtype=np.float32)
        self.learn_batch(batch_inputs, outputs=outputs, targets=targets)

    def learn_batch(
        self,
        inputs: Array,
        *,
        outputs: Optional[Array] = None,
        targets: Optional[Array] = None,
    ) -> None:
        arr = np.asarray(inputs, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[1] != self.num_inputs:
            raise ValueError(
                f"inputs must have shape (batch, {self.num_inputs}); got {arr.shape}"
            )

        if outputs is None:
            outputs = self.forward_batch(arr)
        else:
            outputs = np.asarray(outputs, dtype=np.float32).reshape(-1)
        if targets is not None:
            targets = np.asarray(targets, dtype=np.float32).reshape(-1)

        if outputs.shape[0] != arr.shape[0]:
            raise ValueError("outputs batch size must match inputs")
        if targets is not None and targets.shape[0] != arr.shape[0]:
            raise ValueError("targets batch size must match inputs")

        self.learning_strategy.update(self, arr, outputs, targets)

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------
    def novelty(self) -> float:
        if len(self.input_memory) < 2:
            return 0.0
        a = self.input_memory[-1]
        b = self.input_memory[-2]
        denom = np.maximum(1e-6, np.mean(np.abs(b)))
        score = np.clip(np.mean(np.abs(a - b)) / denom, 0.0, 5.0) / 5.0
        return float(score)

    # Backwards compatibility alias
    novelty_score = novelty

    def reset(self) -> None:
        self.input_memory.clear()
        self.output_memory.clear()
        self.threshold = self.initial_threshold
        self.threshold_strategy.reset(self)

    @property
    def learning_rate(self) -> float:
        return self._learning_rate

    @learning_rate.setter
    def learning_rate(self, value: float) -> None:
        self._learning_rate = float(value)
        self._sync_learning_rate()

    # ------------------------------------------------------------------
    # Hooks for subclasses
    # ------------------------------------------------------------------
    def activation(self, potentials: Array) -> Array:
        threshold = float(self.threshold)
        outputs = np.where(
            potentials >= threshold,
            np.minimum(1.0, potentials),
            np.zeros_like(potentials),
        )
        return outputs.astype(np.float32)

    def _post_forward(
        self, inputs: Array, potentials: Array, outputs: Array
    ) -> None:
        return

    def _update_input_memory(self, inputs: Array) -> None:
        for row in inputs:
            self.input_memory.append(np.asarray(row, dtype=np.float32))

    def _update_output_memory(self, outputs: Array) -> None:
        for value in outputs:
            self.output_memory.append(float(value))

    def _sync_learning_rate(self) -> None:
        if hasattr(self, "learning_strategy") and hasattr(
            self.learning_strategy, "learning_rate"
        ):
            self.learning_strategy.learning_rate = self._learning_rate


__all__ = [
    "Array",
    "LearningStrategy",
    "ThresholdStrategy",
    "NoOpThresholdStrategy",
    "HebbianLearningStrategy",
    "AdaptiveThresholdStrategy",
    "WeightDecayHebbianStrategy",
    "BaseNeuron",
]

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
