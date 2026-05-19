# BioNeuronai 操作手冊
**版本**：v2.1 正式主線 / v2.2 訓練後驗證期
**更新日期**：2026-05-19
**適用對象**：初次使用者 / 日常操作參考

---

## 📑 目錄

- [1. 系統概述](#1-系統概述)
  - [核心能力](#核心能力)
- [2. 安裝與環境設定](#2-安裝與環境設定)
  - [前置需求](#前置需求)
  - [安裝步驟](#安裝步驟)
- [3. Binance API 金鑰設定](#3-binance-api-金鑰設定)
- [4. CLI 命令完整參考](#4-cli-命令完整參考)
  - [status](#status)
  - [plan](#plan)
  - [pretrade](#pretrade)
  - [news](#news)
  - [simulate](#simulate)
  - [backtest](#backtest)
  - [backtest-data](#backtest-data)
  - [backtest-runs](#backtest-runs)
  - [strategy-backtest](#strategy-backtest)
  - [readiness-gate](#readiness-gate)
  - [collect-signal-data](#collect-signal-data)
  - [evolve](#evolve)
  - [trade](#trade)
  - [chat](#chat)
- [5. 設定檔與資料契約說明](#5-設定檔與資料契約說明)
  - [Data Schemas (src/schemas/)](#data-schemas-srcschemas)
  - [傳統 Config (config/trading_config.py)](#傳統-config-configtradingconfigpy)
- [6. 標準操作流程 (SOP)](#6-標準操作流程-sop)
- [7. 常見問題排查](#7-常見問題排查)
  - [ModuleNotFoundError: No module named 'bioneuronai'](#modulenotfounderror-no-module-named-bioneuronai)
  - [Pydantic 模型驗證失敗](#pydantic-模型驗證失敗)
- [8. 風險警示](#8-風險警示)

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
| 系統健康檢查 | 診斷所有模組與 runtime readiness | ✅ | ✗ | `cli/` |
| 每日交易計劃 | 10 步驟 SOP (總經理視角) | ✗ | 部分步驟 | `planning/` |
| 進場前驗核 | 技術 / 基本面三重確認 (交易員視角) | ✗ | ✅ | `planning/` |
| 新聞分析 | 情緒與事件提取 | ✗ | ✗ | `rag/` & `analysis/news` |
| 紙交易模擬 | 在未連線 Binance 情況下驗證主交易邏輯 | ⚠️ 可選 | ✗ | `core/` & `backtest/` |
| 測試網/實盤交易入口 | 透過 Binance connector 進行即時監控；自動送單需依交易引擎模式與安全限制啟用 | ✅ | ✅ | `core/` & `trading/` |
| AI 對話助理 | 雙語交易知識問答（中 / 英），可注入即時市場資料 | ✅ | ✗ | `nlp/chat_engine` |

---

## 2. 安裝與環境設定

### 前置需求
- Python **3.13**（本機全域 runtime）。本專案目前不使用專案內虛擬環境。

### 安裝步驟

```bash
git clone https://github.com/BioNeuronai/BioNeuronai.git
cd BioNeuronai
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchvision==0.23.0+cpu torchaudio==2.8.0+cpu
python -m pip install -e .

# 選填：額外安裝強化學習模組
pip install -e ".[rl]"
```

若 `torch`、現役交易模型、TinyLLM 聊天模型或必要設定缺失，`status` 應直接回報阻擋項目；目前不把缺失狀態降級成可操作狀態。

---

## 3. Binance API 金鑰設定

目前建議以**環境變數與動態載入**為主，不建議直接把金鑰寫死在 `config/` 中的 `.py` 檔內。

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
> - 📊 [分析模組操作手冊 (09_ANALYSIS_MODULE.md)](09_ANALYSIS_MODULE.md)：涵蓋 `news`, `plan`, `pretrade`。
> - ⚔️ [策略模組操作手冊 (10_STRATEGY_MODULE.md)](10_STRATEGY_MODULE.md)：涵蓋 `strategy-backtest` 等競技場指令。

### `plan`
**依賴子系統**：`planning/plan_controller.py`
**用途**：產出 10 步驟高階分析。
```powershell
python main.py plan
python main.py plan --output reports/plan.json
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

### `backtest`
**依賴子系統**：`backtest/backtest_engine.py`
**用途**：以本地歷史 K 線執行完整策略回測，輸出統計指標與回測 runtime。
```bash
python main.py backtest --symbol BTCUSDT --interval 1h --start-date 2020-01-01 --end-date 2020-01-03
python main.py backtest --symbol ETHUSDT --balance 10000
```
詳細說明請參閱 [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)。

### `backtest-data`
**用途**：列出本地可用的歷史資料（OHLCV）資產與時間範圍。
```bash
python main.py backtest-data
python main.py backtest-data --symbol BTCUSDT --interval 1h
python main.py backtest-data --json           # JSON 輸出
```

### `backtest-runs`
**用途**：列出或查詢已執行的回測結果記錄（replay runtime）。
```bash
python main.py backtest-runs                  # 最近 10 筆
python main.py backtest-runs --limit 20
python main.py backtest-runs --run-id 20260428_132540_50707287  # 詳細資料
python main.py backtest-runs --json           # JSON 輸出
```

### `strategy-backtest`
**用途**：執行策略競技場（多策略模板競爭回測），支援 walk-forward 驗證、手續費 / 滑點設定。
> 完整說明（含 `--walk-forward`、`--execution-mode`、`--commission-bps`、`--params` 等進階參數）請參閱 [10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md)。

### `readiness-gate`
**用途**：正式交易前的 BTCUSDT / ETHUSDT 多時間框架 gate。它使用 `backtest/` replay service 實際跑策略矩陣，並依 `config/trading_readiness_gate.json` 的資料覆蓋、Walk-Forward 與績效門檻輸出 `PASS` / `FAIL`。這個命令不會送出真實訂單。
```bash
python main.py readiness-gate --dry-run
python main.py readiness-gate --output output/readiness_gate.json
python main.py readiness-gate --symbols BTCUSDT --intervals 1h --start-date 2020-01-01 --end-date 2020-03-31
```
若缺少設定矩陣中的資料（例如 `4h` K 線尚未下載），`--dry-run` 會直接列出缺失項；完整執行時未達門檻會以非 0 exit code 阻擋後續上線。

### `collect-signal-data`
**用途**：從本地歷史 K 線產生訊號訓練樣本，輸出為 JSONL 檔供後續模型訓練使用。
```bash
python main.py collect-signal-data
python main.py collect-signal-data --symbol BTCUSDT --interval 1h --output data/signal_history.jsonl
```
詳細說明請參閱 [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md)。

### `evolve`
**用途**：對策略參數執行遺傳演算法優化，找出最優策略設定。
```bash
python main.py evolve --symbol BTCUSDT
python main.py evolve --symbol BTCUSDT --interval 1h --generations 20 --population 30
python main.py evolve --output output/best_strategy.json
```

### `trade`
**依賴子系統**：`core/trading_engine.py` 與 connector / 帳戶狀態層  
**用途**：進行 monitor、paper-live、測試網或實盤監控 / 交易入口。AI 模型預設載入；如需關閉需明確加 `--no-ai-model`。
```bash
python main.py trade --testnet
python main.py trade --paper-live --paper-balance 10000
python main.py trade --live
```
`--paper-live` 使用 Binance mainnet 行情，但訂單只寫入本地虛擬帳戶，不送出真實 Binance order。使用 `--live` 時系統會有強制二次確認，避免意外進入實盤。若要從 Dashboard / API 啟用自動交易，請使用 `paper_live`、`testnet_auto` 或 `live_auto` 模式並確認 `/api/v1/trade/status`。

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
- 若模型未載入，預設報錯並停止；需明確加上 `--allow-rule-based-fallback` 才會進入開發用規則模式
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
4. **啟動回放、paper-live 或測試網觀測** (`backtest` / `simulate` / `trade --paper-live` / `trade --testnet`)。
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
