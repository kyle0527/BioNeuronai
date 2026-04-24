# 分析模組操作手冊

這份手冊專注於說明**分析模組 (Analysis Module)** 的操作方式。分析模組是 BioNeuronAI 系統中負責「看懂市場」的眼睛，主要涵蓋**新聞情緒**、**宏觀市場環境掃描 (每日計畫)**，以及**進場前綜合驗核 (Pre-trade)**。

定位很簡單：
1. 怎麼用 CLI 跑分析功能
2. 怎麼用 UI / API 呼叫分析功能
3. 這些分析結果會輸出到哪裡，以及如何影響交易決策

---

## 適用範圍

目前這份手冊對應的是分析模組的三大核心操作：
- **新聞情緒分析 (`news`)**：抓取最新新聞、計算情緒分數、關鍵字過濾。
- **每日交易計畫與宏觀掃描 (`plan`)**：整合恐慌貪婪指數、全球市值、DeFi TVL 等外部數據，給出總體市場狀態建議。
- **進場前驗核 (`pretrade`)**：綜合技術面、基本面（新聞/RAG）、資金管理，執行 6 點安全檢查。

---

## 這個功能實際在做什麼分析

### 1. 新聞情緒分析 (News Analysis)
- 從 CryptoPanic API 與 RSS Feeds 抓取最新的加密貨幣新聞。
- 過濾目標幣種（如 `BTCUSDT`）的相關新聞。
- 使用內建的關鍵字詞庫（181 個關鍵字）與規則模型，對每篇新聞進行評分（-1 ~ +1）。
- 自動將分析結果寫入 RAG 知識庫，供 AI 模型與交易引擎參考。

### 2. 宏觀市場掃描 / 每日計畫 (Daily Plan)
- 呼叫多個外部 API（Alternative.me, CoinGecko, DefiLlama）。
- 匯總市場總體情緒（如恐慌貪婪指數）、市場資金流向（穩定幣供應、DeFi 鎖倉量）。
- 結合 Binance 歷史 K 線，判斷目前的「大盤體制」（如：強勢上漲、高波動震盪）。
- 生成一份包含具體建議的每日交易計畫書。

### 3. 進場前驗核 (Pre-trade Check)
在真實下單前，最後一道防線。系統會依序檢查：
1. **信心度檢查**：AI 或策略的訊號強度是否達標。
2. **回撤與風險檢查**：帳戶是否處於過大回撤中。
3. **過度交易檢查**：是否超過每日最大交易次數。
4. **資金與保證金檢查**：可用餘額是否足夠。
5. **RAG / 新聞防護**：近期是否有重大黑天鵝或反向強烈新聞。
6. **參數檢查**：槓桿與止損設定是否合理。

---

## CLI 操作

### 1. 新聞情緒分析 (`news`)

**基本指令：**
```powershell
python main.py news --symbol BTCUSDT
```

**常用參數：**
- `--symbol`: 指定交易對（預設 BTCUSDT）。
- `--max-items`: 限制抓取的新聞數量（預設 10）。
- `--hours`: 指定抓取過去幾小時的新聞（若不指定，系統會自動根據上次抓取時間做自適應抓取）。

**預期輸出：**
CLI 會列出抓到的新聞標題、各自的情緒分數，以及最終的綜合情緒評分（如 `+0.45 偏多`），並顯示成功寫入知識庫的筆數。

### 2. 每日交易計畫 (`plan`)

**基本指令：**
```powershell
python main.py plan --symbol BTCUSDT --output daily_plan.json
```

**常用參數：**
- `--symbol`: 評估的主要交易對。
- `--output`: 將計畫結果輸出成 JSON 檔案。

**預期輸出：**
CLI 會印出宏觀市場狀態（如：恐慌貪婪指數 75 - 貪婪），當前趨勢判定，以及各個子策略（Trend Following, Mean Reversion 等）的推薦權重與操作建議。

### 3. 進場前驗核 (`pretrade`)

**基本指令：**
```powershell
python main.py pretrade --symbol BTCUSDT --action long
```

**常用參數：**
- `--symbol`: 交易對。
- `--action`: 準備執行的方向 (`long` 或 `short`)。
- `--capital`: 準備投入的資金。

**預期輸出：**
會依序印出 5-6 個檢查步驟的狀態（`[OK]` 或 `[REJECT]`）。如果最終被拒絕，會明確給出原因（例如：`REJECT: 期貨錢包可用餘額不足` 或 `REJECT: 新聞情緒與操作方向強烈衝突`）。

---

## UI / API 操作

分析模組的功能已經完全封裝為 FastAPI 的 REST 端點，可以透過 Swagger UI (`http://localhost:8000/docs`) 或自訂的前端直接呼叫。

### 1. 新聞情緒分析 API
**端點**：`POST /api/v1/news`

**請求範例 (JSON)**：
```json
{
  "symbol": "BTCUSDT",
  "max_items": 10,
  "hours": 24
}
```
**回傳**：包含 `sentiment_score` (綜合分數)、`news_items` (個別新聞明細) 與 `regime_suggestion`。

### 2. 每日計畫 API
**端點**：`POST /api/v1/plan`

**請求範例 (JSON)**：
```json
{
  "symbol": "BTCUSDT"
}
```
**回傳**：完整的 `TradingPlan` 結構，包含 `macro_analysis`、`strategy_weights` 與 `risk_parameters`。

### 3. 進場前驗核 API
**端點**：`POST /api/v1/pretrade`

**請求範例 (JSON)**：
```json
{
  "symbol": "BTCUSDT",
  "action": "long",
  "capital": 10000.0,
  "leverage": 10
}
```
**回傳**：包含 `is_approved` (布林值) 以及所有檢查點的明細報告 `check_results`。

---

## 分析結果如何影響系統？

分析模組不是孤立運作的，它的產出會直接回饋給交易與策略層：

1. **新聞情緒 → 策略融合 (Strategy Fusion)**
   - 如果新聞情緒極度看空（如跌破 -0.6），即便技術面策略看多，`strategy_fusion` 也會強制降低多單的權重，甚至觸發禁止做多的保護機制。
   
2. **宏觀掃描 → 策略選擇器 (Strategy Selector)**
   - 每日計畫判斷出的「市場體制」(Regime)，會告訴 Router 現在是「震盪」還是「趨勢」。這會決定接下來一天是由「均值回歸」還是「趨勢跟隨」策略主導。

3. **Pre-trade → 交易引擎 (Trading Engine)**
   - 任何由 AI 或策略發出的交易訊號，在真正送出 Binance API 訂單前，都會被攔截並強制執行一遍 Pre-trade。只有拿到 `is_approved: true` 才會真正成交。

---

## 常見問題與除錯

**Q: 為什麼新聞分析 (`news`) 總是回傳 0 分？**
- A: 可能是近期沒有該交易對的重大新聞，或者您的 `.env` 中 `CRYPTOPANIC_API_TOKEN` 沒有正確設定。預設使用免費版 API。

**Q: Pre-trade 一直被 Reject，說「Futures 餘額為 0」？**
- A: 這是 Binance 正式網路的安全機制。如果您的 `.env` 設為 `BINANCE_TESTNET=false`，但正式期貨帳戶中沒有入金，系統為了保護您會拒絕模擬下單。您可以將 `BINANCE_TESTNET` 改為 `true`，或在正式帳戶劃轉小額資金。

**Q: 外部數據抓取失敗 (如 DefiLlama 報錯) 會導致系統當機嗎？**
- A: 不會。`SyncExternalDataFetcher` 內建了優雅降級機制 (Graceful Fallback)，如果某個外部 API 掛掉，系統會記錄警告，並使用預設的安全值繼續執行，不會中斷主交易流程。
