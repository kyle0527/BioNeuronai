# BioNeuronAI 啟動方式差異

> **套件版本**：v2.1  
> **更新日期**：2026-07-11  
> **方向權威**：[`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md)  
> **現況權威**：[`PROJECT_STATUS.md`](PROJECT_STATUS.md)  
> **目的**：釐清 CLI、API、UI、Docker 四種**操作入口**，以及 `trade`／`autonomous` 兩條**執行主線**的差異與預設用途。

---

## 目錄

1. [四種操作入口](#1-四種操作入口)
   - [1.1 CLI](#11-cli)
   - [1.2 API](#12-api)
   - [1.3 UI](#13-ui)
   - [1.4 Docker](#14-docker)
2. [建議使用順序](#2-建議使用順序)
3. [雙執行主線（必讀）](#3-雙執行主線必讀)
4. [主線 B：`autonomous`（預設 AI 自主）](#4-主線-bautonomous預設-ai-自主)
   - [4.1 單輪](#41-單輪預設-cycles1)
   - [4.2 持續閉環](#42-持續閉環工程自主主路徑)
   - [4.3 執行與學習](#43-執行與學習現行實作要點)
   - [4.4 與訓練的關係](#44-與訓練的關係)
5. [主線 A：`trade`（即時 tick）](#5-主線-atrade即時-tick)
   - [5.1 啟動方式](#51-啟動方式)
   - [5.2 Tick 管線](#52-tick-管線摘要)
   - [5.3 信心度與新聞護欄](#53-信心度與新聞護欄)
6. [模式對照與注意事項](#6-模式對照與注意事項)
7. [驗證時請用哪條](#7-驗證時請用哪條)
8. [修訂紀錄](#修訂紀錄)

---

## 1. 四種操作入口

### 1.1 CLI

最直接的單次／長跑任務入口：

```powershell
python main.py <command>
```

適合：`status`、資料盤點、pretrade、plan、news、backtest、simulate、readiness-gate、chat、**autonomous**、**trade**（paper-live／testnet／live）。

- 不需常駐服務即可驗證單一功能是否跑完。  
- 產物寫入 `backtest/runtime/`、`output/`、ledger／memory 等（見 [`manuals/16_RUNTIME_ARTIFACTS.md`](manuals/16_RUNTIME_ARTIFACTS.md)），屬 runtime，不納入 Git 進度幻想。  
- **本階段正式驗證以本機 Python 3.13 + CLI 為主。**

### 1.2 API

FastAPI 長時間服務：

```powershell
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

負責 UI、Swagger、部分交易控制。**目前** API 未完整覆蓋 `autonomous` 閉環；後續唯一產品面板會改以專屬 runtime API 啟動／停止 `AutonomousOperator`，但該 API 尚未實作——以 [`manuals/05_API_USER_MANUAL.md`](manuals/05_API_USER_MANUAL.md) 為準。

### 1.3 UI

目前主線前端是 `frontend/devops-d`：

```powershell
cd frontend/devops-d
npm run dev
```

UI 不直接執行核心 AI／下單邏輯；一律經 API。Docker 前端常為 `http://localhost:3000`；本機 Vite 常為 `5173`（占用時遞增）。

已決定的產品目標是「手動開啟一個程式 → 一個面板 → 一條自主 runtime」：未來 `frontend/app` 取代多面板入口，並由啟動器管理本機程序；在完成前，不能把現有 UI 說成已可啟動完整 autonomous runtime。

### 1.4 Docker

```powershell
docker compose up api frontend
docker compose run --rm status
```

適合部署與乾淨環境重現。**本階段不以 Docker 為唯一驗收入口**；待本機預設流程穩定後再重建 image。

---

## 2. 建議使用順序

| 情境 | 建議入口 |
|------|----------|
| 確認功能能不能跑 | **CLI** |
| **預設 AI 自主流程（目前）** | **CLI `autonomous`** |
| **預設 AI 自主流程（目標）** | 單一啟動器 + 單一產品面板；尚待實作與驗收 |
| 即時 tick／T0–T2 觀測 | CLI `trade --paper-live` |
| 長期大區間 | CLI：下載歷史 → backtest／readiness-gate |
| UI 監控 | API + UI |
| 部署重現 | Docker（本階段次要） |

方向提醒：先證明 **工程自主與記帳**，再談訓練績效；**不要**用 pytest 代替上表。

---

## 3. 雙執行主線（必讀）

兩條路徑**控制方式不同**，但現役目標是 **共用模型與 paper 執行層**：

| 維度 | 主線 A：`trade` | 主線 B：`autonomous` |
|------|-----------------|----------------------|
| 定位 | 即時 WebSocket 監控 | **預設 AI 自主長跑** |
| 驅動 | 每 tick | `run_forever` 定時輪 |
| 模型 | shared `unified_v2_100m` | **同一** shared |
| Paper | 引擎內 | 委派 `execute_prepared_order` |
| 學習 | T0–T2 → Memory → LoRA／Hub | ledger + shared 平倉回調進引擎學習鏈 |
| 審計 | ActionRecord 等 | **Decision Ledger** 為主 |

**禁止混用驗收標籤**：例如用 A 的 tick 日誌宣稱 B 的 planning 閉環已驗完。

---

## 4. 主線 B：`autonomous`（預設 AI 自主）

### 4.1 單輪（預設 cycles=1）

```powershell
python main.py autonomous --mode advisor --symbol BTCUSDT
python main.py autonomous --mode paper_auto --symbol BTCUSDT
```

- 一輪 observe → plan → pretrade → adapt（與 AI 決策依實作）→ 寫 ledger。  
- 預設結束，不長駐。  
- `advisor`：不執行訂單。  
- `paper_auto` 仍須 **`--execute-paper`** 才會送本機 paper 單。

### 4.2 持續閉環（工程自主主路徑）

```powershell
python main.py autonomous --mode paper_auto --execute-paper --cycles 10 --symbol BTCUSDT --paper-balance 10000
```

- `--cycles N` 且 N>1 → `run_forever`。  
- 每輪間隔依 adaptation；遇 STOP 可停機。  
- 可選：`--max-position-hold-cycles`、`--reflect-every` 等（以 `-h` 為準）。

### 4.3 執行與學習（現行實作要點）

- Paper connector 來自 **TradingEngine**（`paper_trading=True`）。  
- 下單：`execute_prepared_order`。  
- 平倉：`_on_shared_paper_close` → 引擎 `_on_paper_close`（T2／memory／LoRA／hub）+ autonomous ledger／calibrator。  
- quantity：優先 pretrade；無效則 fallback notional fraction。  
- 已有持倉：`skipped=existing_position`。

### 4.4 與「訓練」的關係

- 本階段驗收：**會跑、會記帳**。  
- 終局：同一自主流程上開啟／依賴在線改善。  
- 未訓練模型：可跑通工程；**不可**把盈虧當智能證明。

---

## 5. 主線 A：`trade`（即時 tick）

### 5.1 啟動方式

**CLI**

```powershell
python main.py trade --paper-live --paper-balance 10000
python main.py trade --symbol BTCUSDT --testnet
```

**程式**

```python
from bioneuronai.core.trading_engine import TradingEngine

engine = TradingEngine(
    testnet=True,
    paper_trading=True,
    enable_ai_model=True,
)
engine.load_ai_model("unified_v2_100m")
engine.enable_auto_trading()
engine.start_monitoring("BTCUSDT")
```

**API（若路由啟用）**

```http
POST /api/v1/trade/start
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "mode": "paper_live",
  "auto_trade": true
}
```

### 5.2 Tick 管線（摘要）

```text
WebSocket Tick
  → VirtualAccount 更新與 SL/TP
  → 新聞 event_context
  → StrategySelector + shared InferenceEngine
  → 融合與 auto_trade 閘門
  → 下單 [T1]；平倉 [T2] → Memory → LoRA → Hub
```

現役模型為 **unified v2**（可 `trained: false` 的確定性未訓練初始化），**不是**「仍走 v1 stub」。

### 5.3 信心度與新聞護欄

- `ai_min_confidence` 等門檻會過濾信號；未訓練時信心行為**不可**當產品績效。  
- 新聞重大負面等護欄可硬擋下單——屬設計，不是 silent bug。

---

## 6. 模式對照與注意事項

| 模式概念 | testnet | paper | auto | 說明 |
|----------|---------|-------|------|------|
| 只監控 | 可 | 可 | 否 | 只看信號 |
| paper_live | 否（主網行情） | 是 | 可 | 虛擬成交 |
| testnet_auto | 是 | 否 | 是 | 測試網真實單 |
| live | 否 | 否 | 是 | **真金**；需 guard 與 readiness |

注意：

- `--live` 與 `--paper-live` 不可同時使用（CLI 會擋）。  
- 進 live 前走 readiness-gate、固定區間回測、長時間 paper／testnet 觀察（見手冊 14）。  
- **多帳戶商用能力非本階段啟動需求。**

---

## 7. 驗證時請用哪條

| 要證明 | 用 |
|--------|-----|
| 預設 AI 自主跑通 | `autonomous` + paper 參數 + 多 cycles |
| Tick 融合與 T0–T2 | `trade --paper-live` |
| 長期區間 | 歷史資料 + backtest／gate |
| 單元測試全綠 | **不算**正式完成 |

完整哲學：[`TESTING_AND_VALIDATION_GUIDE.md`](TESTING_AND_VALIDATION_GUIDE.md)。

---

## 修訂紀錄

| 日期 | 說明 |
|------|------|
| 2026-06-15 | 雙主線與 B 線執行層 |
| 2026-07-11 | 對齊 CURRENT_DIRECTION：預設自主、shared 執行、驗證哲學、移除「B 無學習」暗示 |
