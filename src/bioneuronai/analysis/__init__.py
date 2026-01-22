"""分析模組 (Analysis Module)
===================================

BioNeuronai 加密貨幣市場分析工具集，提供完整的數據分析與決策支持功能。

主要子模組：

1. 新聞情緒分析 (news_analyzer)
   - CryptoNewsAnalyzer: 新聞抓取與情緒分析
   - 支援多來源新聞整合
   - 實時情緒追蹤

2. 市場關鍵字匹配 (market_keywords)
   - MarketKeywords: 智能關鍵字識別
   - 多語言支持
   - 實體與事件提取

3. 特徵工程 (feature_engineering)
   - VolumeProfile: 成交量分布分析
   - LiquidationHeatmap: 清算風險評估
   - MarketDataProcessor: 數據處理與特徵提取

4. 市場狀態識別 (market_regime)
   - MarketRegimeDetector: 牛熊市判斷
   - 狀態轉換檢測
   - 波動性分析

5. 每日市場報告 (daily_market_report)
   - DailyMarketReportGenerator: 自動生成分析報告
   - 整合所有分析模組
   - 提供交易建議

使用範例：
    from bioneuronai.analysis import CryptoNewsAnalyzer, MarketKeywords
    
    # 新聞分析
    news_analyzer = CryptoNewsAnalyzer()
    result = news_analyzer.analyze_news("BTCUSDT")
    
    # 關鍵字匹配
    keyword_manager = MarketKeywords()
    matches = keyword_manager.find_matches("Bitcoin ETF approved")

Author: BioNeuronai Team
Version: 1.0
"""


from .news_analyzer import (
    CryptoNewsAnalyzer,
    NewsArticle,
    NewsAnalysisResult,
    get_news_analyzer
)
from .market_keywords import MarketKeywords, KeywordMatch

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

# 
from .market_regime import (
    MarketRegime,
    VolatilityRegime,
    TrendStrength,
    RegimeAnalysis,
    MarketRegimeDetector,
    RegimeBasedStrategySelector,
)

__all__ = [
    # 
    'CryptoNewsAnalyzer',
    'NewsArticle',
    'NewsAnalysisResult',
    'get_news_analyzer',
    'MarketKeywords',
    'KeywordMatch',
    
    # 
    'VolumeProfile',
    'VolumeProfileLevel',
    'VolumeProfileCalculator',
    'LiquidationCluster',
    'LiquidationHeatmap',
    'LiquidationHeatmapCalculator',
    'MarketMicrostructure',
    'MarketDataProcessor',
    
    # 
    'MarketRegime',
    'VolatilityRegime',
    'TrendStrength',
    'RegimeAnalysis',
    'MarketRegimeDetector',
    'RegimeBasedStrategySelector',
]
