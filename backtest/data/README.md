# Backtest Data

`backtest/data/` 是 replay / backtest 的正式歷史資料根目錄。這一層只存放回放輸入資料，不存放執行結果。

## 資料夾內容

- `README.md`
  本文件。
- `binance_historical/`
  正式 replay 歷史資料根目錄。

目前實際可見的下一層結構是：

- `binance_historical/data/`
  歷史資料主體。
- `binance_historical/data/futures/`
  期貨市場資料。

## 使用邊界

- 這裡是唯讀資料來源。
- `HistoricalDataStream`、`get_catalog()`、`resolve_data_dir()` 會優先從這裡找資料。
- 若正式資料不存在，系統仍會依 `backtest.paths.candidate_data_roots()` 嘗試舊路徑 fallback；但那些舊路徑只是相容層，不是正式規格。

## 不應放在這裡的內容

- runtime 結果
- 模擬訂單與成交紀錄
- 回測摘要
- 暫存檔或分析輸出

這些都應寫到 [../runtime/README.md](../runtime/README.md) 說明的 `backtest/runtime/`。

## 文件層級

這個資料夾底下目前沒有更深一層的 README。`binance_historical/` 的資料格式與來源規則由本文件和上層文件概述。

## 相關文件

- [backtest/README.md](../README.md)
- [runtime/README.md](../runtime/README.md)
- [docs/legacy_historical/README.md](../docs/legacy_historical/README.md)
