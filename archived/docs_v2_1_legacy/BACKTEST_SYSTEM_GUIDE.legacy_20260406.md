# 回測系統使用指南
**創建日期**: 2026年2月15日  
**版本**: v2.1  
**適用系統**: BioNeuronai 階段 2 - 回測系統增強

---

## 📑 目錄

1. 系統概覽
2. 快速開始
3. 核心組件
4. 詳細用法
5. 進階功能
6. 性能優化
7. 故障排除
8. 最佳實踐
9. 附錄

---

## 系統概覽

BioNeuronai 回測系統提供基於真實歷史數據的策略驗證能力。

### 主要特性

| 特性 | 說明 |
|------|------|
| 📊 **真實數據** | Binance Futures API（免費、完整） |
| 💰 **精確成本** | 手續費 + 滑點 + 資金費用 |
| ⚡ **高性能** | 異步處理 + 批次載入 |
| 🎯 **靈活配置** | 多時間框架、多交易對 |
| 📈 **完整指標** | 收益率、夏普比率、最大回撤等 |

### 系統架構

```
HistoricalBacktest (總控)
    ├── HistoricalDataLoader (數據載入)
    │   └── BinanceFuturesConnector (API 客戶端)
    ├── BacktestEngine (回測引擎)
    │   ├── TradingCostCalculator (成本計算)
    │   └── SignalProcessor (信號處理)
    └── BacktestResult (結果輸出)
```

---

## 快速開始

### 最小示例（5 行代碼）

```python
from bioneuronai.backtesting import HistoricalBacktest
from schemas.backtesting import BacktestConfig
from datetime import datetime
import asyncio

async def quick_backtest():
    # 1. 配置回測
    config = BacktestConfig(
        name="快速測試",
        symbol="BTCUSDT",
        initial_capital=10000,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31)
    )

    # 2. 初始化
    backtest = HistoricalBacktest(config)

    # 3. 運行（會自動生成隨機信號供測試）
    result = await backtest.run()

    # 4. 查看結果
    print(f"總收益: {result.total_return_pct:.2f}%")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"最大回撤: {result.max_drawdown_pct:.2f}%")
    print(f"勝率: {result.win_rate:.2%}")

asyncio.run(quick_backtest())
```

### 運行測試腳本

我們提供完整的測試腳本：

```bash
# 測試所有組件
python test_backtest_system.py

# 預期輸出: 4/4 測試通過
```

---

## 核心組件

### 1. HistoricalDataLoader - 數據載入器

**功能**: 從 Binance API 載入歷史 K 線數據

#### 基礎用法

```python
from bioneuronai.backtesting import HistoricalDataLoader
from datetime import datetime

loader = HistoricalDataLoader(use_testnet=False)

data = await loader.load_data(
    symbol="BTCUSDT",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1h"
)

print(f"載入 {len(data)} 根 K 線")
print(data.head())
```

#### 數據格式

載入的 DataFrame 包含：

| 列名 | 類型 | 說明 |
|------|------|------|
| `open_time` | datetime64 | 開盤時間 |
| `open` | float64 | 開盤價 |
| `high` | float64 | 最高價 |
| `low` | float64 | 最低價 |
| `close` | float64 | 收盤價 |
| `volume` | float64 | 成交量 |

#### 支持的時間框架

```python
intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", 
             "8h", "12h", "1d", "3d", "1w", "1M"]
```

---

### 2. TradingCostCalculator - 成本計算器

**功能**: 精確計算交易成本（手續費、滑點、資金費）

#### 初始化

```python
from bioneuronai.backtesting import TradingCostCalculator

calculator = TradingCostCalculator(
    maker_fee=0.0002,      # 0.02% Maker
    taker_fee=0.0004,      # 0.04% Taker
    base_slippage=0.0005   # 0.05% 基礎滑點
)
```

#### 計算單筆交易成本

```python
from bioneuronai.backtesting.cost_calculator import OrderInfo

order = OrderInfo(
    symbol="BTCUSDT",
    side="BUY",
    quantity=1.0,
    price=50000.0,
    order_type="LIMIT",
    is_maker=True
)

cost = calculator.calculate_total_cost(order)

print(f"手續費: {cost.fee_pct:.4%} (${order.quantity * order.price * cost.fee_pct:.2f})")
print(f"滑點: {cost.slippage_pct:.4%} (${order.quantity * order.price * cost.slippage_pct:.2f})")
print(f"總成本: {cost.total_cost:.4%} (${order.quantity * order.price * cost.total_cost:.2f})")
```

#### 估算資金費用

```python
# 持倉 5 天，每天資金費率 0.01%
funding = calculator.estimate_daily_funding_cost(
    position_value=50000.0,
    funding_rate=0.0001,
    days=5
)

print(f"5 天資金費用: ${funding:.2f}")
```

---

### 3. BacktestEngine - 回測引擎

**功能**: 執行回測邏輯、處理信號、計算指標

#### 初始化

```python
from bioneuronai.backtesting.historical_backtest import BacktestEngine
from schemas.backtesting import BacktestConfig

config = BacktestConfig(
    name="我的策略",
    symbol="ETHUSDT",
    initial_capital=50000,
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 6, 30),
    # 風險參數
    max_drawdown_pct=20.0,        # 最大回撤 20%
    stop_loss_pct=5.0,             # 止損 5%
    take_profit_pct=10.0,          # 止盈 10%
    # 倉位管理
    leverage=1,                    # 1 倍槓桿（現貨）
    position_size_pct=95           # 每次使用 95% 資金
)

engine = BacktestEngine(config)
```

#### 運行回測

```python
# 準備數據與信號
data = await loader.load_data(symbol, start_date, end_date, "1h")
signals = generate_your_signals(data)  # 你的策略信號

# 執行回測
result = await engine.run_backtest(data, signals)

# 查看結果
print(f"最終資金: ${result.final_capital:,.2f}")
print(f"總交易: {result.total_trades}")
print(f"勝率: {result.win_rate:.2%}")
```

---

### 4. HistoricalBacktest - 總控類

**功能**: 整合所有組件，提供一站式回測服務

#### 完整示例：測試 RSI 策略

```python
from bioneuronai.backtesting import HistoricalBacktest
from schemas.backtesting import BacktestConfig
from datetime import datetime
import pandas as pd
import asyncio

async def backtest_rsi_strategy():
    # 1. 配置
    config = BacktestConfig(
        name="RSI 策略回測",
        symbol="BTCUSDT",
        initial_capital=100000,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31),
        interval="4h",
        max_drawdown_pct=15.0,
        stop_loss_pct=3.0,
        take_profit_pct=6.0
    )

    # 2. 初始化回測
    backtest = HistoricalBacktest(config)

    # 3. 載入數據
    loader = backtest.data_loader
    data = await loader.load_data(
        config.symbol,
        config.start_date,
        config.end_date,
        config.interval
    )

    # 4. 生成 RSI 信號
    def calculate_rsi(data: pd.DataFrame, period=14):
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    data['rsi'] = calculate_rsi(data)

    # 生成信號: RSI < 30 買入, RSI > 70 賣出
    signals = []
    position = None

    for i in range(len(data)):
        if data['rsi'].iloc[i] < 30 and position is None:
            signals.append({
                'timestamp': data['open_time'].iloc[i],
                'action': 'BUY',
                'confidence': 0.8
            })
            position = 'long'
        elif data['rsi'].iloc[i] > 70 and position == 'long':
            signals.append({
                'timestamp': data['open_time'].iloc[i],
                'action': 'SELL',
                'confidence': 0.8
            })
            position = None

    # 5. 執行回測
    result = await backtest.engine.run_backtest(data, signals)

    # 6. 輸出報告
    print("\n" + "="*60)
    print("📊 RSI 策略回測報告")
    print("="*60)
    print(f"交易對: {config.symbol}")
    print(f"時間範圍: {config.start_date.date()} 至 {config.end_date.date()}")
    print(f"時間框架: {config.interval}")
    print("-"*60)
    print(f"初始資金: ${result.initial_capital:,.2f}")
    print(f"最終資金: ${result.final_capital:,.2f}")
    print(f"總收益: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)")
    print(f"年化收益: {result.annualized_return or 0:.2f}%")
    print("-"*60)
    print(f"總交易: {result.total_trades}")
    print(f"盈利交易: {result.winning_trades}")
    print(f"虧損交易: {result.losing_trades}")
    print(f"勝率: {result.win_rate:.2%}")
    print(f"平均盈利: ${result.average_win or 0:,.2f}")
    print(f"平均虧損: ${result.average_loss or 0:,.2f}")
    print("-"*60)
    print(f"夏普比率: {result.sharpe_ratio or 0:.2f}")
    print(f"最大回撤: {result.max_drawdown_pct:.2f}%")
    print(f"手續費: ${result.total_commission:,.2f}")
    print("="*60)

    return result

# 運行
result = asyncio.run(backtest_rsi_strategy())
```

---

## 詳細用法

### 配置參數詳解

#### BacktestConfig 完整參數

```python
from schemas.backtesting import BacktestConfig
from datetime import datetime
from decimal import Decimal

config = BacktestConfig(
    # ===== 基本配置 =====
    name="策略名稱",
    description="策略描述",
    version="2.1",

    # ===== 交易對配置 =====
    symbol="BTCUSDT",              # 交易對
    interval="1h",                 # K 線週期

    # ===== 時間範圍 =====
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),

    # ===== 資金配置 =====
    initial_capital=Decimal("100000"),  # 初始資金
    leverage=1,                         # 槓桿倍數 (1 = 現貨)
    position_size_pct=95,               # 每次使用資金比例 (%)

    # ===== 風險管理 =====
    max_drawdown_pct=20.0,         # 最大回撤 (%)
    stop_loss_pct=5.0,             # 止損 (%)
    take_profit_pct=10.0,          # 止盈 (%)

    # ===== 成本配置 =====
    maker_fee=0.02,                # Maker 手續費 (%)
    taker_fee=0.04,                # Taker 手續費 (%)
    slippage=0.05,                 # 滑點 (%)

    # ===== 其他 =====
    use_testnet=False,             # 使用測試網
    enable_short=False,            # 允許做空
    max_positions=1                # 最大同時持倉數
)
```

### 信號格式說明

回測引擎支持的信號格式：

```python
signals = [
    {
        'timestamp': datetime(2025, 1, 1, 10, 0),  # 必填: 信號時間
        'action': 'BUY',                            # 必填: 動作 (BUY/SELL)
        'confidence': 0.85,                         # 可選: 信心度 (0-1)
        'reason': 'RSI oversold'                    # 可選: 信號原因
    },
    {
        'timestamp': datetime(2025, 1, 2, 14, 0),
        'action': 'SELL',
        'confidence': 0.75,
        'reason': 'RSI overbought'
    }
]
```

### 結果解析

#### BacktestResult 字段說明

```python
result = await backtest.run()

# ===== 識別信息 =====
result.backtest_id         # UUID: 回測唯一識別
result.config              # BacktestConfig: 配置對象
result.status              # BacktestStatus: 狀態 (COMPLETED/FAILED)

# ===== 執行時間 =====
result.started_at          # datetime: 開始時間
result.completed_at        # datetime: 完成時間
result.execution_time_seconds  # float: 執行耗時

# ===== 基本統計 =====
result.total_trades        # int: 總交易次數
result.winning_trades      # int: 盈利交易次數
result.losing_trades       # int: 虧損交易次數
result.win_rate            # Decimal: 勝率 (0-1)

# ===== 收益指標 =====
result.initial_capital     # Decimal: 初始資金
result.final_capital       # Decimal: 最終資金
result.total_return        # Decimal: 總收益 ($)
result.total_return_pct    # Decimal: 總收益率 (%)
result.annualized_return   # Decimal: 年化收益率 (%)

# ===== 風險指標 =====
result.max_drawdown        # Decimal: 最大回撤 ($)
result.max_drawdown_pct    # Decimal: 最大回撤百分比 (%)
result.sharpe_ratio        # float: 夏普比率
result.sortino_ratio       # float: 索提諾比率
result.calmar_ratio        # Decimal: 卡爾馬比率

# ===== 成本統計 =====
result.total_commission    # Decimal: 總手續費 ($)
result.gross_profit        # Decimal: 總毛利 ($)
result.gross_loss          # Decimal: 總毛損 ($)

# ===== 交易統計 =====
result.average_win         # Decimal: 平均盈利 ($)
result.average_loss        # Decimal: 平均虧損 ($)
result.largest_win         # Decimal: 最大單筆盈利 ($)
result.largest_loss        # Decimal: 最大單筆虧損 ($)
result.max_consecutive_wins    # int: 最大連勝次數
result.max_consecutive_losses  # int: 最大連敗次數

# ===== 權益曲線 =====
result.equity_curve        # list: [{'time': datetime, 'equity': float}, ...]

# ===== 交易記錄 =====
result.trades              # list[TradeRecord]: 所有交易詳情
```

---

## 進階功能

### 1. 批次回測（參數優化）

測試多組參數組合：

```python
async def batch_backtest():
    results = []

    # 參數網格
    rsi_periods = [10, 14, 20]
    rsi_oversold = [20, 25, 30]
    rsi_overbought = [70, 75, 80]

    for period in rsi_periods:
        for oversold in rsi_oversold:
            for overbought in rsi_overbought:
                # 生成策略
                signals = generate_rsi_signals(data, period, oversold, overbought)

                # 運行回測
                config = BacktestConfig(
                    name=f"RSI_{period}_{oversold}_{overbought}",
                    symbol="BTCUSDT",
                    initial_capital=10000,
                    start_date=datetime(2025, 1, 1),
                    end_date=datetime(2025, 12, 31)
                )

                backtest = HistoricalBacktest(config)
                result = await backtest.run()

                results.append({
                    'params': (period, oversold, overbought),
                    'return': result.total_return_pct,
                    'sharpe': result.sharpe_ratio,
                    'drawdown': result.max_drawdown_pct
                })

    # 找最佳參數
    best = max(results, key=lambda x: x['sharpe'])
    print(f"最佳參數: RSI({best['params'][0]}, {best['params'][1]}, {best['params'][2]})")
    print(f"夏普比率: {best['sharpe']:.2f}")

    return results
```

### 2. 多交易對回測

同時回測多個交易對：

```python
async def multi_symbol_backtest():
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"]
    results = {}

    for symbol in symbols:
        config = BacktestConfig(
            name=f"{symbol}_Strategy",
            symbol=symbol,
            initial_capital=10000,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31)
        )

        backtest = HistoricalBacktest(config)
        result = await backtest.run()

        results[symbol] = {
            'return': float(result.total_return_pct),
            'sharpe': float(result.sharpe_ratio or 0),
            'trades': result.total_trades
        }

    # 報告
    print("\n多交易對回測結果:")
    for symbol, metrics in results.items():
        print(f"{symbol:10} | 收益: {metrics['return']:>7.2f}% | "
              f"夏普: {metrics['sharpe']:>5.2f} | 交易: {metrics['trades']:>3}")

    return results
```

### 3. 自定義成本模型

實現更複雜的成本計算：

```python
class AdvancedCostCalculator(TradingCostCalculator):
    """高級成本計算器 - 考慮市場深度"""

    def calculate_slippage(
        self,
        order: OrderInfo,
        market_depth: Optional[dict] = None,
        recent_volatility: Optional[float] = None
    ) -> float:
        # 基礎滑點
        slippage = self.base_slippage

        # 根據市場深度調整
        if market_depth:
            order_size_ratio = order.quantity * order.price / market_depth['total_bid_volume']
            slippage *= (1 + order_size_ratio * 10)  # 大單增加滑點

        # 根據波動率調整
        if recent_volatility:
            slippage *= (1 + recent_volatility / 0.01)  # 高波動增加滑點

        # 市價單額外滑點
        if order.order_type == "MARKET":
            slippage *= 1.5

        return slippage
```

### 4. 權益曲線可視化

生成圖表展示回測過程：

```python
import matplotlib.pyplot as plt

def plot_equity_curve(result: BacktestResult):
    """繪製權益曲線"""
    if not result.equity_curve:
        print("無權益曲線數據")
        return

    times = [point['time'] for point in result.equity_curve]
    equity = [point['equity'] for point in result.equity_curve]

    plt.figure(figsize=(12, 6))
    plt.plot(times, equity, label='權益曲線', linewidth=2)
    plt.axhline(y=float(result.initial_capital), 
                color='r', linestyle='--', label='初始資金')

    plt.title(f"{result.config.name} - 權益曲線", fontsize=14)
    plt.xlabel("時間")
    plt.ylabel("資金 ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"equity_curve_{result.backtest_id}.png")
    plt.show()

# 使用
result = await backtest.run()
plot_equity_curve(result)
```

---

## 性能優化

### 1. 數據緩存

避免重複載入相同數據：

```python
from functools import lru_cache
import hashlib

class CachedDataLoader(HistoricalDataLoader):
    """帶緩存的數據載入器"""

    def __init__(self, cache_dir="./cache", **kwargs):
        super().__init__(**kwargs)
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    async def load_data(self, symbol, start_date, end_date, interval):
        # 生成緩存鍵
        key = f"{symbol}_{start_date.date()}_{end_date.date()}_{interval}"
        cache_file = f"{self.cache_dir}/{key}.parquet"

        # 檢查緩存
        if os.path.exists(cache_file):
            logger.info(f"從緩存載入: {cache_file}")
            return pd.read_parquet(cache_file)

        # 載入數據
        data = await super().load_data(symbol, start_date, end_date, interval)

        # 保存緩存
        data.to_parquet(cache_file)
        logger.info(f"已緩存數據: {cache_file}")

        return data
```

### 2. 並行回測

使用 asyncio 並行執行多個回測：

```python
async def parallel_backtest(configs: list[BacktestConfig]):
    """並行執行多個回測"""
    tasks = []

    for config in configs:
        backtest = HistoricalBacktest(config)
        task = asyncio.create_task(backtest.run())
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 過濾錯誤
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    print(f"成功: {len(successful)}, 失敗: {len(failed)}")
    return successful

# 使用
configs = [
    BacktestConfig(name=f"Test_{i}", symbol="BTCUSDT", ...) 
    for i in range(10)
]
results = await parallel_backtest(configs)
```

### 3. 減少內存使用

處理大規模數據時：

```python
# 使用生成器逐條處理
def process_signals_stream(data: pd.DataFrame):
    """流式處理信號"""
    for i in range(len(data)):
        row = data.iloc[i]
        signal = generate_signal(row)
        if signal:
            yield signal

# 使用
for signal in process_signals_stream(data):
    engine.process_signal(signal)
```

---

## 故障排除

### 常見問題

#### 1. 網絡連接失敗

**錯誤**: `HTTPError: 503 Service Unavailable`

**解決**:
```python
# 增加重試機制
import tenacity

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(min=1, max=10)
)
async def load_with_retry(loader, symbol, start, end, interval):
    return await loader.load_data(symbol, start, end, interval)
```

#### 2. 數據缺失

**錯誤**: `WARNING: 無數據`

**原因**:
- 交易對名稱錯誤（如 BTCUSD 應為 BTCUSDT）
- 時間範圍超出歷史深度
- 該交易對不存在於指定日期

**解決**:
```python
# 驗證交易對
from bioneuronai.data.binance_futures import BinanceFuturesConnector

client = BinanceFuturesConnector()
info = client.get_exchange_info()
valid_symbols = [s['symbol'] for s in info['symbols']]

if symbol not in valid_symbols:
    print(f"❌ 無效交易對: {symbol}")
    print(f"✅ 可用交易對: {valid_symbols[:10]}...")
```

#### 3. 回測結果異常

**問題**: 收益率過高或過低

**檢查清單**:
1. 信號時間與數據時間是否對齊
2. 是否包含未來信息（Look-ahead bias）
3. 成本計算是否正確
4. 槓桿倍數設置

**調試**:
```python
# 啟用詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)

# 檢查信號
for i, signal in enumerate(signals[:5]):
    print(f"Signal {i}: {signal}")
    # 驗證時間在數據範圍內
    assert data['open_time'].iloc[0] <= signal['timestamp'] <= data['open_time'].iloc[-1]
```

#### 4. Pydantic 驗證錯誤

**錯誤**: `ValidationError: Field required`

**原因**: BacktestResult 缺少必填字段

**已修復**: v4.0.0 版本已修復此問題

---

## 最佳實踐

### 1. 數據質量檢查

回測前驗證數據：

```python
def validate_data(data: pd.DataFrame):
    """驗證數據質量"""
    checks = {
        "時間序列": data['open_time'].is_monotonic_increasing,
        "無缺失值": not data[['open', 'high', 'low', 'close']].isnull().any().any(),
        "價格邏輯": (data['high'] >= data['low']).all(),
        "OHLC 關係": ((data['high'] >= data['open']) & 
                      (data['high'] >= data['close']) &
                      (data['low'] <= data['open']) & 
                      (data['low'] <= data['close'])).all(),
        "成交量非負": (data['volume'] >= 0).all()
    }

    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")

    return all(checks.values())

# 使用
data = await loader.load_data(...)
if not validate_data(data):
    raise ValueError("數據質量檢查失敗")
```

### 2. 樣本外測試

避免過擬合：

```python
# 訓練期 + 測試期
train_end = datetime(2025, 9, 30)
test_start = datetime(2025, 10, 1)

# 訓練期回測（用於優化參數）
train_config = BacktestConfig(
    name="Train",
    symbol="BTCUSDT",
    start_date=datetime(2025, 1, 1),
    end_date=train_end,
    ...
)
train_result = await HistoricalBacktest(train_config).run()

# 測試期回測（用於驗證策略）
test_config = BacktestConfig(
    name="Test",
    symbol="BTCUSDT",
    start_date=test_start,
    end_date=datetime(2025, 12, 31),
    ...
)
test_result = await HistoricalBacktest(test_config).run()

# 比較結果
print(f"訓練期夏普: {train_result.sharpe_ratio:.2f}")
print(f"測試期夏普: {test_result.sharpe_ratio:.2f}")
print(f"夏普衰減: {(1 - test_result.sharpe_ratio / train_result.sharpe_ratio) * 100:.1f}%")
```

### 3. 風險管理測試

測試極端市場條件：

```python
# 2020 年 3 月加密貨幣崩盤
crash_test = BacktestConfig(
    name="Crash Test",
    symbol="BTCUSDT",
    start_date=datetime(2020, 3, 1),
    end_date=datetime(2020, 3, 31),
    ...
)

crash_result = await HistoricalBacktest(crash_test).run()
print(f"崩盤期最大回撤: {crash_result.max_drawdown_pct:.2f}%")
```

### 4. 性能基準比較

與買入持有策略對比：

```python
async def compare_with_buy_hold(config: BacktestConfig):
    """與買入持有策略對比"""
    # 策略回測
    strategy_result = await HistoricalBacktest(config).run()

    # 買入持有回測
    loader = HistoricalDataLoader()
    data = await loader.load_data(config.symbol, config.start_date, config.end_date, "1d")

    buy_hold_return = (data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0] * 100

    # 比較
    print(f"策略收益: {strategy_result.total_return_pct:>7.2f}%")
    print(f"買入持有: {buy_hold_return:>7.2f}%")
    print(f"超額收益: {strategy_result.total_return_pct - buy_hold_return:>7.2f}%")

    return strategy_result.total_return_pct > buy_hold_return
```

---

## 附錄

### A. 完整 API 參考

請參閱以下模組的 docstring：
- `src/bioneuronai/backtesting/historical_backtest.py`
- `src/bioneuronai/backtesting/cost_calculator.py`
- `src/schemas/backtesting.py`

### B. 相關文檔

- [BACKTEST_DATA_SOURCE.md](BACKTEST_DATA_SOURCE.md) - 數據來源詳解
- [CODE_FIX_GUIDE.md](CODE_FIX_GUIDE.md) - 開發規範
- [RISK_MANAGEMENT_MANUAL.md](RISK_MANAGEMENT_MANUAL.md) - 風險管理

### C. 聯繫支持

如遇問題，請：
1. 檢查日誌文件 (`logs/backtest_*.log`)
2. 運行測試腳本 (`test_backtest_system.py`)
3. 查閱本文檔故障排除章節
4. 提交 Issue 到項目倉庫

---

**文檔版本**: v2.1  
**最後更新**: 2026年2月15日  
**適用版本**: BioNeuronai v2.1+  
**作者**: BioNeuronai 開發團隊
