# TinyLLM - 小型大語言模型

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-1.9%2B-orange.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

基於 Transformer 的小型語言模型，約 124M 參數，支持高效推理和訓練。

## 🌟 特性

### 核心功能 (1-7)
- ✅ **GPT-like 架構**: 基於 Transformer 的自回歸語言模型
- ✅ **KV Cache**: 加速文本生成 2-5x
- ✅ **高級採樣**: Temperature, Top-K, Top-P (Nucleus) 採樣
- ✅ **重複懲罰**: 提高生成文本質量和多樣性
- ✅ **混合精度訓練**: 節省 50% 顯存，提速 2-3x
- ✅ **梯度累積**: 在小顯存設備上訓練大批次
- ✅ **學習率調度**: Warmup + Cosine/Linear Annealing

### 高級功能 (8-13)
- ✅ **Beam Search**: 多路徑並行搜索優化
- ✅ **評估指標**: Perplexity, BLEU, ROUGE 自動計算
- ✅ **流式生成**: 實時 token 輸出
- ✅ **批量推理**: 動態批處理引擎
- ✅ **模型導出**: ONNX, TorchScript, SafeTensors
- ✅ **BPE 分詞器**: 高效子詞分詞

### 專業功能 (14-16)
- ✅ **不確定性量化**: 熵、信心度、Top-K 評估
- ✅ **幻覺檢測**: 自動識別重複、矛盾、不一致內容
- ✅ **誠實生成**: 知道就說知道，不知道就承認

### 訓練優化
- ✅ **梯度裁剪**: 防止梯度爆炸
- ✅ **自動保存**: 最佳模型和檢查點
- ✅ **訓練歷史**: 完整的訓練指標記錄
- ✅ **LoRA 微調**: 低秩適配，只訓練少量參數
- ✅ **模型量化**: 8-bit/4-bit 量化支持

## 🚀 快速開始

### 安裝
```bash
pip install torch transformers
```

### 基礎使用
```python
from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
import torch

# 創建模型
config = TinyLLMConfig(
    vocab_size=50257,
    max_seq_length=512,
    embed_dim=768,
    num_layers=12
)
model = TinyLLM(config)

# 生成文本
input_ids = torch.randint(0, config.vocab_size, (1, 10))
output = model.generate(
    input_ids,
    max_new_tokens=50,
    temperature=0.8,
    top_k=50,
    top_p=0.95,
    repetition_penalty=1.2,
    use_cache=True  # 使用 KV Cache 加速
)
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
    train_dataloader=train_dataloader
)
trainer.train()
```

## 📊 性能表現

### KV Cache 加速
```
測試環境: CPU, 小模型 (7.7M 參數)
輸入長度: 10 tokens
生成長度: 50 tokens

結果:
- 無 Cache: 72.58 tokens/s
- 使用 Cache: 242.81 tokens/s
- 加速比: 3.35x
- 時間節省: 70.1%
```

### 混合精度訓練
```
- 訓練速度提升: ~2.5x
- 顯存節省: ~50%
- 精度影響: 可忽略
```

## 📚 文檔

- [快速開始指南](./QUICK_START.md) - 10分鐘上手
- [能力清單](./CAPABILITIES.md) - 17 個核心能力
- [誠實生成指南](./HONESTY.md) - 不確定性量化與幻覺檢測
- [改進說明](./IMPROVEMENTS.md) - 詳細的功能說明
- [完成報告](./SUMMARY.md) - 第一階段改進總結
- [最終報告](./FINAL_REPORT.md) - 完整項目總結
- [知識蒸餾訓練](./知識蒸餾訓練指南.md) - 高級訓練技巧
- [變更日誌](./CHANGELOG.md) - 版本更新記錄

## 🧪 測試

### 測試訓練器
```bash
python training/advanced_trainer.py
```

## 🎯 使用場景

### 創意寫作
```python
output = model.generate(
    input_ids,
    temperature=1.0,
    top_p=0.95,
    repetition_penalty=1.2
)
```

### 事實回答
```python
output = model.generate(
    input_ids,
    temperature=0.7,
    top_k=40,
    repetition_penalty=1.1
)
```

### 代碼生成
```python
output = model.generate(
    input_ids,
    temperature=0.2,
    top_p=0.9,
    do_sample=False  # 貪婪搜索
)
```

## 📁 項目結構

```
BioNeuronai/
├── src/
│   └── bioneuronai/
│       ├── tiny_llm.py                    # 核心模型
│       ├── generation_utils.py             # 生成工具
│       ├── inference_utils.py              # 推理優化
│       ├── uncertainty_quantification.py   # 不確定性量化
│       ├── hallucination_detection.py      # 幻覺檢測
│       ├── honest_generation.py            # 誠實生成
│       ├── lora.py                         # LoRA 微調
│       ├── quantization.py                 # 模型量化
│       ├── model_export.py                 # 模型導出
│       ├── bpe_tokenizer.py                # BPE 分詞器
│       └── bilingual_tokenizer.py          # 雙語分詞器
├── training/
│   ├── advanced_trainer.py             # 高級訓練器
│   └── train_with_ai_teacher.py        # 知識蒸餾訓練
├── docs/
│   ├── CAPABILITIES.md                 # 能力清單
│   ├── HONESTY.md                      # 誠實生成指南
│   ├── QUICK_START.md                  # 快速開始
│   ├── IMPROVEMENTS.md                 # 改進說明
│   └── FINAL_REPORT.md                 # 最終報告
└── models/
    └── tiny_llm_en_zh_trained/         # 預訓練模型
```

## 🔧 模型配置

| 參數 | 默認值 | 說明 |
|------|-------|------|
| `vocab_size` | 50257 | 詞彙表大小 |
| `max_seq_length` | 512 | 最大序列長度 |
| `embed_dim` | 768 | 嵌入維度 |
| `num_layers` | 12 | Transformer 層數 |
| `num_heads` | 12 | 注意力頭數 |
| `dropout` | 0.1 | Dropout 率 |

**總參數**: ~124M

## 💡 最佳實踐

### 生成參數
| 場景 | Temperature | Top-K | Top-P | Repetition Penalty |
|------|------------|-------|-------|-------------------|
| 創意寫作 | 1.0 | - | 0.95 | 1.2 |
| 事實回答 | 0.7 | 40 | - | 1.1 |
| 代碼生成 | 0.2 | - | 0.9 | 1.0 |

### 訓練參數
| 顯存 | Batch Size | Gradient Accum | AMP |
|------|-----------|---------------|-----|
| 4GB | 4 | 8 | ✅ |
| 8GB | 8 | 4 | ✅ |
| 16GB+ | 16 | 2 | ✅ |

## 🛠️ 高級功能

### Beam Search
```python
from src.bioneuronai.generation_utils import beam_search

best_sequence, best_score = beam_search(
    model, input_ids, num_beams=5
)
```

### 困惑度計算
```python
from src.bioneuronai.generation_utils import calculate_perplexity

perplexity = calculate_perplexity(model, input_ids)
```

## 📈 路線圖

### ✅ 第一階段（已完成）
- KV Cache
- 高級採樣 (Temperature, Top-K, Top-P)
- 重複懲罰
- 混合精度訓練
- 梯度累積
- 學習率調度

### ✅ 第二階段（已完成）
- Beam Search
- 評估指標 (Perplexity, BLEU, ROUGE)
- 流式生成
- 批量推理
- 模型導出 (ONNX, TorchScript, SafeTensors)
- BPE 分詞器

### ✅ 第三階段（已完成）
- 不確定性量化
- 幻覺檢測
- 誠實生成
- LoRA 微調
- 模型量化 (8-bit, 4-bit)

### 🔄 未來計劃
- [ ] Flash Attention
- [ ] 多語言支持擴展
- [ ] 更進階的 Tokenizer
- [ ] 分布式訓練

## 🤝 貢獻

歡迎提交 Issues 和 Pull Requests！

## 📄 許可證

MIT License

## 🙏 致謝

本項目受以下開源項目啟發：
- [HuggingFace Transformers](https://github.com/huggingface/transformers)
- [nanoGPT](https://github.com/karpathy/nanoGPT) by Andrej Karpathy
- [PyTorch](https://pytorch.org/)

## 📞 聯繫

- GitHub Issues: [提交問題](https://github.com/yourusername/BioNeuronai/issues)
- Discussions: [參與討論](https://github.com/yourusername/BioNeuronai/discussions)

---

**Made with ❤️ by BioNeuronai Team**
