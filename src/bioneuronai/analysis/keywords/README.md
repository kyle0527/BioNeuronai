# 分析模組 — 關鍵字系統 (Keywords)

> **版本**: v3.0
> **更新日期**: 2026-03-27

## 目錄
- [模組概述](#模組概述)
- [系統架構與職責分離](#系統架構與職責分離)
- [核心元件與詳細方法](#核心元件與詳細方法)
- [動態權重與學習機制 (RLHF)](#動態權重與學習機制-rlhf)
- [持久化存儲](#持久化存儲)

## 模組概述
`keywords` 子模組是一個動態的市場關鍵字管理系統。它不使用硬編碼的關鍵字，而是透過 `config/keywords/` 下的 JSON 檔案進行分類管理，並結合 SQLite 提供高效的查詢與歷史記錄追蹤。系統內建基於預測準確率的動態權重調整 (RLHF)，讓關鍵字重要性隨市場變化自動演進。

## 系統架構與職責分離
為了符合單一職責原則 (SRP)，系統將查詢與學習分開。總共包含 6 個 Python 檔案，共約 1,824 行代碼。
- **讀取/查詢 (`manager.py`, `loader.py`, `static_utils.py`, `__init__.py`)**: 負責將資料載入記憶體，對外提供文字匹配、權重查詢與統計介面。
- **寫入/學習 (`learner.py`)**: 負責追蹤歷史預測，請求當前市價驗證，並更新 SQLite 與 JSON 的權重數值。
- **資料模型 (`models.py`)**: 定義共用資料結構。

## 核心元件與詳細方法

### `__init__.py` (60 行)
提供統一對外的導出，簡化其他模組的調用。

**導出清單**:
- 模型：`Keyword`, `KeywordMatch`, `PredictionRecord`
- 載入器：`KeywordLoader`
- 管理器：`KeywordManager`, `get_keyword_manager`
- 靜態工具：`MarketKeywords`
- 學習器：`KeywordLearner`

---

### `manager.py` (905 行)
核心管理器，負責關鍵字的載入、文字匹配、預測記錄與持久化。以 Singleton 模式運作。

**類別常數**:
- `DEFAULT_DB_PATH = "config/market_keywords.db"`
- `WEIGHT_INCREASE_FACTOR = 1.08`、`WEIGHT_DECREASE_FACTOR = 0.92`
- `MAX_DYNAMIC_WEIGHT = 2.0`、`MIN_DYNAMIC_WEIGHT = 0.3`
- `MIN_PREDICTIONS_FOR_BASE = 20`（調整基礎權重所需最低預測次數）
- `MAX_BASE_WEIGHT = 3.5`、`MIN_BASE_WEIGHT = 0.5`

**`KeywordManager` 方法**:

*初始化與載入*
- `__init__(config_path, db_path)`: 初始化，優先從 SQLite 快取載入，否則從 JSON 載入。
- `_init_database()`: 建立 SQLite `prediction_history` 資料表。
- `_load_keywords()`: 協調 SQLite / JSON 載入順序。
- `_load_from_database()` → `bool`: 從 SQLite 快取載入關鍵字。
- `_save_to_database()`: 將記憶體中的關鍵字寫回 SQLite。

*匹配與查詢*
- `find_matches(text)` → `List[KeywordMatch]`: 在文本中尋找匹配的關鍵字，支援中英文（中文無須 word boundary）。
- `get_importance_score(text)` → `Tuple[float, List[str]]`: 根據匹配關鍵字的 `effective_weight` 與 `accuracy` 計算重要性分數 (0–10)。
- `get_sentiment_bias(text)` → `Tuple[str, float]`: 統計正負面權重，返回 `'positive'/'negative'/'neutral'` 與信心值 (0–1)。
- `is_high_impact_news(text, threshold=2.5)` → `Tuple[bool, List[str]]`: 快速篩選是否包含高權重關鍵字。

*關鍵字管理*
- `add_keyword(keyword, category, base_weight, sentiment_bias, description, subcategory)` → `bool`: 新增關鍵字並存檔。
- `remove_keyword(keyword)`: 移除關鍵字。
- `refresh_stale_keywords()` → `int`: 重置過時（>90 天未更新且準確率 <40%）關鍵字的 `dynamic_weight`，返回重置數量。
- `update_keywords_from_trending(trending_topics)` → `int`: 從熱門話題清單新增關鍵字，返回新增數量。
- `get_stale_keywords()` → `List[Keyword]`: 返回所有過時關鍵字。
- `get_top_keywords(n=20)` → `List[Keyword]`: 返回 `effective_weight` 最高的 N 個關鍵字。

*預測記錄與驗證*
- `record_prediction(keyword, predicted_direction, price_before, news_title)` → `int`: 在 SQLite `prediction_history` 寫入預測，返回預測 ID。
- `verify_prediction(prediction_id, actual_direction, price_after)` → `bool`: 更新預測的實際方向，並修改對應關鍵字的 `dynamic_weight`；預測次數達 20 次後觸發 `_update_base_weight()`。
- `record_and_verify_prediction(keyword, predicted, actual, price_before, price_after)`: 便捷方法，一次完成記錄與驗證。
- `update_sentiment_bias_from_results(keyword, price_changes)`: 根據近期實際價格變化，自動修正該關鍵字的 `sentiment_bias`。

*統計與報告*
- `get_statistics()` → `Dict`: 返回 `total`, `by_category`, `stale_count`, `avg_weight` 等統計。
- `get_prediction_history(keyword, limit)` → `List[PredictionRecord]`: 查詢特定關鍵字的預測歷史。
- `get_pending_predictions()` → `List[PredictionRecord]`: 返回尚未驗證的預測列表。
- `get_overall_accuracy()` → `Tuple[float, int, int]`: 返回整體準確率 `(accuracy, correct, total)`。
- `get_keyword_performance(min_predictions=5)` → `List[Dict]`: 返回各關鍵字表現排名。
- `print_report()`: 印出完整統計報告。

*持久化*
- `_save_keywords()`: 協調寫入 JSON 分類檔案。
- `_save_to_category_files()`: 依 `category` 分組寫回 `config/keywords/*.json`。
- `_save_to_single_file()`: 備用，寫入單一 JSON 檔案。
- `_update_index_file(by_category)`: 更新 `config/keywords/_index.json`。

**工廠函數**:
- `get_keyword_manager()` → `KeywordManager`: 返回全域 Singleton 實例。

---

### `learner.py` (443 行)
關鍵字學習器，定期執行強化學習 (RLHF) 邏輯，與高頻查詢流程分離。

**類別常數**:
- `DEFAULT_CHECK_HOURS = 4`（預設驗證等待時間）
- `PRICE_THRESHOLD = 0.01`（1% 價格變動門檻）
- `WEIGHT_INCREASE_FACTOR = 1.08`、`WEIGHT_DECREASE_FACTOR = 0.92`
- `MAX_DYNAMIC_WEIGHT = 2.0`、`MIN_DYNAMIC_WEIGHT = 0.3`

**`KeywordLearner` 方法**:
- `__init__(keyword_manager, db_path="config/keyword_learning.db")`: 初始化，建立或接收 `KeywordManager` 實例，初始化學習資料庫。
- `_init_learning_db()`: 建立 SQLite `predictions` 與 `learning_history` 資料表。
- `log_prediction(keywords, predicted_direction, symbol, price_at_prediction, check_after_hours, metadata)` → `str`: 將新預測寫入 `predictions` 資料表，返回 `prediction_id`。
- `validate_and_learn()`: 找出到期（預設 4 小時後）的 pending 預測，請求當前市價，判斷是否正確，呼叫 `_update_keyword_weight()` 更新權重，並寫入 `learning_history`。
- `_update_keyword_weight(keyword, is_correct)`: 根據預測結果調整 `dynamic_weight`，並透過 `keyword_manager` 持久化。
- `_save_keywords()`: 學習完畢後，透過 `keyword_manager` 將新的 `Keyword` 狀態寫回 JSON。
- `get_learning_stats()` → `Dict`: 返回學習統計（總預測數、正確數、準確率、pending 數等）。
- `get_pending_count()` → `int`: 返回尚未驗證的預測數量。

**工廠函數**:
- `get_keyword_learner()` → `KeywordLearner`: 返回全域 Singleton 實例。

---

### `loader.py` (131 行)
JSON 載入器，處理從磁碟讀取關鍵字的邏輯。

**`KeywordLoader` 方法**:
- `__init__(keywords_dir="config/keywords", config_path="config/market_keywords.json")`: 設定分類目錄與備用單一檔案路徑。
- `load()` → `Dict[str, Keyword]`: 主要入口，優先呼叫 `load_from_category_files()`，若無結果則退回 `load_from_single_file()`。
- `load_from_category_files()` → `Dict[str, Keyword]`: 讀取 `_index.json`，依序載入所有分類 JSON 檔案；若無 `_index.json` 則掃描目錄中所有 `*.json`。
- `load_from_single_file()` → `Dict[str, Keyword]`: 備用方案，從 `config/market_keywords.json` 讀取。

---

### `static_utils.py` (186 行)
靜態包裝類，將 `KeywordManager` 的所有功能以類別方法形式對外暴露，無需手動取得 Singleton。

**`MarketKeywords` 類別方法**:

*查詢*
- `get_instance()` → `KeywordManager`: 取得 Singleton。
- `get_importance_score(text)` → `Tuple[float, List[str]]`: 計算文本重要性分數 (0–10)。
- `get_sentiment_bias(text)` → `Tuple[str, float]`: 分析情緒傾向與信心值。
- `find_matches(text)` → `List[KeywordMatch]`: 返回匹配的關鍵字，按權重排序。
- `is_high_impact_news(text, threshold=2.5)` → `Tuple[bool, List[str]]`: 高影響力新聞快速判斷。
- `get_keyword_count()` → `int`: 返回關鍵字總數。
- `get_top_keywords(n=20)` → `List[Keyword]`: 返回權重最高的 N 個關鍵字。
- `get_overall_accuracy()` → `Tuple[float, int, int]`: 返回整體準確率。
- `get_keyword_performance(min_predictions=5)` → `List[Dict]`: 關鍵字表現排名。
- `get_statistics()` → `Dict`: 完整統計資料。

*管理*
- `add_keyword(keyword, category, base_weight, sentiment_bias, description, subcategory)` → `bool`: 新增關鍵字。
- `remove_keyword(keyword)`: 移除關鍵字。
- `refresh_stale_keywords()` → `int`: 重置過時關鍵字。
- `update_from_trending(trending_topics)` → `int`: 從熱門話題新增關鍵字。

*預測*
- `record_prediction(keyword, predicted_direction, price_before, news_title)` → `int`: 記錄預測。
- `verify_prediction(prediction_id, actual_direction, price_after)` → `bool`: 驗證預測。

*報告*
- `print_report()`: 印出統計報告。

---

### `models.py` (99 行)
資料模型定義（`dataclass`，非 Pydantic）。

**`Keyword`**: 關鍵字完整資料結構
- 必填欄位：`word`, `category`, `base_weight`, `dynamic_weight`, `sentiment_bias`, `description`, `added_date`, `last_updated`
- 統計欄位（有預設值）：`hit_count=0`, `prediction_count=0`, `correct_count=0`
- 擴充欄位（有預設值）：`dynamic_bias=0.0`, `subcategory="general"`
- 衍生屬性（`@property`）：`accuracy`, `effective_weight`, `days_since_added`, `days_since_updated`, `is_stale`

**`PredictionRecord`**: 預測記錄（對應 SQLite `prediction_history` 資料表）
- `id`, `keyword`, `news_title`, `predicted_direction`, `actual_direction`, `price_before`, `price_after`, `price_change_pct`, `is_correct`, `created_at`, `verified_at`

**`KeywordMatch`**: 匹配結果
- `keyword`, `category`, `effective_weight`, `sentiment_bias`, `description`, `accuracy`, `days_old`

---

## 動態權重與學習機制 (RLHF)

關鍵字的有效權重 (`effective_weight`) 為 `base_weight × dynamic_weight`。

### 短期動態權重 (`dynamic_weight`)
- 預測正確：`dynamic_weight × 1.08`，上限 `2.0`
- 預測錯誤：`dynamic_weight × 0.92`，下限 `0.3`

### 長期基礎權重 (`base_weight`)
- 條件：`prediction_count >= 20`
- 準確率 > 70%：`base_weight + 0.05`，上限 `3.5`
- 準確率 < 40%：`base_weight - 0.05`，下限 `0.5`

### 情緒偏向自動修正
- `update_sentiment_bias_from_results()` 根據近期預測的實際漲跌比例，自動更新 `sentiment_bias`。

### 關鍵字過時判定
- `Keyword.is_stale`：`days_since_updated > 90` 且 `accuracy < 0.4`
- 可透過 `refresh_stale_keywords()` 批次重置過時關鍵字的 `dynamic_weight`。

---

## 持久化存儲

| 存儲 | 路徑 | 管理者 | 資料表 / 內容 |
|------|------|--------|--------------|
| SQLite | `config/market_keywords.db` | `KeywordManager` | `prediction_history`（預測記錄）、關鍵字快取 |
| SQLite | `config/keyword_learning.db` | `KeywordLearner` | `predictions`（RLHF 驗證隊列）、`learning_history`（學習軌跡） |
| JSON | `config/keywords/*.json` | `KeywordManager._save_to_category_files()` | 依分類儲存關鍵字（`person`, `institution`, `macro`, `legislation`, `event`, `coin`, `tech`） |
| JSON | `config/keywords/_index.json` | `KeywordManager._update_index_file()` | 分類索引，記錄各分類對應的 JSON 檔案名稱 |
| JSON | `config/market_keywords.json` | `KeywordLoader.load_from_single_file()` | 備用單一檔案（舊版相容，主要由分類目錄取代） |
