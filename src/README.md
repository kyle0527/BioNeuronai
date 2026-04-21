# src/ — BioNeuronai 原始碼

> 更新日期：2026-04-20

`src/` 是專案的 Python 原始碼與少量 runtime data 入口。這一層只說明主要 package 的定位與依賴方向；具體類別、方法、行數與操作範例請看各子目錄 README。

---

## 目錄

1. [頂層結構](#頂層結構)
2. [模組定位](#模組定位)
3. [依賴方向](#依賴方向)
4. [文件層級](#文件層級)

---

## 頂層結構

```text
src/
├── bioneuronai/     # 核心交易系統
├── schemas/         # 共用 Pydantic schema / enum
├── rag/             # 檢索增強生成系統
├── nlp/             # 語言模型、ChatEngine 與訓練工具
├── data/            # runtime / knowledge-base 資料
└── __init__.py
```

---

## 模組定位

| 模組 | 角色 | 詳細文件 |
|------|------|----------|
| `bioneuronai/` | 交易系統主體：core、data、analysis、planning、strategies、risk、api、cli | [bioneuronai README](bioneuronai/README.md) |
| `schemas/` | 跨模組共用資料模型、enum 與型別基準 | [schemas README](schemas/README.md) |
| `rag/` | embedding、retriever、internal knowledge base、news adapter、monitoring | [rag README](rag/README.md) |
| `nlp/` | TinyLLM、ChatEngine、分詞器、訓練、量化與模型工具 | [nlp README](nlp/README.md) |
| `data/` | `src/data/bioneuronai/...` runtime data，不是主要 Python package | 依資料內容查看 |

---

## 依賴方向

```text
schemas
  ↑
  ├── bioneuronai
  ├── rag
  └── nlp
```

重點：

1. `schemas` 是共用資料定義來源。
2. `bioneuronai` 是交易主體。
3. `rag` 會使用 `schemas`，並橋接 `bioneuronai.analysis`。
4. `nlp` 提供語言模型與 ChatEngine，CLI/API 可使用其中的對話能力。
5. `src/data/` 是資料目錄，不等同於 `src/bioneuronai/data/` 程式模組。

---

## 文件層級

1. 本文件只維護 `src/` 的概念導覽。
2. 子 package README 維護模組分工與重要主線。
3. 更深層 README 維護檔案、API、資料路徑與限制。

---

> 上層目錄：[根目錄 README](../README.md)
