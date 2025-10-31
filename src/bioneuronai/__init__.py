from .core import BioNeuron, BioLayer, BioNet, cli_loop
from .neuron_types import NEURON_REGISTRY, BaseSpikingNeuron, LIFNeuron, STDPNeuron

__all__ = [
    "BioNeuron",
    "BioLayer",
    "BioNet",
    "cli_loop",
    "BaseSpikingNeuron",
    "LIFNeuron",
    "STDPNeuron",
    "NEURON_REGISTRY",
]

# 導入改進版本 (可選)
try:
    from .improved_core import ImprovedBioNeuron, CuriositDrivenNet, BioNeuronV2
except ImportError:
    pass
else:
    __all__.extend(["ImprovedBioNeuron", "CuriositDrivenNet", "BioNeuronV2"])
