# 模型目錄說明

## 目錄

- [定位](#定位)
- [目前內容](#目前內容)
- [主要模型資產](#主要模型資產)
- [實際載入位置](#實際載入位置)
- [使用建議](#使用建議)
- [已移除的舊描述](#已移除的舊描述)

---

## 定位

`model/` 是專案根目錄下的**模型資產目錄**，存放目前仍會被程式碼直接載入或供訓練流程使用的權重與模型封裝。

這份 README 是**上層總覽**，只說明：

- 這個目錄目前有哪些模型資產
- 哪些仍有主程式載入點
- 哪些屬於 NLP / 歷史訓練資產
- 應該優先看哪份子 README

較細的 TinyLLM 架構、訓練能力、檔案清單，請直接看子目錄文件：

- [tiny_llm_en_zh/README.md](C:/D/E/BioNeuronai/model/tiny_llm_en_zh/README.md)
- [tiny_llm_en_zh_trained/README.md](C:/D/E/BioNeuronai/model/tiny_llm_en_zh_trained/README.md)

---

## 目前內容

| 項目 | 類型 | 目前狀態 | 主要用途 |
| --- | --- | --- | --- |
| `my_100m_model.pth` | PyTorch checkpoint | 主交易模型 | `bioneuronai.core` 交易推論 |
| `tiny_llm_100m.pth` | PyTorch checkpoint | NLP 基礎權重 | `src/nlp/` 訓練/封裝流程起點 |
| `tiny_llm_en_zh/` | 模型封裝目錄 | 基礎版 | TinyLLM 雙語基礎模型包 |
| `tiny_llm_en_zh_trained/` | 模型封裝目錄 | 訓練版 | TinyLLM 訓練後模型包 |

目前檔案大小（依工作樹實際內容）：

- `my_100m_model.pth`: `444,849,917` bytes
- `tiny_llm_100m.pth`: `496,238,771` bytes
- `tiny_llm_en_zh_trained/pytorch_model.bin`: `496,238,131` bytes

---

## 主要模型資產

### `my_100m_model.pth`

這是目前 **`src/bioneuronai` 主交易路徑** 仍會直接載入的模型權重。

已確認的實際用途：

- `src/bioneuronai/core/inference_engine.py`
- `src/bioneuronai/core/trading_engine.py`

目前載入名稱固定使用 `my_100m_model`，對應實體檔案：

```text
model/my_100m_model.pth
```

模型類別仍來自：

```text
archived/pytorch_100m_model.py::HundredMillionModel
```

這代表它雖然是主交易模型，但**目前實際上仍是 legacy 交易模型相容路徑**，而且模型定義仍依賴 `archived/`。後續若要整理模型系統，這會是需要處理的技術債。

### `tiny_llm_100m.pth`

這是 TinyLLM 權重 checkpoint，主要被 `src/nlp/` 工具鏈與 `ChatEngine` 使用，不是 `src/bioneuronai` 交易主鏈的正式交易模型。

目前已確認的用途：

- `src/nlp/tiny_llm.py` 產出/保存
- `src/nlp/chat_engine.py` 預設文字對話模型
- `src/nlp/tools/create_model_package.py` 作為模型封裝輸入
- `src/nlp/training/` 相關流程的基礎權重

因此它比較接近：

- NLP 開發資產
- 訓練起點
- 封裝來源

而不是現在交易系統的直接推論模型。

### `tiny_llm_en_zh/`

這是 TinyLLM 的**基礎模型封裝目錄**，包含：

- `config.json`
- `metadata.json`
- `pytorch_model.bin`
- tokenizer 與 vocab 檔案

它的詳細架構、功能與使用方式已在子 README 中維護，請直接查看：

- [tiny_llm_en_zh/README.md](C:/D/E/BioNeuronai/model/tiny_llm_en_zh/README.md)

### `tiny_llm_en_zh_trained/`

這是 TinyLLM 的**訓練後模型封裝目錄**，包含：

- `config.json`
- `pytorch_model.bin`
- `training_history.json`
- tokenizer 與 vocab 檔案

它目前仍可被 `src/nlp/` 舊工具鏈與訓練/實驗流程引用，但上層 README 不再把它描述成 `src/bioneuronai` 主交易系統的正式依賴。

原因是：

- 目前直接命中的載入點在 `src/nlp/`
- `src/nlp/rag_system.py` 已明確標示為 `DEPRECATED`
- 現行 `bioneuronai.core` 主交易流程並不依賴這個模型目錄

詳細內容請看：

- [tiny_llm_en_zh_trained/README.md](C:/D/E/BioNeuronai/model/tiny_llm_en_zh_trained/README.md)

---

## 實際載入位置

### 交易主鏈

目前交易模型由 `ModelLoader` 預設解析到專案根目錄下的 `model/`：

```python
# src/bioneuronai/core/inference_engine.py
model_dir = Path(__file__).parent.parent.parent.parent / "model"
```

主交易載入範例：

```python
from bioneuronai.core.inference_engine import InferenceEngine

engine = InferenceEngine()
engine.load_model("my_100m_model")
```

更高層的交易引擎則會呼叫：

```python
from bioneuronai.core.trading_engine import TradingEngine

engine = TradingEngine(enable_ai_model=True)
engine.load_ai_model("my_100m_model", warmup=True)
```

### NLP / TinyLLM 路徑

TinyLLM 相關資產目前主要由 `src/nlp/` 使用，例如：

- `src/nlp/tiny_llm.py`
- `src/nlp/tools/create_model_package.py`
- `src/nlp/training/train_with_ai_teacher.py`
- `src/nlp/training/auto_evolve.py`

這些是**NLP 工具鏈與模型實驗路徑**，不等同於 `src/bioneuronai` 的主交易執行鏈。

---

## 使用建議

1. 若你在看主交易系統，先關注 `my_100m_model.pth`。
2. 若你在看 chat、語言模型訓練或 TinyLLM 封裝，再看 `tiny_llm_*` 系列。
3. 上層 README 不再重複 TinyLLM 子目錄的完整功能表，避免和子 README 產生雙重維護。
4. 若 `my_100m_model.pth` 無法載入，先確認不是 Git LFS pointer 或缺檔。

---

## 已移除的舊描述

以下內容已從上層 README 移除，因為它們已過時、過細，或不再適合作為上層總覽描述：

- 把 `tiny_llm_en_zh_trained/` 直接寫成目前正式的 `RAG 新聞分析` 主依賴
- 直接把 `src/nlp/rag_system.py` 視為現行主路徑
- 過細的 checkpoint key 列表
- 舊版推論速度與載入耗時數值
- 應留在子 README 的 TinyLLM 架構細節與訓練歷程全文

---

**最後更新**: 2026-03-28

上層連結：

- [根目錄 README](C:/D/E/BioNeuronai/README.md)
