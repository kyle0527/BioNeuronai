# 英中雙語小型語言模型 (Tiny LLM) - 基礎版本

## 📋 目錄

- [模型描述](#模型描述)
- [核心功能](#核心功能)
- [使用方法](#使用方法)
- [性能特點](#性能特點)
- [文件列表](#文件列表)
- [模型信息](#模型信息)
- [限制](#限制)
- [技術細節](#技術細節)
- [相關文檔](#相關文檔)

---

## 模型描述

這是一個專為英文和中文設計的小型語言模型，基於 GPT 架構。**這是原始未訓練版本**，推薦使用訓練版本 `tiny_llm_en_zh_trained`。

### 模型規格

- **參數量**: 124M (1.24億)
- **架構**: GPT-like Transformer
- **層數**: 12
- **注意力頭數**: 12
- **嵌入維度**: 768
- **FFN 維度**: 3072
- **詞彙表大小**: 30,000
- **最大序列長度**: 512
- **支持語言**: 英文、中文

## 核心功能

- ✅ KV Cache 加速推理 (2-5x)
- ✅ 高級採樣策略 (Temperature, Top-K, Top-P)
- ✅ 重複懲罰機制
- ✅ Beam Search 多路徑搜索
- ✅ 流式生成
- ✅ 批量推理優化
- ✅ 混合精度訓練
- ✅ 梯度累積
- ✅ 模型導出 (ONNX, TorchScript, SafeTensors)
- ✅ BPE 分詞器
- ✅ 不確定性量化
- ✅ 幻覺檢測
- ✅ 誠實生成
- ✅ RAG 檢索增強生成
- ✅ LoRA 微調
- ✅ 模型量化

## 使用方法

### 方式 1: Python API（推薦）

```python
from src.nlp.tiny_llm import TinyLLM, TinyLLMConfig
import torch

# 載入模型
config = TinyLLMConfig.from_file("config.json")
model = TinyLLM(config)
model.load_state_dict(torch.load("pytorch_model.bin"))

# 生成文本（使用 KV Cache）
input_ids = torch.randint(0, config.vocab_size, (1, 10))
output = model.generate(
    input_ids,
    max_new_tokens=50,
    temperature=0.8,
    top_k=50,
    top_p=0.95,
    use_cache=True  # 啟用 KV Cache
)
```

### 使用 Tokenizer

```python
from src.nlp.bilingual_tokenizer import BilingualTokenizer

# 載入 tokenizer
tokenizer = BilingualTokenizer.load("tokenizer.pkl")

# 編碼
text = "Hello 你好，世界！"
ids = tokenizer.encode(text)

# 解碼
decoded_text = tokenizer.decode(ids)
```

### 訓練模型

```python
from training.advanced_trainer import Trainer, TrainingConfig

# 配置訓練
train_config = TrainingConfig(
    batch_size=8,
    gradient_accumulation_steps=4,
    max_epochs=10,
    learning_rate=3e-4,
    use_amp=True,  # 混合精度
    lr_scheduler_type="cosine"
)

# 訓練
trainer = Trainer(
    model=model,
    train_config=train_config,
    train_dataloader=train_dataloader,
    eval_dataloader=eval_dataloader
)
trainer.train()
```

## 性能特點

### 推理優化
- **KV Cache**: 2-5x 加速
- **批量推理**: 動態批處理引擎
- **流式生成**: 實時 token 輸出
- **Beam Search**: 多路徑並行搜索

### 訓練優化
- **混合精度**: 節省 50% 顯存，提速 2-3x
- **梯度累積**: 支持大批次訓練
- **學習率調度**: Warmup + Cosine/Linear Annealing
- **自動保存**: 最佳模型和檢查點

## 文件列表

- `pytorch_model.bin` - PyTorch 模型權重 (~496 MB)
- `config.json` - 模型配置文件
- `tokenizer.pkl` - 雙語分詞器
- `README.md` - 本文件

## 模型信息

| 項目 | 值 |
|------|------|
| 總參數 | 124,000,000 |
| 可訓練參數 | 124,000,000 |
| 模型大小 (FP32) | ~496 MB |
| 模型大小 (FP16) | ~248 MB |
| 模型大小 (INT8) | ~124 MB |

## 訓練數據

模型使用英文和中文文本數據訓練（當前為隨機初始化，需要實際訓練）。

## 限制

- 當前模型為隨機初始化，需要在實際數據上訓練才能使用
- 僅支持英文和中文，其他語言未經優化
- 最大序列長度為 512 tokens

## 技術細節

### 架構

- **嵌入層**: Token Embedding + Position Embedding
- **Transformer 層**: 12 層，每層包含:
  - Multi-Head Self-Attention (12 heads)
  - Feed Forward Network (768 → 3072 → 768)
  - Layer Normalization
  - Residual Connections
- **輸出層**: Language Model Head (權重與 Token Embedding 共享)

### 訓練配置

建議配置:
- Learning Rate: 1e-4 ~ 5e-4
- Batch Size: 8-32
- Sequence Length: 256-512
- Warmup Steps: 1000-5000
- Optimizer: AdamW

## 檔案結構

```
model_directory/
├── config.json              # 模型配置
├── pytorch_model.bin        # 模型權重
├── tokenizer_config.json    # Tokenizer 配置
├── tokenizer.pkl            # Tokenizer 檔案
├── vocab.json               # 詞彙表
├── special_tokens_map.json  # 特殊 tokens 映射
└── README.md               # 本檔案
```

## 建議使用場景

此為基礎版本，建議用於：
- 🎓 學習和研究 GPT 架構
- 🔬 進一步訓練實驗
- 🎯 微調特定任務
- 🛠️ 開發和測試

**⚠️ 注意**: 此為未訓練版本，推薦使用 `tiny_llm_en_zh_trained` 獲得更好的生成質量。

## 相關文檔

- 📘 [NLP 模組文檔](../../src/nlp/README.md) - NLP 工具包完整說明
- 📗 [NLP 訓練指南](../../docs/NLP_TRAINING_GUIDE.md) - 訓練技巧
- 📙 [訓練版本](../tiny_llm_en_zh_trained/README.md) - 推薦使用的訓練後模型

## 技術支持

- GitHub Issues: [提交問題](https://github.com/yourusername/BioNeuronai/issues)
- 文檔: [docs/](../../docs/)

## 授權

MIT License

---

**狀態**: 🟡 基礎模型（未訓練）  
**推薦**: 使用 `tiny_llm_en_zh_trained` 版本  
**更新**: 2026-02-15  
**版本**: 1.0.0

---

> 📖 上層目錄：[model/README.md](../README.md)
