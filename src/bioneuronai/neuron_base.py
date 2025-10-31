"""Shared neuron abstractions for the public BioNeuronAI API."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence


class BaseNeuron(ABC):
    """Common interface implemented by all BioNeuronAI neuron variants."""

    num_inputs: int

    @abstractmethod
    def forward(self, inputs: Sequence[float]) -> float:
        """Run a single inference step and return the neuron activation."""

    @abstractmethod
    def learn(self, inputs: Sequence[float], target: float | None = None) -> float:
        """Update the neuron's internal state and return the activation used."""

    def novelty_score(self) -> float:
        """Optional novelty signal; defaults to zero for neurons without support."""

        return 0.0


class SupportsBatchLearning(ABC):
    """Optional mixin for neurons that can learn from batched samples."""

    @abstractmethod
    def learn_batch(
        self,
        batch: Iterable[Sequence[float]],
        targets: Iterable[float] | None = None,
    ) -> Iterable[float]:
        """Update the neuron with a batch of samples and return activations."""

