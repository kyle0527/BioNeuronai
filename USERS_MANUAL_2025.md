# 🎯 BioNeuronAI 2025 使用者說明書
## Complete User Manual & Tutorial Guide

### 📋 目錄 (Table of Contents)

1. [快速開始](#快速開始)
2. [安裝指南](#安裝指南)
3. [基礎教學](#基礎教學)
4. [RAG系統使用](#rag系統使用)
5. [進階功能](#進階功能)
6. [實用範例](#實用範例)
7. [常見問題](#常見問題)
8. [故障排除](#故障排除)
9. [性能優化](#性能優化)
10. [API參考](#api參考)

---

## 🚀 快速開始

### 什麼是 BioNeuronAI？
BioNeuronAI 2025 是一個整合最新AI技術的生物啟發智能系統平台，包含：
- **🔬 RAG檢索增強生成**：智能文檔檢索與回應生成
- **🧠 增強神經架構**：注意力機制與專家混合系統
- **📚 記憶系統**：三層記憶架構模擬人腦認知
- **⚡ 高性能優化**：90%稀疏化，記憶體節省87.5%

### 30秒快速體驗
```bash
# 1. 安裝
pip install git+https://github.com/kyle0527/BioNeuronai.git

# 2. 測試
python -c "
from bioneuronai import BioNeuron
neuron = BioNeuron(num_inputs=2)
print('BioNeuronAI 2025 運作正常！', neuron.forward([0.8, 0.6]))
"

# 3. 完整驗證
python simple_test_2025.py
```

---

## 💻 安裝指南

### 系統要求
- **Python**: 3.8 或以上版本
- **記憶體**: 最少 4GB RAM
- **磁碟空間**: 至少 2GB 可用空間
- **作業系統**: Windows 10+, macOS 10.15+, Linux Ubuntu 18.04+

### 安裝方式

#### 方式一：標準安裝（推薦）
```bash
# 從GitHub安裝最新版本
pip install git+https://github.com/kyle0527/BioNeuronai.git

# 或從本地安裝（開發版）
git clone https://github.com/kyle0527/BioNeuronai.git
cd BioNeuronai
pip install -e .
```

#### 方式二：完整安裝（包含開發工具）
```bash
# 克隆項目
git clone https://github.com/kyle0527/BioNeuronai.git
cd BioNeuronai

# 安裝完整版本
pip install -e .[dev,docs]

# 驗證安裝
python simple_test_2025.py
```

#### 方式三：Docker安裝
```bash
# 拉取Docker映像檔（如可用）
docker pull bioneuronai:2025

# 運行容器
docker run -it bioneuronai:2025 python simple_test_2025.py
```

### 安裝驗證
```python
# 檢查安裝是否成功
import bioneuronai
print(f"BioNeuronAI 版本: {bioneuronai.__version__}")

# 測試核心功能
from bioneuronai.core import BioNeuron
neuron = BioNeuron(num_inputs=3)
result = neuron.forward([0.5, 0.7, 0.3])
print(f"神經元輸出: {result}")
```

---

## 📚 基礎教學

### 第一課：生物神經元基礎

```python
from bioneuronai.core import BioNeuron

# 創建一個簡單的生物神經元
neuron = BioNeuron(
    num_inputs=3,           # 輸入維度
    threshold=0.5,          # 激活閾值
    learning_rate=0.01,     # 學習率
    memory_window=10        # 記憶窗口
)

# 前向傳播
inputs = [0.8, 0.6, 0.4]
output = neuron.forward(inputs)
print(f"神經元輸出: {output}")

# Hebbian學習
target_output = 1.0
neuron.hebbian_learn(inputs, target_output)

# 檢查新穎性分數
novelty = neuron.novelty_score()
print(f"新穎性分數: {novelty}")
```

### 第二課：神經網路構建

```python
from bioneuronai.core import BioNet

# 創建多層神經網路
network = BioNet(
    layer1_size=4,      # 第一層神經元數量
    layer2_size=3,      # 第二層神經元數量
    threshold=0.6,      # 激活閾值
    learning_rate=0.05  # 學習率
)

# 網路前向傳播
inputs = [0.2, 0.8]
layer2_output, layer1_output = network.forward(inputs)
print(f"第一層輸出: {layer1_output}")
print(f"第二層輸出: {layer2_output}")

# 網路學習
network.learn(inputs)

# 檢查網路狀態
stats = network.get_network_stats()
print(f"網路統計: {stats}")
```

### 第三課：超大規模網路

```python
from bioneuronai.mega_core import create_hundred_million_param_network
import numpy as np

# 創建一億參數網路
mega_net = create_hundred_million_param_network(
    input_dim=2000,     # 輸入維度
    hidden_dim=5000,    # 隱藏層維度
    output_dim=500,     # 輸出維度
    sparsity=0.9        # 稀疏度（90%連接被剪枝）
)

# 高維數據處理
high_dim_input = np.random.random(2000)
output = mega_net.forward(high_dim_input)

print(f"輸入維度: {len(high_dim_input)}")
print(f"輸出維度: {len(output)}")
print(f"實際參數量: {mega_net.actual_parameters:,}")
print(f"記憶體使用: {mega_net.get_network_stats()['total_memory_mb']:.1f} MB")
```

---

## 🔍 RAG系統使用

### RAG系統概述
RAG（檢索增強生成）是BioNeuronAI 2025的核心功能之一，它結合了：
- **文檔檢索**：從知識庫中找到相關資訊
- **智能生成**：基於檢索結果生成回應
- **混合策略**：密集檢索+稀疏檢索+圖檢索

### 基本RAG使用

```python
from bioneuronai.rag_integration import BioRAGSystem

# 1. 初始化RAG系統
rag_system = BioRAGSystem(
    embedding_dim=768,      # 嵌入維度
    max_documents=10000,    # 最大文檔數
    chunk_size=512,         # 分塊大小
    overlap_ratio=0.1       # 重疊比例
)

# 2. 添加知識文檔
documents = [
    "BioNeuronAI是基於生物神經科學原理設計的AI系統。",
    "Hebbian學習規則描述了神經元之間連接強度的變化。", 
    "RAG技術結合檢索和生成，提供更準確的AI回應。",
    "注意力機制幫助模型聚焦於重要的輸入信息。",
    "專家混合系統通過多個專家網路提升模型能力。"
]

for doc in documents:
    rag_system.add_document(doc)

# 3. 進行智能查詢
query = "什麼是Hebbian學習？"
response = rag_system.generate_response(query, top_k=3)

print(f"查詢: {query}")
print(f"RAG回應: {response}")

# 4. 查看檢索結果
retrieved_docs = rag_system.retrieve_documents(query, top_k=3)
for i, (doc, score) in enumerate(retrieved_docs):
    print(f"文檔 {i+1} (相似度: {score:.3f}): {doc[:100]}...")
```

### 進階RAG功能

```python
# 批量文檔添加
batch_documents = [
    "神經可塑性是大腦適應和學習的基礎。",
    "深度學習模型通過反向傳播算法進行訓練。",
    "生物啟發算法模擬自然界的智能行為。"
]
rag_system.add_documents_batch(batch_documents)

# 自定義檢索策略
custom_config = {
    'dense_weight': 0.4,     # 密集檢索權重
    'sparse_weight': 0.35,   # 稀疏檢索權重  
    'graph_weight': 0.25,    # 圖檢索權重
    'rerank_enabled': True,   # 啟用重排序
    'diversity_penalty': 0.1  # 多樣性懲罰
}

response = rag_system.generate_response(
    "解釋神經可塑性的重要性",
    retrieval_config=custom_config
)

# 檢索性能分析
performance = rag_system.analyze_performance()
print(f"平均檢索時間: {performance['avg_retrieval_time']:.3f}秒")
print(f"文檔覆蓋率: {performance['document_coverage']:.1%}")
```

### RAG與新穎性檢測整合

```python
from bioneuronai.core import BioNeuron
from bioneuronai.rag_integration import BioRAGSystem

# 創建新穎性檢測神經元
novelty_neuron = BioNeuron(num_inputs=2, threshold=0.5)

# 初始化RAG系統
rag_system = BioRAGSystem()

# 簡單的新穎性路由邏輯
def intelligent_response(query: str, context_features: list) -> dict:
    """基於新穎性的智能回應"""
    novelty_score = novelty_neuron.forward(context_features)
    
    if novelty_score > 0.6:  # 高新穎性，使用RAG
        response = rag_system.query(query)
        method = "RAG檢索"
    else:  # 低新穎性，基礎回應
        response = f"基於既有知識的回應: {query}"
        method = "基礎回應"
    
    return {
        'response': response,
        'method': method,
        'novelty_score': novelty_score
    }

# 測試不同新穎性場景
novelty_neuron.forward([0.1, 0.1])  # 低新穎性輸入
result1 = intelligent_response("簡單問題", [0.2, 0.1])
print(f"低新穎性: {result1['method']} (分數: {result1['novelty_score']:.3f})")

novelty_neuron.forward([0.9, 0.8])  # 高新穎性輸入
result2 = intelligent_response("複雜的技術問題", [0.8, 0.9])
print(f"高新穎性: {result2['method']} (分數: {result2['novelty_score']:.3f})")
```

---

## 🧠 進階功能

### 增強神經核心使用

```python
from bioneuronai.enhanced_core import EnhancedBioCore
import numpy as np

# 創建增強神經核心
enhanced_core = EnhancedBioCore(
    input_dim=512,          # 輸入維度
    output_dim=256,         # 輸出維度
    hidden_dims=[1024, 2048, 1024],  # 隱藏層維度列表
    enable_rag=True         # 啟用RAG集成
)

# 處理高維數據
input_data = np.random.random(512)  # 512維輸入
enhanced_output = enhanced_core.forward(input_data)

print(f"輸入維度: {len(input_data)}")
print(f"輸出維度: {len(enhanced_output)}")

# 獲取系統統計
stats = enhanced_core.get_system_stats()
print(f"處理時間: {stats.get('processing_time', 'N/A')}ms")
print(f"記憶體使用: {stats.get('memory_usage', 'N/A')}MB")

# RAG系統查詢（如果啟用）
if hasattr(enhanced_core, 'rag_system'):
    query_result = enhanced_core.enhanced_query("什麼是生物神經網路？")
    print(f"RAG增強查詢結果: {query_result[:100]}...")
```

### AI優化配置

```python
from bioneuronai.ai_optimization_2025 import (
    get_optimization_config,
    apply_optimizations,
    get_performance_recommendations
)

# 獲取2025 AI優化配置
config = get_optimization_config()

print("🎯 2025 AI趨勢:")
for trend, description in config['TRENDS_2024_2025'].items():
    print(f"  • {trend}: {description}")

print("\n⚡ 性能優化策略:")
performance_opts = config['OPTIMIZATION_STRATEGIES']['performance']
for strategy in performance_opts:
    print(f"  • {strategy}")

print("\n🗓️ 實施路線圖:")
roadmap = config['ROADMAP_2025']
for quarter, goals in roadmap.items():
    print(f"  {quarter}: {', '.join(goals)}")

# 應用優化建議
model = enhanced_core  # 使用前面創建的模型
optimized_model = apply_optimizations(model, config)

# 獲取個性化建議
recommendations = get_performance_recommendations(
    model_size="large",
    use_case="rag_system", 
    hardware="gpu"
)
print(f"\n💡 個性化建議: {recommendations}")
```

### 層次化記憶系統

```python
from bioneuronai.enhanced_core import HierarchicalMemorySystem

# 創建三層記憶系統
memory_system = HierarchicalMemorySystem(
    working_capacity=512,     # 工作記憶容量
    episodic_capacity=1000,   # 情節記憶容量  
    semantic_capacity=5000,   # 語義記憶容量
    consolidation_threshold=0.7  # 鞏固閾值
)

# 存儲體驗到工作記憶
experiences = [
    torch.randn(128) for _ in range(10)
]

for exp in experiences:
    memory_system.store_experience(exp)

# 記憶鞏固過程
memory_system.consolidate_memories()

# 基於查詢的記憶檢索
query = torch.randn(128)
retrieved_memories = memory_system.retrieve_memories(query, top_k=3)

print(f"檢索到 {len(retrieved_memories)} 條相關記憶")

# 記憶系統統計
stats = memory_system.get_memory_stats()
print(f"記憶系統狀態:")
print(f"  工作記憶使用率: {stats['working_usage']:.1%}")
print(f"  情節記憶使用率: {stats['episodic_usage']:.1%}")
print(f"  語義記憶使用率: {stats['semantic_usage']:.1%}")
```

---

## 💡 實用範例

### 範例一：智能問答系統

```python
from bioneuronai.rag_integration import BioRAGSystem
from bioneuronai.core import BioNeuron

class IntelligentQASystem:
    """智能問答系統"""
    
    def __init__(self):
        # 初始化組件
        self.rag_system = BioRAGSystem()
        self.novelty_detector = BioNeuron(num_inputs=2)
        
        # 載入知識庫
        self._load_knowledge_base()
        
    def _load_knowledge_base(self):
        """載入知識庫"""
        knowledge = [
            "人工智慧是模擬人類智能的技術。",
            "機器學習是AI的子領域，使用數據訓練模型。",
            "深度學習使用多層神經網路進行學習。",
            "自然語言處理幫助電腦理解人類語言。",
            "計算機視覺讓機器能夠理解圖像。"
        ]
        
        for knowledge_item in knowledge:
            self.rag_system.add_document(knowledge_item)
    
    def ask_question(self, question: str) -> dict:
        """提出問題並獲得答案"""
        # 檢測問題新穎性
        question_features = [len(question), question.count('?')]
        novelty_score = self.novelty_detector.forward(question_features)
        
        # 基於新穎性決定回應策略
        if novelty_score > 0.5:
            # 高新穎性：使用RAG系統
            answer = self.rag_system.generate_response(question)
            method = "RAG檢索"
        else:
            # 低新穎性：簡單回應
            answer = f"這是關於'{question}'的基本回應"
            method = "基礎模型"
        
        return {
            'question': question,
            'answer': answer,
            'novelty_score': novelty_score,
            'method': method
        }

# 使用智能問答系統
qa_system = IntelligentQASystem()

questions = [
    "什麼是人工智慧？",
    "機器學習和深度學習有什麼區別？",
    "未來AI技術的發展趨勢如何？"
]

for q in questions:
    result = qa_system.ask_question(q)
    print(f"問題: {result['question']}")
    print(f"答案: {result['answer']}")
    print(f"新穎性: {result['novelty_score']:.3f} ({result['method']})")
    print("-" * 50)
```

### 範例二：文檔分析助手

```python
import os
from pathlib import Path

class DocumentAnalyzer:
    """文檔分析助手"""
    
    def __init__(self):
        self.rag_system = BioRAGSystem()
        self.processed_files = set()
        
    def analyze_directory(self, directory_path: str):
        """分析目錄中的所有文檔"""
        directory = Path(directory_path)
        
        # 支持的文件類型
        supported_extensions = {'.txt', '.md', '.py', '.json'}
        
        for file_path in directory.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in supported_extensions and
                file_path not in self.processed_files):
                
                self._process_file(file_path)
                
    def _process_file(self, file_path: Path):
        """處理單個文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 添加文檔到RAG系統
            document_info = f"文件: {file_path.name}\n內容: {content[:1000]}"
            self.rag_system.add_document(document_info)
            
            self.processed_files.add(file_path)
            print(f"✅ 已處理: {file_path}")
            
        except Exception as e:
            print(f"❌ 處理失敗 {file_path}: {e}")
    
    def query_documents(self, query: str, top_k: int = 5):
        """查詢文檔"""
        response = self.rag_system.generate_response(query, top_k=top_k)
        retrieved = self.rag_system.retrieve_documents(query, top_k=top_k)
        
        return {
            'answer': response,
            'source_documents': retrieved,
            'total_processed': len(self.processed_files)
        }
    
    def get_summary(self):
        """獲取分析摘要"""
        return {
            'processed_files': len(self.processed_files),
            'knowledge_base_size': len(self.rag_system.documents),
            'file_list': [str(f) for f in self.processed_files]
        }

# 使用文檔分析助手
analyzer = DocumentAnalyzer()

# 分析當前項目目錄
analyzer.analyze_directory('./src')

# 查詢功能
queries = [
    "這個項目中有哪些主要的類別？",
    "RAG系統是如何實現的？",
    "有哪些測試文件？"
]

for query in queries:
    result = analyzer.query_documents(query)
    print(f"\n🔍 查詢: {query}")
    print(f"📋 回應: {result['answer']}")
    print(f"📚 來源文檔數: {len(result['source_documents'])}")

# 獲取分析摘要
summary = analyzer.get_summary()
print(f"\n📊 分析摘要:")
print(f"  處理文件數: {summary['processed_files']}")
print(f"  知識庫大小: {summary['knowledge_base_size']}")
```

### 範例三：學習進度追蹤器

```python
import json
from datetime import datetime

class LearningProgressTracker:
    """學習進度追蹤器"""
    
    def __init__(self):
        self.neuron = BioNeuron(num_inputs=3, memory_window=50)
        self.learning_history = []
        self.knowledge_graph = {}
        
    def record_learning_session(self, topic: str, difficulty: float, 
                              understanding: float, time_spent: int):
        """記錄學習會話"""
        # 輸入特徵：難度、理解度、時間投入（標準化）
        features = [
            difficulty / 10.0,           # 難度 (1-10 -> 0-1)
            understanding / 10.0,        # 理解度 (1-10 -> 0-1) 
            min(time_spent / 120.0, 1.0) # 時間 (分鐘, 最大120分鐘)
        ]
        
        # 神經元處理
        activation = self.neuron.forward(features)
        novelty = self.neuron.novelty_score()
        
        # 記錄學習會話
        session = {
            'timestamp': datetime.now().isoformat(),
            'topic': topic,
            'difficulty': difficulty,
            'understanding': understanding,
            'time_spent': time_spent,
            'activation': activation,
            'novelty': novelty,
            'features': features
        }
        
        self.learning_history.append(session)
        
        # 更新知識圖譜
        self._update_knowledge_graph(topic, understanding, novelty)
        
        # Hebbian學習
        target = understanding / 10.0  # 目標輸出基於理解度
        self.neuron.hebbian_learn(features, target)
        
        return session
        
    def _update_knowledge_graph(self, topic: str, understanding: float, novelty: float):
        """更新知識圖譜"""
        if topic not in self.knowledge_graph:
            self.knowledge_graph[topic] = {
                'sessions': 0,
                'avg_understanding': 0.0,
                'avg_novelty': 0.0,
                'mastery_level': 'beginner'
            }
        
        kg = self.knowledge_graph[topic]
        kg['sessions'] += 1
        
        # 更新平均值
        kg['avg_understanding'] = (
            (kg['avg_understanding'] * (kg['sessions'] - 1) + understanding) / kg['sessions']
        )
        kg['avg_novelty'] = (
            (kg['avg_novelty'] * (kg['sessions'] - 1) + novelty) / kg['sessions'] 
        )
        
        # 決定掌握程度
        if kg['avg_understanding'] >= 8.0 and kg['sessions'] >= 3:
            kg['mastery_level'] = 'advanced'
        elif kg['avg_understanding'] >= 6.0 and kg['sessions'] >= 2:
            kg['mastery_level'] = 'intermediate'
        else:
            kg['mastery_level'] = 'beginner'
    
    def get_learning_insights(self):
        """獲取學習洞察"""
        if not self.learning_history:
            return "尚無學習記錄"
        
        recent_sessions = self.learning_history[-10:]  # 最近10次會話
        
        insights = {
            'total_sessions': len(self.learning_history),
            'avg_understanding': np.mean([s['understanding'] for s in recent_sessions]),
            'avg_novelty': np.mean([s['novelty'] for s in recent_sessions]),
            'learning_trend': self._calculate_learning_trend(),
            'recommended_topics': self._get_topic_recommendations(),
            'knowledge_graph': self.knowledge_graph
        }
        
        return insights
    
    def _calculate_learning_trend(self):
        """計算學習趨勢"""
        if len(self.learning_history) < 2:
            return "insufficient_data"
        
        recent_understanding = [s['understanding'] for s in self.learning_history[-5:]]
        early_understanding = [s['understanding'] for s in self.learning_history[:5]]
        
        recent_avg = np.mean(recent_understanding)
        early_avg = np.mean(early_understanding)
        
        if recent_avg > early_avg + 1.0:
            return "improving"
        elif recent_avg < early_avg - 1.0:
            return "declining"
        else:
            return "stable"
    
    def _get_topic_recommendations(self):
        """獲取學習建議"""
        recommendations = []
        
        for topic, info in self.knowledge_graph.items():
            if info['mastery_level'] == 'beginner' and info['avg_understanding'] < 5.0:
                recommendations.append(f"需要加強: {topic}")
            elif info['mastery_level'] == 'intermediate' and info['avg_novelty'] < 0.3:
                recommendations.append(f"可以深入: {topic}")
        
        return recommendations

# 使用學習進度追蹤器
tracker = LearningProgressTracker()

# 模擬學習會話
learning_sessions = [
    ("Python基礎", 3, 7, 45),
    ("機器學習概念", 6, 5, 60),
    ("神經網路", 8, 4, 90),
    ("深度學習", 9, 6, 120),
    ("BioNeuronAI", 7, 8, 75)
]

print("🎓 學習會話記錄:")
for topic, difficulty, understanding, time_spent in learning_sessions:
    session = tracker.record_learning_session(topic, difficulty, understanding, time_spent)
    print(f"主題: {topic}")
    print(f"  難度: {difficulty}/10, 理解度: {understanding}/10")
    print(f"  神經激活: {session['activation']:.3f}, 新穎性: {session['novelty']:.3f}")
    print()

# 獲取學習洞察
insights = tracker.get_learning_insights()
print("📊 學習洞察分析:")
print(f"總會話數: {insights['total_sessions']}")
print(f"平均理解度: {insights['avg_understanding']:.1f}/10")
print(f"平均新穎性: {insights['avg_novelty']:.3f}")
print(f"學習趨勢: {insights['learning_trend']}")

print("\n📈 知識掌握情況:")
for topic, info in insights['knowledge_graph'].items():
    print(f"{topic}: {info['mastery_level']} "
          f"(理解度: {info['avg_understanding']:.1f}/10, "
          f"會話數: {info['sessions']})")

if insights['recommended_topics']:
    print("\n💡 學習建議:")
    for rec in insights['recommended_topics']:
        print(f"  • {rec}")
```

---

## ❓ 常見問題

### Q1: 安裝時遇到依賴問題怎麼辦？
**A:** 
```bash
# 嘗試升級pip
pip install --upgrade pip

# 清除緩存重新安裝
pip cache purge
pip install --no-cache-dir git+https://github.com/kyle0527/BioNeuronai.git

# 如果仍有問題，使用conda環境
conda create -n bioneuronai python=3.9
conda activate bioneuronai
pip install git+https://github.com/kyle0527/BioNeuronai.git
```

### Q2: 為什麼RAG系統回應不夠準確？
**A:** 
1. **增加文檔數量**：確保知識庫包含足夠相關的文檔
2. **調整檢索參數**：嘗試不同的top_k值和檢索權重
3. **改進查詢**：使用更具體和清晰的查詢語句
4. **文檔品質**：確保添加的文檔內容準確且相關

```python
# 優化RAG配置
rag_system = BioRAGSystem(
    embedding_dim=768,      # 增加嵌入維度
    chunk_size=256,         # 減小分塊大小  
    overlap_ratio=0.2       # 增加重疊比例
)

# 使用更好的檢索策略
response = rag_system.generate_response(
    query, 
    top_k=5,  # 增加檢索文檔數
    retrieval_config={
        'dense_weight': 0.5,
        'sparse_weight': 0.3, 
        'graph_weight': 0.2,
        'rerank_enabled': True
    }
)
```

### Q3: 神經網路訓練太慢怎麼辦？
**A:**
```python
# 使用稀疏連接減少計算量
mega_net = create_hundred_million_param_network(
    sparsity=0.95  # 增加稀疏度到95%
)

# 批量處理提升效率
inputs_batch = [np.random.random(2000) for _ in range(10)]
for batch in inputs_batch:
    output = mega_net.forward(batch)

# 使用GPU加速（如果可用）
import torch
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
enhanced_core = EnhancedBioCore().to(device)
```

### Q4: 記憶體使用量太高怎麼辦？
**A:**
```python
# 減少網路規模
smaller_net = create_hundred_million_param_network(
    hidden_dim=1000,  # 減少隱藏層維度
    sparsity=0.95     # 增加稀疏度
)

# 限制記憶系統容量
memory_system = HierarchicalMemorySystem(
    working_capacity=256,   # 減少工作記憶
    episodic_capacity=500,  # 減少情節記憶
    semantic_capacity=2000  # 減少語義記憶
)

# 定期清理記憶
memory_system.cleanup_old_memories()
```

### Q5: 如何提高新穎性檢測的準確性？
**A:**
```python
# 調整神經元參數
neuron = BioNeuron(
    num_inputs=4,           # 增加輸入維度
    threshold=0.3,          # 降低閾值提高靈敏度
    learning_rate=0.02,     # 調整學習率
    memory_window=20        # 增加記憶窗口
)

# 使用多個神經元集成
ensemble_neurons = [
    BioNeuron(num_inputs=3, threshold=t) 
    for t in [0.3, 0.5, 0.7]
]

def ensemble_novelty(inputs):
    novelties = [neuron.forward(inputs) for neuron in ensemble_neurons]
    return np.mean(novelties)
```

---

## 🔧 故障排除

### 常見錯誤及解決方案

#### 錯誤 1: ImportError
```
ImportError: No module named 'bioneuronai'
```
**解決方案:**
```bash
# 確認安裝
pip list | grep bioneuronai

# 重新安裝
pip uninstall bioneuronai
pip install git+https://github.com/kyle0527/BioNeuronai.git

# 檢查Python路徑
python -c "import sys; print(sys.path)"
```

#### 錯誤 2: Memory Error
```
MemoryError: Unable to allocate array
```
**解決方案:**
```python
# 減少網路規模
smaller_config = {
    'input_dim': 500,    # 從2000減少到500
    'hidden_dim': 1000,  # 從5000減少到1000
    'sparsity': 0.98     # 增加稀疏度到98%
}

# 使用批處理
def process_in_batches(data, batch_size=32):
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        yield process_batch(batch)
```

#### 錯誤 3: CUDA OutOfMemoryError
```
RuntimeError: CUDA out of memory
```
**解決方案:**
```python
# 清理GPU記憶體
import torch
torch.cuda.empty_cache()

# 使用混合精度
model = EnhancedBioCore().half()  # 使用FP16

# 減少批處理大小
batch_size = 8  # 從32減少到8
```

#### 錯誤 4: SQLite Database Locked
```
sqlite3.OperationalError: database is locked
```
**解決方案:**
```python
# 確保正確關閉連接
rag_system.close()  # 明確關閉RAG系統

# 或使用上下文管理器
with BioRAGSystem() as rag:
    rag.add_document("test document")
    response = rag.generate_response("test query")
```

### 性能診斷工具

```python
import time
import psutil
import gc

class PerformanceDiagnostic:
    """性能診斷工具"""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        
    def start_monitoring(self):
        """開始監控"""
        gc.collect()  # 強制垃圾回收
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    def end_monitoring(self):
        """結束監控"""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        return {
            'execution_time': end_time - self.start_time,
            'memory_used': end_memory - self.start_memory,
            'total_memory': end_memory
        }
    
    def diagnose_model(self, model, test_input):
        """診斷模型性能"""
        self.start_monitoring()
        
        # 執行推理
        try:
            output = model(test_input) if hasattr(model, '__call__') else model.forward(test_input)
            success = True
        except Exception as e:
            success = False
            error = str(e)
        
        metrics = self.end_monitoring()
        metrics['success'] = success
        if not success:
            metrics['error'] = error
            
        return metrics

# 使用診斷工具
diagnostic = PerformanceDiagnostic()

# 診斷RAG系統
test_query = "測試查詢"
rag_metrics = diagnostic.diagnose_model(
    lambda x: rag_system.generate_response(x),
    test_query
)

print(f"RAG系統診斷:")
print(f"  執行時間: {rag_metrics['execution_time']:.3f}秒")
print(f"  記憶體使用: {rag_metrics['memory_used']:.1f}MB")
print(f"  執行成功: {rag_metrics['success']}")
```

---

## ⚡ 性能優化

### 系統級優化

```python
import os
import multiprocessing

# 設置環境變數優化
os.environ['OMP_NUM_THREADS'] = str(multiprocessing.cpu_count())
os.environ['MKL_NUM_THREADS'] = str(multiprocessing.cpu_count())

# NumPy優化
import numpy as np
np.seterr(all='ignore')  # 忽略數值警告提升性能

# 批處理優化
class BatchProcessor:
    """批處理優化器"""
    
    def __init__(self, batch_size=32):
        self.batch_size = batch_size
        
    def process_batch(self, model, inputs):
        """批量處理輸入"""
        results = []
        
        for i in range(0, len(inputs), self.batch_size):
            batch = inputs[i:i + self.batch_size]
            batch_results = []
            
            for item in batch:
                result = model(item)
                batch_results.append(result)
                
            results.extend(batch_results)
            
        return results
```

### RAG系統優化

```python
from functools import lru_cache
import asyncio

class OptimizedRAGSystem(BioRAGSystem):
    """優化的RAG系統"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.query_cache = {}
        self.embedding_cache = {}
        
    @lru_cache(maxsize=1000)
    def cached_embedding(self, text: str):
        """緩存嵌入計算"""
        return self.embedder.encode(text)
        
    async def async_retrieve(self, query: str, top_k: int = 5):
        """異步檢索"""
        # 檢查緩存
        cache_key = f"{query}_{top_k}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        # 並行檢索
        dense_task = asyncio.create_task(self._async_dense_retrieval(query, top_k))
        sparse_task = asyncio.create_task(self._async_sparse_retrieval(query, top_k))
        
        dense_results = await dense_task
        sparse_results = await sparse_task
        
        # 融合結果
        fused_results = self._fuse_results([dense_results, sparse_results])
        
        # 緩存結果
        self.query_cache[cache_key] = fused_results
        
        return fused_results
        
    def optimize_database(self):
        """優化資料庫"""
        # SQLite優化
        self.cursor.execute("PRAGMA journal_mode = WAL")
        self.cursor.execute("PRAGMA synchronous = NORMAL")  
        self.cursor.execute("PRAGMA cache_size = 10000")
        self.cursor.execute("PRAGMA temp_store = memory")
        
        # 創建索引
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_similarity 
            ON documents(embedding)
        """)
```

### 神經網路優化

```python
import torch.nn.utils.prune as prune

class OptimizedEnhancedCore(EnhancedBioCore):
    """優化的增強核心"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_pruned = False
        
    def apply_pruning(self, pruning_ratio=0.1):
        """應用網路剪枝"""
        for name, module in self.named_modules():
            if isinstance(module, torch.nn.Linear):
                prune.l1_unstructured(module, name='weight', amount=pruning_ratio)
                prune.remove(module, 'weight')
        
        self.is_pruned = True
        
    def apply_quantization(self):
        """應用量化"""
        self.eval()
        self.qconfig = torch.quantization.get_default_qconfig('fbgemm')
        torch.quantization.prepare(self, inplace=True)
        
        # 校準（需要代表性數據）
        with torch.no_grad():
            for _ in range(100):
                dummy_input = torch.randn(1, self.input_dim)
                self(dummy_input)
        
        torch.quantization.convert(self, inplace=True)
        
    def enable_mixed_precision(self):
        """啟用混合精度"""
        self.scaler = torch.cuda.amp.GradScaler()
        
    def forward(self, x):
        """優化的前向傳播"""
        if hasattr(self, 'scaler'):
            # 混合精度計算
            with torch.cuda.amp.autocast():
                return super().forward(x)
        else:
            return super().forward(x)
```

### 記憶體優化

```python
import gc
import torch

class MemoryOptimizer:
    """記憶體優化器"""
    
    @staticmethod
    def cleanup_memory():
        """清理記憶體"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    @staticmethod
    def monitor_memory():
        """監控記憶體使用"""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB  
            'percent': process.memory_percent()
        }
    
    @staticmethod
    def set_memory_limit(limit_mb: int):
        """設置記憶體限制"""
        import resource
        
        # 設置記憶體限制（僅在Unix系統上）
        try:
            resource.setrlimit(
                resource.RLIMIT_AS, 
                (limit_mb * 1024 * 1024, limit_mb * 1024 * 1024)
            )
        except:
            print("無法設置記憶體限制（可能不支持）")

# 使用記憶體優化
memory_optimizer = MemoryOptimizer()

# 定期清理記憶體
def training_loop_with_cleanup(model, data_loader):
    for i, batch in enumerate(data_loader):
        output = model(batch)
        
        # 每10個batch清理一次記憶體
        if i % 10 == 0:
            memory_optimizer.cleanup_memory()
            
        # 監控記憶體使用
        if i % 50 == 0:
            memory_stats = memory_optimizer.monitor_memory()
            print(f"Memory usage: {memory_stats['rss']:.1f}MB ({memory_stats['percent']:.1f}%)")
```

---

## 📖 API參考

### 核心API

#### BioNeuron
```python
class BioNeuron:
    """生物啟發神經元"""
    
    def __init__(self, num_inputs: int, threshold: float = 0.5, 
                 learning_rate: float = 0.01, memory_window: int = 10):
        """
        初始化生物神經元
        
        參數:
            num_inputs: 輸入維度
            threshold: 激活閾值
            learning_rate: 學習率
            memory_window: 記憶窗口大小
        """
    
    def forward(self, inputs: List[float]) -> float:
        """前向傳播"""
        
    def hebbian_learn(self, inputs: List[float], target_output: float):
        """Hebbian學習規則"""
        
    def novelty_score(self) -> float:
        """計算新穎性分數"""
```

#### BioRAGSystem  
```python
class BioRAGSystem:
    """RAG檢索增強生成系統"""
    
    def __init__(self, embedding_dim: int = 768, max_documents: int = 10000,
                 chunk_size: int = 512, overlap_ratio: float = 0.1):
        """初始化RAG系統"""
        
    def add_document(self, document: str, metadata: dict = None):
        """添加單個文檔"""
        
    def query(self, query: str, top_k: int = 5) -> dict:
        """執行RAG查詢並返回結果字典"""
        
    def get_statistics(self) -> dict:
        """獲取系統統計信息"""
        
    def export_knowledge_base(self, filepath: str):
        """導出知識庫到文件"""
```

#### EnhancedBioCore
```python
class EnhancedBioCore(torch.nn.Module):
    """增強生物神經核心"""
    
    def __init__(self, input_dim: int, hidden_dim: int, num_experts: int = 8,
                 num_heads: int = 8, use_attention: bool = True,
                 use_memory: bool = True, dropout_rate: float = 0.1):
        """初始化增強核心"""
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向傳播"""
        
    def get_attention_weights(self) -> torch.Tensor:
        """獲取注意力權重"""
        
    def get_memory_content(self) -> List:
        """獲取記憶內容"""
```

### 工具API

#### BioNeuron (核心神經元)
```python
class BioNeuron:
    """生物啟發神經元"""
    
    def __init__(self, num_inputs: int, threshold: float = 0.5,
                 learning_rate: float = 0.01, memory_window: int = 10):
        """初始化神經元"""
        
    def forward(self, inputs: List[float]) -> float:
        """前向傳播處理"""
        
    def novelty_score(self) -> float:
        """計算新穎性分數用於智能路由"""
```

#### PerformanceMonitor
```python  
class PerformanceMonitor:
    """性能監控器"""
    
    def monitor_inference(self, model, inputs):
        """監控推理性能"""
        
    def suggest_optimizations(self) -> List[str]:
        """提供優化建議"""
```

### 配置API

#### get_optimization_config
```python
def get_optimization_config() -> dict:
    """
    獲取AI優化配置
    
    返回:
        dict: 包含2025年AI趨勢、優化策略和路線圖的配置
    """
```

#### apply_optimizations
```python
def apply_optimizations(model, config: dict):
    """
    應用優化配置到模型
    
    參數:
        model: 要優化的模型
        config: 優化配置字典
        
    返回:
        優化後的模型
    """
```

---

## 📞 技術支援

### 獲取幫助
- **GitHub Issues**: [提交問題](https://github.com/kyle0527/BioNeuronai/issues)
- **討論區**: [GitHub Discussions](https://github.com/kyle0527/BioNeuronai/discussions)  
- **文檔**: [完整文檔](https://bioneuronai.readthedocs.io)
- **範例**: 查看 `examples/` 目錄中的完整範例

### 社區資源
- **教學影片**: [YouTube頻道](https://youtube.com/BioNeuronAI)
- **技術部落格**: [Medium](https://medium.com/@BioNeuronAI)
- **社交媒體**: [Twitter @BioNeuronAI](https://twitter.com/BioNeuronAI)

### 商業支援
如需企業級技術支援，請聯繫：support@bioneuronai.org

---

## 🎯 快速參考卡

### 基本操作
```python
# 導入核心模組
from bioneuronai import BioNeuron, BioRAGSystem, EnhancedBioCore

# 創建神經元
neuron = BioNeuron(num_inputs=3, threshold=0.5)

# 初始化RAG系統  
rag = BioRAGSystem()
rag.add_document("your document text")

# 增強核心
core = EnhancedBioCore(input_dim=512, hidden_dim=1024)

# 快速測試
python simple_test_2025.py
```

### 常用參數
| 參數 | 描述 | 建議值 |
|------|------|--------|
| `threshold` | 神經元激活閾值 | 0.3-0.7 |
| `learning_rate` | 學習率 | 0.001-0.1 |
| `top_k` | RAG檢索文檔數 | 3-10 |
| `embedding_dim` | 嵌入維度 | 256-1024 |
| `sparsity` | 網路稀疏度 | 0.8-0.95 |

### 故障排除快速檢查
1. ✅ Python版本 >= 3.8
2. ✅ 記憶體 >= 4GB  
3. ✅ 磁碟空間 >= 2GB
4. ✅ 依賴包已安裝
5. ✅ `simple_test_2025.py` 通過

---

*最後更新: 2025年11月*  
*版本: BioNeuronAI 2025*  
*維護者: BioNeuronAI開發團隊*