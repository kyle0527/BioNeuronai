"""
BioNeuronai 外部數據源模型

定義外部市場數據相關的 Pydantic 模型（遵循 CODE_FIX_GUIDE.md 單一數據來源原則）
"""

from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# 範例數據常量
EXAMPLE_TIMESTAMP = "2026-02-15T10:00:00Z"


class DataSourceType(str, Enum):
    """外部數據源類型"""
    COINGECKO = "coingecko"
    ALTERNATIVE_ME = "alternative_me"
    DEFI_LLAMA = "defillama"
    BINANCE = "binance"
    ECONOMIC_CALENDAR = "economic_calendar"


class FearGreedIndex(BaseModel):
    """恐慌貪婪指數模型"""
    
    value: int = Field(..., ge=0, le=100, description="指數值 0-100")
    value_classification: str = Field(..., description="分類：Extreme Fear, Fear, Neutral, Greed, Extreme Greed")
    timestamp: datetime = Field(..., description="時間戳")
    time_until_update: Optional[int] = Field(None, description="距離下次更新的秒數")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "value": 45,
                    "value_classification": "Fear",
                    "timestamp": EXAMPLE_TIMESTAMP,
                    "time_until_update": 3600
                }
            ]
        }
    }


class GlobalMarketData(BaseModel):
    """全球市場數據模型"""
    
    total_market_cap: float = Field(..., gt=0, description="全球市值（美元）")
    total_volume_24h: float = Field(..., ge=0, description="24小時交易量（美元）")
    btc_dominance: float = Field(..., ge=0, le=100, description="BTC市場占比（%）")
    eth_dominance: float = Field(..., ge=0, le=100, description="ETH市場占比（%）")
    active_cryptocurrencies: int = Field(..., gt=0, description="活躍加密貨幣數量")
    markets: int = Field(..., gt=0, description="市場數量")
    market_cap_change_24h: float = Field(..., description="24小時市值變化（%）")
    timestamp: datetime = Field(..., description="時間戳")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_market_cap": 2500000000000.0,
                    "total_volume_24h": 85000000000.0,
                    "btc_dominance": 52.5,
                    "eth_dominance": 17.3,
                    "active_cryptocurrencies": 10000,
                    "markets": 750,
                    "market_cap_change_24h": 2.5,
                    "timestamp": EXAMPLE_TIMESTAMP
                }
            ]
        }
    }


class DeFiMetrics(BaseModel):
    """DeFi 協議指標模型"""
    
    total_tvl: float = Field(..., ge=0, description="總鎖倉價值（美元）")
    chains: Dict[str, float] = Field(default_factory=dict, description="各鏈 TVL 分布")
    protocols: Dict[str, float] = Field(default_factory=dict, description="各協議 TVL 分布")
    tvl_change_24h: float = Field(..., description="24小時 TVL 變化（%）")
    timestamp: datetime = Field(..., description="時間戳")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_tvl": 95000000000.0,
                    "chains": {"ethereum": 45000000000.0, "bsc": 12000000000.0},
                    "protocols": {"uniswap": 8000000000.0, "aave": 6500000000.0},
                    "tvl_change_24h": 1.2,
                    "timestamp": EXAMPLE_TIMESTAMP
                }
            ]
        }
    }


class StablecoinMetrics(BaseModel):
    """穩定幣指標模型"""
    
    total_supply: float = Field(..., ge=0, description="總供應量（美元）")
    supply_by_token: Dict[str, float] = Field(default_factory=dict, description="各穩定幣供應量")
    supply_change_24h: float = Field(..., description="24小時供應量變化（%）")
    supply_change_7d: float = Field(..., description="7天供應量變化（%）")
    timestamp: datetime = Field(..., description="時間戳")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_supply": 145000000000.0,
                    "supply_by_token": {"USDT": 95000000000.0, "USDC": 35000000000.0},
                    "supply_change_24h": 0.5,
                    "supply_change_7d": 2.1,
                    "timestamp": EXAMPLE_TIMESTAMP
                }
            ]
        }
    }


class EconomicEvent(BaseModel):
    """經濟日曆事件模型"""
    
    event_id: str = Field(..., description="事件ID")
    title: str = Field(..., description="事件標題")
    country: str = Field(..., description="國家代碼")
    date: datetime = Field(..., description="事件日期時間")
    impact: str = Field(..., description="影響級別：Low, Medium, High")
    forecast: Optional[str] = Field(None, description="預測值")
    previous: Optional[str] = Field(None, description="前值")
    actual: Optional[str] = Field(None, description="實際值")
    currency: Optional[str] = Field(None, description="相關貨幣")
    
    @field_validator("impact")
    @classmethod
    def validate_impact(cls, v: str) -> str:
        """驗證影響級別"""
        valid_impacts = ["Low", "Medium", "High"]
        if v not in valid_impacts:
            raise ValueError(f"影響級別必須是 {valid_impacts} 之一")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_id": "fed_2026_02_15",
                    "title": "Federal Reserve Interest Rate Decision",
                    "country": "US",
                    "date": "2026-02-15T19:00:00Z",
                    "impact": "High",
                    "forecast": "5.25%",
                    "previous": "5.25%",
                    "actual": None,
                    "currency": "USD"
                }
            ]
        }
    }


class MarketSentiment(BaseModel):
    """市場情緒綜合評分模型"""
    
    overall_sentiment: float = Field(..., ge=-1.0, le=1.0, description="整體情緒評分 -1 (極度看空) 到 +1 (極度看多)")
    fear_greed_score: float = Field(..., ge=-1.0, le=1.0, description="恐慌貪婪標準化評分")
    news_sentiment: float = Field(..., ge=-1.0, le=1.0, description="新聞情緒評分")
    social_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0, description="社交媒體情緒評分")
    market_momentum: float = Field(..., ge=-1.0, le=1.0, description="市場動量評分")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="信心水平 0-1")
    timestamp: datetime = Field(..., description="時間戳")
    components: Dict[str, float] = Field(default_factory=dict, description="各組成部分的原始值")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "overall_sentiment": 0.35,
                    "fear_greed_score": 0.2,
                    "news_sentiment": 0.45,
                    "social_sentiment": 0.3,
                    "market_momentum": 0.5,
                    "confidence_level": 0.75,
                    "timestamp": EXAMPLE_TIMESTAMP,
                    "components": {
                        "fear_greed_index": 60,
                        "volume_change_24h": 15.5,
                        "market_cap_change_24h": 2.3
                    }
                }
            ]
        }
    }


class ExternalDataSnapshot(BaseModel):
    """外部數據快照（統一數據容器）"""
    
    snapshot_id: str = Field(..., description="快照ID")
    timestamp: datetime = Field(..., description="快照時間戳")
    
    # 各類數據（可選）
    fear_greed: Optional[FearGreedIndex] = Field(None, description="恐慌貪婪指數")
    global_market: Optional[GlobalMarketData] = Field(None, description="全球市場數據")
    defi_metrics: Optional[DeFiMetrics] = Field(None, description="DeFi指標")
    stablecoin_metrics: Optional[StablecoinMetrics] = Field(None, description="穩定幣指標")
    market_sentiment: Optional[MarketSentiment] = Field(None, description="市場情緒")
    economic_events: List[EconomicEvent] = Field(default_factory=list, description="重要經濟事件")
    
    # 元數據
    data_sources: List[DataSourceType] = Field(default_factory=list, description="數據來源列表")
    fetch_duration_ms: Optional[int] = Field(None, description="數據抓取耗時（毫秒）")
    errors: List[str] = Field(default_factory=list, description="錯誤列表")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "snapshot_id": "snapshot_20260215_100000",
                    "timestamp": EXAMPLE_TIMESTAMP,
                    "fear_greed": {
                        "value": 45,
                        "value_classification": "Fear",
                        "timestamp": EXAMPLE_TIMESTAMP
                    },
                    "data_sources": ["alternative_me", "coingecko"],
                    "fetch_duration_ms": 1250,
                    "errors": []
                }
            ]
        }
    }
