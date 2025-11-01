"""Synaptic learning rules used by spiking neuron models."""
from __future__ import annotations

import numpy as np


def stdp_update(
    weights: np.ndarray,
    pre_trace: np.ndarray,
    post_trace: float,
    lr: float,
    a_plus: float,
    a_minus: float,
    w_min: float,
    w_max: float,
) -> np.ndarray:
    """Apply pair-based STDP to the provided weights."""

    delta_w = lr * (a_plus * pre_trace * post_trace - a_minus * pre_trace ** 2)
    updated = np.clip(weights + delta_w, w_min, w_max)
    return updated


def anti_hebbian_update(
    weights: np.ndarray,
    activity: np.ndarray,
    lr: float,
    decay: float,
    w_min: float,
    w_max: float,
) -> np.ndarray:
    """Apply an anti-Hebbian decorrelation update to the weights."""

    delta_w = -lr * (activity - decay * np.mean(activity))
    updated = np.clip(weights + delta_w, w_min, w_max)
    return updated
