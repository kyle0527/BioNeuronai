# 分析模組 — 每日報告系統 (Daily Report)

> **版本**: v2.0
> **更新日期**: 2026-03-27

## 目錄

- [模組概述](#模組概述)
- [檔案結構](#檔案結構)
- [系統架構](#系統架構)
- [核心元件與方法](#核心元件與方法)
- [執行流程 (SOP)](#執行流程-sop)
- [依賴關係](#依賴關係)

---

## 模組概述

`daily_report` 子模組負責自動生成每日的加密貨幣市場分析報告。整合全球市場數據、技術指標、新聞情緒、策略規劃與風險管理，輸出結構化 JSON 與可讀文字報告。為自動化 SOP 的核心元件之一。

主要入口類別 `SOPAutomationSystem`（位於 `__init__.py`）扮演協調者角色，依序呼叫所有子模組完成分析後，委由 `ReportGenerator` 儲存與輸出報告。

---

## 檔案結構

```
daily_report/
├── __init__.py          717 行  主控制器（SOPAutomationSystem）
├── market_data.py       557 行  全球市場與經濟日曆數據收集
├── strategy_planner.py  447 行  市場狀態判斷與策略規劃
├── risk_manager.py      605 行  帳戶風險評估與交易對篩選
├── report_generator.py  289 行  報告格式化與持久化輸出
├── news_sentiment.py    131 行  新聞情緒整合包裝
├── models.py            133 行  Dataclass 資料模型定義
└── README.md                    本文件
```

**總計**: 2,879 行

---

## 系統架構

```
SOPAutomationSystem (__init__.py)
│
├─ execute_daily_premarket_check()   主要 SOP 入口（2 大步驟）
│   ├─ Step 1: _check_market_environment()
│   │   ├─ MarketDataCollector.get_global_market_data()
│   │   ├─ MarketDataCollector.check_economic_calendar()
│   │   └─ NewsSentimentAnalyzer.perform_ai_news_analysis()
│   └─ Step 2: _prepare_trading_plan()   ← 20 子步驟詳細版
│       ├─ 步驟 1-6:  StrategyPlanner（分析→評估→匹配→配置→驗證→確認）
│       ├─ 步驟 7-12: RiskManager（帳戶→風險參數→波動率→持倉→頻率→整合）
│       ├─ 步驟 13-17: RiskManager（掃描交易對→流動性→波動率相容→過濾→排序）
│       └─ 步驟 18-20: 回測驗證→每日限額→最終確認
│
└─ run_full_report()                 完整 4 段報告入口
    ├─ 【1/4】關鍵字系統報告（KeywordManager.print_report）
    ├─ 【2/4】技術分析（generate_technical_analysis，需提供 klines）
    ├─ 【3/4】全球市場數據（MarketDataCollector）
    └─ 【4/4】每日開盤前報告（execute_daily_premarket_check）
```

---

## 核心元件與方法

### `__init__.py` — 717 行

#### `SOPAutomationSystem`

主控制器，初始化時注入 `BinanceFuturesConnector`（由環境變數決定是否啟用帳戶功能）。

**`__init__()`**

- 建立 `BinanceFuturesConnector`（讀取 `BINANCE_API_KEY` / `BINANCE_API_SECRET` / `BINANCE_TESTNET`）
- 初始化所有子模組（`MarketDataCollector`、`StrategyPlanner`、`RiskManager`、`ReportGenerator`）
- 延遲載入 `CryptoNewsAnalyzer` 並注入 `NewsSentimentAnalyzer`

**`execute_daily_premarket_check() -> Dict`**
主要 SOP 入口，依序執行：

1. `_check_market_environment()` — 全球市況 + 情緒 + 經濟日曆
2. `_prepare_trading_plan()` — 20 步驟策略與風控規劃
3. `_assess_overall_readiness()` — 綜合評估與交易建議
4. 自動呼叫 `ReportGenerator.save_check_results()` 儲存 JSON

**`run_full_report(klines, symbol, current_price) -> str`**
完整 4 段式報告，適合手動診斷使用：

- `klines` 為可選參數；若提供則執行技術分析（市場狀態/成交量/微觀結構）
- 同時列印至 stdout 並回傳完整文字

**`generate_technical_analysis(klines, symbol, current_price) -> Dict`**
整合三個分析器的技術輸出：

- `MarketRegimeDetector` → `regime_report` + `regime_recommendation`
- `VolumeProfileCalculator` → `volume_profile_report`
- `MarketMicrostructure` → `microstructure_report`

**`_prepare_trading_plan()` — 20 步驟詳細版**

| 階段             | 步驟  | 執行動作                              |
| ---------------- | ----- | ------------------------------------- |
| 第一階段：策略   | 1-2   | 市場狀態分析 + 策略評估               |
|                  | 3-4   | 策略匹配 + 參數配置                   |
|                  | 5-6   | 適用性驗證 + 最終策略選定             |
| 第二階段：風控   | 7-8   | 帳戶分析 + 基礎風險參數               |
|                  | 9-10  | 波動率調整 + 持倉管理                 |
|                  | 11-12 | 交易頻率 + 風險整合                   |
| 第三階段：交易對 | 13-15 | 掃描交易對 + 流動性分析 + 波動率相容  |
|                  | 16-17 | 風險過濾 + 優先級排序                 |
| 第四階段：驗證   | 18    | 回測驗證（`NOT_IMPLEMENTED`，跳過） |
|                  | 19    | 計算每日損失限額                      |
|                  | 20    | 最終計劃驗證                          |

**其他方法**

- `_assess_overall_readiness(market, plan)` — 輸出 `market_condition`、`recommendation`、`readiness_score`
- `_perform_final_plan_validation(backtest, strategy, suitability)` — 回傳 `status`、`score`（0-10）
- `generate_daily_report()` — 委派至 `ReportGenerator.generate_daily_report()`
- `_dataclass_to_dict(obj)` — 遞迴將 dataclass 轉為可序列化 dict

---

### `market_data.py` — 557 行

#### `MarketDataCollector`

**公開方法**

| 方法                          | 說明                                                    |
| ----------------------------- | ------------------------------------------------------- |
| `get_global_market_data()`  | 整合全球股市、恐慌貪婪指數、幣安市場情緒，回傳完整 dict |
| `check_economic_calendar()` | 彙整未來重大事件列表（資金費率、季合約交割、FOMC）      |

**私有方法（內部數據來源）**

| 方法                                | 資料來源                                         |
| ----------------------------------- | ------------------------------------------------ |
| `_get_global_stock_indices()`     | Yahoo Finance（S&P500、DJI、NASDAQ、歐股、日股） |
| `_get_fear_greed_index()`         | Alternative.me API                               |
| `_get_binance_market_sentiment()` | Binance 永續合約長空比                           |
| `_get_binance_funding_events()`   | 內建排程（每 8 小時結算）                        |
| `_get_binance_delivery_events()`  | 內建排程（季度交割日）                           |
| `_get_macro_events()`             | 內建 FOMC 排程（至 2026 年底）                   |
| `_analyze_global_stock_trends()`  | 彙整多市場漲跌幅                                 |
| `_analyze_regional_market()`      | 分區域（美/歐/亞）市場評估                       |
| `_classify_market_trend()`        | 根據均值漲跌幅分類趨勢                           |
| `_analyze_crypto_sentiment()`     | 整合幣安長空比與恐慌指數                         |
| `_classify_crypto_sentiment()`    | Fear & Greed 數值 → 文字標籤                    |
| `_build_market_data_response()`   | 組裝最終回傳 dict                                |

---

### `strategy_planner.py` — 447 行

#### `StrategyPlanner`

**`analyze_current_market_condition() -> MarketCondition`**
抓取 Binance 1H K 線 200 根，傳入 `MarketRegimeDetector`，回傳 `MarketCondition`（condition / volatility / trend / strength）。

**`evaluate_strategy_performance() -> StrategyPerformance`**
從 `StrategySelector` 獲取各策略預期勝率與獲利因子，回傳最佳策略名稱與績效指標。

**`match_strategy_to_market(market_condition) -> Dict`**
根據波動率與趨勢配對策略：

- `EXTREME` / `HIGH` → BreakoutStrategy
- `LOW` → MeanReversionStrategy
- 其他 → 依趨勢方向選擇

回傳 `recommended`（策略名）與 `match_score`（0-10）。

**`configure_strategy_parameters(strategy_name) -> Dict`**
生成該策略的預設運行參數（止損 ATR 倍數、持倉比例等）。

**`verify_strategy_suitability(strategy_match, market_condition) -> Dict`**
多維度驗證策略適用性，回傳 `status`（SUITABLE / MARGINAL / UNSUITABLE）、`confidence`（0-1）、`score`（0-10）、`risks` 清單。

**`finalize_strategy_selection(strategy_match, suitability) -> Dict`**
彙整最終策略選擇，回傳含 `name`、`confidence`、`parameters`、`status`、`score`、`risks` 的完整結果。

**`perform_plan_backtest() -> Dict`**

> ⚠️ **未實現**：固定回傳 `status: "NOT_IMPLEMENTED"`，`annual_return / max_drawdown / sharpe_ratio / win_rate` 均為 `None`。

**私有輔助方法**

- `_map_regime_to_condition(regime)` — Regime 枚舉 → condition 字串
- `_map_volatility_regime(vol_regime)` — VolatilityRegime → LOW/MEDIUM/HIGH/EXTREME
- `_map_trend_direction(direction)` — int(1/-1/0) → UPTREND/DOWNTREND/SIDEWAYS
- `_get_suitability_recommendation(status)` — status → 建議文字

---

### `risk_manager.py` — 605 行

#### `RiskManager`

**帳戶與風險參數**

| 方法                                                        | 說明                                                            |
| ----------------------------------------------------------- | --------------------------------------------------------------- |
| `analyze_account_funds()`                                 | 讀取 Binance 帳戶餘額/可用資金/未實現損益，評級 LOW/MEDIUM/HIGH |
| `calculate_base_risk_parameters(account_analysis)`        | 計算單筆可承受虧損 %                                            |
| `adjust_risk_for_volatility(base_risk, market_condition)` | 依波動率動態調整風險（極端波動時降低持倉上限）                  |
| `configure_position_management(max_positions)`            | 設定最大同時持倉數與相關規則                                    |
| `calculate_trading_frequency(market_condition)`           | 計算每日最大交易次數                                            |
| `integrate_risk_parameters(...)`                          | 整合上述結果，回傳 `RiskParameters` dataclass                 |

**交易對管理**

| 方法                                                    | 說明                                                              |
| ------------------------------------------------------- | ----------------------------------------------------------------- |
| `scan_available_trading_pairs()`                      | 掃描 Binance 全部 USDT 永續合約，取得 24h 量                      |
| `analyze_liquidity_metrics(available_pairs)`          | 依 24h 交易量 > 10 億/1 億分級 HIGH/MEDIUM/LOW                    |
| `check_volatility_compatibility(liquidity_analysis)`  | 過濾與市場波動率不相容的交易對                                    |
| `apply_risk_filters(volatility_match, risk_params)`   | 套用全部風險過濾條件                                              |
| `prioritize_trading_pairs(risk_filtered)`             | BTC/ETH 設主要，其他高流動性為備用，回傳 `TradingPairsPriority` |
| `calculate_comprehensive_daily_limits(account, risk)` | 計算每日最大虧損金額（USD）與其他每日限制                         |

---

### `report_generator.py` — 289 行

#### `ReportGenerator`

**建構**: `ReportGenerator(data_dir="sop_automation_data")`

| 方法                                       | 說明                                                                |
| ------------------------------------------ | ------------------------------------------------------------------- |
| `generate_daily_report()`                | 讀取最新 JSON，呼叫 `_build_report_text()` 輸出可讀文字           |
| `save_check_results(results)`            | 將結果儲存為 `sop_automation_data/sop_check_YYYYMMDD_HHMMSS.json` |
| `generate_summary(results)`              | 生成簡短摘要文字                                                    |
| `_build_report_text(result, check_time)` | 組裝市場環境 / 交易計劃 / 風控 / 評估四區段報告文字                 |
| `_get_latest_check_result()`             | 掃描 `data_dir` 找最新 JSON 檔                                    |
| `_convert_to_serializable(obj)`          | 遞迴轉換 datetime / dataclass 為 JSON 可序列化格式                  |
| `_format_sentiment(sentiment)`           | float → 情緒文字（含 emoji）                                       |
| `_format_economic_events(events)`        | 事件列表 → 格式化字串                                              |
| `_format_news_analysis(news)`            | 新聞分析 dict → 可讀字串                                           |
| `_format_risk_parameters(risk)`          | 風險參數 → 可讀字串                                                |
| `_format_trading_pairs(pairs)`           | 交易對列表 → 可讀字串                                              |
| `_format_daily_limits(limits)`           | 每日限額 dict → 可讀字串                                           |

---

### `news_sentiment.py` — 109 行

#### `NewsSentimentAnalyzer`

包裝 `CryptoNewsAnalyzer`，**必須傳入已初始化的實例**（不接受 `None`）。

| 方法                                              | 說明                                                                                          |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `__init__(news_analyzer)`                       | `news_analyzer` 為 `None` 時直接 `raise RuntimeError`                                   |
| `perform_ai_news_analysis(symbol, hours)`       | 呼叫 `CryptoNewsAnalyzer.analyze_news()`；失敗時 `raise RuntimeError`                     |
| `assess_market_status_from_news(news_analysis)` | `news_analysis` 為 `None` 時 `raise RuntimeError`；否則回傳 BULLISH / BEARISH / NEUTRAL |
| `_extract_major_events(analysis)`               | 從分析結果提取重大事件列表                                                                    |

> **無 mock / fallback**：分析器不可用或分析失敗時直接拋出例外，由呼叫端（`execute_daily_premarket_check()`）接收並處理。

---

### `models.py` — 133 行

所有模組共用的 `@dataclass` 定義：

| 類別                       | 欄位                                                                                                                     | 說明                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `MarketEnvironmentCheck` | timestamp, us_futures, asian_markets, european_markets, crypto_sentiment, economic_events, news_analysis, overall_status | Step 1 輸出                                                        |
| `TradingPlanCheck`       | timestamp, selected_strategy, risk_parameters, trading_pairs, daily_limits, overall_status                               | Step 2 輸出                                                        |
| `MarketCondition`        | condition, volatility, trend, strength(0-1)                                                                              | 由 `StrategyPlanner` 產生                                        |
| `StrategyPerformance`    | best_strategy, win_rate, profit_factor, max_drawdown, sample_size                                                        | 由 `StrategyPlanner` 產生                                        |
| `RiskParameters`         | single_trade_risk, daily_max_loss, max_positions, max_daily_trades, adjustment_factor                                    | 由 `RiskManager` 產生                                            |
| `TradingPairsPriority`   | primary, backup, excluded                                                                                                | 由 `RiskManager` 產生，`__post_init__` 確保 excluded 不為 None |
| `DailyReport`            | report_time, report_version, report_type, market_environment, trading_plan, overall_assessment                           | 完整報告容器，含 `to_dict()` 與靜態 `_dataclass_to_dict()`     |

---

## 執行流程 (SOP)

### 簡易執行（programmatic）

```python
from bioneuronai.analysis.daily_report import SOPAutomationSystem

system = SOPAutomationSystem()

# 執行完整 SOP（含儲存 JSON）
results = system.execute_daily_premarket_check()

# 或執行含技術分析的 4 段完整報告
report_text = system.run_full_report(klines=klines_list, symbol="BTCUSDT")
```

### 20 步驟詳細流程（`_prepare_trading_plan` 內部）

```
【第一階段：策略分析與選擇】
  步驟 1-2  → analyze_current_market_condition()  +  evaluate_strategy_performance()
  步驟 3-4  → match_strategy_to_market()  +  configure_strategy_parameters()
  步驟 5-6  → verify_strategy_suitability()  +  finalize_strategy_selection()

【第二階段：風險管理與資金配置】
  步驟 7-8  → analyze_account_funds()  +  calculate_base_risk_parameters()
  步驟 9-10 → adjust_risk_for_volatility()  +  configure_position_management()
  步驟11-12 → calculate_trading_frequency()  +  integrate_risk_parameters()

【第三階段：交易對篩選與優化】
  步驟13-15 → scan_available_trading_pairs()  +  analyze_liquidity_metrics()
              +  check_volatility_compatibility()
  步驟16-17 → apply_risk_filters()  +  prioritize_trading_pairs()

【第四階段：回測驗證與最終確認】
  步驟 18   → perform_plan_backtest()      ⚠️ NOT_IMPLEMENTED，跳過
  步驟 19   → calculate_comprehensive_daily_limits()
  步驟 20   → _perform_final_plan_validation()
```

### 報告輸出

| 輸出 | 位置                                                   | 內容             |
| ---- | ------------------------------------------------------ | ---------------- |
| JSON | `sop_automation_data/sop_check_YYYYMMDD_HHMMSS.json` | 完整結構化結果   |
| 文字 | stdout + 回傳值                                        | 可讀的四區段報告 |

---

## 依賴關係

### 內部依賴

| 模組                                                                 | 用途                                                              |
| -------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `bioneuronai.analysis.news.CryptoNewsAnalyzer`                     | 新聞情緒分析（可選，不可用時降級為 mock）                         |
| `bioneuronai.analysis.market_regime.MarketRegimeDetector`          | K 線市場狀態識別（StrategyPlanner + generate_technical_analysis） |
| `bioneuronai.analysis.feature_engineering.VolumeProfileCalculator` | 成交量分布（generate_technical_analysis）                         |
| `bioneuronai.analysis.feature_engineering.MarketMicrostructure`    | 微觀結構（generate_technical_analysis）                           |
| `bioneuronai.analysis.keywords.manager.KeywordManager`             | 關鍵字報告（run_full_report 第一段）                              |
| `bioneuronai.strategies.selector.core.StrategySelector`            | 策略評估（StrategyPlanner.evaluate_strategy_performance）         |
| `bioneuronai.data.binance_futures.BinanceFuturesConnector`         | Binance API（帳戶查詢與 K 線抓取）                                |

### 外部依賴

| 套件 / API   | 用途                                            |
| ------------ | ----------------------------------------------- |
| `requests` | Yahoo Finance、Alternative.me、Binance REST API |
| `logging`  | 全模組統一日誌輸出                              |

### 環境變數

| 變數                   | 預設值     | 說明                                   |
| ---------------------- | ---------- | -------------------------------------- |
| `BINANCE_API_KEY`    | `""`     | Binance API Key，空值時僅可用公開端點  |
| `BINANCE_API_SECRET` | `""`     | Binance API Secret                     |
| `BINANCE_TESTNET`    | `"true"` | `"false"` 表示主網，其餘均為 testnet |

---

> 上層目錄：[analysis README](../README.md)
