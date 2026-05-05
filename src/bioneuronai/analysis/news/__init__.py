"""
新聞分析模組
============

此模組提供加密貨幣新聞分析功能，包括：
- 新聞獲取 (CryptoPanic, RSS)
- 情緒分析
- 事件檢測
- 規則式評估
- 事件合約（時間維度影響力衰減）

主要類別：
- NewsArticle: 新聞文章數據類
- NewsAnalysisResult: 分析結果數據類
- CryptoNewsAnalyzer: 主要新聞分析器
- RuleBasedEvaluator: 規則式事件評估器
- NewsEventContract: 事件合約（衰減追蹤）
- NewsEventContractManager: 合約管理員

使用範例：
    from bioneuronai.analysis.news import (
        CryptoNewsAnalyzer,
        get_news_analyzer,
        RuleBasedEvaluator,
        get_rule_evaluator,
        NewsArticle,
        NewsAnalysisResult,
        NewsEventContract,
        NewsEventContractManager,
        get_contract_manager,
    )
    
    # 使用單例
    analyzer = get_news_analyzer()
    result = analyzer.analyze_news("BTCUSDT", hours=24)
    print(result.recommendation)
    
    # 規則評估（自動建立 NewsEventContract）
    evaluator = get_rule_evaluator()
    event = evaluator.evaluate_headline("Breaking: Exchange hacked!")
    
    # 取得衰減後的事件強度（供 Meta-Learner 使用）
    intensity = evaluator.get_aggregated_event_intensity("BTCUSDT")

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

# 事件合約（v2.2 Phase 1.2）
from .event_contract import (
    NewsEventContract,
    NewsEventContractManager,
    get_contract_manager,
    DECAY_EXPONENTIAL,
    DECAY_LINEAR,
    URGENCY_CRITICAL,
    URGENCY_HIGH,
    URGENCY_MEDIUM,
    URGENCY_LOW,
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
    # 事件合約（v2.2 Phase 1.2）
    "NewsEventContract",
    "NewsEventContractManager",
    "get_contract_manager",
    "DECAY_EXPONENTIAL",
    "DECAY_LINEAR",
    "URGENCY_CRITICAL",
    "URGENCY_HIGH",
    "URGENCY_MEDIUM",
    "URGENCY_LOW",
    # 預測循環
    "NewsPredictionLoop",  # ✅ 新增導出
]
