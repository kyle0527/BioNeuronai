# src/ — BioNeuronai 原始碼

> **更新日期**: 2026-02-15

---

## 目錄

- [模組總覽](#模組總覽)
- [模組詳細](#模組詳細)
  - [bioneuronai/ — 核心交易系統](#bioneuronai--核心交易系統)
  - [nlp/ — 自研語言模型工具包](#nlp--自研語言模型工具包)
  - [rag/ — 檢索增強生成系統](#rag--檢索增強生成系統)
  - [schemas/ — Pydantic 資料模型](#schemas--pydantic-資料模型)
- [模組間依賴](#模組間依賴)
- [程式碼統計](#程式碼統計)

---

## 模組總覽

`src/` 包含 BioNeuronai 交易系統的全部原始碼，分為 4 個頂層模組：

```
src/
├── bioneuronai/     # 核心交易系統（5 層架構）
├── nlp/             # 自研語言模型工具包
├── rag/             # 檢索增強生成系統
├── schemas/         # Pydantic 資料模型定義
└── __init__.py
```

---

## 模組詳細

### bioneuronai/ — 核心交易系統

BioNeuronai 的主體模組，實現完整的加密貨幣量化交易系統。

| 子模組 | 說明 |
|--------|------|
| `core/` | 核心基礎設施（市場分析、計畫控制、外部數據） |
| `data/` | 數據層（資料庫管理、Binance 連接器、Web 數據） |
| `strategies/` | 策略層（11 種交易策略 + 策略引擎） |
| `risk_management/` | 風險管理（倉位管理、風控引擎） |
| `trading/` | 交易執行（回測引擎、自動化、SOP） |
| `analysis/` | 分析層（新聞分析、關鍵字系統、自我改善） |

📖 [詳細文檔](bioneuronai/README.md)

---

### nlp/ — 自研語言模型工具包

獨立的 LLM 開發工具包，提供 100M 參數 GPT 風格 Transformer 的完整訓練、微調、量化到部署工具鏈。

| 功能 | 說明 |
|------|------|
| 核心模型 | TinyLLM (100M params, 12 層, 768 維) |
| 分詞器 | BPE + 英中雙語 |
| 優化 | LoRA 微調 / 8-bit & 4-bit 量化 |
| 可靠性 | Monte Carlo Dropout + 幻覺檢測 + 誠實生成 |
| 導出 | ONNX / TorchScript |

📖 [詳細文檔](nlp/README.md)

---

### rag/ — 檢索增強生成系統

整合向量嵌入、語義檢索、內部知識庫和外部數據源的 RAG 系統。

| 子模組 | 說明 |
|--------|------|
| `core/` | 嵌入服務 + 統一檢索器 |
| `internal/` | 內部知識庫 + FAISS 向量索引 |
| `services/` | 新聞適配器 + 交易前檢查 |
| `monitoring/` | 請求追蹤 + 延遲統計 |

📖 [詳細文檔](rag/README.md)

---

### schemas/ — Pydantic 資料模型

基於 Pydantic v2 的統一資料模型定義，作為整個系統的 Single Source of Truth。

| 統計 | 數量 |
|------|------|
| Schema 檔案 | 17 個 |
| 枚舉定義 | 37 個 |
| Pydantic 模型 | 75+ 個 |
| 自訂型別 | 23 個 |
| Schema 版本 | 2.3.0 |

📖 [詳細文檔](schemas/README.md)

---

## 模組間依賴

```
schemas/  ←──────── (所有模組共用)
    ▲
    │
bioneuronai/  ←──── 核心業務邏輯
    ▲
    │
rag/  ────────────── 檢索增強（依賴 bioneuronai + schemas）
    
nlp/  ────────────── 獨立模組（訓練腳本從 bioneuronai 匯入）
```

---

## 程式碼統計

| 模組 | Python 檔案數 | 總行數 |
|------|---------------|--------|
| `bioneuronai/` | 23 | ~8,500 |
| `nlp/` | 19 | ~7,800 |
| `rag/` | 10 | ~2,200 |
| `schemas/` | 19 | ~5,800 |
| **合計** | **71** | **~24,300** |

---

> 📖 上層目錄：[根目錄 README](../README.md)