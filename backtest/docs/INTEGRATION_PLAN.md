# Backtest Integration Plan

這份文件只描述 `backtest/` 這個 replay 領域。

## 目前定位

- `backtest/` 是正式 replay 主路徑
- 角色是歷史資料重放、模擬接單、模擬帳戶狀態
- 不負責策略決策
- 不改動原始歷史資料
- 正式歷史資料已搬到 `backtest/data/binance_historical/`
- 正式 runtime artifacts 已固定落到 `backtest/runtime/`

## 目錄規則

- `backtest/data/`
  - replay 專用資料根目錄
  - 長期目標是把正式可用的歷史資料集中在這裡
- `backtest/runtime/`
  - 執行期間產生的模擬狀態、暫存結果、日誌
  - 這裡的內容可重建，不可當歷史來源
- `backtest/ui/`
  - replay UI 資產
- `backtest/vendor/`
  - 已決定整合的第三方材料、授權、局部改寫說明
- `backtest/docs/`
  - replay 專屬說明、設計與整合計畫

## 外部能力整合落點

### 1. Adapter / execution boundary

參考來源：
- NautilusTrader 的 data / execution 分層

本地落點：
- `backtest/contracts.py`
- `backtest/service.py`
- 後續若需要再新增 `backtest/execution/`

原則：
- 專案決定是否下單
- replay 只接收 `OrderIntent`
- replay 回傳 `ExecutionReceipt`

### 2. UI / dashboard 操作流

參考來源：
- Hummingbot Dashboard / API client

本地落點：
- `backtest/ui/index.html`
- 後續若需要可新增 `backtest/ui/assets/`

目前做法：
- `src/bioneuronai/api/app.py` 只保留入口
- UI 本體放在 `backtest/ui/`

### 3. Exchange adapter 統一路徑

參考來源：
- CCXT

本地落點：
- 先不直接複製第三方原始碼
- 若導入，建立在 `backtest/vendor/` 留存版本與授權說明
- 正式整合點仍由 `src/bioneuronai/data/` 與 `backtest/` 之間的 adapter 控制

### 4. Data catalog workflow

參考來源：
- Freqtrade 的 data workflow

本地落點：
- `backtest/catalog.py`
- `backtest/docs/`

### 5. Paper trade / remote control

參考來源：
- Hummingbot 的 bot control 思路

本地落點：
- `backtest/service.py`
- `backtest/runtime_store.py`
- `src/bioneuronai/api/app.py`

目前已落地：
- `python main.py backtest-runs`
- `GET /api/v1/backtest/runs`
- `GET /api/v1/backtest/runs/{run_id}`
- `backtest/runtime/<run_id>/...`

## 已淘汰的做法

- 不再把 replay UI 直接寫死在 API 檔案內
- 不再把 `data_downloads/binance_historical` 當正式主資料路徑
- 不再把 replay 描述成會自己決定是否交易

詳細淘汰紀錄見：

- `backtest/docs/DEPRECATIONS.md`

## 外部下載材料規則

- 已確定要整合的內容：
  - 放進 `backtest/vendor/`
- 暫時抓下來但最後不用的材料：
  - 放到 `C:\Users\User\Downloads\新增資料夾 (5)`
  - 不留在 repo 內
