"""
BioNeuronai Schemas 模組

統一導出所有的 Pydantic 模型。
基於 AIVA Common v6.3 標準和 Pydantic v2 最佳實踐。
專注於幣安期貨交易需求。
"""

# 核心枚舉
from .enums import (
    # 風險管理
    RiskLevel,
    
    # 交易相關
    PositionType,
    SignalType,
    SignalStrength,
    OrderType,
    OrderSide,
    OrderStatus,
    TimeInForce,
    
    # 策略相關
    StrategyState,
    StrategyType,
    
    # 市場數據
    TimeFrame,
    MarketState,
    
    # API 相關
    ApiStatus,
    Environment,
    
    # 命令系統
    CommandType,
    CommandStatus,
    
    # 資料庫
    DatabaseOperation,
    DatabaseStatus,
)

# 市場數據模型
from .market import (
    MarketData,
)

# 交易信號模型
from .trading import (
    TradingSignal,
)

# 訂單模型 (幣安期貨專用)
from .orders import (
    BinanceOrderRequest,
    BinanceOrderResponse,
    OrderBook,
)

# 倉位模型 (幣安期貨專用)
from .positions import (
    BinancePosition,
    PositionRisk,
    AccountBalance,
)

# 組合管理模型
from .portfolio import (
    PortfolioSummary,
    Portfolio,
    PortfolioAnalytics,
    RiskMetrics,
)

# API 通信模型
from .api import (
    ApiCredentials,
    ApiResponse,
    BinanceApiError,
    WebSocketMessage,
    ExchangeInfo,
)

# 命令系統模型 (AIVA Common v6.3)
from .commands import (
    AICommand,
    AICommandResult,
    TradingCommand,
    AnalysisCommand,
    RiskManagementCommand,
    SystemCommand,
)

# 資料庫模型
from .database import (
    DatabaseConfig,
    DatabaseQuery,
    DatabaseResult,
    DatabaseConnection,
    TradingDataRecord,
    DatabaseService,  # 向後兼容
)

# 風險管理模型 (從現有文件導入)
try:
    from .risk import (
        RiskParameters,
        PositionSizing,
        PortfolioRisk,
        RiskAlert,
    )
except ImportError:
    # risk.py 文件可能有導入錯誤，先跳過
    pass

# 策略模型 (從現有文件導入)
try:
    from .strategy import (
        StrategyConfig,
        StrategySelection,
        StrategyPerformanceMetrics,
        TradeSetup,
    )
except ImportError:
    # strategy.py 文件可能有導入錯誤，先跳過
    pass

# RAG 相關模型
try:
    from .rag import (
        # 枚舉
        RAGDocumentType,
        RAGCheckResult,
        RAGRiskFactor,
        NewsSentiment,
        NewsCategory,
        SearchEngine,
        RetrievalSource,
        # 模型
        RAGRiskItem,
        RAGNewsItem,
        PreTradeCheckRequest,
        PreTradeCheckResponse,
        SearchResult,
        RetrievalQuery,
        RetrievalResult,
        KnowledgeDocumentSchema,
    )
except ImportError:
    # rag.py 文件可能有導入錯誤，先跳過
    pass

# 版本信息
__version__ = "2.0.0"
__description__ = "專為幣安期貨交易設計的 Pydantic 模型庫 (基於 AIVA Common v6.3)"
__author__ = "BioNeuronai Team"

# 導出清單 - 按類別組織
__all__ = [
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
    
    # API 通信
    "ApiCredentials",
    "ApiResponse",
    "BinanceApiError",
    "WebSocketMessage",
    "ExchangeInfo",
    
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
    
    # 枚舉類型
    "PositionType",
    "SignalType",
    "SignalStrength",
    "StrategyState",
    "StrategyType",
]
