# Analysis 分析模組 v4.0

> **更新日期**: 2026-02-14  
> **版本**: v4.0 (策略進化系統完成)  
> **遵循規範**: CODE_FIX_GUIDE.md

BioNeuronAI 加密貨幣市場分析工具集，提供完整的新聞情緒分析、市場關鍵字識別、特徵工程、市場狀態檢測和每日報告生成功能。

## 📋 模組概述

Analysis 模組是 BioNeuronAI 系統的核心分析服務，整合多種先進的市場分析技術，為 AI 交易決策提供數據支持。

---

## 🏗️ 模組結構（v2.1 架構）

```
src/bioneuronai/analysis/
├── __init__.py                     # 統一導出接口
│
├── news/                           # ✅ 新聞分析模組
│   ├── __init__.py
│   ├── models.py                  # 新聞數據模型
│   ├── analyzer.py                # 新聞分析器
│   ├── evaluator.py               # 規則評估器
│   └── prediction_loop.py         # ✅ 預測循環系統（已移動）
│
├── keywords/                       # ✅ 關鍵字系統模組
│   ├── __init__.py
│   ├── models.py                  # 關鍵字數據模型
│   ├── manager.py                 # 關鍵字管理器
│   ├── loader.py                  # 關鍵字載入器
│   ├── static_utils.py            # 靜態工具函數
│   └── learner.py                 # ✅ 關鍵字學習器（已移動）
│
├── daily_report/                   # 每日報告模組
│   ├── __init__.py
│   ├── market_data.py             # 市場數據分析
│   ├── news_sentiment.py          # 新聞情緒整合
│   ├── report_generator.py        # 報告生成器
│   ├── risk_manager.py            # 風險管理
│   └── strategy_planner.py        # 策略規劃
│
├── feature_engineering.py          # 特徵工程
└── market_regime.py                # 市場狀態檢測
```

### 🔄 v2.1 架構變更

**主要改進**（2026-01-30）：
1. ✅ 將 `news_prediction_loop.py` 移入 `news/` 子模組
2. ✅ 將 `keyword_learner.py` 移入 `keywords/` 子模組
3. ✅ 修復所有導入路徑
4. ✅ 修復 `keywords/manager.py` 中的屬性錯誤（`keyword` → `word`）
5. ✅ 統一模組化結構，清晰的職責劃分

**架構原則**：
- **數據層**: `news/`, `keywords/` - 數據獲取和基礎分析
- **整合層**: `daily_report/` - 多源數據彙總和報告
- **單一職責**: 每個子模組專注一個核心功能
- **高內聚低耦合**: 清晰的模組邊界和導入路徑

---

## 🎯 主要組件

### 1. Daily Report 模組 (每日報告)

#### DailyReport (每日市場報告)
自動生成綜合市場分析報告，整合所有分析模組的數據。

**主要功能：**
- 市場環境檢查與評估
- 交易計劃自動審核
- 策略績效統計分析
- 風險參數動態監控
- 交易對優先級排序

#### SOPAutomationSystem (SOP 自動化系統)
標準操作流程自動化執行系統，確保交易流程規範化。

### 2. News 模組 (新聞分析) ✅

#### CryptoNewsAnalyzer (新聞分析器)
基於多層次情緒分析的新聞分析系統，支持實時新聞抓取和多維度情緒評估。

**主要功能：**
- 實時新聞抓取（多個來源）
- 多維度情緒分析（情緒、緊急度、影響力）
- 市場關鍵字識別
- 新聞去重和排序
- 分幣種情緒統計

**新聞來源：**
- CoinDesk, CoinTelegraph, Decrypt
- The Block, Bitcoin.com
- 多個 RSS 來源整合

**導入路徑** (v2.1):
```python
from bioneuronai.analysis.news import CryptoNewsAnalyzer, NewsPredictionLoop
```

#### RuleBasedEvaluator (規則評估器)
基於規則的新聞評估系統，提供快速的情緒分類和影響力評估。

#### NewsPredictionLoop (預測循環) ✅ v2.1 新位置
RLHF 預測循環系統，用於驗證新聞預測準確性並調整關鍵字權重。

**核心功能：**
- 智能品種選擇（基於成交量和新聞數量）
- 時間衰減模型（24 小時追蹤）
- 自動驗證預測結果
- 關鍵字權重動態調整

**文件位置**: `src/bioneuronai/analysis/news/prediction_loop.py`

---

### 3. Keywords 模組 (關鍵字系統) ✅

#### Keyword (關鍵字模型)
關鍵字數據結構，包含：
- `word`: 關鍵字文本 (⚠️ 注意：屬性名為 `word`，非 `keyword`)
- `category`: 分類（person, institution, event, coin, etc.）
- `base_weight`: 基礎權重 1.0-3.0
- `dynamic_weight`: 動態權重
- `sentiment_bias`: 情緒傾向
- 統計數據：命中次數、預測準確率等

**導入路徑** (v2.1):
```python
from bioneuronai.analysis.keywords import Keyword, KeywordManager, KeywordLearner
```

#### KeywordManager (關鍵字管理器) ✅ v2.1 已修復
關鍵字數據庫管理和預測記錄系統。

**主要功能：**
- 關鍵字匹配與權重計算
- SQLite 數據庫持久化
- 預測記錄管理
- 權重動態調整
- 過時關鍵字刷新

**v2.1 修復**:
- ✅ 修正所有 `keyword` 屬性為 `word`（遵循 Keyword 模型定義）
- ✅ 修復導入錯誤，確保類型提示正確

#### KeywordLearner (關鍵字學習器) ✅ v2.1 新位置
基於 RLHF 的關鍵字權重學習系統。

**核心功能：**
- 從預測記錄學習權重
- 動態調整關鍵字影響力
- 準確率追蹤和優化

**文件位置**: `src/bioneuronai/analysis/keywords/learner.py`

---

### 4. Daily Report 模組 (每日報告)

**職責**: 整合多源數據生成綜合市場分析報告（宏觀層面）

#### DailyReport (每日市場報告)
自動生成綜合市場分析報告。

**報告內容：**
- 市場環境檢查
- 交易計劃評估
- 策略績效分析
- 風險參數監控
- 交易對優先級排序

#### Newssentiment (新聞情緒整合)
整合新聞分析模組的數據，生成整體市場情緒評估。

**與 news/ 模組的關係**：
- `news/analyzer.py`: 微觀層面 - 單條新聞分析
- `daily_report/news_sentiment.py`: 宏觀層面 - 整合多源數據

#### SOPAutomationSystem (SOP 自動化系統)
標準操作流程自動化執行系統。

---

### 5. Feature Engineering 模組 (特徵工程)

#### VolumeProfile (成交量分布分析)
識別關鍵價格區間與成交量集中點，提供價值區域分析。

**功能：**
- POC (Point of Control) 識別
- 價值區域 (Value Area) 計算
- 支撐/阻力位檢測
- 多時間週期分析

#### LiquidationHeatmap (清算熱力圖)
預測潛在清算集中區域，識別高槓桿部位風險。

**功能：**
- 清算風險評估
- 多空力量對比
- 高風險區域識別
- 槓桿分析

#### MarketMicrostructure (市場微觀結構)
市場數據處理器，提供技術指標和特徵工程。

**特徵類型：**
- 技術指標 (RSI, MACD, Bollinger Bands)
- 價格特徵 (收益率, 波動率)
- 成交量特徵
- 時間特徵
- 訂單簿特徵

### 6. Market Regime 模組 (市場狀態檢測)

#### MarketRegimeDetector (市場狀態檢測器)
基於統計模型的市場狀態自動識別系統。

**市場狀態：**
- 牛市 (Bullish) - 持續上漲趨勢
- 熊市 (Bearish) - 持續下跌趨勢
- 震盪市 (Ranging) - 橫盤整理
- 高波動 (High Volatility) - 劇烈波動期

#### RegimeAnalysis (狀態分析)
多維度市場特徵整合分析。

**分析維度：**
- 波動性分析
- 趨勢強度評估
- 成交量模式識別
- 價格動能分析

#### RegimeBasedStrategySelector (狀態策略選擇器)
基於市場狀態的交易策略自動選擇。

#### DailyReport (每日市場報告)
自動生成綜合市場分析報告。

**報告內容：**
- 市場環境檢查
- 交易計劃評估
- 策略績效分析
- 風險參數監控
- 交易對優先級排序

#### SOPAutomationSystem (SOP 自動化系統)
標準操作流程自動化執行系統。

## 📦 導出 API (v2.1)

```python
from bioneuronai.analysis import (
    # ✅ 新聞分析（news/）
    CryptoNewsAnalyzer,
    NewsArticle,
    NewsAnalysisResult,
    NewsPredictionLoop,        # ✅ v2.1 新增
    get_news_analyzer,
    RuleBasedEvaluator,
    get_rule_evaluator,
    
    # ✅ 關鍵字系統（keywords/）
    Keyword,                    # ⚠️ 屬性為 word，非 keyword
    KeywordMatch,
    PredictionRecord,
    KeywordLoader,
    KeywordManager,             # ✅ v2.1 已修復
    KeywordLearner,             # ✅ v2.1 新增
    get_keyword_manager,
    
    # 特徵工程
    VolumeProfile,
    VolumeProfileLevel,
    VolumeProfileCalculator,
    LiquidationCluster,
    LiquidationHeatmap,
    LiquidationHeatmapCalculator,
    MarketMicrostructure,
    MarketDataProcessor,
    
    # 市場狀態
    MarketRegime,
    VolatilityRegime,
    TrendStrength,
    RegimeAnalysis,
    MarketRegimeDetector,
    RegimeBasedStrategySelector,
    
    # 每日報告
    SOPAutomationSystem,
    MarketEnvironmentCheck,
    TradingPlanCheck,
    MarketCondition,
    StrategyPerformance,
    RiskParameters,
    TradingPairsPriority,
    DailyReport,
)
```

### ⚠️ v2.1 重要變更

**新的導入路徑**:
```python
# ✅ 正確（v2.1）
from bioneuronai.analysis.news import NewsPredictionLoop
from bioneuronai.analysis.keywords import KeywordLearner

# ❌ 已廢棄（v2.0）
from bioneuronai.analysis.news_prediction_loop import NewsPredictionLoop
from bioneuronai.analysis.keyword_learner import KeywordLearner
```

**關鍵字模型屬性**:
```python
# ✅ 正確
keyword = Keyword(word="bitcoin", category="coin", ...)
print(keyword.word)  # "bitcoin"

# ❌ 錯誤（v2.0 遺留問題已修復）
print(keyword.keyword)  # AttributeError
```

---

## 🔗 依賴關係

**被依賴於：**
- `core.TradingEngine` - 用於交易決策
- `automation.SOPAutomation` - SOP 流程分析
- `automation.PreTradeAutomation` - 交易前檢查
- `core.InferenceEngine` - AI 特徵輸入

## 🔗 依賴關係

**被依賴於：**
- `core.TradingEngine` - 用於交易決策
- `automation.SOPAutomation` - SOP 流程分析
- `automation.PreTradeAutomation` - 交易前檢查
- `core.InferenceEngine` - AI 特徵輸入

**外部依賴：**
- `numpy` - 數值計算
- `pandas` - 數據處理
- `scikit-learn` - 機器學習
- `requests` - HTTP 請求
- `beautifulsoup4` - HTML 解析
- `feedparser` - RSS 解析

---

## 🎨 架構設計 (v2.1)

```
analysis/
├── news/                   # ✅ 新聞分析模組
│   ├── __init__.py        
│   ├── models.py          # 新聞數據模型
│   ├── analyzer.py        # 核心新聞分析器
│   ├── evaluator.py       # 規則評估器
│   └── prediction_loop.py # ✅ 預測循環（已移動）
│
├── keywords/               # ✅ 關鍵字系統
│   ├── __init__.py        
│   ├── models.py          # 關鍵字數據模型
│   ├── manager.py         # ✅ 關鍵字管理器（已修復）
│   ├── loader.py          # 關鍵字載入器
│   ├── static_utils.py    # 靜態工具函數
│   └── learner.py         # ✅ 關鍵字學習器（已移動）
│
├── daily_report/           # 每日報告生成
│   ├── __init__.py        
│   ├── models.py          # 數據模型定義
│   ├── market_data.py     # 市場數據分析
│   ├── news_sentiment.py  # 新聞情緒整合（宏觀層）
│   ├── report_generator.py # 報告生成器
│   ├── risk_manager.py    # 風險評估
│   └── strategy_planner.py # 策略規劃
│
├── __init__.py            # 統一導出接口
├── feature_engineering.py # 特徵工程
├── market_regime.py       # 市場狀態檢測
└── README.md              # 本說明文件
```

### 🔄 與 v2.0 的差異

**已移除**（已移入子模組）:
- ~~`keyword_learner.py`~~ → `keywords/learner.py`
- ~~`news_prediction_loop.py`~~ → `news/prediction_loop.py`

**已修復**:
- ✅ `keywords/manager.py`: 所有 `keyword` 屬性改為 `word`

---

## 📊 數據模型

### NewsArticle (新聞文章)
```python
@dataclass
class NewsArticle:
    title: str              # 標題
    url: str                # 網址
    source: str             # 來源
    published_time: datetime  # 發布時間
    content: str            # 內容
    summary: str            # 摘要
```

### NewsAnalysisResult (分析結果)
```python
@dataclass
class NewsAnalysisResult:
    sentiment_score: float        # 情緒分數 (-1 到 1)
    impact_level: str            # 影響級別 (HIGH/MEDIUM/LOW)
    urgency: str                 # 緊急度
    related_symbols: List[str]   # 相關幣種
    keywords: List[str]          # 關鍵字
    category: str                # 分類
```

### VolumeProfileLevel (成交量等級)
```python
@dataclass
class VolumeProfileLevel:
    price: float            # 價格等級
    volume: float           # 成交量
    is_poc: bool           # 是否為 POC
    is_value_area: bool    # 是否在價值區域
```

## 🔧 配置說明

```python
# 新聞來源配置
NEWS_SOURCES = {
    'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'cointelegraph': 'https://cointelegraph.com/rss',
    'decrypt': 'https://decrypt.co/feed',
}

# 特徵工程配置
FEATURE_CONFIG = {
    'volume_profile_bins': 50,      # 成交量分布區間數
    'liquidation_levels': 10,       # 清算熱力圖等級
    'technical_indicators': [       # 技術指標列表
        'rsi', 'macd', 'bollinger', 'volume_sma'
    ]
}

# 市場狀態配置
REGIME_CONFIG = {
    'volatility_window': 20,        # 波動率計算窗口
    'trend_window': 50,            # 趨勢檢測窗口
    'regime_threshold': 0.7,       # 狀態識別閾值
}
```

## 📝 使用場景

### 場景 1：完整市場分析流程

```python
from bioneuronai.analysis import (
    get_news_analyzer, MarketKeywords, 
    MarketMicrostructure, MarketRegimeDetector,
    DailyReport
)

async def comprehensive_analysis(symbol: str):
    # 1. 新聞情緒分析
    news_analyzer = await get_news_analyzer()
    news_sentiment = await news_analyzer.get_symbol_sentiment(symbol)
    
    # 2. 關鍵字分析
    keyword_manager = MarketKeywords()
    trending_keywords = keyword_manager.get_trending_keywords(days=1)
    
    # 3. 特徵工程
    feature_engineer = MarketMicrostructure()
    market_features = feature_engineer.create_features(market_data)
    
    # 4. 市場狀態檢測
    regime_detector = MarketRegimeDetector()
    current_regime = regime_detector.detect_regime(symbol)
    
    # 5. 生成每日報告
    report_generator = DailyReport()
    daily_report = await report_generator.generate_report(symbol)
    
    return {
        'sentiment': news_sentiment,
        'keywords': trending_keywords,
        'features': market_features,
        'regime': current_regime,
        'report': daily_report
    }
```

### 場景 2：實時風險監控

```python
from bioneuronai.analysis import LiquidationHeatmap, MarketRegimeDetector

def monitor_risk(symbol: str, orderbook_data: dict):
    # 清算風險評估
    heatmap = LiquidationHeatmap()
    risk_zones = heatmap.identify_risk_zones(orderbook_data)
    
    # 市場狀態檢查
    regime_detector = MarketRegimeDetector()
    current_regime = regime_detector.detect_regime(symbol)
    
    # 風險等級評估
    risk_level = 'HIGH' if risk_zones and current_regime['type'] == 'HIGH_VOLATILITY' else 'MEDIUM'
    
    return {
        'risk_zones': risk_zones,
        'market_regime': current_regime,
        'overall_risk': risk_level
    }
```

### 場景 3：AI 模型特徵準備

```python
from bioneuronai.analysis import MarketMicrostructure, VolumeProfile

def prepare_ai_features(market_data: dict, orderbook: dict):
    # 市場微觀結構特徵
    microstructure = MarketMicrostructure()
    base_features = microstructure.create_features(market_data)
    
    # 成交量分布特徵
    volume_profile = VolumeProfile()
    volume_features = volume_profile.calculate_profile(market_data['price'], market_data['volume'])
    
    # 訂單簿特徵
    orderbook_features = microstructure.extract_orderbook_features(orderbook)
    
    # 合併所有特徵
    all_features = {**base_features, **volume_features, **orderbook_features}
    
    return all_features
```

## ⚠️ 注意事項

1. **數據質量**：確保輸入數據的完整性和準確性
2. **計算性能**：特徵工程可能需要較長計算時間
3. **市場變化**：模型參數需要定期校準
4. **API 限制**：新聞來源可能有請求頻率限制

## 🚀 快速開始

```python
import asyncio
from bioneuronai.analysis import get_news_analyzer, MarketKeywords, DailyReport

async def main():
    # 新聞分析
    news_analyzer = await get_news_analyzer()
    news = await news_analyzer.get_latest_news(hours=24, limit=5)
    
    # 關鍵字分析
    keywords = MarketKeywords()
    trending = keywords.get_trending_keywords(days=1)
    
    # 生成報告
    report = DailyReport()
    daily_report = await report.generate_report('BTCUSDT')
    
    print("市場分析完成！")
    print(f"新聞數量: {len(news)}")
    print(f"熱門關鍵字: {len(trending)}")
    print(f"報告生成: {daily_report is not None}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📈 性能指標

- 新聞抓取時間：2-5 秒（多個來源）
- 單條新聞分析：< 10ms
- 關鍵字匹配：< 5ms
- 特徵工程：50-200ms（視數據量）
- 市場狀態檢測：< 50ms
- 支持並發分析：是

## 🔄 版本歷史

- v2.2.0 - 新增每日報告模組，重構架構
- v2.1.0 - 模組化重構，新增特徵工程
- v2.0.0 - 新增多語言支持，市場狀態檢測
- v1.5.0 - 優化情緒分析算法
- v1.0.0 - 初始版本
為機器學習模型生成技術指標特徵。

**主要類**:
- `FeatureEngineering` - 特徵工程器

**特徵類型**:
- 技術指標 (RSI, MACD, Bollinger Bands)
- 價格特徵 (收益率, 波動率)
- 成交量特徵
- 時間特徵

**使用示例**:
```python
from bioneuronai.analysis import FeatureEngineering

# 初始化特徵工程器
fe = FeatureEngineering()

# 生成特徵
features = fe.create_features(market_data)

# 選擇重要特徵
top_features = fe.select_features(features, target, top_k=20)
```

### 5. BacktestEngine (回測引擎)

識別和分類市場相關的關鍵字和事件。

**主要功能：**
- 關鍵字分類（監管、技術、市場、機構）
- 關鍵字權重評分
- 上下文匹配
- 多語言支持

**使用示例：**
```python
from bioneuronai.analysis import MarketKeywords

# 初始化關鍵字系統
keywords = MarketKeywords()

# 檢測新聞中的關鍵字
text = "SEC approves Bitcoin ETF application"
matches = keywords.find_keywords(text)

for match in matches:
    print(f"關鍵字: {match.keyword}")
    print(f"類別: {match.category}")
    print(f"權重: {match.weight}")
```

**關鍵字分類：**
- 🏛️ `REGULATORY` - 監管相關
- 💻 `TECHNICAL` - 技術相關
- 📈 `MARKET` - 市場相關
- 🏢 `INSTITUTIONAL` - 機構相關

### 3. get_news_analyzer() 單例函數

獲取共享的新聞分析器實例（單例模式）。

```python
from bioneuronai.analysis import get_news_analyzer

# 獲取分析器實例（整個應用共享）
analyzer = await get_news_analyzer()
```

## 📦 導出 API

```python
from bioneuronai.analysis import (
    CryptoNewsAnalyzer,    # 新聞分析器
    NewsArticle,           # 新聞文章數據類
    NewsAnalysisResult,    # 分析結果數據類
    get_news_analyzer,     # 單例獲取函數
    MarketKeywords,        # 關鍵字識別
    KeywordMatch,          # 關鍵字匹配結果
)
```

## 🔗 依賴關係

**被依賴於：**
- `core.TradingEngine` - 用於交易決策
- `automation.SOPAutomation` - SOP 流程分析
- `automation.PreTradeAutomation` - 交易前檢查

**外部依賴：**
- `requests` - HTTP 請求
- `beautifulsoup4` - HTML 解析
- `textblob` - 情緒分析（備用）
- `feedparser` - RSS 解析

## 🎨 架構設計

```
analysis/
├── news_analyzer.py        # 新聞分析核心
├── market_keywords.py      # 關鍵字系統
└── __init__.py            # 模組導出
```

## 📊 數據模型

### NewsArticle (新聞文章)

```python
@dataclass
class NewsArticle:
    title: str              # 標題
    url: str                # 網址
    source: str             # 來源
    published_time: datetime  # 發布時間
    content: str            # 內容
    summary: str            # 摘要
```

### NewsAnalysisResult (分析結果)

```python
@dataclass
class NewsAnalysisResult:
    sentiment_score: float        # 情緒分數 (-1 到 1)
    impact_level: str            # 影響級別 (HIGH/MEDIUM/LOW)
    urgency: str                 # 緊急度
    related_symbols: List[str]   # 相關幣種
    keywords: List[str]          # 關鍵字
    category: str                # 分類
```

## 🔧 配置說明

```python
# 新聞來源配置
NEWS_SOURCES = {
    'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'cointelegraph': 'https://cointelegraph.com/rss',
    'decrypt': 'https://decrypt.co/feed',
}

# 情緒分析配置
SENTIMENT_CONFIG = {
    'positive_threshold': 0.3,    # 正面閾值
    'negative_threshold': -0.3,   # 負面閾值
    'impact_keywords_weight': 2.0, # 關鍵字權重
}
```

## 📝 使用場景

### 場景 1：監控市場情緒

```python
async def monitor_market_sentiment():
    analyzer = await get_news_analyzer()
    
    while True:
        # 每小時檢查一次
        news = await analyzer.get_latest_news(hours=1)
        
        # 計算整體情緒
        overall_sentiment = sum(
            analyzer.analyze_sentiment(n).sentiment_score 
            for n in news
        ) / len(news)
        
        print(f"市場情緒: {overall_sentiment:.2f}")
        await asyncio.sleep(3600)
```

### 場景 2：重大事件警報

```python
async def alert_major_events():
    analyzer = await get_news_analyzer()
    
    news = await analyzer.get_latest_news(hours=1)
    
    for article in news:
        result = analyzer.analyze_sentiment(article)
        
        if result.impact_level == "HIGH":
            print(f"⚠️ 重大事件: {article.title}")
            print(f"情緒: {result.sentiment_score}")
            print(f"關鍵字: {', '.join(result.keywords)}")
```

### 場景 3：幣種特定分析

```python
async def analyze_specific_coin(symbol: str):
    analyzer = await get_news_analyzer()
    
    # 獲取該幣種的情緒
    sentiment_data = await analyzer.get_symbol_sentiment(symbol)
    
    print(f"{symbol} 情緒分析:")
    print(f"平均情緒: {sentiment_data['average_sentiment']:.2f}")
    print(f"新聞數量: {sentiment_data['news_count']}")
    print(f"正面新聞: {sentiment_data['positive_count']}")
    print(f"負面新聞: {sentiment_data['negative_count']}")
```

## ⚠️ 注意事項

1. **API 限制**：某些新聞源可能有請求頻率限制
2. **語言支持**：主要針對英文，中文支持有限
3. **情緒準確性**：情緒分析基於規則和關鍵字，不是 100% 準確
4. **網絡依賴**：需要穩定的網絡連接

## 🚀 快速開始

```python
import asyncio
from bioneuronai.analysis import get_news_analyzer

async def main():
    # 獲取分析器
    analyzer = await get_news_analyzer()
    
    # 獲取最新新聞
    news = await analyzer.get_latest_news(hours=24, limit=10)
    
    # 分析每條新聞
    for article in news:
        result = analyzer.analyze_sentiment(article)
        print(f"\n📰 {article.title}")
        print(f"情緒: {result.sentiment_score:.2f}")
        print(f"影響: {result.impact_level}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📈 性能指標

- 新聞抓取時間：2-5 秒（多個來源）
- 單條新聞分析：< 10ms
- 關鍵字匹配：< 5ms
- 支持並發分析：是

## 🔄 版本歷史

- v2.1.0 - 模組化重構，改進 API
- v2.0.0 - 新增多語言支持
- v1.5.0 - 優化情緒分析算法
- v1.0.0 - 初始版本
