# RAG Monitoring — 系統監控模組

> **版本**: v2.1 | **更新日期**: 2026-04-20

---

## 目錄

1. [模組定位](#模組定位)
2. [目錄結構](#目錄結構)
3. [核心類別](#核心類別)
4. [全域函數](#全域函數)
5. [整合方式](#整合方式)

---

## 模組定位

`src/rag/monitoring/` 提供 RAG 系統的**輕量級運行時監控**，追蹤檢索請求的數量、延遲、快取命中率和錯誤率。

---

## 目錄結構

```
monitoring/
└── __init__.py        # 監控器實現 (273 行)
```

---

## 核心類別

### RetrievalMetrics 資料類

單次檢索的指標記錄：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `timestamp` | datetime | 時間戳 |
| `latency_ms` | float | 延遲（毫秒） |
| `cache_hit` | bool | 是否命中快取 |
| `result_count` | int | 結果數量 |
| `source` | str | 檢索來源 |
| `error` | str | 錯誤信息（若有） |

### RAGMonitor 類別

線程安全的 RAG 系統監控器。

| 方法 | 說明 |
|------|------|
| `log_retrieval(metrics)` | 記錄一次檢索指標 |
| `get_stats()` | 取得統計摘要 |
| `get_recent_history(n)` | 取得最近 n 次記錄 |
| `reset()` | 重置所有統計 |
| `print_stats()` | 輸出統計報告 |

**監控指標**：
- 總請求數、成功 / 失敗數
- 平均延遲、P50 / P95 / P99 延遲
- 快取命中率
- 各來源的請求分布

---

## 全域函數

| 函數 | 說明 |
|------|------|
| `get_monitor()` | 取得全域監控器實例（單例模式） |
| `reset_monitor()` | 重置全域監控器 |

```python
from rag.monitoring import get_monitor

monitor = get_monitor()
monitor.print_stats()  # 輸出監控報告
```

---

## 整合方式

`UnifiedRetriever` 在每次檢索時自動調用 `get_monitor()` 記錄指標，無需手動呼叫。

---

> 📖 相關：[RAG 總覽](../README.md) | [Core 檢索器](../core/README.md)
>
> 📖 上層目錄：[src/rag/README.md](../README.md)
