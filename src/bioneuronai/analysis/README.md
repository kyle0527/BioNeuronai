# 分析模組 (Analysis)

> **路徑**: `src/bioneuronai/analysis/`  
> **更新日期**: 2026-04-01  
> **狀態**: 依目前程式碼重新對齊（上層聚焦架構；子模組細節請看各子 README）

## 模組定位

`analysis` 是 BioNeuronai 的分析層，負責把市場資料、新聞文字與關鍵字訊號轉為可被交易層使用的結構化結果。

上層 README 只描述：
1. 模組切分
2. 模組責任邊界
3. 對外整合入口

子模組內部方法、欄位、限制與資料格式，統一放在各子目錄 README。

---

## 目錄與責任切分

```text
analysis/
├── __init__.py              # 統一導出 analysis 層公開 API
├── __main__.py              # 分析層 CLI 示範入口（--sop / --kw / full）
├── feature_engineering.py   # 市場微結構特徵工程
├── market_regime.py         # 市場體制識別
├── news/                    # 新聞分析與事件評估（含 Analysis -> RAG ingest）
├── keywords/                # 關鍵字匹配、評分、學習回饋
├── daily_report/            # SOP 每日開盤前分析與報告生成
└── image/                   # 圖像相關資源（非本層核心分析流程）
```

### 1) `news/`（新聞理解）
- 負責新聞抓取、情緒/事件判讀、規則評估、預測驗證。
- 分析結果可寫入 RAG（`ingest_news_analysis_with_status`），銜接知識檢索路徑。
- 細節見：`news/README.md`

### 2) `keywords/`（語意特徵）
- 負責關鍵字匹配、重要性分數、情緒偏向與權重學習。
- 提供查詢介面（`KeywordManager`/`MarketKeywords`）與學習介面（`KeywordLearner`）。
- 細節見：`keywords/README.md`

### 3) `daily_report/`（流程編排）
- 負責每日 SOP 分析流程（市場環境 + 交易計劃）與報告輸出。
- 整合 `news`、市場資料、策略與風控模組。
- 細節見：`daily_report/README.md`

### 4) `feature_engineering.py`（數值特徵）
- 成交量分布、清算熱力圖、市場微觀結構特徵。
- 給策略/模型層提供結構化向量與摘要。

### 5) `market_regime.py`（體制判斷）
- 依 K 線與技術指標識別市場 regime 與波動型態。
- 產出 regime 結果與策略偏好建議。

---

## 對外導出（以程式碼為準）

`analysis/__init__.py` 目前對外整合導出：
1. `daily_report`：`SOPAutomationSystem`、`MarketEnvironmentCheck`、`TradingPlanCheck`、`DailyMarketCondition`、`StrategyPerformance`、`DailyRiskLimits`、`TradingPairsPriority`、`DailyReport`
2. `keywords`：`Keyword`、`KeywordMatch`、`PredictionRecord`、`KeywordLoader`、`KeywordManager`、`get_keyword_manager`、`MarketKeywords`、`KeywordLearner`
3. `news`：`CryptoNewsAnalyzer`、`NewsArticle`、`NewsAnalysisResult`、`get_news_analyzer`、`RuleBasedEvaluator`、`get_rule_evaluator`、`EventRule`、`NewsPredictionLoop`
4. 直屬檔案：`feature_engineering.py` 與 `market_regime.py` 的公開類型

---

## 執行入口

`analysis/__main__.py` 提供示範執行：

```bash
python -m bioneuronai.analysis
python -m bioneuronai.analysis --sop
python -m bioneuronai.analysis --kw
```

說明：
1. 預設模式會用模擬 K 線示範完整流程。
2. 生產環境應由上層傳入真實行情資料，不以示範模式為準。

---

## 本次移除的老舊/錯誤敘述

1. 舊資料模型名稱（`MarketCondition`、`RiskParameters`）
2. 過時的固定檔案數、行數、覆蓋率描述
3. 與現況不符的 API 導出清單
4. 上層 README 過度描述子模組內部實作細節

---

## 子模組文件

1. `src/bioneuronai/analysis/daily_report/README.md`
2. `src/bioneuronai/analysis/keywords/README.md`
3. `src/bioneuronai/analysis/news/README.md`
