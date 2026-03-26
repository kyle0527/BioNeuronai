# 分析模組 — 每日報告系統 (Daily Report)

> **版本**: v1.0
> **更新日期**: 2026-03-19

## 目錄
- [模組概述](#模組概述)
- [系統架構](#系統架構)
- [核心元件與類別](#核心元件與類別)
- [執行流程 (SOP)](#執行流程-sop)
- [依賴關係](#依賴關係)

## 模組概述
`daily_report` 子模組負責自動生成每日的加密貨幣市場分析報告。它整合了總體經濟數據、市場技術指標、新聞情緒、策略規劃與風險管理，並輸出結構化的 JSON 與易讀的文字報告。此模組為自動化標準作業程序 (SOP) 的重要組成部分。

## 系統架構
本系統將報告生成流程拆分為數個專責元件，最後由 `ReportGenerator` 彙整輸出。
- **資料獲取**: 收集外部市場與價格資料 (`market_data.py`).
- **情緒分析**: 整合新聞分析結果 (`news_sentiment.py`).
- **策略與風險**: 根據市場狀態產生建議與限制 (`strategy_planner.py`, `risk_manager.py`).
- **報告生成**: 彙整所有結果並持久化 (`report_generator.py`).

## 核心元件與類別

### `report_generator.py`
負責文字報告的格式化與 JSON 結果的儲存。
- **`ReportGenerator`**:
  - `generate_daily_report()`: 讀取最新檢查結果並產生格式化文字報告。
  - `save_check_results(results)`: 將報告結果儲存為 JSON (預設路徑 `sop_automation_data/sop_check_YYYYMMDD_HHMMSS.json`)。
  - `generate_summary(results)`: 產生精簡的摘要。

### `market_data.py`
全球市場資料收集器。
- **`MarketDataCollector`**:
  - 獲取美股期貨、歐洲市場、亞洲市場的狀態。
  - 收集即將發生的經濟事件 (Economic Events)。
  - 從 Binance / CoinGecko 獲取加密貨幣價格數據。

### `news_sentiment.py`
新聞情緒整合器。
- **`NewsSentimentAnalyzer`**:
  - 委託 `CryptoNewsAnalyzer` 執行新聞抓取。
  - 將複雜的分析結果簡化為報告所需的格式 (情緒評分、正負面新聞數量)。

### `strategy_planner.py`
基於市場資料的策略規劃。
- **`StrategyPlanner`**:
  - 分析市場趨勢 (牛市/熊市/震盪)。
  - 選擇適合當前市場環境的策略。
  - 篩選推薦的交易對。

### `risk_manager.py`
報告專用的風險管理分析。
- **`ReportRiskManager`**:
  - 計算帳戶健康度與可用保證金。
  - 設定每日交易限制 (最大虧損、單筆上限、交易次數)。
  - 產出風險參數建議。

### `models.py`
Pydantic/Dataclass 資料模型定義，包含 `DailyReport`, `MarketCondition` 等結構。

## 執行流程 (SOP)
在自動化腳本中，每日報告的生成通常遵循以下步驟：
1. `MarketDataCollector` 獲取全球市況。
2. `NewsSentimentAnalyzer` 計算當日情緒分數。
3. 結合上述資訊，`StrategyPlanner` 與 `ReportRiskManager` 產生交易建議。
4. `ReportGenerator` 收集所有 Dict 結構，呼叫 `save_check_results` 儲存 JSON。
5. `generate_daily_report` 輸出可讀報告，傳送至終端機或 Telegram 機器人。

## 依賴關係
- **內部依賴**: `bioneuronai.analysis.news.CryptoNewsAnalyzer` (用於情緒), `bioneuronai.data.BinanceFuturesConnector` (用於價格).
- **外部 API**: Yahoo Finance, CoinGecko, Binance.
