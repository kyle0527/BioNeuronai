from .core import BioNeuron, BioLayer, BioNet, cli_loop
from .neuron_base import LearningConfig, NeuronBase, NeuronProtocol

# 導入改進版本 (可選)
try:
    from .improved_core import ImprovedBioNeuron, CuriositDrivenNet, BioNeuronV2
    __all__ = [
        "BioNeuron",
        "BioLayer",
        "BioNet",
        "cli_loop",
        "LearningConfig",
        "NeuronBase",
        "NeuronProtocol",
        "ImprovedBioNeuron",
        "CuriositDrivenNet",
        "BioNeuronV2",
    ]
except ImportError:
    __all__ = [
        "BioNeuron",
        "BioLayer",
        "BioNet",
        "cli_loop",
        "LearningConfig",
        "NeuronBase",
        "NeuronProtocol",
    ]
