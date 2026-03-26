# 分析模組 — 關鍵字系統 (Keywords)

> **版本**: v3.0
> **更新日期**: 2026-03-19

## 目錄
- [模組概述](#模組概述)
- [系統架構與職責分離](#系統架構與職責分離)
- [核心元件與詳細方法](#核心元件與詳細方法)
- [動態權重與學習機制 (RLHF)](#動態權重與學習機制-rlhf)
- [持久化存儲](#持久化存儲)

## 模組概述
`keywords` 子模組是一個動態的市場關鍵字管理系統。它不再使用硬編碼的關鍵字，而是透過 `config/keywords/` 下的 JSON 檔案進行分類管理，並結合 SQLite 提供高效的查詢與歷史記錄追蹤。系統內建了基於預測準確率的動態權重調整 (RLHF)，讓關鍵字的重要性隨著市場變化自動演進。

## 系統架構與職責分離
為了符合單一職責原則 (SRP)，系統將查詢與學習分開：
- **讀取/查詢 (`KeywordManager`, `KeywordLoader`, `MarketKeywords`)**: 負責將資料載入記憶體，並對外部提供文字匹配與權重查詢。
- **寫入/學習 (`KeywordLearner`)**: 負責追蹤歷史預測、向外部 API 請求驗證價格，並更新 SQLite 與 JSON 檔案中的權重數值。

## 核心元件與詳細方法

### `manager.py` (核心管理器)
負責將關鍵字資料結構化，並處理預測記錄寫入。
- **`KeywordManager` (Singleton)**:
  - `find_matches(text)`: 在文本中尋找匹配的關鍵字，支援中英文（中文無須 word boundary）。
  - `record_prediction(...)`: 在 SQLite `prediction_history` 寫入一筆預測。
  - `verify_prediction(...)`: 更新該筆預測的實際方向，並修改對應關鍵字的 `dynamic_weight`。若預測次數大於 20，會呼叫 `_update_base_weight()` 調整長期基礎權重。
  - `update_sentiment_bias_from_results()`: 根據近期的實際價格變化，自動修正情緒偏向 (positive/negative)。

### `learner.py` (關鍵字學習器)
定期被呼叫以執行強化學習 (RLHF) 邏輯，避免與日常的高頻查詢混淆。
- **`KeywordLearner`**:
  - `log_prediction()`: 將新聞或分析預測推入 `predictions` 資料表。
  - `validate_and_learn()`: 找出到期 (預設 4 小時後) 的 pending 預測，請求當前市價，判斷是否正確，然後呼叫內部邏輯或 manager 來更新權重。
  - `_save_keywords()`: 學習完畢後，將新的 `Keyword` 狀態分門別類寫回 `config/keywords/*.json`。

### `loader.py` (JSON 載入器)
處理從磁碟讀取關鍵字的邏輯。
- **`KeywordLoader`**:
  - `load_from_category_files()`: 讀取 `_index.json` 並依序載入所有分類檔。
  - `load_from_single_file()`: 備用方案，讀取單一大檔。

### `static_utils.py` (靜態介面)
提供簡潔的全域靜態方法，背後委託給 `KeywordManager` 單例。
- **`MarketKeywords`**:
  - `get_importance_score(text)`: 根據匹配到的關鍵字的 `effective_weight` (base * dynamic) 與 `accuracy` 計算總分。
  - `get_sentiment_bias(text)`: 統計正負面權重，判斷整句新聞為看漲或看跌。
  - `is_high_impact_news(text)`: 快速篩選是否包含高權重 (>=2.5) 的災難或利多關鍵字。

### `models.py` (資料模型)
- **`Keyword`**: 包含 `base_weight`, `dynamic_weight`, `sentiment_bias`, `accuracy` 等屬性。
- **`KeywordMatch`**: 匹配結果，包含 `effective_weight`。
- **`PredictionRecord`**: SQLite 中預測歷史的對應模型。

## 動態權重與學習機制 (RLHF)
關鍵字的有效權重 (`effective_weight`) 為 `base_weight * dynamic_weight`。
1. **短期動態權重 (`dynamic_weight`)**: 每次預測正確 +8% (上限 2.0)，錯誤 -8% (下限 0.3)。
2. **長期基礎權重 (`base_weight`)**: 當預測次數 > 20 次，若準確率 > 70% 則增加基礎權重；若 < 40% 則降低。
3. **情緒偏向自動修正**: 根據過去多次預測的實際漲跌比例，自動更新該關鍵字的 `sentiment_bias`。

## 持久化存儲
- **SQLite** (`config/market_keywords.db`, `config/keyword_learning.db`): 存儲所有的預測歷史 (`prediction_history`) 與學習軌跡 (`learning_history`)。
- **JSON** (`config/keywords/*.json`): 分類保存關鍵字（如 event, emotion, technical），確保可讀性與可攜性，每次學習後自動更新。
