# -*- coding: utf-8 -*-
"""
統一檢索器 (Unified Retriever)
==============================

整合內部知識庫和外部搜索的統一檢索接口
"""

import hashlib
import logging
import time
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

# 導入監控（可選）
try:
    from ..monitoring import get_monitor
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    get_monitor = None


class RetrievalSource(Enum):
    """檢索來源"""
    INTERNAL_KNOWLEDGE = "internal_knowledge"   # 內部知識庫
    WEB_SEARCH = "web_search"                   # 網路搜索
    NEWS_API = "news_api"                       # 新聞 API
    SOCIAL_MEDIA = "social_media"              # 社交媒體
    HISTORICAL_DATA = "historical_data"        # 歷史數據
    TRADING_RULES = "trading_rules"            # 交易規則
    ALL = "all"                                 # 所有來源


@dataclass
class RetrievalResult:
    """檢索結果"""
    content: str
    source: RetrievalSource
    relevance_score: float          # 0-1 相關性分數
    timestamp: datetime
    url: Optional[str] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "source": self.source.value,
            "relevance_score": self.relevance_score,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
            "title": self.title,
            "metadata": self.metadata
        }


@dataclass
class RetrievalQuery:
    """檢索查詢"""
    query: str
    sources: List[RetrievalSource] = field(default_factory=lambda: [RetrievalSource.ALL])
    top_k: int = 10
    min_relevance: float = 0.3
    time_range_hours: Optional[int] = None  # 時間範圍限制
    filters: Dict[str, Any] = field(default_factory=dict)


class UnifiedRetriever:
    """
    統一檢索器
    
    整合多種數據源的檢索：
    - 內部知識庫 (向量搜索)
    - 外部網路搜索
    - 新聞 API
    - 社交媒體
    """
    
    def __init__(
        self,
        embedding_service=None,
        internal_kb=None,
        web_search=None,
        news_api=None,
        cache_ttl_seconds: int = 300
    ):
        self.embedding_service = embedding_service
        self.internal_kb = internal_kb
        self.web_search = web_search
        self.news_api = news_api
        self._cache: Dict[str, tuple] = {}  # key -> (results, expiry_time)
        self._cache_ttl = timedelta(seconds=cache_ttl_seconds)

        logger.info("統一檢索器已初始化")

    def _cache_key(self, query: "RetrievalQuery") -> str:
        """生成查詢的快取鍵"""
        key_parts = [
            query.query,
            ",".join(sorted(s.value for s in query.sources)),
            str(query.top_k),
            str(query.min_relevance),
            str(query.time_range_hours),
        ]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[List["RetrievalResult"]]:
        """從快取取得結果，若已過期則返回 None"""
        if cache_key in self._cache:
            results, expiry = self._cache[cache_key]
            if datetime.now() < expiry:
                return results
            del self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, results: List["RetrievalResult"]) -> None:
        """將結果存入快取"""
        self._cache[cache_key] = (results, datetime.now() + self._cache_ttl)
    
    def retrieve(self, query: Union[str, RetrievalQuery]) -> List[RetrievalResult]:
        """
        執行檢索
        
        Args:
            query: 查詢字符串或 RetrievalQuery 對象
            
        Returns:
            List[RetrievalResult] 檢索結果列表
        """
        start_time = time.time()
        error = None
        result_count = 0
        sources_used = []
        cache_hit = False

        try:
            if isinstance(query, str):
                query = RetrievalQuery(query=query)

            # 快取檢測
            cache_key = self._cache_key(query)
            cached_results = self._get_cached(cache_key)
            if cached_results is not None:
                cache_hit = True
                result_count = len(cached_results)
                return cached_results

            results = []

            # 根據指定來源檢索
            sources = query.sources
            if RetrievalSource.ALL in sources:
                sources = [
                    RetrievalSource.INTERNAL_KNOWLEDGE,
                    RetrievalSource.WEB_SEARCH,
                    RetrievalSource.NEWS_API
                ]

            sources_used = [s.value for s in sources]

            for source in sources:
                try:
                    source_results = self._retrieve_from_source(query, source)
                    results.extend(source_results)
                except Exception as e:
                    logger.warning(f"從 {source.value} 檢索失敗: {e}")

            # 按相關性排序
            results.sort(key=lambda x: x.relevance_score, reverse=True)

            # 過濾低相關性結果
            results = [r for r in results if r.relevance_score >= query.min_relevance]

            # 限制返回數量
            results = results[:query.top_k]
            result_count = len(results)

            # 存入快取
            self._set_cache(cache_key, results)

            return results

        except Exception as e:
            error = str(e)
            logger.error(f"檢索失敗: {e}")
            return []

        finally:
            # 記錄監控指標
            latency_ms = (time.time() - start_time) * 1000
            if MONITORING_AVAILABLE and get_monitor is not None:
                try:
                    monitor = get_monitor()
                    source_label = "hybrid" if len(sources_used) > 1 else (sources_used[0] if sources_used else "unknown")
                    monitor.log_retrieval(
                        latency_ms=latency_ms,
                        cache_hit=cache_hit,
                        result_count=result_count,
                        source=source_label,
                        error=error
                    )
                except Exception as mon_error:
                    logger.debug(f"監控記錄失敗: {mon_error}")
    
    def _retrieve_from_source(
        self,
        query: RetrievalQuery,
        source: RetrievalSource
    ) -> List[RetrievalResult]:
        """從特定來源檢索"""
        
        if source == RetrievalSource.INTERNAL_KNOWLEDGE:
            return self._retrieve_internal(query)
        elif source == RetrievalSource.WEB_SEARCH:
            return self._retrieve_web(query)
        elif source == RetrievalSource.NEWS_API:
            return self._retrieve_news(query)
        elif source == RetrievalSource.TRADING_RULES:
            return self._retrieve_trading_rules(query)
        else:
            return []
    
    def _retrieve_internal(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """從內部知識庫檢索"""
        if not self.internal_kb:
            return []
        
        try:
            docs = self.internal_kb.search(
                query=query.query,
                top_k=query.top_k,
                min_score=query.min_relevance
            )
            return [
                RetrievalResult(
                    content=doc.content,
                    source=RetrievalSource.INTERNAL_KNOWLEDGE,
                    relevance_score=doc.score,
                    timestamp=doc.created_at,
                    title=doc.title,
                    metadata=doc.metadata
                )
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"內部檢索錯誤: {e}")
            return []
    
    def _retrieve_web(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """從網路搜索檢索"""
        if not self.web_search:
            return []
        
        try:
            results = self.web_search.search(
                query=query.query,
                num_results=query.top_k,
                time_range_hours=query.time_range_hours
            )
            return [
                RetrievalResult(
                    content=r.snippet,
                    source=RetrievalSource.WEB_SEARCH,
                    relevance_score=r.relevance_score,
                    timestamp=r.published_at or datetime.now(),
                    url=r.url,
                    title=r.title,
                    metadata={"domain": r.domain}
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"網路搜索錯誤: {e}")
            return []
    
    def _retrieve_news(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """從新聞 API 檢索"""
        if not self.news_api:
            return []
        
        try:
            articles = self.news_api.search(
                query=query.query,
                max_results=query.top_k,
                hours=query.time_range_hours or 24
            )
            return [
                RetrievalResult(
                    content=article.summary or article.title,
                    source=RetrievalSource.NEWS_API,
                    relevance_score=article.relevance_score,
                    timestamp=article.published_at,
                    url=article.url,
                    title=article.title,
                    metadata={
                        "source_name": article.source,
                        "sentiment": article.sentiment
                    }
                )
                for article in articles
            ]
        except Exception as e:
            logger.error(f"新聞檢索錯誤: {e}")
            return []
    
    def _retrieve_trading_rules(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """從交易規則庫檢索"""
        # 這裡可以連接到專門的交易規則知識庫
        return []
    
    def retrieve_for_trading(
        self,
        symbol: str,
        context: str = "",
        include_news: bool = True,
        include_web: bool = True,
        time_hours: int = 24
    ) -> Dict[str, List[RetrievalResult]]:
        """
        針對交易決策的專門檢索
        
        Args:
            symbol: 交易對符號 (如 BTCUSDT)
            context: 額外上下文
            include_news: 是否包含新聞
            include_web: 是否包含網路搜索
            time_hours: 時間範圍
            
        Returns:
            分類的檢索結果
        """
        base_symbol = symbol.replace("USDT", "").replace("BUSD", "")
        
        # 構建查詢
        queries = {
            "market_news": f"{base_symbol} cryptocurrency news price",
            "sentiment": f"{base_symbol} crypto market sentiment analysis",
            "events": f"{base_symbol} upcoming events announcements",
        }
        
        if context:
            queries["context"] = f"{base_symbol} {context}"
        
        results = {}
        sources = []
        if include_news:
            sources.append(RetrievalSource.NEWS_API)
        if include_web:
            sources.append(RetrievalSource.WEB_SEARCH)
        sources.append(RetrievalSource.INTERNAL_KNOWLEDGE)
        
        for category, q in queries.items():
            query = RetrievalQuery(
                query=q,
                sources=sources,
                top_k=5,
                time_range_hours=time_hours
            )
            results[category] = self.retrieve(query)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            "embedding_service": self.embedding_service is not None,
            "internal_kb": self.internal_kb is not None,
            "web_search": self.web_search is not None,
            "news_api": self.news_api is not None
        }
