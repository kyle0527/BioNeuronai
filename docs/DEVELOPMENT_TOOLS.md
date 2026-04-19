# 🔌 BioNeuronai 開發工具與插件指南
> 最後更新: 2026-01-22

## 📑 目錄

1. 🔹 VS Code 擴充功能
2. 🐍 Python 套件與工具
3. ⚙️ 開發環境配置
4. 🎯 使用建議
5. 📋 版本資訊
6. 🔗 相關資源

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

### 💹 加密貨幣交易核心

| 套件 | 版本 | 說明 |
|------|------|------|
| `python-binance` | >=1.0.0 | Binance API 客戶端 |
| `ccxt` | >=4.0.0 | 統一加密貨幣交易所 API |
| `ta` | >=0.11.0 | 技術分析指標庫 |
| `ta-lib` | >=0.4.0 | TA-Lib 技術分析 |

### 🤖 AI & 機器學習

| 套件 | 版本 | 說明 |
|------|------|------|
| `torch` | >=2.1.0 | PyTorch 深度學習框架 |
| `scikit-learn` | >=1.3.0 | 機器學習工具集 |
| `numpy` | >=1.24.0 | 數值計算 |
| `transformers` | >=4.30.0 | Hugging Face 轉換器 |
| `openai` | >=1.0.0 | OpenAI API 客戶端 |

### 📊 資料處理與分析

| 套件 | 版本 | 說明 |
|------|------|------|
| `pandas` | >=2.0.0 | 資料分析 |
| `numpy` | >=1.24.0 | 數值計算 |
| `matplotlib` | >=3.7.0 | 資料視覺化 |
| `seaborn` | >=0.12.0 | 統計圖表 |

### 🌐 HTTP 客戶端與網頁抓取

| 套件 | 版本 | 說明 |
|------|------|------|
| `httpx` | >=0.27.0 | 非同步 HTTP 客戶端 |
| `requests` | >=2.31.0 | 同步 HTTP 客戶端 |
| `aiohttp` | >=3.8.0 | 非同步 HTTP 框架 |
| `beautifulsoup4` | >=4.12.2 | HTML 解析工具 |

### 📝 日誌與監控

| 套件 | 版本 | 說明 |
|------|------|------|
| `loguru` | >=0.7.0 | 簡化的日誌記錄 |
| `rich` | >=13.0.0 | 豐富的終端輸出 |
| `click` | >=8.1.0 | 命令列介面 |

### 🎯 實用工具

| 套件 | 版本 | 說明 |
|------|------|------|
| `tenacity` | >=8.3.0 | 重試與韌性模式 |
| `python-dotenv` | >=1.0.1 | 環境變數管理 |
| `pydantic` | >=2.7.0 | 資料驗證 |
| `orjson` | >=3.10.0 | 高效 JSON 處理 |

### 🛠️ 開發工具

| 套件 | 版本 | 說明 |
|------|------|------|
| `pytest` | >=8.0.0 | 測試框架 |
| `black` | >=24.0.0 | 程式碼格式化 |
| `ruff` | >=0.3.0 | 快速檢查工具 |
| `mypy` | >=1.8.0 | 類型檢查 |

**總計**: 30+ 個核心 Python 套件

---

## ⚙️ 開發環境配置

### 🔧 Python 建置系統

**配置**: `pyproject.toml`

#### Tool Configurations

**Black** (程式碼格式化):
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.git
  | \.venv
  | build
  | dist
  | __pycache__
)/
'''
```

**Ruff** (快速檢查):
```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]
```

**Pytest** (測試框架):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

---

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
    "**/.pytest_cache": true,
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
   pip install -r requirements-crypto.txt
   pip install -e ".[dev]"        # 開發工具 (pytest, black, ruff, mypy)
   pip install -e ".[rl]"         # 選填：強化學習模組
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
- ⚡ 定期清理 `.pytest_cache` 和 `__pycache__`

### 代碼品質檢查

```bash
# 運行 Ruff 檢查
ruff check src/

# 運行 Black 格式化
black src/

# 運行 Mypy 類型檢查
mypy src/

# 運行測試
pytest tests/
```

### 推薦的開發流程

1. **開發前**: 確保 SonarLint 和 ErrorLens 已啟用
2. **編碼中**: 使用 Pylance 自動補全和類型提示
3. **提交前**: 運行 `black` 和 `ruff` 格式化代碼
4. **測試**: 使用 `pytest` 運行單元測試
5. **文檔**: 使用 Markdown 和 Mermaid 編寫技術文檔

---

## 📋 版本資訊

- **Python**: 3.11+
- **BioNeuronai**: v1.0
- **專案類型**: 加密貨幣量化交易系統

---

## 🔗 相關資源

### 📚 開發指南
- [用戶手冊](./USER_MANUAL.md)
- [交易策略指南](./TRADING_STRATEGIES_GUIDE.md)
- [數據源指南](../archived/docs_v2_1_legacy/DATA_SOURCES_GUIDE.legacy_20260406.md)
- [代碼修復指南](./CODE_FIX_GUIDE.md)

### 🏗️ 專案文檔
- [專案結構](../archived/docs_v2_1_legacy/PROJECT_STRUCTURE.legacy_20260406.md)
- [加密交易 README](../CRYPTO_TRADING_README.md)
- [SOP 自動化文檔](./CRYPTO_TRADING_SOP.md)

---

**維護者**: BioNeuronai Team  
**更新週期**: 每月或重大變更時  
**問題回報**: 請至 GitHub Issues 提出

