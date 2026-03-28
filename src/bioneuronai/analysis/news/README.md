# 分析模組 — 新聞分析系統 (News)

> **版本**: v4.1
> **更新日期**: 2026-03-27

## 目錄
- [模組概述](#模組概述)
- [系統架構](#系統架構)
- [核心元件與詳細方法](#核心元件與詳細方法)
- [RLHF 預測驗證循環](#rlhf-預測驗證循環)
- [快取與效能優化](#快取與效能優化)

## 模組概述
`news` 子模組是系統的「新聞大腦」，負責從外部來源 (CryptoPanic, RSS) 抓取新聞，進行情緒分析、關鍵字提取、重大事件評估，並產生交易建議。此模組深度整合了 `keywords` 系統，並實作基於強化學習思想的預測循環 (RLHF)，讓 AI 不僅讀取新聞，還能驗證自身的預測準確度並動態調整權重。

## 系統架構
本系統分為三個主要部分：新聞分析與抓取 (`analyzer`)、基於規則的事件評估 (`evaluator`)、與預測循環驗證 (`prediction_loop`)。整個子模組由 5 個 Python 檔案組成，總計約 2,621 行代碼。

---

## 核心元件與詳細方法

### `__init__.py` (72 行)
提供統一對外導出的入口介面，簡化其他模組的匯入。

**導出清單**:
- 模型：`NewsArticle`, `NewsAnalysisResult`
- 分析器：`CryptoNewsAnalyzer`, `get_news_analyzer`
- 評估器：`RuleBasedEvaluator`, `get_rule_evaluator`, `EventRule`
- 預測循環：`NewsPredictionLoop`

> 注意：`PredictionScheduler` 在 `prediction_loop.py` 內定義但未對外導出，需直接從模組引入。

---

### `analyzer.py` (1,140 行)
核心新聞分析器，負責抓取資料並進行自然語言初步處理。以 Singleton 模式運作。

**`CryptoNewsAnalyzer` 公開方法**:
- `analyze_news(symbol, hours=24)` → `NewsAnalysisResult`: 主進入點，整合 CryptoPanic API 與 RSS，分析指定時間內的新聞，產出 `NewsAnalysisResult`。
- `get_quick_summary(symbol)` → `str`: 快速回傳簡短的單行摘要，適合 CLI 顯示。
- `should_trade(symbol)` → `Tuple[bool, str]`: 快速防護機制，若偵測到極端負面情緒或安全事件，回傳 `(False, 原因)` 以暫停交易。
- `evaluate_pending_news()` → `Dict[str, int]`: 讀取已儲存的新聞記錄，驗證過去預測是否正確，並回饋至關鍵字系統更新動態權重。

**`CryptoNewsAnalyzer` 內部方法（主要流程）**:
- `_fetch_news(coin, hours)`: 協調 CryptoPanic 與 RSS 兩個來源，合併去重後回傳文章列表。
- `_fetch_from_cryptopanic(coin)`: 呼叫 CryptoPanic API 抓取原始資料。
- `_fetch_from_rss(coin)`: 並行讀取多個 RSS 來源。
- `_process_single_rss_feed(feed_url, coin)`: 處理單一 RSS 來源。
- `_parse_rss_item(item, feed_url, coin)` → `Optional[NewsArticle]`: 解析單筆 RSS 條目。
- `_analyze_articles(symbol, articles)` → `NewsAnalysisResult`: 對所有文章進行整體分析，彙整情緒、關鍵事件、推薦建議。
- `_analyze_sentiment(text)` → `Tuple[str, float]`: 使用內建正負面詞庫計算情緒分數 (−1 到 1)。
- `_calculate_importance_score(article, target_coin)` → `float`: 綜合評分機制 (0–10)，考量來源權威性、事件類型 (駭客、ETF)、時效性、相關性與情緒強度。
- `_detect_key_events(text)`, `_detect_event_type(text)`, `_detect_with_keywords(text)`, `_classify_keyword_event(keyword)`, `_detect_with_regex(text_lower)`: 多層事件偵測管道。
- `_extract_keywords(text)` → `List[str]`: 提取文本關鍵字。
- `_check_content_relevance(full_text, coin)`, `_match_with_keywords(full_text)`, `_match_with_coin_keywords(full_text, coin)`: 相關性與關鍵字匹配。
- `_calculate_time_score(hours_old)`, `_calculate_relevance_score(...)`: 評分子函數。
- `_generate_recommendation(...)`: 根據整體情緒與事件分數產生交易建議文字。
- `_save_news_record(article, current_price)`: 將文章與當前價格寫入本地記錄（用於後續 `evaluate_pending_news`）。
- `_evaluate_single_news(record)`, `_calculate_weight_factor(direction, impact)`, `_update_single_keyword(km, kw, factor, result)`, `_update_keyword_weights(keywords, result)`: 評估歷史新聞並調整關鍵字權重。
- `_get_current_price(symbol)` → `float`: 取得當前市價（呼叫 Binance API）。
- `_parse_publication_date(pub_date)` → `datetime`: 解析 RSS 日期格式。

**工廠函數**:
- `get_news_analyzer()` → `CryptoNewsAnalyzer`: 返回全域 Singleton 實例。

---

### `evaluator.py` (404 行)
規則式事件評估器，負責從新聞標題識別具體事件，並追蹤事件的完整生命週期。

**`EventDatabase` Protocol**:
定義事件資料庫的介面，需實作：`save_event()`, `get_active_events()`, `resolve_event()`, `calculate_total_event_score()`。

**`EventRule`**:
從 `schemas.rag` 導入（符合 Single Source of Truth 原則，非本地定義）。預設提供以下事件類型規則：`WAR`, `HACK`, `REGULATION`, `MACRO`, `EXCHANGE_ISSUE`, `ETF_APPROVAL`（含正負面基礎分數及各自的 `decay_hours`）。

**`RuleBasedEvaluator` 方法**:
- `__init__(custom_rules)`: 初始化，接受自定義規則列表；無參數時使用 `DEFAULT_RULES`，並嘗試連接事件資料庫。
- `evaluate_headline(headline, source, source_confidence)` → `Optional[Dict]`: 將新聞與所有 `EventRule` 進行匹配，若命中則建立事件記錄，存入 event_memory 資料庫，並返回事件資訊字典 (含 `event_type`, `score`, `decay_hours` 等)。
- `get_current_event_score(symbol)` → `Tuple[float, List[Dict]]`: 取得當前所有活躍事件的綜合分數，供 `strategy_fusion` 使用。
- `evaluate_news_batch(articles)` → `List[Dict]`: 批次評估多篇文章，返回所有命中事件的清單。
- `cleanup_expired_events()` → `int`: 根據每個事件特有的 `decay_hours`，定期清理過期市場事件，返回清理數量。
- `_check_termination_keywords(headline_lower)`: **Hard Stop 機制**，當出現如 `"funds recovered"`, `"ceasefire"` 等關鍵字時，自動將對應的活躍負面事件標記為已解析 (resolved)。
- `_create_event(rule, headline, source, confidence)`: 建立事件記錄並寫入資料庫。
- `_connect_db()`: 嘗試連接事件記憶資料庫。

**工廠函數**:
- `get_rule_evaluator()` → `RuleBasedEvaluator`: 返回全域 Singleton 實例。

---

### `prediction_loop.py` (903 行)
新聞預測驗證循環，實作「預測 → 驗證 → 學習」完整流程。

**資料模型**:
- `PredictionStatus` (Enum): `PENDING`, `VALIDATING`, `CORRECT`, `WRONG`, `EXPIRED`, `HUMAN_REVIEW`
- `PredictionDirection` (Enum): `BULLISH`, `BEARISH`, `NEUTRAL`
- `NewsPrediction` (dataclass): 預測完整記錄，欄位包含 `prediction_id`, `news_title`, `news_source`, `target_symbol`, `predicted_direction`, `predicted_magnitude`, `confidence`, `prediction_time`, `check_after_hours`, `price_at_prediction`, `price_at_validation`, `actual_change_pct`, `status`, `is_correct`, `accuracy_score`, `keywords_used`, `sentiment_score`, `human_feedback`, `human_rating`。提供 `to_dict()` / `from_dict()` 序列化方法。
- `ValidationResult` (dataclass): 驗證結果，含 `prediction_id`, `is_correct`, `accuracy_score`, `price_change_pct`, `status`, `validated_at`。

**`NewsPredictionLoop` 方法**:

*預測記錄*
- `__init__(data_dir, price_fetcher, keyword_manager)`: 初始化，設定資料目錄 (`./news_predictions/`)，載入現有預測記錄。
- `log_prediction(news_title, news_source, target_symbol, predicted_direction, confidence, check_after_hours, keywords_used, sentiment_score, price_at_prediction)` → `str`: 記錄新預測並寫入 `predictions.jsonl`，返回 `prediction_id`，狀態設為 `PENDING`。
- `add_manual_note(prediction_id, note)`: 為特定預測新增備註。
- `add_human_feedback(prediction_id, is_correct, feedback, rating)`: 新增人工反饋覆蓋自動驗證結果。

*驗證與學習*
- `validate_pending_predictions()` → `List[ValidationResult]`: 掃描所有 `PENDING` 預測，判斷是否到期，呼叫 `_validate_single_prediction()` 逐一驗證，並觸發權重更新。
- `update_keyword_weights_from_results()`: 依據驗證結果批次呼叫關鍵字模組 API 調整權重。
- `_validate_single_prediction(prediction)` → `ValidationResult`: 抓取當前市價，對比預測方向，計算 `accuracy_score`，更新 `prediction.status`。
- `_evaluate_accuracy(predicted_direction, actual_change_pct)` → `Tuple[bool, float]`: 評估預測正確性（1% 門檻判斷）。
- `_calculate_accuracy_score(is_correct, confidence, actual_change_pct)` → `float`: 計算準確度分數 (0–1)。
- `_feedback_to_keywords(prediction)`: 根據驗證結果回饋至 `KeywordManager`，調整關鍵字動態權重。

*統計*
- `get_accuracy_by_source()` → `Dict[str, float]`: 按新聞來源統計準確率。
- `get_accuracy_by_symbol()` → `Dict[str, float]`: 按交易對統計準確率。
- `get_statistics()` → `Dict`: 返回總體統計（總預測、已驗證、正確、錯誤、準確率等）。
- `get_recent_predictions(limit=20)` → `List[NewsPrediction]`: 返回最近 N 筆預測記錄。

*持久化*
- `_save_prediction(prediction)`: 追加寫入 `predictions.jsonl`。
- `_save_all_predictions()`: 覆寫整個 `predictions.jsonl` 檔案。
- `_load_predictions()`: 啟動時從 `predictions.jsonl` 載入所有歷史預測。

**`PredictionScheduler` 類別**（後台定時器，不對外導出）:
- `__init__(prediction_loop, check_interval_minutes=60)`: 接收 `NewsPredictionLoop` 實例，預設每 60 分鐘驗證一次。
- `start()`: 啟動後台 daemon 線程，排程每 N 分鐘驗證 + 每日 09:00 產生報告。
- `stop()`: 停止調度器並清除排程任務。
- `_run_scheduler()`: 後台線程主迴圈（每 30 秒呼叫 `schedule.run_pending()`）。
- `_validate_predictions()`: 定時任務，呼叫 `prediction_loop.validate_pending_predictions()`。
- `_generate_daily_report()`: 定時任務，產生每日統計報告。

---

### `models.py` (102 行)
資料模型定義（`dataclass`，非 Pydantic）。

**`NewsArticle`**: 單篇新聞資料結構
- 必填：`title`, `source`, `url`, `published_at`
- 可選（有預設值）：`summary`, `sentiment`, `sentiment_score`, `keywords`, `category`, `source_credibility`, `coins_mentioned`, `importance_score`, `relevance_score`, `price_at_news`, `target_coin`

**`NewsAnalysisResult`**: 整體分析結果
- 必填：`symbol`, `total_articles`, `positive_count`, `negative_count`, `neutral_count`, `overall_sentiment`, `sentiment_score`, `key_events`, `top_keywords`, `recent_headlines`, `recommendation`, `analysis_time`
- 可選：`articles`（文章列表）
- 方法：
  - `is_high_risk()` → `bool`: 檢查是否含安全或監管事件
  - `is_bullish()` → `bool`: `sentiment_score > 0.2` 且 `overall_sentiment == "positive"`
  - `is_bearish()` → `bool`: `sentiment_score < -0.2` 且 `overall_sentiment == "negative"`
  - `to_dict()` → `dict`: 序列化為字典（含 articles 摘要）

---

## RLHF 預測驗證循環

### 完整工作流程

1. **智能品種選擇**：針對性事件直接識別目標幣種（BTC ETF → BTC）；全局性事件選 1–2 個最有把握的品種（FED 升息 → BTC+ETH）。

2. **發布預測**：呼叫 `NewsPredictionLoop.log_prediction()` 寫入 `predictions.jsonl`，狀態設為 `PENDING`，根據事件類型動態設定驗證等待時間。

3. **時間衰減模型**（不同事件類型的影響力衰減）：

   | 事件類型 | 初始影響 | 5天後 | 10/15/30天後 |
   |---------|---------|-------|-------------|
   | 駭客事件 | 9.0 | 6.0 | 3.0 (10天) |
   | 升降息 | 8.5 | 6.5 | 4.0 (15天) |
   | 戰爭 | 9.5 | 7.0 | 4.5 (30天) |
   | ETF 批准 | 8.0 | 5.0 | 2.0 (7天) |
   | 一般新聞 | 5.0 | 2.0 | 0.5 (3天) |

4. **真相驗證**：`PredictionScheduler` 每小時喚醒，抓取當前市價，對比發稿價格：
   - 預測漲 + 實際漲 > 1% → `CORRECT`
   - 預測漲 + 實際漲 < 1% → 部分準確（方向對但幅度小）
   - 預測漲 + 實際跌 → `WRONG`

5. **智能權重修正**（`_feedback_to_keywords`）：

   | 結果 | 權重調整因子 |
   |------|-------------|
   | 完全正確 | × 1.15 |
   | 部分準確 | × 1.05 |
   | 錯誤 | × 0.85 |
   | 連續錯誤 | × 0.70 |

6. **準確度追蹤**：系統分類統計按事件類型、幣種、時間範圍的準確率；準確率 < 60% 的關鍵字/來源自動降權，無需人工介入。

---

## 快取與效能優化
- **API 快取**: `CryptoNewsAnalyzer` 實作線程安全記憶體快取 (`_cache`)，預設 TTL 為 300 秒 (5 分鐘)，避免頻繁呼叫外部 API 觸發 Rate Limit。
- **標題去重機制**: 基於標題前 50 字元進行去重，確保同一事件不因多家媒體報導而重複計算權重與分數。
- **預測持久化**: 預測記錄存於 `./news_predictions/predictions.jsonl`（JSONL 格式），非 SQLite，便於跨進程讀取與人工稽核。
