# 虛擬貨幣期貨交易系統配置

# =======================================
# 幣安 API 配置
# =======================================

# API 密鑰（從 Binance 官網獲取）
BINANCE_API_KEY = ""
BINANCE_API_SECRET = ""

# 使用測試網（建議先在測試網練習）
USE_TESTNET = True

# 測試網 API：https://testnet.binancefuture.com
# 正式網 API：https://fapi.binance.com

# =======================================
# 交易配置
# =======================================

# 監控的交易對
TRADING_PAIRS = [
    "BTCUSDT",   # 比特幣/USDT
    "ETHUSDT",   # 以太坊/USDT
    "BNBUSDT",   # 幣安幣/USDT
]

# 自動交易開關（⚠️ 謹慎開啟）
AUTO_TRADE_ENABLED = False

# 使用策略融合系統（推薦）
USE_STRATEGY_FUSION = True

# 最大單次交易金額（USDT）
MAX_TRADE_AMOUNT = 100.0

# 最大倉位數量
MAX_POSITIONS = 3

# 槓桿倍數（1-125）
LEVERAGE = 1

# =======================================
# 交易策略配置
# =======================================

# 選擇交易策略
# 可選: "RSI_Divergence", "Bollinger_Bands", "MACD_Trend", "AI_Fusion"
ACTIVE_STRATEGY = "AI_Fusion"

# RSI 策略參數
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# 布林帶策略參數
BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2.0

# MACD 策略參數
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9

# AI 融合策略參數
# 是否啟用動態權重調整
AI_ENABLE_DYNAMIC_WEIGHTS = True
# 最少交易次數才開始調整權重
AI_MIN_TRADES_FOR_ADJUSTMENT = 10

# =======================================
# 風險管理
# =======================================

# 單筆交易最大風險百分比（0.02 = 2%）
MAX_RISK_PER_TRADE = 0.02

# 止損比例（例如：0.02 = 2%）
STOP_LOSS_PERCENTAGE = 0.02

# 止盈比例
TAKE_PROFIT_PERCENTAGE = 0.03

# 最大回撤比例（超過此值停止交易）
MAX_DRAWDOWN_PERCENTAGE = 0.10

# 單日最大交易次數
MAX_TRADES_PER_DAY = 10

# 最低信號置信度（0-1）
MIN_SIGNAL_CONFIDENCE = 0.65

# =======================================
# AI 策略配置
# =======================================

# 最低信號置信度（0-1）
MIN_SIGNAL_CONFIDENCE = 0.7

# 價格歷史窗口大小
PRICE_HISTORY_SIZE = 100

# 短期均線週期
SHORT_MA_PERIOD = 5

# 長期均線週期
LONG_MA_PERIOD = 20

# =======================================
# 通知配置
# =======================================

# 啟用通知
ENABLE_NOTIFICATIONS = True

# Telegram Bot Token（可選）
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# Email 通知（可選）
EMAIL_ENABLED = False
EMAIL_FROM = ""
EMAIL_TO = ""
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# =======================================
# 日誌配置
# =======================================

# 日誌級別 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# 日誌文件路徑
LOG_FILE = "logs/trading.log"

# 保存交易記錄
SAVE_TRADE_HISTORY = True
TRADE_HISTORY_FILE = "data/trade_history.json"

# 保存信號歷史
SAVE_SIGNAL_HISTORY = True
SIGNAL_HISTORY_FILE = "data/signal_history.json"
