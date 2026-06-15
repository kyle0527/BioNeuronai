# 資料取得與資料目錄操作手冊

> **套件版本**：v2.1
> **更新日期**：2026-06-15
> **範圍**：確認、取得與檢查歷史 replay 資料
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)

---

## 目錄

1. [確認本地資料](#1-確認本地資料)
2. [資料根目錄與 fallback](#2-資料根目錄與-fallback)
3. [下載歷史資料](#3-下載歷史資料)
4. [API / CLI 查詢](#4-api--cli-查詢)
5. [短回測驗收](#5-短回測驗收)
6. [缺失排查](#6-缺失排查)
7. [勿手動修改的資料](#7-勿手動修改的資料)

---

## 1. 確認本地資料

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

成功標準：顯示 `resolved_root`、至少一組 dataset、日期範圍與檔案數量。

---

## 2. 資料根目錄與 fallback

`backtest/paths.py` 的 `candidate_data_roots()` 搜尋順序：

| 優先 | 路徑 | 說明 |
|------|------|------|
| 1 | `--data-dir` 指定 | CLI/API 覆寫 |
| 2 | `backtest/data/binance_historical/` | **正式規格** |
| 3 | `data/bioneuronai/historical/data_downloads/binance_historical/` | 專案相容路徑 |
| 4 | `data_downloads/binance_historical/` | 舊路徑 |
| 5 | `training_data/data_downloads/binance_historical/` | 訓練用相容路徑 |

常見檔案結構：

```text
.../binance_historical/data/futures/um/daily/klines/<SYMBOL>/<INTERVAL>/
```

詳見 [`backtest/data/README.md`](../../backtest/data/README.md)。

---

## 3. 下載歷史資料

資料缺失時，使用 repo 內下載工具（路徑依專案設定，常見為 `tools/data_download/`）。下載完成後重新執行 `backtest-data` 確認 catalog。

readiness-gate 需要 BTC/ETH 多週期（如 `1h`、`4h`）資料齊全時，請依 [`config/trading_readiness_gate.json`](../../config/trading_readiness_gate.json) 矩陣補齊。

---

## 4. API / CLI 查詢

**CLI：**

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h --json
```

**API**（需先啟動 uvicorn）：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/backtest/catalog?symbol=BTCUSDT&interval=1h"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/data/catalog"
```

---

## 5. 短回測驗收

```powershell
python main.py backtest `
  --symbol BTCUSDT `
  --interval 1h `
  --start-date 2020-01-01 `
  --end-date 2020-01-03 `
  --balance 10000 `
  --warmup-bars 10
```

成功標準：終端印出 Run ID；`backtest/runtime/<run_id>/` 有輸出。詳見 [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)。

---

## 6. 缺失排查

| 現象 | 可能原因 | 處理 |
|------|----------|------|
| catalog 0 組 | 未下載或路徑錯 | 檢查 §2 各路徑；執行下載工具 |
| symbol 找不到 | 無該交易對 | 換現有 symbol 或補資料 |
| interval 找不到 | 無該週期 | readiness 常需補 `4h` 等 |
| 回測日期超出範圍 | start/end 不在 catalog | 依 catalog 日期重設 |

---

## 7. 勿手動修改的資料

```text
backtest/data/binance_historical/   # 唯讀歷史來源
data/processed/*.pt
model/*.pth
```

手動改動會使回測/訓練不可重現。