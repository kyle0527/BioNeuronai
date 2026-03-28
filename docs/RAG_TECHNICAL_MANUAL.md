# BioNeuronai RAG 系統技術手冊
> **檢索增強生成 (Retrieval-Augmented Generation) 完整技術文檔**
> **版本**: v1.1.0
> **最後更新**: 2026年3月20日

---

## 📑 目錄

1. 系統概述
2. 系統架構
3. 核心組件
4. 安裝與配置
5. 快速開始
6. API 參考
7. 使用示例
8. 性能優化
9. 故障排除
10. 最佳實踐
11. 擴展開發
12. 附錄
13. 更新日誌

---

## 系統概述

### 什麼是 RAG？

**檢索增強生成 (RAG)** 是一種結合檢索系統和生成模型的技術架構，通過在生成回答前先檢索相關知識來提升 AI 系統的準確性和可靠性。

### BioNeuronai RAG 系統特性

- **多模型支持** - 本地模型 (sentence-transformers) 和 API 模型 (OpenAI)
- **高速檢索** - FAISS 向量索引（faiss-cpu 已列入依賴），毫秒級搜索
- **內建緩存** - Embedding LRU 快取（10,000 筆）+ UnifiedRetriever TTL 快取（300 秒）
- **多源整合** - 內部知識庫、網路搜索、新聞 API、歷史數據
- **持久化存儲** - JSON 和 FAISS 雙重存儲機制
- **效能監控** - RAGMonitor 追蹤延遲 p50/p95/p99、快取命中率、QPS
- **生產就緒** - 完整錯誤處理、日誌和監控

### 使用場景

| 場景 | 說明 |
|------|------|
| **新聞分析** | 從新聞知識庫中檢索相關市場事件 |
| **交易決策** | 檢索歷史相似情況和交易規則 |
| **策略優化** | 查找歷史策略配置和性能數據 |
| **風險管理** | 檢索風險管理規則和歷史風險事件 |

---

## 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG 系統架構                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐      ┌──────────────────────────────┐     │
│  │   查詢輸入   │─────▶│  UnifiedRetriever            │     │
│  │  (Query)    │      │  統一檢索器                   │     │
│  └─────────────┘      └──────────┬───────────────────┘     │
│                                   │                          │
│                       ┌───────────┴──────────────┐          │
│                       │                           │          │
│         ┌─────────────▼────────┐   ┌─────────────▼────┐    │
│         │ InternalKnowledgeBase│   │  ExternalSources │    │
│         │   內部知識庫          │   │   外部數據源      │    │
│         └──────────┬────────────┘   └──────────────────┘    │
│                    │                                         │
│         ┌──────────▼────────────┐                           │
│         │  EmbeddingService     │                           │
│         │  向量嵌入服務          │                           │
│         ├───────────────────────┤                           │
│         │ • Local Models        │                           │
│         │ • OpenAI API          │                           │
│         └──────────┬────────────┘                           │
│                    │                                         │
│         ┌──────────▼────────────┐                           │
│         │  VectorIndex (FAISS)  │                           │
│         │  向量索引              │                           │
│         └───────────────────────┘                           │
│                                                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │  輸出: List[RetrievalResult]                     │       │
│  │  • content: 檢索內容                              │       │
│  │  • relevance_score: 相關性分數                   │       │
│  │  • source: 數據來源                              │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 數據流程

1. **查詢處理** → 用戶輸入查詢文本
2. **向量化** → EmbeddingService 將查詢轉換為向量
3. **檢索** → UnifiedRetriever 從多個數據源檢索
4. **排序** → 按相關性分數排序結果
5. **返回** → 返回 Top-K 最相關結果

---

## 核心組件

### 向量嵌入服務 (EmbeddingService)

#### 功能說明

將文本轉換為高維向量表示，支持語義相似度計算。

#### 支持的模型

| 模型 | 維度 | 特點 | 適用場景 |
|------|------|------|----------|
| **all-MiniLM-L6-v2** | 384 | 快速、輕量 | 即時檢索 |
| **all-mpnet-base-v2** | 768 | 高品質 | 精確搜索 |
| **paraphrase-multilingual** | 384 | 多語言 | 中英混合 |
| **text-embedding-3-small** | 1536 | OpenAI | 高精度 |
| **text-embedding-3-large** | 3072 | OpenAI | 最高精度 |

#### 使用方法

```python
from rag.core.embeddings import EmbeddingService, EmbeddingModel

# 初始化服務
service = EmbeddingService(
    model=EmbeddingModel.LOCAL_MINILM,
    cache_enabled=True,
    max_cache_size=10000
)

# 單文本嵌入
text = "Bitcoin price analysis"
result = service.embed(text)
print(f"維度: {result.dimensions}")
print(f"向量: {result.embedding[:5]}...")  # 前5維

# 批量嵌入
texts = ["BTC bullish", "ETH bearish", "Market neutral"]
results = service.embed_batch(texts)
print(f"處理了 {len(results)} 個文本")

# 計算相似度
similarity = service.cosine_similarity(
    result.embedding,
    results[0].embedding
)
print(f"相似度: {similarity:.4f}")
```

#### 主要方法

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `embed(text)` | 單文本嵌入 | EmbeddingResult |
| `embed_batch(texts)` | 批量嵌入 | List[EmbeddingResult] |
| `cosine_similarity(a, b)` | 計算餘弦相似度 | float (0-1) |
| `find_most_similar(query, candidates, top_k)` | 找最相似向量 | List[(index, score)] |
| `get_stats()` | 獲取統計信息 | Dict |

---

### 統一檢索器 (UnifiedRetriever)

#### 功能說明

整合多種數據源的統一檢索接口，支持內部知識庫、網路搜索、新聞API等。

#### 檢索來源

```python
class RetrievalSource(Enum):
    INTERNAL_KNOWLEDGE = "internal_knowledge"   # 內部知識庫
    WEB_SEARCH = "web_search"                   # 網路搜索
    NEWS_API = "news_api"                       # 新聞 API
    SOCIAL_MEDIA = "social_media"              # 社交媒體
    HISTORICAL_DATA = "historical_data"        # 歷史數據
    TRADING_RULES = "trading_rules"            # 交易規則
    ALL = "all"                                 # 所有來源
```

#### 使用方法

```python
from rag.core.retriever import UnifiedRetriever, RetrievalQuery, RetrievalSource
from rag.core.embeddings import EmbeddingService
from rag.internal.knowledge_base import InternalKnowledgeBase

# 初始化組件
embedding_service = EmbeddingService()
internal_kb = InternalKnowledgeBase(embedding_service)

# 創建檢索器
retriever = UnifiedRetriever(
    embedding_service=embedding_service,
    internal_kb=internal_kb
)

# 簡單檢索
results = retriever.retrieve("Bitcoin price prediction")

# 高級檢索
query = RetrievalQuery(
    query="BTC market analysis",
    sources=[RetrievalSource.INTERNAL_KNOWLEDGE, RetrievalSource.NEWS_API],
    top_k=10,
    min_relevance=0.5,
    time_range_hours=24
)
results = retriever.retrieve(query)

# 處理結果
for result in results:
    print(f"來源: {result.source.value}")
    print(f"相關性: {result.relevance_score:.2f}")
    print(f"內容: {result.content[:100]}...")
    print(f"---")
```

#### 檢索結果結構

```python
@dataclass
class RetrievalResult:
    content: str                    # 檢索內容
    source: RetrievalSource         # 數據來源
    relevance_score: float          # 相關性分數 (0-1)
    timestamp: datetime             # 時間戳
    url: Optional[str]              # 來源 URL
    title: Optional[str]            # 標題
    metadata: Dict[str, Any]        # 元數據
```

---

### 內部知識庫 (InternalKnowledgeBase)

#### 功能說明

管理交易系統的內部知識文檔，支持增刪改查、向量檢索和持久化存儲。

#### 文檔類型

```python
class DocumentType(Enum):
    TRADING_RULE = "trading_rule"           # 交易規則
    STRATEGY_CONFIG = "strategy_config"     # 策略配置
    MARKET_ANALYSIS = "market_analysis"     # 市場分析
    HISTORICAL_TRADE = "historical_trade"   # 歷史交易
    NEWS_ARCHIVE = "news_archive"           # 新聞存檔
    CUSTOM = "custom"                       # 自定義
```

#### 使用方法

```python
from rag.internal.knowledge_base import InternalKnowledgeBase, DocumentType
from rag.core.embeddings import EmbeddingService

# 初始化
embedding_service = EmbeddingService()
kb = InternalKnowledgeBase(
    embedding_service=embedding_service,
    storage_path="rag_test_data/knowledge_base.json"
)

# 添加文檔
doc = kb.add_document(
    title="BTC 趨勢追蹤策略",
    content="當 BTC 突破 20 日均線時買入，跌破 10 日均線時賣出...",
    doc_type=DocumentType.STRATEGY_CONFIG,
    tags=["BTC", "trend_following", "ma_strategy"]
)

# 搜索文檔
results = kb.search(
    query="BTC 趨勢策略",
    top_k=5,
    min_score=0.3
)

# 按類型過濾
strategy_docs = kb.get_documents_by_type(DocumentType.STRATEGY_CONFIG)

# 按標籤過濾
btc_docs = kb.get_documents_by_tags(["BTC"])

# 更新文檔
kb.update_document(
    doc_id=doc.id,
    content="更新後的策略內容...",
    tags=["BTC", "trend_following", "ma_strategy", "optimized"]
)

# 刪除文檔
kb.delete_document(doc.id)

# 保存到磁盤
kb.save()
```

#### 預設交易規則

知識庫包含以下預設交易規則：

1. **風險管理規則 - 單筆交易風險**
2. **風險管理規則 - 最大持倉**
3. **風險管理規則 - 止損設定**
4. **趨勢追蹤策略 - EMA 金叉死叉**
5. **趨勢追蹤策略 - 突破交易**
6. **波動交易策略 - RSI 超買超賣**

---

### FAISS 向量索引 (VectorIndex)

#### 功能說明

基於 Facebook 的 FAISS 庫實現高速向量檢索，支持百萬級別文檔的毫秒級搜索。

#### 使用方法

```python
from rag.internal.faiss_index import create_index, VectorIndex
import numpy as np

# 創建索引
index = create_index(
    dimension=384,
    index_type="Flat"  # 或 "IVF100,Flat" 用於大規模數據
)

# 添加向量
embeddings = np.random.rand(1000, 384).astype('float32')
ids = list(range(1000))
index.add(embeddings, ids)

# 搜索
query = np.random.rand(1, 384).astype('float32')
distances, indices = index.search(query, top_k=10)

# 保存索引
index.save("vectorindex.faiss")

# 載入索引
loaded_index = VectorIndex.load("vectorindex.faiss", dimension=384)
```

#### 索引類型選擇

| 索引類型 | 特點 | 適用場景 |
|---------|------|----------|
| **Flat** | 精確搜索、慢 | < 10萬文檔 |
| **IVF100,Flat** | 快速搜索、略損精度 | 10萬-100萬文檔 |
| **HNSW32** | 最快、高內存 | 實時應用 |

---

## 安裝與配置

### 系統要求

- Python 3.11+
- 內存: 最低 4GB，推薦 8GB+
- 磁盤: 最低 2GB 可用空間

### 安裝依賴

```bash
# 基礎依賴
pip install sentence-transformers numpy

# FAISS (CPU 版本)
pip install faiss-cpu

# FAISS (GPU 版本，如有 NVIDIA GPU)
pip install faiss-gpu

# 可選：OpenAI API
pip install openai
```

### 配置文件

創建 `config/rag_config.py`:

```python
from rag.core.embeddings import EmbeddingModel

RAG_CONFIG = {
    # 嵌入模型
    "embedding_model": EmbeddingModel.LOCAL_MINILM,
    "openai_api_key": None,  # 如使用 OpenAI

    # 緩存設置
    "cache_enabled": True,
    "max_cache_size": 10000,

    # 檢索設置
    "default_top_k": 10,
    "min_relevance_score": 0.3,

    # 存儲路徑
    "knowledge_base_path": "rag_test_data/knowledge_base.json",
    "faiss_index_path": "rag_test_data/vectorindex.faiss",

    # FAISS 設置
    "faiss_index_type": "Flat",  # 或 "IVF100,Flat"
}
```

---

## 快速開始

### 5分鐘快速示例

```python
"""
RAG 系統快速開始示例
運行方式: python quick_start_rag.py
"""

from rag.core.embeddings import EmbeddingService, EmbeddingModel
from rag.internal.knowledge_base import InternalKnowledgeBase, DocumentType

# 1. 初始化嵌入服務
print("🔧 初始化嵌入服務...")
embedding_service = EmbeddingService(
    model=EmbeddingModel.LOCAL_MINILM,
    cache_enabled=True
)

# 2. 初始化知識庫 (自動載入預設交易規則)
print("📚 初始化知識庫...")
kb = InternalKnowledgeBase(
    embedding_service=embedding_service,
    storage_path="rag_test_data/knowledge_base.json"
)

# 3. 添加自定義文檔
print("\n📝 添加自定義策略...")
kb.add_document(
    title="BTC 日內交易策略",
    content="""
    策略邏輯：
    1. 在亞洲時段(UTC 00:00-08:00)觀察價格波動
    2. 當波動率 > 2% 時進場
    3. 止損設置為 1%，止盈目標為 2%
    4. 持倉時間不超過 4 小時
    """,
    doc_type=DocumentType.STRATEGY_CONFIG,
    tags=["BTC", "intraday", "volatility"]
)

# 4. 執行檢索
print("\n🔍 執行檢索: 'BTC 交易策略'")
results = kb.search("BTC 交易策略", top_k=3)

print(f"\n找到 {len(results)} 個相關文檔:\n")
for i, doc in enumerate(results, 1):
    print(f"[{i}] {doc.title}")
    print(f"    類型: {doc.doc_type.value}")
    print(f"    相關性: {doc.score:.2f}")
    print(f"    標籤: {', '.join(doc.tags)}")
    print(f"    內容預覽: {doc.content[:80]}...")
    print()

# 5. 保存知識庫
print("💾 保存知識庫...")
kb.save()

print("✅ 示例完成！")
```

---

## API 參考

### EmbeddingService API

#### 初始化

```python
EmbeddingService(
    model: EmbeddingModel = EmbeddingModel.LOCAL_MINILM,
    api_key: Optional[str] = None,
    cache_enabled: bool = True,
    max_cache_size: int = 10000
)
```

#### 主要方法

##### embed(text: str) → EmbeddingResult

單文本嵌入。

**參數:**
- `text` (str): 要嵌入的文本

**返回:**
- `EmbeddingResult`: 包含文本、向量、模型信息

**示例:**
```python
result = service.embed("Bitcoin market analysis")
print(result.dimensions)  # 384
print(result.embedding.shape)  # (384,)
```

##### embed_batch(texts: List[str]) → List[EmbeddingResult]

批量文本嵌入。

**參數:**
- `texts` (List[str]): 文本列表

**返回:**
- `List[EmbeddingResult]`: 嵌入結果列表

**示例:**
```python
texts = ["BTC analysis", "ETH trend", "Market sentiment"]
results = service.embed_batch(texts)
```

##### cosine_similarity(a: np.ndarray, b: np.ndarray) → float

計算兩個向量的餘弦相似度。

**參數:**
- `a` (np.ndarray): 向量 A
- `b` (np.ndarray): 向量 B

**返回:**
- `float`: 相似度分數 (0-1)

**示例:**
```python
sim = service.cosine_similarity(
    result1.embedding,
    result2.embedding
)
print(f"相似度: {sim:.4f}")
```

---

### InternalKnowledgeBase API

#### 初始化

```python
InternalKnowledgeBase(
    embedding_service: EmbeddingService,
    storage_path: str = "rag_test_data/knowledge_base.json",
    auto_save: bool = True
)
```

#### 主要方法

##### add_document(...) → KnowledgeDocument

添加文檔到知識庫。

**參數:**
- `title` (str): 文檔標題
- `content` (str): 文檔內容
- `doc_type` (DocumentType): 文檔類型
- `tags` (List[str], 可選): 標籤列表
- `metadata` (Dict, 可選): 元數據

**返回:**
- `KnowledgeDocument`: 已添加的文檔對象

**示例:**
```python
doc = kb.add_document(
    title="趨勢策略",
    content="策略內容...",
    doc_type=DocumentType.STRATEGY_CONFIG,
    tags=["trend", "ma"]
)
```

##### search(query: str, top_k: int, min_score: float) → List[KnowledgeDocument]

搜索相關文檔。

**參數:**
- `query` (str): 搜索查詢
- `top_k` (int, 默認 10): 返回最多文檔數
- `min_score` (float, 默認 0.3): 最小相關性分數

**返回:**
- `List[KnowledgeDocument]`: 按相關性排序的文檔列表

**示例:**
```python
results = kb.search("BTC 策略", top_k=5, min_score=0.5)
for doc in results:
    print(f"{doc.title}: {doc.score:.2f}")
```

##### get_document_by_id(doc_id: str) → Optional[KnowledgeDocument]

根據ID獲取文檔。

##### get_documents_by_type(doc_type: DocumentType) → List[KnowledgeDocument]

獲取特定類型的所有文檔。

##### get_documents_by_tags(tags: List[str]) → List[KnowledgeDocument]

獲取包含指定標籤的文檔。

##### update_document(doc_id: str, **kwargs)

更新文檔字段。

##### delete_document(doc_id: str)

刪除文檔。

##### save()

保存知識庫到磁盤。

##### load()

從磁盤載入知識庫。

---

## 使用示例

### 示例 1: 新聞分析增強

```python
"""
使用 RAG 增強新聞分析
"""
from rag.core.embeddings import EmbeddingService
from rag.internal.knowledge_base import InternalKnowledgeBase, DocumentType

# 初始化
embedding_service = EmbeddingService()
kb = InternalKnowledgeBase(embedding_service)

# 添加歷史新聞
kb.add_document(
    title="2024-01 BTC ETF 通過",
    content="SEC 批准多檔 BTC 現貨 ETF，市場大幅上漲 15%",
    doc_type=DocumentType.NEWS_ARCHIVE,
    tags=["BTC", "ETF", "positive"],
    metadata={"price_change": 15.0, "volume_increase": 200}
)

# 當收到新新聞時，檢索相似歷史事件
new_news = "傳聞 ETH ETF 即將獲批"
similar_events = kb.search(new_news, top_k=3)

for event in similar_events:
    print(f"類似事件: {event.title}")
    print(f"歷史價格變化: {event.metadata.get('price_change', 'N/A')}%")
    print("---")
```

### 示例 2: 策略配置檢索

```python
"""
根據市場條件檢索最佳策略
"""
from rag.internal.knowledge_base import InternalKnowledgeBase, DocumentType

kb = InternalKnowledgeBase(embedding_service)

# 添加多個策略配置
strategies = [
    {
        "title": "牛市趨勢策略",
        "content": "適用於強勢上升趨勢，使用 EMA 快線交叉...",
        "tags": ["bull_market", "trend", "high_volume"]
    },
    {
        "title": "震盪區間策略",
        "content": "適用於橫盤整理，使用布林通道上下軌...",
        "tags": ["sideways", "range", "low_volatility"]
    },
    {
        "title": "熊市防禦策略",
        "content": "適用於下跌趨勢，減少持倉，使用短期反彈...",
        "tags": ["bear_market", "defensive", "short_positions"]
    }
]

for strat in strategies:
    kb.add_document(
        title=strat["title"],
        content=strat["content"],
        doc_type=DocumentType.STRATEGY_CONFIG,
        tags=strat["tags"]
    )

# 根據當前市場條件檢索策略
market_condition = "市場處於高波動震盪狀態"
recommended_strategies = kb.search(market_condition, top_k=2)

print("推薦策略:")
for strat in recommended_strategies:
    print(f"• {strat.title} (相關性: {strat.score:.2f})")
```

### 示例 3: 交易規則遵循檢查

```python
"""
檢查交易決策是否符合規則
"""

kb = InternalKnowledgeBase(embedding_service)

# 模擬交易決策
trade_decision = "計劃使用 50% 資金買入 BTC，不設止損"

# 檢索相關風險管理規則
related_rules = kb.search(trade_decision, top_k=3)

print("相關風險規則:")
for rule in related_rules:
    if rule.doc_type == DocumentType.TRADING_RULE:
        print(f"\n⚠️ {rule.title}")
        print(f"   {rule.content[:150]}...")

        # 檢查是否違反規則
        if "50%" in trade_decision and "單筆交易" in rule.content:
            print("   ❌ 可能違反風險限制！")
```

### 示例 4: 語義搜索與過濾

```python
"""
綜合使用搜索和過濾功能
"""

kb = InternalKnowledgeBase(embedding_service)

# 1. 語義搜索
results = kb.search("BTC 波動策略", top_k=10)

# 2. 按類型過濾
strategy_results = [doc for doc in results 
                   if doc.doc_type == DocumentType.STRATEGY_CONFIG]

# 3. 按標籤過濾
btc_results = [doc for doc in strategy_results 
               if "BTC" in doc.tags]

# 4. 按時間過濾（最近一個月）
from datetime import datetime, timedelta
recent_cutoff = datetime.now() - timedelta(days=30)
recent_results = [doc for doc in btc_results 
                  if doc.created_at >= recent_cutoff]

print(f"找到 {len(recent_results)} 個最新 BTC 策略")
```

---

## 性能優化

### 1. 嵌入緩存

**問題**: 重複文本的嵌入計算浪費資源

**解決方案**: 啟用緩存機制

```python
service = EmbeddingService(
    cache_enabled=True,
    max_cache_size=10000  # 緩存最多 10000 個嵌入
)

# 第一次：計算嵌入
result1 = service.embed("Bitcoin analysis")  # 耗時 ~10ms

# 第二次：從緩存讀取
result2 = service.embed("Bitcoin analysis")  # 耗時 <0.1ms
```

**效果**: 相同文本的嵌入速度提升 100-1000 倍

---

### 2. 批量處理

**問題**: 逐個處理文本效率低

**解決方案**: 使用批量嵌入

```python
# ❌ 慢速方式
for text in texts:
    result = service.embed(text)

# ✅ 快速方式
results = service.embed_batch(texts)
```

**效果**: 批量處理比逐個處理快 5-10 倍

---

### 3. FAISS 索引優化

**小規模 (< 10萬文檔)**:
```python
index = create_index(dimension=384, index_type="Flat")
# 精確搜索，適合小規模
```

**中規模 (10萬-100萬文檔)**:
```python
index = create_index(dimension=384, index_type="IVF100,Flat")
# 訓練索引
index.train(training_vectors)
# 快速搜索，略損精度
```

**大規模 (> 100萬文檔)**:
```python
index = create_index(dimension=384, index_type="HNSW32")
# 最快搜索，內存佔用高
```

---

### 4. 並行搜索

**多數據源並行檢索**:

```python
import asyncio

async def parallel_search(query):
    # 並行檢索多個數據源
    results = await asyncio.gather(
        internal_kb.search_async(query),
        news_api.search_async(query),
        web_search.search_async(query)
    )
    return combine_results(results)
```

---

## 故障排除

### 問題 1: 導入錯誤 - ModuleNotFoundError

**錯誤信息**:
```
ModuleNotFoundError: No module named 'sentence_transformers'
```

**解決方案**:
```bash
pip install sentence-transformers
```

---

### 問題 2: FAISS 索引載入失敗

**錯誤信息**:
```
RuntimeError: Error in faiss::FileIOReader::FileIOReader
```

**解決方案**:
1. 檢查檔案是否存在
2. 檢查檔案權限
3. 重新創建索引

```python
# 重新創建索引
index = create_index(dimension=384)
index.add(embeddings, ids)
index.save("vectorindex.faiss")
```

---

### 問題 3: 記憶體不足

**錯誤信息**:
```
MemoryError: Unable to allocate array
```

**解決方案**:
1. 減少緩存大小
2. 使用更輕量的模型
3. 分批處理數據

```python
# 減少緩存
service = EmbeddingService(max_cache_size=1000)

# 使用更輕量模型
service = EmbeddingService(model=EmbeddingModel.LOCAL_MINILM)  # 384維

# 分批處理
batch_size = 100
for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    results = service.embed_batch(batch)
```

---

### 問題 4: 搜索結果不相關

**問題**: 搜索結果相關性差

**解決方案**:
1. 調整相似度閾值
2. 使用更高品質的模型
3. 檢查查詢文本是否清晰

```python
# 提高相似度閾值
results = kb.search(query, min_score=0.5)  # 從 0.3 提高到 0.5

# 使用高品質模型
service = EmbeddingService(model=EmbeddingModel.LOCAL_MPNET)  # 768維

# 優化查詢文本
# ❌ "btc"
# ✅ "Bitcoin 趨勢分析策略"
```

---

### 問題 5: OpenAI API 錯誤

**錯誤信息**:
```
openai.error.AuthenticationError: Invalid API key
```

**解決方案**:
```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

service = EmbeddingService(
    model=EmbeddingModel.OPENAI_SMALL,
    api_key=os.getenv("OPENAI_API_KEY")
)
```

---

## 最佳實踐

### 1. 文檔組織

✅ **好的實踐**:
- 文檔標題清晰簡潔
- 內容結構化
- 使用標籤分類
- 定期更新文檔

```python
# ✅ 良好示例
kb.add_document(
    title="BTC 趨勢策略 v2.1",
    content="""
    策略邏輯：
    1. 當價格突破 20 日 EMA 時買入
    2. 當價格跌破 10 日 EMA 時賣出
    3. 止損: 2%, 止盈: 5%

    適用市場：牛市上升趨勢
    回測收益：+25% (2025-Q1)
    """,
    doc_type=DocumentType.STRATEGY_CONFIG,
    tags=["BTC", "trend", "ema", "v2.1"],
    metadata={"version": "2.1", "backtest_return": 0.25}
)
```

❌ **不好的實踐**:
```python
# 標題不清晰，內容混亂
kb.add_document(
    title="策略1",
    content="買入然後賣出",
    doc_type=DocumentType.CUSTOM,
    tags=[]
)
```

---

### 2. 搜索策略

**組合使用語義搜索和過濾**:

```python
# 1. 語義搜索獲取候選
candidates = kb.search("波動策略", top_k=20)

# 2. 按類型過濾
strategies = [d for d in candidates 
              if d.doc_type == DocumentType.STRATEGY_CONFIG]

# 3. 按標籤過濾
btc_strategies = [d for d in strategies if "BTC" in d.tags]

# 4. 按相關性排序
final_results = sorted(btc_strategies, 
                      key=lambda d: d.score, 
                      reverse=True)[:5]
```

---

### 3. 性能監控

**記錄和分析性能指標**:

```python
import time

def monitor_search(kb, query):
    start = time.time()
    results = kb.search(query)
    duration = time.time() - start

    print(f"查詢: {query}")
    print(f"耗時: {duration*1000:.2f}ms")
    print(f"結果: {len(results)} 個文檔")
    print(f"平均相關性: {np.mean([d.score for d in results]):.2f}")

    return results

# 使用
results = monitor_search(kb, "BTC 策略")
```

---

### 4. 定期維護

**知識庫維護任務**:

```python
# 1. 清理低質量文檔
low_quality = [doc for doc in kb.get_all_documents() 
               if len(doc.content) < 50]
for doc in low_quality:
    kb.delete_document(doc.id)

# 2. 更新過時文檔
old_docs = kb.get_documents_by_tags(["deprecated"])
for doc in old_docs:
    # 標記為已歸檔
    kb.update_document(doc.id, tags=doc.tags + ["archived"])

# 3. 重建向量索引（如有新版本模型)
kb.rebuild_index()

# 4. 備份數據
kb.save()  # JSON 格式
kb.export_to_csv("backup.csv")  # 可選：CSV 備份
```

---

### 5. 錯誤處理

**健壯的錯誤處理**:

```python
from typing import Optional

def safe_search(kb, query: str, top_k: int = 5) -> Optional[List]:
    """安全搜索，帶錯誤處理"""
    try:
        results = kb.search(query, top_k=top_k)

        if not results:
            logger.warning(f"搜索無結果: {query}")
            return []

        return results

    except Exception as e:
        logger.error(f"搜索錯誤: {query} - {e}", exc_info=True)
        return None

# 使用
results = safe_search(kb, "BTC 策略")
if results is not None:
    for doc in results:
        print(doc.title)
else:
    print("搜索失敗，請查看日誌")
```

---

## 擴展開發

### 添加新的嵌入模型

```python
from rag.core.embeddings import EmbeddingService, EmbeddingModel

class CustomEmbeddingService(EmbeddingService):
    def _initialize_model(self):
        if self.model_type == EmbeddingModel.CUSTOM:
            # 載入自定義模型
            from your_model import YourModel
            self._model = YourModel.load("path/to/model")
            self._dimensions = 512  # 自定義維度
        else:
            super()._initialize_model()
```

### 添加新的檢索來源

```python
from rag.core.retriever import RetrievalSource, RetrievalResult
from datetime import datetime

class TwitterSearchSource:
    """Twitter 數據源"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        # 實現 Twitter 搜索邏輯
        tweets = self._fetch_tweets(query, count=top_k)

        results = []
        for tweet in tweets:
            result = RetrievalResult(
                content=tweet["text"],
                source=RetrievalSource.SOCIAL_MEDIA,
                relevance_score=tweet["engagement_score"],
                timestamp=datetime.now(),
                url=tweet["url"],
                metadata={"likes": tweet["likes"], "retweets": tweet["retweets"]}
            )
            results.append(result)

        return results
```

### 自定義文檔類型

```python
from rag.internal.knowledge_base import DocumentType

# 擴展文檔類型
class ExtendedDocumentType(Enum):
    TRADING_RULE = "trading_rule"
    BACKTEST_REPORT = "backtest_report"      # 新增
    RISK_ALERT = "risk_alert"                # 新增
    MARKET_FORECAST = "market_forecast"      # 新增
```

---

## 附錄

### A. 性能基準測試

| 操作 | 文檔數量 | 平均耗時 | 備註 |
|------|---------|---------|------|
| 單文本嵌入 | - | 10ms | LOCAL_MINILM |
| 批量嵌入 (100) | - | 150ms | 1.5ms/文本 |
| 向量搜索 | 1,000 | 5ms | Flat 索引 |
| 向量搜索 | 100,000 | 15ms | IVF100 索引 |
| 向量搜索 | 1,000,000 | 30ms | HNSW32 索引 |
| 知識庫保存 | 10,000 | 500ms | JSON 格式 |

### B. 模型對比

| 模型 | 維度 | 速度 | 精度 | 內存 | 推薦場景 |
|------|------|------|------|------|----------|
| LOCAL_MINILM | 384 | ⚡⚡⚡ | ⭐⭐⭐ | 💾 | 實時檢索 |
| LOCAL_MPNET | 768 | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💾💾 | 精確搜索 |
| OPENAI_SMALL | 1536 | ⚡ | ⭐⭐⭐⭐ | 💾💾💾 | 商業應用 |
| OPENAI_LARGE | 3072 | ⚡ | ⭐⭐⭐⭐⭐ | 💾💾💾💾 | 最高精度 |

### C. 相關資源

**官方文檔**:
- Sentence Transformers: https://www.sbert.net/
- FAISS: https://github.com/facebookresearch/faiss
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings

**教程**:
- RAG 架構詳解: https://arxiv.org/abs/2005.11401
- 向量搜索最佳實踐: https://www.pinecone.io/learn/

**社群**:
- GitHub Issues: https://github.com/kyle0527/BioNeuronai/issues
- Discord: (待建立)

---

## 更新日誌

### v1.1.0 (2026-03-20)
- ✅ UnifiedRetriever TTL 記憶體快取（預設 300 秒），重複查詢跳過向量搜尋
- ✅ RAGMonitor 效能監控（延遲追蹤、快取命中率、QPS 統計）
- ✅ NewsAdapter 整合 CryptoNewsAnalyzer + RuleBasedEvaluator 事件偵測
- ✅ `cache_hit` flag 正確傳遞至 monitor.log_retrieval()
- ✅ faiss-cpu 已列入 pyproject.toml 依賴
- ✅ sentence-transformers 已列入 pyproject.toml 依賴

### v1.0.0 (2026-02-15)
- ✅ 初始版本發布
- ✅ 支持本地和 OpenAI 嵌入模型
- ✅ FAISS 向量索引集成
- ✅ 內部知識庫管理
- ✅ 統一檢索接口
- ✅ 完整技術文檔

---

**維護者**: BioNeuronai 開發團隊
**授權**: MIT License
**最後更新**: 2026年3月20日

如有問題或建議，請提交 GitHub Issue 或聯繫開發團隊。
