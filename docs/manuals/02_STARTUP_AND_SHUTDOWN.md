# BioNeuronai 開機與關機手冊

> **套件版本**：v2.1（`pyproject.toml`）
> **更新日期**：2026-06-15
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)
> **適用對象**：第一次啟動、日常本地操作、API + Dashboard、Docker

---

## 目錄

1. [開機前檢查](#1-開機前檢查)
2. [路線 A：只用 CLI](#2-路線-a只用-cli)
3. [路線 B：本地 API + Dashboard](#3-路線-b本地-api--dashboard)
4. [路線 C：Docker](#4-路線-cdocker)
5. [交易相關開機](#5-交易相關開機)
6. [Live 前禁止跳過的檢查](#6-live-前禁止跳過的檢查)
7. [關機與清理](#7-關機與清理)
8. [相關手冊](#8-相關手冊)

---

## 1. 開機前檢查

### 1.1 四種啟動入口（介面層）

本節的「路線 A/B/C」指**操作介面**，與下方 §1.2 的 `trade` / `autonomous` **執行主線**不同。

| 入口 | 指令 | 使用情境 | 注意事項 |
|------|------|----------|----------|
| CLI | `python main.py <command>` | 單次任務、回測、simulate、paper-live、readiness-gate、chat | 不需常駐服務；最適合確認單一功能是否跑完 |
| API | `python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000` | UI 後端、Swagger、外部自動化 | UI 依賴 API；未啟動會 `Failed to fetch` |
| UI | `cd frontend/devops-d; npm run dev` | Operations Dashboard | UI 不直接執行 AI；透過 API 呼叫後端 |
| Docker | `docker compose up api frontend` | 部署、重現環境 | 本輪非主要驗證入口；本機收斂後再重建 image |

更完整說明見 [../STARTUP_MODES.md](../STARTUP_MODES.md)。

### 1.2 雙執行主線（交易層，必讀）

即使都用 CLI，**`trade` 與 `autonomous` 是兩條不同路徑**，學習閉環與產物不同：

| 維度 | 主線 A：`trade` | 主線 B：`autonomous` |
|------|----------------|----------------------|
| 典型指令 | `trade --paper-live` / `--testnet` / `--live` | `autonomous --mode advisor` / `paper_auto` |
| 執行核心 | `TradingEngine` + WebSocket | `AutonomousOperator` 規劃迴圈 |
| 長時間監控 | ✅ 預設用途 | 單輪預設；`--cycles N` 才持續迴圈 |
| LoRA / EpisodicMemory | ✅（paper-live 平倉） | ❌ |
| Decision Ledger | ❌ | ✅ `decision_ledger.jsonl` |

**開機建議順序**：`status` →（可選）`autonomous --mode advisor` → 再決定是否 `trade --paper-live`。詳見 [04_CLI_OPERATION.md](04_CLI_OPERATION.md) §2、§7。

### 1.3 環境與依賴

在 repo 根目錄確認 Python 3.13 與依賴：

```powershell
cd C:\D\E\BioNeuronai
python --version
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchvision==0.23.0+cpu torchaudio==2.8.0+cpu
python -m pip install -e .
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

本專案目前不使用專案內虛擬環境。`pyproject.toml` **沒有** `[rl]` optional extra；RL 訓練使用主依賴內 PyTorch，無需 `pip install -e ".[rl]"`。

接著執行：

```powershell
python main.py --help
python main.py status
```

成功標準：

- `--help` 列出 `status`、`news`、`plan`、`pretrade`、`autonomous`、`simulate`、`backtest`、`trade`、`readiness-gate`、`chat` 等命令。
- `status` 顯示核心模組 `[OK]`。
- 若 API 已啟動，`GET /api/v1/status` 應回傳 `ready: true`、`blocking: []`。

驗收層級定義見 [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md) §4（Level 0～4）。

### 1.4 環境變數

日常不接交易所時只保留 `.env.example`。要使用 Binance、pretrade、testnet 或 live 時：

```powershell
Copy-Item .env.example .env
```

常用欄位：

```dotenv
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5176,http://127.0.0.1:5173,http://127.0.0.1:5176
```

完整說明見 [17_ENVIRONMENT_VARIABLES.md](17_ENVIRONMENT_VARIABLES.md)。

---

## 2. 路線 A：只用 CLI

最輕量開機方式，不需啟動長時間服務。對應驗收 **Level 0**（§1.3 連結）。

### 2.1 查資料

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

成功標準：能列出本地可用資料區間。

### 2.2 Autonomous 單輪值班（主線 B）

目標是「先看系統建議」，而非啟動長時間監控：

```powershell
python main.py autonomous --mode advisor --symbol BTCUSDT --output output\autonomous_advisor.json
```

成功標準：

- 終端顯示 `candidates`、`plan_status`、`plan_execution_ready`、`final_action`、`reasons`
- 若有 pretrade 結果，終端印 **Pretrade** 區塊（JSON 欄位為 `pretrade_summary`）
- `output\autonomous_advisor.json` 寫入成功
- `data\bioneuronai\planning\autonomous\decision_ledger.jsonl` 追加一筆 `autonomous_cycle`

若 `final_action` 為 `advise_only` / `observe`，或 pretrade 顯示 `WAIT` / `REJECT`，本輪應停在觀察，**不要**把這當成已啟動 `TradingEngine`。

### 2.3 短區間模擬

```powershell
python main.py simulate `
  --symbol BTCUSDT `
  --interval 1h `
  --bars 20 `
  --balance 10000 `
  --start-date 2020-01-01 `
  --end-date 2020-01-03
```

成功標準：CLI 印出餘額、PnL、Run ID；`backtest/runtime/<run_id>/` 產生目錄。

### 2.4 短區間回測

```powershell
python main.py backtest `
  --symbol BTCUSDT `
  --interval 1h `
  --start-date 2020-01-01 `
  --end-date 2020-01-03 `
  --balance 10000 `
  --warmup-bars 10
```

成功標準：CLI 印出報酬率、夏普、回撤、勝率、交易次數；`backtest/runtime/<run_id>/` 產生目錄。

---

## 3. 路線 B：本地 API + Dashboard

建議的日常操作路線。對應驗收 **Level 1**。

### 3.1 啟動 API

```powershell
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

另開 PowerShell 驗證：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/status"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/backtest/catalog?symbol=BTCUSDT&interval=1h"
```

成功標準：`ready: true`、`blocking: []`；catalog 回傳 `success: true`。

### 3.2 啟動 Dashboard

```powershell
cd C:\D\E\BioNeuronai\frontend\devops-d
npm run dev
```

瀏覽器開啟終端輸出的 URL（通常 `http://localhost:5173`；port 被占用時可能為 5174～5176）。請確認 `.env` 的 `ALLOWED_ORIGINS` 包含實際 origin。

成功標準：Dashboard 可開啟；Status 面板能取得後端狀態；API Playground 可呼叫 `/api/v1/status`。

### 3.3 關閉

- API / Dashboard 終端各按 `Ctrl+C`
- 確認無殘留 uvicorn：

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn*bioneuronai.api.app*' } |
  Select-Object ProcessId, CommandLine
```

---

## 4. 路線 C：Docker

本輪非主要驗證入口；以下保留給部署或乾淨環境複驗。

### 4.1 建置與啟動

```powershell
docker compose build
docker compose up api frontend
# 或背景：docker compose up -d api frontend
```

成功標準：`docker compose ps` 顯示 `api`、`frontend` 為 running / healthy。

瀏覽器：`http://localhost:3000`、`http://localhost:8000/docs`

### 4.2 CLI 容器任務

```powershell
docker compose run --rm status
docker compose run --rm simulate
docker compose run --rm backtest
```

### 4.3 關閉

```powershell
docker compose down
```

不要使用 `docker compose down -v`（會刪除 volume）。

---

## 5. 交易相關開機

原則：**先 paper-live，再 testnet，最後 live**。完整細節見 [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md)。

### 5.1 Paper-live（主線 A，建議優先）

不需 testnet 金鑰即可驗證引擎與學習閉環（行情用 mainnet public data，下單只進本地虛擬帳戶）：

```powershell
python main.py trade --symbol BTCUSDT --paper-live --paper-balance 10000
```

成功標準：

- `TradingEngine` 初始化；`ai_model_loaded=true`
- log 目錄位於 `data/bioneuronai/trading/paper_live/`（啟動時 CLI 會印出）
- 可用 `Ctrl+C` 停止
- 平倉後可檢查 `data/bioneuronai/memory/`、`data/bioneuronai/learning/adaptive_hub.json`

### 5.2 Testnet（主線 A）

`.env` 設定 `BINANCE_TESTNET=true` 與 testnet 金鑰後：

```powershell
python main.py trade --symbol BTCUSDT --testnet
```

成功標準：引擎初始化、能讀取價格或進入監控、`Ctrl+C` 可停止。對應驗收 **Level 3**。

### 5.3 API 啟停交易（主線 A）

需先啟動 API（§3.1）：

```powershell
$body = @{
  symbol = "BTCUSDT"
  testnet = $true
  mode = "monitor_only"
  paper_initial_balance = 10000
  auto_trade = $false
  load_ai_model = $true
  model_name = "my_100m_model"
  warmup_model = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/trade/start" -Method POST -Body $body -ContentType "application/json"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/trade/status" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/trade/stop" -Method POST
```

Paper-live API 範例見 [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) §4。

> **注意**：`autonomous` 不經 `/api/v1/trade/start`；它是獨立的 CLI 規劃入口（主線 B）。

---

## 6. Live 前禁止跳過的檢查

實盤前必須完成（對應 [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md) Level 0～2 與 Level 4 前置）：

1. Level 0～2 手冊驗收通過（含短回測、API/UI、news/plan/pretrade）。
2. **Paper-live** 已連續運行並檢查本地 paper log 符合預期。
3. Testnet 可啟動、可停止、無殘留背景程序（Level 3）。
4. `pretrade` 能明確給出 PROCEED / CAUTION / REJECT。
5. 已確認最大單筆風險、槓桿、回撤限制（[11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md)）。
6. 已跑指定長區間 OOS / walk-forward 回測。
7. `.env` 使用正式網金鑰、`BINANCE_TESTNET=false`。
8. API / UI live 路線：`ALLOW_LIVE_TRADING=1` 且 `confirm_live=I_UNDERSTAND_LIVE_RISK`。

CLI live：

```powershell
python main.py trade --symbol BTCUSDT --live
```

CLI 會要求輸入 `YES` 二次確認。

---

## 7. 關機與清理

### 停止 CLI 交易 / autonomous

在執行終端按 `Ctrl+C`。

### 停止卡住的 uvicorn

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn*bioneuronai.api.app*' -or $_.CommandLine -like '*main.py trade*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

### 檢查 Git 狀態

```powershell
git status --short
```

runtime、ledger、logs 多為執行產物，見 [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)。

---

## 8. 相關手冊

| 想做的事 | 手冊 |
|----------|------|
| 快速開始 | [03_QUICKSTART.md](03_QUICKSTART.md) |
| 完整 CLI | [04_CLI_OPERATION.md](04_CLI_OPERATION.md) |
| API 端點 | [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md) |
| Dashboard | [06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md) |
| Docker | [07_DOCKER_DEPLOYMENT.md](07_DOCKER_DEPLOYMENT.md) |
| 回測 | [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) |
| news / plan / pretrade | [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md) |
| testnet / live / autonomous | [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) |
| 產物路徑 | [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md) |
| 驗收矩陣 | [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md) |