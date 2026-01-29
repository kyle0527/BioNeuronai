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

# =======================================
# Jules Session 優化後的風險參數 (2026-01-27)
# =======================================
MAX_RISK_PER_TRADE = 0.02              # 單筆交易最大風險 2%
MAX_DRAWDOWN_PERCENTAGE = 0.10          # 最大回撤 10%
MAX_POSITION_RATIO = 0.25               # 最大倉位比例 25%
MAX_CORRELATION = 0.7                   # 最大相關性
STOP_LOSS_PERCENTAGE = 0.02             # 預設止損 2%
TAKE_PROFIT_PERCENTAGE = 0.04           # 預設止盈 4% (優化後)
MAX_TRADES_PER_DAY = 10                 # 每日最大交易次數
MIN_SIGNAL_CONFIDENCE = 0.65            # 最低信號置信度 65%
MIN_RISK_REWARD_RATIO = 2.0             # 最小風險報酬比 2:1 (優化後)
MIN_EXPECTED_RETURN = 0.016             # 最小預期收益 1.6%

# 交易時間窗口 (24小時制)
TRADING_HOURS_START = 0
TRADING_HOURS_END = 23

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
