# RAG 模組 — 檢索增強生成系統

> **版本**: v2.1 | **更新日期**: 2026-04-20

---

## 目錄

- [模組定位](#模組定位)
- [架構總覽](#架構總覽)
- [目錄結構](#目錄結構)
- [子模組說明](#子模組說明)
- [工作流程](#工作流程)
- [快速開始](#快速開始)
- [API 參考](#api-參考)
- [可用性旗標](#可用性旗標)
- [整合模組](#整合模組)
- [技術規格](#技術規格)

---

## 模組定位

`src/rag/` 是 BioNeuronai 的**檢索增強生成 (RAG)** 系統，整合向量嵌入、語義檢索、內部知識庫和外部數據源，為交易決策提供上下文增強的資訊檢索能力。

> ⚠️ 此模組取代了 `src/nlp/rag_system.py`（已廢棄），是 RAG 功能的唯一正式實現。

---

## 架構總覽

```
┌──────────────────────────────────────────────────────────┐
│                      RAG 系統架構                         │
├─────────────┬────────────────────────────────────────────┤
│  Core 層     │  EmbeddingService ←→ UnifiedRetriever      │
│             │  向量嵌入 + 統一檢索介面                      │
├─────────────┼────────────────────────────────────────────┤
│  Internal 層 │  InternalKnowledgeBase + VectorIndex        │
│             │  文檔管理 + FAISS 向量索引                    │
├─────────────┼────────────────────────────────────────────┤
│  Services 層 │  NewsAdapter                                  │
│             │  外部數據橋接（新聞）                           │
├─────────────┼────────────────────────────────────────────┤
│  Monitoring  │  RAGMonitor                                 │
│             │  請求追蹤 / 延遲統計 / 快取命中率              │
└─────────────┴────────────────────────────────────────────┘
```

---

## 目錄結構

```
src/rag/
├── __init__.py                  # 模組入口 (250 行)，統一匯出 + 工廠函數
├── README.md                    # 本文件
├── core/
│   ├── __init__.py              # 匯出核心類別
│   ├── embeddings.py            # 向量嵌入服務 (311 行)
│   ├── retriever.py             # 統一檢索器 (411 行)
│   └── README.md
├── internal/
│   ├── __init__.py              # 匯出知識庫類別
│   ├── knowledge_base.py        # 內部知識庫 (576 行)
│   ├── faiss_index.py           # FAISS 向量索引 (217 行)
│   └── README.md
├── services/
│   ├── __init__.py              # 匯出服務類別
│   ├── news_adapter.py          # 新聞適配器 (482 行)
│   └── README.md
└── monitoring/
    ├── __init__.py              # RAG 監控器 (273 行)
    └── README.md
```

---

## 子模組說明

### Core — 核心嵌入與檢索

| 檔案 | 行數 | 主要類別 | 說明 |
|------|------|----------|------|
| `embeddings.py` | 311 | `EmbeddingService`, `EmbeddingModel`, `EmbeddingResult` | 支持本地模型 + OpenAI API，含快取機制 |
| `retriever.py` | 411 | `UnifiedRetriever`, `RetrievalQuery`, `RetrievalResult`, `RetrievalSource` | 整合多種數據源的統一檢索 |

### Internal — 內部知識庫

| 檔案 | 行數 | 主要類別 | 說明 |
|------|------|----------|------|
| `knowledge_base.py` | 576 | `InternalKnowledgeBase`, `KnowledgeDocument`, `DocumentType` | 文檔 CRUD + 語義搜索 + 持久化 |
| `faiss_index.py` | 217 | `VectorIndex` | FAISS 向量索引，不可用時降級為 NumPy |

### Services — 外部數據橋接

| 檔案 | 行數 | 主要類別 | 說明 |
|------|------|----------|------|
| `news_adapter.py` | 482 | `NewsAdapter`, `NewsSearchResult` | CryptoNewsAnalyzer 的 RAG 相容封裝 |

### Monitoring — 系統監控

| 檔案 | 行數 | 主要類別 | 說明 |
|------|------|----------|------|
| `__init__.py` | 273 | `RAGMonitor`, `RetrievalMetrics` | 請求追蹤、延遲、快取、錯誤統計 |

---

## 工作流程

```
使用者查詢
    │
    ▼
UnifiedRetriever.retrieve(query)
    │
    ├─ 內部知識庫 ─→ InternalKnowledgeBase.search()
    │                    └─ VectorIndex (FAISS/NumPy)
    │
    ├─ 新聞搜索 ───→ NewsAdapter.search()
    │                    └─ CryptoNewsAnalyzer
    │
    ├─ 交易規則 ───→ 內建 DEFAULT_TRADING_RULES
    │
    └─ 其他來源 ───→ Web / Social / Historical
    │
    ▼
RetrievalResult[] ──→ RAGMonitor.log_retrieval()
    │
    ▼
排序 + 過濾 → 傳回結果
```

---

## 快速開始

### 建立檢索器

```python
from rag import create_unified_retriever

retriever = create_unified_retriever()
```

### 執行檢索

```python
from rag.core import RetrievalQuery, RetrievalSource

query = RetrievalQuery(
    query="BTC 大額轉帳風險",
    sources=[RetrievalSource.INTERNAL_KNOWLEDGE, RetrievalSource.NEWS_API],
    top_k=5,
    min_relevance=0.3
)
results = retriever.retrieve(query)

for r in results:
    print(f"[{r.source.value}] {r.title} (相關性: {r.relevance_score:.2f})")
```

### 交易專用檢索

```python
results = retriever.retrieve_for_trading(symbol="BTCUSDT")
```

### 管理知識庫

```python
from rag.internal import InternalKnowledgeBase, KnowledgeDocument, DocumentType

kb = InternalKnowledgeBase()
kb.add_document(KnowledgeDocument(
    id="rule-custom-001",
    title="自訂風控規則",
    content="連續虧損 3 次後暫停交易 24 小時",
    doc_type=DocumentType.TRADING_RULE,
    tags=["risk", "custom"]
))
```

### 查看監控

```python
from rag.monitoring import get_monitor

monitor = get_monitor()
monitor.print_stats()
```

---

## API 參考

### `__init__.py` 頂層函數

| 函數 | 回傳類型 | 說明 |
|------|----------|------|
| `create_unified_retriever()` | `UnifiedRetriever` | 工廠函數，建立預設配置的檢索器 |
| `get_rag_status()` | `dict` | 取得 RAG 模組狀態（各子模組可用性） |

### 核心匯出

```python
from rag import (
    # Core
    EmbeddingService, EmbeddingModel, EmbeddingResult,
    UnifiedRetriever, RetrievalResult, RetrievalQuery, RetrievalSource,
    # Internal
    InternalKnowledgeBase, KnowledgeDocument, DocumentType,
    # Services
    NewsAdapter, NewsSearchResult, get_news_adapter,
    # Factory
    create_unified_retriever, get_rag_status,
)
```

---

## 可用性旗標

`__init__.py` 定義了 4 個布林旗標，指示各依賴模組是否可用：

| 旗標 | 依賴 | 說明 |
|------|------|------|
| `CORE_AVAILABLE` | rag.core | 核心嵌入 + 檢索 |
| `INTERNAL_KB_AVAILABLE` | rag.internal | 內部知識庫 |
| `ANALYSIS_AVAILABLE` | bioneuronai.analysis | 關鍵字 + 新聞分析 |
| `NEWS_ADAPTER_AVAILABLE` | rag.services | 新聞適配器 |

```python
from rag import CORE_AVAILABLE, ANALYSIS_AVAILABLE
if CORE_AVAILABLE:
    retriever = create_unified_retriever()
```

---

## 整合模組

RAG 模組與 bioneuronai 的以下模組整合：

| 整合來源 | 匯入 | 用途 |
|----------|------|------|
| `bioneuronai.analysis.keywords` | `KeywordManager` | 關鍵字匹配 |
| `bioneuronai.analysis.news` | `CryptoNewsAnalyzer` | 新聞分析 |
| `schemas.rag` | RAG Pydantic 模型 | 結構化數據定義 |

---

## 技術規格

| 項目 | 規格 |
|------|------|
| **版本** | 2.1 |
| **Python 檔案** | 10 個 |
| **總行數** | 2,587 行 |
| **類別數** | 11 個 |
| **嵌入後端** | 本地 (sentence-transformers) / OpenAI API |
| **向量索引** | FAISS (可選，降級為 NumPy) |
| **監控** | 線程安全，單例模式 |
| **高可用性** | try/except 容錯，全部可選依賴 |

---

> 📖 子模組文檔：[Core](core/README.md) | [Internal](internal/README.md) | [Services](services/README.md) | [Monitoring](monitoring/README.md)
>
> 📖 相關文檔：[RAG 技術手冊](../../docs/RAG_TECHNICAL_MANUAL.md) | [Schemas — rag.py](../schemas/README.md)
>
> 📖 上層目錄：[src/README.md](../README.md)
