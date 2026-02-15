# RAG Internal — 內部知識庫模組

> **版本**: v2.0.0 | **更新日期**: 2026-02-15

---

## 模組定位

`src/rag/internal/` 管理系統的**內部知識庫**，包括交易規則、策略配置、市場分析報告、歷史交易記錄等文檔，並提供基於向量索引的語義搜索功能。

---

## 目錄結構

```
internal/
├── __init__.py            # 匯出核心類別
├── knowledge_base.py      # 內部知識庫管理器 (461 行)
└── faiss_index.py         # FAISS 向量索引包裝器 (197 行)
```

---

## knowledge_base.py — 內部知識庫

### DocumentType 枚舉

| 類型 | 說明 |
|------|------|
| `TRADING_RULE` | 交易規則 |
| `STRATEGY_CONFIG` | 策略配置 |
| `MARKET_ANALYSIS` | 市場分析 |
| `HISTORICAL_TRADE` | 歷史交易 |
| `NEWS_ARCHIVE` | 新聞歸檔 |
| `CUSTOM` | 自訂類型 |

### InternalKnowledgeBase 類別

| 方法 | 說明 |
|------|------|
| `add_document(doc)` | 新增文檔 |
| `update_document(doc)` | 更新文檔 |
| `delete_document(id)` | 刪除文檔 |
| `get_document(id)` | 取得單一文檔 |
| `search(query, top_k)` | 語義搜索 |
| `get_by_type(doc_type)` | 按類型篩選 |
| `get_by_tags(tags)` | 按標籤篩選 |
| `save_to_storage()` | 持久化存儲 |
| `get_stats()` | 統計資訊 |

### KnowledgeDocument 資料類

知識文檔：`id`, `title`, `content`, `doc_type`, `tags`, `metadata`, `embedding`, `score`。

### 內建交易規則

知識庫初始化時自動載入 `DEFAULT_TRADING_RULES`（5 條預設規則）：
1. 風險管理規則
2. 進場規則
3. 出場規則
4. 新聞交易規則
5. 市場狀態判斷

```python
from src.rag.internal import InternalKnowledgeBase, KnowledgeDocument, DocumentType

kb = InternalKnowledgeBase()
doc = KnowledgeDocument(
    id="rule-001",
    title="止損規則",
    content="單筆交易最大虧損不超過帳戶餘額的 2%",
    doc_type=DocumentType.TRADING_RULE,
    tags=["risk", "stop-loss"]
)
kb.add_document(doc)
results = kb.search("止損設定", top_k=3)
```

---

## faiss_index.py — 向量索引

FAISS 向量索引的包裝器，提供高效的向量檢索能力。**自動降級**：若 FAISS 不可用（未安裝），自動退回 NumPy 線性搜索。

### VectorIndex 類別

| 方法 | 說明 |
|------|------|
| `add(embeddings)` | 添加向量 |
| `search(query, k)` | 搜索最近鄰 |
| `reset()` | 清空索引 |
| `ntotal()` | 目前索引的向量數 |
| `get_stats()` | 統計資訊 |

### 工廠函數

```python
from src.rag.internal.faiss_index import create_index

index = create_index(dimension=384, use_gpu=False)
```

---

## 公開介面

```python
from src.rag.internal import (
    InternalKnowledgeBase, KnowledgeDocument, DocumentType,
)
```

---

> 📖 相關：[RAG 總覽](../README.md) | [Core 嵌入與檢索](../core/README.md)
>
> 📖 上層目錄：[src/rag/README.md](../README.md)