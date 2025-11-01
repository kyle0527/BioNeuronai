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


# 導入改進的核心模組
_improved = _try_import("bioneuronai.improved_core")
if _improved is not None:
    __all__.extend(["ImprovedBioNeuron", "CuriositDrivenNet", "BioNeuronV2"])
    ImprovedBioNeuron = getattr(_improved, "ImprovedBioNeuron")
    CuriositDrivenNet = getattr(_improved, "CuriositDrivenNet")
    BioNeuronV2 = getattr(_improved, "BioNeuronV2")

# 導入一億參數超大規模核心
_mega = _try_import("bioneuronai.mega_core")
if _mega is not None:
    __all__.extend([
        "MegaBioNeuron", "MegaBioLayer", "MegaBioNet", 
        "NetworkTopology", "create_hundred_million_param_network", "demo_mega_network"
    ])
    MegaBioNeuron = getattr(_mega, "MegaBioNeuron")
    MegaBioLayer = getattr(_mega, "MegaBioLayer")
    MegaBioNet = getattr(_mega, "MegaBioNet")
    NetworkTopology = getattr(_mega, "NetworkTopology")
    create_hundred_million_param_network = getattr(_mega, "create_hundred_million_param_network")
    demo_mega_network = getattr(_mega, "demo_mega_network")

# 導入RAG集成系統
_rag = _try_import("bioneuronai.rag_integration")
if _rag is not None:
    __all__.extend([
        "BioRAGSystem", "HybridRetriever", "BioNeuronEmbedder", 
        "Document", "QueryResult", "AdaptiveChunker", "MemoryAugmentedGenerator"
    ])
    BioRAGSystem = getattr(_rag, "BioRAGSystem")
    HybridRetriever = getattr(_rag, "HybridRetriever")
    BioNeuronEmbedder = getattr(_rag, "BioNeuronEmbedder")
    Document = getattr(_rag, "Document")
    QueryResult = getattr(_rag, "QueryResult")
    AdaptiveChunker = getattr(_rag, "AdaptiveChunker")
    MemoryAugmentedGenerator = getattr(_rag, "MemoryAugmentedGenerator")

# 導入增強核心 (2025優化版)
_enhanced = _try_import("bioneuronai.enhanced_core")
if _enhanced is not None:
    __all__.extend([
        "EnhancedBioCore", "BioAttentionMechanism", "HierarchicalMemorySystem",
        "BioMixtureOfExperts", "AttentionConfig", "MemoryConfig", "MoEConfig"
    ])
    EnhancedBioCore = getattr(_enhanced, "EnhancedBioCore")
    BioAttentionMechanism = getattr(_enhanced, "BioAttentionMechanism")
    HierarchicalMemorySystem = getattr(_enhanced, "HierarchicalMemorySystem")
    BioMixtureOfExperts = getattr(_enhanced, "BioMixtureOfExperts")
    AttentionConfig = getattr(_enhanced, "AttentionConfig")
    MemoryConfig = getattr(_enhanced, "MemoryConfig")
    MoEConfig = getattr(_enhanced, "MoEConfig")

# 導入AI優化配置
_ai_opt = _try_import("bioneuronai.ai_optimization_2025")
if _ai_opt is not None:
    __all__.extend([
        "AI_ARCHITECTURE_TRENDS_2024_2025", "RAG_OPTIMIZATION_STRATEGIES",
        "BIONEURON_OPTIMIZATION_RECOMMENDATIONS", "IMPLEMENTATION_PRIORITY", "ROADMAP_2025"
    ])
    AI_ARCHITECTURE_TRENDS_2024_2025 = getattr(_ai_opt, "AI_ARCHITECTURE_TRENDS_2024_2025")
    RAG_OPTIMIZATION_STRATEGIES = getattr(_ai_opt, "RAG_OPTIMIZATION_STRATEGIES")
    BIONEURON_OPTIMIZATION_RECOMMENDATIONS = getattr(_ai_opt, "BIONEURON_OPTIMIZATION_RECOMMENDATIONS")
    IMPLEMENTATION_PRIORITY = getattr(_ai_opt, "IMPLEMENTATION_PRIORITY")
    ROADMAP_2025 = getattr(_ai_opt, "ROADMAP_2025")

# 導入安全模組
_try_import("bioneuronai.enhanced_auth_module")
_try_import("bioneuronai.production_idor_module")
_try_import("bioneuronai.production_sqli_module")
