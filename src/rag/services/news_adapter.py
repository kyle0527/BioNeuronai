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
from pathlib import Path
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

# 導入 InternalKnowledgeBase（新聞知識寫入）
_imported_internal_kb: Optional[type[Any]]
try:
    from rag.internal import InternalKnowledgeBase as _imported_internal_kb
    INTERNAL_KB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"無法導入 InternalKnowledgeBase: {e}")
    INTERNAL_KB_AVAILABLE = False
    _imported_internal_kb = None

InternalKnowledgeBase = cast(Optional[type[Any]], _imported_internal_kb)


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
        knowledge_base: Optional[Any] = None,
        kb_storage_path: Optional[str] = None,
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
        self._knowledge_base = knowledge_base
        self._kb_storage_path = kb_storage_path
        
        # 延遲初始化
        self._initialized = False
        
        logger.info("NewsAdapter 已建立 (延遲初始化)")

    def _ensure_knowledge_base(self) -> Optional[Any]:
        """確保 InternalKnowledgeBase 已初始化"""
        if self._knowledge_base is not None:
            return self._knowledge_base

        if not INTERNAL_KB_AVAILABLE or InternalKnowledgeBase is None:
            logger.warning("InternalKnowledgeBase 不可用，跳過新聞入庫")
            return None

        try:
            storage_path = self._kb_storage_path
            if not storage_path:
                # 專案根目錄/data/bioneuronai/rag/internal
                project_root = Path(__file__).parent.parent.parent
                storage_path = str(project_root / "data" / "bioneuronai" / "rag" / "internal")

            self._knowledge_base = InternalKnowledgeBase(
                storage_path=storage_path,
                auto_load=True,
                use_faiss=False,  # 入庫路徑預設穩定優先
            )
            logger.info("✅ InternalKnowledgeBase 已初始化")
        except Exception as e:
            logger.error(f"InternalKnowledgeBase 初始化失敗: {e}")
            self._knowledge_base = None

        return self._knowledge_base
    
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
        """從查詢中提取幣種符號

        若傳入完整交易對（如 BTCUSDT），直接回傳，
        避免 Binance API 收到不完整 symbol 導致 400 錯誤。
        """
        query_upper = query.upper().strip()

        # 完整交易對直接回傳
        if query_upper.endswith("USDT") or query_upper.endswith("BUSD"):
            return query_upper

        # 常見幣種映射（關鍵字 → 完整交易對）
        coin_keywords = {
            "BTCUSDT": ["BTC", "BITCOIN"],
            "ETHUSDT": ["ETH", "ETHEREUM"],
            "BNBUSDT": ["BNB", "BINANCE"],
            "SOLUSDT": ["SOL", "SOLANA"],
            "XRPUSDT": ["XRP", "RIPPLE"],
        }

        for symbol, keywords in coin_keywords.items():
            for kw in keywords:
                if kw in query_upper:
                    return symbol

        # 其他情況補上 USDT 後綴
        first_word = query.split()[0].upper() if query else "BTC"
        return first_word + "USDT"
    
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
    
    def get_event_context(self, symbol: str) -> "Optional[EventContext]":
        """
        獲取事件上下文 - 供 strategy_fusion 使用
        
        Args:
            symbol: 交易對符號
            
        Returns:
            EventContext 物件，或 None
        """
        if not self._rule_evaluator or not SCHEMAS_AVAILABLE:
            return None
        
        try:
            # get_current_event_score 回傳 Tuple[float, List[Dict]]
            event_score, active_events = self._rule_evaluator.get_current_event_score(symbol)

            if not active_events:
                return None

            # 構建 EventContext 物件 (而非字典)
            primary_event = active_events[0] if active_events else {}

            return EventContext(
                event_score=event_score,
                event_type=primary_event.get("event_type"),
                intensity=self._score_to_intensity(event_score),
                decay_factor=1.0,
                source_confidence=0.7,
                affected_symbols=[symbol],
                timestamp=datetime.now(),
            )
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

    def ingest_news_analysis(
        self,
        analysis_result: Any,
        symbol: str = "BTCUSDT",
        hours: int = 24,
    ) -> int:
        """
        唯一新聞知識寫入服務入口（B.3）

        Args:
            analysis_result: NewsAnalysisResult 相容物件
            symbol: 交易對
            hours: 分析時間範圍

        Returns:
            寫入或更新的文檔數量
        """
        result = self.ingest_news_analysis_with_status(
            analysis_result=analysis_result,
            symbol=symbol,
            hours=hours,
        )
        return int(result.get("ingested_docs", 0) or 0)

    def ingest_news_analysis_with_status(
        self,
        analysis_result: Any,
        symbol: str = "BTCUSDT",
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        新聞知識入庫（含狀態）

        Returns:
            Dict[str, Any]:
            - status: OK / NO_DATA / ERROR
            - ingested_docs: int
            - message: str
        """
        kb = self._ensure_knowledge_base()
        if kb is None:
            return {
                "status": "ERROR",
                "ingested_docs": 0,
                "message": "InternalKnowledgeBase 不可用",
            }

        try:
            docs = kb.add_news_analysis(
                symbol=symbol,
                analysis_result=analysis_result,
                hours=hours,
                source="NewsAdapter",
                update_index=True,
            )
            if not docs:
                return {
                    "status": "NO_DATA",
                    "ingested_docs": 0,
                    "message": f"{symbol} 無可入庫的新聞資料",
                }
            kb.save_to_storage()
            logger.info(f"✅ 新聞知識入庫完成: {symbol} | docs={len(docs)}")
            return {
                "status": "OK",
                "ingested_docs": len(docs),
                "message": f"{symbol} 入庫成功",
            }
        except Exception as e:
            logger.error(f"新聞知識入庫失敗: {e}")
            return {
                "status": "ERROR",
                "ingested_docs": 0,
                "message": str(e),
            }


# 單例模式
_news_adapter_instance: Optional[NewsAdapter] = None


def get_news_adapter() -> NewsAdapter:
    """獲取 NewsAdapter 單例"""
    global _news_adapter_instance
    if _news_adapter_instance is None:
        _news_adapter_instance = NewsAdapter()
    return _news_adapter_instance


def ingest_news_analysis(
    analysis_result: Any,
    symbol: str = "BTCUSDT",
    hours: int = 24,
) -> int:
    """
    模組級唯一寫入函數（供 analysis 直接呼叫）
    """
    adapter = get_news_adapter()
    return adapter.ingest_news_analysis(
        analysis_result=analysis_result,
        symbol=symbol,
        hours=hours,
    )


def ingest_news_analysis_with_status(
    analysis_result: Any,
    symbol: str = "BTCUSDT",
    hours: int = 24,
) -> Dict[str, Any]:
    """
    模組級入庫函數（含狀態）
    """
    adapter = get_news_adapter()
    return adapter.ingest_news_analysis_with_status(
        analysis_result=analysis_result,
        symbol=symbol,
        hours=hours,
    )


__all__ = [
    "NewsAdapter",
    "NewsSearchResult",
    "get_news_adapter",
    "ingest_news_analysis",
    "ingest_news_analysis_with_status",
]
