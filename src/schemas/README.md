# BioNeuronAI Schemas - 數據模型架構

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![Type Checked](https://img.shields.io/badge/type_checked-mypy-blue.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **✅ 系統狀態**: 100% 功能完整，Pydantic v2 完全兼容，專為幣安期貨交易設計  
> **🔄 最後更新**: 2026年1月25日  
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

---

## 🎯 核心特性

### 🏛️ Single Source of Truth (唯一真相來源)
- ✅ **集中定義**: 所有枚舉、類型、常數在此統一定義
- ✅ **禁止重複**: 其他模組只能導入，不可重新定義
- ✅ **一致性保證**: 確保整個系統使用相同的數據結構

### 基於官方標準設計
- ✅ **Pydantic v2 官方標準**: 完全符合 [Pydantic v2 文檔](https://docs.pydantic.dev/) 的最佳實踐
- ✅ **幣安期貨 API 標準**: 嚴格按照 [幣安官方文檔](https://developers.binance.com/docs/derivatives) 設計
- ✅ **Python 標準規範**: 遵循 [PEP 257](https://peps.python.org/pep-0257/) 文檔字符串規範
- ✅ **高精度計算**: 使用 Decimal 確保金融計算精度（符合 IEEE 754 標準）

---

## 📊 模組統計

**根據實際程式碼統計（2026年1月25日驗證）**：

| 項目 | 數量 | 說明 |
|------|------|------|
| **核心檔案** | 13 個 | 包含 README.md |
| **枚舉定義** | 30 個 | enums.py (23) + rag.py (7) |
| **Pydantic 模型** | 50+ 個 | 完整功能驗證 |
| **覆蓋領域** | 9 大領域 | 訂單、倉位、市場、風險、策略、API、資料庫、投資組合、事件系統 |
| **類型安全** | 100% | 零 Pylance 錯誤/警告 |

---

## 📂 目錄結構

```
schemas/
├── __init__.py          # 模組導出和公開 API (統一導入入口)
├── enums.py             # 核心枚舉定義 (23 個標準枚舉)
├── api.py               # API 通信模型
├── commands.py          # 命令系統模型 (AIVA Common v6.3)
├── database.py          # 資料庫操作模型
├── market.py            # 市場數據模型
├── orders.py            # 訂單相關模型 (幣安期貨專用)
├── portfolio.py         # 投資組合模型
├── positions.py         # 倉位管理模型 (幣安期貨專用)
├── rag.py               # RAG 和事件系統模型
├── risk.py              # 風險管理模型
├── strategy.py          # 策略配置模型
├── trading.py           # 交易信號模型
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

### 1️⃣ 枚舉定義 (enums.py) - 23 個枚舉

**系統核心枚舉定義，按優先級分類**

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
    
    # 第4優先級 - 模組專屬
    StrategyType, MarketRegime, MarketCondition, MarketState,
    Complexity, DatabaseOperation, DatabaseStatus, ApiStatus,
)
```

### 2️⃣ 策略模型 (strategy.py) - 5 個模型 + 1 個常數

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

### 3️⃣ RAG 和事件系統 (rag.py) - 7 個枚舉 + 10 個模型

**事件驅動交易系統的核心模型**

| 枚舉 | 說明 |
|------|------|
| `RAGDocumentType` | RAG 文檔類型 |
| `RAGCheckResult` | RAG 檢查結果 |
| `RAGRiskFactor` | RAG 風險因子 |
| `NewsSentiment` | 新聞情緒 |
| `NewsCategory` | 新聞類別 |
| `SearchEngine` | 搜索引擎 |
| `RetrievalSource` | 檢索來源 |

| 模型 | 說明 |
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

#### 枚舉類型 (30 個)
```python
# enums.py (23 個)
OrderType, OrderSide, OrderStatus, TimeInForce, TimeFrame,
Environment, RiskLevel, PositionType, SignalType, SignalStrength,
StrategyState, CommandType, CommandStatus, StrategyType,
DatabaseOperation, DatabaseStatus, MarketState, MarketRegime,
Complexity, MarketCondition, ApiStatus, EventType, EventIntensity

# rag.py (7 個)
RAGDocumentType, RAGCheckResult, RAGRiskFactor, NewsSentiment,
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

### 2026-01-25 更新
- ➕ 新增 `StrategyRecommendation` 完整策略推薦模型
- ➕ 新增 `STRATEGY_MARKET_FIT` 策略-市場適配表常數
- ➕ 新增 `EventContext`, `EventRule` 事件系統模型
- ➕ 新增 `EventType`, `EventIntensity` 事件枚舉
- ➕ 新增 `Complexity` 複雜度枚舉
- ➕ 擴展 `MarketRegime` 新增詳細分類 (TRENDING_BULL, TRENDING_BEAR, 等)
- ➕ 擴展 `StrategyType` 新增 NEWS_TRADING, PAIR_TRADING
- 🔧 統一常數命名規範

### 2026-01-22 初版
- 初始 schemas 架構建立
- 24 個標準枚舉
- 45+ 個 Pydantic 模型

---

*最後更新: 2026年1月25日 | 版本: v2.1.0 | 作者: BioNeuronAI Team*
