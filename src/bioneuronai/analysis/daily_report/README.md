# 分析模組 — 每日報告系統 (Daily Report)

> **路徑**: `src/bioneuronai/analysis/daily_report/`  
> **更新日期**: 2026-04-20
> **文件焦點**: 子模組內部流程與 API（系統分層請看上層 [analysis README](../README.md)）

## 目錄

1. [子模組職責](#子模組職責)
2. [檔案結構](#檔案結構)
3. [主入口與流程](#主入口與流程)
4. [實作現況](#實作現況)
5. [輸出](#輸出)
6. [維護邊界](#維護邊界)

---

## 子模組職責

`daily_report` 專注在「每日開盤前 SOP 分析流程編排」：
1. 市場環境檢查
2. 交易計畫準備
3. 報告保存與文字輸出

它是分析層的流程 orchestrator，不負責定義新聞規則與關鍵字知識本體。

---

## 檔案結構

```text
daily_report/
├── __init__.py          # SOPAutomationSystem 主入口
├── models.py            # dataclass：MarketEnvironmentCheck 等
├── market_data.py       # 全球市場與經濟事件收集
├── news_sentiment.py    # 對 CryptoNewsAnalyzer 的封裝
├── strategy_planner.py  # 市場條件與策略規劃
├── risk_manager.py      # 風控參數與交易對篩選
├── report_generator.py  # JSON 保存與文字報告輸出
└── README.md
```

檔案對照：
1. [__init__.py](__init__.py)
2. [models.py](models.py)
3. [market_data.py](market_data.py)
4. [news_sentiment.py](news_sentiment.py)
5. [strategy_planner.py](strategy_planner.py)
6. [risk_manager.py](risk_manager.py)
7. [report_generator.py](report_generator.py)

---

## 主入口與流程

主入口：`SOPAutomationSystem`（[__init__.py](__init__.py)）

主要公開方法：
1. `execute_daily_premarket_check()`：執行 Step1/Step2 並保存結果
2. `run_full_report(klines, symbol, current_price)`：四段式整合輸出
3. `generate_technical_analysis(...)`：市場體制 + 特徵工程
4. `generate_daily_report()`：輸出最新文字報告

核心內部流程：
1. `_check_market_environment()`
2. `_prepare_trading_plan()`（20 子步驟）
3. `_assess_overall_readiness()`

---

## 實作現況

### `models.py`

定義這個子模組自己的 dataclass：
1. `MarketEnvironmentCheck`
2. `TradingPlanCheck`
3. `DailyMarketCondition`
4. `StrategyPerformance`
5. `DailyRiskLimits`
6. `TradingPairsPriority`
7. `DailyReport`

### `market_data.py`

主類：`MarketDataCollector`

主要職責：
1. `get_global_market_data()`
2. `check_economic_calendar()`
3. 全球股市、恐慌貪婪、Binance funding / delivery 事件整理

### `news_sentiment.py`

主類：`NewsSentimentAnalyzer`

主要職責：
1. `perform_ai_news_analysis()`
2. `_extract_major_events()`
3. `assess_market_status_from_news()`

這個檔案只做 daily report 所需的新聞封裝，不重複定義新聞主分析流程；新聞主體仍在上游 [news README](../news/README.md)。

### `strategy_planner.py`

主類：`StrategyPlanner`

主要公開方法：
1. `analyze_current_market_condition()`
2. `evaluate_strategy_performance()`
3. `match_strategy_to_market()`
4. `configure_strategy_parameters()`
5. `verify_strategy_suitability()`
6. `finalize_strategy_selection()`
7. `perform_plan_backtest()`

### `risk_manager.py`

主類：`RiskManager`

主要公開方法：
1. `analyze_account_funds()`
2. `calculate_base_risk_parameters()`
3. `adjust_risk_for_volatility()`
4. `configure_position_management()`
5. `calculate_trading_frequency()`
6. `scan_available_trading_pairs()`
7. `analyze_liquidity_metrics()`
8. `prioritize_trading_pairs()`
9. `calculate_comprehensive_daily_limits()`

### `report_generator.py`

主類：`ReportGenerator`

主要公開方法：
1. `generate_daily_report()`
2. `save_check_results()`
3. `generate_summary()`

重點：
1. 預設資料夾為 `sop_automation_data/`
2. 會把 daily report 結果寫成 JSON
3. 目前也會將市場分析結果寫回 knowledge base

### 當前狀態摘要

1. 資料模型採用 `DailyMarketCondition`、`DailyRiskLimits`
2. `NewsSentimentAnalyzer` 需注入可用 `CryptoNewsAnalyzer`
3. `StrategyPlanner.perform_plan_backtest()` 已接上正式 replay backtest
4. `ReportGenerator.save_check_results()` 已包含知識庫寫回路徑

---

## 輸出

1. 結構化結果：`sop_automation_data/sop_check_YYYYMMDD_HHMMSS.json`
2. 文字報告：`generate_daily_report()` / `run_full_report()`

## 子模組邊界

這個資料夾目前沒有更深一層的 README 子文件，因此細節維護到「檔案與公開方法」這一層為止。

## 維護邊界

1. 這層只描述 daily report 的流程編排與公開方法；新聞規則與關鍵字資料結構請放在各自子模組 README。
2. 不在此文件放固定總行數或覆蓋率，避免和實際檔案漂移。
3. 若 `perform_plan_backtest()` 的回測來源、摘要欄位或驗證邏輯變更，需同步更新「實作現況」與輸出說明。

---

> 上層架構說明：[analysis README](../README.md)
