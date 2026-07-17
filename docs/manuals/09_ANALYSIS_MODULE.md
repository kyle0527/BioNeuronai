# 分析模組操作手冊

> **套件版本**：v2.1
> **更新日期**：2026-07-12
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)

---

## 目錄

1. [適用範圍](#1-適用範圍)
2. [這個功能實際在做什麼分析](#2-這個功能實際在做什麼分析)
3. [CLI 操作](#3-cli-操作)
4. [UI / API 操作](#4-ui--api-操作)
5. [分析結果如何影響系統（雙主線）](#5-分析結果如何影響系統雙主線)
6. [常見問題與除錯](#6-常見問題與除錯)

---

## 1. 適用範圍

目前這份手冊對應的是分析模組的三大核心操作：
- **新聞情緒分析 (`news`)**：抓取最新新聞、計算情緒分數、關鍵字過濾。
- **每日交易計畫與宏觀掃描 (`plan`)**：整合恐慌貪婪指數、全球市值、DeFi TVL 等外部數據，給出總體市場狀態建議。
- **進場前驗核 (`pretrade`)**：綜合技術面、基本面（新聞/RAG）、資金管理，執行 6 點安全檢查。

---

## 2. 這個功能實際在做什麼分析

### 1. 新聞情緒分析 (News Analysis)

新聞模組是**戰略資訊層**：一般程式負責來源、抓取、去重、原始資料歸檔、事件記憶、重要性衰減與到期。啟動時抓取一次；持續自主運作時在本地時間每小時第 5 分鐘更新。完整新聞只在更新時處理，平常交易決策只讀濃縮事件記憶。策略模組獨立以市場資料形成戰術候選；統一 AI 只負責綜合判斷與最終決定。

| 項目 | 現行程式事實 | 已確認目標規格 |
|------|-------------|----------------|
| 幣圈來源 | **CoinDesk RSS** | 幣圈與產業新聞 |
| 宏觀來源 | **Google News RSS 的固定宏觀查詢** | 戰爭、制裁、能源、Fed/FOMC、通膨、衰退、美國／歐洲經濟、ECB 等 |
| 來源數 | **僅 2 個入口** | 一個幣圈、一個宏觀 |
| 來源失敗 | 任一來源即該輪明確錯誤 | 不降級、不以部分新聞或假性中性結論繼續 |

上表是目前程式的正式契約；`news` 指令會在同一輪抓取兩類新聞，任一來源無法取得或解析時即失敗。

每篇文章會保留實際發布時間、來源、標題、RSS 摘要、URL、原文語言與關鍵字／事件標籤，正式即時根目錄為 `data/bioneuronai/trading/sop/`。事件合約保存初始重要性、最低保留重要性、有效期與衰減方式。事件規則不儲存固定多空；AI 在每次交易決策時依事件記憶、策略與市場狀態自行判斷方向。

### 2. 宏觀市場掃描 / 每日計畫 (Daily Plan)
- 呼叫多個外部 API（Alternative.me, CoinGecko, DefiLlama）。
- 匯總市場總體情緒（如恐慌貪婪指數）、市場資金流向（穩定幣供應、DeFi 鎖倉量）。
- 結合 Binance 歷史 K 線，判斷目前的「大盤體制」（如：強勢上漲、高波動震盪）。
- 生成一份包含具體建議的每日交易計畫書。

### 3. 進場前驗核 (Pre-trade Check)

在真實下單前，最後一道防線。由 `PreTradeCheckSystem`（`planning/pretrade_automation.py`）執行，風險計算使用**內部 `RiskCalculation`** 與 **`AIConfidenceCalibrator`**，輸出 `order_parameters`（含 quantity、止損止盈）。**此路徑不直接呼叫 `RiskManager.calculate_position_size()`**（`RiskManager` 主要服務 `TradingEngine`）。

依序檢查要點：

1. **信心度檢查**：AI 或策略訊號是否達標（含 calibrator 動態乘數）。
2. **回撤與風險檢查**：帳戶是否處於過大回撤中。
3. **過度交易檢查**：是否超過每日最大交易次數。
4. **資金與保證金檢查**：可用餘額是否足夠。
5. **RAG / 新聞防護**：以**事件合約重要性**與 HACK／WAR／REGULATION 等風險類型判斷是否需謹慎；**不**用規則 signed 多空分數（該欄位現役固定 0）。  
6. **參數檢查**：槓桿與止損設定是否合理。

> 新聞模組不輸出 LONG／SHORT。`NewsAdapter.get_direction_bias` 與 strategy fusion 均固定 `NEUTRAL`，只帶 importance／strength。

---

## 3. CLI 操作

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
CLI 會列出抓到的新聞標題、各自的情緒分數，以及最終的綜合情緒評分，並顯示成功寫入知識庫的筆數。它會同時讀取 CoinDesk 與 Google News RSS；任一來源失敗會明確報錯，而不是回傳空新聞。

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

**預期輸出：**
會依序印出 6 點檢查狀態（`PROCEED` / `CAUTION` / `REJECT`）。如果最終被拒絕，會明確給出原因（例如：期貨錢包可用餘額不足或新聞/RAG 風險過高）。

---

## 4. UI / API 操作

分析模組的功能已經完全封裝為 FastAPI 的 REST 端點，可以透過 Swagger UI (`http://localhost:8000/docs`) 或自訂的前端直接呼叫。

### 1. 新聞情緒分析 API
**端點**：`POST /api/v1/news`

**請求範例 (JSON)**：
```json
{
  "symbol": "BTCUSDT",
  "max_items": 10
}
```
**回傳**：包含新聞情緒、文章數、標題、關鍵字與操作建議。正式來源契約完成後，任一指定來源抓取失敗必須回傳明確錯誤狀態；不得改用未列入契約的來源，也不得以空文章偽裝成功。

### 2. 每日計畫 API

目前 FastAPI 主線沒有暴露 `/api/v1/plan`。每日計畫請使用 CLI：

```powershell
python main.py plan --symbol BTCUSDT --output daily_plan.json
```

若未來新增 REST route，需同步更新本節與 [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md)。

### 3. 進場前驗核 API
**端點**：`POST /api/v1/pretrade`

**請求範例 (JSON)**：
```json
{
  "symbol": "BTCUSDT",
  "action": "long"
}
```
**回傳**：包含 overall assessment、風險理由與各檢查點明細。`REJECT` 是有效風控結果，不代表 API 失敗。

---

## 5. 分析結果如何影響系統（雙主線）

分析產出會進入不同執行路徑，請對照 [04_CLI_OPERATION.md](04_CLI_OPERATION.md) §2：

### 新聞、策略與 AI 的固定邊界

- 事件規則目前只產生 `event_importance`、有效期與事件描述；既有 `event_score` 固定為 0，避免舊規則繼續直接左右交易方向。
- `get_direction_bias()` 在事件存在時仍使用相容欄位，但固定回傳 `NEUTRAL`。
- `AutonomousOperator` 的 `ai_input_v2` 將 `news_memory`、`strategy`、`market` 分開保存；只有 AI 推論時才融合。
- 決策帳本保存文章 ID 與新聞更新摘要，不重複保存或每輪重讀完整新聞。

固定責任邊界：**新聞模組管理資訊與記憶；策略模組管理戰術計算與策略保存／切換；統一 AI 只做判斷和最終決定。** 三者不互相覆蓋，新聞或策略都不能繞過 AI 直接下單。

**主線 A**：`TradingEngine._fuse_signals()` 在即時 tick 中帶入 event_score。
**主線 B**：`autonomous` 直接讀濃縮 `news_memory`、獨立策略候選與市場 patch，交由 shared InferenceEngine 產生最終 65 維決策；原始新聞不進入平常循環。

### Plan → 策略選擇 / 自主規劃

- 每日計畫的市場體制（Regime）影響 `StrategySelector` 權重建議。
- `autonomous` 每輪會跑 plan，結果寫入 ledger 的 `plan_status`、`plan_execution_ready`。

### Pretrade → 兩條執行路徑

| 消費者 | 如何使用 pretrade 輸出 |
|--------|------------------------|
| **主線 A** `TradingEngine` | 引擎內嵌 `PreTradeCheckSystem`；`paper-live` / testnet / live 決策流程一致，僅 connector 不同 |
| **主線 B** `AutonomousOperator` | 對候選 symbol 跑 pretrade；adaptation 依 summary 決定 `final_action` |

**主線 B 執行層（2026-06-15）**：`--execute-paper` **優先**採 pretrade `order_parameters.quantity`（× `risk_multiplier`）；quantity 無效時 fallback `paper_notional_fraction`。止損/止盈仍從 `order_parameters` 讀取。詳見 [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md) §9。

---

## 6. 常見問題與除錯

**Q: 為什麼新聞分析 (`news`) 總是回傳 0 分？**
- A: 先分辨兩種情況：兩個來源都成功但近期沒有符合條件的文章，才是有效的零篇／中性；CoinDesk 或 Google News RSS 任一抓取失敗都是明確錯誤，不能降級。

**Q: Pre-trade 一直被 Reject，說「Futures 餘額為 0」？**
- A: 這是 Binance 正式網路的安全機制。如果您的 `.env` 設為 `BINANCE_TESTNET=false`，但正式期貨帳戶中沒有入金，系統為了保護您會拒絕模擬下單。您可以將 `BINANCE_TESTNET` 改為 `true`，或在正式帳戶劃轉小額資金。

**Q: 外部數據抓取失敗 (如 DefiLlama 報錯) 會導致系統當機嗎？**
- A: 交易主流程不應使用預設安全值繼續產生判斷。外部資料不可用時，分析結果需標記為 `DATA_UNAVAILABLE` 或 `ERROR`，自動交易流程應被阻擋；只有非交易核心的展示或效能層可以在明確標示原因後受限運作。
