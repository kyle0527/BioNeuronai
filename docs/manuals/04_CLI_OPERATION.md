# BioNeuronai CLI 操作手冊

**套件版本**：v2.1（`pyproject.toml`）  
**更新日期**：2026-07-11  
**適用對象**：初次使用者／日常操作／工程自主驗收  
**方向權威**：[`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)  
**現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)

---

## 目錄

1. [系統概述](#1-系統概述)
2. [現行方向與雙執行主線（必讀）](#2-現行方向與雙執行主線必讀)
   - [2.1 優先級](#21-優先級操作者必讀)
   - [2.2 雙入口對照](#22-雙入口對照)
3. [安裝與環境設定](#3-安裝與環境設定)
4. [Binance API 金鑰設定](#4-binance-api-金鑰設定)
5. [CLI 命令參考](#5-cli-命令參考)
   - [status / plan / pretrade / news](#status)
   - [backtest 系列](#backtest--backtest-data--backtest-runs)
   - [trade（主線 A）](#trade主線-a)
   - [autonomous（主線 B）](#autonomous主線-b)
   - [reflect / chat](#reflect)
6. [產出物與驗收路徑](#6-產出物與驗收路徑)
7. [標準操作流程 (SOP)](#7-標準操作流程-sop)
8. [常見問題排查](#8-常見問題排查)
9. [風險警示](#9-風險警示)
10. [相關文件](#10-相關文件)

---

## 1. 系統概述

BioNeuronai 是加密貨幣期貨交易系統，模組分工如下：

| 模組 | 職責 |
|------|------|
| `planning/` | 交易計畫、盤前檢查、自主迴圈 |
| `core/` | TradingEngine、InferenceEngine、AdaptiveHub |
| `strategies/` | 策略選擇、fusion、Meta-Learner |
| `trading/` | VirtualAccount、成交事實 |
| `risk_management/` | RiskManager + AIConfidenceCalibrator |
| `backtest/` | 歷史 replay / 回測 |

### 核心能力速查

| 功能 | CLI 入口 | 需要 torch | 需要 API 金鑰 | 主責模組 |
|------|----------|:----------:|:------------:|----------|
| 系統健康檢查 | `status` | ✅ | ✗ | `cli/` |
| 每日交易計畫 | `plan` | ✗ | 部分 | `planning/` |
| 盤前驗核 | `pretrade` | ✗ | ✅ | `planning/` |
| 自主值班 | `autonomous` | ✗ | 部分 | `planning/` |
| AI 反思 / 校準 refit | `reflect` | ✗ | ✗ | `planning/` |
| 即時交易 / paper | `trade` | ✅ | paper-live 僅行情 | `core/` |
| 新聞分析 | `news` | ✗ | ✗ | `analysis/` + `rag/` |
| 回測 | `backtest` 等 | ⚠️ 視模式 | ✗ | `backtest/` |
| AI 對話 | `chat` | ✅ | ✗ | `nlp/` |

---

## 2. 現行方向與雙執行主線（必讀）

### 2.1 優先級（操作者必讀）

| 順序 | 目標 | CLI 重心 |
|:----:|------|----------|
| 1 | **工程自主**：預設流程跑通、記帳正確 | `autonomous` paper + cycles |
| 2 | 穩定長跑／重啟 | 同上 + 抽查產物 |
| 3 | 訓練改善 | 訓練 runbook + 再開滿在線學習 |
| 終局 | 自主時直接改善 | paper 平倉 → Hub／LoRA |

- **日常驗證**：虛擬帳戶／Paper 真實操作。  
- **長期**：先下載歷史 → `backtest`／`readiness-gate`。  
- **不要**用 `tests/` pytest 當「已驗收」。  
- **多帳戶／認證**：非本階段操作目標。  
- **未訓練模型**：可跑流程；勿用盈虧宣稱智能。

詳見 [`CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)、[`TESTING_AND_VALIDATION_GUIDE.md`](../TESTING_AND_VALIDATION_GUIDE.md)。

### 2.2 雙入口對照

**控制方式不同，模型與 paper 執行應共用；不可混用驗收標籤。**

| 維度 | 主線 A：`trade` | 主線 B：`autonomous`（預設 AI 自主） |
|------|-----------------|--------------------------------------|
| 驅動 | WebSocket 即時 tick | 定時規劃（`run_forever`） |
| 典型用途 | tick 監控、T0–T2 觀測 | **自主長跑**、規劃閉環 |
| 模型 | shared `unified_v2_100m` | **同一** shared |
| Paper | 引擎內 | `execute_prepared_order` |
| ActionRecord T0/T1/T2 | ✅ | 平倉經 shared callback 進引擎鏈 |
| EpisodicMemory / LoRA | ✅ paper 平倉 | ✅ 經 `_on_shared_paper_close` |
| Decision Ledger | ❌ | ✅ JSONL |
| AdaptiveLearningHub | ✅ | ✅ |

**主線 B 執行層**：

- 真下單：`--mode paper_auto` **且** `--execute-paper`  
- quantity：優先 pretrade；無效 fallback `--paper-notional-fraction`  
- 已有持倉：`skipped=true`，`reason=existing_position`  
- 平倉回填 calibrator；卡單 `--max-position-hold-cycles`；反思 `--reflect-every`  
- 獨立反思：`python main.py reflect --sample-size 50`

---

## 3. 安裝與環境設定

### 前置需求

- Python **3.13**（專案 `requires-python` 鎖定 3.13）
- 本文件假設在 repo 根目錄執行 `python main.py ...`

### 安裝步驟

```bash
git clone https://github.com/kyle0527/BioNeuronai.git
cd BioNeuronai
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchvision==0.23.0+cpu torchaudio==2.8.0+cpu
python -m pip install -e .
```

> **注意**：`pyproject.toml` 目前**沒有** `[rl]` optional extra。歷史 RL 訓練（`training/rl_trainer.py`）使用主依賴內的 PyTorch，無需額外 `pip install -e ".[rl]"`。

安裝後執行：

```bash
python main.py status
```

---

## 4. Binance API 金鑰設定

建議使用環境變數，不要把金鑰寫死在程式碼。

```bash
cp .env.example .env
```

```ini
BINANCE_API_KEY=你的_API_KEY
BINANCE_API_SECRET=你的_SECRET
BINANCE_TESTNET=true
```

- `pretrade` / `trade --testnet` / `trade --live` 需要有效金鑰（依模式）
- `trade --paper-live` 使用主網行情，但**不送**真實訂單，金鑰需求較低（視 connector 實作）
- `autonomous --mode advisor` 主要用歷史 K 線 + pretrade，不一定需要金鑰，但 pretrade 內部可能嘗試連接器

---

## 5. CLI 命令參考

正式入口：repo 根目錄 `main.py` → `src/bioneuronai/cli/main.py`。

### `status`

```bash
python main.py status
```

檢查核心模組是否可 import。不作為交易績效驗收。

### `plan`

```bash
python main.py plan
python main.py plan --output reports/plan.json
```

產出 10 步驟交易計畫。詳見 [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md)。

### `pretrade`

```bash
python main.py pretrade --symbol BTCUSDT --action long
```

執行盤前檢查。終端機會輸出：
- 技術 / 基本面 / 風險評估
- **`[AI 信心校準]`**、**`[AI 雙層對齊]`**、**`[AI 動態倉位]`**（來自 `AIConfidenceCalibrator`）
- 最終 `order_parameters`（含調整後 `quantity`）

> pretrade 使用內部 `RiskCalculation` + calibrator，**不是**直接呼叫 `RiskManager.calculate_position_size()`。詳見 [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md)。

### `news`

```bash
python main.py news --symbol BTCUSDT --max-items 10
```

### `backtest` / `backtest-data` / `backtest-runs`

```bash
python main.py backtest --symbol BTCUSDT --interval 1h --start-date 2020-01-01 --end-date 2020-01-03
python main.py backtest-data --symbol BTCUSDT --interval 1h
python main.py backtest-runs --limit 10
```

詳見 [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)。

### `strategy-backtest` / `readiness-gate` / `collect-signal-data` / `evolve`

- `strategy-backtest`：多策略模板回測 → [10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md)
- `readiness-gate`：上線前 gate，`PASS` / `FAIL` 退出碼
- `collect-signal-data`：產生訓練用 JSONL
- `evolve`：遺傳演算法策略參數優化

### `trade`（主線 A）

```bash
# 監控 only（預設不下單）
python main.py trade --symbol BTCUSDT

# Paper-live：主網行情 + 本地虛擬成交 + 完整學習閉環
python main.py trade --paper-live --paper-balance 10000

# Testnet（需金鑰；需 --auto-trade 或 API 啟用才送單）
python main.py trade --testnet --auto-trade

# 實盤（強制二次確認）
python main.py trade --live
```

| 旗標 | 說明 |
|------|------|
| `--paper-live` | 啟用 paper 連接器並 `enable_auto_trading()` |
| `--paper-balance` | 虛擬初始餘額（預設 10000） |
| `--auto-trade` | testnet/mainnet 自動送單 |
| `--no-ai-model` | 不載入 AI 模型 |
| `--load-ai-model` / `--model-name` | 控制模型載入 |

**學習閉環僅在 paper-live（或 auto_trade 且實際成交）時完整運作**：平倉 → ActionRecord T2 → EpisodicMemory → LoRA（每 100 筆）。

### `autonomous`（主線 B）

```bash
# 單輪建議（預設，不送單）
python main.py autonomous --mode advisor --symbol BTCUSDT

# 輸出 JSON
python main.py autonomous --mode advisor --symbol BTCUSDT --output output/advisor.json

# Paper 執行（需明確 --execute-paper）
python main.py autonomous --mode paper_auto --symbol BTCUSDT --execute-paper --paper-balance 10000

# 持續閉環 N 輪（輪間隔由 adaptation 的 next_interval_minutes 決定）
python main.py autonomous --mode paper_auto --symbol BTCUSDT --execute-paper --cycles 24

# 每 10 輪觸發 reflection_loop（需主線 A 累積 EpisodicMemory）
python main.py autonomous --mode paper_auto --execute-paper --cycles 30 --reflect-every 10
```

#### `autonomous` 完整參數

| 參數 | 預設 | 說明 |
|------|------|------|
| `--mode` | `advisor` | `advisor` / `paper_auto` / `testnet_auto` / `live_guarded` |
| `--cycles` | `1` | `>1` 進入 `run_forever`；遇 `STOP` 自動停機 |
| `--symbol` | `BTCUSDT` | 主交易對 |
| `--action` | `BUY` | pretrade 方向（支援 LONG/SHORT 別名） |
| `--interval` | `1h` | 載入 K 線週期 |
| `--balance` | `10000` | 計畫用帳戶餘額 |
| `--klines-limit` | `300` | K 線數量 |
| `--max-pairs` | `3` | pretrade 候選交易對上限 |
| `--data-dir` | 自動 | 歷史資料根目錄 |
| `--ledger-path` | 見 §6 | 自訂 decision ledger 路徑 |
| `--output` | — | 輸出本輪 JSON |
| `--execute-paper` | false | **僅** `paper_auto` 且 adaptation 允許時送 paper 單 |
| `--paper-balance` | `10000` | paper 初始餘額 |
| `--paper-notional-fraction` | `0.01` | quantity 無效時 fallback：餘額 × 比例 × risk_multiplier |
| `--max-position-hold-cycles` | `0` | 持倉超過 N 輪自動 reduce-only 平倉（0=停用） |
| `--reflect-every` | `0` | `run_forever` 每 N 輪執行 reflection_loop（0=停用） |
| `--reflection-sample-size` | `50` | reflection 抽樣 EpisodicMemory 筆數 |

#### 終端機輸出欄位（與程式一致）

- `candidates`、`plan_status`、`plan_execution_ready`
- `final_action`、`can_execute`、`risk_multiplier`、`confidence_floor`
- `next_interval_minutes`、`reasons`
- `pretrade_summary`（每 symbol 的 status / score）
- `paper_execution`（symbol、side、qty、`quantity_source`、`skipped`、order status）

#### 模式說明

| mode | 行為 |
|------|------|
| `advisor` | 只輸出決策與 ledger，**不送單** |
| `paper_auto` | adaptation 允許且 `--execute-paper` 時送本機 paper 單 |
| `testnet_auto` | v1 標記候選，**不直接送 testnet 單** |
| `live_guarded` | 標記需人工確認，**不直接送 live 單** |

### `reflect`

```bash
python main.py reflect --sample-size 50
python main.py reflect --sample-size 50 --json
```

對 EpisodicMemory 熱緩衝抽樣，分析虧損特徵並嘗試 `refit_temperature()`。樣本來自主線 A（`trade --paper-live` 平倉寫入 memory）；主線 B 單獨運行時可能樣本不足。

### `chat`

```bash
python main.py chat --language zh --symbol BTCUSDT
```

輸入 `exit` / `quit` 結束。模型未載入時預設報錯；可加 `--allow-rule-based-fallback` 進入規則模式。

---

## 6. 產出物與驗收路徑

直接操作後，可用以下檔案驗收（**非 pytest**）：

| 路徑 | 產生時機 | 內容 |
|------|----------|------|
| `data/bioneuronai/planning/autonomous/decision_ledger.jsonl` | `autonomous` 每輪 | `autonomous_cycle` + `trade_outcome` + `reflection_cycle` |
| `data/bioneuronai/learning/adaptive_hub.json` | 平倉後 hub 更新 | 策略×幣對 EWMA 績效 |
| `data/bioneuronai/memory/` | paper 平倉（A 直接；B 經 shared callback） | EpisodicMemory |
| paper log 目錄 | `trade --paper-live` 或 autonomous paper | 虛擬成交紀錄 |

**驗收 autonomous 時建議檢查**：

1. ledger 最新一筆 `final_action` 與 `reasons` 是否合理  
2. 若有 `--execute-paper`：`paper_execution.quantity_source` 為 `pretrade_quantity` 或 `notional_fraction` fallback  
3. 平倉後 ledger 是否有 `trade_outcome`；帳戶餘額是否對得上  
4. 若開啟學習寫入：Hub／memory 是否有變化（未平倉或未達門檻則可能無）  
5. 若 `--reflect-every N`：ledger 是否有 `reflection_cycle`  

詳見 [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)。

---

## 7. 標準操作流程 (SOP)

### 本階段日常（工程自主優先）

1. `python main.py status`  
2. `python main.py pretrade --symbol BTCUSDT --action long`（可選）  
3. `python main.py autonomous --mode advisor --symbol BTCUSDT`  
4. **預設主路徑**：`python main.py autonomous --mode paper_auto --execute-paper --cycles N --paper-balance 10000`  
5. 對帳：ledger + paper 產物（[16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)）  
6. （可選）tick 觀測：`trade --paper-live`  
7. （長期）下載歷史後 `backtest`／`readiness-gate`  

### 不建議的順序

- 同時對同 symbol 無協調地跑 `trade --paper-live` 與 `autonomous --execute-paper`  
- 用 pytest 代替上述真實操作  
- 假設「B 線永遠不能觸發 LoRA／memory」——平倉應走 shared callback；無變化時先查是否真的平倉  

---

## 8. 常見問題排查

### `ModuleNotFoundError: No module named 'bioneuronai'`

請使用 repo 根目錄的 `python main.py`，不要直接 `python -m bioneuronai.cli.main`（除非已正確設定 PYTHONPATH）。

### `pip install -e ".[rl]"` 失敗

正常。目前 `pyproject.toml` 無 `[rl]` extra，請移除該步驟。

### autonomous 有 pretrade 建議但 paper 倉位不符

2026-06-15 起預設優先採 pretrade quantity。若 `quantity_source=notional_fraction`，表示 pretrade quantity 無效而 fallback；檢查 pretrade `order_parameters.quantity` 是否為 0 或缺失。

### `reflect` 回報樣本不足

正常：需要 EpisodicMemory 中有成交樣本。可先跑 `trade --paper-live` 或能真正平倉的 autonomous paper，累積後再 `reflect`。

### Pydantic 驗證失敗

自建腳本繞過 `schemas/` 時常見。請對照 `src/schemas/` 必填欄位。

---

## 9. 風險警示

1. `--testnet` 仍連外部測試網，非純本機模擬。
2. `--live` 有二次確認，但仍可能造成真實虧損。
3. `--paper-live` 不送 Binance 訂單，但會改變本地虛擬倉位與學習狀態。
4. `autonomous --execute-paper` 的風控規則來自 AdaptationController + pretrade，與 TradingEngine 路徑不同。

---

## 10. 相關文件

| 文件 | 說明 |
|------|------|
| [../PROJECT_STATUS.md](../PROJECT_STATUS.md) | 模組現況權威來源 |
| [../ARCHITECTURE_OVERVIEW.md](../ARCHITECTURE_OVERVIEW.md) | 雙主線架構圖 |
| [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md) | plan / pretrade / news 細節 |
| [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md) | RiskManager + calibrator |
| [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) | 回測 |
| [../TESTING_AND_VALIDATION_GUIDE.md](../TESTING_AND_VALIDATION_GUIDE.md) | 驗證哲學（正式入口，非 pytest） |