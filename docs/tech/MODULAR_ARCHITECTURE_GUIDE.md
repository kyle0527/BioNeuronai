# BioNeuronai 模組化架構技術手冊
> **版本**: v2.1  
> **日期**: 2026年1月19日  
> **狀態**: ✅ 已完成重構並推送至 GitHub


## 📑 目錄

1. 架構概覽
2. 模組詳細說明
3. API 參考
4. 遷移指南
5. 最佳實踐
6. 故障排除
7. 📊 性能指標
8. 🚀 後續規劃
9. 📚 相關文檔
10. 📞 技術支持
11. 📝 變更日誌

---

## 架構概覽

> ⚠️ 本章節部分過時：
> 此處列出的部分目錄與模組路徑屬於舊版重構設計，不應直接當作目前實際檔案結構的唯一依據。
> 閱讀時應搭配現行 repo 結構與最新基準文件。

### 🎯 重構目標

將原本 **1200+ 行**的單一檔案 `crypto_futures_trader.py` 重構為模組化架構，實現：
- **職責分離**: 每個模組專注單一功能
- **可測試性**: 易於編寫單元測試
- **可維護性**: 降低修改成本
- **可擴展性**: 方便添加新功能
- **向後兼容**: 舊代碼無需修改

### 📁 新目錄結構

```
src/bioneuronai/
│
├── data_models/                    # 數據模型層
│   └── __init__.py                # MarketData, TradingSignal, Position, OrderResult
│
├── connectors/                     # API 連接器層
│   ├── __init__.py
│   └── binance_futures.py         # Binance Futures API (REST + WebSocket)
│
├── risk_management/                # 風險管理層
│   ├── __init__.py
│   └── risk_manager.py            # 風險控制核心
│
├── strategies/                     # 交易策略層
│   ├── __init__.py
│   ├── base_strategy.py           # 基礎策略類
│   ├── trend_following.py         # 趨勢跟隨策略
│   ├── swing_trading.py           # 波段交易策略
│   ├── mean_reversion.py          # 均值回歸策略
│   ├── breakout_trading.py        # 突破交易策略
│   └── strategy_fusion.py         # AI 策略融合系統
│
├── trading_engine.py               # 🆕 主交易引擎
├── crypto_futures_trader.py        # 🔄 向後兼容層（已重構為導入別名）
├── news_analyzer.py                # 新聞分析服務
├── self_improvement.py             # 自我改進系統
└── trading_strategies.py           # 策略統一導出
```

### 🔄 架構變化對比

| 層級 | 重構前 | 重構後 | 改進 |
|------|--------|--------|------|
| **數據模型** | 散落各處 | `data_models/` 集中管理 | ✅ 統一定義，避免重複 |
| **API 連接** | 混在主類中 | `connectors/binance_futures.py` | ✅ 獨立測試，易於擴展 |
| **風險管理** | 嵌套在主類 | `risk_management/risk_manager.py` | ✅ 獨立配置，複用性高 |
| **交易引擎** | 與所有功能耦合 | `trading_engine.py` 協調器 | ✅ 清晰職責，易於維護 |
| **策略系統** | 分散實現 | `strategies/` 統一接口 | ✅ 標準化，易於添加新策略 |

---

## 模組詳細說明

### 1. 📊 data_models - 數據模型層

**路徑**: `src/schemas/` (Single Source of Truth)

**職責**: 定義所有核心數據結構，確保類型安全

#### 核心類別

##### `MarketData`
市場數據結構，存儲 OHLCV 與即時行情資訊

```python
# 來源：src/schemas/market.py
class MarketData(BaseModel):
    symbol: str              # 交易對符號 (如 BTCUSDT)
    timestamp: datetime      # 時間戳
    open: float              # 開盤價
    high: float              # 最高價
    low: float               # 最低價
    close: float             # 收盤價
    volume: float            # 成交量
    # 即時行情欄位（Optional）
    bid: Optional[float]         # 買一價
    ask: Optional[float]         # 賣一價
    funding_rate: float = 0.0    # 資金費率
    open_interest: float = 0.0   # 未平倉合約數量
    # 技術指標（Optional）
    rsi: Optional[float] = None
    macd: Optional[float] = None
    atr: Optional[float] = None

    @computed_field
    @property
    def price(self) -> float:
        """= close，便捷屬性"""
        return self.close
```

**使用示例**:
```python
from schemas.market import MarketData
from datetime import datetime

market_data = MarketData(
    symbol="BTCUSDT",
    timestamp=datetime.now(),
    open=45000.0, high=46000.0, low=44500.0, close=45500.0,
    volume=1234.56,
    bid=45490.0, ask=45510.0
)
print(market_data.price)  # 45500.0 (= close)
```

##### `TradingSignal`
交易信號結構，策略分析結果

```python
# 來源：src/schemas/trading.py
class TradingSignal(BaseModel):
    symbol: str                              # 交易對
    signal_type: SignalType                  # BUY | SELL | HOLD
    strength: SignalStrength = MODERATE      # 信號強度
    confidence: float                        # 信心度 (0-1)
    entry_price: Optional[float] = None      # 建議進場價
    target_price: Optional[float] = None     # 目標價
    stop_loss: Optional[float] = None        # 止損價
    take_profit: Optional[float] = None      # 止盈價
    strategy_name: Optional[str] = None
    reason: Optional[str] = None

    @computed_field
    @property
    def action(self) -> str:
        """= signal_type.value.upper()，方便日誌與比較"""
        return self.signal_type.value.upper()
```

**使用示例**:
```python
from schemas.trading import TradingSignal
from schemas.enums import SignalType

signal = TradingSignal(
    signal_type=SignalType.BUY,
    symbol="BTCUSDT",
    confidence=0.85,
    reason="短期均線上穿長期均線，趨勢向上",
    target_price=46000.0,
    stop_loss=44500.0
)
print(signal.action)  # 'BUY'
```

##### `SQLiteConfig`
系統實際使用的 SQLite 資料庫配置

```python
# 來源：src/schemas/database.py
class SQLiteConfig(BaseModel):
    db_path: str = "data/bioneuronai/trading/runtime/trading.db"
    timeout: float = 30.0
    check_same_thread: bool = False
    backup_enabled: bool = True
```

---

### 2. 🔌 connectors - API 連接器層

**路徑**: `src/bioneuronai/connectors/binance_futures.py`

**職責**: 封裝 Binance Futures API，提供統一接口

#### `BinanceFuturesConnector` 類

##### 初始化參數
```python
def __init__(
    self, 
    api_key: str = "", 
    api_secret: str = "", 
    testnet: bool = True
)
```

- `api_key`: Binance API 金鑰
- `api_secret`: Binance API 密鑰
- `testnet`: 是否使用測試網（預設 True）

##### 核心方法

###### 1. 獲取實時價格 (REST API)
```python
def get_ticker_price(self, symbol: str = "BTCUSDT") -> Optional[MarketData]
```

**返回**: `MarketData` 對象或 `None`

**示例**:
```python
connector = BinanceFuturesConnector(testnet=True)
price_data = connector.get_ticker_price("BTCUSDT")
if price_data:
    print(f"BTC 價格: ${price_data.price:,.2f}")
```

###### 2. WebSocket 實時數據流
```python
def subscribe_ticker_stream(
    self, 
    symbol: str, 
    callback: Callable,
    auto_reconnect: bool = True
)
```

**參數**:
- `symbol`: 交易對（小寫），如 `"btcusdt"`
- `callback`: 數據回調函數
- `auto_reconnect`: 自動重連（預設 True）

**示例**:
```python
def on_price_update(data):
    current_price = float(data['c'])
    print(f"實時價格: ${current_price:,.2f}")

connector.subscribe_ticker_stream("btcusdt", on_price_update)
```

###### 3. 下單 (支持止損止盈)
```python
def place_order(
    self,
    symbol: str,
    side: str,              # BUY or SELL
    order_type: str,        # LIMIT or MARKET
    quantity: float,
    price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None
) -> Optional[Dict]
```

**示例**:
```python
result = connector.place_order(
    symbol="BTCUSDT",
    side="BUY",
    order_type="MARKET",
    quantity=0.01,
    stop_loss=44000.0,
    take_profit=46000.0
)
```

###### 4. 獲取賬戶信息
```python
def get_account_info() -> Optional[Dict]
```

**返回**: 包含餘額、持倉等信息的字典

##### 特色功能

- ✅ **自動速率限制**: 防止超過 API 限制 (1200 req/min)
- ✅ **自動重連**: WebSocket 斷線自動重連（最多 10 次）
- ✅ **簽名認證**: 自動生成 HMAC SHA256 簽名
- ✅ **止損止盈**: 下單時自動設置止損止盈訂單

---

### 3. 🛡️ risk_management - 風險管理層

**路徑**: `src/bioneuronai/risk_management/risk_manager.py`

**職責**: 風險控制、倉位計算、回撤監控

#### `RiskManager` 類

##### 核心參數
```python
class RiskParameters:
    max_risk_per_trade: float = 0.02      # 單筆最大風險 2%
    max_drawdown: float = 0.10            # 最大回撤 10%
    max_trades_per_day: int = 10          # 每日最大交易次數
    min_confidence: float = 0.65          # 最低信號置信度
    position_sizing_method: str = "kelly" # kelly, fixed, volatility
```

##### 核心方法

###### 1. 計算倉位大小（Kelly 準則）
```python
def calculate_position_size(
    self,
    account_balance: float,
    entry_price: float,
    stop_loss: float
) -> float
```

**Kelly 準則公式**:
```
Position Size = Risk Amount / (Entry Price × Price Risk %)
```

**示例**:
```python
risk_manager = RiskManager()
position_size = risk_manager.calculate_position_size(
    account_balance=10000.0,
    entry_price=45000.0,
    stop_loss=44500.0
)
print(f"建議倉位: {position_size:.4f} BTC")
```

###### 2. 檢查是否可以交易
```python
def check_can_trade(
    self, 
    signal_confidence: float
) -> Tuple[bool, str]
```

**返回**: `(可否交易, 原因說明)`

**檢查項目**:
- ✅ 每日交易次數限制
- ✅ 信號置信度閾值
- ✅ 最大回撤檢查
- ✅ 資金充足性

**示例**:
```python
can_trade, reason = risk_manager.check_can_trade(signal_confidence=0.75)
if can_trade:
    execute_trade()
else:
    print(f"無法交易: {reason}")
```

###### 3. 更新餘額和回撤追蹤
```python
def update_balance(self, new_balance: float)
```

自動追蹤峰值餘額和當前回撤

###### 4. 記錄交易
```python
def record_trade(self, trade_info: Dict)
```

記錄交易歷史，用於績效分析

##### 風險統計
```python
def get_statistics() -> Dict
```

**返回信息**:
```python
{
    'total_trades': 150,
    'win_rate': '65.3%',
    'total_profit': '12.5%',
    'daily_trades_today': 3,
    'current_drawdown': '2.3%'
}
```

---

### 4. 🧠 strategies - 交易策略層

**路徑**: `src/bioneuronai/strategies/`

所有策略繼承自 `BaseStrategy`，實現統一接口

#### 可用策略

| 策略 | 文件 | 適用場景 |
|------|------|----------|
| 趨勢跟隨 | `trend_following.py` | 單邊趨勢市場 |
| 波段交易 | `swing_trading.py` | 震蕩上升市場 |
| 均值回歸 | `mean_reversion.py` | 橫盤震蕩市場 |
| 突破交易 | `breakout_trading.py` | 盤整後突破 |
| AI 融合 | `strategy_fusion.py` | 所有市場環境 |

#### 統一接口

```python
class BaseStrategy:
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """分析市場數據，返回交易信號"""
        pass
```

#### 使用示例

```python
from bioneuronai.strategies import (
    TrendFollowingStrategy,
    StrategyFusion
)

# 單一策略
trend_strategy = TrendFollowingStrategy()
signal = trend_strategy.analyze(market_data)

# AI 融合策略（推薦）
fusion = StrategyFusion()
signal = fusion.analyze(market_data)
print(f"信號: {signal.action}, 信心度: {signal.confidence:.2%}")
```

---

### 5. ⚙️ trading_engine - 主交易引擎

**路徑**: `src/bioneuronai/trading_engine.py`

**職責**: 協調所有模塊，執行完整交易流程

#### `TradingEngine` 類

##### 初始化
```python
def __init__(
    self,
    api_key: str = "",
    api_secret: str = "",
    testnet: bool = True,
    use_strategy_fusion: bool = True  # 使用 AI 融合策略
)
```

##### 核心方法

###### 1. 啟動市場監控
```python
def start_monitoring(self, symbol: str = "BTCUSDT")
```

**功能**:
- 📰 顯示交易前新聞分析
- 📊 實時 WebSocket 數據流
- 🧠 策略分析（每次價格更新）
- 🛡️ 風險管理檢查
- 🚀 自動交易執行（可選）

**示例**:
```python
engine = TradingEngine(testnet=True)
engine.auto_trade = True  # 啟用自動交易
engine.start_monitoring("BTCUSDT")
```

###### 2. 執行交易
```python
def execute_trade(self, signal: TradingSignal)
```

**流程**:
1. 📰 新聞風險檢查
2. 💼 獲取賬戶信息
3. 📏 計算倉位大小（基於 Kelly 準則）
4. 🛡️ 風險管理驗證
5. 📤 提交訂單（市價單 + 止損止盈）
6. 📝 記錄交易

###### 3. 獲取賬戶摘要
```python
def get_account_summary() -> Dict
```

**返回**:
```python
{
    "status": "✅ 已連接",
    "balance": 10000.0,
    "available_balance": 9500.0,
    "unrealized_pnl": 120.5,
    "positions_count": 2,
    "risk_stats": {...},
    "strategy_weights": {...}  # 如果使用融合策略
}
```

###### 4. 新聞分析
```python
def get_news_summary(symbol: str = "BTCUSDT") -> str
def set_news_analysis(enabled: bool)
```

控制新聞分析功能的開啟/關閉

###### 5. 保存歷史數據
```python
def save_signals_history(filepath: str = "signals_history.json")
```

保存信號歷史、策略權重、風險統計

---

## API 參考

### 快速開始代碼

#### 基礎使用
```python
from bioneuronai import TradingEngine

# 1. 創建交易引擎（測試網）
engine = TradingEngine(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True,
    use_strategy_fusion=True  # 使用 AI 融合策略
)

# 2. 獲取實時價格
price_data = engine.get_real_time_price("BTCUSDT")
print(f"BTC 價格: ${price_data.price:,.2f}")

# 3. 查看賬戶
account = engine.get_account_summary()
print(f"餘額: ${account['balance']:,.2f}")

# 4. 啟動監控（手動交易模式）
engine.auto_trade = False
engine.start_monitoring("BTCUSDT")
```

#### 自動交易模式
```python
# 啟用自動交易
engine.auto_trade = True
engine.max_position_size = 0.01  # 最大倉位 0.01 BTC

# 啟動監控（會自動執行交易）
engine.start_monitoring("BTCUSDT")

# 保持運行
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    engine.stop_monitoring()
    engine.save_signals_history()
```

#### 使用單一策略
```python
from bioneuronai.strategies import TrendFollowingStrategy
from bioneuronai.data_models import MarketData

# 創建策略
strategy = TrendFollowingStrategy()

# 準備市場數據
market_data = MarketData(
    symbol="BTCUSDT",
    price=45000.0,
    volume=1000.0,
    timestamp=int(time.time() * 1000)
)

# 獲取信號
signal = strategy.analyze(market_data)
print(f"動作: {signal.action}")
print(f"信心度: {signal.confidence:.2%}")
print(f"理由: {signal.reason}")
```

---

## 遷移指南

### 🔄 從舊架構遷移

#### 向後兼容性

**好消息**: 舊代碼無需修改！

`crypto_futures_trader.py` 現在是一個兼容層：
```python
# 舊代碼仍然可用
from bioneuronai.crypto_futures_trader import CryptoFuturesTrader

trader = CryptoFuturesTrader(testnet=True)
trader.start_monitoring("BTCUSDT")
```

實際上 `CryptoFuturesTrader` 是 `TradingEngine` 的別名：
```python
# 內部實現
from .trading_engine import TradingEngine as CryptoFuturesTrader
```

#### 推薦遷移步驟

##### 步驟 1: 更新導入語句
```python
# 舊方式 (仍可用)
from bioneuronai.crypto_futures_trader import CryptoFuturesTrader
trader = CryptoFuturesTrader()

# 新方式 (推薦)
from bioneuronai import TradingEngine
engine = TradingEngine()
```

##### 步驟 2: 使用新的數據模型
```python
# 舊方式
from bioneuronai.crypto_futures_trader import MarketData

# 新方式 (更清晰)
from bioneuronai.data_models import MarketData, TradingSignal, Position
```

##### 步驟 3: 直接使用子模塊
```python
# 更細粒度的控制
from bioneuronai.connectors import BinanceFuturesConnector
from bioneuronai.risk_management import RiskManager
from bioneuronai.strategies import StrategyFusion

connector = BinanceFuturesConnector(testnet=True)
risk_manager = RiskManager()
strategy = StrategyFusion()
```

#### 遷移對照表

| 舊代碼 | 新代碼 | 說明 |
|--------|--------|------|
| `CryptoFuturesTrader()` | `TradingEngine()` | 主類重命名 |
| `trader.connector` | `engine.connector` | 內部組件訪問方式相同 |
| `trader.risk_manager` | `engine.risk_manager` | 風險管理器訪問相同 |
| `trader.strategy` | `engine.strategy` | 策略訪問相同 |

---

## 最佳實踐

> ⚠️ 本章節部分過時：
> 這裡同時混用了 `config/trading_config.py` 舊配置方式與環境變數方式。
> 目前若要落地，應優先以最新憑證流、`src/schemas/` 單一事實來源與現行模組路徑為準，而不是直接照本章節套用。

### 1. 📝 配置管理

#### 使用配置文件
```python
# config/trading_config.py
BINANCE_CONFIG = {
    "api_key": "your_key",
    "api_secret": "your_secret",
    "testnet": True
}

RISK_CONFIG = {
    "max_risk_per_trade": 0.02,
    "max_drawdown": 0.10,
    "max_trades_per_day": 10
}

# 使用
from config.trading_config import BINANCE_CONFIG, RISK_CONFIG
from bioneuronai import TradingEngine

engine = TradingEngine(**BINANCE_CONFIG)
engine.risk_manager.max_risk_per_trade = RISK_CONFIG["max_risk_per_trade"]
```

### 2. 🔒 安全實踐

#### 環境變數管理 API 金鑰
```python
import os
from dotenv import load_dotenv

load_dotenv()

engine = TradingEngine(
    api_key=os.getenv("BINANCE_API_KEY"),
    api_secret=os.getenv("BINANCE_API_SECRET"),
    testnet=True
)
```

#### .env 文件示例
```bash
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

### 3. 📊 日誌記錄

#### 配置詳細日誌
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

### 4. 🧪 測試優先

#### 單元測試示例
```python
import pytest
from bioneuronai.data_models import MarketData, TradingSignal
from bioneuronai.strategies import TrendFollowingStrategy

def test_trend_strategy_buy_signal():
    strategy = TrendFollowingStrategy()

    # 準備測試數據
    market_data = MarketData(
        symbol="BTCUSDT",
        price=45000.0,
        volume=1000.0,
        timestamp=1642012800000
    )

    # 執行分析
    signal = strategy.analyze(market_data)

    # 驗證結果
    assert signal.symbol == "BTCUSDT"
    assert signal.action in ["BUY", "SELL", "HOLD"]
    assert 0 <= signal.confidence <= 1
```

### 5. 📈 監控和警報

#### 添加自定義回調
```python
def on_trade_executed(trade_info):
    """交易執行後的回調"""
    # 發送通知（Telegram、Email 等）
    send_telegram_message(f"交易已執行: {trade_info}")

def on_high_risk_detected(risk_info):
    """高風險檢測回調"""
    logging.warning(f"高風險警報: {risk_info}")
    # 暫停交易
    engine.auto_trade = False

# 集成到交易引擎
engine.on_trade = on_trade_executed
engine.on_risk_alert = on_high_risk_detected
```

---

## 故障排除

### 常見問題

#### 1. ModuleNotFoundError

**問題**: `ModuleNotFoundError: No module named 'bioneuronai'`

**解決**:
```bash
# 確保在正確的目錄
cd BioNeuronai

# 安裝依賴
pip install -r requirements-crypto.txt

# 如果使用開發模式
pip install -e .
```

#### 2. API 連接失敗

**問題**: `Connection error` 或 `Timeout`

**解決**:
```python
# 1. 檢查網路連接
# 2. 確認 API 金鑰正確
# 3. 檢查是否使用正確的網路（測試網/主網）

connector = BinanceFuturesConnector(testnet=True)  # 確認 testnet 設置
account = connector.get_account_info()

if account is None:
    print("❌ 連接失敗，請檢查 API 配置")
```

#### 3. WebSocket 斷線

**問題**: WebSocket 連接頻繁斷線

**解決**: 啟用自動重連（預設已啟用）
```python
connector.subscribe_ticker_stream(
    "btcusdt", 
    callback,
    auto_reconnect=True  # 自動重連
)
```

#### 4. 類型錯誤

**問題**: `Type error` 或 Pylance 警告

**解決**: 所有類型錯誤已在 v2.0 修復
```bash
# 確保使用最新版本
git pull origin main

# 重新載入 VS Code 視窗
# Ctrl+Shift+P -> "Reload Window"
```

#### 5. 倉位計算錯誤

**問題**: 計算的倉位大小為 0 或異常大

**檢查**:
```python
# 確保參數正確
position_size = risk_manager.calculate_position_size(
    account_balance=10000.0,     # 確保 > 0
    entry_price=45000.0,         # 確保 > 0
    stop_loss=44500.0            # 確保 < entry_price (做多)
)

if position_size < 0.001:
    print("⚠️ 倉位太小，調整止損或增加資金")
```

### 調試技巧

#### 啟用詳細日誌
```python
import logging

# 設置為 DEBUG 級別
logging.getLogger('bioneuronai').setLevel(logging.DEBUG)
```

#### 檢查模塊加載
```python
import sys
print(sys.path)  # 確認模塊路徑

import bioneuronai
print(bioneuronai.__file__)  # 確認加載的包位置
```

---

## 📊 性能指標

### 架構改進成效

| 指標 | 重構前 | 重構後 | 改進 |
|------|--------|--------|------|
| **代碼行數** | 1200+ 行單檔 | 分散至 10+ 模塊 | ✅ -70% 單檔複雜度 |
| **循環複雜度** | 平均 15+ | 平均 5-8 | ✅ 降低 50% |
| **單元測試覆蓋率** | 0% | 目標 80%+ | ✅ 可測試性大幅提升 |
| **導入時間** | ~2.5s | ~1.2s | ✅ 快 52% |
| **類型錯誤** | 154 個 | 0 個 | ✅ 100% 修復 |

---

## 🚀 後續規劃

> ⚠️ 補註：
> 本章節屬於歷史規劃，不代表目前已確認的開發方向。
> 特別是 `GraphQL API`、`分散式交易`、`多帳戶協調` 這類內容，不能壓過目前「外部 API 集中、內部模組直連、避免過度設計」的基準。

### v2.1 計劃功能

- [ ] **GraphQL API**: 更靈活的數據查詢
- [ ] **插件系統**: 支持自定義策略插件
- [ ] **Web Dashboard**: 實時監控界面
- [ ] **回測引擎**: 完整的策略回測框架
- [ ] **多交易所支持**: Binance + OKX + Bybit

### v2.2 計劃功能

- [ ] **機器學習優化**: 自動調參系統
- [ ] **雲端部署**: Docker + Kubernetes
- [ ] **分散式交易**: 多帳戶協調
- [ ] **高頻策略**: 微秒級延遲優化

---

## 📚 相關文檔

- [ARCHITECTURE_REFACTORING.md](../../ARCHITECTURE_REFACTORING.md) - 架構重構總覽
- [CRYPTO_TRADING_GUIDE.md](../CRYPTO_TRADING_GUIDE.md) - 加密貨幣交易指南
- [STRATEGIES_QUICK_REFERENCE.md](../STRATEGIES_QUICK_REFERENCE.md) - 策略快速參考
- [TRADING_STRATEGIES_GUIDE.md](../TRADING_STRATEGIES_GUIDE.md) - 交易策略詳細指南

---

## 📞 技術支持

- **GitHub Issues**: [https://github.com/kyle0527/BioNeuronai/issues](https://github.com/kyle0527/BioNeuronai/issues)
- **項目主頁**: [https://github.com/kyle0527/BioNeuronai](https://github.com/kyle0527/BioNeuronai)

---

## 📝 變更日誌

### v2.0 (2026-01-19)
- ✅ 完成架構重構
- ✅ 修復所有 154 個類型錯誤
- ✅ 創建模組化目錄結構
- ✅ 添加向後兼容層
- ✅ 推送至 GitHub

---

**最後更新**: 2026年1月19日  
**維護者**: BioNeuronai 開發團隊
