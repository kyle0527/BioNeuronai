# 分析模組 — 關鍵字系統 (Keywords)

> **版本**: v3.0
> **更新日期**: 2026-03-19

## 目錄
- [模組概述](#模組概述)
- [系統架構](#系統架構)
- [核心元件與類別](#核心元件與類別)
- [動態權重與學習機制 (RLHF)](#動態權重與學習機制-rlhf)
- [持久化存儲](#持久化存儲)

## 模組概述
`keywords` 子模組是一個動態的市場關鍵字管理系統。它不再使用硬編碼的關鍵字，而是透過 `config/keywords/` 下的 JSON 檔案進行分類管理，並結合 SQLite 提供高效的查詢與歷史記錄追蹤。系統內建了基於預測準確率的動態權重調整 (RLHF)，讓關鍵字的重要性隨著市場變化自動演進。

## 系統架構
本系統分為四個主要部分：載入 (`loader`)、管理/匹配 (`manager`)、學習/更新 (`learner`) 與靜態介面 (`static_utils`)。

## 核心元件與類別

### `manager.py` — 核心管理器
負責關鍵字匹配、預測記錄、與資料庫互動。
- **`KeywordManager` (Singleton)**:
  - `find_matches(text)`: 在文本中尋找匹配的關鍵字，支援中英文（英文使用 word boundary）。
  - `record_prediction(...)`: 記錄基於某關鍵字所做出的市場方向預測。
  - `verify_prediction(...)`: 在一段時間後驗證預測結果，並更新關鍵字的動態權重與準確率。
  - `get_importance_score(text)` / `get_sentiment_bias(text)`: 計算文本的重要度與情緒偏向。

### `learner.py` — 關鍵字學習器
實現強化學習 (RLHF) 邏輯，與 `manager` 解耦。
- **`KeywordLearner`**:
  - 定期掃描未驗證的預測記錄。
  - 根據實際價格走勢，呼叫 `manager.verify_prediction` 更新權重。

### `loader.py` — JSON 載入器
處理從磁碟讀取關鍵字的邏輯。
- **`KeywordLoader`**:
  - 掃描 `config/keywords/*.json`。
  - 支援載入分類設定（如 event, emotion, technical）。

### `models.py` — 資料模型
- **`Keyword`**: 包含 `base_weight`, `dynamic_weight`, `sentiment_bias`, `accuracy` 等屬性。
- **`KeywordMatch`**: 匹配結果，包含 `effective_weight`。
- **`PredictionRecord`**: SQLite 中預測歷史的對應模型。

### `static_utils.py` — 靜態介面
提供簡潔的全域靜態方法，背後委託給 `KeywordManager` 單例。
- **`MarketKeywords`**: 提供 `get_importance_score`, `get_sentiment_bias`, `find_matches` 等靜態方法，方便其他模組直接呼叫。

## 動態權重與學習機制 (RLHF)
關鍵字的有效權重 (`effective_weight`) 為 `base_weight * dynamic_weight`。
1. **短期動態權重 (`dynamic_weight`)**: 每次預測正確 +8% (max 2.0)，錯誤 -8% (min 0.3)。
2. **長期基礎權重 (`base_weight`)**: 當預測次數 > 20 次，若準確率 > 70% 則增加基礎權重；若 < 40% 則降低。
3. **情緒偏向自動修正**: 根據過去 10 次預測的實際漲跌比例，動態更新該關鍵字的 `sentiment_bias` (positive, negative, neutral, uncertain)。

## 持久化存儲
- **SQLite** (`config/market_keywords.db`): 存儲所有關鍵字目前的權重、統計資料，以及完整的 `prediction_history`。
- **JSON** (`config/keywords/*.json`): 確保關鍵字資料的可讀性與可攜性，每次重大更新後會同步回寫。
