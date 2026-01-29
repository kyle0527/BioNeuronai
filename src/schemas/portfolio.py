"""
BioNeuronai 組合管理模型

專為幣安期貨組合管理設計的 Pydantic 模型。
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any

from pydantic import BaseModel, Field, computed_field

from .enums import RiskLevel, PositionType
from .positions import BinancePosition, AccountBalance


class PortfolioSummary(BaseModel):
    """組合概要模型"""
    
    # 基本信息
    account_id: str = Field(..., description="賬戶ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="更新時間")
    
    # 餘額信息
    total_balance: Decimal = Field(..., description="總餘額")
    available_balance: Decimal = Field(..., description="可用餘額")
    unrealized_pnl: Decimal = Field(..., description="未實現盈虧")
    total_wallet_balance: Decimal = Field(..., description="錢包總餘額")
    
    # 倉位信息
    total_positions: int = Field(default=0, description="總倉位數")
    long_positions: int = Field(default=0, description="多倉數量")
    short_positions: int = Field(default=0, description="空倉數量")
    
    # 風險指標
    total_margin_used: Decimal = Field(default=Decimal("0"), description="使用的保證金")
    margin_ratio: Decimal = Field(default=Decimal("0"), description="保證金比率")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="整體風險等級")
    
    @computed_field
    @property
    def total_equity(self) -> Decimal:
        """總資產淨值"""
        return self.total_wallet_balance + self.unrealized_pnl
    
    @computed_field
    @property
    def margin_usage_percentage(self) -> Decimal:
        """保證金使用率"""
        if self.total_wallet_balance > 0:
            return (self.total_margin_used / self.total_wallet_balance) * 100
        return Decimal("0")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "account_id": "futures_account_1",
                    "total_balance": "10000.00",
                    "available_balance": "8500.00",
                    "unrealized_pnl": "150.25",
                    "total_wallet_balance": "10150.25",
                    "total_positions": 3,
                    "long_positions": 2,
                    "short_positions": 1,
                    "total_margin_used": "1500.00",
                    "margin_ratio": "14.78",
                    "risk_level": "medium"
                }
            ]
        }
    }


class Portfolio(BaseModel):
    """簡化投資組合模型 - 基於實際使用需求"""
    
    # 基本餘額信息
    balance: Decimal = Field(..., description="總餘額")
    margin_used: Decimal = Field(default=Decimal("0"), description="已使用保證金")
    
    # 詳細數據
    positions: List[Dict[str, Any]] = Field(default_factory=list, description="所有倉位")
    orders: List[Dict[str, Any]] = Field(default_factory=list, description="活躍訂單")
    
    # 績效統計
    daily_pnl: Decimal = Field(default=Decimal("0"), description="日盈虧")
    
    # 更新時間
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
    
    @computed_field
    @property
    def total_balance(self) -> Decimal:
        """總餘額（包含未實現盈虧）"""
        return self.balance + self.total_unrealized_pnl
    
    @computed_field
    @property
    def available_margin(self) -> Decimal:
        """可用保證金"""
        return self.balance - self.margin_used
    
    @computed_field
    @property
    def margin_ratio(self) -> Decimal:
        """保證金比率（百分比）"""
        if self.balance > 0:
            return (self.margin_used / self.balance) * 100
        return Decimal("0")
    
    @computed_field
    @property
    def total_unrealized_pnl(self) -> Decimal:
        """總未實現盈虧"""
        total_pnl = Decimal("0")
        for position_data in self.positions:
            if isinstance(position_data, dict) and 'unrealized_pnl' in position_data:
                total_pnl += Decimal(str(position_data['unrealized_pnl']))
        return total_pnl
    
    @computed_field
    @property
    def position_count(self) -> int:
        """開倉數量"""
        return len([pos for pos in self.positions if pos])
    
    @computed_field
    @property
    def position_count_by_symbol(self) -> Dict[str, int]:
        """按交易對統計倉位數量"""
        count = {}
        for position_data in self.positions:
            if isinstance(position_data, dict) and 'symbol' in position_data:
                symbol = position_data['symbol']
                count[symbol] = count.get(symbol, 0) + 1
        return count


class PortfolioAnalytics(BaseModel):
    """組合分析模型"""
    
    # 基本信息
    portfolio_id: str = Field(..., description="組合ID")
    analysis_date: datetime = Field(default_factory=datetime.now, description="分析日期")
    
    # 風險指標
    value_at_risk: Decimal = Field(..., description="風險價值 (VaR)")
    expected_shortfall: Decimal = Field(..., description="預期短缺 (ES)")
    maximum_drawdown: Decimal = Field(..., description="最大回撤")
    
    # 收益指標
    sharpe_ratio: Decimal = Field(..., description="夏普比率")
    sortino_ratio: Decimal = Field(..., description="索提諾比率")
    calmar_ratio: Decimal = Field(..., description="卡瑪比率")
    
    # 績效指標
    win_rate: Decimal = Field(..., description="勝率")
    profit_factor: Decimal = Field(..., description="盈利因子")
    avg_win: Decimal = Field(..., description="平均盈利")
    avg_loss: Decimal = Field(..., description="平均虧損")
    
    # 歷史表現
    total_trades: int = Field(default=0, description="總交易次數")
    winning_trades: int = Field(default=0, description="盈利交易次數")
    losing_trades: int = Field(default=0, description="虧損交易次數")
    
    # 分散度指標
    correlation_matrix: Dict[str, Dict[str, Decimal]] = Field(default_factory=dict, description="相關性矩陣")
    diversification_ratio: Decimal = Field(default=Decimal("0"), description="分散度比率")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "portfolio_id": "portfolio_001",
                    "value_at_risk": "450.00",
                    "expected_shortfall": "678.50",
                    "maximum_drawdown": "12.35",
                    "sharpe_ratio": "1.25",
                    "sortino_ratio": "1.67",
                    "calmar_ratio": "0.98",
                    "win_rate": "65.5",
                    "profit_factor": "1.85",
                    "avg_win": "125.50",
                    "avg_loss": "-67.80",
                    "total_trades": 150,
                    "winning_trades": 98,
                    "losing_trades": 52
                }
            ]
        }
    }


class RiskMetrics(BaseModel):
    """風險指標模型"""
    
    # 基本信息
    timestamp: datetime = Field(default_factory=datetime.now, description="計算時間")
    portfolio_value: Decimal = Field(..., description="組合總值")
    
    # 集中度風險
    position_concentration: Dict[str, Decimal] = Field(default_factory=dict, description="倉位集中度")
    symbol_exposure: Dict[str, Decimal] = Field(default_factory=dict, description="交易對曝險")
    
    # 保證金風險
    margin_ratio: Decimal = Field(..., description="保證金比率")
    margin_call_level: Decimal = Field(default=Decimal("80"), description="追保水平")
    liquidation_level: Decimal = Field(default=Decimal("50"), description="強平水平")
    
    # 流動性風險
    liquidity_score: Decimal = Field(default=Decimal("0"), description="流動性評分")
    market_impact: Decimal = Field(default=Decimal("0"), description="市場衝擊成本")
    
    @computed_field
    @property
    def risk_warning_level(self) -> RiskLevel:
        """風險警告等級"""
        if self.margin_ratio > 90:
            return RiskLevel.CRITICAL
        elif self.margin_ratio > 75:
            return RiskLevel.HIGH
        elif self.margin_ratio > 50:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    @computed_field
    @property
    def max_position_size(self) -> Decimal:
        """建議最大倉位規模"""
        # 根據風險等級調整最大倉位規模
        risk_level = self.risk_warning_level
        base_size = self.portfolio_value * Decimal("0.1")  # 基礎 10%
        
        if risk_level == RiskLevel.CRITICAL:
            return base_size * Decimal("0.2")  # 極高風險: 2%
        elif risk_level == RiskLevel.HIGH:
            return base_size * Decimal("0.5")  # 高風險: 5%
        elif risk_level == RiskLevel.MEDIUM:
            return base_size * Decimal("0.8")  # 中等風險: 8%
        else:
            return base_size  # 低風險: 10%