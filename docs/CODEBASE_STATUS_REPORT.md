# BioNeuronai 代碼庫現況報告

> 最後更新：2026-04-08  
> 分析範圍：完整代碼庫靜態分析 + 邏輯追蹤  
> 狀態：**尚未達到可正式訓練的狀態**

---

## 一、專案概述

**BioNeuronai** 的目標是結合 AI 語言模型（TinyLLM）與加密貨幣量化交易，訓練一個能理解交易信號的雙語（中英文）語言模型，並整合回測、RAG 知識庫與自動進化訓練系統。

### 已完成的核心架構
- `src/nlp/tiny_llm.py` — Transformer-based 小型語言模型
- `src/nlp/bilingual_tokenizer.py` — 中英雙語 tokenizer
- `src/backtest/` — 回測引擎與交易信號收集
- `src/rag/` — RAG 知識庫系統
- `src/auto_evolve.py` — 自動進化訓練系統
- `src/unified_trainer.py` — 統一訓練入口

---

## 二、問題清單

### 🔴 致命錯誤（程式啟動或第一個 batch 即崩潰）

#### 2.1 `auto_evolve.py:144` — `outputs.logits` AttributeError

**問題描述：**  
`TinyLLM.forward()` 直接返回一個普通的 `torch.Tensor`，不是含有 `.logits` 屬性的 dataclass 或 namedtuple。`auto_evolve.py` 卻在訓練迴圈中使用 `outputs.logits`，導致第一個 batch 就拋出 `AttributeError: 'Tensor' object has no attribute 'logits'`。

**修復方向：**  
將 `outputs.logits` 改為直接使用返回值，即：
```python
# 修改前
logits = outputs.logits
# 修改後
logits = outputs  # forward() 直接返回 logits tensor
```

---

#### 2.2 `auto_evolve.py:179, 182` — 未定義變數 NameError

**問題描述：**  
訓練完成後嘗試儲存模型時，程式使用了從未被定義的 `config_dict` 和 `vocab_file` 兩個變數，必定拋出 `NameError`。

**修復方向：**  
在儲存前正確建立這兩個變數：
```python
config_dict = model.config.__dict__
vocab_file = os.path.join(TOKENIZER_DIR, "vocab.json")
```

---

#### 2.3 `auto_evolve.py:97` — 存檔格式不相容 KeyError

**問題描述：**  
`load_llm()` 期望讀取的 checkpoint 格式為 `{'state_dict': ..., 'config': ...}`，但 `unified_trainer.py` 的存檔只保存 `model.state_dict()`（純 `OrderedDict`），兩套系統格式完全不相容，`load_llm()` 嘗試讀取時拋出 `KeyError: 'config'`。

**修復方向：**  
統一存檔格式。建議 `unified_trainer.py` 改為：
```python
torch.save({'state_dict': model.state_dict(), 'config': model.config.__dict__}, path)
```

---

#### 2.4 `unified_trainer.py:334` — `--sig-only` 模式 KeyError

**問題描述：**  
`--sig-only` 模式的 DataLoader 只產出含 `feature_seq`/`signal_labels` 的 batch，但共用的 `_train_epoch()` 迴圈無條件讀取 `batch['input_ids']`，第一步就拋出 `KeyError: 'input_ids'`。

**修復方向：**  
在 `_train_epoch()` 中根據 batch 內容決定走語言模型路徑還是信號預測路徑：
```python
if 'input_ids' in batch:
    # LLM 訓練邏輯
elif 'feature_seq' in batch:
    # Signal 訓練邏輯
```

---

#### 2.5 `inference_engine.py:231` — warmup RuntimeError

**問題描述：**  
warmup 時使用 `torch.randn(1, 1024)` 產生浮點 Tensor 傳入 `forward()`，但 `forward()` 的第一個參數 `input_ids` 需要整數（`torch.long`）的 token ID。PyTorch embedding 層收到浮點輸入時拋出 `RuntimeError`。

**修復方向：**
```python
# 修改前
dummy = torch.randn(1, 1024).to(self.device)
# 修改後
dummy = torch.zeros(1, 16, dtype=torch.long).to(self.device)
```

---

### 🟠 嚴重錯誤（不崩潰，但訓練結果無意義）

#### 2.6 `auto_evolve.py:115` — 互動式 `input()` 阻塞非互動環境

**問題描述：**  
`auto_evolve.py` 在流程中呼叫 `input()` 等待使用者鍵盤輸入，在 Docker 容器、CI/CD 或任何非互動終端機環境中會無限期阻塞，導致訓練程序永遠無法推進。

**修復方向：**  
加入 `--non-interactive` CLI 參數，或偵測 `sys.stdin.isatty()` 自動略過互動提示。

---

#### 2.7 `unified_trainer.py:142` — `--sig-only` 預設使用純隨機雜訊

**問題描述：**  
若未提供真實信號資料，`--sig-only` 訓練會自動產生 1,000 筆完全隨機的 `(feature_seq, signal_label)` 資料。模型學到的是毫無意義的雜訊映射，訓練完全浪費計算資源。

**修復方向：**  
偵測到沒有真實資料時應直接報錯退出，而非靜默產生假資料：
```python
if not real_data_available:
    raise RuntimeError("No real signal data found. Please run backtest first.")
```

---

#### 2.8 `model/*/config.json` — config 欄位名稱不對齊

**問題描述：**  
`model/` 目錄下的 `config.json` 使用 HuggingFace 慣例的欄位名稱（如 `hidden_size`、`num_hidden_layers`、`num_attention_heads`），但 `TinyLLMConfig.from_dict()` 讀取的是自訂欄位名稱（如 `embed_dim`、`num_layers`、`num_heads`）。讀取時所有超參數被靜默忽略，全部使用 default 值，等同於每次都從預設架構開始，已調整的架構設定完全失效。

**修復方向：**  
更新 `config.json` 欄位名稱以對齊 `TinyLLMConfig`，或在 `from_dict()` 中加入欄位名稱映射轉換。

---

#### 2.9 `model/tokenizer/vocab.json` 不存在

**問題描述：**  
多個腳本在執行 `unified_trainer.py` 完成詞彙表初始化之前，就嘗試載入 `model/tokenizer/vocab.json`，導致 `FileNotFoundError`。此外，即使 tokenizer 完成初始化，詞彙表也僅從 23 段硬編碼對話建立，對真實輸入的覆蓋率預估低於 10%（UNK 率 > 90%）。

**修復方向：**  
1. 在代碼庫中提供一個預建的基礎 `vocab.json`（或在首次執行時自動建立）。
2. 擴大詞彙表建立語料，涵蓋交易術語、幣種名稱、技術指標等領域詞彙。

---

#### 2.10 `train_with_ai_teacher.py` — 訓練資料與任務無關

**問題描述：**  
所謂「AI 老師訓練資料」包含的全是通用問答（「什麼是 AI？」「機器學習是什麼？」），沒有任何交易相關內容（例如 K 線分析、MACD 信號、倉位管理等），訓練出的模型對交易推理完全無幫助。

**修復方向：**  
替換訓練資料，使用包含交易信號解讀、技術分析問答、風險管理情境的領域資料集。

---

#### 2.11 `backtest/service.py:397` — 循環依賴

**問題描述：**  
`collect_signal_training_data()` 負責收集信號訓練資料，但在沒有已訓練模型時，所有 signal 標籤都填零（因為需要呼叫模型推論才能產生非零標籤）。然而模型必須先用信號訓練資料才能訓練。這形成一個無法自舉（bootstrap）的循環依賴。

**修復方向：**  
第一輪訓練改用基於規則的信號標籤（如簡單的 MA 金叉/死叉、RSI 超買超賣），不依賴模型推論，完成冷啟動後再切換為模型生成標籤。

---

### 🟡 中等問題（不崩潰，但影響結果品質）

#### 2.12 `inference_engine.py:~727` — MACD 信號線計算不正確

**問題描述：**  
MACD 信號線（Signal Line）應為 MACD 值的 9 週期指數移動平均（EMA），但程式碼使用 `macd * (2/(n+1))` 一次乘法近似，完全不是滾動 EMA，造成 1024 維特徵向量中多個技術指標值偏差。

**修復方向：**  
改用標準 EMA 公式，或使用 `pandas_ta` / `ta-lib` 計算正確的 MACD 信號線。

---

#### 2.13 `rag/core/retriever.py:274` — 交易規則檢索空白

**問題描述：**  
`_retrieve_trading_rules()` 方法直接 `return []`，交易規則的 RAG 檢索功能完全未實作，是一個空殼。

**修復方向：**  
實作對 `trading_rules` 知識庫的向量相似度檢索邏輯。

---

#### 2.14 `rag/core/embeddings.py:229` — 無效的 fallback 嵌入

**問題描述：**  
在未安裝 `sentence-transformers` 時，系統 fallback 使用 hash-seeded 隨機向量作為文字嵌入。隨機向量的相似度計算完全無效，但系統不發出任何警告，用戶無從察覺 RAG 系統正在使用廢棄的嵌入。

**修復方向：**  
改為在缺少依賴時直接拋出 `ImportError` 並提示安裝指令，或提供 TF-IDF 等無需 GPU/額外依賴的合理 fallback。

---

#### 2.15 `tiny_llm.py:149` — `use_cache=False` 死程式碼

**問題描述：**  
`use_cache=False` 路徑在程式碼結構上永遠不會被執行，因為邏輯判斷的順序保證它總是走有快取的路徑，即使明確設定 `use_cache=False` 也一樣。

---

#### 2.16 `unified_trainer.py:257` — `strict=False` 載入靜默丟失訓練成果

**問題描述：**  
使用 `strict=False` 載入 checkpoint 時，若詞彙表大小不符，embedding 層會靜默地重新隨機初始化，所有已訓練的 embedding 參數全部遺失，但程式不輸出任何警告。

**修復方向：**  
偵測到 embedding 層尺寸不符時，應輸出明確警告，並讓用戶選擇截斷/填充詞彙表或重新訓練。

---

## 三、各模組現況彙整

| 模組 | 狀態 | 說明 |
|------|------|------|
| `src/nlp/tiny_llm.py` | 🟡 可用，有小問題 | `use_cache=False` 死程式碼 |
| `src/nlp/bilingual_tokenizer.py` | 🟠 部分可用 | 詞彙表覆蓋率極低 |
| `src/nlp/lora.py` | ✅ 完整可用 | LoRA 微調 |
| `src/nlp/quantization.py` | ✅ 完整可用 | 8-bit/4-bit 量化 |
| `src/nlp/model_export.py` | ✅ 完整可用 | ONNX/TorchScript/SafeTensors 導出 |
| `src/nlp/generation_utils.py` | ✅ 完整可用 | top-k/top-p/beam search |
| `src/nlp/hallucination_detection.py` | ✅ 完整可用 | 幻覺檢測（基於規則） |
| `src/nlp/uncertainty_quantification.py` | ✅ 完整可用 | 不確定性量化 |
| `src/unified_trainer.py` | 🔴 有致命錯誤 | 格式不相容、`--sig-only` 崩潰 |
| `src/auto_evolve.py` | 🔴 有致命錯誤 | 3 個立即崩潰的 Bug |
| `src/inference_engine.py` | 🔴 有致命錯誤 | warmup 型別錯誤；MACD 計算錯誤 |
| `src/backtest/service.py` | 🟠 有循環依賴 | 冷啟動問題 |
| `src/rag/core/retriever.py` | 🟠 部分空殼 | 交易規則檢索未實作 |
| `src/rag/core/embeddings.py` | 🟠 fallback 無效 | 缺少 sentence-transformers 時完全失效 |
| `train_with_ai_teacher.py` | 🟠 資料無關 | 訓練資料與交易任務無關 |

---

## 四、建議修復優先順序

### P0 — 必須先修（訓練流程完全無法啟動）

1. **`auto_evolve.py:144`** — `outputs.logits` → 直接使用返回值
2. **`auto_evolve.py:179,182`** — 補上未定義的 `config_dict` 和 `vocab_file`
3. **統一存檔格式** — `unified_trainer.py` 改為存 `{'state_dict':..., 'config':...}`
4. **`inference_engine.py:231`** — warmup 改用 `torch.long` tensor

### P1 — 高優先（訓練可啟動但結果無意義）

5. **`unified_trainer.py:334`** — `_train_epoch` 支援 signal batch 格式
6. **`model/*/config.json`** — 欄位名稱對齊 `TinyLLMConfig`
7. **補上 `model/tokenizer/vocab.json`** 並擴大詞彙表語料
8. **`backtest/service.py:397`** — 冷啟動改用規則式標籤

### P2 — 中優先（影響品質但不阻斷訓練）

9. **`auto_evolve.py:115`** — 移除非互動環境的 `input()` 阻塞
10. **`rag/core/retriever.py:274`** — 實作 `_retrieve_trading_rules()`
11. **`rag/core/embeddings.py:229`** — 補充依賴缺失的警告或 fallback
12. **`inference_engine.py:~727`** — 修正 MACD 信號線計算公式
13. **`train_with_ai_teacher.py`** — 替換為交易領域訓練資料

### P3 — 低優先（技術債，不影響當前功能）

14. **`tiny_llm.py:149`** — 修復 `use_cache=False` 死程式碼
15. **`unified_trainer.py:257`** — 載入時詞彙表尺寸不符應有明確警告

---

## 五、達到可訓練狀態所需的最小工作量

完成 **P0 + P1**（共 8 項修復）後，系統可以執行完整的一輪訓練。估計修改量：

- 約 6 個檔案需要修改
- 主要集中在 `auto_evolve.py`、`unified_trainer.py`、`inference_engine.py`
- `config.json` 欄位名稱對齊為配置調整，不涉及程式邏輯
- `vocab.json` 需要初始化腳本

---

*本報告由靜態代碼分析與邏輯追蹤產生，建議在修復後進行完整的整合測試。*
