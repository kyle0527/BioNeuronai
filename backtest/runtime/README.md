# Backtest Runtime

`backtest/runtime/` 存放 replay 執行期間產生的可變狀態與輸出結果。這裡是執行產物區，不是正式歷史資料來源。

## 資料夾內容

- `README.md`
  本文件。
- `<run_id>/`
  每次 `simulate` 或 `backtest` 執行後產生的一個 run 目錄。

目前這個資料夾內已存在多個以時間戳加隨機碼組成的 run 目錄，例如 `20260423_103454_70aedfd9/`。

## run 目錄內容

由 `ReplayRunRecorder` 寫入的常見檔案包含：

- `summary.json`
- `status.json`
- `account.json`
- `runtime_state.json`
- `result.json`
- `orders.jsonl`

實際出現哪些檔案，取決於該次 run 是否有下單、是否跑完整 backtest，以及是否有結果需要落盤。

## 使用邊界

- 可以清除並重建。
- 不應視為訓練原始資料或正式市場歷史資料。
- 同一個 run 的資料應完整留在自己的 `<run_id>/` 目錄中，不要跨 run 混寫。

## 文件層級

這個資料夾底下目前沒有更深一層的 README。run 目錄是執行輸出，不需要再建立文件鏈。

## 相關文件

- [backtest/README.md](../README.md)
- [data/README.md](../data/README.md)
