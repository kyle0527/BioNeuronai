"""
每日報告資料模型
================

定義每日市場分析報告的資料結構

遵循 CODE_FIX_GUIDE.md 規範
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, cast
from dataclasses import dataclass


@dataclass
class MarketEnvironmentCheck:
    """
    市場環境檢查結果
    
    包含全球市場動態、加密貨幣情緒、經濟事件等分析結果
    """
    timestamp: datetime
    us_futures: Optional[str] = None
    asian_markets: Optional[str] = None
    european_markets: Optional[str] = None
    crypto_sentiment: Optional[float] = None
    economic_events: Optional[List[str]] = None
    news_analysis: Optional[Dict] = None
    overall_status: str = "UNKNOWN"


@dataclass
class TradingPlanCheck:
    """
    交易計劃檢查結果
    
    包含策略選擇、風險參數、交易對篩選等規劃結果
    """
    timestamp: datetime
    selected_strategy: Optional[str] = None
    risk_parameters: Optional[Dict] = None
    trading_pairs: Optional[List[str]] = None
    daily_limits: Optional[Dict] = None
    overall_status: str = "UNKNOWN"


@dataclass
class DailyMarketCondition:
    """
    市場狀況分析結果
    """
    condition: str  # NORMAL, VOLATILE, TRENDING, RANGING
    volatility: str  # LOW, MEDIUM, HIGH, EXTREME
    trend: str  # UPTREND, DOWNTREND, SIDEWAYS
    strength: float  # 0.0 - 1.0


@dataclass
class StrategyPerformance:
    """
    策略表現評估結果
    """
    best_strategy: str
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sample_size: int = 0


@dataclass
class DailyRiskLimits:
    """
    風險參數配置
    """
    single_trade_risk: float  # 單筆交易風險 %
    daily_max_loss: float  # 每日最大虧損 %
    max_positions: int  # 最大持倉數
    max_daily_trades: int  # 每日最大交易次數
    adjustment_factor: float = 1.0  # 波動率調整係數


@dataclass
class TradingPairsPriority:
    """
    交易對優先級清單
    """
    primary: List[str]  # 主要交易對
    backup: List[str]  # 備用交易對
    excluded: Optional[List[str]] = None  # 排除的交易對
    
    def __post_init__(self):
        if self.excluded is None:
            self.excluded = []


@dataclass
class DailyReport:
    """
    每日市場分析報告
    """
    report_time: datetime
    report_version: str
    report_type: str
    market_environment: MarketEnvironmentCheck
    trading_plan: TradingPlanCheck
    overall_assessment: Dict
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "report_time": self.report_time.isoformat() if isinstance(self.report_time, datetime) else str(self.report_time),
            "report_version": self.report_version,
            "report_type": self.report_type,
            "market_environment": self._dataclass_to_dict(self.market_environment),
            "trading_plan": self._dataclass_to_dict(self.trading_plan),
            "overall_assessment": self.overall_assessment
        }
    
    @staticmethod
    def _dataclass_to_dict(obj: Any) -> Dict[str, Any]:
        """將 dataclass 轉換為字典"""
        if hasattr(obj, '__dataclass_fields__'):
            result: Dict[str, Any] = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                elif hasattr(value, '__dataclass_fields__'):
                    result[field_name] = DailyReport._dataclass_to_dict(value)
                else:
                    result[field_name] = value
            return result
        return cast(Dict[str, Any], obj)
