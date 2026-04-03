# 分析模組 — 關鍵字系統 (Keywords)

> **路徑**: `src/bioneuronai/analysis/keywords/`  
> **更新日期**: 2026-04-01  
> **文件焦點**: 子模組內部 API、資料流與持久化（分層說明請看上層 `analysis/README.md`）

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

---

## 角色分工

1. `KeywordManager`（`manager.py`）
- 主責高頻查詢、匹配、預測記錄、統計、SQLite/JSON 持久化。

2. `MarketKeywords`（`static_utils.py`）
- 提供靜態呼叫介面，內部代理 `KeywordManager`。

3. `KeywordLearner`（`learner.py`）
- 主責延遲驗證與學習資料維護，將結果回饋到關鍵字權重。

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

## 實作現況（已對齊程式碼）

1. `KeywordManager` 與 `KeywordLearner` 為兩條責任線，不再混為單一元件
2. `static_utils.py` 與 `manager.py` 方法對應已一致
3. `__init__.py` 導出已含 `KeywordLearner`

---

## 已移除的老舊/錯誤內容

1. 舊版行數/總行數陳述
2. 舊分工說法（查詢與學習責任混淆）
3. 舊路徑或舊 API 名稱
4. 與現行方法清單不一致的描述

---

> 上層架構說明：`src/bioneuronai/analysis/README.md`
