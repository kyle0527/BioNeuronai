from .core import BioNeuron, BioLayer, BioNet, cli_loop
from .neuron_base import LearningConfig, NeuronBase, NeuronProtocol

from .core import BioLayer, BioNet, BioNeuron, cli_loop
from .network import (
    BioNetConfig,
    LayerConfig,
    NetworkBuilder,
    NeuronConfig,
    load_config,
)


from .tool_gating import ToolDescriptor, ToolGatingManager, NoveltyThresholdStrategy

__all__ = [
    "BioNeuron",
    "BioLayer",
    "BioNet",
    "cli_loop",
    "ToolDescriptor",
    "ToolGatingManager",
    "NoveltyThresholdStrategy",
]

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
    __all__ = [
        "BioNeuron",
        "BioLayer",
        "BioNet",
        "cli_loop",

        "NeuronConfig",
        "LayerConfig",
        "BioNetConfig",
        "NetworkBuilder",
        "load_config",
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
