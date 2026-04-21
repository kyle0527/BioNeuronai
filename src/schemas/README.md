# Schemas — 統一資料模型

> 路徑：`src/schemas/`
> 更新日期：2026-04-20
> 定位：全系統共用的 Pydantic v2 schema、enum、型別與常數來源

`schemas` 是 BioNeuronai 的資料定義基準。交易、策略、API、RAG、回測、風險、告警與外部資料結構都應優先從這裡匯入，避免在各模組重複定義相同 enum 或模型。

---

## 目錄

1. [實際結構](#實際結構)
2. [匯入方式](#匯入方式)
3. [主要模組](#主要模組)
4. [Enum 邊界](#enum-邊界)
5. [RAG 型別](#rag-型別)
6. [維護原則](#維護原則)

---

## 實際結構

```text
schemas/
├── __init__.py          # 統一匯出入口
├── types.py             # 共用型別、版本常數與驗證 helper
├── enums.py             # 系統 enum 定義
├── events.py            # Event Sourcing 模型
├── backtesting.py       # 回測模型
├── ml_models.py         # ML 模型生命週期資料結構
├── alerts.py            # 告警與通知模型
├── trading.py           # 交易信號模型
├── orders.py            # 訂單模型
├── positions.py         # 倉位模型
├── market.py            # 市場資料模型
├── portfolio.py         # 投資組合模型
├── risk.py              # 風險模型
├── strategy.py          # 策略配置與推薦模型
├── api.py               # REST / WebSocket API 模型
├── commands.py          # 命令模型
├── database.py          # 資料庫操作模型
├── external_data.py     # 外部市場資料模型
├── rag.py               # RAG、事件與檢索模型
├── py.typed
└── README.md
```

目前實際統計：

| 項目 | 數量 |
|------|-----:|
| Python 檔案 | 19 |
| Python 行數 | 5,935 |
| class 總數 | 147 |
| Enum class | 38 |
| Pydantic `BaseModel` class | 105 |

---

## 匯入方式

此目錄是頂層 Python package，不在 `bioneuronai/` 底下。正確匯入方式：

```python
from schemas import StrategyType, MarketRegime, TradingSignal
from schemas.rag import EventContext, RetrievalQuery, RetrievalSource
```

不要把 `schemas` 當成 `bioneuronai` 的子 package；目前它是 `src` 下的獨立頂層 package。

---

## 主要模組

| 檔案 | 主要內容 |
|------|----------|
| `types.py` | `SCHEMA_VERSION`、金融數值型別、symbol 型別與驗證 helper |
| `enums.py` | Binance / 系統 / 策略 / 市場 / 事件等 enum |
| `strategy.py` | `StrategyConfig`、`StrategyRecommendation`、`TradeSetup`、`STRATEGY_MARKET_FIT` |
| `trading.py` | `TradingSignal` 與交易信號驗證 |
| `risk.py` | `RiskParameters`、`PositionSizing`、`PortfolioRisk`、`RiskAlert` |
| `api.py` | API request/response、status、dashboard WebSocket 模型 |
| `rag.py` | `EventContext`、`EventRule`、`RetrievalQuery`、`RetrievalResult`、RAG item 模型 |
| `external_data.py` | Fear & Greed、global market、DeFi、stablecoin、macro event snapshot |
| `backtesting.py` | `BacktestConfig`、`TradeRecord`、`BacktestResult` 等 |
| `events.py` | `TradeEvent`、`OrderEvent`、`PositionEvent`、`RiskEvent` |
| `ml_models.py` | `ModelConfig`、`ModelPrediction`、`TrainingJob` |
| `alerts.py` | `AlertRule`、`AlertEvent`、`NotificationConfig` |

---

## Enum 邊界

跨模組共享 enum 應放在 `schemas`，模組內部只保留真正局部的 enum。

常用 enum：

```python
from schemas.enums import (
    OrderType,
    OrderSide,
    OrderStatus,
    TimeInForce,
    TimeFrame,
    Environment,
    RiskLevel,
    PositionType,
    SignalType,
    SignalStrength,
    StrategyState,
    CommandType,
    CommandStatus,
    StrategyType,
    MarketRegime,
    MarketCondition,
    MarketState,
    Complexity,
    EventType,
    EventIntensity,
    TradeEventType,
    BacktestStatus,
    PredictionType,
    ModelStatus,
    AlertSeverity,
    AlertType,
    NotificationChannel,
)
```

RAG 專用 enum 目前定義在 `schemas.rag`：

```python
from schemas.rag import (
    RAGDocumentType,
    RAGCheckResult,
    RAGRiskFactor,
    NewsSentiment,
    NewsCategory,
    SearchEngine,
    RetrievalSource,
)
```

---

## RAG 型別

`RetrievalSource`、`RetrievalQuery`、`RetrievalResult` 已統一由 `schemas.rag` 提供。`rag/core/retriever.py` 不再自行定義這些型別。

```python
from schemas.rag import RetrievalQuery, RetrievalSource

query = RetrievalQuery(
    query="BTC 大額轉帳風險",
    sources=[RetrievalSource.INTERNAL_KNOWLEDGE, RetrievalSource.NEWS_API],
    top_k=5,
    min_relevance=0.3,
)
```

`EventContext` 也是事件調權的共用型別，`StrategySelector`、`AIStrategyFusion`、`NewsAdapter` 都應以此為邊界。

---

## 維護原則

1. 新增跨模組資料結構時，先判斷是否應放在 `schemas`。
2. 若只在單一子模組內使用，保留在該模組本地，避免污染共用 schema。
3. 修改 enum value 前先搜尋全專案引用，避免破壞序列化資料與 DB 內容。
4. README 的統計數字應以實際檔案重新計算，不保留不可驗證的品質宣稱。

---

> 上層目錄：[src README](../README.md)
