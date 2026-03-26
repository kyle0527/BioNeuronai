# 分析模組 — 新聞分析系統 (News)

> **版本**: v2.1
> **更新日期**: 2026-03-19

## 目錄
- [模組概述](#模組概述)
- [系統架構](#系統架構)
- [核心元件與類別](#核心元件與類別)
- [RLHF 預測循環](#rlhf-預測循環)
- [快取與效能優化](#快取與效能優化)

## 模組概述
`news` 子模組是系統的「新聞大腦」，負責從外部來源 (CryptoPanic, RSS) 抓取新聞，進行情緒分析、關鍵字提取、重大事件評估，並產生交易建議。此模組深度整合了 `keywords` 系統，並實作了預測循環以驗證新聞的實際影響力。

## 系統架構
本系統分為三個主要部分：新聞分析與抓取 (`analyzer`)、事件評估 (`evaluator`)、與預測循環 (`prediction_loop`)。

## 核心元件與類別

### `analyzer.py` — 核心新聞分析器
- **`CryptoNewsAnalyzer` (Singleton)**:
  - `analyze_news(symbol, hours)`: 主進入點。從多來源抓取新聞，分析情緒、重要性，並彙整出 `NewsAnalysisResult`。
  - `_fetch_from_cryptopanic`, `_fetch_from_rss`: 實作 API 串接與 RSS 解析。
  - `_calculate_importance_score`: 根據來源權威性、事件類型 (駭客、ETF等)、時效性與情緒強度，給出 0-10 分的重要度評分。
  - `evaluate_pending_news()`: 評估之前保存的新聞記錄，更新關鍵字系統的權重。

### `evaluator.py` — 事件評估器
- **`RuleBasedEvaluator`**:
  - 基於規則的新聞事件評估引擎。
  - 辨識出「嚴重安全事件 (Security)」、「重大監管 (Regulation)」等，並可觸發系統的 Hard Stop 機制。

### `prediction_loop.py` — 新聞預測循環 (RLHF)
- **`NewsPredictionLoop`**:
  - 實作「預測 → 驗證 → 學習」的完整循環。
  - 將新聞分析器給出的看漲/看跌預測記錄下來。
  - 包含事件衰減模型 (Decay Model)：例如「駭客事件」初始影響力為 9.0，10 天後衰減為 3.0。
  - 追蹤不同新聞來源 (Source) 與交易對 (Symbol) 的預測準確率。

### `models.py` — 資料模型
- **`NewsArticle`**: 單篇新聞模型 (標題、摘要、時間、情緒、關鍵字、重要性評分等)。
- **`NewsAnalysisResult`**: 針對特定時間段與交易對的整體分析結果。

## RLHF 預測循環與關鍵字聯動
當 `CryptoNewsAnalyzer` 分析一篇重要新聞時：
1. 若價格資訊可用，記錄當下價格與新聞特徵至 `news_records.json`。
2. 經過一段時間 (例如 24 小時) 後，呼叫 `evaluate_pending_news()`。
3. 對比當下價格，判斷當初的情緒預測是否正確。
4. 呼叫 `KeywordManager.update_keyword_weight()`，若預測正確則增加該新聞關鍵字的權重，錯誤則降低，實現自我完善的機制。

## 快取與效能優化
- **API 快取**: `CryptoNewsAnalyzer` 實作了線程安全的記憶體快取 (`_cache`)，預設 TTL 為 300 秒 (5 分鐘)，避免頻繁調用外部 API 觸發 Rate Limit。
- **去重機制**: 基於標題字串特徵 (`title_key`) 進行新聞去重，確保同一事件不會被重複計算權重。
