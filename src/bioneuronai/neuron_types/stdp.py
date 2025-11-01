"""STDP-capable neuron types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .learning_rules import anti_hebbian_update, stdp_update
from .lif import LIFNeuron


@dataclass
class PlasticityConfig:
    lr: float = 1e-2
    tau_pre: float = 20.0
    tau_post: float = 20.0
    a_plus: float = 0.01
    a_minus: float = 0.012
    w_min: float = -1.0
    w_max: float = 1.0
    anti_hebbian_decay: float = 0.1


class STDPNeuron(LIFNeuron):
    """Leaky integrate-and-fire neuron equipped with STDP plasticity."""

    def __init__(
        self,
        num_inputs: int,
        plasticity: PlasticityConfig | None = None,
        **lif_kwargs,
    ) -> None:
        super().__init__(num_inputs=num_inputs, **lif_kwargs)
        self.plasticity = plasticity or PlasticityConfig()
        self.pre_trace = np.zeros(self.num_inputs, dtype=np.float32)
        self.post_trace = 0.0

    def _decay_traces(self, dt: float) -> None:
        self.pre_trace *= np.exp(-dt / self.plasticity.tau_pre)
        self.post_trace *= float(np.exp(-dt / self.plasticity.tau_post))

    def step(self, inputs: Sequence[float], dt: float = 1.0) -> bool:
        if len(inputs) != self.num_inputs:
            raise ValueError("inputs length mismatch")
        pre_spike = (np.asarray(inputs, dtype=np.float32) > 0).astype(np.float32)
        self._decay_traces(dt)
        self.pre_trace += pre_spike

        spiked = super().step(inputs, dt=dt)
        if spiked:
            self.post_trace += 1.0

        self._apply_plasticity(pre_spike, spiked)
        return spiked

    def _apply_plasticity(self, pre_spike: np.ndarray, post_spike: bool) -> None:
        cfg = self.plasticity
        if post_spike:
            self.weights = stdp_update(
                self.weights,
                self.pre_trace,
                post_trace=self.post_trace,
                lr=cfg.lr,
                a_plus=cfg.a_plus,
                a_minus=cfg.a_minus,
                w_min=cfg.w_min,
                w_max=cfg.w_max,
            )
        elif np.any(pre_spike > 0):
            self.weights = anti_hebbian_update(
                self.weights,
                activity=pre_spike,
                lr=cfg.lr,
                decay=cfg.anti_hebbian_decay,
                w_min=cfg.w_min,
                w_max=cfg.w_max,
            )
