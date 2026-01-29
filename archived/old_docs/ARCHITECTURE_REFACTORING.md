# 交易系統架構重構說明

## 📁 新架構概覽

```
src/bioneuronai/
├── data_models/              # 數據模型層
│   └── __init__.py          # MarketData, TradingSignal, Position, OrderResult
│
├── connectors/              # API 連接器層
│   ├── __init__.py
│   └── binance_futures.py   # Binance Futures API 連接器
│
├── risk_management/         # 風險管理層
│   ├── __init__.py
│   └── risk_manager.py      # RiskManager, RiskParameters, PositionSizeCalculator
│
├── strategies/              # 策略層（已存在）
│   ├── trend_following.py
│   ├── swing_trading.py
│   ├── mean_reversion.py
│   ├── breakout_trading.py
│   └── strategy_fusion.py
│
├── trading_engine.py        # 主交易引擎（新）
├── crypto_futures_trader.py # 向後兼容層（舊接口）
└── news_analyzer.py         # 新聞分析服務
```

## 🔄 重構前後對比

### 原架構問題
- ❌ 單一巨大文件 (1200+ 行)
- ❌ 所有功能耦合在一起
- ❌ 難以測試和維護
- ❌ 代碼重複
- ❌ 缺乏清晰的職責分離

### 新架構優勢
- ✅ 模塊化設計，職責清晰
- ✅ 易於單元測試
- ✅ 可擴展性強
- ✅ 代碼複用率高
- ✅ 易於維護和調試

## 📦 模塊說明

### 1. **data_models** - 數據模型層
**職責**: 定義所有核心數據結構
- `MarketData`: 市場數據
- `TradingSignal`: 交易信號
- `Position`: 持倉信息
- `OrderResult`: 訂單結果

**特點**:
- 使用 `@dataclass` 減少樣板代碼
- 類型安全
- 易於序列化

### 2. **connectors** - API 連接器層
**職責**: 處理與交易所的所有交互
- REST API 請求
- WebSocket 實時數據流
- 簽名認證
- 速率限制控制
- 自動重連機制

**優勢**:
- 統一的錯誤處理
- 自動速率限制
- 請求重試機制
- 連接池管理

### 3. **risk_management** - 風險管理層
**職責**: 全面的風險控制
- 倉位大小計算（Kelly, Fixed Risk, Volatility Adjusted）
- 回撤監控
- 交易頻率控制
- 置信度檢查
- 時間窗口控制

**核心類**:
- `RiskManager`: 綜合風險管理器
- `RiskParameters`: 風險參數配置
- `PositionSizeCalculator`: 倉位計算器
- `DrawdownTracker`: 回撤追蹤器
- `TradeCounter`: 交易計數器

### 4. **trading_engine** - 主交易引擎
**職責**: 整合所有模塊，提供統一接口
- 市場監控
- 信號處理
- 訂單執行
- 數據持久化
- 新聞分析整合

**特點**:
- 事件驅動架構
- 異步處理
- 狀態管理
- 完整的生命週期管理

## 🚀 使用方式

### 方式 1: 使用新架構（推薦）

```python
from src.bioneuronai.trading_engine import TradingEngine

# 創建交易引擎
engine = TradingEngine(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True,
    strategy_type="fusion",
    risk_config_path="risk_config.json"  # 可選
)

# 啟用自動交易
engine.enable_auto_trading()

# 開始監控
engine.start_monitoring("BTCUSDT")

# 停止時保存數據
engine.stop_monitoring()
engine.save_all_data()
```

### 方式 2: 使用舊接口（向後兼容）

```python
from src.bioneuronai.crypto_futures_trader import CryptoFuturesTrader

# 舊代碼無需修改，完全兼容
trader = CryptoFuturesTrader(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True
)

trader.start_monitoring("BTCUSDT")
```

## 🔧 配置管理

### 風險配置文件 (risk_config.json)

```json
{
  "max_risk_per_trade": 0.02,
  "max_drawdown": 0.10,
  "max_trades_per_day": 10,
  "min_confidence": 0.65,
  "max_position_ratio": 0.25,
  "max_correlation": 0.7,
  "default_stop_loss": 0.02,
  "default_take_profit": 0.04,
  "trading_hours_start": 0,
  "trading_hours_end": 23
}
```

### 動態更新風險參數

```python
# 運行時調整風險參數
engine.risk_manager.update_risk_parameters(
    max_risk_per_trade=0.01,  # 降低到 1%
    max_trades_per_day=5       # 減少每日交易次數
)

# 保存配置
engine.risk_manager.save_config("updated_risk_config.json")
```

## 📊 數據持久化

新架構自動保存以下數據：

1. **交易歷史** (`trades_history.jsonl`)
   - 每筆交易的詳細記錄
   - JSONL 格式，便於流式處理

2. **信號歷史** (`signals_history.json`)
   - 最近 1000 條交易信號
   - 包含時間戳和策略信息

3. **策略權重** (`strategy_weights.json`)
   - 策略融合的動態權重
   - 表現歷史記錄

4. **風險統計** (`risk_statistics.json`)
   - 回撤數據
   - 交易統計
   - 表現指標

5. **風險配置** (`risk_config.json`)
   - 當前風險參數
   - 可重新載入

## 🧪 測試

### 單元測試示例

```python
# 測試風險管理器
def test_risk_manager():
    rm = RiskManager()
    
    # 測試倉位計算
    position = rm.calculate_position_size(
        account_balance=10000,
        entry_price=50000,
        stop_loss_price=49000
    )
    
    assert position > 0
    assert position <= rm.parameters.max_position_ratio

# 測試連接器
def test_connector():
    connector = BinanceFuturesConnector(testnet=True)
    price = connector.get_ticker_price("BTCUSDT")
    
    assert price is not None
    assert price.price > 0
```

## 🔜 未來擴展

### 計劃功能

1. **多交易所支持**
   ```python
   from connectors import OKXConnector, BybitConnector
   
   engine = TradingEngine(
       connectors=[
           BinanceFuturesConnector(...),
           OKXConnector(...),
           BybitConnector(...)
       ]
   )
   ```

2. **高級分析模塊**
   - 技術指標庫擴展
   - 量化分析工具
   - 回測引擎增強

3. **機器學習整合**
   - 預測模型接口
   - 自動特徵工程
   - 模型訓練管道

4. **Web 管理界面**
   - 實時監控儀表板
   - 配置管理界面
   - 交易報表生成

5. **通知系統**
   - Telegram 機器人
   - 郵件通知
   - Webhook 支持

## 📝 最佳實踐

### 1. 錯誤處理

```python
try:
    engine.start_monitoring("BTCUSDT")
except Exception as e:
    logger.error(f"監控失敗: {e}")
    engine.save_all_data()  # 確保數據保存
```

### 2. 優雅關閉

```python
import signal

def signal_handler(sig, frame):
    print("\\n停止交易系統...")
    engine.stop_monitoring()
    engine.save_all_data()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
```

### 3. 日誌配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)
```

## 🐛 調試技巧

### 啟用詳細日誌

```python
import logging
logging.getLogger('src.bioneuronai').setLevel(logging.DEBUG)
```

### 模擬模式

```python
# 不實際下單，僅記錄
engine.auto_trade = False
engine.start_monitoring("BTCUSDT")
```

### 風險參數測試

```python
# 使用極保守的參數測試
engine.risk_manager.update_risk_parameters(
    max_risk_per_trade=0.001,  # 0.1%
    max_trades_per_day=1
)
```

## 📚 相關文檔

- [Binance API 文檔](https://binance-docs.github.io/apidocs/futures/cn/)
- [策略開發指南](STRATEGIES_IMPLEMENTATION_SUMMARY.md)
- [風險管理詳解](docs/RISK_MANAGEMENT.md)

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License