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
6. [執行方式](#執行方式)

---

## 🎯 模組概述

分析模組是 BioNeuronai 的「感知層」，負責從多種數據源（新聞、市場微結構、成交量、總體經濟數據）提取特徵與情緒信號，為策略層和交易層提供決策依據。本模組設計高度解耦，包含 3 個專門的子模組以及位於頂層的核心特徵與狀態引擎。

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
├── __init__.py              # 統一導出接口
├── feature_engineering.py   # 進階特徵工程 (Volume, Liquidity)
├── market_regime.py         # 市場狀態識別 (HMM, GARCH)
│
├── news/                    # 📰 新聞分析與預測子模組
│   ├── analyzer.py          # (核心分析器)
│   ├── prediction_loop.py   # (RLHF 循環)
│   └── ...
│
├── keywords/                # 🔑 關鍵字與權重管理子模組
│   ├── manager.py           # (核心管理器, SQLite+JSON)
│   ├── learner.py           # (學習器)
│   └── ...
│
└── daily_report/            # 📊 每日報告與市況整合子模組
    ├── report_generator.py  # (文字與 JSON 生成)
    ├── market_data.py       # (總經數據)
    └── ...
```

---

## 🎯 核心組件 (Top-Level)

### `feature_engineering.py` — 進階特徵工程
為策略層或 AI 模型提供高品質的特徵輸入矩陣。
- **`VolumeProfile`**: 計算 POC (Point of Control) 與價值區域 (Value Area)。
- **`LiquidationHeatmap` / `LiquidityMap`**: 分析訂單簿與清算數據。
- **`MarketDataProcessor`**: 將原始 K 線轉換為特徵矩陣。

### `market_regime.py` — 市場狀態識別
基於統計模型自動分類當前的市場體制。
- **`MarketRegimeDetector`**: 整合 HMM、GARCH 波動率與多時間框架，識別出「牛市 / 熊市 / 震盪市 / 高波動」。
- **`RegimeBasedStrategySelector`**: 根據當前體制，提供最適合的策略建議。

---

## 📁 子模組導航

為了保持代碼的整潔與可維護性，複雜邏輯已拆分至獨立子模組。請點擊查看詳細的技術文檔：

### 1. 📰 [新聞分析系統 (`news/`)](news/README.md)
負責 CryptoPanic 與 RSS 的資料獲取、自然語言情緒分析、事件檢測（如駭客、監管、ETF），以及新聞預測的 RLHF 循環與衰減模型。

### 2. 🔑 [關鍵字系統 (`keywords/`)](keywords/README.md)
核心的動態關鍵字管理器。取代硬編碼，從 JSON 載入關鍵字，並使用 SQLite 持久化預測記錄，透過強化學習 (RLHF) 動態調整每個關鍵字對市場預測的權重與情緒偏向。

### 3. 📊 [每日報告系統 (`daily_report/`)](daily_report/README.md)
SOP 自動化流程的核心，負責收集全球市場數據（美股、加密貨幣、經濟事件）、整合新聞情緒與風險管理參數，並自動生成格式化的每日市場文字與 JSON 報告。

---

## 📦 導出 API

您可以直接從 `bioneuronai.analysis` 匯入最常用的類別，無需深入子資料夾：

```python
from bioneuronai.analysis import (
    # 新聞與事件
    CryptoNewsAnalyzer,
    RuleBasedEvaluator,
    NewsPredictionLoop,

    # 關鍵字系統
    MarketKeywords,

    # 特徵與狀態
    VolumeProfile,
    MarketRegimeDetector,

    # 報告模型
    DailyReport,
)
```

---

## 🚀 執行方式

分析模組可以作為獨立腳本執行，用於生成完整或部分的市場報告。

```bash
# 1. 執行完整報告 (關鍵字 + 總經數據 + SOP報告 + 補充驗證)
python -m bioneuronai.analysis

# 2. 僅執行 SOP 每日流程
python -m bioneuronai.analysis --sop

# 3. 僅檢視關鍵字系統的表現報告
python -m bioneuronai.analysis --kw
```

> **注意**: 執行完整流程時，請確保環境變數（如 API Keys）已正確配置，且 `PYTHONPATH` 包含項目根目錄。

---

> 📖 父模組：[BioNeuronai 主模組](../README.md)
