# BioNeuronAI 測試與驗證指南 (Testing & Validation Guide)

> 更新日期：2026-04-24  
> 目的：規範 v2.1 之後的測試方法。我們已全面屏棄瑣碎的 Mock 測試腳本，改為擁抱「End-to-End CLI 測試」與「沙盒驗證」。

## 🚫 測試哲學：End-to-End > 單元測試

在早期的開發中，我們有許多散落的 `test_xxx.py` 用於測試單一模組，但這些腳本經常因為架構升級（如 Schema 變更）而過期報錯。

在 v2.1 中，我們認為 **「如果一個功能無法在真實的 CLI 指令中被觸發，那它就不算完成」**。因此，我們的主要測試路徑都是基於真實的 CLI 入口。

---

## 🧪 核心測試路徑

### 1. 策略邏輯驗證 (`strategy-backtest`)
如果您修改了 `strategies/` 內的演算法，請**不要**寫單元測試去 assert 計算結果，而是直接執行策略回測引擎：

```bash
python src/bioneuronai/cli/main.py strategy-backtest --symbol BTCUSDT --interval 1h
```
*   **用途**：逐一評估策略實例，它會讀取真實的歷史 K 線，並輸出模擬的進出場與成交紀錄。
*   **檢驗標準**：觀察輸出的 PnL、交易次數是否符合預期，確保沒有觸發風控熔斷。

### 2. 系統健康度與環境驗證 (`status`)
在修改設定檔 `.env` 或安裝新套件後，請執行：

```bash
python src/bioneuronai/cli/main.py status
```
*   **用途**：快速檢查 7 大核心模組（TradingEngine, BinanceFutures, NewsAnalyzer 等）是否能順利初始化並連線。
*   **檢驗標準**：所有狀態必須顯示為 `[OK]`。

### 3. 進場前邏輯驗證 (`pretrade`)
如果您修改了 RAG 檢索邏輯或風險管理規則，請執行：

```bash
python src/bioneuronai/cli/main.py pretrade --symbol BTCUSDT --action long
```
*   **用途**：模擬系統即將執行多單/空單，觸發完整的 5 步驟盤前檢查（包含餘額確認、新聞掃描）。
*   **檢驗標準**：觀察終端機輸出的 REJECT/APPROVE 原因是否合理。

### 4. 實盤沙盒測試 (`trade --dry-run`)
準備上線新功能前，使用測試網（Testnet）或 Dry-run 模式：

```bash
# 確保 .env 中 BINANCE_TESTNET=true
python src/bioneuronai/cli/main.py trade
```
*   **用途**：真實連接交易所 WebSocket 並接收市場資料，但不發送真實訂單（或僅發送至測試網）。
*   **檢驗標準**：觀察系統是否能穩定運行 24 小時以上不崩潰。

---

## 🐛 持續整合 (CI) 與防呆 Smoke Test

我們仍保留了唯一一個綜合型的 Pytest 腳本，用於攔截最低級別的語法錯誤與依賴缺失：

```bash
python -m pytest tests/test_smoke.py -q
```
*   **要求**：在提交任何 PR 或進行 `git commit` 之前，必須確保此命令回傳 `passed`（目前應為 26/26 通過）。

## 📝 總結
1.  **開發階段**：使用 `strategy-backtest` 快速迭代演算法。
2.  **整合階段**：使用 `pretrade` 與 `status` 確認各模組接通。
3.  **上線階段**：通過 `test_smoke.py` 後，使用 Testnet 進行 `trade` 實機運行。
