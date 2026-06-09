# BioNeuronAI 開機開始與關機手冊

> 版本：v2.1 正式主線 / v2.2 訓練後驗證期
> 建立日期：2026-05-02  
> 更新日期：2026-05-19
> 適用對象：第一次啟動、日常本地操作、API + Dashboard 操作、Docker 操作

---

## 📑 目錄

- [1. 開機前檢查](#1-開機前檢查)
- [2. 路線 A：只用 CLI 操作](#2-路線-a只用-cli-操作)
  - [2.1 查資料](#21-查資料)
  - [2.1A 跑一輪 autonomous 值班判斷](#21a-跑一輪-autonomous-值班判斷)
  - [2.2 跑短區間模擬](#22-跑短區間模擬)
  - [2.3 跑短區間回測](#23-跑短區間回測)
- [3. 路線 B：本地 API + Dashboard](#3-路線-b本地-api-dashboard)
  - [3.1 啟動 API](#31-啟動-api)
  - [3.2 啟動 Dashboard](#32-啟動-dashboard)
  - [3.3 關閉本地 API + Dashboard](#33-關閉本地-api-dashboard)
- [4. 路線 C：Docker API + Dashboard](#4-路線-cdocker-api-dashboard)
  - [4.1 建置](#41-建置)
  - [4.2 啟動核心服務](#42-啟動核心服務)
  - [4.3 跑 Docker CLI 任務](#43-跑-docker-cli-任務)
  - [4.4 關閉 Docker](#44-關閉-docker)
- [5. Testnet 交易開機](#5-testnet-交易開機)
- [6. Live 交易前禁止跳過的檢查](#6-live-交易前禁止跳過的檢查)
- [7. 常見關機與清理](#7-常見關機與清理)
  - [停止本地 uvicorn](#停止本地-uvicorn)
  - [停止卡住的 uvicorn 程序](#停止卡住的-uvicorn-程序)
  - [停止 Docker](#停止-docker)
  - [檢查 Git 狀態](#檢查-git-狀態)
- [8. 與其他手冊的關係](#8-與其他手冊的關係)

---

## 1. 開機前檢查

### 1.1 四種啟動入口的差異

| 入口 | 指令 | 使用情境 | 注意事項 |
|---|---|---|---|
| CLI | `python main.py <command>` | 單次任務、回測、simulate、paper-live、readiness gate、chat | 不需要常駐服務，最適合確認單一功能是否實際跑完 |
| API | `python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000` | UI 後端、外部自動化、Swagger 操作 | UI 的所有資料都依賴 API；API 未啟動會導致 `Failed to fetch` |
| UI | `cd frontend/devops-d; npm run dev` | Operations Dashboard 人工操作與監控 | UI 不直接執行 AI；它透過 API 呼叫後端 |
| Docker | `docker compose up api frontend` / `docker compose run --rm status` | 部署、重現環境、隔離依賴 | 本輪先不作主要驗證；本機功能收斂後最後重建 image |

更完整說明見 [../STARTUP_MODES.md](../STARTUP_MODES.md)。

請先在專案根目錄確認本機全域 Python 3.13 與依賴：

```powershell
cd C:\D\E\BioNeuronai
python --version
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchvision==0.23.0+cpu torchaudio==2.8.0+cpu
python -m pip install -e .
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

本專案目前不使用專案內虛擬環境；第一次安裝成功後，後續啟動只需要檢查，不需要每次重新設定。PyTorch 2.8.0+cpu 是目前 Windows 本機已確認可 import 的 CPU 組合。

接著執行：

```powershell
python main.py --help
python main.py status
```

成功標準：

- `--help` 能列出 `status`、`news`、`plan`、`pretrade`、`simulate`、`backtest`、`trade`、`chat` 等命令。
- `status` 顯示核心模組為 `[OK]`，API `/api/v1/status` 對應回傳 `ready: true`、`blocking: []`。

如果要使用 Binance、pretrade、testnet 或 live trading，請先確認 `.env`：

```powershell
Copy-Item .env.example .env
```

必要欄位：

```dotenv
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5176,http://127.0.0.1:5173,http://127.0.0.1:5176
```

---

## 2. 路線 A：只用 CLI 操作

這是最輕量的開機方式，不需要啟動長時間服務。

### 2.1 查資料

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

成功標準：能列出本地可用資料區間。

### 2.1A 跑一輪 autonomous 值班判斷

如果今天的目標是先看系統會不會建議進一步操作，而不是直接啟動長時間監控：

```powershell
python main.py autonomous --mode advisor --symbol BTCUSDT --output output\autonomous_advisor.json
```

成功標準：

- 顯示 `candidates`、`plan_status`、`final_action`
- 結果成功寫入 `output\autonomous_advisor.json`
- 若 `final_action=advise_only` 或 `Pretrade=WAIT`，代表今天這輪先停在觀察

### 2.2 跑短區間模擬

```powershell
python main.py simulate `
  --symbol BTCUSDT `
  --interval 1h `
  --bars 20 `
  --balance 10000 `
  --start-date 2020-01-01 `
  --end-date 2020-01-03
```

成功標準：

- CLI 印出最終餘額、PnL、Run ID。
- `backtest/runtime/<run_id>/` 產生 runtime 目錄。

### 2.3 跑短區間回測

```powershell
python main.py backtest `
  --symbol BTCUSDT `
  --interval 1h `
  --start-date 2020-01-01 `
  --end-date 2020-01-03 `
  --balance 10000 `
  --warmup-bars 10
```

成功標準：

- CLI 印出總報酬率、夏普比率、最大回撤、勝率、交易次數。
- `backtest/runtime/<run_id>/` 產生 runtime 目錄。

---

## 3. 路線 B：本地 API + Dashboard

這是建議的日常操作路線。

### 3.1 啟動 API

在專案根目錄：

```powershell
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

另開一個 PowerShell 驗證：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/status"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/backtest/catalog?symbol=BTCUSDT&interval=1h"
```

成功標準：

- `/api/v1/status` 回傳 `ready: true`、`blocking: []`。
- `/api/v1/backtest/catalog` 回傳 `success: true` 並列出 dataset。

### 3.2 啟動 Dashboard

另開 PowerShell：

```powershell
cd C:\D\E\BioNeuronai\frontend\devops-d
npm run dev
```

瀏覽器開啟：

```text
http://localhost:5173
```

如果 Vite 顯示 5173 已被占用，會自動改用 5174、5175、5176 等下一個 port；此時以終端輸出的 URL 為準，並確認 `.env` 的 `ALLOWED_ORIGINS` 包含該 origin。

成功標準：

- Dashboard 可開啟。
- Status 面板能取得後端狀態。
- API Playground 可呼叫 `/api/v1/status`。

### 3.3 關閉本地 API + Dashboard

- 在 API 終端按 `Ctrl+C`。
- 在 Dashboard 終端按 `Ctrl+C`。
- 若需要確認沒有殘留：

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn*bioneuronai.api.app*' } |
  Select-Object ProcessId, CommandLine
```

---

## 4. 路線 C：Docker API + Dashboard

本輪調整期間先不使用 Docker 作為主要驗證入口。Docker image 會在本機自然語言、交易判斷、API/UI readiness 與文件收斂後最後重建；以下流程保留給後續部署或乾淨環境複驗。

### 4.1 建置

```powershell
docker compose build
```

### 4.2 啟動核心服務

```powershell
docker compose up api frontend
```

或背景執行：

```powershell
docker compose up -d api frontend
```

成功標準：

```powershell
docker compose ps
```

應看到 `api` 與 `frontend` 為 running / healthy。

瀏覽器：

```text
http://localhost:3000
http://localhost:8000/docs
```

### 4.3 跑 Docker CLI 任務

```powershell
docker compose run --rm status
docker compose run --rm simulate
docker compose run --rm backtest
```

成功標準：CLI 容器執行後正常退出，並印出結果。

### 4.4 關閉 Docker

```powershell
docker compose down
```

不要在一般情況使用：

```powershell
docker compose down -v
```

因為 `-v` 會刪除 volume，可能清掉資料。

---

## 5. Testnet 交易開機

> 這一段只適用測試網，不代表可直接實盤。

確認 `.env`：

```dotenv
BINANCE_TESTNET=true
```

啟動：

```powershell
python main.py trade --symbol BTCUSDT --testnet
```

成功標準：

- TradingEngine 初始化。
- 能讀取即時價格或進入監控。
- 可用 `Ctrl+C` 停止。

若是 API 控制：

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

---

## 6. Live 交易前禁止跳過的檢查

實盤前必須完成：

1. Level 0 到 Level 2 手冊驗收全部通過。
2. Testnet 可啟動、可停止、沒有殘留背景程序。
3. `pretrade` 能明確給出 PROCEED / CAUTION / REJECT。
4. 已確認最大單筆風險、最大槓桿、最大回撤限制。
5. 已跑指定長區間 OOS / walk-forward 回測。
6. 人工確認 `.env` 使用正式網金鑰與正確 `BINANCE_TESTNET=false`。
7. 若走 API / UI live 自動交易路線，後端必須設定 `ALLOW_LIVE_TRADING=1`，且請求必須提供 `confirm_live=I_UNDERSTAND_LIVE_RISK`。

實盤啟動：

```powershell
python main.py trade --symbol BTCUSDT --live
```

CLI 路線會要求輸入 `YES` 進行二次確認；API / UI 路線則由 `ALLOW_LIVE_TRADING=1` 與 `confirm_live=I_UNDERSTAND_LIVE_RISK` 雙重限制。

---

## 7. 常見關機與清理

### 停止本地 uvicorn

在啟動終端按：

```text
Ctrl+C
```

### 停止卡住的 uvicorn 程序

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn*bioneuronai.api.app*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

### 停止 Docker

```powershell
docker compose down
```

### 檢查 Git 狀態

實際操作可能產生 runtime 或更新資料庫。驗收後請檢查：

```powershell
git status --short
```

若出現 runtime、logs、DB 類變更，應判斷它是驗收產物還是應提交的文件/程式變更。

---

## 8. 與其他手冊的關係

| 想做的事 | 下一份手冊 |
|---|---|
| 看完整 CLI 操作 | `docs/manuals/04_CLI_OPERATION.md` |
| 看 API 端點 | `docs/manuals/05_API_USER_MANUAL.md` |
| 操作 Dashboard | `docs/manuals/06_FRONTEND_DASHBOARD.md` |
| 用 Docker 部署 | `docs/manuals/07_DOCKER_DEPLOYMENT.md` |
| 跑回測 | `docs/manuals/08_BACKTEST_SYSTEM.md` |
| 跑策略比較 | `docs/manuals/10_STRATEGY_MODULE.md` |
| 做新聞、計畫、pretrade | `docs/manuals/09_ANALYSIS_MODULE.md` |
| 看整體驗收矩陣 | `docs/manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md` |
