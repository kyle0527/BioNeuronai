"""
新聞數據模型
==============

包含：
- NewsArticle - 新聞文章數據類
- NewsAnalysisResult - 新聞分析結果數據類

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
    # 正式來源與語言資料，供每小時 AI 快照與 tokenizer corpus 使用
    source_id: str = ""
    source_scope: str = ""
    language: str = ""


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
                    'source_id': a.source_id,
                    'source_scope': a.source_scope,
                    'language': a.language,
                    'summary': a.summary,
                    'sentiment': a.sentiment,
                    'published_at': a.published_at.isoformat(),
                    'importance_score': a.importance_score
                }
                for a in self.articles
            ]
        }

    def build_model_context(
        self,
        max_articles: int = 4,
        max_text_tokens: int = 128,
    ) -> str:
        """建立目前 unified_v2_100m 可直接接收的自然語言新聞脈絡。

        文字部分保留原本中英文標題／摘要，而不是把新聞壓成規則式分數或
        多空標籤。時間、來源與重要性等可精確量化的事實則同時保留在
        :meth:`to_ai_snapshot` 的結構化欄位。模型文字輸入上限為 128 tokens，
        因此先各保留至少一篇中文與英文的重要文章，再依重要性補足。
        """
        supported = [article for article in self.articles if article.language in {"zh", "en"}]
        ranked = sorted(
            supported,
            key=lambda article: (article.importance_score, article.published_at),
            reverse=True,
        )
        selected: List[NewsArticle] = []
        for language in ("zh", "en"):
            candidate = next((article for article in ranked if article.language == language), None)
            if candidate is not None:
                selected.append(candidate)
        for article in ranked:
            if len(selected) >= max_articles:
                break
            if article not in selected:
                selected.append(article)

        tokenizer = self._load_runtime_tokenizer()
        lines = [f"{self.symbol} news:"]
        for article in selected:
            content = " ".join(part for part in (article.title, article.summary) if part).strip()
            if article.language == "zh":
                prefix = "中文："
            else:
                prefix = "English: "
            for limit in (160, 100, 60, 30, 15, 8):
                candidate = "\n".join([*lines, prefix + content[:limit]])
                if self._token_count(tokenizer, candidate) <= max_text_tokens:
                    lines.append(prefix + content[:limit])
                    break
        if self.key_events:
            event_sentence = "Event labels: " + ", ".join(self.key_events)
            candidate = "\n".join([*lines, event_sentence])
            if self._token_count(tokenizer, candidate) <= max_text_tokens:
                lines.append(event_sentence)
        return "\n".join(lines)

    @staticmethod
    def _load_runtime_tokenizer() -> Any:
        """載入與 unified_v2_100m 同一份 tokenizer artifact。"""
        from nlp.bilingual_tokenizer import BilingualTokenizer

        tokenizer_path = Path(__file__).parents[4] / "model" / "tokenizer" / "vocab.json"
        return BilingualTokenizer.load(str(tokenizer_path))

    @staticmethod
    def _token_count(tokenizer: Any, text: str) -> int:
        return len(tokenizer.encode(text, add_special_tokens=True))

    def to_ai_snapshot(self, max_text_tokens: int = 128) -> dict[str, Any]:
        """輸出每小時 AI 輸入中屬於新聞模組的可持久化事實。"""
        from .event_contract import get_contract_manager

        now = datetime.now()
        active_contracts = get_contract_manager().get_active_contracts(
            symbol=self.symbol,
            at_time=now,
        )
        return {
            "symbol": self.symbol,
            "analysis_time": self.analysis_time.isoformat(),
            "news_articles": [
                {
                    "article_id": f"{article.source_id}:{article.url}",
                    "language": article.language,
                    "source_id": article.source_id,
                    "source_scope": article.source_scope,
                    "publisher": article.source,
                    "published_at": article.published_at.isoformat(),
                    "title": article.title,
                    "summary": article.summary,
                    "url": article.url,
                    "keyword_ids": article.keywords,
                    "importance": article.importance_score,
                }
                for article in self.articles
                if article.language in {"zh", "en"}
            ],
            "event_labels": self.key_events,
            "active_event_contracts": [
                {
                    "contract_id": contract.contract_id,
                    "event_type": contract.event_type,
                    "headline": contract.headline,
                    "created_at": contract.created_at.isoformat(),
                    "expires_at": contract.expires_at.isoformat(),
                    "initial_importance": contract.initial_importance,
                    "current_importance": contract.get_current_importance(now),
                    "minimum_importance": contract.minimum_importance,
                    "urgency": contract.urgency,
                    "decay_mode": contract.decay_mode,
                    "decay_rate_hours": contract.decay_rate,
                }
                for contract in active_contracts
            ],
            "model_context_text": self.build_model_context(max_text_tokens=max_text_tokens),
        }
