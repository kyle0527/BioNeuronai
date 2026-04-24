# 模型相容模組 (Models)

> 路徑：`src/bioneuronai/models/`
> 更新日期：2026-04-23
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

目前這個資料夾只做一件事：

1. 讓 `InferenceEngine` 在遇到舊版 MLP checkpoint 時，有穩定且不依賴 `archived/` 的載入位置

這表示：

1. 舊版交易權重相容性維護在這裡
2. 新模型訓練與新模型架構不在這裡維護
3. 新的 NLP / TinyLLM 主線應看 `src/nlp/`

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

1. 定義 `HundredMillionModel`
2. 用於相容載入舊格式 `my_100m_model.pth`
3. 被 `bioneuronai.core.inference_engine.ModelLoader` 在偵測到 legacy MLP checkpoint 時自動使用

---

## 維護邊界

1. 本文件只描述相容模型的角色，不描述新模型訓練流程。
2. 若未來 `models/` 新增更多相容類型，應在此文件補上檔案分工。
3. 新模型主線、tokenizer 與訓練入口請看 `src/nlp/` 與專案層訓練文件。

---

> 上層目錄：[BioNeuronai README](../README.md)
