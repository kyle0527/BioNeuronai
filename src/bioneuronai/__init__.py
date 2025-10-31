"""Unified public API surface for BioNeuronAI."""

from .core import BioNeuron, BioLayer, BioNet, cli_loop
from .neuron_base import BaseNeuron, SupportsBatchLearning

__all__ = [
    "BaseNeuron",
    "SupportsBatchLearning",
    "BioNeuron",
    "BioLayer",
    "BioNet",
    "cli_loop",
]

try:  # 導入改進版本 (可選)
    from .improved_core import CuriositDrivenNet, ImprovedBioNeuron, BioNeuronV2

    __all__.extend(["ImprovedBioNeuron", "CuriositDrivenNet", "BioNeuronV2"])
except ImportError:  # pragma: no cover - optional dependency path
    pass
