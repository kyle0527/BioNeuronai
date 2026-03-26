# 分析模組 — 每日報告系統 (Daily Report)

> **版本**: v1.0
> **更新日期**: 2026-03-19

## 目錄
- [模組概述](#模組概述)
- [系統架構](#系統架構)
- [核心元件與詳細方法](#核心元件與詳細方法)
- [執行流程 (SOP)](#執行流程-sop)
- [依賴關係](#依賴關係)

## 模組概述
`daily_report` 子模組負責自動生成每日的加密貨幣市場分析報告。它整合了總體經濟數據、市場技術指標、新聞情緒、策略規劃與風險管理，並輸出結構化的 JSON 與易讀的文字報告。此模組為自動化標準作業程序 (SOP) 的重要組成部分。

## 系統架構
本系統將報告生成流程拆分為數個專責元件，最後由 `ReportGenerator` 彙整輸出。總計包含 7 個 Python 檔案，共 2,879 行代碼。
- **主流程入口**: 初始化所有組件並管理 SOP 流程 (`__init__.py`).
- **資料獲取**: 收集外部市場與經濟日曆資料 (`market_data.py`).
- **情緒分析**: 整合新聞分析結果與綜合情緒 (`news_sentiment.py`).
- **策略與風險**: 根據市場狀態產生交易對與限制 (`strategy_planner.py`, `risk_manager.py`).
- **報告生成**: 彙整所有結果並持久化輸出 (`report_generator.py`).
- **資料模型**: 定義 Pydantic / Dataclass 模型 (`models.py`).

## 核心元件與詳細方法

### `__init__.py` (717 行)
包含模組導出與 SOP 流程控制器。
- **`SOPAutomationSystem`**: (若此類別位於此，則負責呼叫所有子模組來產生日報的協調者角色)。
- 統一對外導出所有報告相關模型與產生器。

### `market_data.py` (557 行)
負責向外請求大盤資訊，包含 Yahoo Finance 與 Binance 接口。
- **`MarketDataCollector`**:
  - `get_global_market_data()`: 透過 Yahoo Finance API 獲取美股 (S&P500, DJI, NASDAQ)、歐股與日股的隔夜漲跌幅，並結合 Crypto Fear & Greed Index 輸出全球市場綜合數據。
  - `check_economic_calendar()`: 彙整未來的重大事件，包含 Binance 永續合約資金費率結算、季度合約交割日，以及美國 FOMC 利率決議排程（已內建至 2026 年底）。

### `strategy_planner.py` (447 行)
負責判斷當前盤面，並給予最適合的交易策略。
- **`StrategyPlanner`**:
  - `analyze_current_market_condition()`: 抓取 Binance 1H K 線 200 根，傳入 `MarketRegimeDetector`，判斷目前處於「牛市/熊市/震盪」與「波動率高低」，回傳 `MarketCondition` 模型。
  - `evaluate_strategy_performance()`: 從 `StrategySelector` 獲取各策略的預期勝率與獲利因子。
  - `match_strategy_to_market()`: 根據波動率配對合適的策略（例如 HIGH 對應 BreakoutStrategy，LOW 對應 MeanReversion）。
  - `configure_strategy_parameters()`: 生成該策略的預設運行參數。

### `risk_manager.py` (605 行)
評估帳戶健康度並設定保護機制。
- **`RiskManager`**:
  - `analyze_account_funds()`: 透過帶有 API Key 的 Binance Connector 讀取真實帳戶餘額、可用資金與未實現損益，並給予風險承受度評級 (LOW/MEDIUM/HIGH)。
  - `calculate_base_risk_parameters()` / `adjust_risk_for_volatility()`: 計算單筆交易可承受的虧損百分比，並依據波動率動態調整（極端波動時降低持倉上限）。
  - `scan_available_trading_pairs()` / `analyze_liquidity_metrics()`: 掃描 Binance 上所有 USDT 永續合約，並依據 24 小時交易量大於 10 億/1 億劃分高低流動性。
  - `prioritize_trading_pairs()`: 將 BTC/ETH 設為優先，其他高流動性幣種為備用。

### `report_generator.py` (289 行)
將各模組產生的 `Dict` 結果轉換為可閱讀的報告。
- **`ReportGenerator`**:
  - `generate_daily_report()`: 讀取目錄下最新的檢查結果 JSON，產生包含「市場環境」、「交易計畫建議」、「風險參數」與「綜合評估」的文字報告。
  - `save_check_results(results)`: 將 SOP 執行的結果完整儲存為 JSON，預設路徑 `sop_automation_data/sop_check_YYYYMMDD_HHMMSS.json`。

### `news_sentiment.py` (131 行)
負責抓取與計算加密貨幣專屬的新聞情緒。
- **`NewsSentimentAnalyzer`**:
  - 整合 `CryptoNewsAnalyzer` 算出當日情緒分數 (Sentiment Score)。
  - 提供正負面新聞數量的統計。

### `models.py` (133 行)
定義了上述模組互動所使用的 Pydantic 與 Dataclass 模型，包含 `MarketCondition`, `StrategyPerformance`, `RiskParameters`, `TradingPairsPriority` 與 `DailyReport` 等。

## 執行流程 (SOP)
在自動化腳本 (`bioneuronai.trading.SOPAutomationSystem` 或 `__init__.py` 內部呼叫) 中，每日報告的生成通常遵循以下步驟：
1. **環境檢查**: `MarketDataCollector` 獲取全球市況與經濟事件。
2. **情緒評分**: `NewsSentimentAnalyzer` 透過 `CryptoNewsAnalyzer` 算出當日情緒分數。
3. **盤面與策略**: `StrategyPlanner` 分析 K 線體制，給定推薦策略。
4. **風控設限**: `RiskManager` 取得帳戶資金，設定每日停損金額與流動性交易對。
5. **整合匯出**: `ReportGenerator` 將所有 Dict 結構呼叫 `save_check_results` 儲存，並呼叫 `generate_daily_report` 輸出終端文字。

## 依賴關係
- **內部依賴**:
  - `bioneuronai.analysis.news.CryptoNewsAnalyzer` (用於情緒)
  - `bioneuronai.analysis.market_regime.MarketRegimeDetector` (用於體制識別)
  - `bioneuronai.strategies.selector.core.StrategySelector` (用於策略選擇)
- **外部依賴**: `requests` (Yahoo Finance, CoinGecko, Binance, Alternative.me API).