"""
新聞情緒分析器
==============

負責執行 AI 新聞分析並整合結果

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import logging
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class NewsSentimentAnalyzer:
    """
    新聞情緒分析器
    
    功能：
    - 整合 CryptoNewsAnalyzer 結果
    - 提供 Mock 數據作為後備
    - 提取重要事件標籤
    """
    
    def __init__(self, news_analyzer=None):
        """
        Args:
            news_analyzer: CryptoNewsAnalyzer 實例（共享）
        """
        self.news_analyzer = news_analyzer
    
    def perform_ai_news_analysis(self, symbol: str = "BTCUSDT", hours: int = 24) -> Optional[Dict]:
        """
        執行 AI 新聞分析
        
        Args:
            symbol: 交易對符號
            hours: 分析時間範圍（小時）
        
        Returns:
            新聞分析結果字典
        """
        try:
            if self.news_analyzer is None:
                logger.warning("[WARN] 新聞分析器未初始化，使用 Mock 數據")
                return self._get_mock_news_data()
            
            # 從共享的新聞分析器獲取結果
            analysis = self.news_analyzer.analyze_news(symbol, hours=hours)
            
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
                "mock": False
            }
                
        except Exception as e:
            logger.error(f"執行新聞分析失敗: {e}")
            return None
    
    def _get_mock_news_data(self) -> Dict:
        """獲取 Mock 新聞數據"""
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "major_topics": ["市場整合中"],
            "key_events": [],
            "major_events": [],
            "recommendation": "觀望",
            "news_count": 0,
            "positive_count": 0,
            "negative_count": 0,
            "headlines": [],
            "mock": True
        }
    
    def _extract_major_events(self, analysis) -> list:
        """提取重大事件"""
        major_events = []
        
        # 從 key_events 提取
        for event in analysis.key_events:
            if isinstance(event, dict):
                event_type = event.get('type', 'general')
                description = event.get('description', '')
                
                major_events.append({
                    'type': event_type,
                    'description': description,
                    'timestamp': event.get('timestamp', datetime.now().isoformat())
                })
        
        return major_events
    
    def assess_market_status_from_news(self, news_analysis: Optional[Dict]) -> str:
        """
        根據新聞分析評估市場狀態
        
        Args:
            news_analysis: 新聞分析結果
        
        Returns:
            市場狀態 (BULLISH/BEARISH/NEUTRAL/UNKNOWN)
        """
        if news_analysis is None:
            return "UNKNOWN"
        
        sentiment_score = news_analysis.get('sentiment_score', 0.0)
        
        if sentiment_score > 0.3:
            return "BULLISH"
        elif sentiment_score < -0.3:
            return "BEARISH"
        else:
            return "NEUTRAL"
