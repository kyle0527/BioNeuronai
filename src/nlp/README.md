# NLP 模組 — 自研語言模型工具包

> **版本**: v1.1.0 | **更新日期**: 2026-02-15

---

## 目錄

- [模組定位](#模組定位)
- [架構總覽](#架構總覽)
- [目錄結構](#目錄結構)
- [核心模型](#核心模型)
- [分詞器](#分詞器)
- [模型優化](#模型優化)
- [推理與生成](#推理與生成)
- [可靠性保障](#可靠性保障)
- [訓練系統](#訓練系統)
- [工具與導出](#工具與導出)
- [快速開始](#快速開始)
- [API 參考](#api-參考)
- [技術規格](#技術規格)
- [注意事項](#注意事項)

---

## 模組定位

`src/nlp/` 是 BioNeuronai 專案的**獨立 LLM 開發工具包**，提供從零開始訓練、微調、優化到部署一個 100M 參數 GPT 風格 Transformer 語言模型的完整工具鏈。

此模組**不依賴**任何第三方大型語言模型框架（如 HuggingFace Transformers），所有元件均為自研實現。

---

## 架構總覽

```
┌──────────────────────────────────────────────────────┐
│                  NLP 模組架構                         │
├────────────────┬─────────────────────────────────────┤
│  核心模型層     │  TinyLLM (100M GPT-like Transformer) │
├────────────────┼─────────────────────────────────────┤
│  分詞器層       │  BPETokenizer / BilingualTokenizer   │
├────────────────┼─────────────────────────────────────┤
│  優化層         │  LoRA 微調 / 量化壓縮                 │
├────────────────┼─────────────────────────────────────┤
│  推理層         │  批量推理 / 流式生成 / 採樣策略        │
├────────────────┼─────────────────────────────────────┤
│  可靠性層       │  不確定性量化 / 幻覺檢測 / 誠實生成    │
├────────────────┼─────────────────────────────────────┤
│  訓練層         │  高級訓練 / 知識蒸餾 / 自動進化        │
├────────────────┼─────────────────────────────────────┤
│  工具層         │  模型導出 / 模型打包                   │
└────────────────┴─────────────────────────────────────┘
```

---

## 目錄結構

```
src/nlp/
├── __init__.py                      # 模組入口，提供 3 個工廠函數
├── tiny_llm.py                      # 核心：100M GPT-like Transformer 模型
├── rag_system.py                    # ⚠️ 已廢棄，遷移至 src/rag/
├── bpe_tokenizer.py                 # BPE 子詞分詞器
├── bilingual_tokenizer.py           # 英中雙語分詞器
├── quantization.py                  # 8-bit / 4-bit 模型量化
├── lora.py                          # LoRA 低秩適配微調
├── inference_utils.py               # 批量推理引擎 + 流式生成
├── generation_utils.py              # 採樣策略（Top-K / Top-P / 重複懲罰）
├── hallucination_detection.py       # 幻覺 / 重複 / 矛盾檢測
├── honest_generation.py             # 誠實生成（整合不確定性 + 幻覺檢測）
├── uncertainty_quantification.py    # Monte Carlo Dropout 不確定性量化
├── model_export.py                  # ONNX / TorchScript 模型導出
├── models/                          # 已保存的模型（目前為空）
├── weights/                         # 模型權重檔（目前為空）
├── tools/
│   └── create_model_package.py      # HuggingFace 格式模型打包
└── training/
    ├── advanced_trainer.py          # 混合精度 + 梯度累積訓練器
    ├── auto_evolve.py               # 自動進化微調
    ├── data_manager.py              # 訓練數據管理與驗證
    ├── train_with_ai_teacher.py     # AI 老師知識蒸餾訓練
    ├── view_training_history.py     # 訓練歷史查看器
    └── training_log.json            # 訓練記錄
```

---

## 核心模型

### TinyLLM (`tiny_llm.py` — 611 行)

100M 參數的 GPT 風格 Decoder-only Transformer 模型。

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `vocab_size` | **50,257** | 詞彙表大小 |
| `max_seq_length` | **512** | 最大序列長度 |
| `embed_dim` | 768 | 嵌入維度 |
| `num_heads` | 12 | 注意力頭數 |
| `num_layers` | 12 | Transformer 層數 |
| `ffn_dim` | 3,072 | 前饋網路維度 |
| `dropout` | 0.1 | Dropout 率 |

**核心類別**:
- `TinyLLMConfig` — 模型配置（dataclass）
- `TinyLLM` — 主模型類

```python
from src.nlp import get_tiny_llm

# 使用預設配置建立模型
model = get_tiny_llm()

# 自訂配置
from src.nlp.tiny_llm import TinyLLM, TinyLLMConfig
config = TinyLLMConfig(vocab_size=50257, max_seq_length=512, num_layers=12)
model = TinyLLM(config)
```

---

## 分詞器

### BPETokenizer (`bpe_tokenizer.py` — 457 行)

基於 Byte Pair Encoding 的子詞分詞器，支援中英文混合文本。

**主要功能**:
- 子詞分詞，自動處理 OOV（未見詞）
- 可從語料庫訓練自訂詞彙表
- 支持保存 / 載入詞彙表
- 高效編碼 / 解碼

```python
from src.nlp import get_bpe_tokenizer

tokenizer = get_bpe_tokenizer()
token_ids = tokenizer.encode("Hello, 你好世界！")
text = tokenizer.decode(token_ids)
```

### BilingualTokenizer (`bilingual_tokenizer.py` — 309 行)

專為英文和中文設計的簡易 BPE 分詞器。

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `vocab_size` | 30,000 | 詞彙表大小 |
| 特殊 tokens | `[PAD]`, `[UNK]`, `[BOS]`, `[EOS]`, `[SEP]`, `[CLS]`, `[MASK]` | 7 種 |

```python
from src.nlp import get_bilingual_tokenizer

tokenizer = get_bilingual_tokenizer()
```

---

## 模型優化

### LoRA 低秩適配 (`lora.py` — 415 行)

實現 LoRA (Low-Rank Adaptation) 參數高效微調方法。

**核心類別**:
- `LoRAConfig` — 配置（r=8, lora_alpha=16, lora_dropout=0.1）
- `LoRALayer` — 低秩分解層，將 W 分解為 W' = W + BA

```python
from src.nlp.lora import LoRAConfig, LoRALayer

config = LoRAConfig(
    r=8,                    # LoRA 秩
    lora_alpha=16,          # 縮放因子
    lora_dropout=0.1,       # Dropout
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "fc1", "fc2"]
)

# 建立 LoRA 層
lora_layer = LoRALayer(in_features=768, out_features=768, r=config.r)
```

### 模型量化 (`quantization.py` — 417 行)

支持 8-bit 和 4-bit 量化以減少模型大小和加速推理。

**核心類別**:
- `QuantizationConfig` — 量化配置（bits, symmetric, per_channel, dynamic）
- `QuantizedLinear` — 量化線性層

```python
from src.nlp.quantization import QuantizationConfig, QuantizedLinear

config = QuantizationConfig(
    bits=8,              # 8-bit 或 4-bit
    symmetric=True,      # 對稱量化
    per_channel=True,    # 每通道量化
    dynamic=False        # 動態量化
)

# 建立量化線性層
layer = QuantizedLinear(in_features=768, out_features=768, config=config)
```

---

## 推理與生成

### 批量推理引擎 (`inference_utils.py` — 439 行)

動態批處理多個推理請求以提高吞吐量，並支持流式生成。

**核心類別**:
- `BatchInferenceConfig` — 批量推理配置（batch_size=8, max_batch_size=32）
- `BatchInferenceEngine` — 批量推理引擎

```python
from src.nlp.inference_utils import BatchInferenceEngine, BatchInferenceConfig

config = BatchInferenceConfig(batch_size=8)
engine = BatchInferenceEngine(model=model, config=config, device="cpu")
request_id = engine.add_request(input_ids=token_ids_tensor)
```

### 生成工具函數 (`generation_utils.py` — 276 行)

提供文本生成的高級採樣策略。

**主要函數**:
- `apply_repetition_penalty(logits, generated_ids, penalty)` — 重複懲罰
- `top_k_filtering(logits, top_k)` — Top-K 過濾
- `top_p_filtering(logits, top_p)` — Top-P (Nucleus) 過濾

```python
from src.nlp.generation_utils import top_k_filtering, top_p_filtering

# Top-K 採樣：保留概率最高的 50 個 token
filtered_logits = top_k_filtering(logits, top_k=50)

# Top-P 採樣：保留累積概率達到 0.9 的 token
filtered_logits = top_p_filtering(logits, top_p=0.9)
```

---

## 可靠性保障

### 不確定性量化 (`uncertainty_quantification.py` — 439 行)

使用 **Monte Carlo Dropout** 方法評估模型預測的信心程度。

**核心類別**:
- `UncertaintyConfig` — 配置（entropy_threshold, num_samples=5 等）
- `UncertaintyQuantifier` — 量化器（計算熵、Top-K 概率質量、方差）
- `MonteCarloDropout` — MC Dropout 實現

```python
from src.nlp.uncertainty_quantification import UncertaintyQuantifier, UncertaintyConfig

config = UncertaintyConfig(
    entropy_threshold=2.0,
    num_samples=5,
    use_ensemble=True
)
quantifier = UncertaintyQuantifier(config)
entropy = quantifier.compute_entropy(logits)
```

### 幻覺檢測 (`hallucination_detection.py` — 511 行)

檢測模型生成中的幻覺、矛盾和不一致內容。

**核心類別**:
- `HallucinationConfig` — 配置（repetition_window=20, confidence_threshold=0.4）
- `HallucinationDetector` — 幻覺檢測器
- `SelfConsistencyChecker` — 自我一致性檢查器

**檢測能力**:
| 類型 | 方法 | 說明 |
|------|------|------|
| 重複檢測 | `detect_repetition()` | 基於滑動視窗的重複比例檢測 |
| 矛盾檢測 | `check_contradiction` | 語義矛盾識別 |
| 事實一致性 | `check_factual_consistency` | 知識一致性檢查 |
| 語義連貫性 | `check_semantic_coherence` | 語義連貫度評估 |

### 誠實生成 (`honest_generation.py` — 508 行)

整合不確定性量化與幻覺檢測，實現可靠的文本生成。

**核心類別**:
- `HonestGenerationConfig` — 配置（confidence_threshold=0.5, hallucination_threshold=0.6）
- `HonestGenerator` — 誠實生成器

**運作機制**:
1. 生成過程中持續監測不確定性
2. 信心低於閾值 → 輸出「不知道」或拒絕生成
3. 檢測到幻覺 → 停止生成
4. 可選啟用自我一致性檢查（多次採樣比較）

```python
from src.nlp.honest_generation import HonestGenerator, HonestGenerationConfig

config = HonestGenerationConfig(
    confidence_threshold=0.5,
    stop_on_uncertainty=True,
    stop_on_hallucination=True,
    num_consistency_samples=3
)
generator = HonestGenerator(model=model, config=config)
```

---

## 訓練系統

### 高級訓練器 (`training/advanced_trainer.py` — 524 行)

支援混合精度 (AMP)、梯度累積、學習率排程等功能的訓練器。

| 功能 | 說明 |
|------|------|
| 混合精度 (AMP) | `torch.cuda.amp` 自動混合精度 |
| 梯度累積 | 多步梯度累積，等效增大 batch size |
| 學習率排程 | Cosine / Linear / Constant 三種策略 |
| 梯度裁剪 | `max_grad_norm=1.0` 防止梯度爆炸 |
| Warmup | 可設定 warmup 步數 |

```python
from src.nlp.training.advanced_trainer import TrainingConfig

config = TrainingConfig(
    batch_size=8,
    gradient_accumulation_steps=4,
    learning_rate=3e-4,
    use_amp=True,
    lr_scheduler_type="cosine"
)
```

### AI 老師知識蒸餾 (`training/train_with_ai_teacher.py` — 612 行)

使用 AI 生成的高品質英中雙語數據來訓練模型。
- 內建英文、中文、混合語言對話數據
- 知識蒸餾式訓練流程

### 自動進化 (`training/auto_evolve.py` — 233 行)

自動使用進化數據進行微調，篩選高品質 / 修正後的進化數據進行訓練。

### 數據管理器 (`training/data_manager.py` — 446 行)

完整的訓練數據生命週期管理。

**核心類別**:
- `DataSample` — 數據樣本（含自動語言檢測）
- `DataManager` — 數據管理器

**功能**:
- 數據模板和生成器
- 數據質量驗證
- 數據集劃分（訓練 / 驗證 / 測試）
- 數據統計和自動擴充
- 數據導入 / 導出

### 訓練歷史查看器 (`training/view_training_history.py` — 254 行)

命令列工具，查看所有訓練記錄和模型版本。

```bash
python src/nlp/training/view_training_history.py
```

---

## 工具與導出

### 模型導出 (`model_export.py` — 373 行)

支持將 PyTorch 模型導出為生產級部署格式。

**核心類別**: `ModelExporter`

| 導出格式 | 方法 | 說明 |
|----------|------|------|
| **ONNX** | `export_to_onnx()` | 跨平台推理格式（opset_version=14） |
| **TorchScript** | `export_to_torchscript()` | PyTorch 原生序列化格式 |

```python
from src.nlp.model_export import ModelExporter

exporter = ModelExporter(model=model, device="cpu")
exporter.export_to_onnx("model.onnx")
```

### 模型打包 (`tools/create_model_package.py` — 368 行)

按 HuggingFace 標準格式創建完整模型包，包括：
- `config.json` — 模型配置
- `tokenizer_config.json` — 分詞器配置
- `pytorch_model.bin` — 模型權重

---

## 快速開始

### 安裝依賴

```bash
pip install torch numpy regex
```

### 建立模型與分詞器

```python
from src.nlp import get_tiny_llm, get_bpe_tokenizer

# 建立 100M 參數語言模型
model = get_tiny_llm()

# 建立 BPE 分詞器
tokenizer = get_bpe_tokenizer()

# 編碼文本
input_ids = tokenizer.encode("Hello, 你好！")
print(f"Token IDs: {input_ids}")
```

### 模型推理

```python
import torch

# 準備輸入
input_tensor = torch.tensor([input_ids])

# 前向傳播
with torch.no_grad():
    logits = model(input_tensor)

print(f"輸出形狀: {logits.shape}")  # [1, seq_len, vocab_size]
```

### 量化與導出

```python
from src.nlp.quantization import QuantizationConfig, QuantizedLinear
from src.nlp.model_export import ModelExporter

# 導出為 ONNX
exporter = ModelExporter(model=model, device="cpu")
exporter.export_to_onnx("my_model.onnx")
```

### 可靠生成

```python
from src.nlp.honest_generation import HonestGenerator, HonestGenerationConfig

config = HonestGenerationConfig(
    confidence_threshold=0.5,
    stop_on_hallucination=True
)
generator = HonestGenerator(model=model, config=config)
```

---

## API 參考

### `__init__.py` 工廠函數

| 函數 | 回傳類型 | 說明 |
|------|----------|------|
| `get_tiny_llm()` | `TinyLLM` | 建立預設配置的語言模型 |
| `get_bpe_tokenizer()` | `BPETokenizer` | 建立 BPE 分詞器 |
| `get_bilingual_tokenizer()` | `BilingualTokenizer` | 建立英中雙語分詞器 |

> ⚠️ 所有工廠函數使用 lazy import 策略，首次呼叫時才載入模組。

### `__all__` 公開介面

```python
__all__ = ["TinyLLM", "RAGSystem", "BPETokenizer", "BilingualTokenizer"]
```

> ⚠️ `RAGSystem` 已廢棄，新代碼請使用 `src/rag/` 模組。

---

## 技術規格

| 項目 | 規格 |
|------|------|
| **模型架構** | GPT-like Decoder-only Transformer |
| **參數量** | ~100M（12 層, 768 維, 12 頭） |
| **詞彙表** | 50,257 (BPE) / 30,000 (Bilingual) |
| **最大序列長度** | 512 tokens |
| **量化支持** | 8-bit / 4-bit（對稱 / 非對稱, 每通道 / 每張量） |
| **微調方法** | LoRA（r=8, alpha=16） |
| **導出格式** | ONNX (opset 14) / TorchScript |
| **訓練功能** | AMP 混合精度 / 梯度累積 / Cosine LR |
| **可靠性** | Monte Carlo Dropout + 幻覺檢測 + 誠實生成 |
| **依賴** | PyTorch, NumPy, regex |
| **語言支持** | 英文 / 中文 / 英中混合 |

---

## 注意事項

### ⚠️ RAG 系統已遷移

`rag_system.py` 已標記為 **DEPRECATED**（廢棄），將於 **2026-04-26** 後移除。

新代碼請改用獨立模組：

```python
# ❌ 舊版（已廢棄）
from src.nlp.rag_system import RAGSystem

# ✅ 新版（請使用）
from src.rag.core import EmbeddingService, UnifiedRetriever
```

### 空目錄

- `models/` — 預留存放已保存的模型，目前為空
- `weights/` — 預留存放模型權重，目前為空

### 訓練腳本匯入注意

訓練腳本（`training/` 下）從 `src.bioneuronai.*` 匯入模型和分詞器，而非 `src.nlp.*`：

```python
from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
from src.bioneuronai.bilingual_tokenizer import BilingualTokenizer
```

在執行訓練腳本前，請確保 `src/` 目錄的父目錄在 `PYTHONPATH` 中。

---

## 程式碼統計

| 檔案 | 行數 | 主要類別 / 函數 |
|------|------|-----------------|
| `tiny_llm.py` | 611 | `TinyLLM`, `TinyLLMConfig` |
| `rag_system.py` | 601 | ⚠️ DEPRECATED |
| `hallucination_detection.py` | 511 | `HallucinationDetector`, `SelfConsistencyChecker` |
| `honest_generation.py` | 508 | `HonestGenerator`, `HonestGenerationConfig` |
| `bpe_tokenizer.py` | 457 | `BPETokenizer` |
| `data_manager.py` | 446 | `DataSample`, `DataManager` |
| `inference_utils.py` | 439 | `BatchInferenceEngine` |
| `uncertainty_quantification.py` | 439 | `UncertaintyQuantifier`, `MonteCarloDropout` |
| `quantization.py` | 417 | `QuantizationConfig`, `QuantizedLinear` |
| `lora.py` | 415 | `LoRAConfig`, `LoRALayer` |
| `model_export.py` | 373 | `ModelExporter` |
| `create_model_package.py` | 368 | HuggingFace 格式打包 |
| `bilingual_tokenizer.py` | 309 | `BilingualTokenizer` |
| `generation_utils.py` | 276 | `top_k_filtering`, `top_p_filtering` |
| `view_training_history.py` | 254 | 訓練歷史查看器 |
| `auto_evolve.py` | 233 | `EvolutionDataset` |
| `advanced_trainer.py` | 524 | `TrainingConfig`, `AdvancedTrainer` |
| `train_with_ai_teacher.py` | 612 | 知識蒸餾訓練 |
| **合計** | **~7,793** | **19 個 Python 檔案** |

---

> 📖 更多資訊請參閱 [NLP 訓練指南](../../docs/NLP_TRAINING_GUIDE.md)
>
> 📖 上層目錄：[src/README.md](../README.md)