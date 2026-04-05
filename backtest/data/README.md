# Replay Data Root

這裡是正式 replay 歷史資料主目錄。

- `backtest/data/binance_historical/`

目前系統仍相容舊資料路徑，但那只是 fallback，不是正式規格。

原則：

- 原始歷史資料只讀
- 回放期間不可修改這裡的內容
- 所有模擬結果請寫到 `backtest/runtime/`
- 不要把 runtime 輸出、分析結果、暫存檔寫回這裡
