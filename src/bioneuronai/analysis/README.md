# 分析模組 (Analysis)

**路徑**: `src/bioneuronai/analysis/`  
**版本**: v4.1  
**更新日期**: 2026-02-15  
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
8. [使用示例](#使用示例)
9. [相關文檔](#相關文檔)

---

## 🎯 模組概述

分析模組是 BioNeuronai 的「感知層」，負責從多種數據源（新聞、市場微結構、成交量、鏈上數據）提取特徵與情緒信號，為策略層和交易層提供決策依據。包含 3 個專門子模組和 2 個核心分析引擎。

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
├── __init__.py              # 模組入口 (158 行)
├── feature_engineering.py   # 進階特徵工程 (844 行)
├── market_regime.py         # 市場狀態識別 (827 行)
│
├── news/                    # 新聞分析子模組
│   ├── __init__.py
│   ├── analyzer.py          # 新聞分析器 (1,141 行)
│   ├── evaluator.py         # 事件評估器 (395 行)
│   ├── models.py            # 新聞數據模型 (103 行)
│   └── prediction_loop.py   # RLHF 預測循環 (901 行)
│
├── keywords/                # 關鍵字系統
│   ├── __init__.py
│   ├── manager.py           # 關鍵字管理器 (907 行)
│   ├── learner.py           # 關鍵字學習器 (444 行)
│   ├── loader.py            # JSON 載入器 (132 行)
│   ├── models.py            # 關鍵字數據模型 (97 行)
│   └── static_utils.py      # 靜態接口 (186 行)
│
└── daily_report/            # 每日報告系統
    ├── __init__.py
    ├── report_generator.py  # 報告生成器 (291 行)
    ├── market_data.py       # 全球市場數據 (387 行)
    ├── news_sentiment.py    # 新聞情緒整合 (132 行)
    ├── risk_manager.py      # 報告風險管理 (460 行)
    ├── strategy_planner.py  # 策略規劃 (325 行)
    └── models.py            # 報告數據模型 (134 行)
                               ─────────
                               合計 ~6,881 行
```

---

## 🎯 核心組件

### `feature_engineering.py` — 進階特徵工程 (844 行)

為 AI 模型提供高質量特徵輸入。

**主要類**:
- `VolumeProfile` — 成交量分布分析（POC / 價值區域）
- `LiquidationHeatmap` — 清算熱力圖
- `MarketDataProcessor` — K 線→特徵矩陣轉換
- `LiquidityMap` — 訂單簿深度流動性地圖

---

### `market_regime.py` — 市場狀態識別 (827 行)

基於統計模型與機器學習的市場體制自動識別。

**主要類**:
- `MarketRegimeDetector` — 體制檢測器
- `RegimeAnalysis` — 體制分析結果
- `RegimeBasedStrategySelector` — 基於體制的策略建議

**體制類型**: 牛市 / 熊市 / 震盪市 / 高波動  
**技術方法**: HMM · GARCH 波動率 · 移動平均系統 · 多時間框架分析

---

## 📰 子模組：新聞分析 (`news/`)

### `analyzer.py` — 核心新聞分析器 (1,141 行)

從多來源獲取新聞並執行情緒分析。

**主要類**: `CryptoNewsAnalyzer`  
**數據源**: CryptoPanic · RSS 聚合  
**功能**: 多來源抓取 → 情緒評分 → 關鍵字提取 → 事件檢測 → 重要性評分

### `evaluator.py` — 規則式事件評估器 (395 行)

「新聞大腦」— 使用關鍵字規則檢測重大事件。

**主要類**: `RuleBasedEvaluator`  
**流程**: 事件檢測 → `event_memory` 存入 → Hard Stop 判定 → `event_score` 輸出

### `prediction_loop.py` — RLHF 新聞預測循環 (901 行)

AI 預測→驗證→學習→優化的完整 RLHF 循環。

**主要類**: `NewsPredictionLoop`  
**衰減模型**:

| 事件類型 | 初始影響 | 衰減後 | 衰減期 |
|---------|---------|--------|-------|
| 駭客事件 | 9.0 | 3.0 | 10 天 |
| 升降息 | 8.5 | 4.0 | 15 天 |
| 戰爭 | 9.5 | 4.5 | 30 天 |
| ETF 審批 | 8.0 | 2.0 | 7 天 |

### `models.py` — 新聞數據模型 (103 行)

`NewsArticle` (標題/來源/情緒/關鍵字/重要性) · `NewsAnalysisResult` (統計摘要)

---

## 🔑 子模組：關鍵字系統 (`keywords/`)

### `manager.py` — 關鍵字管理器 v3.0 (907 行)

核心關鍵字匹配、預測記錄與準確率追蹤。

**主要類**: `KeywordManager`  
**數據來源**: `config/keywords/*.json`  
**持久化**: SQLite + JSON

### `learner.py` — 關鍵字學習器 (444 行)

RLHF 關鍵字權重更新與學習。

**主要類**: `KeywordLearner`  
**職責分離**: `KeywordManager`（唯讀查詢） ↔ `KeywordLearner`（寫入學習）

### `static_utils.py` — 靜態接口 (186 行)

`MarketKeywords` 類方法接口（委託 `KeywordManager` 單例）。

```python
score, keywords = MarketKeywords.get_importance_score(text)
bias, confidence = MarketKeywords.get_sentiment_bias(text)
```

### 其他

| 檔案 | 行數 | 說明 |
|------|------|------|
| `loader.py` | 132 | JSON 關鍵字檔案載入器 |
| `models.py` | 97 | `Keyword` · `KeywordMatch` · `PredictionRecord` |

---

## 📋 子模組：每日報告 (`daily_report/`)

自動生成每日市場分析報告，涵蓋宏觀、技術、情緒、策略與風險五大面向。

| 檔案 | 行數 | 職責 |
|------|------|------|
| `report_generator.py` | 291 | 報告生成→JSON 保存 |
| `market_data.py` | 387 | 全球市場數據收集（Yahoo Finance / CoinGecko） |
| `news_sentiment.py` | 132 | 新聞情緒整合（委託 `CryptoNewsAnalyzer`） |
| `risk_manager.py` | 460 | 帳戶分析 · 風險參數 · 持倉管理 |
| `strategy_planner.py` | 325 | 市場分析→策略建議 |
| `models.py` | 134 | 報告數據模型（`DailyReport` · `MarketCondition` 等） |

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

## 💡 使用示例

### 新聞分析
```python
from bioneuronai.analysis import CryptoNewsAnalyzer

analyzer = CryptoNewsAnalyzer()
result = await analyzer.analyze("BTCUSDT", hours=24)
print(f"情緒: {result.overall_sentiment}")
print(f"重大事件: {result.major_events}")
```

### 市場狀態識別
```python
from bioneuronai.analysis import MarketRegimeDetector

detector = MarketRegimeDetector()
regime = detector.detect(market_data)
print(f"當前體制: {regime.regime_type}")  # 牛市/熊市/震盪/高波動
```

### 特徵工程
```python
from bioneuronai.analysis import VolumeProfile

vp = VolumeProfile()
profile = vp.calculate(klines)
print(f"POC 價格: {profile.poc_price}")
print(f"價值區域: {profile.value_area}")
```

---

## 📚 相關文檔

- **NLP 訓練指南**: [NLP_TRAINING_GUIDE.md](../../../docs/NLP_TRAINING_GUIDE.md)
- **每日報告清單**: [DAILY_REPORT_CHECKLIST.md](../../../docs/DAILY_REPORT_CHECKLIST.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 2 月 15 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
