"""
BioNeuronAI 枚舉定義 - 按優先級分類

枚舉/結構定義優先級：
1. 國際標準/官方規範 (最高優先級)
   • 幣安期貨 API 官方標準
   • ISO 金融標準
   • Python typing 標準
   ✅ 必須完全遵循官方定義

2. 程式語言標準庫 (次高優先級)
   • Python: enum.Enum, typing 模組
   ✅ 必須使用語言官方推薦方式

3. BioNeuronAI 統一定義 (系統內部標準)
   • RiskLevel, SignalType, StrategyState
   • CommandType, DatabaseOperation
   ✅ 系統內所有模組必須使用

4. 模組專屬枚舉 (最低優先級)
   • 僅當功能完全限於該模組內部時才允許
   ⚠️ 需經過審查確認不會與通用枚舉重複
"""

from enum import Enum


# ========== 第1優先級：國際標準/官方規範 (最高優先級) ==========
# 必須完全遵循官方定義，不可隨意修改

# 幣安期貨 API 官方標準枚舉
class OrderType(str, Enum):
    """訂單類型 - 嚴格按照幣安期貨 API 官方文檔定義
    
    參考: https://developers.binance.com/docs/derivatives
    最後驗證: 2026-01-22
    
    注意: 條件訂單已於 2025-12-09 遷移至 Algo Service
    """
    
    # 基本訂單類型
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    
    # 條件訂單類型 (已遷移到 Algo Service)
    STOP = "STOP"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
    TRAILING_STOP_MARKET = "TRAILING_STOP_MARKET"


class OrderSide(str, Enum):
    """訂單方向 - 幣安期貨 API 官方標準"""
    
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """訂單狀態 - 幣安期貨 API 官方標準
    
    包含 Self-Trade Prevention (STP) 相關狀態
    """
    
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    EXPIRED_IN_MATCH = "EXPIRED_IN_MATCH"  # Self-Trade Prevention 觸發


class TimeInForce(str, Enum):
    """訂單有效期 - 幣安期貨 API 官方標準
    
    參考: https://developers.binance.com/docs/derivatives  
    RPI 新增於 2025-11-18
    """
    
    GTC = "GTC"  # Good Till Canceled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    GTX = "GTX"  # Good Till Crossing (Post Only)
    RPI = "RPI"  # Retail Price Improvement (新增 2025-11-18)


class TimeFrame(str, Enum):
    """時間框架 - 幣安 Kline 官方支援格式"""
    
    MIN_1 = "1m"
    MIN_3 = "3m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    MIN_30 = "30m"
    HOUR_1 = "1h"
    HOUR_2 = "2h"
    HOUR_4 = "4h"
    HOUR_6 = "6h"
    HOUR_8 = "8h"
    HOUR_12 = "12h"
    DAY_1 = "1d"
    DAY_3 = "3d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


# ========== 第2優先級：程式語言標準庫 (次高優先級) ==========
# 必須使用 Python 官方推薦方式

class Environment(str, Enum):
    """運行環境 - 遵循 Python 部署標準慣例"""
    
    PRODUCTION = "production"
    TESTNET = "testnet"  # 幣安測試網
    STAGING = "staging"
    TESTING = "testing"
    DEVELOPMENT = "development"


# ========== 第3優先級：BioNeuronAI 統一定義 (系統內部標準) ==========
# 系統內所有模組必須使用，確保一致性

class RiskLevel(str, Enum):
    """風險等級 - BioNeuronAI 統一風險評估標準"""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PositionType(str, Enum):
    """持倉類型 - 系統統一定義"""
    
    LONG = "long"
    SHORT = "short"


class SignalType(str, Enum):
    """交易信號類型 - AI 模型統一輸出格式"""
    
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class SignalStrength(str, Enum):
    """信號強度 - AI 模型置信度分級"""
    
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class StrategyState(str, Enum):
    """策略狀態 - 系統統一狀態管理"""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class CommandType(str, Enum):
    """命令類型 - 系統統一命令分類"""
    
    TRADING = "trading"
    ANALYSIS = "analysis"
    PORTFOLIO = "portfolio"
    RISK_MANAGEMENT = "risk_management"
    MARKET_DATA = "market_data"
    SYSTEM = "system"
    AI_MODEL = "ai_model"


class CommandStatus(str, Enum):
    """命令狀態 - 系統統一執行狀態"""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELED = "canceled"


# ========== 第4優先級：模組專屬枚舉 (最低優先級) ==========
# 僅當功能完全限於該模組內部時才允許，需經過審查確認不會與通用枚舉重複

class StrategyType(str, Enum):
    """策略類型 - BioNeuronAI 專屬分類
    
    ⚠️ 模組專屬枚舉：僅用於策略分析模組
    """
    
    AI_ML = "ai_ml"
    AI_FUSION = "ai_fusion"  # AI 融合策略
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    QUANTITATIVE = "quantitative"
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SWING_TRADING = "swing_trading"
    SCALPING = "scalping"
    ARBITRAGE = "arbitrage"
    MOMENTUM = "momentum"
    GRID_TRADING = "grid_trading"  # 網格交易
    VOLATILITY_TRADING = "volatility_trading"  # 波動率交易
    NEWS_TRADING = "news_trading"  # 新聞驅動交易 (2026-01-25 新增)
    PAIR_TRADING = "pair_trading"  # 配對交易 (2026-01-25 新增)


class DatabaseOperation(str, Enum):
    """資料庫操作類型 - 資料庫模組專屬
    
    ⚠️ 模組專屬枚舉：僅用於資料庫操作模組
    """
    
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    BULK_INSERT = "bulk_insert"
    BULK_UPDATE = "bulk_update"


class DatabaseStatus(str, Enum):
    """資料庫狀態 - 資料庫模組專屬
    
    ⚠️ 模組專屬枚舉：僅用於資料庫連接管理
    """
    
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MarketState(str, Enum):
    """市場狀態 - 市場分析模組專屬
    
    ⚠️ 模組專屬枚舉：與官方 API 狀態不同，用於內部分析
    """
    
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    POST_MARKET = "post_market"
    HALTED = "halted"
    MAINTENANCE = "maintenance"


class MarketRegime(str, Enum):
    """市場體制 - 技術分析模組專屬
    
    ⚠️ 模組專屬枚舉：僅用於市場狀態分析
    
    更新: 2026-01-25 - 擴展更詳細的分類
    """
    
    # 基礎分類
    BULL = "bull"  # 牛市
    BEAR = "bear"  # 熊市
    SIDEWAYS = "sideways"  # 橫盤
    VOLATILE = "volatile"  # 波動
    QUIET = "quiet"  # 平靜
    
    # 詳細分類 (2026-01-25 新增)
    TRENDING_BULL = "trending_bull"       # 牛市趨勢
    TRENDING_BEAR = "trending_bear"       # 熊市趨勢
    SIDEWAYS_LOW_VOL = "sideways_low_vol" # 低波動盤整
    SIDEWAYS_HIGH_VOL = "sideways_high_vol"  # 高波動盤整
    VOLATILE_UNCERTAIN = "volatile_uncertain"  # 高波動不確定
    BREAKOUT_POTENTIAL = "breakout_potential"  # 突破潛力


class Complexity(str, Enum):
    """策略複雜度 - 用於策略選擇器
    
    2026-01-25 新增
    """
    
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class MarketCondition(str, Enum):
    """市場條件 - 技術分析模組專屬
    
    ⚠️ 模組專屬枚舉：僅用於市場條件判斷
    """
    
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class ApiStatus(str, Enum):
    """API 狀態 - API 管理模組專屬
    
    ⚠️ 模組專屬枚舉：用於內部 API 狀態監控
    """
    
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    LIMITED = "limited"
    ERROR = "error"


# ========== 事件系統枚舉 (Event System - 2026-01-25 新增) ==========

class EventType(str, Enum):
    """事件類型 - 事件驅動交易系統統一定義
    
    用於新聞大腦 (RuleBasedEvaluator) 的事件分類。
    參考：國際新聞分類標準 + 加密貨幣市場特性
    
    最後更新: 2026-01-25
    """
    
    # 地緣政治
    WAR = "WAR"                          # 戰爭/軍事衝突
    GEOPOLITICAL = "GEOPOLITICAL"        # 地緣政治風險
    
    # 安全事件
    HACK = "HACK"                        # 黑客攻擊/安全漏洞
    SECURITY_BREACH = "SECURITY_BREACH"  # 安全事件
    
    # 監管相關
    REGULATION = "REGULATION"            # 監管政策變化
    LEGAL = "LEGAL"                      # 法律訴訟
    
    # 宏觀經濟
    MACRO = "MACRO"                      # 宏觀經濟事件 (利率/通膨)
    FED = "FED"                          # 美聯儲相關
    
    # 公司/項目事件
    EARNINGS = "EARNINGS"                # 財報發布
    PARTNERSHIP = "PARTNERSHIP"          # 合作夥伴關係
    
    # 交易所相關
    EXCHANGE_ISSUE = "EXCHANGE_ISSUE"    # 交易所問題
    LISTING = "LISTING"                  # 上市/下架
    
    # 技術事件
    NETWORK_ISSUE = "NETWORK_ISSUE"      # 網路問題/分叉
    UPGRADE = "UPGRADE"                  # 協議升級
    
    # 其他
    OTHER = "OTHER"                      # 其他未分類事件


class EventIntensity(str, Enum):
    """事件強度等級 - 事件驅動交易系統統一定義
    
    用於評估事件對市場的影響程度。
    
    最後更新: 2026-01-25
    """
    
    LOW = "LOW"           # 低影響 - 可忽略或輕微調整
    MEDIUM = "MEDIUM"     # 中等影響 - 需要關注
    HIGH = "HIGH"         # 高影響 - 需要調整策略
    EXTREME = "EXTREME"   # 極端影響 - Hard Stop 觸發條件
