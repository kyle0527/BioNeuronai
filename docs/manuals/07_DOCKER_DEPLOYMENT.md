# BioNeuronai Docker 部署操作手冊

> **套件版本**：v2.1（`pyproject.toml`）
> **更新日期**：2026-06-15
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)
> **適用對象**：開發者、DevOps 工程師

---

## 📑 目錄

- [1. 概述](#1-概述)
- [2. 前置需求](#2-前置需求)
  - [必要軟體](#必要軟體)
  - [確認安裝](#確認安裝)
- [3. 環境變數設定](#3-環境變數設定)
- [4. 服務架構說明](#4-服務架構說明)
- [5. 常用部署指令](#5-常用部署指令)
  - [建置映像](#建置映像)
  - [啟動核心服務（API + Dashboard）](#啟動核心服務api-dashboard)
  - [啟動所有 CLI 工作服務](#啟動所有-cli-工作服務)
  - [啟動交易服務（需明確 profile）](#啟動交易服務需明確-profile)
  - [停止服務](#停止服務)
  - [查看服務狀態](#查看服務狀態)
- [6. 各服務詳細說明](#6-各服務詳細說明)
  - [api — REST API 伺服器](#api-rest-api-伺服器)
  - [frontend — React Dashboard](#frontend-react-dashboard)
  - [status — 系統健康檢查 CLI](#status-系統健康檢查-cli)
  - [news — 新聞分析 CLI](#news-新聞分析-cli)
  - [pretrade — 進場前驗核 CLI](#pretrade-進場前驗核-cli)
  - [plan — 交易計劃生成 CLI](#plan-交易計劃生成-cli)
  - [backtest — 完整回測 CLI](#backtest-完整回測-cli)
  - [simulate — Replay 模擬 CLI](#simulate-replay-模擬-cli)
  - [trade — 交易監控服務](#trade-交易監控服務)
- [7. Volume 資料持久化](#7-volume-資料持久化)
  - [查看 Volume 位置](#查看-volume-位置)
  - [備份資料](#備份資料)
  - [還原資料](#還原資料)
- [8. 健康檢查與監控](#8-健康檢查與監控)
  - [查看所有服務健康狀態](#查看所有服務健康狀態)
  - [健康檢查設定說明](#健康檢查設定說明)
  - [即時日誌監控](#即時日誌監控)
- [9. 映像建置說明](#9-映像建置說明)
  - [Dockerfile 結構](#dockerfile-結構)
  - [建置時間最佳化](#建置時間最佳化)
  - [前端 Build Args](#前端-build-args)
- [10. 更新部署流程](#10-更新部署流程)
- [11. 常見問題排除](#11-常見問題排除)
- [12. 安全考量](#12-安全考量)
- [相關文件](#相關文件)

---

## 1. 概述

BioNeuronai 使用 **Docker Compose** 管理預設 8 個服務；啟用 `trade` profile 後會額外加入第 9 個交易監控服務。服務分為三個類別：

| 類別 | 服務 | 說明 |
|---|---|---|
| **核心服務** | `api`, `frontend` | 長期運行，提供 HTTP 服務 |
| **CLI 工作服務** | `status`, `news`, `pretrade`, `plan`, `backtest`, `simulate` | 執行後退出；共用 `bioneuronai-api:latest` runtime image |
| **交易服務** | `trade` | 需 `--profile trade` 啟用；預設 testnet，可覆寫為 paper-live 或 live |

API 與 CLI 工作服務共用 `bioneuronai-api:latest`（由 `Dockerfile` 的 `runtime` 目標建置），透過不同的 `command` 分工；frontend 使用 `bioneuronai-frontend:latest`。

> **執行主線說明**：Compose 的 `trade` 服務對應主線 A（`TradingEngine`）。**沒有**獨立的 `autonomous` 服務；主線 B 請在本機或容器內執行 `python main.py autonomous ...`。本輪仍以本機 Python 3.13 為主要驗證入口，Docker 留待功能收斂後重建 image。

---

## 2. 前置需求

### 必要軟體

| 軟體 | 最低版本 | 說明 |
|---|---|---|
| Docker Desktop | 4.x | Windows/macOS 整合安裝包 |
| Docker Compose | v2.x | 隨 Docker Desktop 附帶，使用 `docker compose` 指令 |

> **注意**：本專案使用 `docker compose`（v2，無連字號），不相容舊版 `docker-compose`（v1）。

### 確認安裝
```powershell
docker --version
docker compose version
```

---

## 3. 環境變數設定

Docker 若要注入 API key、port 或交易模式設定，才在專案根目錄由 `.env.example` 建立 `.env`（不提交至 Git）。日常不接外部服務時可只保留 `.env.example`；`docker-compose.yml` 將 `.env` 設為 optional，讓 `docker compose config --quiet` 可在乾淨 checkout 上通過：

```dotenv
# ===== Binance API =====
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=false          # true=測試網, false=主網

# ===== 服務端口 =====
API_PORT=8000                  # API 伺服器對外端口
FRONTEND_PORT=3000             # 前端 Dashboard 端口

# ===== 交易設定 =====
TRADE_SYMBOL=BTCUSDT           # 即時交易的預設交易對
BACKTEST_SYMBOL=BTCUSDT        # 回測預設交易對
BACKTEST_INTERVAL=1h           # 回測 K 線粒度
BACKTEST_START=2020-01-01      # 回測開始日期
BACKTEST_END=2020-01-03        # 回測結束日期
BACKTEST_BALANCE=10000         # 回測初始資金
BACKTEST_WARMUP_BARS=10        # 回測預熱 K 線數量

# ===== 虛擬回測設定 =====
SIM_BALANCE=10000              # Simulate 虛擬初始資金 (USDT)
SIM_BARS=200                   # Simulate 使用幾根 K 線
SIM_START=2020-01-01           # Simulate 開始日期
SIM_END=2020-01-03             # Simulate 結束日期

# ===== CORS 設定 =====
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173

# ===== 選用 =====
CRYPTOPANIC_API_TOKEN=free     # CryptoPanic 新聞 API（免費方案可填 free）
VITE_API_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO                 # DEBUG / INFO / WARNING / ERROR
```

> **安全提醒**：`.env` 含有敏感 API 金鑰，確保已列入 `.gitignore`。

---

## 4. 服務架構說明

```
┌────────────────────────────────────────────────────────┐
│  docker-compose.yml                                    │
│                                                        │
│  ┌──────────┐  ┌─────────────┐                        │
│  │  api     │  │  frontend   │                        │
│  │ :8000    │  │  :3000      │                        │
│  │ FastAPI  │  │  nginx      │                        │
│  │          │  │  React SPA  │                        │
│  └──────────┘  └─────────────┘                        │
│       ↑                                               │
│  ┌────┼───────────────────────┐                       │
│  │    │  CLI 工作服務          │                       │
│  │  status / news / pretrade  │                       │
│  │  plan / backtest / simulate│                       │
│  └───────────────────────────┘                        │
│                                                        │
│  ┌─────────────────────────────┐                      │
│  │  trade  (--profile trade)   │                      │
│  │  restart: unless-stopped    │                      │
│  └─────────────────────────────┘                      │
│                                                        │
│  Volumes: bioneuron-data, bioneuron-logs              │
│  Bind:    ./backtest -> /app/backtest                 │
└────────────────────────────────────────────────────────┘
```

---

## 5. 常用部署指令

### 建置映像
```bash
docker compose build
```

重新建置特定服務：
```bash
docker compose build api
docker compose build frontend
```

### 啟動核心服務（API + Dashboard）
```bash
docker compose up api frontend
```

加上 `-d` 背景執行：
```bash
docker compose up -d api frontend
```

### 啟動所有 CLI 工作服務
```bash
# 依序執行各 CLI 任務
docker compose run --rm status
docker compose run --rm news
docker compose run --rm pretrade
docker compose run --rm plan
docker compose run --rm backtest
docker compose run --rm simulate
```

### 啟動交易服務（需明確 profile）
```bash
docker compose --profile trade up trade
```

> **警告**：`trade` 服務設定 `restart: unless-stopped`，一旦啟動會持續運行並重啟，直到明確 `docker compose stop trade`。

### 停止服務
```bash
# 停止特定服務
docker compose stop api
docker compose stop trade

# 停止所有服務
docker compose down

# 停止並刪除 volumes（⚠️ 會清除所有資料）
docker compose down -v
```

### 查看服務狀態
```bash
docker compose ps
docker compose logs -f api       # 即時查看 api 日誌
docker compose logs --tail=100 frontend
```

---

## 6. 各服務詳細說明

### api — REST API 伺服器

| 設定 | 值 |
|---|---|
| 映像 | 本地 build |
| 端口 | `${API_PORT:-8000}:8000` |
| 健康檢查 | `GET /api/v1/status`，30秒間隔 |
| 重啟策略 | `unless-stopped` |
| 環境變數 | 全部 `.env` 變數 |
| Volume | `bioneuron-data:/app/data`、`bioneuron-logs:/app/logs` |

```yaml
command: uvicorn bioneuronai.api.app:app --host 0.0.0.0 --port 8000
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/status')"]
  interval: 30s
  timeout: 5s
  retries: 3
```

---

### frontend — React Dashboard

| 設定 | 值 |
|---|---|
| 映像 | 本地 build（multi-stage，包含 nginx） |
| 端口 | `${FRONTEND_PORT:-3000}:80` |
| depends_on | `api` healthy |
| Build args | `${VITE_API_BASE_URL:-http://localhost:8000}` |

前端容器使用 multi-stage build：
1. `builder` 階段：Node.js 執行 `npm run build`
2. `runtime` 階段：nginx 服務靜態檔案，並代理 `/api/` 到 `api:8000`

若需更改 API URL（如從外部網路存取），調整 build arg：
```bash
docker compose build --build-arg VITE_API_BASE_URL=http://your-server-ip:8000 frontend
```

---

### status — 系統健康檢查 CLI

```bash
docker compose run --rm status
```
執行 `python main.py status`，輸出所有模組載入狀態後退出。

---

### news — 新聞分析 CLI

```bash
docker compose run --rm news
```
執行 `python main.py news --symbol ${TRADE_SYMBOL}`，輸出新聞分析結果後退出。

---

### pretrade — 進場前驗核 CLI

```bash
docker compose run --rm pretrade
```
執行 `python main.py pretrade --symbol ${TRADE_SYMBOL} --action ${TRADE_ACTION}`，輸出六點驗核結果後退出。

---

### plan — 交易計劃生成 CLI

```bash
docker compose run --rm plan
```
執行 `python main.py plan --symbol ${TRADE_SYMBOL}`，生成每日交易計劃後退出。

---

### backtest — 完整回測 CLI

```bash
docker compose run --rm backtest
```
執行 `python main.py backtest --symbol ${BACKTEST_SYMBOL} --interval ${BACKTEST_INTERVAL} --start-date ${BACKTEST_START} --end-date ${BACKTEST_END} --balance ${BACKTEST_BALANCE} --warmup-bars ${BACKTEST_WARMUP_BARS}`。

---

### simulate — Replay 模擬 CLI

```bash
docker compose run --rm simulate
```
執行 `python main.py simulate --symbol ${TRADE_SYMBOL} --interval ${BACKTEST_INTERVAL} --balance ${SIM_BALANCE} --bars ${SIM_BARS} --start-date ${SIM_START} --end-date ${SIM_END}`。

---

### trade — 交易監控服務

```bash
docker compose --profile trade up trade
```

| 設定 | 值 |
|---|---|
| Profile | `trade`（需明確啟用） |
| 重啟策略 | `unless-stopped` |
| 命令 | `python main.py trade --testnet` |

Paper-live 可用覆寫 command 的方式執行：

```bash
docker compose --profile trade run --rm trade main.py trade --paper-live --paper-balance 10000
```

此模式讀 Binance mainnet 行情，但只寫本地虛擬帳戶，不送出真實 Binance 訂單。

停止交易服務：
```bash
docker compose stop trade
# 或
docker compose --profile trade down trade
```

---

## 7. Volume 資料持久化

Docker Compose 定義兩個 named volume，並額外把本機 `./backtest` bind mount 到容器 `/app/backtest`。歷史 K 線資料不放進 image，而是透過這個 bind mount 供 API、backtest 與 simulate 共用。

| Volume | 容器掛載點 | 說明 |
|---|---|---|
| `bioneuron-data` | `/app/data` | SQLite 資料庫、歷史資料、Signal 紀錄 |
| `bioneuron-logs` | `/app/logs` | 所有服務的日誌檔案 |

| Bind mount | 容器掛載點 | 說明 |
|---|---|---|
| `./backtest` | `/app/backtest` | 回測程式、歷史 K 線、runtime 結果；API 的 `/api/v1/backtest/catalog` 也依賴此掛載 |

### 查看 Volume 位置
```bash
docker volume inspect bioneuron-data
docker volume inspect bioneuron-logs
```

### 備份資料
```powershell
# 備份 data volume
docker run --rm -v bioneuron-data:/data -v ${PWD}:/backup alpine `
  tar czf /backup/bioneuron-data-backup.tar.gz /data

# 備份 logs volume
docker run --rm -v bioneuron-logs:/logs -v ${PWD}:/backup alpine `
  tar czf /backup/bioneuron-logs-backup.tar.gz /logs
```

### 還原資料
```powershell
docker run --rm -v bioneuron-data:/data -v ${PWD}:/backup alpine `
  tar xzf /backup/bioneuron-data-backup.tar.gz -C /
```

> **注意**：執行 `docker compose down -v` 會**永久刪除** volumes 中的所有資料，包括 SQLite 資料庫和歷史交易紀錄。操作前務必先備份。

---

## 8. 健康檢查與監控

### 查看所有服務健康狀態
```powershell
docker compose ps
# 輸出範例:
# NAME                   STATUS
# bioneuron-api-1        Up 2 hours (healthy)
# bioneuron-frontend-1   Up 2 hours (healthy)
```

### 健康檢查設定說明

`api` 服務的健康檢查：
- `interval: 30s` — 每 30 秒執行一次
- `timeout: 10s` — 超過 10 秒無回應視為失敗
- `retries: 3` — 連續 3 次失敗才標為 unhealthy
- `start_period: 30s` — 啟動後 30 秒內不計入失敗次數

`frontend` 依賴 `api` 的 `service_healthy` 狀態才會啟動。

### 即時日誌監控
```bash
# 同時看多個服務的日誌
docker compose logs -f api frontend

# 只看最後 100 行
docker compose logs --tail=100 api
```

---

## 9. 映像建置說明

### Dockerfile 結構

```
Dockerfile
├── builder stage  — Python 3.11 slim，編譯 ta-lib 並安裝 Python 依賴
├── training stage — PyTorch CUDA image，供雲端/GPU 訓練時以 `--target training` 明確建置
└── runtime stage  — Python 3.11 slim，複製 src/config/backtest/model/main.py
```

### 建置時間最佳化

由於 pip 層已快取，一般程式碼修改後重新建置會重用依賴層。若修改了 `requirements-lock.txt`、`pyproject.toml`、Dockerfile 或模型檔，則需要重新建置對應 image。

```bash
# 強制完整重建（清除快取）
docker compose build --no-cache
```

### 前端 Build Args

| 變數 | 說明 | 預設值 |
|---|---|---|
| `VITE_API_BASE_URL` | 前端呼叫 API 的基礎 URL | `http://localhost:8000` |

若部署在遠端伺服器，必須修改此 build arg：
```bash
docker compose build --build-arg VITE_API_BASE_URL=http://192.168.1.100:8000 frontend
```

---

## 10. 更新部署流程

```bash
# 1. 拉取最新程式碼
git pull

# 2. 重新建置有 source 變更的映像
docker compose build api frontend

# 3. 滾動重啟（保留 volumes）
docker compose up -d api frontend

# 4. 確認服務健康
docker compose ps

# 5. 查看 API 是否正常
Invoke-RestMethod "http://localhost:8000/api/v1/status"
```

---

## 11. 常見問題排除

**問：`docker compose build` 失敗，提示 pip install 錯誤**
- 確認 Docker Desktop 已連接網路
- 嘗試 `docker compose build --no-cache` 清除快取

**問：`api` 服務啟動後狀態顯示 `starting` 超過 1 分鐘**
- 查看日誌：`docker compose logs api`
- 常見原因：Python import 錯誤（缺少依賴）
- 解決：`docker compose build --no-cache api`

**問：`frontend` 服務狀態 `waiting for api`**
- `frontend` 依賴 `api` healthy 後才啟動
- 若 `api` 健康檢查一直失敗，`frontend` 不會啟動

**問：volumes 中的資料庫損毀**
- 停止所有服務：`docker compose down`
- 還原備份，或刪除損毀的 db 文件：
  ```bash
  docker run --rm -v bioneuron-data:/data alpine rm /data/bioneuronai/trading/engine/trading.db
  ```
- 重啟 api，系統會自動重新初始化資料庫

**問：`trade` 服務自動重啟停不下來**
- 必須使用 `docker compose stop trade`，不是 `docker compose down`（down 只停止非 trade profile）
- 或加上 profile：`docker compose --profile trade down`

**問：port 8000 / 3000 被佔用**
- 修改 `.env` 中的 `API_PORT` / `FRONTEND_PORT`
- 重啟服務

---

## 12. 安全考量

| 項目 | 說明 |
|---|---|
| API 認證 | 目前 API 無認證，**僅限 localhost 或內部網路存取** |
| .env 保護 | 確認 `.env` 在 `.gitignore` 中，絕不提交至版本控制 |
| CORS 設定 | 透過 `ALLOWED_ORIGINS` 限制允許的前端來源 |
| 正式網金鑰 | 建議使用 read-only API 金鑰，僅在需要交易時使用 trading 權限 |
| BINANCE_TESTNET | 開發和測試階段設定 `true`，確認無誤後才改為 `false` |
| 外部網路部署 | 若需外部存取，必須加上 nginx reverse proxy + SSL + 認證層 |

---

## 相關文件

| 文件 | 說明 |
|---|---|
| [03_QUICKSTART.md](03_QUICKSTART.md) | 新手快速上手（含 Docker 入門） |
| [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md) | REST API 完整端點手冊 |
| [06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md) | 前端 Dashboard 操作手冊 |
| [04_CLI_OPERATION.md](04_CLI_OPERATION.md) | CLI 操作手冊（非 Docker 環境） |
