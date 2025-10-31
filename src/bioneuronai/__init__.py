from .core import BioLayer, BioNet, BioNeuron, cli_loop
from .network import (
    BioNetConfig,
    LayerConfig,
    NetworkBuilder,
    NeuronConfig,
    load_config,
)

# 導入改進版本 (可選)
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
        "NeuronConfig",
        "LayerConfig",
        "BioNetConfig",
        "NetworkBuilder",
        "load_config",
    ]
