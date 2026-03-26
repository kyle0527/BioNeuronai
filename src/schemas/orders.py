"""
BioNeuronai 訂單模型

專為幣安期貨交易設計的訂單相關 Pydantic 模型。
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, computed_field

from .enums import (
    OrderType,
    OrderSide,
    OrderStatus,
    TimeInForce
)


class BinanceOrderRequest(BaseModel):
    """幣安期貨下單請求模型"""
    
    symbol: str = Field(..., description="交易對符號 (如: BTCUSDT)")
    side: OrderSide = Field(..., description="訂單方向")
    type: OrderType = Field(..., description="訂單類型")
    quantity: Decimal = Field(..., gt=0, description="訂單數量")
    
    # 價格相關 (根據訂單類型決定是否必需)
    price: Optional[Decimal] = Field(None, gt=0, description="價格 (限價單必需)")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="觸發價格 (止損單必需)")
    
    # 訂單選項
    time_in_force: TimeInForce = Field(default=TimeInForce.GTC, description="訂單有效期")
    reduce_only: bool = Field(default=False, description="僅減倉")
    close_position: bool = Field(default=False, description="平倉")
    
    # 高級選項
    working_type: Optional[str] = Field(None, description="條件價格類型")
    price_protect: bool = Field(default=False, description="價格保護")
    new_client_order_id: Optional[str] = Field(None, description="客戶自定義訂單ID")
    
    @computed_field  
    @property
    def is_market_order(self) -> bool:
        """判斷是否為市價單"""
        return self.type == OrderType.MARKET
        
    @computed_field
    @property 
    def is_limit_order(self) -> bool:
        """判斷是否為限價單"""
        return self.type == OrderType.LIMIT
        
    @computed_field
    @property
    def requires_quantity(self) -> bool:
        """判斷是否需要數量參數"""
        return True  # 期貨交易都需要數量
    
    @field_validator("price")
    @classmethod
    def validate_price_for_limit_orders(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        """驗證限價單必須有價格"""
        if "type" in info.data:
            order_type = info.data["type"]
            if order_type in [OrderType.LIMIT, OrderType.STOP, OrderType.TAKE_PROFIT]:
                if v is None:
                    raise ValueError(f"{order_type} 訂單必須提供價格")
        return v


class BinanceOrderResponse(BaseModel):
    """幣安期貨訂單響應模型"""
    
    # 幣安返回的基本信息
    symbol: str = Field(..., description="交易對符號")
    order_id: int = Field(..., description="幣安訂單ID")
    client_order_id: str = Field(..., description="客戶訂單ID")
    
    # 訂單詳情
    side: OrderSide = Field(..., description="訂單方向")
    type: OrderType = Field(..., description="訂單類型")
    status: OrderStatus = Field(..., description="訂單狀態")
    
    # 數量和價格
    orig_qty: Decimal = Field(..., description="原始數量")
    executed_qty: Decimal = Field(..., description="已成交數量")
    cumulative_quote_qty: Decimal = Field(..., description="累計成交金額")
    
    price: Decimal = Field(..., description="訂單價格")
    avg_price: Decimal = Field(default=Decimal("0"), description="平均成交價格")
    stop_price: Optional[Decimal] = Field(None, description="觸發價格")
    
    # 時間信息
    time: datetime = Field(..., description="訂單創建時間")
    update_time: datetime = Field(..., description="訂單更新時間")
    
    # 其他選項
    time_in_force: TimeInForce = Field(..., description="訂單有效期")
    reduce_only: bool = Field(default=False, description="僅減倉")
    close_position: bool = Field(default=False, description="平倉")
    
    # 費用信息
    commission: Optional[Decimal] = Field(None, description="手續費")
    commission_asset: Optional[str] = Field(None, description="手續費幣種")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "order_id": 123456789,
                    "client_order_id": "test_order_1",
                    "side": "buy",
                    "type": "limit",
                    "status": "filled",
                    "orig_qty": "0.001",
                    "executed_qty": "0.001",
                    "cumulative_quote_qty": "50.25",
                    "price": "50250.00",
                    "avg_price": "50250.00",
                    "time": "2024-01-01T10:00:00Z",
                    "update_time": "2024-01-01T10:01:00Z",
                    "time_in_force": "gtc",
                    "commission": "0.0201",
                    "commission_asset": "USDT"
                }
            ]
        }
    }


class OrderBook(BaseModel):
    """訂單簿模型"""
    
    symbol: str = Field(..., description="交易對符號")
    last_update_id: int = Field(..., description="最後更新ID")
    
    # 買賣盤數據
    bids: list[tuple[Decimal, Decimal]] = Field(..., description="買盤 [(價格, 數量)]")
    asks: list[tuple[Decimal, Decimal]] = Field(..., description="賣盤 [(價格, 數量)]")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳")
    
    @property
    def best_bid(self) -> Optional[tuple[Decimal, Decimal]]:
        """最優買價"""
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[tuple[Decimal, Decimal]]:
        """最優賣價"""
        return self.asks[0] if self.asks else None
    
    @property
    def spread(self) -> Optional[Decimal]:
        """價差"""
        if self.best_bid and self.best_ask:
            return self.best_ask[0] - self.best_bid[0]
        return None