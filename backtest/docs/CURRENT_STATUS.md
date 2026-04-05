# Current Status

更新日期：2026-04-05

## 正式定位

- `backtest/` 是專案正式 replay 主路徑
- `backtesting/` 不是正式 runtime 主路徑
- 歷史資料已搬到 `backtest/data/binance_historical/`

## 已完成

- replay 資料根目錄收斂到 `backtest/data/`
- replay UI 資產收斂到 `backtest/ui/`
- replay runtime 輸出收斂到 `backtest/runtime/`
- API 已可執行和查詢 replay runs
- CLI 已可執行和查詢 replay runs
- replay 接單後會保存訂單與執行結果
- replay 已可正式評估 `TradingEngine` 主線
- `StrategyArena` 已改用正式 replay 結果，不再使用隨機假績效
- `StrategyPortfolioOptimizer` 已改用正式 replay 聚合各 phase gene 結果

## 目前正式入口

### CLI

- `python main.py backtest`
- `python main.py simulate`
- `python main.py backtest-data`
- `python main.py backtest-runs`

### API

- `GET /api/v1/backtest/catalog`
- `GET /api/v1/backtest/inspect`
- `POST /api/v1/backtest/simulate`
- `POST /api/v1/backtest/run`
- `GET /api/v1/backtest/runs`
- `GET /api/v1/backtest/runs/{run_id}`
- `GET /backtest/ui`

## 目前已確認的責任邊界

- replay 系統不負責決定是否交易
- replay 系統只負責提供資料、接收訂單、模擬執行、保存結果
- 原始歷史資料只讀
- runtime 可刪除、可重建

## 目前已知限制

- 正式資料覆蓋範圍仍有限，目前正式資料根目錄下只有 `ETHUSDT`
- `PairTradingStrategy` 需要次資產資料，現有正式資料不足以完成正式評估
- `TrendFollowing` / `SwingTrading` / `MeanReversion` 已能建立 setup，但固定策略共同流程仍有 setup 驗證順序問題
- `BreakoutTrading` / `DirectionChangeStrategy` 在目前 ETH 歷史資料窗口上尚未驗證出穩定觸發
- 是否有交易取決於上層策略，而不是 replay 本身
- 短資料區間時需要調整 `warmup_bars`
