from .core import BioNeuron, BioLayer, BioNet, cli_loop
from .security import (
    AuthConfig,
    BaseDetectionModule,
    DetectionEngineProtocol,
    EnhancedAuthModule,
    IDORConfig,
    ProductionIDORModule,
    ProductionSQLiModule,
    SQLiConfig,
    UnifiedSmartDetectionManager,
)

# 導入改進版本 (可選)
try:
    from .improved_core import ImprovedBioNeuron, CuriositDrivenNet, BioNeuronV2
    __all__ = ["BioNeuron", "BioLayer", "BioNet", "cli_loop", 
               "ImprovedBioNeuron", "CuriositDrivenNet", "BioNeuronV2"]
except ImportError:
    __all__ = ["BioNeuron", "BioLayer", "BioNet", "cli_loop"]

__all__.extend(
    [
        "AuthConfig",
        "BaseDetectionModule",
        "DetectionEngineProtocol",
        "EnhancedAuthModule",
        "IDORConfig",
        "ProductionIDORModule",
        "ProductionSQLiModule",
        "SQLiConfig",
        "UnifiedSmartDetectionManager",
    ]
)
