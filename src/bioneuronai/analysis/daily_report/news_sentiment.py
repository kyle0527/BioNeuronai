"""
新聞情緒分析器
==============

負責執行 AI 新聞分析並整合結果

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class NewsSentimentAnalyzer:
    """
    新聞情緒分析器

    功能：
    - 整合 CryptoNewsAnalyzer 結果
    - 提取重要事件標籤

    角色定位：
    - 這是 daily_report 專用 adapter
    - 它負責把 CryptoNewsAnalyzer 的完整分析結果，整理成 SOP / 日報流程需要的簡化 dict
    - 它不負責 RAG 檢索介面，也不負責知識庫寫入；這些由 rag/services/news_adapter.py 負責
    """

    def __init__(self, news_analyzer):
        """
        Args:
            news_analyzer: CryptoNewsAnalyzer 實例（必須已初始化）

        Raises:
            RuntimeError: news_analyzer 為 None 時
        """
        if news_analyzer is None:
            raise RuntimeError("NewsSentimentAnalyzer 需要已初始化的 CryptoNewsAnalyzer 實例")
        self.news_analyzer = news_analyzer

    def perform_ai_news_analysis(
        self,
        symbol: str = "BTCUSDT",
        hours: Optional[int] = None,
    ) -> Dict:
        """
        執行 AI 新聞分析

        Args:
            symbol: 交易對符號
            hours: 分析時間範圍（小時）；None 表示使用分析器自適應時間窗

        Returns:
            新聞分析結果字典

        Raises:
            RuntimeError: 分析執行失敗時
        """
        try:
            analysis = self.news_analyzer.analyze_news(symbol, hours=hours)
        except Exception as e:
            raise RuntimeError(f"新聞分析執行失敗: {e}") from e

        logger.info(
            f"📰 [OK] 讀取新聞分析結果：{analysis.total_articles}篇，"
            f"情緒 {analysis.overall_sentiment}"
        )

        return {
            "sentiment": analysis.overall_sentiment,
            "sentiment_score": analysis.sentiment_score,
            "news_count": analysis.total_articles,
            "positive_count": analysis.positive_count,
            "negative_count": analysis.negative_count,
            "key_events": analysis.key_events,
            "recommendation": analysis.recommendation,
            "headlines": analysis.recent_headlines[:5],
            "major_events": self._extract_major_events(analysis),
            "last_update": datetime.now().isoformat(),
        }

    def _extract_major_events(self, analysis) -> list:
        """提取重大事件"""
        major_events = []

        for event in analysis.key_events:
            if isinstance(event, dict):
                major_events.append({
                    'type': event.get('type', 'general'),
                    'description': event.get('description', ''),
                    'timestamp': event.get('timestamp', datetime.now().isoformat())
                })

        return major_events

    def assess_market_status_from_news(self, news_analysis: Dict) -> str:
        """
        根據新聞分析評估市場狀態

        Args:
            news_analysis: 新聞分析結果（不可為 None）

        Returns:
            市場狀態 (BULLISH/BEARISH/NEUTRAL)

        Raises:
            RuntimeError: news_analysis 為 None 時
        """
        if news_analysis is None:
            raise RuntimeError("assess_market_status_from_news 收到 None，新聞分析必須先成功執行")

        sentiment_score = news_analysis.get('sentiment_score', 0.0)

        if sentiment_score > 0.3:
            return "BULLISH"
        elif sentiment_score < -0.3:
            return "BEARISH"
        else:
            return "NEUTRAL"
