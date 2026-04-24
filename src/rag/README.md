# RAG 模組

`src/rag/` 是專案的檢索增強生成子系統。這一層只說明模組分工、依賴方向與子文件入口；具體類別、方法與檔案責任放在下一層 README。

## 模組定位

RAG 模組負責三件事：

1. 提供嵌入與統一檢索入口。
2. 管理內部知識庫與向量索引。
3. 橋接新聞分析結果，並提供監控資料。

這個 package 也是 `nlp/rag_system.py` 的正式替代實作。若是新程式，應優先使用 `src/rag/` 而不是舊的相容檔案。

## 目錄結構

- `__init__.py`
  頂層匯出與工廠函式，包含可用性旗標與 `create_unified_retriever()`。
- `core/`
  嵌入與統一檢索。
  文件：[core/README.md](core/README.md)
- `internal/`
  內部知識庫與向量索引。
  文件：[internal/README.md](internal/README.md)
- `services/`
  外部資料橋接，目前以新聞適配器為主。
  文件：[services/README.md](services/README.md)
- `monitoring/`
  檢索監控與統計。
  文件：[monitoring/README.md](monitoring/README.md)

## 頂層介面

`rag.__init__` 目前負責：

- 匯出 core 類別：
  `EmbeddingService`、`EmbeddingModel`、`EmbeddingResult`、`UnifiedRetriever`、`RetrievalResult`、`RetrievalQuery`、`RetrievalSource`
- 匯出 internal 類別：
  `InternalKnowledgeBase`、`KnowledgeDocument`、`DocumentType`
- 橋接 analysis / services：
  `KeywordManager`、`KeywordMatch`、`get_keyword_manager()`、`CryptoNewsAnalyzer`、`NewsArticle`、`get_news_analyzer()`、`NewsAdapter`、`NewsSearchResult`、`get_news_adapter()`、`ingest_news_analysis()`、`ingest_news_analysis_with_status()`
- 提供工廠與狀態函式：
  `create_unified_retriever()`、`get_rag_status()`
- 提供可用性旗標：
  `CORE_AVAILABLE`、`INTERNAL_KB_AVAILABLE`、`ANALYSIS_AVAILABLE`、`NEWS_ADAPTER_AVAILABLE`

## 依賴方向

```text
schemas.rag
    ↑
core ────────┐
internal ────┼──→ rag.__init__
services ────┘
    ↑
bioneuronai.analysis

monitoring
    ↑
core.retriever
```

重點是：

- `schemas.rag` 是 `RetrievalQuery`、`RetrievalResult`、`RetrievalSource` 等型別的正式來源。
- `services/` 依賴 `bioneuronai.analysis` 與 `internal/`。
- `monitoring/` 不參與檢索邏輯，只負責觀測。

## 文件鏈

- 下一層文件：
  [core/README.md](core/README.md)
  [internal/README.md](internal/README.md)
  [services/README.md](services/README.md)
  [monitoring/README.md](monitoring/README.md)
- 上一層文件：
  [src/README.md](../README.md)
- 相關文件：
  [schemas/README.md](../schemas/README.md)

## 使用入口

```python
from rag import create_unified_retriever, get_rag_status

status = get_rag_status()
retriever = create_unified_retriever()
```
