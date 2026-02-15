# 🕰️ Backtest Module - 時光機回測引擎

**路徑**: `backtest/`  
**版本**: v4.0.0  
**更新日期**: 2026-02-15

---

## 📋 目錄

- [設計目標](#設計目標)
- [模組結構](#模組結構)
- [快速開始](#快速開始)
- [防偷看機制詳解](#防偷看機制詳解)
- [虛擬帳戶功能](#虛擬帳戶功能)
- [接口偽裝對照表](#接口偽裝對照表)
- [回測結果指標](#回測結果指標)
- [配置參數](#配置參數)
- [數據目錄結構](#數據目錄結構)
- [注意事項](#注意事項)
- [相關文檔](#相關文檔)

---

## 🎯 設計目標

將歷史數據變成「即時串流」，讓 AI 以為它在做真實交易。

### 核心原則

1. **時光機機制**: 使用 `yield` 生成器逐根吐出數據
2. **嚴格防偷看**: 在 T 時刻絕對看不到 T+1 的數據
3. **接口偽裝**: `MockBinanceConnector` 完全模擬真實 API
4. **狀態仿真**: 模擬撮合、手續費、滑點、帳戶餘額
5. **無縫切換**: TradingEngine 不改任何代碼即可切換模式

---

## 📦 模組結構

```
backtest/
├── __init__.py              # 模組入口
├── data_stream.py           # 歷史數據串流生成器
├── virtual_account.py       # 虛擬帳戶狀態仿真
├── mock_connector.py        # 接口偽裝 (核心)
├── backtest_engine.py       # 回測引擎主類
└── README.md                # 本文檔
```

---

## 🚀 快速開始

### 方法 1: 簡單回測

```python
from bioneuronai.backtest import quick_backtest

# 定義策略
def my_strategy(bar, connector):
    # bar: 當前 K線數據
    # connector: Mock 連接器 (與真實 API 相同接口)
    
    if bar.close > bar.open * 1.001:  # 上漲 0.1%
        connector.place_order(bar.symbol, "BUY", "MARKET", 0.01)
    elif bar.close < bar.open * 0.999:  # 下跌 0.1%
        connector.place_order(bar.symbol, "SELL", "MARKET", 0.01)

# 運行回測
result = quick_backtest(
    my_strategy,
    symbol="BTCUSDT",
    start_date="2025-01-01",
    end_date="2025-06-30",
    initial_balance=10000
)

# 查看結果
print(f"總收益率: {result.stats['total_return']:.2f}%")
print(f"勝率: {result.stats['win_rate']:.1f}%")
```

### 方法 2: 與 TradingEngine 整合 (推薦)

```python
from bioneuronai.core import TradingEngine
from bioneuronai.backtest import create_mock_connector

# 1. 創建 Mock 連接器
mock = create_mock_connector(
    symbol="BTCUSDT",
    start_date="2025-01-01",
    end_date="2025-06-30",
    initial_balance=10000
)

# 2. 創建 TradingEngine
engine = TradingEngine(api_key="", api_secret="", testnet=True)

# 3. 替換連接器 - TradingEngine 完全不知道這是回測!
engine.connector = mock

# 4. 現在可以像實盤一樣使用 TradingEngine
# 它會在歷史數據上運行，以為是真實交易

# 運行回測
for bar in mock.data_stream.stream_bars():
    mock.account.update_price(bar.symbol, bar.close)
    mock._current_bar = bar
    
    # 使用 TradingEngine 的方法
    market_data = engine.connector.get_ticker_price(bar.symbol)
    # engine.analyze_and_trade(bar.symbol)  # 或其他方法
```

### 方法 3: 完整控制

```python
from bioneuronai.backtest import BacktestEngine, BacktestConfig

# 詳細配置
config = BacktestConfig(
    data_dir="data_downloads/binance_historical",
    symbol="ETHUSDT",
    interval="5m",
    start_date="2025-01-01",
    end_date="2025-12-31",
    initial_balance=50000,
    leverage=3,
    maker_fee=0.0002,
    taker_fee=0.0004,
    slippage_rate=0.0001,
    warmup_bars=200,  # 預熱期
)

# 創建引擎
engine = BacktestEngine(config=config)

# 定義策略
def advanced_strategy(bar, connector):
    # 獲取歷史 K線 (防偷看: 只能看到當前時間點之前的數據)
    klines = connector.get_klines(bar.symbol, limit=100)
    
    if not klines or len(klines) < 20:
        return
    
    # 計算 SMA
    closes = [float(k[4]) for k in klines[-20:]]
    sma = sum(closes) / len(closes)
    
    # 獲取當前倉位
    position = connector.get_position(bar.symbol)
    
    if bar.close > sma * 1.01 and not position:
        # 突破 SMA 1%，開多
        connector.place_order(
            bar.symbol, "BUY", "MARKET", 0.1,
            stop_loss=bar.close * 0.98,
            take_profit=bar.close * 1.05
        )
    elif bar.close < sma * 0.99 and not position:
        # 跌破 SMA 1%，開空
        connector.place_order(
            bar.symbol, "SELL", "MARKET", 0.1,
            stop_loss=bar.close * 1.02,
            take_profit=bar.close * 0.95
        )

# 運行回測
result = engine.run(advanced_strategy)

# 保存結果
result.save("backtest_result.json")
```

---

## 🔒 防偷看機制詳解

### 為什麼重要？

在回測中，最常見的錯誤是「偷看未來數據」(Look-ahead Bias)：

```python
# ❌ 錯誤示例 - 偷看未來
data = pd.read_csv("btc_data.csv")
for i in range(len(data)):
    if data['close'][i+1] > data['close'][i]:  # 看到了 i+1 的數據!
        buy()  # 這會產生不現實的完美績效
```

### 我們的解決方案

使用 Python 的 `yield` 生成器，確保數據只能按時間順序讀取：

```python
# ✅ 正確方式 - 生成器防偷看
def stream_bars(self):
    for i in range(len(self.data)):
        bar = self.data.iloc[i]
        
        # 更新歷史窗口 (只包含 i 及之前的數據)
        self._history_window.append(bar)
        
        # yield 確保調用者只能看到這一根 K線
        yield bar
        
        # 調用者在這裡無法獲取 i+1 的數據
```

### 使用示例

```python
# 在 T 時刻
bar = next(stream)  # 獲取當前 K線
klines = connector.get_klines(limit=100)  # 只能獲取 T 及之前的數據

# 即使嘗試獲取更多數據
all_klines = connector.get_klines(limit=99999)  
# 結果仍然只有 T 及之前的數據
```

---

## 📊 虛擬帳戶功能

### 完整的交易模擬

```python
account = connector.account

# 下單
order = connector.place_order("BTCUSDT", "BUY", "MARKET", 0.1)

# 訂單會被模擬撮合，包括：
# - 滑點計算 (基於訂單大小)
# - 手續費扣除 (Maker/Taker)
# - 倉位更新
# - 保證金計算

# 查看帳戶狀態
print(f"餘額: {account.get_balance()}")
print(f"可用餘額: {account.get_available_balance()}")
print(f"總權益: {account.get_total_equity()}")

# 查看倉位
position = account.get_position("BTCUSDT")
if position:
    print(f"方向: {position.side}")
    print(f"數量: {position.quantity}")
    print(f"入場價: {position.entry_price}")
    print(f"未實現盈虧: {position.unrealized_pnl}")
```

### 支持的功能

- ✅ 市價單立即撮合
- ✅ 限價單掛單等待
- ✅ 止損單 (STOP_MARKET)
- ✅ 止盈單 (TAKE_PROFIT_MARKET)
- ✅ 滑點模擬 (基於訂單大小)
- ✅ Maker/Taker 手續費
- ✅ 保證金計算
- ✅ 強制平倉機制
- ✅ 多倉位管理

---

## 🎭 接口偽裝對照表

| 真實 BinanceFuturesConnector | MockBinanceConnector |
|------------------------------|----------------------|
| `get_ticker_price(symbol)` | ✅ 完全相同 |
| `get_ticker_24hr(symbol)` | ✅ 完全相同 |
| `get_klines(symbol, interval, limit)` | ✅ 完全相同 |
| `get_order_book(symbol, limit)` | ✅ 完全相同 |
| `get_funding_rate(symbol)` | ✅ 完全相同 |
| `get_open_interest(symbol)` | ✅ 完全相同 |
| `get_account_info()` | ✅ 完全相同 |
| `place_order(...)` | ✅ 完全相同 |
| `subscribe_ticker_stream(...)` | ✅ 完全相同 |
| `close_all_connections()` | ✅ 完全相同 |

---

## 📈 回測結果指標

### 基礎指標
- 總收益率
- 實現盈虧
- 總交易次數
- 勝率

### 風險指標
- 最大回撤
- 夏普比率 (Sharpe Ratio)
- 索提諾比率 (Sortino Ratio)
- 卡爾瑪比率 (Calmar Ratio)

### 交易統計
- 獲利因子 (Profit Factor)
- 最大連續虧損
- 平均每筆交易 K線數

---

## 🔧 配置參數

| 參數 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `data_dir` | str | - | 歷史數據目錄 |
| `symbol` | str | "BTCUSDT" | 交易對 |
| `interval` | str | "1m" | K線間隔 |
| `start_date` | str | None | 開始日期 (YYYY-MM-DD) |
| `end_date` | str | None | 結束日期 |
| `initial_balance` | float | 10000 | 初始餘額 |
| `leverage` | int | 1 | 槓桿倍數 |
| `maker_fee` | float | 0.0002 | Maker 手續費 (0.02%) |
| `taker_fee` | float | 0.0004 | Taker 手續費 (0.04%) |
| `slippage_rate` | float | 0.0001 | 基礎滑點率 (0.01%) |
| `warmup_bars` | int | 100 | 預熱期 K線數 |

---

## 📁 數據目錄結構

回測引擎會自動尋找以下結構的數據：

```
data_downloads/binance_historical/
└── data/
    └── futures/
        └── um/
            └── daily/
                └── klines/
                    └── BTCUSDT/
                        └── 1m/
                            ├── BTCUSDT-1m-2025-01-01.zip
                            ├── BTCUSDT-1m-2025-01-02.zip
                            └── ...
```

---

## ⚠️ 注意事項

1. **數據質量**: 回測結果依賴數據質量，確保使用乾淨的歷史數據
2. **過度擬合**: 避免在回測數據上過度優化參數
3. **滑點假設**: 實際滑點可能大於模擬值
4. **流動性**: 模擬不考慮市場流動性限制
5. **極端行情**: 歷史數據可能不包含極端行情

---

## 🔗 相關文檔

- [交易系統主文檔](../src/bioneuronai/README.md)
- [數據下載工具](../tools/data_download/download-kline.py)
- [策略開發指南](../src/bioneuronai/strategies/README.md)
- [風險管理手冊](../docs/RISK_MANAGEMENT_MANUAL.md)

---

**最後更新**: 2026年2月15日

> 📖 上層目錄：[根目錄 README](../README.md)
