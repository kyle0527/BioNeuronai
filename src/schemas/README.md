# BioNeuronAI Schemas - 數據模型架構

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![Type Checked](https://img.shields.io/badge/type_checked-mypy-blue.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Schema Version](https://img.shields.io/badge/schema_version-2.3.0-orange.svg)]()

> **✅ 系統狀態**: 100% 功能完整，零錯誤零警告，Pydantic v2 完全兼容，專為幣安期貨交易設計  
> **🔄 最後更新**: 2026年2月14日  
> **📋 符合標準**: [PEP 257](https://peps.python.org/pep-0257/), [Pydantic v2 官方標準](https://docs.pydantic.dev/), [幣安期貨 API 官方文檔](https://developers.binance.com/docs/derivatives)

**BioNeuronAI Schemas** 是 BioNeuronAI 交易系統的**核心數據基準**，基於 Pydantic v2 構建，提供完整的類型安全、數據驗證和序列化功能，專為 AI 驅動的加密貨幣期貨交易而設計。

> ⚠️ **重要**: 此資料夾是整個專案的**數據定義基準 (Single Source of Truth)**。所有類型定義、枚舉、常數都應在此定義，其他模組只能導入使用，不可重複定義。

---

## 📑 目錄

- [🎯 核心特性](#-核心特性)
- [📊 模組統計](#-模組統計)
- [📂 目錄結構](#-目錄結構)
- [⚖️ 枚舉/結構標準](#️-枚舉結構標準)
- [🎨 核心模組說明](#-核心模組說明)
- [🚀 快速開始](#-快速開始)
- [📋 完整 API 參考](#-完整-api-參考)
- [📝 最佳實踐](#-最佳實踐)
- [🔄 Event Sourcing 架構](#-event-sourcing-架構)
- [🤖 機器學習模型](#-機器學習模型)
- [📊 回測系統](#-回測系統)
- [🔔 警報系統](#-警報系統)

---

## 🎯 核心特性

### 🏛️ Single Source of Truth (唯一真相來源)
- ✅ **集中定義**: 所有枚舉、類型、常數在此統一定義
- ✅ **禁止重複**: 其他模組只能導入，不可重新定義
- ✅ **一致性保證**: 確保整個系統使用相同的數據結構
- ✅ **版本控制**: SCHEMA_VERSION = "2.3.0"，與系統版本同步

### 🔧 企業級品質標準
- ✅ **零錯誤零警告**: 通過 SonarQube 品質檢查，達到生產環境標準
- ✅ **Pydantic v2 官方標準**: 完全符合 [Pydantic v2 文檔](https://docs.pydantic.dev/) 的最佳實踐
- ✅ **幣安期貨 API 標準**: 嚴格按照 [幣安官方文檔](https://developers.binance.com/docs/derivatives) 設計
- ✅ **Python 標準規範**: 遵循 [PEP 257](https://peps.python.org/pep-0257/) 文檔字符串規範
- ✅ **高精度計算**: 使用 Decimal 確保金融計算精度（符合 IEEE 754 標準）

### 🏗️ 先進架構模式
- ✅ **Event Sourcing**: 不可變事件日志，完整審計追蹤
- ✅ **ML/AI 整合**: 機器學習模型生命週期管理
- ✅ **智能警報**: 多渠道通知系統
- ✅ **高級回測**: 走向前分析、蒙地卡羅模擬

---

## 📊 模組統計

**根據實際程式碼統計（2026年2月14日驗證）**：

| 項目 | 數量 | 說明 |
|------|------|------|
| **核心檔案** | 19 個 | 包含 README.md，新增 5 個模組 |
| **枚舉定義** | 37 個 | enums.py (30) + rag.py (7) |
| **Pydantic 模型** | 75+ 個 | Event Sourcing, ML, Backtesting, Alerts |
| **覆蓋領域** | 14 大領域 | 新增：事件溯源、機器學習、回測、警報、類型定義 |
| **類型安全** | 100% | 零 Pylance 錯誤/警告，通過 SonarQube 檢查 |

---

## 📂 目錄結構

```
schemas/
├── __init__.py          # 統一導入入口 (v2.3.0 完整導出)
├── types.py             # 🆕 可重用類型定義和版本控制
├── enums.py             # 核心枚舉定義 (30 個標準枚舉 + 7 個新增)
├── events.py            # 🆕 Event Sourcing 事件模型
├── backtesting.py       # 🆕 策略回測模型
├── ml_models.py         # 🆕 機器學習模型架構
├── alerts.py            # 🆕 智能警報系統
├── trading.py           # 交易信號模型 (增強驗證器)
├── orders.py            # 訂單相關模型 (幣安期貨專用)
├── positions.py         # 倉位管理模型 (幣安期貨專用)
├── market.py            # 市場數據模型
├── portfolio.py         # 投資組合模型
├── risk.py              # 風險管理模型
├── strategy.py          # 策略配置模型
├── api.py               # API 通信模型
├── commands.py          # 命令系統模型 (AIVA Common v6.3)
├── database.py          # 資料庫操作模型
├── rag.py               # RAG 和事件系統模型
└── README.md            # 本文件 (基準文檔)
```

---

## ⚖️ 枚舉/結構標準

**BioNeuronAI 採用嚴格的枚舉/結構定義優先級制度**：

### 🏅 第1優先級：國際標準/官方規範 (最高優先級)

**必須完全遵循官方定義，不可隨意修改**

| 枚舉 | 來源 | 說明 |
|------|------|------|
| `OrderType` | 幣安期貨 API | MARKET, LIMIT, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET |
| `OrderSide` | 幣安期貨 API | BUY, SELL |
| `OrderStatus` | 幣安期貨 API | NEW, PARTIALLY_FILLED, FILLED, CANCELED, PENDING_CANCEL, REJECTED, EXPIRED, EXPIRED_IN_MATCH |
| `TimeInForce` | 幣安期貨 API | GTC, IOC, FOK, GTX, RPI (2025-11-18 新增) |
| `TimeFrame` | 幣安 Kline API | 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M |

### 🥈 第2優先級：程式語言標準庫

| 枚舉 | 說明 |
|------|------|
| `Environment` | PRODUCTION, TESTNET, STAGING, TESTING, DEVELOPMENT |

### 🥉 第3優先級：BioNeuronAI 統一定義 (系統內部標準)

| 枚舉 | 說明 | 值 |
|------|------|-----|
| `RiskLevel` | 風險等級 | LOW, MEDIUM, HIGH, CRITICAL |
| `PositionType` | 持倉類型 | LONG, SHORT |
| `SignalType` | 交易信號 | BUY, SELL, HOLD |
| `SignalStrength` | 信號強度 | WEAK, MODERATE, STRONG, VERY_STRONG |
| `StrategyState` | 策略狀態 | ACTIVE, INACTIVE, PAUSED, ERROR, STOPPED |
| `CommandType` | 命令類型 | TRADING, ANALYSIS, PORTFOLIO, RISK_MANAGEMENT, MARKET_DATA, SYSTEM, AI_MODEL |
| `CommandStatus` | 命令狀態 | PENDING, RUNNING, COMPLETED, FAILED, TIMEOUT, CANCELED |
| `EventType` | 事件類型 | WAR, GEOPOLITICAL, HACK, SECURITY_BREACH, REGULATION, LEGAL, MACRO, FED, EARNINGS, PARTNERSHIP, EXCHANGE_ISSUE, LISTING, NETWORK_ISSUE, UPGRADE, OTHER |
| `EventIntensity` | 事件強度 | LOW, MEDIUM, HIGH, EXTREME |
### 🚀 第3.5優先級：Event Sourcing & AI/ML 新增 (2026-02-14)

| 枚舉 | 說明 | 值 |
|------|----|-----|
| `TradeEventType` | 交易事件類型 | 25 個值：ORDER_PLACED, POSITION_OPENED, STOP_LOSS_TRIGGERED 等 |
| `BacktestStatus` | 回測狀態 | PENDING, RUNNING, COMPLETED, FAILED, CANCELED |
| `PredictionType` | 預測類型 | PRICE, DIRECTION, VOLATILITY, TREND, REVERSAL, SENTIMENT |
| `ModelStatus` | 模型狀態 | TRAINING, READY, DEPLOYED, DEPRECATED, FAILED |
| `AlertSeverity` | 警報嚴重性 | INFO, WARNING, CRITICAL, EMERGENCY |
| `AlertType` | 警報類型 | 15 個值：價格、技術指標、風險、系統警報 |
| `NotificationChannel` | 通知渠道 | EMAIL, SMS, TELEGRAM, DISCORD, WEBHOOK, IN_APP |
### 🏃 第4優先級：模組專屬枚舉 (最低優先級)

| 枚舉 | 模組 | 說明 |
|------|------|------|
| `StrategyType` | 策略分析 | 16 種策略類型 (AI_ML, AI_FUSION, TECHNICAL, FUNDAMENTAL, QUANTITATIVE, TREND_FOLLOWING, MEAN_REVERSION, BREAKOUT, SWING_TRADING, SCALPING, ARBITRAGE, MOMENTUM, GRID_TRADING, VOLATILITY_TRADING, NEWS_TRADING, PAIR_TRADING) |
| `MarketRegime` | 市場分析 | 11 種市場體制 (BULL, BEAR, SIDEWAYS, VOLATILE, QUIET, TRENDING_BULL, TRENDING_BEAR, SIDEWAYS_LOW_VOL, SIDEWAYS_HIGH_VOL, VOLATILE_UNCERTAIN, BREAKOUT_POTENTIAL) |
| `MarketCondition` | 市場分析 | TRENDING_UP, TRENDING_DOWN, RANGING, BREAKOUT, REVERSAL, HIGH_VOLATILITY, LOW_VOLATILITY |
| `MarketState` | 市場分析 | OPEN, CLOSED, PRE_MARKET, POST_MARKET, HALTED, MAINTENANCE |
| `Complexity` | 策略選擇 | SIMPLE, MEDIUM, COMPLEX |
| `DatabaseOperation` | 資料庫 | CREATE, READ, UPDATE, DELETE, BULK_INSERT, BULK_UPDATE |
| `DatabaseStatus` | 資料庫 | CONNECTED, DISCONNECTED, CONNECTING, ERROR, MAINTENANCE |
| `ApiStatus` | API 監控 | ONLINE, OFFLINE, MAINTENANCE, LIMITED, ERROR |

---

## 🎨 核心模組說明

### 0️⃣ 類型定義和版本控制 (types.py) - 🆕 新增

**全系統版本控制和可重用類型定義**

```python
from schemas.types import (
    SCHEMA_VERSION,        # "2.3.0" - 系統版本
    PositiveDecimal,       # 正數 Decimal 類型
    Percentage,            # 百分比 (0-100)
    Leverage,              # 槓桿 (1-125)
    RSIValue,              # RSI 指標 (0-100)
    BinanceSymbol,         # 幣安交易對
    USDTSymbol,            # USDT 交易對
    Price,                 # 價格類型
    Quantity,              # 數量類型
)

# 版本檢查
print(f"當前 Schema 版本: {SCHEMA_VERSION}")
```

### 1️⃣ 枚舉定義 (enums.py) - 30 個枚舉 + 7 個新增

```python
from schemas.enums import (
    # 第1優先級 - 幣安官方標準
    OrderType, OrderSide, OrderStatus, TimeInForce, TimeFrame,
    
    # 第2優先級 - 語言標準
    Environment,
    
    # 第3優先級 - 系統統一
    RiskLevel, PositionType, SignalType, SignalStrength,
    StrategyState, CommandType, CommandStatus,
    EventType, EventIntensity,
    
    # 新增 Event Sourcing & AI/ML 枚舉 (2026-02-14)
    TradeEventType, BacktestStatus, PredictionType,
    ModelStatus, AlertSeverity, AlertType, NotificationChannel,
    
    # 第4優先級 - 模組專屬
    StrategyType, MarketRegime, MarketCondition, MarketState,
    Complexity, DatabaseOperation, DatabaseStatus, ApiStatus,
)
```

### 2️⃣ Event Sourcing 事件溯源 (events.py) - 🆕 新增

**不可變事件日誌，完整審計追蹤**

| 模型 | 說明 |
|-----------|---------|
| `EventMetadata` | 事件元數據 |
| `TradeEvent` | 交易事件基類 |
| `OrderEvent` | 訂單事件 |
| `PositionEvent` | 倉位事件 |
| `RiskEvent` | 風險事件 |
| `EventStore` | 事件倉庫 |
| `EventQuery` | 事件查詢 |

```python
from schemas.events import TradeEvent, EventMetadata
from schemas.enums import TradeEventType

# 建立不可變事件
event = TradeEvent(
    event_type=TradeEventType.ORDER_PLACED,
    aggregate_id="order_123",
    aggregate_type="order",
    payload={"symbol": "BTCUSDT", "side": "BUY"},
    metadata=EventMetadata(source="trading_engine", version="1.0")
)
```

### 3️⃣ 機器學習模型 (ml_models.py) - 🆕 新增

**AI/ML 模型生命週期管理**

| 模型 | 說明 |
|-----------|---------|
| `FeatureConfig` | 特徵配置 |
| `ModelConfig` | 模型配置 |
| `ModelMetrics` | 模型指標 |
| `ModelPrediction` | 模型預測 |
| `ModelRegistry` | 模型註冊表 |
| `TrainingJob` | 訓練任務 |

```python
from schemas.ml_models import ModelConfig, PredictionType

config = ModelConfig(
    model_name="LSTM_BTCUSDT",
    model_type="lstm",
    prediction_type=PredictionType.PRICE,
    sequence_length=60,
    prediction_horizon=1
)
```

### 4️⃣ 回測系統 (backtesting.py) - 🆕 新增

**高級策略回測和模擬**

| 模型 | 說明 |
|-----------|---------|
| `BacktestConfig` | 回測配置 |
| `TradeRecord` | 交易記錄 |
| `BacktestResult` | 回測結果 |
| `WalkForwardResult` | 走向前分析結果 |
| `MonteCarloResult` | 蒙地卡羅模擬結果 |

```python
from schemas.backtesting import BacktestConfig
from datetime import datetime

config = BacktestConfig(
    strategy_name="Trend_Following",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=Decimal("100000.00"),
    commission_rate=Decimal("0.001")
)
```

### 5️⃣ 警報系統 (alerts.py) - 🆕 新增

**智能警報和多渠道通知**

| 模型 | 說明 |
|-----------|---------|
| `AlertCondition` | 警報條件 |
| `AlertRule` | 警報規則 |
| `AlertEvent` | 警報事件 |
| `NotificationConfig` | 通知配置 |
| `AlertSummary` | 警報摘要 |

```python
from schemas.alerts import AlertRule, AlertCondition
from schemas.enums import AlertType, AlertSeverity

rule = AlertRule(
    name="BTC 價格突破",
    alert_type=AlertType.PRICE_ABOVE,
    severity=AlertSeverity.WARNING,
    metric_name="mark_price",
    condition=AlertCondition(
        condition_type="greater_than",
        target_value=100000.0
    )
)
```

### 6️⃣ 策略模型 (strategy.py) - 5 個模型 + 1 個常數

| 模型/常數 | 說明 |
|-----------|------|
| `StrategyConfig` | 策略配置 (運行時狀態) |
| `StrategySelection` | 策略選擇結果 |
| `StrategyRecommendation` | **完整策略推薦** (2026-01-25 新增) - 包含權重分配、推理說明、風險設定、事件調整 |
| `StrategyPerformanceMetrics` | 策略績效指標 |
| `TradeSetup` | 交易設置 |
| `STRATEGY_MARKET_FIT` | **策略-市場適配表** (2026-01-25 新增) - 定義每種策略在不同市場體制的適合度 |

```python
from schemas.strategy import (
    StrategyConfig,
    StrategySelection,
    StrategyRecommendation,  # 新增
    StrategyPerformanceMetrics,
    TradeSetup,
    STRATEGY_MARKET_FIT,  # 新增
)

# 使用 STRATEGY_MARKET_FIT
fit = STRATEGY_MARKET_FIT[StrategyType.TREND_FOLLOWING]
print(fit['best'])   # [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR]
print(fit['avoid'])  # [MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.VOLATILE_UNCERTAIN]
```

### 7️⃣ 交易信號 (trading.py) - 增強驗證器

**新增 4 個商務邏輯驗證器**

```python
from schemas.trading import TradingSignal
from schemas.enums import SignalType

# 自動驗證止損、目標價格和風險報酬比
signal = TradingSignal(
    symbol="BTCUSDT",
    signal_type=SignalType.BUY,
    confidence=0.85,
    entry_price=50000.0,
    stop_loss=49000.0,     # 自動驗證：買入信號止損 < 進場價
    target_price=52000.0,  # 自動驗證：買入信號目標 > 進場價
)
# 自動驗證風險報酬比 >= 1:1.5 (高信心度)
```

### 8️⃣ 其他核心模組

| 模組 | 主要模型 | 說明 |
|------|---------|---------|
| `api.py` | ApiCredentials, ApiResponse, BinanceApiError, WebSocketMessage, ExchangeInfo | API 通信 |
| `orders.py` | BinanceOrderRequest, BinanceOrderResponse, OrderBook | 訂單管理 |
| `positions.py` | BinancePosition, PositionRisk, AccountBalance | 倉位管理 |
| `market.py` | MarketData | 市場數據 |
| `portfolio.py` | Portfolio, PortfolioSummary, PortfolioAnalytics, RiskMetrics | 投資組合 |
| `risk.py` | RiskParameters, PositionSizing, PortfolioRisk, RiskAlert | 風險管理 |
| `database.py` | DatabaseConfig, DatabaseQuery, DatabaseResult, DatabaseConnection, TradingDataRecord | 資料庫 |
| `commands.py` | AICommand, AICommandResult, TradingCommand, AnalysisCommand | 命令系統 |
| `rag.py` | EventContext, EventRule, RAGRiskItem, PreTradeCheckRequest | RAG 系統 |

---

## 🚀 快速開始

### 基本使用

```python
# 從統一入口導入
from schemas import (
    # 版本和類型
    SCHEMA_VERSION, PositiveDecimal, BinanceSymbol,
    
    # 枚舉
    StrategyType, MarketRegime, Complexity, TradeEventType,
    EventType, EventIntensity, RiskLevel, PredictionType,
    OrderType, OrderSide, TimeInForce, AlertType,
    
    # Event Sourcing
    TradeEvent, EventMetadata, EventStore,
    
    # 機器學習
    ModelConfig, ModelPrediction, TrainingJob,
    
    # 回測系統
    BacktestConfig, BacktestResult,
    
    # 警報系統
    AlertRule, AlertEvent, NotificationConfig,
    
    # 策略系統
    StrategyRecommendation, StrategyConfig,
    BinanceOrderRequest, BinancePosition,
    
    # 常數
    STRATEGY_MARKET_FIT,
)

# 檢查版本
print(f"Schema 版本: {SCHEMA_VERSION}")  # "2.3.0"

# 建立交易事件
event = TradeEvent(
    event_type=TradeEventType.ORDER_PLACED,
    aggregate_id="order_123",
    aggregate_type="order",
    payload={"symbol": "BTCUSDT", "side": "BUY"},
    metadata=EventMetadata(source="trading_engine", version="1.0")
)

# 建立 ML 預測
prediction = ModelPrediction(
    model_id="lstm_model_001",
    symbol="BTCUSDT",
    prediction_type=PredictionType.PRICE,
    predicted_value=52000.0,
    confidence=0.85,
    current_price=50000.0
)

# 建立警報規則
alert_rule = AlertRule(
    name="BTC 價格突破",
    alert_type=AlertType.PRICE_ABOVE,
    metric_name="mark_price",
    condition=AlertCondition(
        condition_type="greater_than",
        target_value=100000.0
    )
)
```
|------|------|
| `EventContext` | **事件上下文** (2026-01-25 新增) - 包含事件類型、強度、影響評分、建議動作 |
| `EventRule` | **事件規則** (2026-01-25 新增) - 定義事件觸發條件和處理邏輯 |
| `RAGRiskItem` | RAG 風險項目 |
| `RAGNewsItem` | RAG 新聞項目 |
| `PreTradeCheckRequest` | 交易前檢查請求 |
| `PreTradeCheckResponse` | 交易前檢查響應 |
| `SearchResult` | 搜索結果 |
| `RetrievalQuery` | 檢索查詢 |
| `RetrievalResult` | 檢索結果 |
| `KnowledgeDocumentSchema` | 知識文檔結構 |

```python
from schemas.rag import EventContext, EventRule
from schemas.enums import EventType, EventIntensity

# 創建事件上下文
context = EventContext(
    event_type=EventType.HACK,
    intensity=EventIntensity.HIGH,
    impact_score=-7.5,
    suggested_action="reduce_position",
    affected_symbols=["BTCUSDT", "ETHUSDT"],
)
```

### 4️⃣ 其他核心模組

| 模組 | 主要模型 | 說明 |
|------|---------|------|
| `api.py` | ApiCredentials, ApiResponse, BinanceApiError, WebSocketMessage, ExchangeInfo | API 通信 |
| `orders.py` | BinanceOrderRequest, BinanceOrderResponse, OrderBook | 訂單管理 |
| `positions.py` | BinancePosition, PositionRisk, AccountBalance | 倉位管理 |
| `market.py` | MarketData | 市場數據 |
| `portfolio.py` | Portfolio, PortfolioSummary, PortfolioAnalytics, RiskMetrics | 投資組合 |
| `risk.py` | RiskParameters, PositionSizing, PortfolioRisk, RiskAlert | 風險管理 |
| `database.py` | DatabaseConfig, DatabaseQuery, DatabaseResult, DatabaseConnection, TradingDataRecord | 資料庫 |
| `commands.py` | AICommand, AICommandResult, TradingCommand, AnalysisCommand | 命令系統 |
| `trading.py` | TradingSignal | 交易信號 |

---

## 🚀 快速開始

### 基本使用

```python
# 從統一入口導入
from schemas import (
    # 枚舉
    StrategyType, MarketRegime, Complexity,
    EventType, EventIntensity, RiskLevel,
    OrderType, OrderSide, TimeInForce,
    
    # 模型
    StrategyRecommendation, StrategyConfig,
    EventContext, EventRule,
    BinanceOrderRequest, BinancePosition,
    
    # 常數
    STRATEGY_MARKET_FIT,
)

# 創建策略推薦
recommendation = StrategyRecommendation(
    primary_strategy=StrategyType.TREND_FOLLOWING,
    primary_confidence=0.85,
    market_regime=MarketRegime.TRENDING_BULL,
    risk_level=RiskLevel.MEDIUM,
    strategy_weights={
        "trend_following": 0.4,
        "momentum": 0.3,
        "breakout": 0.2,
    },
    reasoning=["市場體制: trending_bull", "趨勢跟隨策略在牛市表現最佳"],
)

# 查詢策略適配
fit = STRATEGY_MARKET_FIT[StrategyType.MEAN_REVERSION]
print(f"均值回歸最適合: {fit['best']}")
print(f"均值回歸應避免: {fit['avoid']}")
```

---

## 📋 完整 API 參考

### 從 `bioneuronai.schemas` 可導入的所有項目

#### 版本和類型 (types.py)
```python
SCHEMA_VERSION,        # "2.3.0"
PositiveDecimal, Percentage, Leverage, RSIValue,
BinanceSymbol, USDTSymbol, Price, Quantity, PnL
```

#### 枚舉類型 (37 個)
```python
# enums.py (30 個)
OrderType, OrderSide, OrderStatus, TimeInForce, TimeFrame,
Environment, RiskLevel, PositionType, SignalType, SignalStrength,
StrategyState, CommandType, CommandStatus, StrategyType,
DatabaseOperation, DatabaseStatus, MarketState, MarketRegime,
Complexity, MarketCondition, ApiStatus, EventType, EventIntensity,
# 新增 Event Sourcing & AI/ML (7 個)
TradeEventType, BacktestStatus, PredictionType, ModelStatus,
AlertSeverity, AlertType, NotificationChannel,

# rag.py (7 個)
RAGDocumentType, RAGCheckResult, RAGRiskFactor, NewsSentiment,
NewsCategory, SearchEngine, RetrievalSource
```

#### Pydantic 模型 (75+ 個)
```python
# Event Sourcing (7 個)
EventMetadata, TradeEvent, OrderEvent, PositionEvent, RiskEvent,
EventStore, EventQuery,

# 機器學習 (6 個)
FeatureConfig, ModelConfig, ModelMetrics, ModelPrediction,
ModelRegistry, TrainingJob,

# 回測系統 (5 個)
BacktestConfig, TradeRecord, BacktestResult,
WalkForwardResult, MonteCarloResult,

# 警報系統 (5 個)
AlertCondition, AlertRule, AlertEvent,
NotificationConfig, AlertSummary,

# 其他核心模型
MarketData, TradingSignal,
BinanceOrderRequest, BinanceOrderResponse, OrderBook,
BinancePosition, PositionRisk, AccountBalance,
Portfolio, PortfolioSummary, PortfolioAnalytics, RiskMetrics,
ApiCredentials, ApiResponse, BinanceApiError, WebSocketMessage, ExchangeInfo,
AICommand, AICommandResult, TradingCommand, AnalysisCommand,
RiskManagementCommand, SystemCommand,
DatabaseConfig, DatabaseQuery, DatabaseResult, DatabaseConnection,
TradingDataRecord, DatabaseService,
RiskParameters, PositionSizing, PortfolioRisk, RiskAlert,
StrategyConfig, StrategySelection, StrategyRecommendation,
StrategyPerformanceMetrics, TradeSetup,
RAGRiskItem, RAGNewsItem, PreTradeCheckRequest, PreTradeCheckResponse,
SearchResult, RetrievalQuery, RetrievalResult, KnowledgeDocumentSchema,
EventContext, EventRule
```

#### 常數
```python
STRATEGY_MARKET_FIT  # Dict[StrategyType, Dict[str, list[MarketRegime]]]
```
NewsCategory, SearchEngine, RetrievalSource
```

#### Pydantic 模型 (50+ 個)
```python
# 市場數據
MarketData

# 交易信號
TradingSignal

# 訂單管理
BinanceOrderRequest, BinanceOrderResponse, OrderBook

# 倉位管理
BinancePosition, PositionRisk, AccountBalance

# 投資組合
Portfolio, PortfolioSummary, PortfolioAnalytics, RiskMetrics

# API 通信
ApiCredentials, ApiResponse, BinanceApiError, WebSocketMessage, ExchangeInfo

# 命令系統
AICommand, AICommandResult, TradingCommand, AnalysisCommand,
RiskManagementCommand, SystemCommand

# 資料庫
DatabaseConfig, DatabaseQuery, DatabaseResult, DatabaseConnection,
TradingDataRecord, DatabaseService

# 風險管理
RiskParameters, PositionSizing, PortfolioRisk, RiskAlert

# 策略管理
StrategyConfig, StrategySelection, StrategyRecommendation,
StrategyPerformanceMetrics, TradeSetup

# RAG 系統
RAGRiskItem, RAGNewsItem, PreTradeCheckRequest, PreTradeCheckResponse,
SearchResult, RetrievalQuery, RetrievalResult, KnowledgeDocumentSchema,
EventContext, EventRule
```

#### 常數
```python
STRATEGY_MARKET_FIT  # Dict[StrategyType, Dict[str, list[MarketRegime]]]
```

---

## 📝 最佳實踐

### 1. Single Source of Truth 原則

```python
# ✅ 正確：從 schemas 導入
from schemas import StrategyType, MarketRegime

# ❌ 錯誤：在其他模組重新定義
class StrategyType(Enum):  # 不要這樣做！
    ...
```

### 2. 枚舉使用優先級

```python
# ✅ 使用官方標準 (第1優先級)
order = BinanceOrderRequest(
    type=OrderType.MARKET,  # 幣安官方標準
    side=OrderSide.BUY,
)

# ❌ 自定義與官方不符
order = BinanceOrderRequest(
    type="market_order",  # 錯誤！
    side="buy_side",       # 錯誤！
)
```

### 3. 金融精度

```python
from decimal import Decimal

# ✅ 使用 Decimal
position = BinancePosition(
    position_amt=Decimal("0.001"),
    entry_price=Decimal("50000.00"),
)

# ❌ 使用 float (精度問題)
position = BinancePosition(
    position_amt=0.001,  # 可能有精度問題
)
```

### 4. 類型安全

```python
from schemas import StrategyType, MarketRegime, STRATEGY_MARKET_FIT

# ✅ 類型安全的查詢
def get_suitable_strategies(regime: MarketRegime) -> list[StrategyType]:
    suitable = []
    for strategy, fit in STRATEGY_MARKET_FIT.items():
        if regime in fit['best'] or regime in fit['good']:
            suitable.append(strategy)
    return suitable
```

---

## 📊 變更歷史

### 2026-02-14 重大更新 (v2.3.0) - Event Sourcing & AI/ML 擴展
- ➕ **新增 5 個核心模組**: `types.py`, `events.py`, `backtesting.py`, `ml_models.py`, `alerts.py`
- ➕ **新增 7 個枚舉**: TradeEventType (25個值), BacktestStatus, PredictionType, ModelStatus, AlertSeverity, AlertType, NotificationChannel
- ➕ **新增 23+ 個模型**: Event Sourcing (7), ML (6), Backtesting (5), Alerts (5)
- ➕ **版本控制**: SCHEMA_VERSION = "2.3.0", 與系統版本同步
- ➕ **可重用類型**: PositiveDecimal, Percentage, Leverage, RSIValue, BinanceSymbol 等
- 🔧 **增強驗證**: TradingSignal 新增 4 個商務邏輯驗證器
- ✨ **企業級品質**: 通過 SonarQube 檢查，零錯誤零警告
- 🏢 **Event Sourcing**: 不可變事件日誌架構，完整審計追蹤
- 🤖 **AI/ML 整合**: 模型生命週期管理，特徵工程，預測對標
- 📈 **進階回測**: 走向前分析、蒙地卡羅模擬、風險指標
- 🔔 **智能警報**: 多渠道通知 (Email, Telegram, Discord, Webhook)

### 2026-01-25 更新 (v2.1.0)
- ➕ 新增 `StrategyRecommendation` 完整策略推薦模型
- ➕ 新增 `STRATEGY_MARKET_FIT` 策略-市場適配表常數
- ➕ 新增 `EventContext`, `EventRule` 事件系統模型
- ➕ 新增 `EventType`, `EventIntensity` 事件枚舉
- ➕ 新增 `Complexity` 複雜度枚舉
- ➕ 擴展 `MarketRegime` 新增詳細分類 (TRENDING_BULL, TRENDING_BEAR, 等)
- ➕ 擴展 `StrategyType` 新增 NEWS_TRADING, PAIR_TRADING
- 🔧 統一常數命名規範

### 2026-01-22 初版 (v2.0.0)
- 初始 schemas 架構建立
- 23 個標準枚舉
- 45+ 個 Pydantic 模型

---

## 🛑 官方文檔維護

請對照以下官方文檔：

- [Binance Futures Official API Documentation](https://developers.binance.com/docs/derivatives)
- [AIVA Common v6.3 Specification](https://aiva-common.readthedocs.io/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)

若官方 API 有更新，請優先修正 schemas 中的定義。

---

*最後更新: 2026年2月14日 | 版本: v2.3.0 | 作者: BioNeuronAI Team*
