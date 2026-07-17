"""
BioNeuronai 交易成本計算器

提供精確的交易成本計算，包括：
- 交易手續費 (Maker/Taker)
- 市場滑點估算
- 資金費率 (期貨)
- 總成本評估

遵循 CODE_FIX_GUIDE.md 規範:
- 單一數據來源 (schemas/backtesting.py)
- 完整類型註釋
- 詳細文檔字符串

最後更新: 2026-02-15
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class TradingCost:
    """交易成本數據類
    
    Attributes:
        fee_pct: 手續費百分比
        slippage_pct: 滑點百分比
        total_cost_pct: 總成本百分比
        fee_usd: 手續費金額 (USD)
        slippage_usd: 滑點金額 (USD)
        total_cost_usd: 總成本金額 (USD)
        funding_rate: 資金費率 (期貨, 可選)
    """
    fee_pct: float
    slippage_pct: float
    total_cost_pct: float
    fee_usd: float
    slippage_usd: float
    total_cost_usd: float
    funding_rate: Optional[float] = None


class OrderInfo(BaseModel):
    """訂單信息模型"""
    size: Decimal = Field(..., description="訂單大小 (數量)")
    price: Decimal = Field(..., description="訂單價格")
    order_type: str = Field(..., description="訂單類型 (market/limit)")
    side: str = Field(..., description="訂單方向 (buy/sell)")


class TradingCostCalculator:
    """
    交易成本精確計算器
    
    計算模型：
    1. **手續費**: 基於 Binance Futures 費率表
       - Maker: 0.02% (掛單)
       - Taker: 0.04% (吃單)
    
    2. **滑點**: 動態模型
       - 基礎滑點: 0.05%
       - 訂單簿深度影響: order_size / avg_depth
       - 波動率放大: (1 + volatility)
       - 最大滑點: 1%
    
    3. **資金費率** (期貨):
       - 8小時結算一次
       - 通常範圍: -0.05% 到 +0.05%
    
    參考:
        - https://www.binance.com/en/fee/schedule
        - https://www.binance.com/en/support/faq/perpetual-futures-fee-structure
    
    Example:
        >>> calculator = TradingCostCalculator()
        >>> order = OrderInfo(
        ...     size=Decimal("1.0"),
        ...     price=Decimal("50000"),
        ...     order_type="market",
        ...     side="buy"
        ... )
        >>> cost = calculator.calculate_total_cost(order, is_maker=False)
        >>> print(f"總成本: {cost.total_cost_pct:.4%}")
    """
    
    def __init__(
        self,
        maker_fee: float = 0.0002,   # 0.02%
        taker_fee: float = 0.0004,   # 0.04%
        base_slippage: float = 0.0005  # 0.05%
    ):
        """
        初始化成本計算器
        
        Args:
            maker_fee: Maker 手續費率
            taker_fee: Taker 手續費率
            base_slippage: 基礎滑點率
        """
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.base_slippage = base_slippage
        
        logger.info(
            f"✅ TradingCostCalculator 初始化: "
            f"Maker={maker_fee:.4%}, Taker={taker_fee:.4%}, "
            f"BaseSlippage={base_slippage:.4%}"
        )
    
    def calculate_slippage(
        self,
        order_size: float,
        market_depth: Optional[Dict] = None,
        volatility: float = 0.0
    ) -> float:
        """
        計算市場滑點
        
        滑點模型:
            slippage = base_slippage * depth_factor * volatility_factor
            
            其中:
            - depth_factor = 1 + (order_size / avg_depth)
            - volatility_factor = 1 + volatility
        
        Args:
            order_size: 訂單大小 (USDT)
            market_depth: 訂單簿深度數據 {"total_volume_10": float}
            volatility: 波動率 (0-1)
        
        Returns:
            滑點百分比 (如 0.001 = 0.1%)
        """
        # 深度因子
        if market_depth and 'total_volume_10' in market_depth:
            avg_depth = market_depth['total_volume_10']
            depth_ratio = order_size / max(avg_depth, 1.0)
        else:
            # 無深度數據時使用保守估計
            depth_ratio = 0.1
        
        depth_factor = 1.0 + depth_ratio
        
        # 波動率因子
        volatility_factor = 1.0 + max(min(volatility, 1.0), 0.0)
        
        # 計算滑點
        slippage = self.base_slippage * depth_factor * volatility_factor
        
        # 限制最大滑點 1%
        return min(slippage, 0.01)
    
    def calculate_fee(self, is_maker: bool) -> float:
        """
        計算交易手續費
        
        Args:
            is_maker: 是否為 maker 訂單
        
        Returns:
            手續費百分比
        """
        return self.maker_fee if is_maker else self.taker_fee
    
    def calculate_total_cost(
        self,
        order: OrderInfo,
        is_maker: bool = False,
        market_depth: Optional[Dict] = None,
        volatility: float = 0.0,
        funding_rate: Optional[float] = None
    ) -> TradingCost:
        """
        計算總交易成本
        
        Args:
            order: 訂單信息
            is_maker: 是否為 maker 訂單
            market_depth: 訂單簿深度
            volatility: 市場波動率
            funding_rate: 資金費率 (期貨)
        
        Returns:
            TradingCost 對象，包含完整成本分解
        """
        # 訂單價值 (USDT)
        order_value = float(order.size * order.price)
        
        # 計算手續費
        fee_pct = self.calculate_fee(is_maker)
        fee_usd = order_value * fee_pct
        
        # 計算滑點
        slippage_pct = self.calculate_slippage(
            order_size=order_value,
            market_depth=market_depth,
            volatility=volatility
        )
        slippage_usd = order_value * slippage_pct
        
        # 總成本
        total_cost_pct = fee_pct + slippage_pct
        total_cost_usd = fee_usd + slippage_usd
        
        return TradingCost(
            fee_pct=fee_pct,
            slippage_pct=slippage_pct,
            total_cost_pct=total_cost_pct,
            fee_usd=fee_usd,
            slippage_usd=slippage_usd,
            total_cost_usd=total_cost_usd,
            funding_rate=funding_rate
        )
    
    def estimate_daily_funding_cost(
        self,
        position_value: float,
        funding_rate: float
    ) -> float:
        """
        估算每日資金費用 (期貨)
        
        資金費率每8小時結算一次，一天3次。
        
        Args:
            position_value: 持倉價值 (USDT)
            funding_rate: 單次資金費率 (如 0.0001 = 0.01%)
        
        Returns:
            每日資金費用 (USDT)
        """
        return position_value * funding_rate * 3  # 一天3次


if __name__ == "__main__":
    """測試交易成本計算器"""
    
    # 創建計算器
    calculator = TradingCostCalculator()
    
    # 創建測試訂單
    order = OrderInfo(
        size=Decimal("1.0"),
        price=Decimal("50000"),
        order_type="market",
        side="buy"
    )
    
    # 測試 1: 基礎成本計算
    print("\n" + "="*60)
    print("測試 1: 基礎成本計算 (Taker)")
    print("="*60)
    cost = calculator.calculate_total_cost(order, is_maker=False)
    print(f"訂單大小: {order.size} BTC")
    print(f"訂單價格: ${order.price}")
    print(f"訂單價值: ${float(order.size * order.price)}")
    print(f"手續費: {cost.fee_pct:.4%} (${cost.fee_usd:.2f})")
    print(f"滑點: {cost.slippage_pct:.4%} (${cost.slippage_usd:.2f})")
    print(f"總成本: {cost.total_cost_pct:.4%} (${cost.total_cost_usd:.2f})")
    
    # 測試 2: Maker 成本
    print("\n" + "="*60)
    print("測試 2: Maker 成本")
    print("="*60)
    cost_maker = calculator.calculate_total_cost(order, is_maker=True)
    print(f"手續費: {cost_maker.fee_pct:.4%} (${cost_maker.fee_usd:.2f})")
    print(f"總成本: {cost_maker.total_cost_pct:.4%} (${cost_maker.total_cost_usd:.2f})")
    
    # 測試 3: 高波動環境
    print("\n" + "="*60)
    print("測試 3: 高波動環境 (波動率 50%)")
    print("="*60)
    cost_volatile = calculator.calculate_total_cost(
        order,
        is_maker=False,
        volatility=0.5
    )
    print(f"滑點: {cost_volatile.slippage_pct:.4%} (${cost_volatile.slippage_usd:.2f})")
    print(f"總成本: {cost_volatile.total_cost_pct:.4%} (${cost_volatile.total_cost_usd:.2f})")
    
    # 測試 4: 資金費用估算
    print("\n" + "="*60)
    print("測試 4: 資金費用估算")
    print("="*60)
    position_value = 50000.0
    funding_rate = 0.0001  # 0.01%
    daily_funding = calculator.estimate_daily_funding_cost(position_value, funding_rate)
    print(f"持倉價值: ${position_value}")
    print(f"資金費率: {funding_rate:.4%}")
    print(f"每日費用: ${daily_funding:.2f}")
    
    print("\n✅ 所有測試完成")
