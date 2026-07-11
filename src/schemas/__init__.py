"""
BioNeuronai Schemas 模組

統一導出所有的 Pydantic 模型。
基於 AIVA Common v6.3 標準和 Pydantic v2 最佳實踐。
專注於幣安期貨交易需求。

更新日誌:
- v2.3.0: 新增 types, events, backtesting, ml_models, alerts 模組
- v2.0.0: 初始版本
"""

# 類型定義和版本控制
# API 通信模型（底層 Binance 通訊）
# REST API 入口層 Request / Response / Status 模型 (2026-03-28 新增)
from .api import (
    ApiCredentials,
    ApiResponse,
    ApiStatusInfo,
    BacktestRequest,
    BinanceApiError,
    BinanceValidateRequest,
    ExchangeInfo,
    JobStatus,
    ModuleStatus,
    NewsRequest,
    PreTradeRequest,
    RestApiResponse,
    SimulateRequest,
    StatusResponse,
    TradeStartRequest,
    WebSocketMessage,
)

# 命令系統模型 (AIVA Common v6.3)
from .commands import (
    AICommand,
    AICommandResult,
    AnalysisCommand,
    RiskManagementCommand,
    SystemCommand,
    TradingCommand,
)

# 資料庫模型
from .database import (
    DatabaseConfig,
    DatabaseConnection,
    DatabaseQuery,
    DatabaseResult,
    DatabaseService,  # 向後兼容
    SQLiteConfig,  # noqa: F401
    TradingDataRecord,
)

# 核心枚舉
from .enums import (
    AlertSeverity,
    AlertType,
    # API 相關
    ApiStatus,
    BacktestStatus,
    CommandStatus,
    # 命令系統
    CommandType,
    Complexity,
    # 資料庫
    DatabaseOperation,
    DatabaseStatus,
    Environment,
    EventIntensity,
    # 事件系統 (2026-01-25 新增)
    EventType,
    MarketCondition,
    # 市場分析 (2026-01-25 新增)
    MarketRegime,
    MarketState,
    ModelStatus,
    NotificationChannel,
    OrderSide,
    OrderStatus,
    OrderType,
    # 交易相關
    PositionType,
    PredictionType,
    # 風險管理
    RiskLevel,
    SignalStrength,
    SignalType,
    # 策略相關
    StrategyState,
    StrategyType,
    # 市場數據
    TimeFrame,
    TimeInForce,
    # Event Sourcing 和新功能 (2026-02-14 新增)
    TradeEventType,
)

# 外部數據源模型 (2026-02-15 新增)
from .external_data import (
    DataSourceType,
    DeFiMetrics,
    EconomicEvent,
    ExternalDataSnapshot,
    FearGreedIndex,
    GlobalMarketData,
    MarketSentiment,
    StablecoinMetrics,
)

# 市場數據模型
from .market import (
    MarketData,
)

# 訂單模型 (幣安期貨專用)
from .orders import (
    BinanceOrderRequest,
    BinanceOrderResponse,
    OrderBook,
)

# 組合管理模型
from .portfolio import (
    Portfolio,
    PortfolioAnalytics,
    PortfolioSummary,
    RiskMetrics,
)

# 倉位模型 (幣安期貨專用)
from .positions import (
    AccountBalance,
    BinancePosition,
    PositionRisk,
)

# 交易信號模型
from .trading import (
    TradingSignal,
)
from .types import (
    SCHEMA_VERSION,
    BinanceSymbol,
    Leverage,
    Percentage,
    PositiveDecimal,
    Price,
    Quantity,
    RSIValue,
    USDTSymbol,
)

# 風險管理模型 (從現有文件導入)
try:
    from .risk import (
        PortfolioRisk,
        PositionSizing,
        RiskAlert,
        RiskParameters,
    )
except ImportError:
    # risk.py 文件可能有導入錯誤，先跳過
    pass

# 策略模型 (從現有文件導入)
try:
    from .strategy import (
        STRATEGY_MARKET_FIT,
        StrategyConfig,
        StrategyPerformanceMetrics,
        # 2026-01-25 新增
        StrategyRecommendation,
        StrategySelection,
        TradeSetup,
    )
except ImportError:
    # strategy.py 文件可能有導入錯誤，先跳過
    pass

# Event Sourcing 模型 (2026-02-14 新增)
# 警報系統模型 (2026-02-14 新增)
from .alerts import (
    AlertCondition,
    AlertEvent,
    AlertRule,
    AlertSummary,
    NotificationConfig,
)

# 回測模型 (2026-02-14 新增)
from .backtesting import (
    BacktestConfig,
    BacktestResult,
    MonteCarloResult,
    TradeRecord,
    WalkForwardResult,
)
from .events import (
    EventMetadata,
    EventQuery,
    EventStore,
    OrderEvent,
    PositionEvent,
    RiskEvent,
    TradeEvent,
)

# 機器學習模型 (2026-02-14 新增)
from .ml_models import (
    FeatureConfig,
    ModelConfig,
    ModelMetrics,
    ModelPrediction,
    ModelRegistry,
    TrainingJob,
)

# RAG 相關模型
try:
    from .rag import (
        # 事件系統 (2026-01-25 新增)
        EventContext,
        EventRule,
        KnowledgeDocumentSchema,
        NewsCategory,
        NewsSentiment,
        PreTradeCheckRequest,
        PreTradeCheckResponse,
        RAGCheckResult,
        # 枚舉
        RAGDocumentType,
        RAGNewsItem,
        RAGRiskFactor,
        # 模型
        RAGRiskItem,
        RetrievalQuery,
        RetrievalResult,
        RetrievalSource,
        SearchEngine,
        SearchResult,
    )
except ImportError:
    # rag.py 文件可能有導入錯誤，先跳過
    pass

# 版本信息 (與 SCHEMA_VERSION 同步)
__version__ = SCHEMA_VERSION
__description__ = "專為幣安期貨交易設計的 Pydantic 模型庫 (基於 AIVA Common v6.3)"
__author__ = "BioNeuronai Team"

# 導出清單 - 按類別組織
__all__ = [
    # 版本和類型
    "SCHEMA_VERSION",
    "PositiveDecimal",
    "Percentage",
    "Leverage",
    "RSIValue",
    "BinanceSymbol",
    "USDTSymbol",
    "Price",
    "Quantity",

    # 枚舉類型
    "RiskLevel",
    "PositionType",
    "SignalType",
    "SignalStrength",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "TimeInForce",
    "StrategyState",
    "StrategyType",
    "TimeFrame",
    "MarketState",
    "ApiStatus",
    "Environment",
    "CommandType",
    "CommandStatus",
    "DatabaseOperation",
    "DatabaseStatus",

    # 市場數據
    "MarketData",

    # 外部數據源 (2026-02-15)
    "DataSourceType",
    "FearGreedIndex",
    "GlobalMarketData",
    "DeFiMetrics",
    "StablecoinMetrics",
    "EconomicEvent",
    "MarketSentiment",
    "ExternalDataSnapshot",

    # 交易相關
    "TradingSignal",
    "BinanceOrderRequest",
    "BinanceOrderResponse",
    "OrderBook",

    # 倉位管理 (幣安期貨)
    "BinancePosition",
    "PositionRisk",
    "AccountBalance",

    # 組合管理
    "PortfolioSummary",
    "Portfolio",
    "PortfolioAnalytics",
    "RiskMetrics",

    # API 通信（底層 Binance）
    "ApiCredentials",
    "ApiResponse",
    "BinanceApiError",
    "WebSocketMessage",
    "ExchangeInfo",
    "ApiStatusInfo",

    # REST API 入口層 Request / Response / Status (2026-03-28)
    "NewsRequest",
    "PreTradeRequest",
    "BacktestRequest",
    "SimulateRequest",
    "TradeStartRequest",
    "BinanceValidateRequest",
    "RestApiResponse",
    "ModuleStatus",
    "StatusResponse",
    "JobStatus",

    # 命令系統 (AIVA Common v6.3)
    "AICommand",
    "AICommandResult",
    "TradingCommand",
    "AnalysisCommand",
    "RiskManagementCommand",
    "SystemCommand",

    # 資料庫
    "DatabaseConfig",
    "DatabaseQuery",
    "DatabaseResult",
    "DatabaseConnection",
    "TradingDataRecord",
    "DatabaseService",

    # 風險管理 (如果可用)
    "RiskParameters",
    "PositionSizing",
    "PortfolioRisk",
    "RiskAlert",

    # 策略管理 (如果可用)
    "StrategyConfig",
    "StrategySelection",
    "StrategyPerformanceMetrics",
    "TradeSetup",

    # RAG 相關 (如果可用)
    "RAGDocumentType",
    "RAGCheckResult",
    "RAGRiskFactor",
    "NewsSentiment",
    "NewsCategory",
    "SearchEngine",
    "RetrievalSource",
    "RAGRiskItem",
    "RAGNewsItem",
    "PreTradeCheckRequest",
    "PreTradeCheckResponse",
    "SearchResult",
    "RetrievalQuery",
    "RetrievalResult",
    "KnowledgeDocumentSchema",

    # 事件系統 (2026-01-25 新增)
    "EventType",
    "EventIntensity",
    "EventContext",
    "EventRule",

    # 市場分析 (2026-01-25 新增)
    "MarketRegime",
    "MarketCondition",
    "Complexity",

    # 策略推薦 (2026-01-25 新增)
    "StrategyRecommendation",
    "STRATEGY_MARKET_FIT",

    # Event Sourcing 新增枚舉 (2026-02-14)
    "TradeEventType",
    "BacktestStatus",
    "PredictionType",
    "ModelStatus",
    "AlertSeverity",
    "AlertType",
    "NotificationChannel",

    # Event Sourcing 模型 (2026-02-14)
    "EventMetadata",
    "TradeEvent",
    "OrderEvent",
    "PositionEvent",
    "RiskEvent",
    "EventStore",
    "EventQuery",

    # 回測模型 (2026-02-14)
    "BacktestConfig",
    "TradeRecord",
    "BacktestResult",
    "WalkForwardResult",
    "MonteCarloResult",

    # 機器學習模型 (2026-02-14)
    "FeatureConfig",
    "ModelConfig",
    "ModelMetrics",
    "ModelPrediction",
    "ModelRegistry",
    "TrainingJob",

    # 警報系統 (2026-02-14)
    "AlertCondition",
    "AlertRule",
    "AlertEvent",
    "NotificationConfig",
    "AlertSummary",
]
