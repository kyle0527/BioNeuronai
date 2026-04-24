# Schemas

`src/schemas/` 是全專案共用的資料模型與 enum 邊界。這個資料夾目前沒有更深一層的 README，所以本文件直接負責說明主要檔案分工。

## 模組定位

`schemas` 的責任是集中管理跨模組共享的：

- Pydantic 模型
- enum
- 型別別名與驗證 helper
- 匯出邊界

若同一份資料結構會被 `bioneuronai`、`rag`、`backtest`、`api` 或訓練流程共同使用，優先放在這裡，而不是在各模組重複定義。

## 資料夾內容

- `__init__.py`
  統一匯出入口，集中 re-export 各子模組的主要型別。
- `types.py`
  `SCHEMA_VERSION`、金融數值型別、symbol 驗證與序列化 helper。
- `enums.py`
  系統級 enum，如訂單、策略、市場、事件、回測、模型與告警相關列舉。
- `market.py`
  市場資料模型。
- `external_data.py`
  外部資料快照模型，如恐慌貪婪、全球市場、DeFi、穩定幣、總體事件。
- `trading.py`
  `TradingSignal` 與交易信號資料結構。
- `orders.py`
  訂單請求、回應與 order book。
- `positions.py`
  倉位、風險與帳戶餘額。
- `portfolio.py`
  投資組合摘要、分析與風險指標。
- `risk.py`
  `RiskParameters`、`PositionSizing`、`PortfolioRisk`、`RiskAlert`。
- `strategy.py`
  `StrategyConfig`、`StrategySelection`、`StrategyRecommendation`、`TradeSetup`、`STRATEGY_MARKET_FIT`。
- `api.py`
  REST / WebSocket request、response、dashboard 資料模型。
- `commands.py`
  命令模型與命令結果。
- `database.py`
  資料庫設定、查詢、結果與服務模型。
- `events.py`
  event sourcing 相關模型。
- `backtesting.py`
  回測設定、交易紀錄、回測結果、walk-forward、Monte Carlo。
- `ml_models.py`
  特徵、模型設定、預測、訓練工作與 registry。
- `alerts.py`
  告警條件、規則、事件、通知設定與摘要。
- `rag.py`
  RAG 專用 enum 與模型，如 `RetrievalSource`、`RetrievalQuery`、`RetrievalResult`、`EventContext`、`EventRule`。

## 匯出邊界

`schemas.__init__` 目前會統一匯出大部分共用型別，但有兩點要注意：

1. 部分模組使用 `try/except ImportError` 包起來。
   目前 `risk.py`、`strategy.py`、`rag.py` 若匯入失敗，頂層匯出可能會缺少對應符號。
2. `schemas.api` 內除了 README 已列出的 REST 模型，還另外定義了聊天與 dashboard WebSocket 模型。

常見匯入方式：

```python
from schemas import StrategyType, MarketRegime, TradingSignal
from schemas.rag import RetrievalQuery, RetrievalResult, RetrievalSource
```

## 主要使用原則

1. 共用 enum 優先放 `enums.py`，不要在子模組各自複製。
2. RAG 專用型別優先放 `rag.py`，例如 `RetrievalSource` 與 `EventContext`。
3. API request / response 與 WebSocket payload 由 `api.py` 集中管理。
4. 修改 enum value 或 schema 欄位前，先搜尋全專案引用，避免破壞序列化資料與歷史資料。

## 文件層級

- 這個資料夾目前沒有更深一層的 README。
- 各 schema 檔案的責任範圍由本文件直接說明。
- 上一層文件見 [src/README.md](../README.md)。

## 相關文件

- [RAG 模組](../rag/README.md)
- [bioneuronai 模組](../bioneuronai/README.md)
