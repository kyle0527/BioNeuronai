"""
新聞分析模組
============

此模組提供加密貨幣新聞分析功能，包括：
- 新聞獲取 (CryptoPanic, RSS)
- 情緒分析
- 事件檢測
- 規則式評估

主要類別：
- NewsArticle: 新聞文章數據類
- NewsAnalysisResult: 分析結果數據類
- CryptoNewsAnalyzer: 主要新聞分析器
- RuleBasedEvaluator: 規則式事件評估器

使用範例：
    from bioneuronai.analysis.news import (
        CryptoNewsAnalyzer,
        get_news_analyzer,
        RuleBasedEvaluator,
        get_rule_evaluator,
        NewsArticle,
        NewsAnalysisResult,
    )
    
    # 使用單例
    analyzer = get_news_analyzer()
    result = analyzer.analyze_news("BTCUSDT", hours=24)
    print(result.recommendation)
    
    # 規則評估
    evaluator = get_rule_evaluator()
    event = evaluator.evaluate_headline("Breaking: Exchange hacked!")

遵循 CODE_FIX_GUIDE.md 規範
"""

# 數據模型
from .models import NewsArticle, NewsAnalysisResult

# 新聞分析器
from .analyzer import (
    CryptoNewsAnalyzer,
    get_news_analyzer,
)

# 規則評估器
from .evaluator import (
    RuleBasedEvaluator,
    get_rule_evaluator,
    EventRule,
)

# 預測循環系統
from .prediction_loop import NewsPredictionLoop  # ✅ 從新位置導入

# 公開 API
__all__ = [
    # 數據模型
    "NewsArticle",
    "NewsAnalysisResult",
    # 分析器
    "CryptoNewsAnalyzer",
    "get_news_analyzer",
    # 評估器
    "RuleBasedEvaluator",
    "get_rule_evaluator",
    "EventRule",
    # 預測循環
    "NewsPredictionLoop",  # ✅ 新增導出
]
