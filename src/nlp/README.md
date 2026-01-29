# NLP 模組 - 自然語言處理

**路徑**: `src/nlp/`  
**版本**: v1.0.0  
**更新日期**: 2026-01-22

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [核心組件](#核心組件)
3. [文件說明](#文件說明)
4. [使用範例](#使用範例)
5. [相關文檔](#相關文檔)

---

## 🎯 模組概述

本模組包含完整的自然語言處理和大型語言模型 (LLM) 開發功能，從模型架構到訓練、推理和部署的完整工具鏈。

### 主要特點
- ✅ 100M 參數 Transformer 模型 (GPT-like 架構)
- ✅ RAG (檢索增強生成) 系統
- ✅ BPE 和雙語分詞器
- ✅ 模型量化和優化
- ✅ LoRA 微調支持
- ✅ 幻覺檢測和誠實生成
- ✅ 不確定性量化

---

## 🧩 核心組件

### 1. 語言模型

#### [tiny_llm.py](tiny_llm.py) - 小型語言模型
- **功能**: 100M 參數 Transformer 模型
- **架構**: GPT-like decoder-only
- **特點**: 
  - KV Cache 加速推理
  - 支持文本生成
  - 可訓練和微調
  - Flash Attention 支持

---

### 2. RAG 系統

#### [rag_system.py](rag_system.py) - 檢索增強生成
- **功能**: 結合檢索和生成的混合系統
- **特點**:
  - 向量數據庫檢索
  - 上下文增強生成
  - 相關性排序

---

### 3. 分詞器

#### [bpe_tokenizer.py](bpe_tokenizer.py) - BPE 分詞器
- **功能**: Byte-Pair Encoding 分詞
- **特點**:
  - 子詞切分
  - 詞彙表學習
  - 高效編碼/解碼

#### [bilingual_tokenizer.py](bilingual_tokenizer.py) - 雙語分詞器
- **功能**: 支持中英雙語分詞
- **特點**:
  - 中英文混合處理
  - 統一詞彙表
  - 語言感知切分

---

### 4. 模型優化

#### [quantization.py](quantization.py) - 模型量化
- **功能**: 模型壓縮和加速
- **技術**:
  - INT8/INT4 量化
  - 動態量化
  - 靜態量化
  - 混合精度

#### [lora.py](lora.py) - LoRA 微調
- **功能**: 低秩適應微調
- **特點**:
  - 參數高效微調
  - 快速適應新任務
  - 保留原始模型

---

### 5. 推理工具

#### [inference_utils.py](inference_utils.py) - 推理優化
- **功能**: 推理加速和優化
- **技術**:
  - Batch 推理
  - KV Cache
  - 動態批處理

#### [generation_utils.py](generation_utils.py) - 文本生成
- **功能**: 文本生成策略
- **方法**:
  - Greedy 貪婪搜索
  - Beam Search 束搜索
  - Top-K/Top-P 採樣
  - Temperature 控制

---

### 6. 質量控制

#### [hallucination_detection.py](hallucination_detection.py) - 幻覺檢測
- **功能**: 檢測模型生成的幻覺內容
- **方法**:
  - 一致性檢查
  - 事實驗證
  - 不確定性分析

#### [honest_generation.py](honest_generation.py) - 誠實生成
- **功能**: 確保模型誠實輸出
- **特點**:
  - 不確定性表達
  - 知識邊界識別
  - 可信度評估

#### [uncertainty_quantification.py](uncertainty_quantification.py) - 不確定性量化
- **功能**: 量化模型預測不確定性
- **方法**:
  - 貝葉斯估計
  - 集成方法
  - 熵計算

---

### 7. 模型導出

#### [model_export.py](model_export.py) - 模型導出
- **功能**: 模型格式轉換和部署
- **支持格式**:
  - ONNX
  - TorchScript
  - TensorRT

---

## 📂 子目錄

### [models/](models/) - 預訓練模型
- 存放預訓練模型檢查點
- 包含不同配置的模型變體

### [tools/](tools/) - 開發工具
- [create_model_package.py](tools/create_model_package.py) - 模型打包工具

### [training/](training/) - 訓練工具
- [advanced_trainer.py](training/advanced_trainer.py) - 高級訓練器
- [auto_evolve.py](training/auto_evolve.py) - 自動進化訓練
- [data_manager.py](training/data_manager.py) - 數據管理器
- [train_with_ai_teacher.py](training/train_with_ai_teacher.py) - AI 教師輔助訓練
- [view_training_history.py](training/view_training_history.py) - 訓練歷史查看器

### [weights/](weights/) - 模型權重
- 存放訓練好的模型權重文件

---

## 💻 使用範例

### 1. 載入和使用語言模型

```python
from nlp import get_tiny_llm

# 創建模型
TinyLLM = get_tiny_llm()
model = TinyLLM(
    vocab_size=50000,
    hidden_size=768,
    num_layers=12,
    num_heads=12
)

# 生成文本
output = model.generate(
    input_ids=input_tokens,
    max_length=100,
    temperature=0.8
)
```

### 2. 使用 RAG 系統

```python
from nlp import get_rag_system

# 創建 RAG 系統
RAGSystem = get_rag_system()
rag = RAGSystem(
    model=model,
    retriever=retriever,
    top_k=5
)

# 生成增強回答
answer = rag.generate(
    query="市場趨勢如何？",
    context_docs=documents
)
```

### 3. 模型量化

```python
from nlp.quantization import quantize_model

# 量化模型
quantized_model = quantize_model(
    model=model,
    quantization_config={
        "bits": 8,
        "method": "dynamic"
    }
)
```

### 4. LoRA 微調

```python
from nlp.lora import LoRAModel

# 創建 LoRA 模型
lora_model = LoRAModel(
    base_model=model,
    rank=16,
    alpha=32
)

# 微調
lora_model.train(training_data)
```

---

## 🔗 與交易系統的整合

NLP 模組可以與 [bioneuronai](../bioneuronai/) 交易系統整合：

### 1. 新聞分析增強
```python
from nlp import get_tiny_llm
from bioneuronai.analysis import NewsAnalyzer

# 使用 LLM 增強新聞分析
llm = get_tiny_llm()
news_analyzer = NewsAnalyzer(llm=llm)
```

### 2. 交易策略生成
```python
# 使用 LLM 生成交易策略建議
strategy_suggestion = llm.generate(
    prompt="基於當前市場情況，建議交易策略：...",
    context=market_data
)
```

### 3. RAG 輔助決策
```python
from nlp import get_rag_system

# 使用 RAG 檢索歷史交易經驗
rag = get_rag_system()
advice = rag.query(
    "在高波動市場中應該採取什麼策略？",
    knowledge_base=trading_history
)
```

---

## 📊 技術規格

| 項目 | 規格 |
|------|------|
| **模型參數** | 100M |
| **架構** | Transformer (GPT-like) |
| **最大序列長度** | 2048 tokens |
| **詞彙表大小** | 50,000 |
| **隱藏層維度** | 768 |
| **注意力頭數** | 12 |
| **層數** | 12 |
| **推理延遲** | ~50ms (單次) |

---

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install torch transformers tokenizers
pip install numpy pandas
```

### 2. 訓練模型
```bash
cd training
python train_with_ai_teacher.py
```

### 3. 查看訓練歷史
```bash
python view_training_history.py
```

---

## 📝 開發路線圖

### 已完成 ✅
- [x] 基礎 Transformer 模型
- [x] RAG 系統實現
- [x] 分詞器支持
- [x] 模型量化
- [x] LoRA 微調
- [x] 幻覺檢測

### 進行中 🔄
- [ ] 多語言支持擴展
- [ ] Flash Attention 優化
- [ ] 分佈式訓練支持

### 計劃中 📅
- [ ] 更大規模模型 (500M+)
- [ ] 指令微調 (Instruction Tuning)
- [ ] RLHF (人類反饋強化學習)
- [ ] 多模態支持

---

## 🔧 相關配置

### 環境變量
```bash
export NLP_MODEL_PATH="/path/to/models"
export NLP_CACHE_DIR="/path/to/cache"
```

### 配置文件
```python
# nlp_config.py
NLP_CONFIG = {
    "model_name": "tiny_llm_100m",
    "max_length": 2048,
    "temperature": 0.8,
    "top_k": 50,
    "top_p": 0.95
}
```

---

## 📖 相關文檔

- [BioNeuronAI 主文檔](../../README.md)
- [交易系統文檔](../bioneuronai/README.md)
- [專案結構](../../PROJECT_STRUCTURE.md)

---

**最後更新**: 2026年1月22日  
**維護者**: BioNeuronAI Team
