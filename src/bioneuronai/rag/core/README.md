# RAG 核心模組 (RAG Core)

**路徑**: `src/bioneuronai/rag/core/`  
**版本**: v1.0  
**更新日期**: 2026-01-22

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [核心文件](#核心文件)
3. [主要功能](#主要功能)
4. [使用示例](#使用示例)

---

## 🎯 模組概述

RAG (Retrieval-Augmented Generation) 核心模組，提供文檔嵌入和檢索功能。

### 模組職責
- ✅ 文本向量化
- ✅ 相似度計算
- ✅ 文檔檢索
- ✅ 語義搜索

---

## 📁 核心文件

### `embeddings.py`
文本嵌入模組，將文本轉換為向量表示。

**主要功能**:
- 文本向量化
- 嵌入模型管理
- 批量處理

### `retriever.py`
文檔檢索模組，根據查詢檢索相關文檔。

**主要功能**:
- 語義搜索
- 相似度排序
- 結果過濾

---

## 🛠️ 主要功能

### 1. 文本嵌入
將文本轉換為高維向量表示。

### 2. 文檔檢索
根據查詢向量檢索最相關的文檔。

### 3. 語義匹配
計算文本之間的語義相似度。

---

## 💡 使用示例

```python
from src.bioneuronai.rag.core import Embeddings, Retriever

# 初始化嵌入模型
embeddings = Embeddings()

# 文本向量化
vector = embeddings.embed("比特幣價格上漲")

# 初始化檢索器
retriever = Retriever()

# 檢索相關文檔
results = retriever.search(query="BTC市場分析", top_k=5)
```

---

**最後更新**: 2026年1月22日
