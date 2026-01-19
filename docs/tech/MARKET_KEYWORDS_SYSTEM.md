# 市場關鍵字自適應系統 技術手冊

> **建立日期**: 2026-01-19  
> **版本**: v2.0  
> **狀態**: ✅ 完成  
> **檔案位置**: `src/bioneuronai/market_keywords.py`

---

## 📋 功能概述

市場關鍵字自適應系統用於識別和追蹤會影響加密貨幣市場的重要關鍵字。系統會根據每個關鍵字的預測準確度，自動調整其權重。

### 核心特點

1. **日期追蹤** - 每個關鍵字都有新增日期和最後更新日期
2. **自適應權重** - 根據預測結果動態調整權重
3. **兩階段預測** - 先記錄預測，3天後驗證結果
4. **SQLite 存儲** - 持久化預測歷史記錄
5. **過時檢測** - 自動標記超過90天未更新且準確率低的關鍵字

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    KeywordManager                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Keyword    │    │ Prediction  │    │  SQLite DB  │     │
│  │  (98個)     │───>│  Record     │───>│  Storage    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                   │            │
│         v                  v                   v            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              自適應權重調整引擎                      │   │
│  │  • 正確預測: 權重 × 1.08                            │   │
│  │  • 錯誤預測: 權重 × 0.92                            │   │
│  │  • 權重範圍: 0.3 ~ 2.0                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 資料結構

### Keyword (關鍵字)

```python
@dataclass
class Keyword:
    keyword: str           # 關鍵字
    category: str          # 類別: person, institution, event, coin
    base_weight: float     # 基礎權重 (1.0-3.0)
    dynamic_weight: float  # 動態權重 (0.3-2.0，根據準確率調整)
    sentiment_bias: str    # 情感偏向: positive, negative, neutral, uncertain
    description: str       # 描述
    added_date: str        # 新增日期 (YYYY-MM-DD)
    last_updated: str      # 最後更新日期
    hit_count: int         # 命中次數
    prediction_count: int  # 預測次數
    correct_count: int     # 正確預測次數
```

### PredictionRecord (預測記錄)

```python
@dataclass
class PredictionRecord:
    id: int                           # 記錄ID
    keyword: str                      # 關鍵字
    news_title: str                   # 新聞標題
    predicted_direction: str          # 預測方向
    actual_direction: Optional[str]   # 實際方向
    price_before: float               # 預測時價格
    price_after: Optional[float]      # 驗證時價格
    price_change_pct: Optional[float] # 價格變動百分比
    is_correct: Optional[bool]        # 是否正確
    created_at: str                   # 建立時間
    verified_at: Optional[str]        # 驗證時間
```

---

## 🔧 使用方式

### 基本使用

```python
from src.bioneuronai.market_keywords import KeywordManager, MarketKeywords

# 方式1: 使用 KeywordManager (完整功能)
km = KeywordManager()

# 方式2: 使用 MarketKeywords 靜態類 (簡化接口，向下兼容)
matches = MarketKeywords.find_matches("Fed raises interest rate")
```

### 新聞分析

```python
# 找出匹配的關鍵字
matches = km.find_matches("Federal Reserve raises interest rate")
for m in matches:
    print(f"{m.keyword}: 權重={m.effective_weight}, 情感={m.sentiment_bias}")

# 計算重要性分數 (0-10)
score, keywords = km.get_importance_score("BlackRock Bitcoin ETF approved")
print(f"重要性: {score}/10, 關鍵字: {keywords}")

# 判斷情感傾向
sentiment, strength = km.get_sentiment_bias("SEC files lawsuit against Binance")
print(f"情感: {sentiment}, 強度: {strength:.0%}")

# 是否為高影響新聞
is_high, high_kw = km.is_high_impact_news("Major hack at exchange")
print(f"高影響: {is_high}, 關鍵字: {high_kw}")
```

### 兩階段預測記錄 (自適應學習)

```python
# 第一步: 新聞出現時記錄預測
pred_id = km.record_prediction(
    keyword="fed",
    predicted_direction="negative",  # 預測市場會跌
    price_before=65000.0,
    news_title="Fed hints at rate hike"
)
print(f"預測已記錄，ID: {pred_id}")

# 第二步: 3天後驗證結果
km.verify_prediction(
    prediction_id=pred_id,
    actual_direction="negative",  # 實際市場下跌
    price_after=63500.0
)
# 系統會自動:
# - 判斷預測是否正確
# - 調整關鍵字權重
# - 更新準確率統計
```

### 查詢統計

```python
# 整體準確率
accuracy, correct, total = km.get_overall_accuracy()
print(f"整體準確率: {accuracy:.1%} ({correct}/{total})")

# 預測歷史
history = km.get_prediction_history(keyword="fed", limit=10)
for record in history:
    print(f"[{record.created_at}] 預測:{record.predicted_direction} "
          f"實際:{record.actual_direction} 正確:{record.is_correct}")

# 關鍵字表現排名
performance = km.get_keyword_performance(min_predictions=5)
for p in performance[:10]:
    print(f"{p['keyword']}: 準確率={p['accuracy']:.1%}")

# 過時關鍵字
stale = km.get_stale_keywords()
print(f"過時關鍵字數: {len(stale)}")
```

---

## 📁 預設關鍵字 (98個)

### 分類統計

| 類別 | 數量 | 說明 |
|------|------|------|
| person | 24 | 重要人物 (Powell, Musk, Saylor...) |
| institution | 20 | 機構 (Fed, SEC, BlackRock...) |
| event | 42 | 事件 (rate hike, ETF, hack...) |
| coin | 12 | 幣種 (BTC, ETH, SOL...) |

### 高權重關鍵字 (base_weight ≥ 2.5)

| 關鍵字 | 類別 | 基礎權重 | 情感偏向 |
|--------|------|----------|----------|
| fed / federal reserve | institution | 3.0 | uncertain |
| powell / jerome powell | person | 3.0 | uncertain |
| rate hike | event | 3.0 | negative |
| rate cut | event | 3.0 | positive |
| etf approved | event | 3.0 | positive |
| hack | event | 3.0 | negative |
| sec | institution | 2.8 | uncertain |
| yellen | person | 2.8 | uncertain |
| stolen | event | 2.8 | negative |
| ban / banned | event | 2.8 | negative |
| bankruptcy | event | 2.8 | negative |
| halving | event | 2.8 | positive |

---

## 🗄️ 存儲位置

| 檔案 | 用途 |
|------|------|
| `config/market_keywords.db` | SQLite 主資料庫 (關鍵字 + 預測歷史) |
| `config/market_keywords.json` | JSON 備份 (關鍵字設定) |

---

## 🔗 整合位置

### news_analyzer.py (已整合)

```python
# 第 267-279 行: 重要性評分加成
kw_score, matched_keywords = MarketKeywords.get_importance_score(...)
keyword_bonus = min(kw_score * 0.3, 3.0)  # 最多 +3 分

# 第 289 行: 事件類型檢測
matches = MarketKeywords.find_matches(text)
```

### crypto_futures_trader.py (待整合)

- [ ] 新聞觸發交易時自動記錄預測
- [ ] 定時任務：3天後自動驗證預測結果

---

## ⚙️ 配置參數

```python
class KeywordManager:
    # 權重調整參數
    WEIGHT_INCREASE_FACTOR = 1.08  # 正確預測時增加 8%
    WEIGHT_DECREASE_FACTOR = 0.92  # 錯誤預測時減少 8%
    MAX_DYNAMIC_WEIGHT = 2.0       # 最大動態權重
    MIN_DYNAMIC_WEIGHT = 0.3       # 最小動態權重
```

---

## 📈 權重計算公式

```
有效權重 = 基礎權重 × 動態權重

動態權重調整:
- 預測正確: dynamic_weight × 1.08
- 預測錯誤: dynamic_weight × 0.92
- 範圍限制: 0.3 ≤ dynamic_weight ≤ 2.0

過時判斷:
- 超過 90 天未更新 且 準確率 < 40%
```

---

## 🧪 測試命令

```bash
# 執行測試
python -m src.bioneuronai.market_keywords
```

---

## 📝 待辦事項

- [ ] 整合到交易流程，自動記錄和驗證預測
- [ ] 新增關鍵字管理 UI
- [ ] 定時清理過時關鍵字
- [ ] 導出/導入關鍵字設定功能

---

## 📚 相關文件

- [新聞分析系統](./NEWS_ANALYZER_SYSTEM.md) (待建立)
- [交易策略系統](./TRADING_STRATEGIES.md) (待建立)
