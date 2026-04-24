# src/

`src/` 是專案的 Python 原始碼根目錄。這一層只負責說明主要 package 的定位與文件入口，不展開檔案級細節。

## 頂層結構

- `bioneuronai/`
  交易系統主體。
  文件：[bioneuronai/README.md](bioneuronai/README.md)
- `schemas/`
  共用資料模型與 enum 邊界。
  文件：[schemas/README.md](schemas/README.md)
- `rag/`
  檢索增強生成子系統。
  文件：[rag/README.md](rag/README.md)
- `nlp/`
  語言模型、對話、分詞器與訓練工具。
  文件：[nlp/README.md](nlp/README.md)
- `data/`
  runtime / knowledge-base / 快取資料目錄，不是主要 Python package README 鏈的一部分。
- `__init__.py`
  `src` package 入口。

## 依賴方向

```text
schemas
  ↑
  ├── bioneuronai
  ├── rag
  └── nlp

rag
  ↑
  └── bioneuronai.analysis
```

重點是：

- `schemas` 是跨模組共用定義來源。
- `bioneuronai` 是交易系統主線。
- `rag` 是獨立 package，但會橋接 `bioneuronai.analysis`。
- `nlp` 提供模型、對話與訓練工具；新的 RAG 主線不在 `nlp` 裡。
- `src/data/` 是資料目錄，不等於 `src/bioneuronai/data/` 程式模組。

## 文件層級

- 本文件只做頂層導覽。
- 下一層 README 負責各 package 的模組分工：
  [bioneuronai/README.md](bioneuronai/README.md)
  [schemas/README.md](schemas/README.md)
  [rag/README.md](rag/README.md)
  [nlp/README.md](nlp/README.md)
- 若子 package 下面還有 README，應由該 package README 再往下連。

## 上層文件

- [根目錄 README](../README.md)
