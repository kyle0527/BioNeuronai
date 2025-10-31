from .core import BioNeuron, BioLayer, BioNet, cli_loop
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

# 導入改進版本 (可選)
try:
    from .improved_core import ImprovedBioNeuron, CuriositDrivenNet, BioNeuronV2

    __all__ += ["ImprovedBioNeuron", "CuriositDrivenNet", "BioNeuronV2"]
except ImportError:
    pass
