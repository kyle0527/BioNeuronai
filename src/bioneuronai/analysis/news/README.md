# 分析模組 — 新聞分析系統 (News)

> **版本**: v2.1
> **更新日期**: 2026-03-19

## 目錄
- [模組概述](#模組概述)
- [系統架構](#系統架構)
- [核心元件與詳細方法](#核心元件與詳細方法)
- [RLHF 預測驗證循環](#rlhf-預測驗證循環)
- [快取與效能優化](#快取與效能優化)

## 模組概述
`news` 子模組是系統的「新聞大腦」，負責從外部來源 (CryptoPanic, RSS) 抓取新聞，進行情緒分析、關鍵字提取、重大事件評估，並產生交易建議。此模組深度整合了 `keywords` 系統，並實作了基於強化學習思想的預測循環 (RLHF)，讓 AI 不僅讀取新聞，還能驗證自身的預測準確度並動態調整權重。

## 系統架構
本系統分為三個主要部分：新聞分析與抓取 (`analyzer`)、基於規則的事件評估 (`evaluator`)、與預測循環驗證 (`prediction_loop`)。整個子模組由 5 個 Python 檔案組成，總計約 2,621 行代碼。

## 核心元件與詳細方法

### `__init__.py` (72 行)
提供統一對外導出的入口介面，簡化其他模組的匯入，例如 `CryptoNewsAnalyzer`, `RuleBasedEvaluator`, `NewsPredictionLoop`。

### `analyzer.py` (1,140 行)
核心新聞分析器，負責抓取資料並進行自然語言初步處理。
- **`CryptoNewsAnalyzer` (Singleton)**:
  - `analyze_news(symbol, hours)`: 主進入點。整合 API 與 RSS，分析指定時間內的新聞，產出 `NewsAnalysisResult`。
  - `_fetch_from_cryptopanic()`, `_fetch_from_rss()`: 從外部服務抓取原始文章。
  - `_analyze_sentiment()`: 使用內建的正負面詞庫計算情緒分數 (-1 到 1)。
  - `_calculate_importance_score()`: 綜合評分機制 (0-10分)，考量來源權威性、事件類型 (駭客、ETF)、時效性、相關性與情緒強度。
  - `should_trade(symbol)`: 提供快速防護機制，若檢測到極端負面情緒或安全事件，會回傳暫停交易建議。
  - `evaluate_pending_news()`: 定期更新並回饋至關鍵字系統。

### `evaluator.py` (404 行)
規則式事件評估器，負責從新聞標題中識別具體事件，並追蹤事件的生命週期。
- **`RuleBasedEvaluator`**:
  - `evaluate_headline()`: 將新聞與預設的 `EventRule` 進行匹配 (如 WAR, HACK, REGULATION)。
  - `_check_termination_keywords()`: 實作 **Hard Stop** 機制，當出現如 "funds recovered" 等關鍵字時，自動將相關的負面安全事件標記為已解析 (resolved)。
  - `cleanup_expired_events()`: 根據每個事件特有的 `decay_hours`，定期清理過期的市場事件影響。

### `prediction_loop.py` (903 行)
新聞預測驗證循環，實作「預測 → 驗證 → 學習」的完整流程。
- **`NewsPredictionLoop`**:
  - `log_prediction()`: 當有重要新聞時，系統自動預測未來幾小時的市場方向並記錄。
  - `validate_pending_predictions()`: 對比歷史預測與當下實際價格的漲跌幅度。
  - `update_keyword_weights_from_results()`: 若預測正確，調高相關關鍵字權重 (最高 1.15 倍)；若錯誤則降低權重，實現完全自動化的 RLHF 學習。
  - 提供 `get_accuracy_by_source` 與 `get_accuracy_by_symbol` 統計函數，動態評估不同新聞來源的可靠性。
- **`PredictionScheduler`**: 後台定時器，負責每小時自動觸發上述的驗證流程。

### `models.py` (102 行)
資料模型定義。
- **`NewsArticle`**: 儲存單篇新聞的標題、來源、情緒、重要性評分等。
- **`NewsAnalysisResult`**: 針對特定時間段與交易對的整體分析結果。提供 `is_high_risk()`, `is_bullish()`, `is_bearish()` 等快速判斷方法。

## RLHF 預測驗證循環
系統的學習機制如下：
1. **預測**: 分析某篇重要新聞後，預測 BTC 將在 4 小時內上漲，呼叫 `log_prediction` 寫入 `predictions.jsonl`，狀態為 `PENDING`。
2. **衰減**: 若為重大事件，套用時間衰減模型 (例如駭客事件初始影響力 9.0，5 天後降至 6.0)。
3. **驗證**: 排程任務每小時喚醒，抓取當下市價。若 4 小時後價格確實上漲 > 1%，則標記為 `CORRECT`。
4. **學習**: 將結果回饋給 `KeywordManager`，提高該新聞中出現的關鍵字（如 "ETF"）的動態權重，並增加該新聞來源（如 "CoinDesk"）的信賴度評分。反之亦然。

## 快取與效能優化
- **API 快取**: `CryptoNewsAnalyzer` 實作了線程安全的記憶體快取 (`_cache`)，預設 TTL 為 300 秒 (5 分鐘)，避免頻繁調用外部 API 觸發 Rate Limit。
- **標題去重機制**: 基於標題前 50 字元進行去重，確保同一事件不會被多家媒體報導而重複計算權重與分數。
