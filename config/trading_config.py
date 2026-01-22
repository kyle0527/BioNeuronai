# 交易配置文件

# =======================================
# Binance API 配置
# =======================================

# API 金鑰 (從 Binance Demo Trading 獲取)
# 申請地址: https://testnet.binancefuture.com/
BINANCE_API_KEY = "9KZTxxFzolHHnmCwu6yzE7YCfeZGJTSQPKWbuMgXw7ImVXWX5geYIvcZEhO7vDhE"
BINANCE_API_SECRET = "KuA1Vvi3xvJF0dPdgkFkUhywRQ5oNbY9rCe1PB5QQJjgBoJPI0IfgiGIJnwuJR7g"

# 使用測試網 (Demo Trading)
USE_TESTNET = True

# API Endpoint: https://demo-fapi.binance.com (自動選擇)

#  APIhttps://testnet.binancefuture.com
#  APIhttps://fapi.binance.com

# =======================================
# 
# =======================================

# 
TRADING_PAIRS = [
    "BTCUSDT",   # /USDT
    "ETHUSDT",   # /USDT
    "BNBUSDT",   # /USDT
]

#  
AUTO_TRADE_ENABLED = False

# 
USE_STRATEGY_FUSION = True

# USDT
MAX_TRADE_AMOUNT = 100.0

# 
MAX_POSITIONS = 3

# 1-125
LEVERAGE = 1

# =======================================
# 
# =======================================

# 
# : "RSI_Divergence", "Bollinger_Bands", "MACD_Trend", "AI_Fusion"
ACTIVE_STRATEGY = "AI_Fusion"

# RSI 
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# 
BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2.0

# MACD 
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9

# AI 
# 
AI_ENABLE_DYNAMIC_WEIGHTS = True
# 
AI_MIN_TRADES_FOR_ADJUSTMENT = 10

# =======================================
# 風險管理參數 - 統一由 risk_management 模組管理
# =======================================
# ⚠️ 重要：所有風險參數統一在 src/bioneuronai/risk_management/position_manager.py 定義
# 請使用 get_risk_params(level) 函數獲取風險參數，而非在此重複定義

# 當前使用的風險等級: CONSERVATIVE, MODERATE, AGGRESSIVE, HIGH_RISK
RISK_LEVEL = "MODERATE"

# 以下為向後兼容保留，實際應使用 risk_management 模組
MAX_RISK_PER_TRADE = 0.02  # 建議使用 get_risk_params(RISK_LEVEL).max_risk_per_trade
STOP_LOSS_PERCENTAGE = 0.02
TAKE_PROFIT_PERCENTAGE = 0.03
MAX_DRAWDOWN_PERCENTAGE = 0.10
MAX_TRADES_PER_DAY = 10
MIN_SIGNAL_CONFIDENCE = 0.65
MIN_RISK_REWARD_RATIO = 1.5
MIN_EXPECTED_RETURN = 0.005

# =======================================
# AI 
# =======================================

# 0-1
MIN_SIGNAL_CONFIDENCE = 0.7

# 
PRICE_HISTORY_SIZE = 100

# 
SHORT_MA_PERIOD = 5

# 
LONG_MA_PERIOD = 20

# =======================================
# 
# =======================================

# 
ENABLE_NOTIFICATIONS = True

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# Email 
EMAIL_ENABLED = False
EMAIL_FROM = ""
EMAIL_TO = ""
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# =======================================
# 
# =======================================

#  (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# 
LOG_FILE = "logs/trading.log"

# 
SAVE_TRADE_HISTORY = True
TRADE_HISTORY_FILE = "data/trade_history.json"

# 
SAVE_SIGNAL_HISTORY = True
SIGNAL_HISTORY_FILE = "data/signal_history.json"
