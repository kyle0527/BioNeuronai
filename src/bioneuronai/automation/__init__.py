"""
自動化模組
==========
包含 SOP 自動化和交易前自動化工具
"""

from .sop_automation import SOPAutomationSystem
from .pretrade_automation import PreTradeCheckSystem

__all__ = [
    'SOPAutomationSystem',
    'PreTradeCheckSystem',
]

# 向後兼容別名
SOPAutomation = SOPAutomationSystem
PreTradeAutomation = PreTradeCheckSystem
