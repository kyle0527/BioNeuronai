# NLP 模組

`src/nlp/` 是專案內的語言模型與對話工具包。這個目錄目前沒有更深一層的 README，所以本文件同時負責模組概要與子資料夾說明。

## 模組定位

`nlp` 主要分成四條主線：

1. 模型本體：`tiny_llm.py`
2. 對話入口：`chat_engine.py`
3. 分詞器與推理輔助：tokenizer、generation、quantization、LoRA、export
4. 訓練工具：`training/` 與 `tools/`

另外 `rag_system.py` 仍在目錄中，但已是舊版相容檔案；新的 RAG 主線已移到 [src/rag/README.md](../rag/README.md)。

## 資料夾內容

- `__init__.py`
  提供 lazy factory：
  `get_tiny_llm()`、`get_chat_engine()`、`get_create_chat_engine()`、`get_bpe_tokenizer()`、`get_bilingual_tokenizer()`。
  `get_rag_system()` 仍保留，但屬於 deprecated 相容入口。
- `tiny_llm.py`
  `GenerationConfig`、`TinyLLMConfig`、`TinyLLM`，以及 `create_tiny_llm()`、`save_llm()`、`load_llm()`。
- `chat_engine.py`
  `ChatMessage`、`ChatResponse`、`MarketContext`、`ConversationHistory`、`ChatEngine`、`create_chat_engine()`。
- `bpe_tokenizer.py`
  `BPETokenizer` 與 `train_tokenizer_from_files()`。
- `bilingual_tokenizer.py`
  `BilingualTokenizer` 與 `create_bilingual_tokenizer()`。
- `generation_utils.py`
  文字生成與抽樣輔助。
- `inference_utils.py`
  批次推理、串流生成與平行生成工具。
- `quantization.py`
  量化設定與量化層。
- `lora.py`
  LoRA layer 與訓練輔助。
- `hallucination_detection.py`
  幻覺、重複與一致性檢查。
- `honest_generation.py`
  誠實生成流程封裝。
- `uncertainty_quantification.py`
  不確定性估計與校準評估。
- `model_export.py`
  模型匯出工具。
- `rag_system.py`
  舊版 RAG 相容層，非新開發主線。
- `training/`
  訓練腳本與資料集流程，這個資料夾目前沒有獨立 README。
- `tools/`
  封裝與模型包工具，這個資料夾目前沒有獨立 README。

## 訓練與工具子資料夾

### `training/`

目前主要檔案：

- `advanced_trainer.py`
  `TrainingConfig`、`Trainer`、`create_real_dataloader()`。
- `data_manager.py`
  `DataSample`、`DataGenerator`、`DatasetManager`。
- `train_with_ai_teacher.py`
  `AITeacherDataset`、`train_with_ai_teacher()`。
- `auto_evolve.py`
  `EvolutionDataset`、`auto_evolve_training()`。
- `unified_trainer.py`
  `DialogueDataset`、`SignalDataset`、`build_lm_dataloader()`、`build_signal_dataloader()`、`build_model()`、`train()`。
- `build_vocab.py`
  `build_vocab()`。
- `trading_dialogue_data.py`
  交易對話訓練資料生成。
- `view_training_history.py`
  訓練歷史查看工具。
- `training_log.json`
  訓練歷史資料檔，不是 Python 模組。

### `tools/`

- `create_model_package.py`
  模型包建立工具。

## 匯入邊界

常見用法：

```python
from nlp.tiny_llm import TinyLLM, TinyLLMConfig, create_tiny_llm
from nlp.chat_engine import ChatEngine, MarketContext, create_chat_engine
from nlp.bilingual_tokenizer import BilingualTokenizer
```

若只想透過 `nlp.__init__` 取得 class / factory，可用：

```python
from nlp import get_tiny_llm, get_chat_engine

TinyLLM = get_tiny_llm()
ChatEngine = get_chat_engine()
```

## 文件層級

- 這個資料夾目前沒有更深一層的 README。
- `training/` 與 `tools/` 的內容由本文件直接概述。
- 上一層文件見 [src/README.md](../README.md)。

## 相關文件

- [RAG 模組](../rag/README.md)
- [NLP 訓練指南](../../docs/NLP_TRAINING_GUIDE.md)
