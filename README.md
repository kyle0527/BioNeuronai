# BioNeuronAI

[繁體中文](#繁體中文) | [English](#english)

---

## 繁體中文

**生物啟發的新穎性檢測與安全協同框架**

BioNeuronAI 實現 Hebbian 學習機制與新穎性評估，並整合認證、SQLi、IDOR 等安全模組，
支援 RAG、工具閘門、儀表板觀測與強化學習流程。

### ✨ 特性

- 🧠 **Hebbian 學習**：具備突觸可塑性與短期記憶佇列。
- 🔍 **新穎性評分**：提供 0~1 區間的探索強度指標。
- 🛡️ **安全模組**：增強認證、SQLi、IDOR 偵測全覆蓋。
- 🛠️ **多語工具鏈**：所有註解與提示皆含 `[ZH]/[EN]` 雙語標籤。
- 📚 **文件系統**：MkDocs 自動生成 API、白皮書與教程。

### 🚀 快速開始

```bash
# 安裝核心、開發與文件依賴
pip install -e .[dev,docs]

# 啟動 CLI 示範
bioneuron-cli

# 啟動文件站點
mkdocs serve
```

### 🧪 測試

```bash
pytest tests/ -v
pytest tests/ --cov=bioneuronai
```

### 📚 文件重點

- 技術白皮書：`docs/whitepaper.md`
- API 參考：`docs/api/`
- 教程：`docs/tutorials/`（涵蓋 RAG、工具閘門、儀表板、強化學習）

更多細節請參考 [CHANGELOG](CHANGELOG.md)。

---

## English

**Bio-inspired novelty gating with safety-aligned modules.**

BioNeuronAI implements Hebbian learning with novelty scoring while integrating
authentication hardening, SQL injection, and IDOR detection modules. It includes
ready-to-follow guides for RAG pipelines, tool gating, dashboards, and
reinforcement learning loops.

### ✨ Features

- 🧠 **Hebbian Learning** with short-term memory buffers.
- 🔍 **Novelty Scoring** delivering normalized curiosity signals.
- 🛡️ **Safety Modules** covering enhanced auth, SQLi, and IDOR detection.
- 🛠️ **Bilingual Tooling** where prompts and comments follow `[ZH]/[EN]` labels.
- 📚 **Documentation Suite** powered by MkDocs with auto-generated API pages.

### 🚀 Quickstart

```bash
# Install package with development & docs extras
pip install -e .[dev,docs]

# Launch the interactive CLI demo
bioneuron-cli

# Serve the documentation locally
mkdocs serve
```

### 🧪 Testing

```bash
pytest tests/ -v
pytest tests/ --cov=bioneuronai
```

### 📚 Documentation Highlights

- Technical whitepaper: `docs/whitepaper.md`
- API reference: `docs/api/`
- Tutorials: `docs/tutorials/` (RAG, tool gating, dashboard, RL)

See the [CHANGELOG](CHANGELOG.md) for release history and upgrade notes.
