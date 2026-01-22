"""
BioNeuronai 倉位模型

專為幣安期貨倉位管理設計的 Pydantic 模型。
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, computed_field

from bioneuronai.schemas.enums import PositionType


class BinancePosition(BaseModel):
    """幣安期貨倉位模型"""
    
    # 基本信息
    symbol: str = Field(..., description="交易對符號")
    position_side: PositionType = Field(..., description="倉位方向")
    
    # 數量和價格
    position_amt: Decimal = Field(..., description="倉位數量")
    entry_price: Decimal = Field(..., description="開倉平均價")
    mark_price: Decimal = Field(..., description="標記價格")
    
    # 損益信息
    unrealized_pnl: Decimal = Field(..., description="未實現盈虧")
    percentage: Decimal = Field(..., description="持倉收益率")
    
    # 保證金信息  
    isolated_margin: Decimal = Field(default=Decimal("0"), description="逐倉保證金")
    notional: Decimal = Field(default=Decimal("0"), description="名義價值")
    isolated_wallet: Decimal = Field(default=Decimal("0"), description="逐倉錢包餘額")
    
    # 保證金類型
    margin_type: str = Field(default="cross", description="保證金類型")
    
    # 更新時間
    update_time: datetime = Field(..., description="更新時間")
    
    # 雙開模式標識
    is_hedge_mode: bool = Field(default=False, description="是否為雙開模式")
    
    @computed_field
    @property
    def is_open(self) -> bool:
        """判斷倉位是否開啟"""
        return abs(self.position_amt) > 0
    
    @computed_field
    @property
    def position_value(self) -> Decimal:
        """倉位價值"""
        return abs(self.position_amt) * self.mark_price
    
    @computed_field
    @property
    def pnl_percentage(self) -> Decimal:
        """盈虧百分比"""
        if self.isolated_margin > 0:
            return (self.unrealized_pnl / self.isolated_margin) * 100
        return Decimal("0")
    
    @computed_field
    @property
    def roi(self) -> Decimal:
        """投資報酬率 (ROI)"""
        if self.entry_price > 0:
            price_diff = self.mark_price - self.entry_price
            if self.position_side == PositionType.SHORT:
                price_diff = -price_diff
            return (price_diff / self.entry_price) * 100
        return Decimal("0")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "position_side": "long",
                    "position_amt": "0.001",
                    "entry_price": "50000.00",
                    "mark_price": "51000.00",
                    "unrealized_pnl": "1.00",
                    "percentage": "2.00",
                    "isolated_margin": "50.00",
                    "notional": "51.00",
                    "isolated_wallet": "51.00",
                    "update_time": "2024-01-01T10:00:00Z",
                    "is_hedge_mode": False
                }
            ]
        }
    }


class PositionRisk(BaseModel):
    """倉位風險信息"""
    
    symbol: str = Field(..., description="交易對符號")
    position_amt: Decimal = Field(..., description="倉位數量")
    entry_price: Decimal = Field(..., description="開倉平均價")
    mark_price: Decimal = Field(..., description="標記價格")
    
    # 風險指標
    unrealized_pnl: Decimal = Field(..., description="未實現盈虧")
    liquidation_price: Decimal = Field(..., description="強平價格")
    leverage: Decimal = Field(..., description="槓桿倍數")
    
    # 保證金信息
    isolated_margin: Decimal = Field(..., description="逐倉保證金")
    notional: Decimal = Field(..., description="名義價值")
    margin_type: str = Field(..., description="保證金模式")
    
    # 更新時間
    update_time: datetime = Field(..., description="更新時間")
    
    @computed_field
    @property
    def margin_ratio(self) -> Decimal:
        """保證金比率"""
        if abs(self.notional) > 0:
            return (self.isolated_margin / abs(self.notional)) * 100
        return Decimal("0")
    
    @computed_field
    @property
    def distance_to_liquidation(self) -> Decimal:
        """距離強平價的百分比"""
        if self.liquidation_price > 0 and self.mark_price > 0:
            return abs((self.mark_price - self.liquidation_price) / self.mark_price) * 100
        return Decimal("0")


class AccountBalance(BaseModel):
    """賬戶餘額模型"""
    
    # 賬戶類型
    account_alias: str = Field(..., description="賬戶別名")
    asset: str = Field(..., description="資產名稱")
    
    # 餘額信息
    balance: Decimal = Field(..., description="總餘額")
    cross_wallet_balance: Decimal = Field(..., description="全倉錢包餘額")
    cross_unrealized_pnl: Decimal = Field(..., description="全倉未實現盈虧")
    available_balance: Decimal = Field(..., description="可用餘額")
    
    # 保證金信息
    max_withdraw_amount: Decimal = Field(..., description="最大可轉出餘額")
    margin_available: bool = Field(..., description="是否可用作聯合保證金")
    
    # 更新時間
    update_time: datetime = Field(..., description="更新時間")
    
    @computed_field
    @property
    def total_wallet_balance(self) -> Decimal:
        """錢包總餘額"""
        return self.cross_wallet_balance + self.cross_unrealized_pnl
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "account_alias": "futures",
                    "asset": "USDT",
                    "balance": "1000.00",
                    "cross_wallet_balance": "1000.00",
                    "cross_unrealized_pnl": "10.50",
                    "available_balance": "950.00",
                    "max_withdraw_amount": "950.00",
                    "margin_available": True,
                    "update_time": "2024-01-01T10:00:00Z"
                }
            ]
        }
    }