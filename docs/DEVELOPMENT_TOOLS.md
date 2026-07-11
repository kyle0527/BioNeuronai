# 🔌 BioNeuronai 開發工具與插件指南
> 最後更新: 2026-01-22

## 📑 目錄

<!-- toc -->

- [🔹 VS Code 擴充功能](#%F0%9F%94%B9-vs-code-%E6%93%B4%E5%85%85%E5%8A%9F%E8%83%BD)
  * [✨ AI & 程式碼協助](#%E2%9C%A8-ai--%E7%A8%8B%E5%BC%8F%E7%A2%BC%E5%8D%94%E5%8A%A9)
  * [🐍 Python 開發](#%F0%9F%90%8D-python-%E9%96%8B%E7%99%BC)
  * [🧪 Jupyter Notebook](#%F0%9F%A7%AA-jupyter-notebook)
  * [📝 文檔與標記](#%F0%9F%93%9D-%E6%96%87%E6%AA%94%E8%88%87%E6%A8%99%E8%A8%98)
  * [🎨 Git 工具](#%F0%9F%8E%A8-git-%E5%B7%A5%E5%85%B7)
  * [🎯 品質與除錯](#%F0%9F%8E%AF-%E5%93%81%E8%B3%AA%E8%88%87%E9%99%A4%E9%8C%AF)
  * [🛠️ 專案管理與實用工具](#%F0%9F%9B%A0%EF%B8%8F-%E5%B0%88%E6%A1%88%E7%AE%A1%E7%90%86%E8%88%87%E5%AF%A6%E7%94%A8%E5%B7%A5%E5%85%B7)
  * [🌍 語言與主題](#%F0%9F%8C%8D-%E8%AA%9E%E8%A8%80%E8%88%87%E4%B8%BB%E9%A1%8C)
  * [🔧 其他工具](#%F0%9F%94%A7-%E5%85%B6%E4%BB%96%E5%B7%A5%E5%85%B7)
- [🐍 Python 套件與工具](#%F0%9F%90%8D-python-%E5%A5%97%E4%BB%B6%E8%88%87%E5%B7%A5%E5%85%B7)
  * [💹 加密貨幣交易核心](#%F0%9F%92%B9-%E5%8A%A0%E5%AF%86%E8%B2%A8%E5%B9%A3%E4%BA%A4%E6%98%93%E6%A0%B8%E5%BF%83)
  * [🤖 AI & 機器學習](#%F0%9F%A4%96-ai--%E6%A9%9F%E5%99%A8%E5%AD%B8%E7%BF%92)
  * [📊 資料處理與分析](#%F0%9F%93%8A-%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E8%88%87%E5%88%86%E6%9E%90)
  * [🌐 HTTP 客戶端與網頁抓取](#%F0%9F%8C%90-http-%E5%AE%A2%E6%88%B6%E7%AB%AF%E8%88%87%E7%B6%B2%E9%A0%81%E6%8A%93%E5%8F%96)
  * [📝 日誌與監控](#%F0%9F%93%9D-%E6%97%A5%E8%AA%8C%E8%88%87%E7%9B%A3%E6%8E%A7)
  * [🎯 實用工具](#%F0%9F%8E%AF-%E5%AF%A6%E7%94%A8%E5%B7%A5%E5%85%B7)
  * [🛠️ 開發工具](#%F0%9F%9B%A0%EF%B8%8F-%E9%96%8B%E7%99%BC%E5%B7%A5%E5%85%B7)
- [⚙️ 開發環境配置](#%E2%9A%99%EF%B8%8F-%E9%96%8B%E7%99%BC%E7%92%B0%E5%A2%83%E9%85%8D%E7%BD%AE)
  * [🔧 Python 建置系統](#%F0%9F%94%A7-python-%E5%BB%BA%E7%BD%AE%E7%B3%BB%E7%B5%B1)
  * [⚙️ VS Code 工作區設定](#%E2%9A%99%EF%B8%8F-vs-code-%E5%B7%A5%E4%BD%9C%E5%8D%80%E8%A8%AD%E5%AE%9A)
- [🎯 使用建議](#%F0%9F%8E%AF-%E4%BD%BF%E7%94%A8%E5%BB%BA%E8%AD%B0)
  * [新手入門順序](#%E6%96%B0%E6%89%8B%E5%85%A5%E9%96%80%E9%A0%86%E5%BA%8F)
  * [效能最佳化建議](#%E6%95%88%E8%83%BD%E6%9C%80%E4%BD%B3%E5%8C%96%E5%BB%BA%E8%AD%B0)
  * [代碼品質檢查](#%E4%BB%A3%E7%A2%BC%E5%93%81%E8%B3%AA%E6%AA%A2%E6%9F%A5)
  * [推薦的開發流程](#%E6%8E%A8%E8%96%A6%E7%9A%84%E9%96%8B%E7%99%BC%E6%B5%81%E7%A8%8B)
- [📋 版本資訊](#%F0%9F%93%8B-%E7%89%88%E6%9C%AC%E8%B3%87%E8%A8%8A)
- [🔗 相關資源](#%F0%9F%94%97-%E7%9B%B8%E9%97%9C%E8%B3%87%E6%BA%90)
  * [📚 開發指南](#%F0%9F%93%9A-%E9%96%8B%E7%99%BC%E6%8C%87%E5%8D%97)
  * [🏗️ 專案文檔](#%F0%9F%8F%97%EF%B8%8F-%E5%B0%88%E6%A1%88%E6%96%87%E6%AA%94)

<!-- tocstop -->

---

本指南記錄 BioNeuronai 加密貨幣交易系統中所有可用的開發工具、VS Code 擴充功能及 Python 依賴套件，協助開發者快速設置開發環境。

---

## 🔹 VS Code 擴充功能

### ✨ AI & 程式碼協助

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `openai.chatgpt` | 0.4.26 | OpenAI ChatGPT 整合 |
| `visualstudioexptteam.vscodeintellicode` | 1.3.2 | IntelliCode 智能建議 |
| `visualstudioexptteam.intellicode-api-usage-examples` | 0.2.9 | API 使用範例 |
| `sourcery.sourcery` | 1.39.0 | Python 程式碼自動優化 |

### 🐍 Python 開發

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `ms-python.python` | 2025.20.0 | Python 官方擴充套件 |
| `ms-python.vscode-pylance` | 2025.10.4 | Pylance 語言伺服器 |
| `ms-python.debugpy` | 2025.16.0 | Python 除錯工具 |
| `ms-python.autopep8` | 2025.2.0 | PEP8 自動格式化 |
| `ms-python.black-formatter` | 2025.2.0 | Black 格式化工具 |
| `ms-python.isort` | 2025.0.0 | 導入排序工具 |
| `ms-python.vscode-python-envs` | 1.12.0 | Python 環境管理 |
| `charliermarsh.ruff` | 2025.28.0 | Ruff 快速檢查工具 |
| `njpwerner.autodocstring` | 0.6.1 | 自動生成文檔字串 |
| `njqdev.vscode-python-typehint` | 1.5.1 | 類型提示支援 |
| `kevinrose.vsc-python-indent` | 1.21.0 | Python 縮排增強 |

### 🧪 Jupyter Notebook

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `ms-toolsai.jupyter` | 2025.9.1 | Jupyter Notebook 支援 |
| `ms-toolsai.jupyter-keymap` | 1.1.2 | Jupyter 鍵盤映射 |
| `ms-toolsai.jupyter-renderers` | 1.3.0 | Jupyter 渲染器 |
| `ms-toolsai.vscode-jupyter-cell-tags` | 0.1.9 | Jupyter 儲存格標籤 |

### 📝 文檔與標記

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `yzhang.markdown-all-in-one` | 3.6.3 | Markdown 增強功能 |
| `davidanson.vscode-markdownlint` | 0.60.0 | Markdown 檢查工具 |
| `bierner.markdown-mermaid` | 1.29.0 | Mermaid 圖表預覽 |
| `bpruitt-goddard.mermaid-markdown-syntax-highlighting` | 1.7.5 | Mermaid 語法高亮 |
| `mermaidchart.vscode-mermaid-chart` | 2.5.6 | Mermaid 圖表編輯器 |
| `tomoki1207.pdf` | 1.2.2 | PDF 檢視器 |

### 🎨 Git 工具

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `eamodio.gitlens` | 17.6.2 | GitLens - Git 超級增強 |
| `donjayamanne.githistory` | 0.6.20 | Git 歷史記錄 |
| `mhutchie.git-graph` | 1.30.0 | Git 圖形化介面 |
| `github.vscode-pull-request-github` | 0.124.0 | GitHub Pull Request |
| `ziyasal.vscode-open-in-github` | 1.3.6 | 在 GitHub 中開啟 |

### 🎯 品質與除錯

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `sonarsource.sonarlint-vscode` | 4.37.0 | SonarLint 程式碼品質檢查 |
| `usernamehw.errorlens` | 3.26.0 | 錯誤顯示增強 |
| `streetsidesoftware.code-spell-checker` | 4.2.6 | 拼字檢查 |
| `aaron-bond.better-comments` | 3.0.2 | 註解增強 |
| `gruntfuggly.todo-tree` | 0.0.226 | TODO 樹狀檢視 |

### 🛠️ 專案管理與實用工具

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `alefragnani.project-manager` | 12.8.0 | 專案管理器 |
| `formulahendry.code-runner` | 0.12.2 | 程式碼執行器 |
| `codezombiech.gitignore` | 0.10.0 | .gitignore 生成器 |
| `christian-kohler.path-intellisense` | 2.10.0 | 路徑智能提示 |
| `mechatroner.rainbow-csv` | 3.23.0 | CSV 檔案彩色顯示 |
| `oderwat.indent-rainbow` | 8.3.1 | 縮排彩虹色 |
| `redhat.vscode-yaml` | 1.19.1 | YAML 支援 |

### 🌍 語言與主題

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `ms-ceintl.vscode-language-pack-zh-hant` | 1.107.2025121009 | 繁體中文語言包 |
| `pkief.material-icon-theme` | 5.29.0 | Material 圖示主題 |
| `vscode-icons-team.vscode-icons` | 12.15.0 | vscode-icons 圖示主題 |

### 🔧 其他工具

| 擴充功能 | 版本 | 說明 |
|---------|------|------|
| `ms-vscode.powershell` | 2025.4.0 | PowerShell 支援 |
| `humao.rest-client` | 0.25.1 | REST API 客戶端 |

**總計**: 約 50 個擴充功能

---

## 🐍 Python 套件與工具

> **目前權威來源**：實際安裝依賴以根目錄 `pyproject.toml` 為準；本節只做摘要。若本節與 `pyproject.toml` 不一致，請優先相信 `pyproject.toml`。本機手冊目前以 Python 3.13 + PyTorch CPU 作為主要 runtime。

### 💹 加密貨幣交易核心

| 套件 | 版本 | 說明 |
|------|------|------|
| `websocket-client` | 1.9.0 | Binance WebSocket 行情連線 |
| `requests` | 2.34.2 | 同步 HTTP 請求 |
| `aiohttp` | 3.13.5 | 非同步 HTTP 請求 |
| `TA-Lib` | 0.6.8 | 技術分析指標 |

### 🤖 AI & 機器學習

| 套件 | 版本 | 說明 |
|------|------|------|
| `torch` | 2.8.0+cpu | PyTorch CPU runtime |
| `torchvision` | 0.23.0+cpu | PyTorch vision 套件 |
| `torchaudio` | 2.8.0+cpu | PyTorch audio 套件 |
| `sentence-transformers` | 5.5.0 | 語意向量與 RAG 支援 |
| `faiss-cpu` | 1.13.2 | 本機向量檢索 |
| `scikit-learn` | 1.8.0 | 機器學習工具集 |

### 📊 資料處理與分析

| 套件 | 版本 | 說明 |
|------|------|------|
| `pandas` | 3.0.3 | 資料分析 |
| `numpy` | 2.4.4 | 數值計算 |
| `regex` | 2026.5.9 | 進階文字處理 |

### 🌐 HTTP 客戶端與網頁抓取

| 套件 | 版本 | 說明 |
|------|------|------|
| `fastapi` | 0.136.1 | API server |
| `uvicorn[standard]` | 0.47.0 | ASGI runtime |
| `google-cloud-storage` | 3.10.1 | GCS artifacts |
| `google-cloud-secret-manager` | 2.28.0 | GCP secret integration |

### 📝 日誌與監控

| 套件 | 版本 | 說明 |
|------|------|------|
| `schedule` | 1.2.2 | 排程任務 |
| Python `logging` | 標準庫 | 專案主要 logging 入口 |

### 🎯 實用工具

| 套件 | 版本 | 說明 |
|------|------|------|
| `python-dotenv` | 1.2.2 | `.env` 載入 |
| `pydantic` | 2.13.4 | 資料驗證 |

### 🛠️ 開發工具

| 套件 | 版本 | 說明 |
|------|------|------|
| `black` | dev extra | 程式碼格式化 |
| `isort` | dev extra | import 排序 |
| `ruff` | dev extra | 快速檢查工具 |
| `mypy` | dev extra | 類型檢查 |

**注意**：`pyproject.toml` 目前沒有 `[rl]` optional extra；RL 訓練使用主依賴中的 PyTorch。

---

## ⚙️ 開發環境配置

### 🔧 Python 建置系統

**配置**: `pyproject.toml`

#### Tool Configurations

**Black** (程式碼格式化):
```toml
[tool.black]
line-length = 100
target-version = ['py313']
```

**Ruff** (快速檢查):
```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501", "E402", "F401"]
```

### ⚙️ VS Code 工作區設定

**配置**: `.vscode/settings.json`

#### Python/Pylance 最佳化
```json
{
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.typeCheckingMode": "basic",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true
}
```

#### 自動格式化
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### 檔案排除
```json
{
    "files.exclude": {
      "**/__pycache__": true,
      "**/*.pyc": true,
      "**/model/*.pth": true,
      "**/trading_data/**": true
    }
}
```

---

## 🎯 使用建議

### 新手入門順序

1. ✅ **安裝 Python 擴充功能包**
   - `ms-python.python`
   - `ms-python.vscode-pylance`
   - `charliermarsh.ruff`
   - `ms-python.black-formatter`

2. ✅ **配置 Python 環境**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchvision==0.23.0+cpu torchaudio==2.8.0+cpu
   python -m pip install -e .
   python -m pip install -e ".[dev]"   # 開發工具 (black, isort, ruff, mypy)
   ```

3. ✅ **安裝 Git 工具組**
   - `eamodio.gitlens`
   - `mhutchie.git-graph`
   - `github.vscode-pull-request-github`

4. ✅ **啟用代碼質量工具**
   - `sonarsource.sonarlint-vscode`
   - `usernamehw.errorlens`

5. ✅ **安裝文檔工具**
   - `yzhang.markdown-all-in-one`
   - `bierner.markdown-mermaid`

### 效能最佳化建議

- ⚡ 使用 `diagnosticMode: "openFilesOnly"` 以提升大型專案效能
- ⚡ 排除大型資料目錄 (`trading_data/`, `model/`, `__pycache__/`)
- ⚡ 僅在需要時啟用自動格式化
- ⚡ 定期清理 `__pycache__`

### 代碼品質檢查

```bash
# 運行 Ruff 檢查
ruff check src/

# 運行 Black 格式化
black src/

# 運行 Mypy 類型檢查
mypy src/

# 實際入口驗證
python main.py status
python main.py backtest-data --symbol BTCUSDT --interval 1h
npm --prefix frontend/devops-d run build
docker compose config --quiet
```

### 推薦的開發流程

1. **開發前**: 確保 SonarLint 和 ErrorLens 已啟用
2. **編碼中**: 使用 Pylance 自動補全和類型提示
3. **提交前**: 運行 `black` 和 `ruff` 格式化代碼
4. **驗證**: 跑 CLI / API / UI / Docker 正式入口，確認使用者流程可實際操作
5. **文檔**: 使用 Markdown 和 Mermaid 編寫技術文檔

---

## 📋 版本資訊

- **Python**: 3.11+
- **BioNeuronai**: v2.1

---

## 🔗 相關資源

### 📚 開發指南
- [V2.2 發展藍圖與規格](./V2.2_ROADMAP_AND_SPEC.md)
- [操作手冊](./manuals/04_CLI_OPERATION.md)
- [測試與驗證指南](./TESTING_AND_VALIDATION_GUIDE.md)
- [代碼修復指南](./CODE_FIX_GUIDE.md)

### 🏗️ 專案文檔
- [目錄結構分析](./SRC_DIRECTORY_ANALYSIS.md)
- [架構總覽](./ARCHITECTURE_OVERVIEW.md)
- [接手地圖](./PROJECT_HANDOVER_MAP.md)

---

**維護者**: BioNeuronai Team  
**更新週期**: 每月或重大變更時  
**問題回報**: 請至 GitHub Issues 提出
