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
]
