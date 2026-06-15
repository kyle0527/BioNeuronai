# Runtime 與輸出產物手冊

> **套件版本**：v2.1
> **更新日期**：2026-06-15
> **範圍**：使用者如何找到每次操作後產生的結果、log、runtime、模型與資料產物。
> **驗證方式**：直接檢查檔案與 CLI/API 輸出（**非 pytest**）。

---

## 目錄

1. [產物總覽（依執行主線）](#1-產物總覽依執行主線)
2. [自主決策與學習產物](#2-自主決策與學習產物)
3. [Paper 與交易執行產物](#3-paper-與交易執行產物)
4. [回測 runtime](#4-回測-runtime)
5. [模型與訓練資料](#5-模型與訓練資料)
6. [CLI `--output` 與 `output/`](#6-cli---output-與-output)
7. [API 查詢 runtime](#7-api-查詢-runtime)
8. [驗收對照表](#8-驗收對照表)
9. [Git 狀態排查](#9-git-狀態排查)
10. [保留與清理原則](#10-保留與清理原則)

---

## 1. 產物總覽（依執行主線）

兩條主線產生的**核心產物不同**，請勿混用驗收標準：

| 主線 | 入口 | 必查產物 | 不會產生 |
|------|------|----------|----------|
| A：`trade` | `trade --paper-live` 等 | `data/bioneuronai/trading/paper_live/`、`data/bioneuronai/memory/`、`data/bioneuronai/learning/adaptive_hub.json` | `decision_ledger.jsonl` |
| B：`autonomous` | `autonomous ...` | `data/bioneuronai/planning/autonomous/decision_ledger.jsonl`、`adaptive_hub.json`（平倉後） | EpisodicMemory / LoRA 更新 |

架構說明見 [../PROJECT_STATUS.md](../PROJECT_STATUS.md) §1.4、[04_CLI_OPERATION.md](04_CLI_OPERATION.md) §2。

---

## 2. 自主決策與學習產物

### Decision Ledger（主線 B）

**預設路徑**：

```text
data/bioneuronai/planning/autonomous/decision_ledger.jsonl
```

自訂：`python main.py autonomous ... --ledger-path <path>`

查看最近紀錄：

```powershell
Get-Content data\bioneuronai\planning\autonomous\decision_ledger.jsonl -Tail 5
```

常見 `type`：

| type | 產生時機 | 用途 |
|------|----------|------|
| `autonomous_cycle` | 每輪規劃結束 | `final_action`、`reasons`、`pretrade_summary` |
| `trade_outcome` | paper 平倉結算後 | `outcome.pnl` 供 AdaptationController 連敗/回撤規則 |

### AdaptiveLearningHub（兩主線共用檔案）

```text
data/bioneuronai/learning/adaptive_hub.json
```

平倉後更新策略×幣對 EWMA 績效；`autonomous` 下一輪規劃會讀取此檔（若存在）。

### EpisodicMemory（僅主線 A）

```text
data/bioneuronai/memory/
```

`trade --paper-live` 平倉後由 `TradingEngine` 寫入；主線 B **不會**更新此目錄。

---

## 3. Paper 與交易執行產物

### Paper-live（主線 A）

```text
data/bioneuronai/trading/paper_live/
```

- 由 `PaperBinanceFuturesConnector` 建立（`trade --paper-live` 啟動時 CLI 會印出 log 目錄）
- 虛擬成交 JSONL；**不**送到 Binance order API

### Autonomous paper 執行（主線 B）

`autonomous --execute-paper` 使用**獨立**的 `PaperBinanceFuturesConnector` 實例，log 同樣寫入 `data/bioneuronai/trading/paper_live/`（與主線 A 共用目錄結構，但連接器生命週期不同）。

**注意**：B 線 paper 倉位算法與 pretrade `order_parameters.quantity` 可能不一致（見 PROJECT_STATUS P2）。

---

## 4. 回測 runtime

```powershell
Get-ChildItem backtest\runtime -Directory |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 5 Name, LastWriteTime
```

查看單次 run：

```powershell
Get-ChildItem backtest\runtime\<run_id>
```

常見檔案：`status.json`、`summary.json`、`trades.json`、`orders.json`（依 run 類型而異）。

---

## 5. 模型與訓練資料

| 路徑 | 內容 |
|------|------|
| `model/*.pth` | TinyLLM、Meta-Learner 等權重 |
| `data/processed/*.pt` | 訓練用處理後張量 |
| `src/data/bioneuronai/` | 歷史 K 線 catalog（`backtest-data` 相關） |
| `logs/` | 應用程式 log（依設定而定） |

---

## 6. CLI `--output` 與 `output/`

單輪 JSON 輸出（非 append-only ledger）：

```powershell
python main.py autonomous --mode advisor --output output\advisor.json
python main.py plan --output output\daily_plan.json
```

`output/` 目錄內容為**該次操作快照**，適合 diff 或存檔；持續紀錄仍以 ledger / paper log 為準。

---

## 7. API 查詢 runtime

啟動 API 後：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/backtest/runs"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/backtest/runs/<run_id>"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/trade/status"
```

`trade/status` 在 paper-live 執行中可看到 `engine.paper_trading`、`engine.ai_model_loaded` 等欄位。

---

## 8. 驗收對照表

| 操作 | 應看到 |
|------|--------|
| `autonomous --mode advisor` | 終端 `final_action`；ledger 新增一筆 |
| `autonomous --execute-paper` | 終端 `Paper Execution`；paper_live log；可能 `trade_outcome` |
| `trade --paper-live` | paper_live log；平倉後 `memory/` 與 `adaptive_hub.json` 變更 |
| `backtest` / `simulate` | `backtest/runtime/<run_id>/` |
| `strategy-backtest` | 策略比較結果與 runtime |
| `frontend build` | `frontend/devops-d/dist/` |

---

## 9. Git 狀態排查

```powershell
git status --short
```

若出現 runtime、logs、ledger、DB 類檔案變更，先判斷是否為執行產物。不要把 `.env`、API 金鑰或大型資料誤提交。

---

## 10. 保留與清理原則

| 產物 | 建議 |
|------|------|
| 成功驗收的 ledger / runtime | 可保留作證據 |
| 臨時短測試 runtime | 可定期清理 |
| `decision_ledger.jsonl` | append-only；清理前請備份 |
| `model/*.pth` | 不隨意刪除 |
| `data/processed/*.pt` | 不隨意刪除 |
| `.env` | 不提交 |