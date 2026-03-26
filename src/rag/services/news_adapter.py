# -*- coding: utf-8 -*-
"""
新聞適配器 (News Adapter) - RAG 與 CryptoNewsAnalyzer 的橋接層
=============================================================

遵循 CODE_FIX_GUIDE.md 原則:
- Single Source of Truth: 使用 schemas 定義
- 修改現有模組: 將 CryptoNewsAnalyzer 包裝為 RAG 兼容接口

功能:
1. 將 CryptoNewsAnalyzer 的新聞結果轉換為 RAG RetrievalResult
2. 提供統一的新聞搜索接口供 UnifiedRetriever 使用
3. 整合 RuleBasedEvaluator 的事件檢測

使用範例:
    from rag.services.news_adapter import NewsAdapter
    
    adapter = NewsAdapter()
    results = adapter.search("BTCUSDT", hours=24)
    
    # 或與 UnifiedRetriever 整合
    from rag.core import UnifiedRetriever
    retriever = UnifiedRetriever(news_api=adapter)

Author: BioNeuronai Team
Date: 2026-01-25
"""

import logging
from typing import Any, Callable, Dict, List, Optional, cast
from datetime import datetime
from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# 從 schemas 導入 (Single Source of Truth)
try:
    from schemas.rag import (  # noqa: F401
        RAGNewsItem,
        NewsSentiment,
        NewsCategory,
        RetrievalSource,
        EventContext,
        EventRule,
    )
    SCHEMAS_AVAILABLE = True
except ImportError:
    logger.warning("無法從 schemas 導入 RAG 模型，使用內部定義")
    SCHEMAS_AVAILABLE = False

# 導入 CryptoNewsAnalyzer (從 bioneuronai 導入)
_imported_crypto_news_analyzer: Optional[type[Any]]
_imported_get_rule_evaluator: Optional[Callable[[], Any]]
try:
    from bioneuronai.analysis.news import (
        CryptoNewsAnalyzer as _imported_crypto_news_analyzer,
        NewsAnalysisResult,  # noqa: F401
        NewsArticle,  # noqa: F401
        get_rule_evaluator as _imported_get_rule_evaluator,
    )
    NEWS_ANALYZER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"無法導入 CryptoNewsAnalyzer: {e}")
    NEWS_ANALYZER_AVAILABLE = False
    _imported_crypto_news_analyzer = None
    _imported_get_rule_evaluator = None

CryptoNewsAnalyzer = cast(Optional[type[Any]], _imported_crypto_news_analyzer)
get_rule_evaluator = cast(Optional[Callable[[], Any]], _imported_get_rule_evaluator)
NewsSearchResult: TypeAlias = RAGNewsItem


class NewsAdapter:
    """
    新聞適配器 - RAG 統一檢索接口
    
    將 CryptoNewsAnalyzer 的功能封裝為 RAG 兼容的接口，
    供 UnifiedRetriever 使用。
    
    設計原則 (CODE_FIX_GUIDE.md):
    - 不重複定義已存在的類型，使用 schemas
    - 作為現有模組的包裝層，不修改核心邏輯
    """
    
    def __init__(
        self,
        enable_event_detection: bool = True,
        default_hours: int = 24,
    ):
        """
        初始化新聞適配器
        
        Args:
            enable_event_detection: 是否啟用事件檢測 (RuleBasedEvaluator)
            default_hours: 預設搜索時間範圍 (小時)
        """
        self._analyzer: Optional[Any] = None
        self._rule_evaluator = None
        self.enable_event_detection = enable_event_detection
        self.default_hours = default_hours
        
        # 延遲初始化
        self._initialized = False
        
        logger.info("NewsAdapter 已建立 (延遲初始化)")
    
    def _ensure_initialized(self):
        """確保分析器已初始化"""
        if self._initialized:
            return
        
        if not NEWS_ANALYZER_AVAILABLE:
            logger.error("CryptoNewsAnalyzer 不可用")
            return
        
        try:
            self._analyzer = CryptoNewsAnalyzer()
            logger.info("✅ CryptoNewsAnalyzer 已初始化")
            
            if self.enable_event_detection:
                try:
                    self._rule_evaluator = get_rule_evaluator()
                    logger.info("✅ RuleBasedEvaluator 已連接")
                except Exception as e:
                    logger.warning(f"RuleBasedEvaluator 初始化失敗: {e}")
            
            self._initialized = True
        except Exception as e:
            logger.error(f"NewsAdapter 初始化失敗: {e}")
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        hours: Optional[int] = None,
    ) -> List[NewsSearchResult]:
        """
        搜索新聞 - RAG 兼容接口
        
        這是供 UnifiedRetriever._retrieve_news() 調用的主要接口。
        
        Args:
            query: 搜索查詢 (通常是幣種符號如 "BTC")
            max_results: 最大返回結果數
            hours: 時間範圍 (小時)
            
        Returns:
            List[NewsSearchResult]: RAG 兼容的搜索結果
        """
        self._ensure_initialized()
        
        if not self._analyzer:
            logger.warning("分析器未初始化，返回空結果")
            return []
        
        hours = hours or self.default_hours
        
        # 從 query 提取幣種符號
        symbol = self._extract_symbol(query)
        
        try:
            # 使用 CryptoNewsAnalyzer 獲取新聞
            analysis = self._analyzer.analyze_news(symbol, hours=hours)
            
            results = []
            for article in analysis.articles[:max_results]:
                result = NewsSearchResult(
                    title=article.title,
                    summary=article.summary or article.title,
                    url=article.url,
                    source=article.source,
                    published_at=article.published_at,
                    relevance_score=self._calculate_relevance(article, query),
                    sentiment=cast(NewsSentiment, analysis.overall_sentiment),
                    sentiment_score=analysis.sentiment_score,
                    category=NewsCategory.GENERAL,
                )
                results.append(result)
                
                # 事件檢測
                if self._rule_evaluator and self.enable_event_detection:
                    self._check_for_events(article)
            
            logger.info(f"NewsAdapter: 找到 {len(results)} 篇新聞 (symbol={symbol})")
            return results
            
        except Exception as e:
            logger.error(f"新聞搜索失敗: {e}")
            return []
    
    def _extract_symbol(self, query: str) -> str:
        """從查詢中提取幣種符號"""
        # 常見幣種映射
        query_upper = query.upper()
        
        coin_keywords = {
            "BTC": ["BTC", "BITCOIN", "BTCUSDT"],
            "ETH": ["ETH", "ETHEREUM", "ETHUSDT"],
            "BNB": ["BNB", "BINANCE", "BNBUSDT"],
            "SOL": ["SOL", "SOLANA", "SOLUSDT"],
            "XRP": ["XRP", "RIPPLE", "XRPUSDT"],
        }
        
        for coin, keywords in coin_keywords.items():
            for kw in keywords:
                if kw in query_upper:
                    return coin
        
        # 嘗試從 XXXUSDT 格式提取
        if "USDT" in query_upper:
            return query_upper.replace("USDT", "").strip()
        
        # 默認返回原始查詢的第一個詞
        return query.split()[0] if query else "BTC"
    
    def _calculate_relevance(self, article: Any, query: str) -> float:
        """計算文章與查詢的相關性分數"""
        score = 0.5  # 基礎分數
        
        query_lower = query.lower()
        title_lower = article.title.lower() if article.title else ""
        
        # 標題包含關鍵字加分
        if query_lower in title_lower:
            score += 0.3
        
        # 基於來源權威度加分
        authority_sources = [
            "reuters", "bloomberg", "coindesk", "cointelegraph",
            "binance", "coinbase", "financial times"
        ]
        source_lower = article.source.lower() if article.source else ""
        if any(auth in source_lower for auth in authority_sources):
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_for_events(self, article: Any):
        """使用 RuleBasedEvaluator 檢測事件"""
        if not self._rule_evaluator:
            return
        
        try:
            headline = article.title or ""
            source = article.source or "unknown"
            
            # 調用 RuleBasedEvaluator 評估
            event_info = self._rule_evaluator.evaluate_headline(
                headline=headline,
                source=source,
                source_confidence=0.7  # 預設可信度
            )
            
            if event_info:
                logger.info(
                    f"🔔 檢測到事件: {event_info.get('event_type', 'UNKNOWN')} "
                    f"(score={event_info.get('score', 0):.2f})"
                )
        except Exception as e:
            logger.debug(f"事件檢測失敗: {e}")
    
    def get_event_context(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        獲取事件上下文 - 供 strategy_fusion 使用
        
        Args:
            symbol: 交易對符號
            
        Returns:
            EventContext 兼容的字典，或 None
        """
        if not self._rule_evaluator:
            return None
        
        try:
            event_score = self._rule_evaluator.get_total_event_score(symbol)
            active_events = self._rule_evaluator.get_active_events(symbol)
            
            if not active_events:
                return None
            
            # 構建 EventContext 兼容的返回值
            primary_event = active_events[0] if active_events else {}
            
            return {
                "event_score": event_score,
                "event_type": primary_event.get("event_type"),
                "intensity": self._score_to_intensity(event_score),
                "decay_factor": 1.0,  # 待從數據庫計算
                "source_confidence": 0.7,
                "affected_symbols": [symbol],
                "timestamp": datetime.now(),
            }
        except Exception as e:
            logger.error(f"獲取事件上下文失敗: {e}")
            return None
    
    def _score_to_intensity(self, score: float) -> str:
        """將分數轉換為強度等級"""
        abs_score = abs(score)
        if abs_score >= 7:
            return "EXTREME"
        elif abs_score >= 4:
            return "HIGH"
        elif abs_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"


# 單例模式
_news_adapter_instance: Optional[NewsAdapter] = None


def get_news_adapter() -> NewsAdapter:
    """獲取 NewsAdapter 單例"""
    global _news_adapter_instance
    if _news_adapter_instance is None:
        _news_adapter_instance = NewsAdapter()
    return _news_adapter_instance


__all__ = [
    "NewsAdapter",
    "NewsSearchResult",
    "get_news_adapter",
]
