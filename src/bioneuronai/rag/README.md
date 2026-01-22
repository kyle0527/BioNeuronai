# RAG 系統 (Retrieval-Augmented Generation)

**路徑**: `src/bioneuronai/rag/`  
**版本**: v1.0  
**更新日期**: 2026-01-22

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [子模組結構](#子模組結構)
3. [工作流程](#工作流程)
4. [使用示例](#使用示例)
5. [相關文檔](#相關文檔)

---

## 🎯 系統概述

RAG (Retrieval-Augmented Generation) 系統為 AI 模型提供外部知識檢索能力，增強生成結果的準確性和相關性。

### 系統職責
- ✅ 文本向量化 (Embeddings)
- ✅ 相似性檢索 (Retrieval)
- ✅ 知識庫管理 (Knowledge Base)
- ✅ 服務層接口 (Services)

---

## 📦 子模組結構

### 1. [core/](core/README.md) - 核心組件
基礎的文本嵌入和檢索功能。

**核心文件**:
- `embeddings.py` - 文本向量化
- `retriever.py` - 文檔檢索

**主要功能**:
- 文本轉向量
- 向量相似度計算
- Top-K 檢索

### 2. [internal/](internal/README.md) - 內部模塊
知識庫的內部實現。

**核心文件**:
- `knowledge_base.py` - 知識庫管理

**主要功能**:
- 文檔存儲
- 索引管理
- 版本控制

### 3. [services/](services/README.md) - 服務層
對外提供的服務接口 (當前為佔位模組)。

**規劃功能**:
- API 接口
- 批量處理
- 異步查詢

---

## 🔄 工作流程

```
用戶查詢
    │
    ▼
[embeddings.py]
將查詢轉換為向量
    │
    ▼
[retriever.py]
在向量空間中檢索
    │
    ▼
[knowledge_base.py]
獲取完整文檔內容
    │
    ▼
[services/]
返回結構化結果
    │
    ▼
AI 模型生成答案
```

---

## 🏗️ 系統架構

```
rag/
│
├── core/                  # 核心層
│   ├── embeddings.py      # 文本 → 向量
│   └── retriever.py       # 向量 → 文檔
│
├── internal/              # 數據層
│   └── knowledge_base.py  # 文檔存儲與索引
│
└── services/              # 服務層 (規劃中)
    └── __init__.py        # 服務接口
```

---

## 💡 使用示例

### 1. 完整 RAG 流程
```python
from src.bioneuronai.rag.core import Embeddings, Retriever
from src.bioneuronai.rag.internal import KnowledgeBase

# 初始化組件
embeddings = Embeddings()
kb = KnowledgeBase()
retriever = Retriever(embeddings, kb)

# 添加文檔到知識庫
documents = [
    "加密貨幣是數字或虛擬貨幣...",
    "比特幣是第一個去中心化的加密貨幣...",
    "以太坊支持智能合約..."
]
kb.add_documents(documents)

# 檢索相關文檔
query = "什麼是智能合約?"
results = retriever.retrieve(query, top_k=3)

# 使用檢索結果增強 AI 回答
context = "\n".join([doc['content'] for doc in results])
answer = ai_model.generate(query, context=context)
```

### 2. 只使用嵌入功能
```python
from src.bioneuronai.rag.core import Embeddings

# 初始化嵌入模型
embeddings = Embeddings(model='sentence-transformers')

# 生成文本向量
text = "區塊鏈技術"
vector = embeddings.encode(text)

# 計算相似度
text1 = "比特幣"
text2 = "以太坊"
similarity = embeddings.cosine_similarity(text1, text2)
```

### 3. 獨立使用知識庫
```python
from src.bioneuronai.rag.internal import KnowledgeBase

# 初始化知識庫
kb = KnowledgeBase(storage_path='./knowledge_db')

# 添加帶元數據的文檔
kb.add_document(
    content="趨勢跟隨策略適用於單邊上漲行情",
    metadata={
        'category': 'trading_strategy',
        'strategy_type': 'trend_following',
        'timestamp': '2026-01-22'
    }
)

# 按類別檢索
strategy_docs = kb.get_by_category('trading_strategy')

# 按時間檢索
recent_docs = kb.get_recent(days=7)
```

---

## 🔧 配置選項

### 嵌入模型配置
```python
embeddings_config = {
    'model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    'device': 'cuda',  # or 'cpu'
    'batch_size': 32,
    'normalize': True
}
```

### 檢索器配置
```python
retriever_config = {
    'top_k': 5,
    'similarity_threshold': 0.7,
    'rerank': True,
    'diversity_weight': 0.3
}
```

### 知識庫配置
```python
kb_config = {
    'storage_type': 'vector_db',  # or 'sqlite', 'json'
    'index_type': 'hnsw',         # or 'flat', 'ivf'
    'dimension': 384,
    'metric': 'cosine'
}
```

---

## 📊 性能指標

| 操作 | 延遲 | 吞吐量 |
|------|------|--------|
| 文本嵌入 | < 50ms | 1000 docs/s |
| 向量檢索 | < 10ms | 10000 queries/s |
| 文檔添加 | < 5ms | 5000 docs/s |

---

## 🛣️ 開發路線圖

### v1.0 (當前)
- ✅ 基礎嵌入功能
- ✅ 簡單檢索
- ✅ 知識庫存儲

### v1.1 (規劃)
- ⏳ 多模型支持
- ⏳ 混合檢索 (向量 + 關鍵字)
- ⏳ 查詢重寫

### v2.0 (未來)
- 📋 分佈式檢索
- 📋 實時索引更新
- 📋 多語言支持

---

## 📚 相關文檔

- **子模組文檔**:
  - [核心組件](core/README.md)
  - [內部模塊](internal/README.md)
  - [服務層](services/README.md)
  
- **其他模組**:
  - [分析工具](../analysis/README.md)
  - [核心系統](../core/README.md)
  - [父模組](../README.md)

---

**最後更新**: 2026年1月22日
