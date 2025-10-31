from .core import BioNeuron, BioLayer, BioNet, cli_loop
from .networks import (
    ConfigurableLayer,
    ConfigurableNetwork,
    LayerConfig,
    NetworkConfig,
    build_network,
)

# 導入改進版本 (可選)
try:
    from .improved_core import ImprovedBioNeuron, CuriositDrivenNet, BioNeuronV2
    __all__ = [
        "BioNeuron",
        "BioLayer",
        "BioNet",
        "cli_loop",
        "ConfigurableLayer",
        "ConfigurableNetwork",
        "LayerConfig",
        "NetworkConfig",
        "build_network",
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
        "ConfigurableLayer",
        "ConfigurableNetwork",
        "LayerConfig",
        "NetworkConfig",
        "build_network",
    ]
