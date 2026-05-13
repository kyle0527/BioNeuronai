# BioNeuronAI 測試與驗證指南 (Testing & Validation Guide)

> 更新日期：2026-05-13
> 目的：規範 v2.1 之後的驗證方法。專案目前優先用正式 CLI / API / UI runtime 入口驗證，不以臨時測試檔或 mock 腳本作為功能完成標準。

## 🚫 測試哲學：End-to-End > 單元測試

在早期的開發中，我們有許多散落的 `test_xxx.py` 用於測試單一模組，但這些腳本經常因為架構升級（如 Schema 變更）而過期報錯。

在 v2.1 中，我們認為 **「如果一個功能無法在真實的 CLI 指令中被觸發，那它就不算完成」**。因此，我們的主要測試路徑都是基於真實的 CLI 入口。

---

## 🧪 核心驗證路徑

### 1. 策略邏輯驗證 (`strategy-backtest`)
如果您修改了 `strategies/` 內的演算法，請**不要**寫單元測試去 assert 計算結果，而是直接執行策略回測引擎：

```bash
python main.py strategy-backtest --symbol BTCUSDT --interval 1h
```
*   **用途**：逐一評估策略實例，它會讀取真實的歷史 K 線，並輸出模擬的進出場與成交紀錄。
*   **檢驗標準**：觀察輸出的 PnL、交易次數是否符合預期，確保沒有觸發風控熔斷。

### 2. 系統健康度與環境驗證 (`status`)
在修改設定檔 `.env` 或安裝新套件後，請執行：

```bash
python main.py status
```
*   **用途**：快速檢查 7 大核心模組（TradingEngine, BinanceFutures, NewsAnalyzer 等）是否能順利初始化並連線。
*   **檢驗標準**：所有狀態必須顯示為 `[OK]`。

### 3. 進場前邏輯驗證 (`pretrade`)
如果您修改了 RAG 檢索邏輯或風險管理規則，請執行：

```bash
python main.py pretrade --symbol BTCUSDT --action long
```
*   **用途**：觸發完整的 6 點盤前檢查（包含餘額、新聞/RAG、技術面與風控）。
*   **檢驗標準**：觀察終端機輸出的 REJECT/APPROVE 原因是否合理。

### 4. Paper-live / Testnet runtime 驗證
準備上線新功能前，優先使用 paper-live 或測試網：

```bash
# 主網行情 + 本地虛擬成交，不送 Binance 訂單
python main.py trade --paper-live --paper-balance 10000

# 或 Binance Futures testnet
python main.py trade --testnet
```
*   **用途**：真實連接交易所行情並接收市場資料。paper-live 不發送真實訂單；testnet 只送測試網。
*   **檢驗標準**：觀察系統是否能穩定運行 24 小時以上不崩潰。

### 5. 正式交易前 Readiness Gate

在 testnet / live 前，必須先跑正式 gate。這不是臨時測試檔，而是 `backtest/` replay service 的 CLI 入口，會依 `config/trading_readiness_gate.json` 檢查 BTCUSDT / ETHUSDT 多時間框架矩陣、資料覆蓋、Walk-Forward IS/OOS 與績效門檻。

```bash
# 只檢查矩陣、資料與門檻設定，不執行回測
python main.py readiness-gate --dry-run

# 執行完整 gate 並保存報告
python main.py readiness-gate --output output/readiness_gate.json
```

*   **用途**：把「正式交易前需完成 BTC/ETH 多時間框架回測並設定通過門檻」變成可執行保護門。
*   **檢驗標準**：完整執行時狀態必須為 `PASS`。若資料缺失（例如 4h K 線未下載）或未達交易次數 / OOS 門檻，CLI 會以 `FAIL` 阻擋。

---

## 🐛 持續整合 (CI) 與防呆 Smoke Test

CI 可以保留綜合型 Pytest 腳本，用於攔截最低級別的語法錯誤與依賴缺失；但它不是本機功能驗證的主要路徑：

```bash
python -m pytest tests/test_smoke.py -q
```
*   **要求**：CI / PR 可使用；本地功能驗證仍以 CLI / API / UI 正式入口為準。

## 📝 總結
1.  **開發階段**：使用 `strategy-backtest` 快速迭代演算法。
2.  **整合階段**：使用 `pretrade` 與 `status` 確認各模組接通。
3.  **上線前門檻**：使用 `readiness-gate` 確認 BTC/ETH 多時間框架矩陣通過。
4.  **上線階段**：使用 paper-live 長時間觀察，接著 testnet，再進 live guard 流程。
