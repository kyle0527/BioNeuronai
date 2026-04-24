# RAG Core

`src/rag/core/` 放 RAG 的核心檢索能力：向量嵌入與統一檢索。這一層直接提供可被 `rag.__init__` 匯出的主要類別，`internal/`、`services/`、`monitoring/` 都是它的下游依賴。

## 資料夾內容

- `__init__.py`
  匯出 `EmbeddingService`、`EmbeddingModel`、`EmbeddingResult`、`UnifiedRetriever`、`RetrievalResult`、`RetrievalQuery`、`RetrievalSource`。
- `embeddings.py`
  定義嵌入模型列舉、嵌入結果資料類別與嵌入服務。
- `retriever.py`
  定義 `UnifiedRetriever`，負責快取、來源分派、檢索排序與交易用快捷入口。

## 主要檔案

### `embeddings.py`

- `EmbeddingModel`
  定義本地與 OpenAI 嵌入後端。
- `EmbeddingResult`
  單筆嵌入結果，包含原文、向量、模型名稱、維度、建立時間與 metadata。
- `EmbeddingService`
  主要方法：
  - `embed(text)`
  - `embed_batch(texts)`
  - `find_similar(query_embedding, candidate_embeddings, top_k)`
  - `cosine_similarity(vec1, vec2)`
  - `euclidean_distance(vec1, vec2)`
  - `get_stats()`

`EmbeddingService` 內部還負責模型初始化、OpenAI 嵌入呼叫、簡化 fallback 嵌入，以及輸入文字的快取。

### `retriever.py`

- `UnifiedRetriever`
  主要方法：
  - `retrieve(query)`
  - `retrieve_for_trading(symbol, hours, top_k, include_news, include_web, include_internal)`
  - `get_stats()`

內部流程分成幾步：

1. 正規化 `RetrievalQuery` 與來源列表。
2. 先查詢記憶體快取。
3. 依來源分派到 `_retrieve_internal()`、`_retrieve_web()`、`_retrieve_news()`、`_retrieve_trading_rules()`。
4. 合併、排序、截斷結果。
5. 若 `rag.monitoring` 可用，寫入檢索監控資料。

`RetrievalQuery`、`RetrievalResult`、`RetrievalSource` 都不是在這個檔案本地定義，而是自 `schemas.rag` 匯入，這裡只負責使用。

## 公開介面

```python
from rag.core import (
    EmbeddingService,
    EmbeddingModel,
    EmbeddingResult,
    UnifiedRetriever,
    RetrievalResult,
    RetrievalQuery,
    RetrievalSource,
)
```

## 文件層級

這個資料夾底下沒有更深一層的 README。`embeddings.py` 和 `retriever.py` 的細節由本文件直接說明。

## 相關文件

- [RAG 總覽](../README.md)
- [Internal 知識庫](../internal/README.md)
- [Services 服務層](../services/README.md)
- [Monitoring 監控](../monitoring/README.md)
