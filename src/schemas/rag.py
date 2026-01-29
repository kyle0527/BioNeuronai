# -*- coding: utf-8 -*-
"""
RAG (Retrieval-Augmented Generation) 相關 Schema

提供 RAG 模組使用的 Pydantic 模型定義。
這些模型可以被其他模組引用，實現類型安全的數據交換。
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .enums import RiskLevel


# ========== RAG 專用枚舉 ==========

class RAGDocumentType(str, Enum):
    """RAG 文檔類型"""
    TRADING_RULE = "trading_rule"           # 交易規則
    STRATEGY_CONFIG = "strategy_config"     # 策略配置
    MARKET_ANALYSIS = "market_analysis"     # 市場分析
    HISTORICAL_TRADE = "historical_trade"   # 歷史交易
    NEWS_ARCHIVE = "news_archive"           # 新聞存檔
    WEB_SEARCH = "web_search"               # 網路搜索結果
    CUSTOM = "custom"                       # 自定義


class RAGCheckResult(str, Enum):
    """RAG 檢查結果"""
    SAFE = "safe"                   # 安全，可以交易
    CAUTION = "caution"             # 注意，需謹慎
    WARNING = "warning"             # 警告，建議減少倉位
    DANGER = "danger"               # 危險，建議不交易
    CRITICAL = "critical"           # 嚴重，必須暫停
    
    def to_risk_level(self) -> RiskLevel:
        """轉換為統一的 RiskLevel"""
        mapping = {
            RAGCheckResult.SAFE: RiskLevel.LOW,
            RAGCheckResult.CAUTION: RiskLevel.MEDIUM,
            RAGCheckResult.WARNING: RiskLevel.HIGH,
            RAGCheckResult.DANGER: RiskLevel.HIGH,
            RAGCheckResult.CRITICAL: RiskLevel.CRITICAL,
        }
        return mapping.get(self, RiskLevel.MEDIUM)


class RAGRiskFactor(str, Enum):
    """RAG 風險因素類型"""
    NEGATIVE_NEWS = "negative_news"             # 負面新聞
    REGULATORY = "regulatory"                   # 監管風險
    SECURITY_BREACH = "security_breach"         # 安全事件
    MARKET_VOLATILITY = "market_volatility"     # 市場波動
    SENTIMENT_EXTREME = "sentiment_extreme"     # 極端情緒
    MAJOR_EVENT = "major_event"                 # 重大事件
    LOW_LIQUIDITY = "low_liquidity"             # 流動性低


class NewsSentiment(str, Enum):
    """新聞情緒"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class NewsCategory(str, Enum):
    """新聞分類"""
    MARKET_ANALYSIS = "market_analysis"     # 市場分析
    REGULATION = "regulation"               # 監管政策
    TECHNOLOGY = "technology"               # 技術更新
    BUSINESS = "business"                   # 商業動態
    SECURITY = "security"                   # 安全事件
    ADOPTION = "adoption"                   # 採用新聞
    TRADING = "trading"                     # 交易相關
    MACRO = "macro"                         # 宏觀經濟
    GENERAL = "general"                     # 一般新聞


class SearchEngine(str, Enum):
    """搜索引擎"""
    DUCKDUCKGO = "duckduckgo"
    GOOGLE = "google"
    BING = "bing"


class RetrievalSource(str, Enum):
    """檢索來源"""
    INTERNAL_KB = "internal_kb"     # 內部知識庫
    WEB_SEARCH = "web_search"       # 網路搜索
    NEWS_API = "news_api"           # 新聞 API


# ========== RAG Pydantic 模型 ==========

class RAGRiskItem(BaseModel):
    """風險項目"""
    factor: RAGRiskFactor
    severity: int = Field(ge=1, le=10, description="嚴重程度 1-10")
    description: str
    source: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None


class RAGNewsItem(BaseModel):
    """新聞項目"""
    title: str
    summary: Optional[str] = None
    url: str
    source: str
    published_at: Optional[datetime] = None
    sentiment: NewsSentiment = NewsSentiment.NEUTRAL
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    category: NewsCategory = NewsCategory.GENERAL
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    duration_hours: Optional[float] = Field(default=None, ge=0.0, description="消息持續時間（小時）")
    related_news_count: int = Field(default=0, ge=0, description="相關新聞數量")
    
    class Config:
        use_enum_values = True


class PreTradeCheckRequest(BaseModel):
    """交易前檢查請求"""
    symbol: str = Field(..., description="交易對符號，如 BTCUSDT")
    context: str = Field(default="", description="額外上下文，如交易方向")
    check_hours: int = Field(default=6, ge=1, le=72, description="檢查時間範圍（小時）")
    include_web_search: bool = Field(default=True, description="是否包含網路搜索")
    include_news: bool = Field(default=True, description="是否包含新聞")
    include_internal_kb: bool = Field(default=True, description="是否包含內部知識庫")


class PreTradeCheckResponse(BaseModel):
    """交易前檢查響應"""
    symbol: str
    check_time: datetime
    result: RAGCheckResult
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=100.0, description="風險分數 0-100")
    can_trade: bool
    reason: str
    
    # 詳細信息
    risks: List[RAGRiskItem] = Field(default_factory=list)
    news_sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    news_count: int = Field(default=0, ge=0)
    positive_count: int = Field(default=0, ge=0)
    negative_count: int = Field(default=0, ge=0)
    
    # 建議
    suggested_action: str = ""
    position_size_modifier: float = Field(default=1.0, ge=0.0, le=2.0)
    
    # 來源統計
    internal_checks: int = Field(default=0, ge=0)
    external_searches: int = Field(default=0, ge=0)
    
    class Config:
        use_enum_values = True


class SearchResult(BaseModel):
    """搜索結果"""
    title: str
    url: str
    snippet: str
    source: str
    engine: SearchEngine = SearchEngine.DUCKDUCKGO
    authority_score: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    published_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class RetrievalQuery(BaseModel):
    """統一檢索查詢"""
    query: str
    symbol: Optional[str] = None
    sources: List[RetrievalSource] = Field(
        default_factory=lambda: list(RetrievalSource)
    )
    top_k: int = Field(default=10, ge=1, le=100)
    time_range_hours: Optional[int] = Field(default=24, ge=1, le=720)
    
    class Config:
        use_enum_values = True


class RetrievalResult(BaseModel):
    """統一檢索結果"""
    source: RetrievalSource
    title: str
    content: str
    url: Optional[str] = None
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class KnowledgeDocumentSchema(BaseModel):
    """知識文檔 Schema"""
    id: str
    title: str
    content: str
    doc_type: RAGDocumentType
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    class Config:
        use_enum_values = True


# ========== 事件系統 Schema (Event System - 2026-01-25 新增) ==========

class EventContext(BaseModel):
    """事件上下文 - 來自新聞大腦的環境資訊
    
    用於對接「新聞判斷與記憶中樞」(RuleBasedEvaluator)，
    提供事件驅動的交易調整。
    
    遵循 Pydantic v2 最佳實踐：使用 BaseModel 而非 dataclass，
    以獲得完整的驗證、序列化和 JSON Schema 支援。
    
    最後更新: 2026-01-25
    
    Attributes:
        event_score: 環境評分 (-10 到 +10)，負值看空，正值看多
        event_type: 事件類型 (使用 EventType 枚舉或字串)
        intensity: 強度等級 (LOW/MEDIUM/HIGH/EXTREME)
        decay_factor: 衰減因子，表示事件影響的持續性 (0-1)
        source_confidence: 來源可信度 (0-1)
        affected_symbols: 受影響的交易對列表
        timestamp: 事件時間戳
    """
    event_score: float = Field(
        default=0.0, 
        ge=-10.0, 
        le=10.0, 
        description="環境評分：-10(極度看空) 到 +10(極度看多)"
    )
    event_type: Optional[str] = Field(
        default=None, 
        description="事件類型：WAR/HACK/REGULATION/MACRO/EARNINGS 等"
    )
    intensity: str = Field(
        default="MEDIUM", 
        description="強度等級：LOW/MEDIUM/HIGH/EXTREME"
    )
    decay_factor: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0, 
        description="衰減因子：1.0=完全生效，0.0=已失效"
    )
    source_confidence: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="來源可信度"
    )
    affected_symbols: List[str] = Field(
        default_factory=list, 
        description="受影響的交易對列表"
    )
    timestamp: Optional[datetime] = Field(
        default=None, 
        description="事件時間戳"
    )
    
    def get_effective_score(self) -> float:
        """計算有效評分 (考慮衰減和可信度)"""
        return self.event_score * self.decay_factor * self.source_confidence
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "event_score": -5.0,
                    "event_type": "HACK",
                    "intensity": "HIGH",
                    "decay_factor": 0.8,
                    "source_confidence": 0.9,
                    "affected_symbols": ["BTCUSDT", "ETHUSDT"],
                    "timestamp": "2026-01-25T10:30:00"
                }
            ]
        }


class EventRule(BaseModel):
    """事件規則定義 - 用於 RuleBasedEvaluator
    
    定義事件檢測規則，包含觸發關鍵字、終止關鍵字 (Hard Stop) 和評分參數。
    
    遵循 Pydantic v2 最佳實踐。
    
    最後更新: 2026-01-25
    
    Attributes:
        event_type: 事件類型識別碼
        trigger_keywords: 觸發關鍵字列表
        termination_keywords: 結束/Hard Stop 關鍵字列表
        base_score: 基礎分數 (-1.0 到 1.0，負=利空)
        decay_hours: 事件衰減時間 (小時)
        affected_symbols: 影響的交易對，None=全部
    """
    event_type: str = Field(
        ..., 
        description="事件類型：WAR, HACK, REGULATION, MACRO 等"
    )
    trigger_keywords: List[str] = Field(
        ..., 
        min_length=1,
        description="觸發關鍵字列表"
    )
    termination_keywords: List[str] = Field(
        default_factory=list, 
        description="結束/Hard Stop 關鍵字列表"
    )
    base_score: float = Field(
        ..., 
        ge=-1.0, 
        le=1.0, 
        description="基礎分數：-1.0(極度利空) 到 1.0(極度利多)"
    )
    decay_hours: int = Field(
        default=24, 
        ge=1, 
        le=720, 
        description="事件衰減時間 (小時)"
    )
    affected_symbols: Optional[List[str]] = Field(
        default=None, 
        description="影響的交易對，None=影響全部"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "event_type": "HACK",
                    "trigger_keywords": ["hack", "exploit", "breach", "stolen"],
                    "termination_keywords": ["recovered", "patched", "secured"],
                    "base_score": -0.8,
                    "decay_hours": 48,
                    "affected_symbols": None
                }
            ]
        }


# 導出清單
__all__ = [
    # 枚舉
    "RAGDocumentType",
    "RAGCheckResult",
    "RAGRiskFactor",
    "NewsSentiment",
    "NewsCategory",
    "SearchEngine",
    "RetrievalSource",
    
    # 模型
    "RAGRiskItem",
    "RAGNewsItem",
    "PreTradeCheckRequest",
    "PreTradeCheckResponse",
    "SearchResult",
    "RetrievalQuery",
    "RetrievalResult",
    "KnowledgeDocumentSchema",
    
    # 事件系統 (2026-01-25 新增)
    "EventContext",
    "EventRule",
]
