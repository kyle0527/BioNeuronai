# RAG Core — 核心檢索與嵌入模組

> **版本**: v2.1 | **更新日期**: 2026-04-05

---

## 模組定位

`src/rag/core/` 提供 RAG 系統的兩大核心能力：**向量嵌入 (Embedding)** 和 **統一檢索 (Retrieval)**。

---

## 目錄結構

```
core/
├── __init__.py          # 匯出核心類別
├── embeddings.py        # 向量嵌入服務 (287 行)
└── retriever.py         # 統一檢索器 (338 行)
```

---

## embeddings.py — 向量嵌入服務

支持多種嵌入後端的統一嵌入介面。

### EmbeddingModel 枚舉

| 模型 | 說明 |
|------|------|
| `LOCAL_MINILM` | sentence-transformers MiniLM |
| `LOCAL_MPNET` | sentence-transformers MPNet |
| `LOCAL_MULTILINGUAL` | 多語言本地模型 |
| `OPENAI_SMALL` | OpenAI text-embedding-3-small |
| `OPENAI_LARGE` | OpenAI text-embedding-3-large |
| `OPENAI_ADA` | OpenAI text-embedding-ada-002 |
| `CUSTOM` | 自訂模型 |

### EmbeddingService 類別

| 方法 | 說明 |
|------|------|
| `embed(text)` | 單條文本向量化 |
| `embed_batch(texts)` | 批量文本向量化 |
| `find_similar()` | 相似度搜索 |
| `cosine_similarity()` | 餘弦相似度（靜態方法） |
| `euclidean_distance()` | 歐幾里得距離（靜態方法） |
| `get_stats()` | 取得統計資訊 |

### EmbeddingResult 資料類

嵌入結果：`text`, `embedding`, `model`, `dimensions`, `created_at`, `metadata`。

```python
from src.rag.core import EmbeddingService, EmbeddingModel

service = EmbeddingService(model=EmbeddingModel.LOCAL_MINILM)
result = service.embed("BTC 今日走勢分析")
# result.embedding → numpy array
```

---

## retriever.py — 統一檢索器

整合內部知識庫、網路搜索、新聞 API 等多種數據源的統一檢索介面。

### RetrievalSource 枚舉

> ⚠️ **單一事實來源**：定義於 `schemas/rag.py`，`retriever.py` 從此導入，不在本地重複定義。

| 來源 | 說明 |
|------|------|
| `INTERNAL_KNOWLEDGE` | 內部知識庫 |
| `WEB_SEARCH` | 網路搜索 |
| `NEWS_API` | 新聞 API |
| `SOCIAL_MEDIA` | 社群媒體 |
| `HISTORICAL_DATA` | 歷史數據 |
| `TRADING_RULES` | 交易規則 |
| `ALL` | 所有來源 |

### UnifiedRetriever 類別

| 方法 | 說明 |
|------|------|
| `retrieve(query)` | 通用檢索（接受 `RetrievalQuery`） |
| `retrieve_for_trading(symbol, ...)` | 交易專用檢索（快捷方法） |
| `get_stats()` | 取得統計資訊 |

### 相關資料類（定義於 `schemas/rag.py`）

- `RetrievalQuery` — 檢索查詢（query, sources, top_k, min_relevance, time_range_hours, filters）
- `RetrievalResult` — 檢索結果（content, source, relevance_score, timestamp, url, title, metadata, to_dict()）

> 2026-03-29：`RetrievalSource`、`RetrievalQuery`、`RetrievalResult` 已從 `retriever.py` 移除重複定義，統一由 `schemas/rag.py` 提供（Single Source of Truth）。`INTERNAL_KB` 值名稱整合為 `INTERNAL_KNOWLEDGE`。

```python
from src.rag.core import UnifiedRetriever, RetrievalQuery, RetrievalSource

retriever = UnifiedRetriever()
query = RetrievalQuery(
    query="BTC 大額轉帳",
    sources=[RetrievalSource.NEWS_API, RetrievalSource.INTERNAL_KNOWLEDGE],
    top_k=5
)
results = retriever.retrieve(query)
```

---

## 公開介面

```python
from src.rag.core import (
    EmbeddingService, EmbeddingModel, EmbeddingResult,
    UnifiedRetriever, RetrievalResult, RetrievalQuery, RetrievalSource,
)
```

---

> 📖 相關：[RAG 總覽](../README.md) | [Internal 知識庫](../internal/README.md) | [Services 服務層](../services/README.md)
>
> 📖 上層目錄：[src/rag/README.md](../README.md)
