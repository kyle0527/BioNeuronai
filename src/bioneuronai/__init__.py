

"""Unified public API surface for BioNeuronAI."""

from .core import BioNeuron, BioLayer, BioNet, cli_loop

from .neuron_base import BaseNeuron, SupportsBatchLearning

__all__ = [
    "BaseNeuron",
    "SupportsBatchLearning",

    "BioLayer",
    "BioNet",
    "cli_loop",

    "NetworkBuilder",
    "BuiltNetwork",
    "BuiltLayer",
    "BaseBioNeuron",
    "LIFNeuron",
    "AntiHebbNeuron",

]

try:
    from .improved_core import ImprovedBioNeuron, CuriositDrivenNet, BioNeuronV2


        "BioLayer",
        "BioNet",
        "cli_loop",

        "ImprovedBioNeuron",
        "CuriositDrivenNet",
        "BioNeuronV2",
    ]

except ImportError:  # pragma: no cover - improved core is optional
    _core_exports = ["BioNeuron", "BioLayer", "BioNet", "cli_loop"]

from .agents.retrieval_controller import (
    InMemoryVectorRetriever,
    RetrievalController,
    RetrievalDecision,
    RetrieverProtocol,
    default_novelty_scorer,
)

__all__ = _core_exports + [
    "RetrievalController",
    "InMemoryVectorRetriever",
    "RetrievalDecision",
    "RetrieverProtocol",
    "default_novelty_scorer",
]




