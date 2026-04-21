# NLP 模組 — 自研語言模型工具包

> 路徑：`src/nlp/`
> 目前 `__version__`：`1.0.0`
> 更新日期：2026-04-20

`nlp` 是專案內的自研語言模型工具包，包含 TinyLLM、分詞器、ChatEngine、生成工具、可靠性檢查、量化、LoRA、模型導出與訓練腳本。交易主模型載入在 `bioneuronai.core.inference_engine`，對話模型則由 `nlp.chat_engine` 使用。

---

## 目錄

1. [實際結構](#實際結構)
2. [實際統計](#實際統計)
3. [匯入方式](#匯入方式)
4. [`__init__.py` 公開介面](#__init__py-公開介面)
5. [核心模型](#核心模型)
6. [分詞器](#分詞器)
7. [對話引擎](#對話引擎)
8. [訓練系統](#訓練系統)
9. [RAG 相容檔案](#rag-相容檔案)
10. [相關文件](#相關文件)

---

## 實際結構

```text
nlp/
├── __init__.py                    # lazy factory 匯出
├── tiny_llm.py                    # TinyLLM / TinyLLMConfig
├── chat_engine.py                 # 雙語交易對話引擎
├── rag_system.py                  # 已廢棄，相容保留
├── bpe_tokenizer.py               # BPE 分詞器
├── bilingual_tokenizer.py         # 中英雙語分詞器
├── quantization.py                # 8-bit / 4-bit 量化
├── lora.py                        # LoRA layer / trainer helper
├── inference_utils.py             # 批量推理與流式生成
├── generation_utils.py            # top-k / top-p / temperature / beam search
├── hallucination_detection.py     # 幻覺、重複、矛盾檢測
├── honest_generation.py           # 誠實生成流程
├── uncertainty_quantification.py  # MC Dropout 與不確定性評估
├── model_export.py                # ONNX / TorchScript export
├── py.typed
├── tools/
│   └── create_model_package.py
└── training/
    ├── advanced_trainer.py
    ├── auto_evolve.py
    ├── build_vocab.py
    ├── data_manager.py
    ├── trading_dialogue_data.py
    ├── train_with_ai_teacher.py
    ├── unified_trainer.py
    └── view_training_history.py
```

目前沒有 `src/nlp/models/` 或 `src/nlp/weights/` 目錄；模型權重目前在 repo root 的 `model/` 目錄下管理。

---

## 實際統計

| 範圍 | Python 檔案 | 行數 |
|------|------------:|-----:|
| `nlp/` 直屬 | 14 | 6,086 |
| `nlp/training/` | 9 | 3,369 |
| `nlp/tools/` | 1 | 367 |
| 合計 | 24 | 9,822 |

主要檔案行數：

| 檔案 | 行數 | 主要內容 |
|------|-----:|----------|
| `tiny_llm.py` | 728 | `TinyLLM`, `TinyLLMConfig`, `create_tiny_llm`, `load_llm`, `save_llm` |
| `chat_engine.py` | 589 | `ChatEngine`, `MarketContext`, `create_chat_engine` |
| `rag_system.py` | 581 | 已廢棄的相容 RAGSystem |
| `bpe_tokenizer.py` | 455 | `BPETokenizer` |
| `bilingual_tokenizer.py` | 313 | `BilingualTokenizer` |
| `quantization.py` | 422 | `QuantizationConfig`, `QuantizedLinear`, `QuantizedEmbedding` |
| `lora.py` | 414 | `LoRAConfig`, `LoRALayer`, `LoRALinear`, `LoRATrainer` |
| `inference_utils.py` | 438 | `BatchInferenceEngine`, `StreamingGenerator`, `ParallelGenerator` |
| `generation_utils.py` | 271 | sampling / perplexity / beam search |
| `hallucination_detection.py` | 510 | `HallucinationDetector`, `SelfConsistencyChecker`, `GroundingValidator` |
| `honest_generation.py` | 502 | `HonestGenerator` |
| `uncertainty_quantification.py` | 439 | `UncertaintyQuantifier`, `MonteCarloDropout`, `CalibrationEvaluator` |
| `training/advanced_trainer.py` | 598 | `TrainingConfig`, `Trainer` |
| `training/data_manager.py` | 445 | `DataSample`, `DataGenerator`, `DatasetManager` |
| `training/train_with_ai_teacher.py` | 611 | `AITeacherDataset`, distillation training |
| `training/unified_trainer.py` | 445 | LM / signal dataloader 與統一訓練入口 |
| `training/trading_dialogue_data.py` | 670 | 交易對話樣本 |

---

## 匯入方式

專案內部目前主要以頂層 package 匯入：

```python
from nlp.tiny_llm import TinyLLM, TinyLLMConfig
from nlp.chat_engine import create_chat_engine, MarketContext
from nlp.bilingual_tokenizer import BilingualTokenizer
```

在 repo root 執行時，`src` 會被加入 import path；若在外部環境使用，需確保 `src/` 在 `PYTHONPATH` 中。

---

## `__init__.py` 公開介面

`nlp.__init__` 目前只提供 lazy factory 函式，不直接匯出 class：

```python
__all__ = [
    "get_tiny_llm",
    "get_chat_engine",
    "get_create_chat_engine",
    "get_bpe_tokenizer",
    "get_bilingual_tokenizer",
    "get_rag_system",
]
```

注意：`get_tiny_llm()` 回傳 `TinyLLM` 類別，不是已初始化的模型實例。

```python
from nlp import get_tiny_llm
from nlp.tiny_llm import TinyLLMConfig

TinyLLM = get_tiny_llm()
model = TinyLLM(TinyLLMConfig())
```

若要直接建立預設模型，也可使用：

```python
from nlp.tiny_llm import create_tiny_llm

model = create_tiny_llm()
```

---

## 核心模型

`TinyLLMConfig` 預設值：

| 參數 | 預設值 |
|------|-------:|
| `vocab_size` | 50,257 |
| `max_seq_length` | 512 |
| `embed_dim` | 768 |
| `num_heads` | 12 |
| `num_layers` | 12 |
| `ffn_dim` | 3,072 |
| `dropout` | 0.1 |

```python
from nlp.tiny_llm import TinyLLM, TinyLLMConfig

config = TinyLLMConfig(vocab_size=50257, max_seq_length=512)
model = TinyLLM(config)
```

---

## 分詞器

```python
from nlp.bpe_tokenizer import BPETokenizer
from nlp.bilingual_tokenizer import BilingualTokenizer

bpe = BPETokenizer()
ids = bpe.encode("Hello, BTC")

tokenizer = BilingualTokenizer(vocab_size=30000)
ids2 = tokenizer.encode("BTC 今日走勢")
```

---

## 對話引擎

`ChatEngine` 是 CLI `chat` 與 API `/api/v1/chat` 的對話入口。

```python
from nlp.chat_engine import create_chat_engine, MarketContext

engine = create_chat_engine()
context = MarketContext(symbol="BTCUSDT", price=50000.0)
response = engine.chat("目前適合交易嗎？", market_context=context)
```

---

## 訓練系統

目前訓練相關類別名稱以實作為準：

| 檔案 | 實際類別 / 函式 |
|------|-----------------|
| `advanced_trainer.py` | `TrainingConfig`, `Trainer`, `create_real_dataloader` |
| `data_manager.py` | `DataSample`, `DataGenerator`, `DatasetManager` |
| `train_with_ai_teacher.py` | `AITeacherDataset`, `train_with_ai_teacher` |
| `auto_evolve.py` | `EvolutionDataset`, `auto_evolve_training` |
| `unified_trainer.py` | `DialogueDataset`, `SignalDataset`, `build_model`, `train` |
| `build_vocab.py` | `build_vocab` |

---

## RAG 相容檔案

`nlp/rag_system.py` 已標記為 deprecated，保留是為了舊程式相容。新程式應使用獨立 RAG package：

```python
from rag.core import EmbeddingService, UnifiedRetriever
from rag.internal import InternalKnowledgeBase
```

---

## 相關文件

- [RAG README](../rag/README.md)
- [NLP 訓練指南](../../docs/NLP_TRAINING_GUIDE.md)
- [src README](../README.md)
