from .core import BioNeuron, BioLayer, BioNet, NetworkBuilder, cli_loop

# 導入改進版本 (可選)
try:
    from .improved_core import ImprovedBioNeuron, CuriositDrivenNet, BioNeuronV2
    __all__ = ["BioNeuron", "BioLayer", "BioNet", "NetworkBuilder", "cli_loop",
               "ImprovedBioNeuron", "CuriositDrivenNet", "BioNeuronV2"]
except ImportError:
    __all__ = ["BioNeuron", "BioLayer", "BioNet", "NetworkBuilder", "cli_loop"]
