# 分析模組 — 關鍵字系統 (Keywords)

> **路徑**: `src/bioneuronai/analysis/keywords/`  
> **更新日期**: 2026-04-20
> **文件焦點**: 子模組內部 API、資料流與持久化（分層說明請看上層 [analysis README](../README.md)）

## 目錄

1. [子模組職責](#子模組職責)
2. [檔案結構](#檔案結構)
3. [角色分工](#角色分工)
4. [對外導出](#對外導出依-__init__py)
5. [資料來源與存儲](#資料來源與存儲)
6. [實作現況](#實作現況)
7. [維護邊界](#維護邊界)

---

## 子模組職責

`keywords` 負責新聞文本到關鍵字特徵的轉換與學習回饋：
1. 載入關鍵字配置
2. 文本匹配與重要性/情緒評分
3. 記錄預測與驗證結果
4. 依結果調整動態權重

---

## 檔案結構

```text
keywords/
├── __init__.py       # 對外導出
├── models.py         # Keyword / KeywordMatch / PredictionRecord
├── loader.py         # JSON 載入
├── manager.py        # 核心管理器
├── static_utils.py   # MarketKeywords 靜態封裝
├── learner.py        # KeywordLearner 學習回饋
└── README.md
```

檔案對照：
1. [__init__.py](__init__.py)
2. [models.py](models.py)
3. [loader.py](loader.py)
4. [manager.py](manager.py)
5. [static_utils.py](static_utils.py)
6. [learner.py](learner.py)

---

## 角色分工

1. `KeywordManager`（`manager.py`）
- 主責高頻查詢、匹配、預測記錄、統計、SQLite/JSON 持久化。

2. `MarketKeywords`（`static_utils.py`）
- 提供靜態呼叫介面，內部代理 `KeywordManager`。

3. `KeywordLearner`（`learner.py`）
- 主責延遲驗證與學習資料維護，將結果回饋到關鍵字權重。

4. `KeywordLoader`（`loader.py`）
- 主責從 `config/keywords/*.json` 或舊版單檔配置載入關鍵字。

5. `models.py`
- 定義 `Keyword`、`PredictionRecord`、`KeywordMatch`。

---

## 對外導出（依 `__init__.py`）

1. `Keyword`
2. `KeywordMatch`
3. `PredictionRecord`
4. `KeywordLoader`
5. `KeywordManager`
6. `get_keyword_manager`
7. `MarketKeywords`
8. `KeywordLearner`

---

## 資料來源與存儲

1. 配置來源（優先）
- `config/keywords/*.json`
- `config/keywords/_index.json`
- 備援：`config/market_keywords.json`

2. 查詢/預測資料庫
- `config/market_keywords.db`

3. 學習資料庫
- `config/keyword_learning.db`

---

## 實作現況

1. `KeywordManager` 與 `KeywordLearner` 為兩條責任線
2. `static_utils.py` 與 `manager.py` 方法對應已一致
3. `__init__.py` 導出已含 `KeywordLearner`
4. `KeywordManager` 同時處理：
   - `find_matches()`
   - `record_prediction()` / `verify_prediction()`
   - `get_importance_score()` / `get_sentiment_bias()`
   - `update_keywords_from_trending()` / `refresh_stale_keywords()`
5. `KeywordLearner` 主要處理較慢的學習回饋流程：
   - `log_prediction()`
   - `validate_and_learn()`
   - `_update_keyword_weight()`
   - `get_learning_stats()`

## 子模組邊界

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到檔案與主類別層級。

## 維護邊界

1. 這層只描述 keyword 子模組的資料流、角色分工與持久化位置。
2. 關鍵字 JSON schema 若有新增欄位，需同步更新 `models.py` 與本文件。
3. 不在此文件維護全 analysis 層架構，避免和上層 README 重複。

---

> 上層架構說明：[analysis README](../README.md)
