# 分析模組 (Analysis)

**路徑**: `src/bioneuronai/analysis/`  
**版本**: v4.4  
**更新日期**: 2026-03-19  
**架構層級**: Layer 4 — 分析與智能層

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [核心組件 (Top-Level)](#核心組件-top-level)
4. [子模組導航](#子模組導航)
5. [導出 API](#導出-api)
6. [執行方式 (SOP 流程)](#執行方式-sop-流程)
7. [相關文檔](#相關文檔)

---

## 🎯 模組概述

分析模組是 BioNeuronai 的「感知層」，負責從多種數據源（新聞、市場微結構、成交量、總體經濟數據）提取特徵與情緒信號，為策略層和交易層提供決策依據。包含 3 個專門的子模組以及位於頂層的核心分析引擎。

### 模組職責
- ✅ **新聞與事件感知**: 多來源新聞抓取、情緒分析、事件檢測。
- ✅ **關鍵字學習 (RLHF)**: 基於預測準確率自動調整關鍵字權重的動態系統。
- ✅ **自動化每日報告**: 整合全球市況與技術指標的 SOP 報告生成。
- ✅ **進階特徵工程**: 成交量分布 (Volume Profile) 與流動性地圖。
- ✅ **市場狀態識別**: 判斷牛熊震盪的高級統計模型。

---

## 🏗️ 架構總覽

```
src/bioneuronai/analysis/
├── __init__.py              # 統一導出接口 (158 行)
├── feature_engineering.py   # 進階特徵工程 (844 行)
├── market_regime.py         # 市場狀態識別 (827 行)
│
├── news/                    # 📰 新聞分析與預測子模組
│   ├── analyzer.py          # (新聞分析器)
│   ├── evaluator.py         # (事件評估器)
│   └── prediction_loop.py   # (RLHF 循環)
│
├── keywords/                # 🔑 關鍵字與權重管理子模組
│   ├── manager.py           # (核心管理器)
│   ├── learner.py           # (學習器)
│   ├── loader.py            # (載入器)
│   └── static_utils.py      # (靜態接口)
│
└── daily_report/            # 📊 每日報告與市況整合子模組
    ├── report_generator.py  # (文字與 JSON 報告生成)
    ├── market_data.py       # (總經數據)
    ├── strategy_planner.py  # (策略規劃)
    └── risk_manager.py      # (風險參數)
```

---

## 🎯 核心組件 (Top-Level)

本目錄頂層的組件負責提供進階分析模型，可為整個系統提供技術與統計上的洞察。

### `feature_engineering.py` — 進階特徵工程 (844 行)
為 AI 模型提供高質量特徵輸入，將微結構量化。
- **`VolumeProfile`**: 計算 POC (Point of Control) 與價值區域 (Value Area)。
- **`LiquidationHeatmap` / `LiquidityMap`**: 分析訂單簿與清算數據熱區。
- **`MarketDataProcessor`**: 負責將原始 K 線資料轉換為 ML-ready 的特徵矩陣。

### `market_regime.py` — 市場狀態識別 (827 行)
基於統計模型自動分類當前的市場體制。
- **`MarketRegimeDetector`**: 整合 HMM (隱馬爾可夫模型)、GARCH 波動率與多時間框架，將市場分類為「牛市 / 熊市 / 震盪市 / 高波動」。
- **`RegimeBasedStrategySelector`**: 根據上述識別結果，建議適合的交易策略 (如趨勢跟蹤、均值回歸等)。

---

## 📁 子模組導航

為了維持模組單一職責與可擴展性，詳細的業務邏輯已經拆分。請點選以查看最詳細的實作說明：

### 1. 📰 [新聞分析系統 (`news/`)](news/README.md)
負責 CryptoPanic 與 RSS 的資料獲取、情緒分析、嚴重事件評估（如駭客、監管），以及 RLHF 新聞預測衰減循環。

### 2. 🔑 [關鍵字系統 (`keywords/`)](keywords/README.md)
核心的動態關鍵字管理器（不再依賴硬編碼）。透過 SQLite 持久化預測記錄，基於實際市場表現（RLHF）動態調整每個關鍵字對市場預測的權重與情緒偏向。

### 3. 📊 [每日報告系統 (`daily_report/`)](daily_report/README.md)
自動化 SOP 流程的核心，整合全球金融市況、技術分析建議與自訂風險管理參數，並自動生成格式化的每日市場文字與 JSON 報告供交易引擎或機器人使用。

---

## 📦 導出 API

您可以直接從 `bioneuronai.analysis` 匯入最常用的類別，無需深入子資料夾：

```python
from bioneuronai.analysis import (
    # 新聞與事件
    CryptoNewsAnalyzer,         # 新聞分析器
    RuleBasedEvaluator,         # 事件評估器
    NewsPredictionLoop,         # RLHF 預測循環

    # 關鍵字系統
    MarketKeywords,             # 關鍵字靜態接口

    # 特徵與狀態
    VolumeProfile,              # 成交量分布
    LiquidationHeatmap,         # 清算熱力圖
    MarketDataProcessor,        # 數據處理器
    MarketRegimeDetector,       # 體制檢測器

    # 報告模型
    DailyReport,                # 報告模型 (from daily_report)
)
```

---

## 🚀 執行方式 (SOP 流程)

分析模組可以作為獨立模組執行，用於生成完整或部分的市場報告。

```bash
# 1. 執行完整報告 (關鍵字 + 總經數據 + SOP報告 + 補充模組驗證)
python -m bioneuronai.analysis

# 2. 僅執行 SOP 每日流程 (不含技術分析)
python -m bioneuronai.analysis --sop

# 3. 僅執行關鍵字系統報告
python -m bioneuronai.analysis --kw
```

### 完整執行流程（預設模式）

```
1. SOPAutomationSystem.run_full_report()
   ├─ [1/4] 關鍵字系統報告（KeywordManager.print_report）
   ├─ [2/4] 技術分析（MarketRegimeDetector + VolumeProfileCalculator）
   ├─ [3/4] 全球市場數據（MarketDataCollector - Yahoo / CoinGecko）
   └─ [4/4] SOP 每日報告（20 步驟完整流程，結果保存至 sop_automation_data/）

2. 補充驗證（涵蓋全部模組）
   ├─ MarketKeywords 靜態接口驗證
   ├─ KeywordLearner RLHF 學習初始化
   ├─ RuleBasedEvaluator 事件評估
   └─ NewsPredictionLoop 預測統計輸出
```

---

## 📚 相關文檔

- **NLP 訓練指南**: [NLP_TRAINING_GUIDE.md](../../../docs/NLP_TRAINING_GUIDE.md)
- **每日報告清單**: [DAILY_REPORT_CHECKLIST.md](../../../docs/DAILY_REPORT_CHECKLIST.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 3 月 19 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
