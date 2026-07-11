# Runtime 與輸出產物手冊

> **套件版本**：v2.1  
> **更新日期**：2026-07-11  
> **範圍**：如何找到操作後的結果、log、runtime、模型與資料產物。  
> **方向權威**：[`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)  
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)  
> **驗證方式**：直接檢查檔案與 CLI／API 輸出（**非 pytest**）。  
> **用途**：工程自主驗收的「正確證據」對帳——決策／進場／出場是否寫進真實產物。  
> 日常 Paper 與長期 `backtest/runtime/` 都算正式證據；單元測試綠燈不算。

---

## 目錄

1. [產物總覽（依執行主線）](#1-產物總覽依執行主線)
2. [自主決策與學習產物](#2-自主決策與學習產物)
   - [Decision Ledger](#decision-ledger主線-b)
   - [AdaptiveLearningHub](#adaptivelearninghub兩主線共用檔案)
   - [EpisodicMemory 與 LoRA](#episodicmemory-與-lora共用平倉鏈)
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

兩條主線**產物重心不同**，但 paper 平倉後應走 **共用學習鏈**（見 PROJECT_STATUS §1.4）。請勿混用驗收標籤。

| 主線 | 入口 | 必查產物 | 通常沒有／較少 |
|------|------|----------|----------------|
| A：`trade` | `trade --paper-live` 等 | `data/bioneuronai/trading/paper_live/`、`memory/`、`learning/adaptive_hub.json`、ActionRecord 路徑 | `decision_ledger.jsonl`（A 不寫 ledger） |
| B：`autonomous` | `autonomous ...` | `decision_ledger.jsonl`、`adaptive_hub.json`（平倉後）；paper 目錄（若 `--execute-paper`） | A 專屬 tick 日誌細節 |
| B + paper 平倉 | shared callback | 除 ledger 外，**可**經 TradingEngine 更新 memory／LoRA／Hub | 勿再寫「B 永遠不更新 memory／LoRA」 |

架構：[../PROJECT_STATUS.md](../PROJECT_STATUS.md) §1.4、[04_CLI_OPERATION.md](04_CLI_OPERATION.md) §2、[../CURRENT_DIRECTION.md](../CURRENT_DIRECTION.md)。

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

### EpisodicMemory 與 LoRA（共用平倉鏈）

```text
data/bioneuronai/memory/
```

- **主線 A**：`trade --paper-live` 平倉 → `TradingEngine` → Memory → LoRA（達門檻時）。  
- **主線 B**：paper 平倉經 `_on_shared_paper_close` → 引擎 `_on_paper_close` **同一學習鏈** + ledger outcome。  
- 若「有 ledger 無 memory 變化」：可能尚未真正平倉、筆數未達 LoRA 門檻、或學習寫入被降級——**不要**假設 B 線被設計成永遠不寫 memory。  

對帳時以**是否發生平倉**與 ledger `trade_outcome` 為準。

---

## 3. Paper 與交易執行產物

### Paper-live（主線 A）

```text
data/bioneuronai/trading/paper_live/
```

- `trade --paper-live` 啟動時 CLI 會印出 log 目錄  
- 虛擬成交；**不**送 Binance order API  

### Autonomous paper 執行（主線 B）

`autonomous --mode paper_auto --execute-paper` 透過 **TradingEngine 持有的 paper connector** 下單（`execute_prepared_order`），log 仍可能落在 `data/bioneuronai/trading/paper_live/` 同類路徑。

- quantity：**優先** pretrade `order_parameters.quantity`（× risk）；無效才 fallback notional fraction  
- 已有持倉：`skipped=existing_position`  
- **不要**再描述為「永遠獨立、與引擎無關的第二套帳戶」  

詳見 [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) §5。

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
| `config/active_model.json` | 現役模型單一真相；可 `trained: false` |
| `model/tokenizer/` | 共用詞表 |
| `model/unified_v2_100m.pth` | v2 訓練完成後才有；目前可能不存在 |
| `model/*.pth` 其他 | 歷史／輔助權重；v1 應在 `archived/` 而非現役 |
| `data/processed/*.pt` | 訓練用處理後張量 |
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
| `autonomous --execute-paper --cycles N` | 多輪 ledger；可能 `Paper Execution` 或 `skipped`；平倉後 `trade_outcome`；可經 shared 鏈更新 hub／memory |
| `trade --paper-live` | paper_live log；平倉後 `memory/` 與 `adaptive_hub.json` 變更 |
| `backtest` / `simulate` | `backtest/runtime/<run_id>/`（**長期**驗證） |
| `strategy-backtest` | 策略比較結果與 runtime |
| `frontend build` | `frontend/devops-d/dist/`（可選，非正式流程完成標準） |

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