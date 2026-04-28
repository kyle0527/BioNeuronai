# BioNeuronAI 資料管線與儲存綱要 (Data Pipeline & Schema)

> 更新日期：2026-04-24  
> 目的：定義 v2.1 系統中資料的流動方式、儲存分層策略，以及核心的資料庫綱要。本文件取代舊版的 Data Storage 規劃。

## 🌊 核心資料流動 (Data Pipeline)

BioNeuronAI 的資料處理嚴格遵循「單向資料流」與「單一事實來源 (Single Source of Truth)」原則：

```text
[外部來源 Binance API / News RSS]
       │
       ▼ (data/ 模組負責抓取與正規化)
[Schemas (src/schemas/)] ──▶ 保證所有資料結構的型別安全 (Pydantic)
       │
       ▼ (存入資料庫與快取)
[Hot/Warm/Cold 儲存層]
       │
       ▼ (由 planning/ 提取)
[TradingPlanController / PretradeAutomation]
       │
       ▼ (將決策轉交執行)
[TradingEngine (core/)] ──▶ 產生 Signal 並執行訂單
       │
       ▼ (記錄交易結果)
[Trading.db & VirtualAccount]
```

---

## 🗄️ 儲存分層架構 (Storage Tiers)

為了兼顧回測效能與硬碟空間，系統採用三層資料架構：

### 1. 熱資料 (Hot Data - Memory)
*   **位置**：Python 記憶體中（如 `TradingEngine.signals_history`, `_klines_cache`）
*   **生命週期**：進程運行期間。
*   **用途**：當日即時決策、極低延遲的特徵工程計算。

### 2. 溫資料 (Warm Data - SQLite)
*   **位置**：`data/bioneuronai/trading/engine/trading.db`
*   **生命週期**：近期歷史（通常保留 90 天），由 `DatabaseManager` 管理。
*   **用途**：短期回顧、統計分析、每日報告產生。

### 3. 冷資料 (Cold Data - Archived)
*   **位置**：`trading_data/backups/` 內的 JSONL 檔案與壓縮檔。
*   **生命週期**：永久保存。
*   **用途**：長期回測語料、AI 模型訓練資料。

---

## 📊 核心 SQLite 綱要 (trading.db)

系統依賴 `trading.db` 作為溫資料的主力。以下為主要資料表結構與其職責：

### `trades` (交易紀錄表)
負責記錄所有已執行的交易，作為 PnL 計算與風控的基礎。
*   `id`: INTEGER PRIMARY KEY
*   `timestamp`: DATETIME
*   `symbol`: VARCHAR (交易對，如 BTCUSDT)
*   `side`: VARCHAR (BUY / SELL)
*   `entry_price`: REAL
*   `exit_price`: REAL (平倉時更新)
*   `size`: REAL
*   `pnl`: REAL (已實現損益)
*   `strategy`: VARCHAR (負責生成該訂單的策略來源)

### `risk_stats` (風控統計快照)
取代舊版 `RiskManager` 的文件儲存，直接由 `risk_management` 模組透過 DB 寫入每日狀態。
*   `date`: DATE PRIMARY KEY
*   `total_trades`: INTEGER
*   `win_rate`: REAL
*   `max_drawdown`: REAL
*   `sharpe_ratio`: REAL

### `news_analysis` (新聞分析快取)
配合 RAG 系統儲存近期新聞情緒，避免重複計算。
*   `id`: INTEGER
*   `timestamp`: DATETIME
*   `title`: TEXT
*   `sentiment_score`: REAL
*   `expires_at`: DATETIME (支援事件合約的時間驗證)

---

## 🔒 資料一致性保證

1.  **Pydantic 優先**：所有寫入 DB 的操作，必須先通過 `src/schemas/` 的 Pydantic 模型驗證，嚴禁使用未定義結構的 dict 直寫。
2.  **雙寫容錯**：重要交易紀錄除寫入 `trading.db` 外，會同步 Append 到 JSONL 備份檔，確保資料庫鎖死時仍有日誌可查。
3.  **無狀態風控**：風險計算依賴 DB 中的歷史交易紀錄聚合而成，而非依賴記憶體中的累加器，確保重啟不丟失風控狀態。
