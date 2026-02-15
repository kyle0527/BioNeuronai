# RAG Services — 外部數據服務層

> **版本**: v2.0.0 | **更新日期**: 2026-02-15

---

## 模組定位

`src/rag/services/` 是 RAG 系統與外部數據源之間的**橋接層**，將 `bioneuronai` 的分析模組封裝為 RAG 相容介面。

---

## 目錄結構

```
services/
├── __init__.py            # 匯出 NewsAdapter + PreTradeCheckSystem
└── news_adapter.py        # 新聞適配器 (358 行)
```

---

## news_adapter.py — 新聞適配器

將 `bioneuronai.analysis.news.CryptoNewsAnalyzer` 封裝為 RAG 相容介面，支援延遲初始化。

### NewsSearchResult 資料類

新聞搜索結果，與 RAG `RetrievalResult` 相容：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `title` | str | 新聞標題 |
| `snippet` | str | 摘要 |
| `url` | str | 來源 URL |
| `source` | str | 來源名稱 |
| `relevance_score` | float | 相關性分數 |
| `sentiment` | float | 情緒分數 |

### NewsAdapter 類別

| 方法 | 說明 |
|------|------|
| `search(query, max_results, hours)` | 搜索相關新聞 |
| `get_event_context(symbol)` | 取得指定幣種的事件上下文 |

**內部方法**：
- `_extract_symbol()` — 從查詢中提取交易對符號
- `_calculate_relevance()` — 計算相關性分數
- `_check_for_events()` — 檢測事件觸發

### 工廠函數

```python
from src.rag.services import get_news_adapter

adapter = get_news_adapter()  # 全局單例
results = adapter.search("BTC 突破新高", max_results=5, hours=24)
```

---

## PreTradeCheckSystem 整合

`services/__init__.py` 也從 `bioneuronai.trading.pretrade_automation` 匯入 `PreTradeCheckSystem`，提供交易前檢查的 RAG 整合入口。

```python
from src.rag.services import PreTradeCheckSystem
```

---

## 依賴關係

```
services/
├── → bioneuronai.analysis.news (CryptoNewsAnalyzer)
├── → bioneuronai.trading.pretrade_automation (PreTradeCheckSystem)
└── → schemas.rag (RAGNewsItem, NewsSentiment, EventContext, EventRule)
```

---

> 📖 相關：[RAG 總覽](../README.md) | [Core 檢索器](../core/README.md)
>
> 📖 上層目錄：[src/rag/README.md](../README.md)