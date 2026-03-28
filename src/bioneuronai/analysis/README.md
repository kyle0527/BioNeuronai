# 分析模組 (Analysis)

**路徑**: `src/bioneuronai/analysis/`
**版本**: v4.4
**更新日期**: 2026-03-27
**架構層級**: Layer 4 — 分析與智能層

---

## 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [直屬核心組件](#直屬核心組件)
4. [子模組索引](#子模組索引)
5. [導出 API](#導出-api)
6. [執行方式](#執行方式)
7. [相關文檔](#相關文檔)

---

## 模組概述

分析模組是 BioNeuronai 的「感知層」，負責從多種數據源（新聞、市場微結構、成交量）提取特徵與情緒信號，為策略層和交易層提供決策依據。包含 2 個直屬核心引擎、3 個專門子模組，共計 22 個 Python 檔案，總計約 7,300 行。

**模組職責**:
- 新聞情緒分析、事件檢測與 RLHF 預測驗證循環
- 市場關鍵字動態學習與權重優化 (RLHF)
- 特徵工程（成交量分布 / 清算熱力圖 / 市場微結構）
- 市場狀態識別（趨勢強度 / 波動度體制 / 多時間框架）
- 每日市場報告自動生成

---

## 架構總覽

```
src/bioneuronai/analysis/
├── __init__.py              # 模組統一導出 (157 行)
├── __main__.py              # CLI 執行入口 (183 行)
├── feature_engineering.py   # 進階特徵工程 (843 行)
├── market_regime.py         # 市場狀態識別 (827 行)
│
├── news/                    # 新聞分析子模組 (5 個檔案，2,621 行)
│   └── README.md            # → 詳見子模組文檔
│
├── keywords/                # 關鍵字系統子模組 (6 個檔案，1,824 行)
│   └── README.md            # → 詳見子模組文檔
│
└── daily_report/            # 每日報告子模組 (7 個檔案)
    └── README.md            # → 詳見子模組文檔
```

---

## 直屬核心組件

### `feature_engineering.py` (843 行)
為 AI 模型提供高品質特徵輸入，處理原始 K 線資料並輸出結構化微結構數據。

**資料模型**:
- `PriceLevel` (Enum): 價格水平分類
- `VolumeProfileLevel`: 單一價位的成交量資料（含 `delta`, `delta_percentage` 屬性）
- `VolumeProfile`: 成交量分布分析結果（POC / 價值區域上下緣）
- `LiquidationCluster`: 單一清算叢集
- `LiquidationHeatmap`: 清算熱力圖（多個叢集的彙整結果）
- `MarketMicrostructure`: 市場微觀結構完整快照（含 `to_feature_vector()` 輸出特徵向量）

**計算器**:
- `VolumeProfileCalculator`: 從 K 線計算成交量分布（POC、價值區域、高低量節點）
- `LiquidationHeatmapCalculator`: 估算各價位的潛在清算量
- `MarketDataProcessor`: 即時更新價格/成交量/持倉量/清算事件，並建構 `MarketMicrostructure`，提供 `generate_market_summary_prompt()` 輸出自然語言摘要

---

### `market_regime.py` (827 行)
基於技術指標的市場體制自動識別，輸出結構化分析結果供策略層路由使用。

**枚舉類型**:
- `MarketRegime` (Enum): 市場體制（趨勢多頭、趨勢空頭、震盪、突破等）
- `VolatilityRegime` (Enum): 波動度體制（低波動、正常、高波動、極端）
- `TrendStrength` (Enum): 趨勢強度分級

**資料模型**:
- `RegimeAnalysis`: 體制分析結果，包含當前體制、波動度、趨勢強度、支撐阻力位、建議持倉方向等；提供 `get_trading_recommendation()`, `to_prompt()`, `to_feature_vector()` 方法

**核心類別**:
- `MarketRegimeDetector`: 輸入 K 線，計算 ATR / ADX / EMA，輸出 `RegimeAnalysis`；內部透過 `_analyze_trend()`, `_classify_volatility()`, `_find_support_resistance()`, `_classify_regime()` 等流程完成分析
- `RegimeBasedStrategySelector`: 接收 `RegimeAnalysis`，輸出適合當前體制的策略建議字典（含波動度調整係數）

---

## 子模組索引

| 子模組 | 職責概述 | 文檔 |
|--------|---------|------|
| `news/` | 新聞抓取、情緒分析、事件偵測、RLHF 預測驗證循環 | [news/README.md](news/README.md) |
| `keywords/` | 關鍵字動態管理、RLHF 權重學習、文字匹配評分 | [keywords/README.md](keywords/README.md) |
| `daily_report/` | 每日市場分析報告自動生成（宏觀/技術/情緒/策略/風控） | [daily_report/README.md](daily_report/README.md) |

---

## 導出 API

`__init__.py` 將所有子模組的公開介面統一匯出，完整清單如下：

```python
from bioneuronai.analysis import (
    # ── 每日報告 ──────────────────────────────────────────
    SOPAutomationSystem,        # SOP 自動化主流程
    MarketEnvironmentCheck,     # 市場環境檢查
    TradingPlanCheck,           # 交易計劃檢查
    MarketCondition,            # 市場狀況模型
    StrategyPerformance,        # 策略表現模型
    RiskParameters,             # 風險參數模型
    TradingPairsPriority,       # 交易對優先序模型
    DailyReport,                # 每日報告模型

    # ── 關鍵字系統 ────────────────────────────────────────
    Keyword,                    # 關鍵字資料模型
    KeywordMatch,               # 匹配結果模型
    PredictionRecord,           # 預測記錄模型
    KeywordLoader,              # JSON 載入器
    KeywordManager,             # 核心管理器 (Singleton)
    get_keyword_manager,        # Singleton 工廠函數
    MarketKeywords,             # 靜態包裝類（推薦使用）
    KeywordLearner,             # RLHF 學習器

    # ── 新聞分析 ──────────────────────────────────────────
    CryptoNewsAnalyzer,         # 新聞分析器 (Singleton)
    get_news_analyzer,          # Singleton 工廠函數
    NewsArticle,                # 新聞文章模型
    NewsAnalysisResult,         # 分析結果模型
    RuleBasedEvaluator,         # 規則式事件評估器
    get_rule_evaluator,         # Singleton 工廠函數
    NewsPredictionLoop,         # RLHF 預測驗證循環

    # ── 特徵工程 ──────────────────────────────────────────
    VolumeProfile,              # 成交量分布結果
    VolumeProfileLevel,         # 單一價位成交量資料
    VolumeProfileCalculator,    # 成交量分布計算器
    LiquidationCluster,         # 單一清算叢集
    LiquidationHeatmap,         # 清算熱力圖結果
    LiquidationHeatmapCalculator, # 清算熱力圖計算器
    MarketMicrostructure,       # 市場微觀結構快照
    MarketDataProcessor,        # 即時市場數據處理器

    # ── 市場狀態識別 ──────────────────────────────────────
    MarketRegime,               # 市場體制枚舉
    VolatilityRegime,           # 波動度體制枚舉
    TrendStrength,              # 趨勢強度枚舉
    RegimeAnalysis,             # 體制分析結果
    MarketRegimeDetector,       # 體制檢測器
    RegimeBasedStrategySelector, # 體制策略建議器
)
```

---

## 執行方式

`__main__.py` 提供三種 CLI 模式，技術分析部分使用模擬 K 線示範：

```bash
# 完整報告（SOP 全流程 + 模擬技術分析 + 補充模組驗證）
python -m bioneuronai.analysis

# 僅執行 SOP 每日流程（不含技術分析）
python -m bioneuronai.analysis --sop

# 僅執行關鍵字系統報告
python -m bioneuronai.analysis --kw
```

> 實際生產使用時請透過交易所連接器取得真實 K 線後直接呼叫：
> ```python
> sop = SOPAutomationSystem()
> sop.run_full_report(klines=real_klines, symbol="BTCUSDT", current_price=price)
> ```

**驗證狀態（2026-03-27）**: 全模組共 22 個 `.py` 檔案皆通過匯入與功能驗證。

---

## 相關文檔

- **NLP 訓練指南**: [NLP_TRAINING_GUIDE.md](../../../docs/NLP_TRAINING_GUIDE.md)
- **每日報告清單**: [DAILY_REPORT_CHECKLIST.md](../../../docs/DAILY_REPORT_CHECKLIST.md)
- **上層目錄**: [src/bioneuronai/README.md](../README.md)
