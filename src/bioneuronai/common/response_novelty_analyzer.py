"""Utilities to estimate response novelty using BioNeuron variants."""

from __future__ import annotations

from collections import deque
from typing import Iterable, Sequence

import numpy as np

from ..core import BioNeuron
from ..improved_core import ImprovedBioNeuron


class ResponseNoveltyAnalyzer:
    """Blend BioNeuron/BioNeuronV2 style novelty estimates for responses.

    The analyzer keeps a rolling baseline window of recent "known good" feature
    vectors and uses both :class:`BioNeuron` and :class:`ImprovedBioNeuron` to
    provide a smooth novelty score in ``[0, 1]``.  The original BioNeuron reacts
    quickly to sudden jumps while the improved neuron captures medium-term
    trends via its enhanced novelty calculation.
    """

    def __init__(
        self,
        input_dim: int,
        *,
        baseline_window: int = 50,
        primary_weight: float = 0.45,
        secondary_weight: float = 0.35,
        baseline_weight: float = 0.20,
        seed: int | None = None,
    ) -> None:
        if input_dim <= 0:
            raise ValueError("input_dim must be > 0")

        self.input_dim = int(input_dim)
        self.primary_weight = float(primary_weight)
        self.secondary_weight = float(secondary_weight)
        self.baseline_weight = float(baseline_weight)
        total = self.primary_weight + self.secondary_weight + self.baseline_weight
        if total <= 0:
            raise ValueError("at least one novelty weight must be positive")

        self._normalisation = None
        self._baseline_vectors: deque[np.ndarray] = deque(maxlen=int(baseline_window))

        # Neuron instances are initialised with different seeds to diversify
        # their internal dynamics.
        self._primary = BioNeuron(
            num_inputs=self.input_dim,
            memory_len=max(5, int(baseline_window // 5)),
            seed=None if seed is None else seed + 1,
        )
        self._secondary = ImprovedBioNeuron(
            num_inputs=self.input_dim,
            memory_len=max(5, int(baseline_window // 4)),
            adaptive_threshold=True,
            seed=None if seed is None else seed + 991,
        )

    # ------------------------------------------------------------------
    # Baseline management helpers
    # ------------------------------------------------------------------
    def observe_baseline(self, features: Sequence[float]) -> None:
        """Register a baseline ("normal") response feature vector."""

        vector = self._prepare(features)
        self._baseline_vectors.append(vector)
        self._update_normalisation()

        # Drive both neurons with the baseline vector so that their internal
        # memories capture the typical patterns.
        self._primary.forward(vector)
        self._secondary.forward(vector)
        self._primary.hebbian_learn(vector, output=1.0)
        self._secondary.improved_hebbian_learn(vector, target=1.0)

    def learn_from_feedback(self, features: Sequence[float], is_anomaly: bool) -> None:
        """Adjust the baseline depending on analyst feedback.

        When a prediction is deemed false-positive the vector is reinforced as a
        baseline sample.  Confirmed anomalies simply update the neuron memory
        without Hebbian reinforcement so the model remains sensitive.
        """

        vector = self._prepare(features)
        if not is_anomaly:
            self.observe_baseline(vector)
            return

        # For anomalies we only update the forward pass memories so the neurons
        # know about the new behaviour but keep their learned baseline.
        self._primary.forward(vector)
        self._secondary.forward(vector)

    # ------------------------------------------------------------------
    # Novelty scoring
    # ------------------------------------------------------------------
    def score(self, features: Sequence[float]) -> float:
        """Return a novelty score in ``[0, 1]`` for the supplied features."""

        vector = self._prepare(features)

        # Ensure both neurons observe the vector before retrieving their novelty
        # measurements.  The secondary neuron exposes ``enhanced_novelty_score``
        # for richer dynamics.
        self._primary.forward(vector)
        self._secondary.forward(vector)

        primary_score = float(self._primary.novelty_score())
        secondary_score = float(self._secondary.enhanced_novelty_score())
        baseline_score = float(self._baseline_deviation(vector))

        weighted = (
            self.primary_weight * primary_score
            + self.secondary_weight * secondary_score
            + self.baseline_weight * baseline_score
        )
        total_weight = self.primary_weight + self.secondary_weight + self.baseline_weight
        novelty = float(np.clip(weighted / total_weight, 0.0, 1.0))
        return novelty

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare(self, features: Sequence[float]) -> np.ndarray:
        if not isinstance(features, Iterable):
            raise TypeError("features must be a sequence of floats")

        vector = np.asarray(list(features), dtype=np.float32)
        if vector.size != self.input_dim:
            raise ValueError(
                f"Expected feature vector of length {self.input_dim}, got {vector.size}"
            )

        if self._normalisation is None:
            # Lazily initialise scaling to avoid division by zero.
            self._normalisation = np.maximum(1e-6, np.abs(vector))

        return vector / self._normalisation

    def _update_normalisation(self) -> None:
        if not self._baseline_vectors:
            return
        stacked = np.stack(list(self._baseline_vectors))
        # Use robust scaling by clipping extremes to avoid numerical issues.
        self._normalisation = np.maximum(1e-6, np.percentile(np.abs(stacked), 95, axis=0))

    def _baseline_deviation(self, vector: np.ndarray) -> float:
        if not self._baseline_vectors:
            return 0.0
        baseline_mean = np.mean(np.stack(list(self._baseline_vectors)), axis=0)
        deviation = float(np.mean(np.abs(vector - baseline_mean)))
        return float(np.clip(deviation, 0.0, 1.0))


__all__ = ["ResponseNoveltyAnalyzer"]
