"""
靜態工具類
==========

MarketKeywords - 靜態包裝類，提供方便的類方法接口

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
from typing import List, Tuple, Dict, Optional, Any

# 2. 本地模組
from .manager import get_keyword_manager
from .models import Keyword, KeywordMatch, PredictionRecord


class MarketKeywords:
    """
    靜態包裝類，提供方便的類方法接口
    
    使用方式:
        from analysis.keywords import MarketKeywords
        
        score, keywords = MarketKeywords.get_importance_score("BTC ETF 通過")
        sentiment, confidence = MarketKeywords.get_sentiment_bias("Fed升息")
    """
    
    @classmethod
    def get_instance(cls):
        """取得 KeywordManager 單例"""
        return get_keyword_manager()
    
    @classmethod
    def get_importance_score(cls, text: str) -> Tuple[float, List[str]]:
        """
        計算文本重要性評分
        
        Returns:
            (score, matched_keywords): 評分 (0-10) 和匹配到的關鍵字
        """
        return cls.get_instance().get_importance_score(text)
    
    @classmethod
    def get_sentiment_bias(cls, text: str) -> Tuple[str, float]:
        """
        分析文本情緒傾向
        
        Returns:
            (bias, confidence): 'positive'/'negative'/'neutral' 和信心值 (0-1)
        """
        return cls.get_instance().get_sentiment_bias(text)
    
    @classmethod
    def find_matches(cls, text: str) -> List[KeywordMatch]:
        """
        在文本中尋找匹配的關鍵字
        
        Returns:
            匹配到的關鍵字列表，按權重排序
        """
        return cls.get_instance().find_matches(text)
    
    @classmethod
    def is_high_impact_news(
        cls, 
        text: str, 
        threshold: float = 2.5
    ) -> Tuple[bool, List[str]]:
        """
        判斷是否為高影響力新聞
        
        Returns:
            (is_high_impact, high_impact_keywords)
        """
        return cls.get_instance().is_high_impact_news(text, threshold)
    
    @classmethod
    def add_keyword(
        cls,
        keyword: str,
        category: str,
        base_weight: float,
        sentiment_bias: str,
        description: str = "",
        subcategory: str = "general"
    ) -> bool:
        """
        新增關鍵字
        
        Args:
            keyword: 關鍵字
            category: 分類 (regulatory, technical, market, etc.)
            base_weight: 基礎權重 (0.5-3.0)
            sentiment_bias: 情緒傾向 (positive/negative/neutral)
            description: 描述
            subcategory: 子分類
        
        Returns:
            是否成功新增
        """
        return cls.get_instance().add_keyword(
            keyword, category, base_weight, 
            sentiment_bias, description, subcategory
        )
    
    @classmethod
    def remove_keyword(cls, keyword: str):
        """移除關鍵字"""
        cls.get_instance().remove_keyword(keyword)
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """
        獲取關鍵字統計資料
        
        Returns:
            包含 total, by_category, stale_count 等統計資訊
        """
        return cls.get_instance().get_statistics()
    
    @classmethod
    def get_keyword_count(cls) -> int:
        """獲取關鍵字總數"""
        return len(cls.get_instance().keywords)
    
    @classmethod
    def get_top_keywords(cls, n: int = 20) -> List[Keyword]:
        """獲取權重最高的 N 個關鍵字"""
        return cls.get_instance().get_top_keywords(n)
    
    @classmethod
    def record_prediction(
        cls,
        keyword: str,
        predicted_direction: str,
        price_before: float = 0.0,
        news_title: str = ""
    ) -> int:
        """記錄預測，返回預測 ID"""
        return cls.get_instance().record_prediction(
            keyword, predicted_direction, price_before, news_title
        )
    
    @classmethod
    def verify_prediction(
        cls,
        prediction_id: int,
        actual_direction: str,
        price_after: float = 0.0
    ) -> bool:
        """驗證預測，返回是否正確"""
        return cls.get_instance().verify_prediction(
            prediction_id, actual_direction, price_after
        )
    
    @classmethod
    def get_overall_accuracy(cls) -> Tuple[float, int, int]:
        """
        獲取整體準確率
        
        Returns:
            (accuracy, correct, total)
        """
        return cls.get_instance().get_overall_accuracy()
    
    @classmethod
    def get_keyword_performance(cls, min_predictions: int = 5) -> List[Dict]:
        """獲取關鍵字表現排名"""
        return cls.get_instance().get_keyword_performance(min_predictions)
    
    @classmethod
    def refresh_stale_keywords(cls) -> int:
        """重置過時關鍵字，返回重置數量"""
        return cls.get_instance().refresh_stale_keywords()
    
    @classmethod
    def update_from_trending(cls, trending_topics: List[Dict[str, Any]]) -> int:
        """從熱門話題更新關鍵字，返回新增數量"""
        return cls.get_instance().update_keywords_from_trending(trending_topics)
    
    @classmethod
    def print_report(cls):
        """印出統計報告"""
        cls.get_instance().print_report()
