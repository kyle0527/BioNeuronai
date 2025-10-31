from .core import BioNeuron, BioLayer, BioNet, cli_loop
from .curiosity import CuriosityConfig, CuriosityDrivenNet

# 導入改進版本 (可選)
try:
    from .improved_core import ImprovedBioNeuron, BioNeuronV2
    __all__ = [
        "BioNeuron",
        "BioLayer",
        "BioNet",
        "cli_loop",
        "ImprovedBioNeuron",
        "CuriosityConfig",
        "CuriosityDrivenNet",
        "BioNeuronV2",
    ]
except ImportError:
    __all__ = [
        "BioNeuron",
        "BioLayer",
        "BioNet",
        "cli_loop",
        "CuriosityConfig",
        "CuriosityDrivenNet",
    ]
