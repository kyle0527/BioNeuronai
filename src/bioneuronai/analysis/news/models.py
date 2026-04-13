"""
新聞數據模型
==============

包含：
- NewsArticle - 新聞文章數據類
- NewsAnalysisResult - 新聞分析結果數據類

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class NewsArticle:
    """新聞文章數據類"""
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str = ""
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    # 文章分類
    category: str = "general"
    # 來源可信度
    source_credibility: float = 0.5
    # 提及的幣種
    coins_mentioned: List[str] = field(default_factory=list)
    # 重要性評分 (0-10)
    importance_score: float = 5.0
    # 與目標幣種相關性 (0-2)
    relevance_score: float = 1.0
    # 新聞發布時的價格
    price_at_news: float = 0.0
    # 目標幣種
    target_coin: str = ""


@dataclass
class NewsAnalysisResult:
    """新聞分析結果"""
    symbol: str
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    overall_sentiment: str  # positive/negative/neutral
    sentiment_score: float  # -1.0 到 1.0
    key_events: List[str]
    top_keywords: List[Tuple[str, int]]
    recent_headlines: List[str]
    recommendation: str
    analysis_time: datetime
    signal_valid_hours: int = 24
    signal_expires_at: Optional[datetime] = None
    signal_urgency: str = "medium"
    applicable_timeframes: List[str] = field(default_factory=list)
    articles: List[NewsArticle] = field(default_factory=list)
    
    def is_high_risk(self) -> bool:
        """判斷是否高風險"""
        danger_events = ['🔒 安全事件', '⚖️ 監管風險']
        return any(e in self.key_events for e in danger_events)
    
    def is_bullish(self) -> bool:
        """判斷是否看漲"""
        return self.sentiment_score > 0.2 and self.overall_sentiment == "positive"
    
    def is_bearish(self) -> bool:
        """判斷是否看跌"""
        return self.sentiment_score < -0.2 and self.overall_sentiment == "negative"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            'symbol': self.symbol,
            'total_articles': self.total_articles,
            'positive_count': self.positive_count,
            'negative_count': self.negative_count,
            'neutral_count': self.neutral_count,
            'overall_sentiment': self.overall_sentiment,
            'sentiment_score': self.sentiment_score,
            'key_events': self.key_events,
            'top_keywords': self.top_keywords,
            'recent_headlines': self.recent_headlines,
            'recommendation': self.recommendation,
            'analysis_time': self.analysis_time.isoformat(),
            'signal_valid_hours': self.signal_valid_hours,
            'signal_expires_at': self.signal_expires_at.isoformat() if self.signal_expires_at else None,
            'signal_urgency': self.signal_urgency,
            'applicable_timeframes': self.applicable_timeframes,
            'is_high_risk': self.is_high_risk(),
            'articles': [
                {
                    'title': a.title,
                    'source': a.source,
                    'url': a.url,
                    'sentiment': a.sentiment,
                    'published_at': a.published_at.isoformat(),
                    'importance_score': a.importance_score
                }
                for a in self.articles
            ]
        }
