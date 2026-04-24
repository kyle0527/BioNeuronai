# RAG Services

`src/rag/services/` 是 RAG 與外部資料來源之間的橋接層。目前這一層只處理新聞分析整合，將 `bioneuronai.analysis.news` 的輸出轉成可被 RAG 使用與入庫的形式。

## 資料夾內容

- `__init__.py`
  以 graceful import 方式匯出 `NewsAdapter`、`NewsSearchResult`、`get_news_adapter()`、`ingest_news_analysis()`、`ingest_news_analysis_with_status()`。
- `news_adapter.py`
  新聞搜尋、事件上下文整理與新聞分析結果入庫主流程。

## 主要檔案

### `news_adapter.py`

- `NewsSearchResult`
  是 `schemas.rag.RAGNewsItem` 的型別別名，不是本地重新定義的資料類別。
- `NewsAdapter`
  主要方法：
  - `search(query, max_results, hours)`
  - `get_event_context(symbol)`
  - `ingest_news_analysis(analysis_result, symbol, hours)`
  - `ingest_news_analysis_with_status(analysis_result, symbol, hours)`

內部輔助流程：

- `_ensure_initialized()`
  延遲初始化 `CryptoNewsAnalyzer` 與事件評估器。
- `_ensure_knowledge_base()`
  準備 `InternalKnowledgeBase` 實例。
- `_extract_symbol(query)`
  從查詢中推測交易對。
- `_calculate_relevance(article, query)`
  計算新聞與查詢的相關性分數。
- `_check_for_events(article)`
  檢查新聞是否觸發事件規則。

### 模組層函式

- `get_news_adapter()`
  回傳全域單例 `NewsAdapter`。
- `ingest_news_analysis(...)`
  對外暴露的新聞入庫快捷函式。
- `ingest_news_analysis_with_status(...)`
  狀態化版本，額外回傳入庫狀態與訊息。

## 公開介面

```python
from rag.services import (
    NewsAdapter,
    NewsSearchResult,
    get_news_adapter,
    ingest_news_analysis,
    ingest_news_analysis_with_status,
)
```

## 文件層級

這個資料夾底下沒有更深一層的 README。服務層目前也只有新聞適配器這一條主線。

## 相關文件

- [RAG 總覽](../README.md)
- [Core 檢索層](../core/README.md)
- [Internal 知識庫](../internal/README.md)
