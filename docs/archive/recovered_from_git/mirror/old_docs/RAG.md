# RAG (Retrieval-Augmented Generation) 系統

## 概述

RAG 系統結合了**檢索**（Retrieval）和**生成**（Generation）技術，通過從知識庫中檢索相關信息來增強語言模型的回答能力。

## 核心功能

### 🔍 1. 文檔檢索
- 向量化表示文檔
- 基於相似度的快速檢索
- 支持語義搜索

### 🤖 2. 增強生成
- 基於檢索上下文生成回答
- 引用來源文檔
- 提高回答準確性

### 💾 3. 知識庫管理
- 添加/刪除文檔
- 持久化存儲
- 批量導入

## 快速開始

### 基礎使用

```python
from src.bioneuronai.rag_system import create_rag_system

# 創建 RAG 系統
rag = create_rag_system(model_path="models/tiny_llm_en_zh_trained")

# 添加文檔到知識庫
documents = [
    "Python 是一種高級編程語言。",
    "機器學習是 AI 的一個分支。",
    "深度學習使用神經網絡。"
]

rag.add_documents(documents)
rag.build_index()

# 查詢
result = rag.query("什麼是 Python？")
print(result['answer'])
```

### 使用命令行工具

```bash
# 交互式模式
python use_rag.py --mode interactive

# 使用自定義文檔
python use_rag.py --mode interactive --documents my_docs.json

# 批量查詢
python use_rag.py --mode batch --questions questions.txt --output results.json

# 保存知識庫
python use_rag.py --mode build --documents docs.json --kb-save my_kb.json

# 載入已有知識庫
python use_rag.py --mode interactive --kb-load my_kb.json
```

## 架構設計

### 1. 文檔處理流程

```
原始文檔 → 分詞 → 嵌入模型 → 向量表示 → 向量存儲
```

### 2. 查詢流程

```
用戶問題 → 嵌入模型 → 查詢向量 → 相似度檢索 → Top-K 文檔
                                                      ↓
            生成回答 ← 語言模型 ← 增強提示（問題 + 上下文）
```

### 3. 核心組件

#### VectorStore（向量存儲）
- 存儲文檔的向量表示
- 支持餘弦相似度檢索
- 可持久化到文件

#### SimpleEmbedding（嵌入模型）
- 將文本轉換為向量
- 使用平均池化
- L2 正規化

#### RAGSystem（主系統）
- 整合檢索和生成
- 管理知識庫
- 提供查詢接口

## 高級功能

### 文檔元數據

```python
documents = ["文檔內容..."]
metadatas = [
    {"source": "來源", "category": "分類", "date": "2026-01-19"}
]

rag.add_documents(documents, metadatas)
```

### 自定義檢索參數

```python
result = rag.query(
    question="問題",
    top_k=10,              # 檢索前 10 個文檔
    max_new_tokens=200,    # 最大生成長度
    temperature=0.8        # 生成溫度
)
```

### 查看檢索來源

```python
result = rag.query(question="...", show_sources=True)

# 查看來源
for source in result['sources']:
    print(f"排名: {source['rank']}")
    print(f"相似度: {source['score']}")
    print(f"內容: {source['text']}")
    print(f"元數據: {source['metadata']}")
```

## 文檔格式

### JSON 格式

```json
[
  {
    "text": "文檔內容",
    "metadata": {
      "source": "來源",
      "category": "分類"
    }
  },
  {
    "text": "另一個文檔",
    "metadata": {}
  }
]
```

或簡單格式：

```json
[
  "文檔1",
  "文檔2",
  "文檔3"
]
```

### 純文本格式

```
每行一個文檔
支持中英文
空行會被忽略
```

## 交互命令

在交互模式中可用的命令：

| 命令 | 說明 |
|------|------|
| `/help` | 顯示幫助信息 |
| `/sources` | 切換顯示/隱藏來源 |
| `/topk N` | 設置檢索數量 |
| `/save` | 保存知識庫 |
| `/quit` | 退出 |

## 性能優化

### 1. 批量添加文檔

```python
# 一次添加多個文檔比多次添加更快
documents = [...]  # 大量文檔
rag.add_documents(documents)
rag.build_index()  # 只需構建一次索引
```

### 2. 調整檢索數量

```python
# 根據需求調整 top_k
result = rag.query(question="...", top_k=3)  # 快速但可能不全面
result = rag.query(question="...", top_k=10) # 更全面但較慢
```

### 3. 設置相似度閾值

```python
# 在 RAGSystem 中設置
rag.score_threshold = 0.3  # 只返回相似度 > 0.3 的文檔
```

## 最佳實踐

### 1. 文檔準備
- ✅ 將長文檔拆分為段落
- ✅ 保持文檔長度適中（100-500 字）
- ✅ 添加有意義的元數據
- ✅ 去除無關內容

### 2. 查詢優化
- ✅ 使用清晰具體的問題
- ✅ 根據知識庫大小調整 top_k
- ✅ 檢查檢索結果的相關性
- ✅ 適當調整溫度參數

### 3. 知識庫維護
- ✅ 定期更新文檔
- ✅ 移除過時信息
- ✅ 備份知識庫文件
- ✅ 監控查詢效果

## 使用場景

### 1. 技術文檔問答
```python
# 添加項目文檔
docs = ["README 內容", "API 文檔", "使用指南"]
rag.add_documents(docs)

# 回答技術問題
rag.query("如何安裝這個庫？")
```

### 2. 客服系統
```python
# 添加常見問題
faqs = ["如何註冊？", "如何退款？", "配送時間"]
rag.add_documents(faqs)

# 自動回答客戶問題
rag.query("我想退款")
```

### 3. 教育輔助
```python
# 添加課程材料
materials = ["第一章內容", "第二章內容", "習題解答"]
rag.add_documents(materials)

# 回答學生問題
rag.query("什麼是機器學習？")
```

## 擴展開發

### 自定義嵌入模型

```python
class CustomEmbedding(nn.Module):
    def __init__(self):
        super().__init__()
        # 自定義架構
    
    def forward(self, input_ids):
        # 自定義邏輯
        return embeddings

# 使用自定義模型
rag = RAGSystem(
    model=model,
    tokenizer=tokenizer,
    embedding_model=CustomEmbedding()
)
```

### 實現重排序

```python
def rerank_results(results, query):
    """對檢索結果重新排序"""
    # 實現更複雜的排序邏輯
    return sorted_results

# 在查詢後使用
results = rag.retrieve(query)
results = rerank_results(results, query)
```

## 故障排除

### 問題：找不到相關文檔

**解決方案：**
- 降低 `score_threshold`
- 增加 `top_k` 值
- 檢查知識庫內容
- 改寫問題

### 問題：回答不準確

**解決方案：**
- 增加相關文檔到知識庫
- 調整 `top_k` 獲取更多上下文
- 調整生成溫度
- 檢查檢索結果質量

### 問題：性能慢

**解決方案：**
- 減少 `top_k` 值
- 使用更小的 `embed_dim`
- 批量處理文檔
- 使用 GPU 加速

## API 參考

### RAGSystem

```python
class RAGSystem:
    def __init__(
        self,
        model,              # 語言模型
        tokenizer,          # 分詞器
        embedding_model,    # 嵌入模型（可選）
        embed_dim=384,      # 嵌入維度
        device="cpu"        # 設備
    )
    
    def add_documents(
        self,
        texts: List[str],           # 文檔列表
        metadatas: List[Dict] = None  # 元數據列表
    )
    
    def build_index(self)  # 構建檢索索引
    
    def retrieve(
        self,
        query: str,                    # 查詢文本
        top_k: int = 5,                # 返回數量
        score_threshold: float = 0.0   # 相似度閾值
    ) -> List[RetrievalResult]
    
    def query(
        self,
        question: str,         # 問題
        top_k: int = None,     # 檢索數量
        max_new_tokens: int = 100,  # 生成長度
        temperature: float = 0.7,    # 溫度
        show_sources: bool = True    # 顯示來源
    ) -> Dict
    
    def save_knowledge_base(self, path)  # 保存知識庫
    def load_knowledge_base(self, path)  # 載入知識庫
```

## 相關文檔

- [主文檔](README.md)
- [快速開始](docs/QUICK_START.md)
- [完整功能列表](docs/CAPABILITIES.md)
- [模型使用](use_model.py)

## 授權

MIT License

---

**更新日期**: 2026-01-19  
**版本**: 1.0.0
