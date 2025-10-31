from .core import BioLayer, BioNet, BioNeuron
from .cli import app as cli_app, main as cli_main


def cli_loop() -> None:
    """Backward compatible CLI entry point."""

    cli_main()

# 導入改進版本 (可選)
try:
    from .improved_core import ImprovedBioNeuron, CuriositDrivenNet, BioNeuronV2
    __all__ = [
        "BioNeuron",
        "BioLayer",
        "BioNet",
        "cli_loop",
        "cli_app",
        "cli_main",
        "ImprovedBioNeuron",
        "CuriositDrivenNet",
        "BioNeuronV2",
    ]
except ImportError:
    __all__ = ["BioNeuron", "BioLayer", "BioNet", "cli_loop", "cli_app", "cli_main"]
