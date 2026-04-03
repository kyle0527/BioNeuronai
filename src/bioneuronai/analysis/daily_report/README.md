# 分析模組 — 每日報告系統 (Daily Report)

> **路徑**: `src/bioneuronai/analysis/daily_report/`  
> **更新日期**: 2026-04-01  
> **文件焦點**: 子模組內部流程與 API（系統分層請看上層 `analysis/README.md`）

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

---

## 主入口與流程

主入口：`SOPAutomationSystem`（`__init__.py`）

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

## 實作現況（已對齊程式碼）

1. 資料模型採用 `DailyMarketCondition`、`DailyRiskLimits`（非舊名稱）
2. `NewsSentimentAnalyzer` 需注入可用 `CryptoNewsAnalyzer`，初始化失敗會拋錯
3. `StrategyPlanner.perform_plan_backtest()` 仍為 `NOT_IMPLEMENTED`
4. `ReportGenerator` 預設資料夾為 `sop_automation_data/`

---

## 輸出

1. 結構化結果：`sop_automation_data/sop_check_YYYYMMDD_HHMMSS.json`
2. 文字報告：`generate_daily_report()` / `run_full_report()`

---

## 已移除的老舊/錯誤內容

1. 舊模型名稱與舊欄位命名
2. 「失敗時自動 mock/fallback」等與現況不符敘述
3. 固定行數、固定檔案數等易過時資訊
4. 與現行方法不一致的步驟說明

---

> 上層架構說明：`src/bioneuronai/analysis/README.md`
