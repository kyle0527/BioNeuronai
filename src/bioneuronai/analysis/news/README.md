# 分析模組 — 新聞分析系統 (News)

> **路徑**: `src/bioneuronai/analysis/news/`  
> **更新日期**: 2026-04-20
> **文件焦點**: 子模組內部能力、Analysis -> RAG 寫入、事件規則與驗證循環（系統分層請看上層 [analysis README](../README.md)）

## 目錄

1. [子模組職責](#子模組職責)
2. [檔案結構](#檔案結構)
3. [對外導出](#對外導出依-__init__py)
4. [核心元件](#核心元件)
5. [現行資料路徑](#現行資料路徑)
6. [維護邊界](#維護邊界)

---

## 子模組職責

`news` 負責新聞理解與事件判讀：
1. 抓取新聞（CryptoPanic + RSS）
2. 情緒分析與事件偵測
3. 規則式事件評估與事件分數查詢
4. 預測驗證循環
5. 分析結果寫入 RAG 知識庫

---

## 檔案結構

```text
news/
├── __init__.py          # 對外導出
├── models.py            # NewsArticle / NewsAnalysisResult
├── analyzer.py          # CryptoNewsAnalyzer
├── evaluator.py         # RuleBasedEvaluator
├── prediction_loop.py   # NewsPredictionLoop / PredictionScheduler
└── README.md
```

---

## 對外導出（依 `__init__.py`）

1. `NewsArticle`
2. `NewsAnalysisResult`
3. `CryptoNewsAnalyzer`
4. `get_news_analyzer`
5. `RuleBasedEvaluator`
6. `get_rule_evaluator`
7. `EventRule`（由 `schemas.rag` 導入）
8. `NewsPredictionLoop`

---

## 核心元件

### `CryptoNewsAnalyzer` (`analyzer.py`)

主要公開方法：
1. `analyze_news(symbol="BTCUSDT", hours=24)`
2. `get_quick_summary(symbol="BTCUSDT")`
3. `should_trade(symbol="BTCUSDT")`
4. `evaluate_pending_news()`

重點：
1. `analyze_news()` 完成分析後會呼叫 `_ingest_analysis_to_rag()`
2. `_ingest_analysis_to_rag()` 透過 `rag.services.news_adapter.ingest_news_analysis_with_status(...)`
3. 入庫狀態以 `OK / NO_DATA / ERROR` 區分，失敗記錄但不阻斷主分析流程

### `RuleBasedEvaluator` (`evaluator.py`)

重點：
1. `EventRule` 以 `schemas.rag` 為單一事實來源（SSOT）
2. 規則載入順序：`config/event_rules.json` -> `DEFAULT_RULES` -> `custom_rules`
3. 提供 `get_current_event_score(symbol=None)` 供上層風險檢查

### `NewsPredictionLoop` (`prediction_loop.py`)

重點：
1. 預測記錄、到期驗證、準確率統計
2. 結果回饋關鍵字權重
3. `PredictionScheduler` 提供排程驗證能力

---

## 現行資料路徑

1. 新聞記錄：`data/bioneuronai/trading/sop/news_records.json`
2. 預測資料：`news_predictions/predictions.jsonl`
3. 事件記憶：`data/bioneuronai/trading/runtime/trading.db`（由 `DatabaseManager` 管理）

---

## 維護邊界

1. 這層只描述新聞分析、事件評估、預測驗證與 RAG 入庫。
2. `EventRule` 與 `EventContext` 的資料結構以 `schemas.rag` 為準，不在此重新定義。
3. 若 `NewsAdapter` 入庫介面或狀態碼改變，需同步更新本文件與 `rag/services/README.md`。

---

> 上層架構說明：[analysis README](../README.md)
