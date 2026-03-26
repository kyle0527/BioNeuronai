# 分析模組 (Analysis)

**路徑**: `src/bioneuronai/analysis/`  
**版本**: v4.4  
**更新日期**: 2026-03-19  
**架構層級**: Layer 4 — 分析與智能層

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [核心組件](#核心組件)
4. [子模組：新聞分析](#子模組新聞分析-news)
5. [子模組：關鍵字系統](#子模組關鍵字系統-keywords)
6. [子模組：每日報告](#子模組每日報告-daily_report)
7. [導出 API](#導出-api)
8. [執行方式 (SOP 流程)](#執行方式-sop-流程)
9. [相關文檔](#相關文檔)

---

## 🎯 模組概述

分析模組是 BioNeuronai 的「感知層」，負責從多種數據源（新聞、市場微結構、成交量、鏈上數據）提取特徵與情緒信號，為策略層和交易層提供決策依據。包含 3 個專門子模組和核心分析引擎，共計 22 個 Python 檔案，總計約 7,300 行。

### 模組職責
- ✅ 新聞情緒分析與事件檢測
- ✅ 市場關鍵字學習與權重優化 (RLHF)
- ✅ 特徵工程（成交量分布 / 清算熱力圖 / 流動性地圖）
- ✅ 市場狀態識別（HMM / GARCH / 多時間框架）
- ✅ 每日市場報告自動生成
- ✅ 新聞預測驗證循環 (RLHF)

---

## 🏗️ 架構總覽

```
src/bioneuronai/analysis/
├── __init__.py              # 模組入口 (157 行)
├── __main__.py              # 模組執行入口 (183 行)
├── feature_engineering.py   # 進階特徵工程 (843 行)
├── market_regime.py         # 市場狀態識別 (827 行)
│
├── news/                    # 新聞分析子模組 (5 個檔案)
│   ├── __init__.py          # (72 行)
│   ├── analyzer.py          # 新聞分析器 (1,140 行)
│   ├── evaluator.py         # 事件評估器 (404 行)
│   ├── models.py            # 新聞數據模型 (102 行)
│   └── prediction_loop.py   # RLHF 預測循環 (903 行)
│
├── keywords/                # 關鍵字系統 (6 個檔案)
│   ├── __init__.py          # (60 行)
│   ├── manager.py           # 關鍵字管理器 (905 行)
│   ├── learner.py           # 關鍵字學習器 (443 行)
│   ├── loader.py            # JSON 載入器 (131 行)
│   ├── models.py            # 關鍵字數據模型 (99 行)
│   └── static_utils.py      # 靜態接口 (186 行)
│
└── daily_report/            # 每日報告系統 (7 個檔案)
    ├── __init__.py          # 模組入口與主流程 (717 行)
    ├── report_generator.py  # 報告生成器 (289 行)
    ├── market_data.py       # 全球市場數據 (557 行)
    ├── news_sentiment.py    # 新聞情緒整合 (131 行)
    ├── risk_manager.py      # 報告風險管理 (605 行)
    ├── strategy_planner.py  # 策略規劃 (447 行)
    └── models.py            # 報告數據模型 (133 行)
```

---

## 🎯 核心組件

### `feature_engineering.py` — 進階特徵工程 (843 行)
為 AI 模型提供高質量特徵輸入。
- **`VolumeProfile`**: 成交量分布分析（POC / 價值區域）。
- **`LiquidationHeatmap`**: 清算熱力圖。
- **`MarketDataProcessor`**: K 線→特徵矩陣轉換。
- **`LiquidityMap`**: 訂單簿深度流動性地圖。

### `market_regime.py` — 市場狀態識別 (827 行)
基於統計模型與機器學習的市場體制自動識別。
- **`MarketRegimeDetector`**: 體制檢測器。
- **`RegimeAnalysis`**: 體制分析結果。
- **`RegimeBasedStrategySelector`**: 基於體制的策略建議。

---

## 📰 子模組：新聞分析 (`news/`)
詳見：[news/README.md](news/README.md)

- `analyzer.py` (1,140 行): 從 CryptoPanic / RSS 獲取新聞並執行情緒分析。
- `evaluator.py` (404 行): 規則式事件評估器，產生事件並檢測 Hard Stop 條件。
- `prediction_loop.py` (903 行): 預測→驗證→學習→優化的完整 RLHF 循環。
- `models.py` (102 行): `NewsArticle`, `NewsAnalysisResult`。

---

## 🔑 子模組：關鍵字系統 (`keywords/`)
詳見：[keywords/README.md](keywords/README.md)

- `manager.py` (905 行): 關鍵字匹配、預測記錄與準確率追蹤 (SQLite + JSON)。
- `learner.py` (443 行): 獨立的 RLHF 關鍵字權重更新與學習。
- `loader.py` (131 行): JSON 關鍵字檔案載入器。
- `static_utils.py` (186 行): 靜態接口（如 `MarketKeywords.get_importance_score`）。
- `models.py` (99 行): `Keyword`, `KeywordMatch`, `PredictionRecord`。

---

## 📋 子模組：每日報告 (`daily_report/`)
詳見：[daily_report/README.md](daily_report/README.md)

自動生成每日市場分析報告，涵蓋宏觀、技術、情緒、策略與風險五大面向。
- `__init__.py` (717 行): `SOPAutomationSystem` 模組入口與主流程執行。
- `market_data.py` (557 行): 全球市場數據收集（Yahoo Finance / Binance API 經濟日曆）。
- `strategy_planner.py` (447 行): 分析當前市場狀態並給定適合的策略。
- `risk_manager.py` (605 行): 根據帳戶狀態與波動率給出資金保護參數。
- `report_generator.py` (289 行): 報告文字格式化與 JSON 持久化。
- `news_sentiment.py` (131 行): 整合 `CryptoNewsAnalyzer` 算出當日情緒分數。
- `models.py` (133 行): `DailyReport`, `MarketCondition`, `StrategyPerformance` 等模型。

---

## 📦 導出 API

```python
from bioneuronai.analysis import (
    # 新聞分析
    CryptoNewsAnalyzer,         # 新聞分析器
    RuleBasedEvaluator,         # 事件評估器
    NewsPredictionLoop,         # RLHF 預測循環

    # 關鍵字系統
    MarketKeywords,             # 關鍵字靜態接口

    # 特徵工程
    VolumeProfile,              # 成交量分布
    LiquidationHeatmap,         # 清算熱力圖
    MarketDataProcessor,        # 數據處理器

    # 市場狀態
    MarketRegimeDetector,       # 體制檢測器
    RegimeAnalysis,             # 分析結果

    # 每日報告
    DailyReport,                # 報告模型 (from daily_report)
)
```

---

## 🚀 執行方式 (SOP 流程)

```bash
# 1. 完整報告（4 部分：關鍵字 + 技術分析 + 全球市況 + SOP 報告 + 補充模組驗證）
python -m bioneuronai.analysis

# 2. 僅執行 SOP 每日流程（不含技術分析）
python -m bioneuronai.analysis --sop

# 3. 僅執行關鍵字系統報告
python -m bioneuronai.analysis --kw
```

### 驗證狀態（2026-03-19）
全模組共 22 個 `.py` 檔案皆通過匯入與功能驗證。

---

## 📚 相關文檔

- **NLP 訓練指南**: [NLP_TRAINING_GUIDE.md](../../../docs/NLP_TRAINING_GUIDE.md)
- **每日報告清單**: [DAILY_REPORT_CHECKLIST.md](../../../docs/DAILY_REPORT_CHECKLIST.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 3 月 19 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
