"""
交易計劃制定系統（相容層）

此模組保留 `TradingPlanGenerator` 舊入口以維持相容，
實際計劃編排已統一委派到 `TradingPlanController`（單一路徑）。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .plan_controller import TradingPlanController

logger = logging.getLogger(__name__)


class TradingPlanGenerator:
    """交易計劃生成器（相容包裝器）"""

    def __init__(self, account_balance: float = 10000.0) -> None:
        self.account_balance = account_balance
        self._controller = TradingPlanController()
        logger.info("TradingPlanGenerator 已切換為 TradingPlanController 相容包裝器")

    async def generate_comprehensive_trading_plan(
        self,
        klines: Optional[List[Dict[str, Any]]] = None,
        account_balance: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        生成完整交易計劃（委派至 TradingPlanController）
        """
        balance = self.account_balance if account_balance is None else account_balance
        return await self._controller.create_comprehensive_plan(
            klines=klines,
            account_balance=float(balance),
        )

    def generate_comprehensive_trading_plan_sync(
        self,
        klines: Optional[List[Dict[str, Any]]] = None,
        account_balance: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        同步包裝（便於舊同步調用端過渡）
        """
        return asyncio.run(
            self.generate_comprehensive_trading_plan(
                klines=klines,
                account_balance=account_balance,
            )
        )


__all__ = ["TradingPlanGenerator"]
