# 資料取得與資料目錄操作手冊

> 範圍：使用者如何確認、取得與檢查歷史資料。  
> 主要入口：`backtest-data`、`tools/data_download/`、`backtest/data/`。

---

## 📑 目錄

- [1. 確認本地資料是否存在](#1-確認本地資料是否存在)
- [2. 資料位置](#2-資料位置)
- [3. 檢查特定資料集](#3-檢查特定資料集)
- [4. 使用資料跑短回測](#4-使用資料跑短回測)
- [5. 資料缺失排查](#5-資料缺失排查)
- [6. 不要手動修改的資料](#6-不要手動修改的資料)

---

## 1. 確認本地資料是否存在

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

成功標準：

- 顯示資料根目錄。
- 顯示至少一組 dataset。
- 顯示日期範圍與 zip 數量。

---

## 2. 資料位置

主要歷史資料根目錄：

```text
backtest/data/binance_historical/
```

常見結構：

```text
backtest/data/binance_historical/data/futures/um/daily/klines/<SYMBOL>/<INTERVAL>/
```

例如：

```text
backtest/data/binance_historical/data/futures/um/daily/klines/BTCUSDT/1h/
```

---

## 3. 檢查特定資料集

透過 API：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/backtest/catalog?symbol=BTCUSDT&interval=1h"
```

或透過 CLI：

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

---

## 4. 使用資料跑短回測

資料存在後，先跑短區間確認可 replay：

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

- 回測完成。
- 產生 `Run ID`。
- `backtest/runtime/<run_id>/` 有輸出。

---

## 5. 資料缺失排查

| 現象 | 可能原因 | 處理 |
|---|---|---|
| catalog 顯示 0 組資料 | 資料未下載或路徑不對 | 檢查 `backtest/data/binance_historical/` |
| 指定 symbol 找不到 | 沒有該交易對資料 | 改用現有 symbol 或補資料 |
| 指定 interval 找不到 | 沒有該週期資料 | 改用現有 interval |
| 回測日期超出範圍 | start/end 不在資料範圍內 | 依 catalog 顯示日期重設 |

---

## 6. 不要手動修改的資料

不要手動改動：

```text
backtest/data/binance_historical/
data/processed/*.pt
model/*.pth
```

這些資料若被手動改動，可能造成回測或訓練結果不可重現。
