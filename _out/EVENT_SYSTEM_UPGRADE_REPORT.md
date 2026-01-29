# 🧠 事件驅動交易系統升級報告

**版本**: v2.2.0  
**日期**: 2026-01-25  
**狀態**: ✅ 四步驟升級完成

---

## 📋 升級概述

本次升級實現了「新聞大腦」事件驅動架構，讓交易系統能夠感知並響應外部市場事件（如戰爭、駭客攻擊、監管行動等），而不僅僅是技術指標。

### 核心理念

**Before（舊架構）**:
```
新聞 → (人工閱讀) → 交易決策
```

**After（新架構）**:
```
新聞 → RuleBasedEvaluator → event_memory (DB) → EventContext → strategy_fusion
                    ↓
            Hard Stop 自動解析
```

---

## ✅ Step 1: 建立記憶 (Data Layer)

**檔案**: `src/bioneuronai/data/database_manager.py`

### 新增 `event_memory` 資料表

```sql
CREATE TABLE event_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,       -- WAR/HACK/REGULATION/MACRO/etc.
    headline TEXT NOT NULL,
    score REAL NOT NULL,            -- -1.0 到 +1.0
    status TEXT DEFAULT 'ACTIVE',   -- ACTIVE/RESOLVED
    termination_condition TEXT,     -- 結束條件描述
    embedding_id TEXT,              -- 預留給 NLP 向量
    source TEXT,
    source_confidence REAL DEFAULT 0.5,
    affected_symbols TEXT,          -- 逗號分隔
    metadata TEXT,
    created_at TEXT,
    resolved_at TEXT,
    updated_at TEXT
)
```

### 新增方法

| 方法 | 功能 |
|------|------|
| `save_event(event_info)` | 保存事件到資料庫 |
| `get_active_events(event_type, symbol)` | 查詢活躍事件 |
| `resolve_event(event_id, resolution_note)` | 解析（關閉）事件 |
| `calculate_total_event_score(symbol)` | 計算總事件分數 |

---

## ✅ Step 2: 改造身體 (Execution Layer)

**檔案**: `src/bioneuronai/strategies/strategy_fusion.py`

### 新增 `EventContext` 資料類別

```python
@dataclass
class EventContext:
    event_score: float = 0.0      # -10 到 +10
    event_type: str = "UNKNOWN"   # WAR, HACK, REGULATION, MACRO
    intensity: float = 0.0        # 0-1
    decay_factor: float = 1.0     # 時間衰減
    source_confidence: float = 0.5 # 來源可信度
    
    def get_effective_score(self) -> float:
        return self.event_score * self.decay_factor * self.source_confidence
```

### 新增 `_apply_asymmetric_filter()` 方法

- **極空環境** (`event_score < -7`): 阻擋做多信號
- **極多環境** (`event_score > 7`): 阻擋做空信號

### 新增 `_adjust_weights_by_event()` 方法

根據事件類型調整策略權重：

| 事件類型 | 效果 |
|---------|------|
| WAR | 趨勢追蹤 ↑, 震盪策略 ↓ |
| HACK | 動量策略 ↓, 均值回歸 ↓ |
| REGULATION | 所有策略 ↓ 50% |
| MACRO | 長週期策略 ↑ |

### 修改 `generate_fusion_signal()` 簽名

```python
def generate_fusion_signal(
    self,
    market_data: Dict,
    event_score: float = 0.0,           # NEW
    event_context: Optional[EventContext] = None  # NEW
) -> FusionSignal:
```

---

## ✅ Step 3: 打造大腦 (Perception Layer)

**檔案**: `src/bioneuronai/analysis/news_analyzer.py`

### 新增 `EventRule` 資料類別

```python
@dataclass
class EventRule:
    event_type: str              # WAR, HACK, REGULATION, MACRO
    trigger_keywords: List[str]  # 觸發關鍵字
    termination_keywords: List[str]  # 結束關鍵字 (Hard Stop)
    base_score: float            # -1.0 到 +1.0
    decay_hours: int = 24        # 衰減時間
    affected_symbols: Optional[List[str]] = None
```

### 新增 `RuleBasedEvaluator` 類別

**核心功能**:

1. **事件檢測**: 使用關鍵字規則檢測重大事件
2. **Hard Stop**: 檢測事件結束關鍵字，自動解析事件
3. **事件分數計算**: 為 strategy_fusion 提供 `event_score`

**預設規則**:

| 事件類型 | 基礎分數 | 衰減時間 | 觸發範例 |
|---------|---------|---------|---------|
| WAR | -0.8 | 72h | "war", "invasion", "missile" |
| HACK | -0.7 | 48h | "hacked", "exploit", "stolen" |
| REGULATION | -0.6 | 168h | "sec lawsuit", "crypto ban" |
| MACRO | -0.5 | 120h | "rate hike", "recession" |
| EXCHANGE_ISSUE | -0.65 | 48h | "withdrawal suspended" |
| ETF_APPROVAL | +0.8 | 72h | "etf approved" |
| INSTITUTIONAL | +0.6 | 48h | "institutional adoption" |

**使用方式**:

```python
from bioneuronai.analysis.news_analyzer import get_rule_evaluator

evaluator = get_rule_evaluator()

# 評估單則新聞
event = evaluator.evaluate_headline(
    headline="Breaking: Major exchange hacked, $100M stolen",
    source="Reuters",
    source_confidence=0.9
)

# 獲取當前事件分數
score, events = evaluator.get_current_event_score(symbol="BTCUSDT")
```

---

## ✅ Step 4: 接通神經 (Control Layer)

**檔案**: `src/bioneuronai/trading/plan_controller.py`

### 修改內容

1. **導入事件系統**:
```python
from ..analysis.news_analyzer import get_rule_evaluator, RuleBasedEvaluator
from ..strategies.strategy_fusion import EventContext
```

2. **初始化事件評估器**:
```python
def __init__(self):
    # ...
    self._rule_evaluator: Optional[RuleBasedEvaluator] = None
    if EVENT_SYSTEM_AVAILABLE:
        self._rule_evaluator = get_rule_evaluator()
```

3. **修改 Step 4 情緒分析**:
   - 調用 `get_current_event_score()` 查詢活躍事件
   - 構建 `EventContext` 供後續使用
   - 根據事件分數判斷 `breaking_news_risk`

4. **修改 `create_comprehensive_plan()`**:
   - 實際執行 Step 4 而非跳過
   - 將 `event_score` 和 `event_context` 存入 plan 結果
   - 當 `event_score < -0.5` 時發出警告

---

## 🔄 資料流程圖

```
┌─────────────────┐
│  外部新聞來源    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  RuleBasedEvaluator (新聞大腦)                   │
│  - evaluate_headline()                          │
│  - 關鍵字匹配 → 事件類型 + 基礎分數              │
│  - Hard Stop 檢測 → 自動解析事件                 │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  DatabaseManager.event_memory (事件記憶)         │
│  - 持久化存儲                                    │
│  - ACTIVE/RESOLVED 狀態追蹤                      │
│  - 支援查詢與過期清理                            │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  TradingPlanController.Step4                    │
│  - 查詢活躍事件                                  │
│  - 計算總 event_score                           │
│  - 構建 EventContext                            │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  AIStrategyFusion (執行層)                      │
│  - _apply_asymmetric_filter()                   │
│  - _adjust_weights_by_event()                   │
│  - 最終交易信號產出                              │
└─────────────────────────────────────────────────┘
```

---

## 🧪 測試建議

### 單元測試

```python
# 測試 RuleBasedEvaluator
def test_evaluate_headline():
    evaluator = RuleBasedEvaluator()
    
    # 測試駭客事件
    event = evaluator.evaluate_headline("Major exchange hacked!")
    assert event['event_type'] == 'HACK'
    assert event['score'] < 0
    
    # 測試 Hard Stop
    evaluator.evaluate_headline("Funds recovered after hack")
    # 應該自動解析 HACK 事件

# 測試 event_memory
def test_event_memory():
    from bioneuronai.data.database_manager import get_database_manager
    db = get_database_manager()
    
    # 保存事件
    db.save_event({
        'event_id': 'test_001',
        'event_type': 'HACK',
        'headline': 'Test event',
        'score': -0.7
    })
    
    # 查詢
    events = db.get_active_events(event_type='HACK')
    assert len(events) == 1
    
    # 解析
    db.resolve_event('test_001')
    events = db.get_active_events(event_type='HACK')
    assert len(events) == 0
```

### 整合測試

```python
async def test_plan_with_events():
    controller = TradingPlanController()
    
    # 模擬負面事件
    evaluator = controller._rule_evaluator
    evaluator.evaluate_headline("Breaking: SEC files lawsuit against major exchange")
    
    # 執行計劃
    plan = await controller.create_comprehensive_plan()
    
    # 驗證事件分數被計入
    assert plan['event_score'] < 0
    assert plan['steps_results'][4]['breaking_news_risk'] == 'ELEVATED'
```

---

## 📌 後續擴展

1. **NLP 向量化**: 使用 `embedding_id` 欄位存儲文章向量，實現語義相似度搜索
2. **自動新聞抓取**: 整合 RSS 或 API 自動評估新聞流
3. **事件權重學習**: 根據歷史準確度動態調整 `base_score`
4. **多語言支援**: 擴展關鍵字規則至中文新聞

---

## 📁 修改檔案清單

| 檔案 | 修改類型 | 行數變化 |
|------|---------|---------|
| `database_manager.py` | 新增表格 + 方法 | +180 行 |
| `strategy_fusion.py` | 新增類別 + 方法 | +150 行 (之前完成) |
| `news_analyzer.py` | 新增類別 | +280 行 |
| `plan_controller.py` | 修改 + 整合 | +60 行 |

---

**升級完成！** 🎉

系統現在具備了事件驅動交易能力，能夠：
- 自動檢測市場重大事件
- 持久化存儲事件記憶
- 根據事件調整交易策略權重
- 在極端環境下阻擋逆勢信號
