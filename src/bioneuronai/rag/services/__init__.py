# -*- coding: utf-8 -*-
"""
RAG Services 服務模塊

注意: 交易前檢查功能已整合到 trading.pretrade_automation 模組
請使用: from bioneuronai.trading import PreTradeCheckSystem
"""

# 從 trading 模組導入
try:
    from ...trading.pretrade_automation import PreTradeCheckSystem
except ImportError:
    PreTradeCheckSystem = None

__all__ = [
    'PreTradeCheckSystem',
]
