"""Public package interface for BioNeuronAI."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Optional

from .core import BioLayer, BioNet, BioNeuron, cli_loop

__all__ = ["BioNeuron", "BioLayer", "BioNet", "cli_loop"]


def _try_import(module_name: str) -> Optional[ModuleType]:
    """Attempt to import a module and expose it as a package attribute."""

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None

    attr_name = module_name.rsplit(".", 1)[-1]
    globals()[attr_name] = module
    __all__.append(attr_name)
    return module


_improved = _try_import("bioneuronai.improved_core")
if _improved is not None:
    __all__.extend(["ImprovedBioNeuron", "CuriositDrivenNet", "BioNeuronV2"])
    ImprovedBioNeuron = getattr(_improved, "ImprovedBioNeuron")
    CuriositDrivenNet = getattr(_improved, "CuriositDrivenNet")
    BioNeuronV2 = getattr(_improved, "BioNeuronV2")

_try_import("bioneuronai.enhanced_auth_module")
_try_import("bioneuronai.production_idor_module")
_try_import("bioneuronai.production_sqli_module")
