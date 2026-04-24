# RAG Monitoring

`src/rag/monitoring/` 提供 RAG 執行期間的輕量監控。這個資料夾只有一個 `__init__.py`，所以本 README 直接說明全部內容。

## 資料夾內容

- `__init__.py`
  定義檢索指標資料類別、監控器本體與全域單例入口。

## 主要內容

- `RetrievalMetrics`
  單次檢索記錄，包含時間、延遲、是否命中快取、結果數量、來源與錯誤訊息。
- `RAGMonitor`
  主要方法：
  - `log_retrieval(latency_ms, cache_hit, result_count, source, error=None)`
  - `get_stats()`
  - `get_recent_history(minutes=5)`
  - `reset()`
  - `print_stats()`
- `get_monitor()`
  取得全域監控器實例。
- `reset_monitor()`
  重置全域監控器。

`UnifiedRetriever` 在模組可用時會呼叫 `get_monitor()` 寫入檢索紀錄，所以這一層是觀測能力，不是檢索主流程本身。

## 文件層級

這個資料夾底下沒有更深一層的 README，也沒有其他 Python 檔案。

## 相關文件

- [RAG 總覽](../README.md)
- [Core 檢索層](../core/README.md)
