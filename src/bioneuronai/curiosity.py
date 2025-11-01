"""Curiosity-driven utilities built on top of :mod:`bioneuronai.improved_core`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from .improved_core import ImprovedBioNeuron

__all__ = ["CuriosityConfig", "CuriosityDrivenNet"]


@dataclass
class CuriosityConfig:
    """Configuration options for :class:`CuriosityDrivenNet`."""

    input_dim: int = 2
    hidden_dim: int = 3
    curiosity_threshold: float = 0.5
    intrinsic_gain: float = 1.0


class CuriosityDrivenNet:
    """Network that exposes novelty as an intrinsic reward signal.

    The network is composed of :class:`~bioneuronai.improved_core.ImprovedBioNeuron`
    units. After every forward pass the associated novelty score of each neuron can
    be converted into a scalar intrinsic reward that can be fed back into a
    reinforcement learning update.
    """

    def __init__(self, input_dim: int = 2, hidden_dim: int = 3,
                 curiosity_threshold: float = 0.5, intrinsic_gain: float = 1.0) -> None:
        self.config = CuriosityConfig(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            curiosity_threshold=curiosity_threshold,
            intrinsic_gain=intrinsic_gain,
        )
        self.neurons: List[ImprovedBioNeuron] = [
            ImprovedBioNeuron(
                num_inputs=input_dim,
                adaptive_threshold=True,
                seed=42 + i,
            )
            for i in range(hidden_dim)
        ]
        self._last_novelties: List[float] = []

    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[float]]:
        """Run a forward pass and return both neuron outputs and novelties."""

        outputs: List[float] = []
        novelties: List[float] = []

        for neuron in self.neurons:
            output = neuron.forward(inputs)
            novelty = neuron.enhanced_novelty_score()
            outputs.append(output)
            novelties.append(novelty)

        self._last_novelties = novelties
        return outputs, novelties

    def intrinsic_reward(
        self,
        novelties: Iterable[float] | None = None,
        *,
        gain: float | None = None,
        baseline: float = 0.0,
    ) -> float:
        """Convert novelty scores into a scalar intrinsic reward.

        Args:
            novelties: Novelty scores to aggregate. When omitted the most recent
                novelties from :meth:`forward` are reused.
            gain: Optional multiplicative factor overriding the configured
                ``intrinsic_gain``.
            baseline: Value subtracted from the aggregated novelty. Use this to
                dampen persistent curiosity spikes.

        Returns:
            A clipped reward in ``[0, 1]`` suitable to be added to extrinsic
            environment rewards.
        """

        novelty_values = (
            list(novelties)
            if novelties is not None
            else list(self._last_novelties)
        )

        if not novelty_values:
            return 0.0

        aggregated = float(np.mean(novelty_values) - baseline)
        effective_gain = float(gain if gain is not None else self.config.intrinsic_gain)
        reward = max(0.0, aggregated) * effective_gain
        return float(np.clip(reward, 0.0, 1.0))

    def curious_learn(self, inputs: Sequence[float]) -> float:
        """Perform curiosity gated learning and return the average curiosity."""

        _, novelties = self.forward(inputs)
        avg_curiosity = float(np.mean(novelties))

        if avg_curiosity > self.config.curiosity_threshold:
            for neuron, novelty in zip(self.neurons, novelties):
                enhanced_lr = neuron.learning_rate * (1 + novelty)
                original_lr = neuron.learning_rate
                neuron.learning_rate = enhanced_lr
                neuron.improved_hebbian_learn(inputs)
                neuron.learning_rate = original_lr

        return avg_curiosity

    def get_network_stats(self) -> dict:
        """Return aggregated statistics for the curiosity network."""

        stats = [neuron.get_statistics() for neuron in self.neurons]
        return {
            "avg_activation_rate": float(np.mean([s["activation_rate"] for s in stats])),
            "avg_threshold": float(np.mean([s["current_threshold"] for s in stats])),
            "neuron_count": len(self.neurons),
            "individual_stats": stats,
        }


# Deprecated backwards compatibility for the previous typoed name. This alias will
# be removed in a future release after downstream projects migrate to the corrected
# :class:`CuriosityDrivenNet` symbol.
CuriositDrivenNet = CuriosityDrivenNet
