"""分析模組 (Analysis Module)
===================================

BioNeuronai 加密貨幣市場分析工具集，提供完整的數據分析與決策支持功能。

主要子模組：

1. 每日市場報告 (daily_report)
   - SOPAutomationSystem: 標準操作流程自動化
   - MarketEnvironmentCheck: 市場環境檢查
   - DailyReport: 綜合市場分析報告

2. 關鍵字系統 (keywords)
   - KeywordManager: 關鍵字數據庫管理
   - MarketKeywords: 智能關鍵字識別
   - 多語言關鍵字匹配與趨勢分析

3. 新聞分析 (news)
   - CryptoNewsAnalyzer: 新聞抓取與情緒分析
   - RuleBasedEvaluator: 規則評估器
   - 支援多來源新聞整合與實時情緒追蹤

4. 特徵工程 (feature_engineering)
   - VolumeProfile: 成交量分布分析
   - LiquidationHeatmap: 清算風險評估
   - MarketMicrostructure: 市場微觀結構分析

5. 市場狀態識別 (market_regime)
   - MarketRegimeDetector: 牛熊市判斷
   - RegimeAnalysis: 狀態轉換檢測
   - 波動性分析與策略選擇

使用範例：
    from bioneuronai.analysis import CryptoNewsAnalyzer, MarketKeywords, DailyReport
    
    # 新聞分析
    news_analyzer = CryptoNewsAnalyzer()
    result = news_analyzer.analyze_news("BTCUSDT")
    
    # 關鍵字匹配
    keyword_manager = MarketKeywords()
    matches = keyword_manager.find_matches("Bitcoin ETF approved")
    
    # 生成每日報告
    report = DailyReport()
    daily_analysis = report.generate_report("BTCUSDT")

Author: BioNeuronai Team
Version: 1.0
"""


# 每日報告 (從 daily_report/ 子模組導入)
from .daily_report import (
    SOPAutomationSystem,
    MarketEnvironmentCheck,
    TradingPlanCheck,
    DailyMarketCondition,
    StrategyPerformance,
    DailyRiskLimits,
    TradingPairsPriority,
    DailyReport,
)

# 關鍵字系統 (從 keywords/ 子模組導入)
from .keywords import (
    Keyword,
    KeywordMatch,
    PredictionRecord,
    KeywordLoader,
    KeywordManager,
    get_keyword_manager,
    MarketKeywords,
    KeywordLearner,  # ✅ 從 learner.py 導入
)

# 新聞分析 (從 news/ 子模組導入)
from .news import (
    CryptoNewsAnalyzer,
    NewsArticle,
    NewsAnalysisResult,
    get_news_analyzer,
    RuleBasedEvaluator,
    get_rule_evaluator,
    NewsPredictionLoop,  # ✅ 從 prediction_loop.py 導入
)

# 
from .feature_engineering import (
    VolumeProfile,
    VolumeProfileLevel,
    VolumeProfileCalculator,
    LiquidationCluster,
    LiquidationHeatmap,
    LiquidationHeatmapCalculator,
    MarketMicrostructure,
    MarketDataProcessor,
)

# 市場狀態
from .market_regime import (
    MarketRegime,
    VolatilityRegime,
    TrendStrength,
    RegimeAnalysis,
    MarketRegimeDetector,
    RegimeBasedStrategySelector,
)

__all__ = [
    # 每日報告
    'SOPAutomationSystem',
    'MarketEnvironmentCheck',
    'TradingPlanCheck',
    'DailyMarketCondition',
    'StrategyPerformance',
    'DailyRiskLimits',
    'TradingPairsPriority',
    'DailyReport',
    
    # 關鍵字系統
    'Keyword',
    'KeywordMatch',
    'PredictionRecord',
    'KeywordLoader',
    'KeywordManager',
    'get_keyword_manager',
    'MarketKeywords',
    'KeywordLearner',  # ✅ 新增導出
    
    # 新聞分析
    'CryptoNewsAnalyzer',
    'NewsArticle',
    'NewsAnalysisResult',
    'get_news_analyzer',
    'RuleBasedEvaluator',
    'NewsPredictionLoop',  # ✅ 新增導出
    'get_rule_evaluator',
    
    # 特徵工程
    'VolumeProfile',
    'VolumeProfileLevel',
    'VolumeProfileCalculator',
    'LiquidationCluster',
    'LiquidationHeatmap',
    'LiquidationHeatmapCalculator',
    'MarketMicrostructure',
    'MarketDataProcessor',
    
    # 市場狀態
    'MarketRegime',
    'VolatilityRegime',
    'TrendStrength',
    'RegimeAnalysis',
    'MarketRegimeDetector',
    'RegimeBasedStrategySelector',
]
