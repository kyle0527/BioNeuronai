# RAG Services — 外部數據服務層

> **版本**: v2.1 | **更新日期**: 2026-04-20

---

## 目錄

1. [模組定位](#模組定位)
2. [目錄結構](#目錄結構)
3. [news_adapter.py — 新聞適配器](#news_adapterpy-新聞適配器)
4. [依賴關係](#依賴關係)

---

## 模組定位

`src/rag/services/` 是 RAG 系統與外部數據源之間的**橋接層**，將 `bioneuronai` 的分析模組封裝為 RAG 相容介面。

---

## 目錄結構

```
services/
├── __init__.py            # 匯出 NewsAdapter + ingest_news_analysis
└── news_adapter.py        # 新聞適配器（482 行，含唯一入庫入口）
```

---

## news_adapter.py — 新聞適配器

將 `bioneuronai.analysis.news.CryptoNewsAnalyzer` 封裝為 RAG 相容介面，支援延遲初始化。

### NewsSearchResult 型別

`NewsSearchResult` 目前是 `schemas.rag.RAGNewsItem` 的 type alias，不是本地重複定義的 dataclass。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `title` | str | 新聞標題 |
| `summary` | str | 摘要 |
| `url` | str | 來源 URL |
| `source` | str | 來源名稱 |
| `published_at` | datetime | 發布時間 |
| `sentiment` | `NewsSentiment` | 情緒分類 |
| `sentiment_score` | float | 情緒分數 |
| `category` | `NewsCategory` | 新聞分類 |
| `relevance_score` | float | 相關性分數 |

### NewsAdapter 類別

| 方法 | 說明 |
|------|------|
| `search(query, max_results, hours)` | 搜索相關新聞，回傳 `List[RAGNewsItem]` |
| `get_event_context(symbol)` | 取得指定幣種的事件上下文（呼叫 `RuleBasedEvaluator.get_current_event_score()`） |
| `ingest_news_analysis(analysis_result, symbol, hours)` | 唯一新聞知識寫入入口，將分析結果寫入 InternalKnowledgeBase |
| `ingest_news_analysis_with_status(analysis_result, symbol, hours)` | 狀態化入庫入口，回傳 `OK/NO_DATA/ERROR` + `ingested_docs` + `message` |

**內部方法**：
- `_ensure_initialized()` — 延遲初始化 `CryptoNewsAnalyzer` 與 `RuleBasedEvaluator`
- `_extract_symbol()` — 從查詢中提取交易對符號
- `_calculate_relevance()` — 計算相關性分數
- `_check_for_events()` — 檢測事件觸發（呼叫 `RuleBasedEvaluator.evaluate_headline()`）

> 2026-03-29 修復：`get_event_context()` 原本呼叫不存在的 `get_total_event_score()` / `get_active_events()`，已改為正確的 `get_current_event_score()`（回傳 `Tuple[float, List[Dict]]`）。

### 工廠函數

```python
from rag.services import (
    get_news_adapter,
    ingest_news_analysis,
    ingest_news_analysis_with_status,
)

adapter = get_news_adapter()  # 全局單例
results = adapter.search("BTC 突破新高", max_results=5, hours=24)
# analysis 結果入庫
count = ingest_news_analysis(analysis_result, symbol="BTCUSDT", hours=24)
status = ingest_news_analysis_with_status(analysis_result, symbol="BTCUSDT", hours=24)
```

### 新增（2026-03-30）

- 已補齊 B.3 缺口：`news_adapter.py` 提供唯一寫入函數 `ingest_news_analysis()`。
- 補強入庫可觀測性：新增 `ingest_news_analysis_with_status()`，可區分 `NO_DATA` 與 `ERROR`。
- `InternalKnowledgeBase` 新增新聞專用 API：`add_news_analysis()`。
- `CryptoNewsAnalyzer.analyze_news()` 執行後會自動呼叫入庫（失敗不阻塞主流程）。

---

## 依賴關係

```
services/
├── → bioneuronai.analysis.news (CryptoNewsAnalyzer)
└── → schemas.rag (RAGNewsItem, NewsSentiment, EventContext, EventRule)
```

---

> 📖 相關：[RAG 總覽](../README.md) | [Core 檢索器](../core/README.md)
>
> 📖 上層目錄：[src/rag/README.md](../README.md)
