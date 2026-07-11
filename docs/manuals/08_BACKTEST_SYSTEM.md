# BioNeuronai 回測系統使用指南

> **套件版本**：v2.1（`pyproject.toml`）
> **更新日期**：2026-06-15
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)
> **子系統細節**：[`backtest/README.md`](../../backtest/README.md)

---

## 目錄

1. [系統概覽](#1-系統概覽)
2. [Replay 與即時交易主線的差異](#2-replay-與即時交易主線的差異)
3. [歷史資料準備](#3-歷史資料準備)
4. [CLI 命令參考](#4-cli-命令參考)
5. [Runtime 產物與驗收](#5-runtime-產物與驗收)
6. [API 與 UI 入口](#6-api-與-ui-入口)
7. [自定義腳本（BacktestEngine）](#7-自定義腳本backtestengine)
8. [核心組件](#8-核心組件)
9. [相關手冊](#9-相關手冊)

---

## 1. 系統概覽

`backtest/` 是專案的正式 **歷史 replay / 回測** 子系統，與 repo 根目錄的 `python main.py` CLI 及 FastAPI 共用同一套服務層（`backtest/service.py`）。

核心設計：

- 使用 `MockBinanceConnector` 取代即時 `BinanceFuturesConnector`，將歷史 K 線逐 bar 推進。
- 策略（`strategies/`）與 AI 推理（`core/inference_engine.py`）**沿用實盤程式碼**；撮合與帳戶狀態在 mock connector 內模擬。
- **資料無未來性**：`HistoricalDataStream` / `get_klines_until_now()` 確保在時刻 `T` 拿不到 `T+1` 收盤價。
- 每次執行寫入 `backtest/runtime/<run_id>/`（見 §5）。

---

## 2. Replay 與即時交易主線的差異

請勿把「回測」與「即時交易」混為同一條驗收路徑：

| 維度 | Replay（本手冊） | 主線 A：`trade` | 主線 B：`autonomous` |
|------|------------------|-----------------|----------------------|
| 資料 | 本地歷史 K 線 | WebSocket 即時行情 | 定時載入 K 線做規劃 |
| 連接器 | `MockBinanceConnector` | 真實 / paper / testnet connector | 獨立 paper connector（`--execute-paper`） |
| 主要產物 | `backtest/runtime/<run_id>/` | `paper_live/` log、`memory/` | `decision_ledger.jsonl` |
| LoRA 閉環 | ❌（replay 不觸發即時平倉學習） | ✅（paper-live 平倉） | ❌ |
| 典型用途 | 策略驗證、readiness-gate | 長時間監控 | 盤前值班 |

即時交易操作見 [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md)；產物總覽見 [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)。

---

## 3. 歷史資料準備

### 3.1 盤點本地資料

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

可加 `--json` 輸出機器可讀格式。找不到資料時，CLI 會提示先執行 `tools/data_download/` 下載。

### 3.2 資料根目錄（優先順序）

`resolve_data_dir()` 依 `backtest/paths.py` 的 `candidate_data_roots()` 搜尋，優先順序大致為：

1. `--data-dir` 指定路徑
2. `backtest/data/binance_historical/`（正式規格）
3. `data/bioneuronai/historical/data_downloads/binance_historical/`（相容 fallback）
4. 其他舊路徑（`data_downloads/`、`training_data/` 等）

詳見 [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md)、[`backtest/data/README.md`](../../backtest/data/README.md)。

---

## 4. CLI 命令參考

所有命令在 **repo 根目錄**執行。執行後請檢查終端印出的 `Run ID` 與 `Runtime Dir`。

### 4.1 `simulate` — 信號觀測（預設不下 mock 單）

逐 bar 推進，呼叫 `TradingEngine.generate_trading_signal()` 統計信號次數；**不**呼叫 `place_order()`（CLI 說明「不產生真實訂單」= 不送 Binance，且此模式也不做 mock 撮合）。

```powershell
python main.py simulate `
  --symbol BTCUSDT `
  --interval 1h `
  --bars 20 `
  --balance 10000 `
  --start-date 2020-01-01 `
  --end-date 2020-01-03
```

| 參數 | 預設 | 說明 |
|------|------|------|
| `--symbol` | `BTCUSDT` | 交易對 |
| `--interval` | `15m` | K 線週期 |
| `--balance` | `100000` | 模擬資金 |
| `--bars` | `200` | 最多處理幾根 K 線 |
| `--start-date` / `--end-date` | — | 可選日期範圍 |
| `--data-dir` | 自動 | 歷史資料根目錄 |

成功標準：印出 `signals_emitted`、`signal_counts`、Run ID；`backtest/runtime/<run_id>/` 產生目錄。

### 4.2 `backtest` — 完整 AI 策略 replay（含 mock 撮合）

在 warmup 後依 AI 信號透過 `MockBinanceConnector.place_order()` 模擬進出場。

```powershell
python main.py backtest `
  --symbol BTCUSDT `
  --interval 1h `
  --start-date 2020-01-01 `
  --end-date 2020-01-03 `
  --balance 10000 `
  --warmup-bars 10
```

| 參數 | 預設 | 說明 |
|------|------|------|
| `--symbol` | `ETHUSDT` | 交易對 |
| `--interval` | `1h` | K 線週期 |
| `--balance` | `10000` | 初始資金 |
| `--warmup-bars` | `100` | 預熱 K 線數（預熱期不交易） |
| `--start-date` / `--end-date` | 資料全集 | 可選 |
| `--data-dir` | 自動 | 歷史資料根目錄 |

成功標準：印出總報酬率、夏普、最大回撤、勝率、交易次數、Run ID。

### 4.3 `strategy-backtest` — 策略模板競技

逐一評估策略模板（10 個模板或 hybrid 模式），保存模擬進出場紀錄。詳見 [10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md)。

```powershell
python main.py strategy-backtest `
  --symbol BTCUSDT `
  --interval 1h `
  --start-date 2020-01-01 `
  --end-date 2020-01-03 `
  --output output\strategy_compare.json
```

常用參數：`--execution-mode template_rules|hybrid`、`--walk-forward`、`--commission-bps`、`--slippage-bps`、`--params <json>`。

### 4.4 `readiness-gate` — 上線前門檻

對 BTC/ETH 多時間框架矩陣跑策略回測門檻；`FAIL` 時 **exit code = 1**。

```powershell
# 只檢查矩陣、資料與設定（不跑回測）
python main.py readiness-gate --dry-run

# 正式執行
python main.py readiness-gate --output output\readiness_report.json
```

預設設定檔：`config/trading_readiness_gate.json`。可覆寫 `--symbols`、`--intervals`、`--start-date`、`--end-date`。

### 4.5 `collect-signal-data` — 訊號訓練資料

從真實未來 K 線結果收集 `unified_trainer` 的 16×64 特徵、65 維標籤與中英說明（預設 `data/unified_v2_training.jsonl`）。不再呼叫模型產生訓練標籤。

```powershell
python main.py collect-signal-data `
  --symbol BTCUSDT `
  --interval 1h `
  --max-samples 1000 `
  --future-horizon 12 `
  --output data\unified_v2_training.jsonl
```

### 4.6 `backtest-runs` — 查詢歷史 run

```powershell
python main.py backtest-runs --limit 5
python main.py backtest-runs --run-id <run_id>
python main.py backtest-runs --run-id <run_id> --json
```

---

## 5. Runtime 產物與驗收

每次 `simulate` / `backtest` / `strategy-backtest` 成功後，產物位於：

```text
backtest/runtime/<run_id>/
```

常見檔案（依 run 類型而異）：

| 檔案 | 內容 |
|------|------|
| `summary.json` | 摘要統計 |
| `status.json` | 執行狀態 |
| `account.json` | 模擬帳戶快照 |
| `runtime_state.json` | bar 推進狀態 |
| `result.json` | 完整結果（backtest） |
| `orders.jsonl` | 模擬訂單流水 |

PowerShell 查最近 run：

```powershell
Get-ChildItem backtest\runtime -Directory |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 5 Name, LastWriteTime
```

**驗收方式**：檢查終端輸出 + runtime 目錄內容（**非 pytest**）。詳見 [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md) §4。

---

## 6. API 與 UI 入口

需先啟動 API（見 [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md) §3.1）：

| 方法 | 路徑 | 用途 |
|------|------|------|
| GET | `/api/v1/backtest/catalog` | 歷史資料清單 |
| GET | `/api/v1/backtest/inspect` | 資料集載入檢查 |
| POST | `/api/v1/backtest/simulate` | replay 模擬 |
| POST | `/api/v1/backtest/run` | 完整 backtest |
| POST | `/api/v1/backtest/strategy-run` | 策略模板回測 |
| GET | `/api/v1/backtest/runs` | 列出 runtime runs |
| GET | `/api/v1/backtest/runs/{run_id}` | 單一 run 詳情 |
| GET | `/backtest/ui` | 內建簡易 HTML 工具 |

完整請求格式見 [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md)。

---

## 7. 自定義腳本（BacktestEngine）

若需 Jupyter 或自訂分析，請在 repo 根目錄執行，並使用 `backtest` 套件匯入：

### 7.1 自訂策略回呼

```python
from backtest import BacktestEngine

def my_strategy(bar, connector):
    """每根 K 線觸發一次；connector 為 MockBinanceConnector。"""
    klines = connector.data_stream.get_klines_until_now(50)
    if not klines or len(klines) < 20:
        return
    # connector.place_order(bar.symbol, "BUY", "MARKET", 0.01)

engine = BacktestEngine(
    symbol="BTCUSDT",
    interval="1h",
    start_date="2020-01-01",
    end_date="2020-01-03",
    initial_balance=10000.0,
)
result = engine.run(my_strategy, print_summary=True)

print(f"交易次數: {len(result.trades)}")
print(f"總損益: {result.stats.get('total_pnl', 0):.2f} USDT")
```

### 7.2 `run_with_trading_engine()` — 完整 TradingEngine 管道

```python
from backtest import BacktestEngine
from bioneuronai.core.trading_engine import TradingEngine

trading_engine = TradingEngine(testnet=True, enable_ai_model=False)

engine = BacktestEngine(
    symbol="BTCUSDT",
    interval="1h",
    start_date="2020-01-01",
    end_date="2020-01-03",
    initial_balance=10000.0,
)

result = engine.run_with_trading_engine(
    trading_engine=trading_engine,
    auto_trade=True,   # False = 只產生信號，不 execute_trade
    print_summary=True,
)
```

`run_with_trading_engine()` 會暫時把 `trading_engine.connector` 換成 `MockBinanceConnector`，結束後還原；每次 `run()` 開始會 reset InferenceEngine 滾動視窗。

---

## 8. 核心組件

| 組件 | 路徑 | 職責 |
|------|------|------|
| `HistoricalDataStream` | `backtest/data_stream.py` | 載入歷史 K 線、無未來洩漏 |
| `MockBinanceConnector` | `backtest/mock_connector.py` | 模擬行情、撮合；內部使用 `bioneuronai.trading.VirtualAccount` |
| `BacktestEngine` | `backtest/backtest_engine.py` | 逐 bar 驅動策略回呼 |
| `ReplayRunRecorder` | `backtest/runtime_store.py` | 寫入 `backtest/runtime/<run_id>/` |
| `service.py` | `backtest/service.py` | CLI/API 高階入口：`run_backtest_summary`、`run_simulation_summary` 等 |
| `readiness_gate.py` | `backtest/readiness_gate.py` | 多矩陣門檻檢查 |

**注意**：replay 產物寫入 `backtest/runtime/`，**不**寫入 `decision_ledger.jsonl` 或 `data/bioneuronai/memory/`。子系統細節與 `backtest/docs/USER_MANUAL.md` 互補：本手冊為使用者主入口，`backtest/docs/` 為實作細節。

---

## 9. 相關手冊

| 手冊 | 用途 |
|------|------|
| [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md) | Level 0 短回測驗收 |
| [04_CLI_OPERATION.md](04_CLI_OPERATION.md) | CLI 總覽 |
| [10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md) | `strategy-backtest` 解讀 |
| [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md) | 歷史資料下載 |
| [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md) | 產物路徑 |
| [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md) | Backtest API |
