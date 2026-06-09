# 模型相容模組 (Models)

> 路徑：`src/bioneuronai/models/`
> 更新日期：2026-05-11
> 定位：舊版 checkpoint 相容層

`models/` 目前不是新模型訓練主目錄，而是提供舊版交易模型 checkpoint 的正式相容載入位置。

---

## 目錄

1. [模組定位](#模組定位)
2. [實際結構](#實際結構)
3. [核心檔案](#核心檔案)
4. [維護邊界](#維護邊界)

---

## 模組定位

目前這個資料夾做兩件事：

1. 讓 `InferenceEngine` 在遇到舊版 MLP checkpoint 時，有穩定的相容載入位置
2. 明確定義 checkpoint 樣式詘別規則，供 `ModelLoader` 自動判斷使用 `HundredMillionModel`

這表示：

1. 舊版交易權重相容性維護在這裡
2. 新模型訓練與新模型架構不在這裡維護
3. 現役交易模型權重護存於 **`model/`（專案根目錄）**，不是這裡
4. 新的 NLP / TinyLLM 主線請看 `src/nlp/`

**現役 checkpoint 指定方式**：

`ModelLoader` 依序解析模型路徑：

1. `MODEL_PATH` / `BIONEURONAI_MODEL_PATH` 環境變數（支援 GCS URI）
2. `MODEL_DIR` / `BIONEURONAI_MODEL_DIR` 環境變數
3. `config/active_model.json`（由 `POST /api/v1/model/promote` 寫入）
4. `model/{model_name}.pth`（專案根目錄預設回退）

目前實際 promote 的現役樓檢：

```json
{
  "model_name": "my_100m_model",
  "model_path": "C:\\D\\E\\BioNeuronai\\model\\my_100m_model_trained_20260510.pth",
  "promoted_at": "2026-05-11T00:10:05",
  "notes": "validation promote on 2026-05-11, same trained checkpoint"
}
```

---

## 實際結構

```text
models/
├── __init__.py
├── legacy.py   # HundredMillionModel 舊版相容模型
└── README.md
```

檔案對照：
1. [__init__.py](__init__.py)
2. [legacy.py](legacy.py)

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到相容模型檔案層級。

---

## 核心檔案

### `legacy.py`

1. 定義 `HundredMillionModel`（架構：1024 → 8192 → 8192 → 4096 → 512， MLP + GELU + LayerNorm）
2. 用於相容載入舊格式 `my_100m_model.pth`
3. 被 `bioneuronai.core.inference_engine.ModelLoader` 在偵測到 legacy MLP checkpoint
   （state_dict key 以 `hidden_layers.` 開頭）時自動使用
4. 不用於新模型訓練，不用於 TinyLLM signal inference 導入；
   目前現役樓檢是 TinyLLM `numeric_proj` + `signal_head` 格式，軚道 `forward_signal()`

**識別逻輯**（`ModelLoader` 自動判斷）：

| Checkpoint 類型 | 識別特徵 | 載入類別 |
|---|---|---|
| 舊版 100M MLP | state_dict key 以 `hidden_layers.` 開頭 | `HundredMillionModel` |
| TinyLLM signal | 包含 `numeric_proj.*` 與 `signal_head.*` | `TinyLLM` |
| TinyLLM 文字生成 | 缺少 signal head | 拒絕載入（防止錯誤推論）|

---

## 維護邊界

1. 本文件只描述相容模型的角色，不描述新模型訓練流程。
2. 若未來 `models/` 新增更多相容類型，應在此文件補上檔案分工。
3. 新模型主線、tokenizer 與訓練入口請看 `src/nlp/` 與專案層訓練文件。

---

> 上層目錄：[BioNeuronai README](../README.md)
