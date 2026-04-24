# RAG Internal

`src/rag/internal/` 管理內部知識庫與向量索引。這一層的責任是把規則、分析結果與歷史內容保存成可檢索的文件，並提供語義搜尋能力給 `rag.core.UnifiedRetriever`。

## 資料夾內容

- `__init__.py`
  匯出 `InternalKnowledgeBase`、`KnowledgeDocument`、`DocumentType`。
- `knowledge_base.py`
  文件模型、文件 CRUD、儲存與搜尋主流程。
- `faiss_index.py`
  向量索引包裝器；若 FAISS 不可用會退回 NumPy 線性搜尋。

## 主要檔案

### `knowledge_base.py`

- `DocumentType`
  內部知識文件類型列舉。
- `KnowledgeDocument`
  知識文件資料類別，提供 `to_dict()` / `from_dict()`。
- `InternalKnowledgeBase`
  主要方法：
  - `add_document(...)`
  - `add_news_analysis(analysis_result, symbol, hours, source)`
  - `update_document(doc_id, ...)`
  - `delete_document(doc_id)`
  - `get_document(doc_id)`
  - `search(query, top_k, min_score, doc_types)`
  - `get_by_type(doc_type)`
  - `get_by_tags(tags)`
  - `save_to_storage()`
  - `get_stats()`

這個檔案另外包含：

- `_load_default_rules()`
  啟動時載入預設交易規則。
- `_build_news_doc_id(...)`
  為新聞分析結果建立穩定文件 ID，避免重複入庫。
- `_rebuild_index()`
  文件集合變動後重建向量索引。
- `_load_from_storage()`
  從本地儲存載入現有知識文件。

### `faiss_index.py`

- `VectorIndex`
  主要方法：
  - `add(embeddings)`
  - `search(query_embedding, k)`
  - `reset()`
  - `ntotal()`
  - `is_using_faiss()`
  - `get_stats()`
- `create_index(dimension, use_gpu=False)`
  建立索引的工廠函式。

## 公開介面

```python
from rag.internal import (
    InternalKnowledgeBase,
    KnowledgeDocument,
    DocumentType,
)
```

## 文件層級

這個資料夾底下沒有更深一層的 README。知識文件模型、入庫流程與向量索引都由本文件直接描述。

## 相關文件

- [RAG 總覽](../README.md)
- [Core 檢索層](../core/README.md)
- [Services 服務層](../services/README.md)
