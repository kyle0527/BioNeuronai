from .core import BioNeuron, BioLayer, BioNet, cli_loop
from .network_builder import NetworkBuilder, BuiltNetwork, BuiltLayer
from .neurons import BaseBioNeuron, LIFNeuron, AntiHebbNeuron

__all__ = [
    "BioNeuron",
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

    __all__.extend(["ImprovedBioNeuron", "CuriositDrivenNet", "BioNeuronV2"])
except ImportError:
    pass
