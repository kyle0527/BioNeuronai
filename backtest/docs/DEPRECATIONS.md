# Deprecations And Removed Wrong Assumptions

這份文件只記錄已淘汰或已修正的舊說法。

## 已移除的錯誤或過時說法

### 1. `backtest/` 會決定是否交易

這是錯的。

目前正確說法：

- 策略模組 / 專案主體決定是否下單
- replay 系統只接收訂單請求並模擬執行

### 2. 正式資料仍在 `data/bioneuronai/historical/...`

這已不是正式主路徑。

目前正確說法：

- 正式資料主路徑：`backtest/data/binance_historical/`
- 舊路徑只保留相容用途

### 3. replay UI 本體放在 API 程式碼內

這已移除。

目前正確說法：

- UI 本體放在 `backtest/ui/index.html`
- `src/bioneuronai/api/app.py` 只保留入口

### 4. `backtest/` 是策略評估核心

這個說法容易混淆。

目前正確說法：

- `backtest/` 是 replay / 模擬執行層
- 策略優劣仍由專案自己的策略、分析、績效邏輯判讀

### 5. 只要跑 replay 就一定會有交易

這是錯的。

目前正確說法：

- replay 能接單，不代表上層策略一定會送單
- 沒有交易時，應先檢查策略輸出與資料區間，而不是先怪 replay

### 6. 舊 README 內的示意承諾可直接當正式規格

這已不成立。

例如：

- 「TradingEngine 完全不知道這是回測」
- 「只需替換連接器實例」
- 舊的 `data_downloads/binance_historical` 路徑示例

這些敘述現在只能當歷史背景，不能當正式文件規格。

### 7. `StrategyArena` / `StrategyPortfolioOptimizer` 仍以假績效評估

這已不成立。

目前正確說法：

- `StrategyArena` 已使用正式 replay 評估單一策略實例
- `StrategyPortfolioOptimizer` 已使用正式 replay 聚合各 phase gene 的結果
- 目前真正的限制不是假績效，而是固定策略層本身仍在調整

### 8. `MeanReversionStrategy` 仍完全未實作正式進場邏輯

這個說法已不精確。

目前正確說法：

- `MeanReversionStrategy.evaluate_entry_conditions()` 已有正式邏輯
- 目前主要問題是固定策略共同的 setup 驗證順序，而不是只剩空實作

## 保留但降級為歷史參考

- `backtest/docs/legacy_historical/`

這個資料夾只保留歷史資料相關舊文件，不代表目前正式規格。
