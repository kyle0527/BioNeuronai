# BioNeuronai 操作手冊
**版本**：v2.1
**更新日期**：2026-04-06
**適用對象**：初次使用者 / 日常操作參考

---

## 📑 目錄

1. 系統概述
2. 安裝與環境設定
3. Binance API 金鑰設定
4. CLI 命令完整參考
5. 設定檔與資料契約說明
6. 標準操作流程
7. 常見問題排查
8. 風險警示

---

## 1. 系統概述

BioNeuronai (v2.1) 是一套加密貨幣期貨交易系統。  
目前正式主線已收斂為：

- `planning/` 負責高階規劃與盤前檢查
- `core/` 負責主交易引擎與 AI 推理
- `strategies/` 負責固定策略、selector、fusion 與競爭層
- `trading/` 負責訂單 / 帳戶 / 持倉 / 資金的事實層
- `backtest/` 負責 replay / backtest

### 核心能力

| 功能 | 說明 | 需要 torch | 需要 API 金鑰 | 主責模組 |
|------|------|:----------:|:------------:|----------|
| 系統健康檢查 | 診斷所有模組狀態 | ✗ | ✗ | `cli/` |
| 每日交易計劃 | 10 步驟 SOP (總經理視角) | ✗ | 部分步驟 | `planning/` |
| 進場前驗核 | 技術 / 基本面三重確認 (交易員視角) | ✗ | ✅ | `planning/` |
| 新聞分析 | 情緒與事件提取 | ✗ | ✗ | `rag/` & `analysis/news` |
| 紙交易模擬 | 在未連線 Binance 情況下驗證主交易邏輯 | ⚠️ 可選 | ✗ | `core/` & `backtest/` |
| 測試網/實盤交易 | 透過 Binance connector 進行即時交易 | ✅ | ✅ | `core/` & `trading/` |
| AI 對話助理 | 雙語交易知識問答（中 / 英），可注入即時市場資料 | ⚠️ 可選 | ✗ | `nlp/chat_engine` |

---

## 2. 安裝與環境設定

### 前置需求
- Python **3.9** 以上（推薦 3.10 / 3.11）

### 安裝步驟

```bash
git clone https://github.com/BioNeuronai/BioNeuronai.git
cd BioNeuronai
python -m venv venv

# Windows 啟動: venv\Scripts\activate
# Linux/Mac 啟動: source venv/bin/activate

# 基礎安裝 (執行 plan/pretrade/news)
pip install pydantic>=2.0.0 numpy>=1.24.0 pandas>=2.0.0 websocket-client requests aiohttp

# 完整依賴 (包含 AI 模型)
pip install -r requirements-crypto.txt

# 選填：強化學習模組 (rl_fusion_agent)
pip install -e ".[rl]"
```

若 `torch` 未安裝，執行 `status` 時 `TradingEngine` 會顯示警告，但不影響沒有用到 AI 推理的非實盤動作。

---

## 3. Binance API 金鑰設定

依據 `API_INTEGRATION_BASELINE.md`，目前建議以**環境變數與動態載入**為主，不建議直接把金鑰寫死在 `config/` 中的 `.py` 檔內。

**設定方式 (.env)**:
```bash
cp .env.example .env
```
編輯 `.env`，填寫：
```ini
BINANCE_API_KEY=你的測試網或正式網_API_KEY
BINANCE_API_SECRET=你的測試網或正式網_SECRET
BINANCE_TESTNET=true
```

> **注意**：使用 `trade --live` 必須同時切換 `BINANCE_TESTNET=false` 以及正式網金鑰，並確保期貨合約權限已開通。

---

## 4. CLI 命令完整參考

目前 CLI 正式入口為根目錄下的 `main.py`，再交由 `src/bioneuronai/cli/main.py` 分派。

### `status`
**用途**：系統健康檢查。
```bash
python main.py status
```

> 💡 **進階操作提示**：
> 關於以下功能的更詳細參數（如 `--walk-forward` 樣本內外驗證、`--max-items` 新聞自適應抓取），請參閱我們最新編寫的專業子手冊：
> - 📊 [分析模組操作手冊 (ANALYSIS_MODULE_USER_MANUAL.md)](ANALYSIS_MODULE_USER_MANUAL.md)：涵蓋 `news`, `plan`, `pretrade`。
> - ⚔️ [策略模組操作手冊 (STRATEGY_MODULE_USER_MANUAL.md)](STRATEGY_MODULE_USER_MANUAL.md)：涵蓋 `strategy-backtest` 等競技場指令。

### `plan`
**依賴子系統**：`planning/plan_controller.py`
**用途**：產出 10 步驟高階分析。
```bash
python main.py plan
python main.py plan --output reports/$(date +%F)_plan.json
```

### `pretrade`
**依賴子系統**：`planning/pretrade_automation.py`
**用途**：執行交易前的硬性檢查。
```bash
python main.py pretrade --symbol BTCUSDT --action long
```

### `news`
**用途**：抓取加密貨幣新聞。
```bash
python main.py news --symbol BTCUSDT --max-items 10
```

### `simulate`
**依賴子系統**：`backtest/mock_connector.py`
**用途**：利用本地歷史資料推送 K 線，模擬實盤行進。

### `trade`
**依賴子系統**：`core/trading_engine.py` 與 connector / 帳戶狀態層  
**用途**：進行測試網或實盤交易。
```bash
python main.py trade --testnet
python main.py trade --live
```
使用 `--live` 時系統會有強制二次確認，避免意外按下 Enter 進入實盤。

### `chat`
**依賴子系統**：`src/nlp/chat_engine.py`、`src/nlp/training/trading_dialogue_data.py`  
**用途**：與 AI 交易助理進行雙語對話（繁體中文 / 英文），可詢問策略、合約規則、技術分析、系統操作等。
```bash
python main.py chat                          # 自動語言偵測
python main.py chat --language zh            # 強制繁體中文
python main.py chat --language en            # 強制英文
python main.py chat --symbol BTCUSDT         # 附帶即時市場資料注入對話上下文
```
- 輸入 `exit` 或 `quit` 結束對話
- 若模型未載入，自動降級為關鍵字匹配的規則型回應
- 對話知識庫涵蓋：幣安合約機制、訂單類型、風險管理、技術分析、BioNeuronai 系統操作

| 功能 | 需要 torch | 需要 API 金鑰 |
|------|:----------:|:------------:|
| 規則型回應（關鍵字匹配）| ✗ | ✗ |
| AI 模型完整對話 | ✅ | ✗ |
| 即時市場資料注入 | ✗ | ✅ |

也可透過 REST API 呼叫（含多輪對話 session 管理）：
```bash
POST /api/v1/chat          # 對話
DELETE /api/v1/chat/{id}   # 清除對話歷史
```

---

## 5. 設定檔與資料契約說明

### Data Schemas (`src/schemas/`)
v2.1 的正式主線以 Pydantic v2 模型作為跨模組主要資料契約。
- 欲調整任何設定值，請先確認 `schemas/` 下的定義。
- 當使用 `trade` 或 `plan` 時，CLI 端點會打包對應的 Schema，然後才傳給 `core/` 或 `planning/`，避免任何 Dictionary 混用。

### 傳統 Config (`config/trading_config.py`)
> ⚠️ **過渡注意**：此處設定正在逐步過渡，如果您找尋風險閥值的調整（如 `MAX_DRAWDOWN_PERCENTAGE`），目前仍需參照 `risk_management/` 中套用的預設值與 `config/` 檔定義。

---

## 6. 標準操作流程 (SOP)

1. **盤前檢查** (`status`) => 確保網路與環境變數載入。
2. **大盤掃描** (`plan`) => 產出高階交易計劃或觀望建議。
3. **特定幣種確認** (`pretrade`) => 對候選標的做進場前檢查。
4. **啟動回放或測試網觀測** (`backtest` / `simulate` / `trade --testnet`)。
5. **檢閱結果與帳戶狀態** => 依情境查看 replay runtime、資料庫記錄或帳戶快照。

---

## 7. 常見問題排查

### `ModuleNotFoundError: No module named 'bioneuronai'`
**原因**：未加載根目錄到 `PYTHONPATH`，建議一律使用 `python main.py [指令]`，因為 `main.py` 已經在頂端掛載了 `sys.path.insert(0, str(project_root / "src"))`。

### Pydantic 模型驗證失敗
**原因**：系統嚴格檢查資料型別（例如字串傳入整數，或是少給 `symbol`）。通常是因為開發或自建腳本時跳過了 Schema Builder，請回去查閱 `src/schemas/` 的必填欄位。

---

## 8. 風險警示

1. `--testnet` 不等於本地模擬：它仍會連 Binance 測試網，請確保網路穩定且金鑰配置正確。
2. `--live` 下的實際風險控制，仍以 `risk_management/` 與當前主交易流程為準；若調整上限，應先確認對 sizing 與風險閥值的影響。
