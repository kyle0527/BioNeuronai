# Runtime State

這個資料夾只放 replay 執行期間的可變狀態，例如：

- 模擬訂單紀錄
- 模擬成交紀錄
- 模擬帳戶快照
- run 摘要
- runtime 狀態
- backtest 結果輸出

原則：

- 可以刪除
- 可以重建
- 不可當成正式歷史資料來源
- 一次 replay 對應一個 `<run_id>` 目錄
