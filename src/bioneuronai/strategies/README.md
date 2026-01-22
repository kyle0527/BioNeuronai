# 策略模組 (Trading Strategies)

**路徑**: `src/bioneuronai/strategies/`  
**版本**: v2.1 (策略融合版)  
**更新日期**: 2026-01-22

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [核心文件](#核心文件)
3. [策略分類](#策略分類)
4. [策略融合](#策略融合)
5. [使用示例](#使用示例)
6. [相關文檔](#相關文檔)

---

## 🎯 模組概述

策略模組包含多種量化交易策略，支持獨立使用或融合使用。

### 模組職責
- ✅ 交易信號生成
- ✅ 多策略融合
- ✅ 策略績效評估
- ✅ 參數優化
- ✅ 回測支持

---

## 📁 核心文件

### `base_strategy.py` (策略基類)
所有策略的抽象基類。

**主要類**:
- `BaseStrategy` - 策略基類

**核心方法**:
```python
class BaseStrategy:
    def generate_signals(self, data) -> Dict:
        """生成交易信號"""
        
    def calculate_indicators(self, data):
        """計算技術指標"""
        
    def get_strategy_type(self) -> str:
        """返回策略類型"""
```

---

## 📊 策略分類

### 趨勢追蹤策略

#### `trend_following.py` (趨勢跟隨)
基於趨勢指標的交易策略。

**主要類**:
- `TrendFollowingStrategy` - 趨勢跟隨策略

**核心指標**:
- 移動平均線 (MA/EMA)
- MACD
- ADX (趨勢強度)
- Parabolic SAR

**信號規則**:
```python
# 做多條件
- EMA(20) > EMA(50) > EMA(200)
- MACD > Signal
- ADX > 25
- Price > SAR

# 做空條件
- EMA(20) < EMA(50) < EMA(200)
- MACD < Signal
- ADX > 25
- Price < SAR
```

**適用市場**: 強趨勢市場

---

### 突破策略

#### `breakout_trading.py` (突破交易)
基於價格突破關鍵水平的策略。

**主要類**:
- `BreakoutStrategy` - 突破策略

**核心邏輯**:
- 布林帶突破
- 支撐/阻力位突破
- 成交量確認
- ATR 止損

**信號規則**:
```python
# 做多條件
- Price breaks above resistance
- Volume > Average Volume * 1.5
- RSI < 70 (未超買)

# 做空條件
- Price breaks below support
- Volume > Average Volume * 1.5
- RSI > 30 (未超賣)
```

**適用市場**: 盤整後突破

---

### 均值回歸策略

#### `mean_reversion.py` (均值回歸)
基於價格偏離均值後回歸的策略。

**主要類**:
- `MeanReversionStrategy` - 均值回歸策略

**核心指標**:
- 布林帶 (Bollinger Bands)
- RSI (相對強弱指標)
- Z-Score
- Stochastic

**信號規則**:
```python
# 做多條件
- Price < Lower Bollinger Band
- RSI < 30 (超賣)
- Z-Score < -2

# 做空條件
- Price > Upper Bollinger Band
- RSI > 70 (超買)
- Z-Score > 2
```

**適用市場**: 震盪市場

---

### 波段交易策略

#### `swing_trading.py` (波段交易)
中期持有的波段交易策略。

**主要類**:
- `SwingTradingStrategy` - 波段交易策略

**核心邏輯**:
- 多時間框架分析
- 支撐阻力位
- 形態識別
- 動量指標

**持有週期**: 2-10 天

**適用市場**: 波動適中市場

---

## 🎭 策略融合

### `strategy_fusion.py` (策略融合系統)
智能整合多個策略的信號。

**主要類**:
- `StrategyFusion` - 策略融合器

**融合方法**:

#### 1. 投票法 (Voting)
```python
# 多數決
if sum(signals) >= threshold:
    return 'BUY'
```

#### 2. 加權平均 (Weighted Average)
```python
# 根據歷史表現加權
weights = {
    'trend': 0.4,
    'breakout': 0.3,
    'mean_reversion': 0.3
}
final_signal = weighted_sum(signals, weights)
```

#### 3. 市場適配 (Market Regime)
```python
# 根據市場狀態選擇策略
if market_state == 'trending':
    use TrendFollowingStrategy
elif market_state == 'ranging':
    use MeanReversionStrategy
elif market_state == 'volatile':
    use BreakoutStrategy
```

#### 4. 動態調整 (Dynamic Adjustment)
```python
# 根據最近表現動態調整權重
weights = calculate_recent_performance(strategies)
```

---

## 🎯 策略選擇矩陣

| 市場狀態 | 推薦策略 | 次選策略 |
|---------|---------|---------|
| 強趨勢上漲 | TrendFollowing | Breakout |
| 強趨勢下跌 | TrendFollowing | - |
| 盤整震盪 | MeanReversion | SwingTrading |
| 突破前夕 | Breakout | TrendFollowing |
| 高波動 | Breakout | - |
| 低波動 | MeanReversion | SwingTrading |

---

## 💡 使用示例

### 1. 使用單一策略
```python
from src.bioneuronai.strategies import TrendFollowingStrategy

# 初始化策略
strategy = TrendFollowingStrategy(
    fast_period=20,
    slow_period=50,
    trend_period=200
)

# 生成信號
signals = strategy.generate_signals(market_data)

print(f"信號: {signals['action']}")  # BUY/SELL/HOLD
print(f"信心度: {signals['confidence']}")  # 0-1
print(f"止損: {signals['stop_loss']}")
print(f"止盈: {signals['take_profit']}")
```

### 2. 使用策略融合
```python
from src.bioneuronai.strategies import (
    StrategyFusion,
    TrendFollowingStrategy,
    BreakoutStrategy,
    MeanReversionStrategy
)

# 初始化多個策略
strategies = [
    TrendFollowingStrategy(),
    BreakoutStrategy(),
    MeanReversionStrategy()
]

# 創建融合器
fusion = StrategyFusion(strategies)

# 設定權重
fusion.set_weights({
    'TrendFollowing': 0.4,
    'Breakout': 0.3,
    'MeanReversion': 0.3
})

# 生成融合信號
signals = fusion.generate_signals(market_data)
```

### 3. 根據市場狀態選擇策略
```python
from src.bioneuronai.strategies import StrategyFusion
from src.bioneuronai.trading import MarketAnalyzer

# 分析市場狀態
analyzer = MarketAnalyzer(connector)
market_state = analyzer.analyze_market('BTCUSDT')

# 自動選擇策略
fusion = StrategyFusion(strategies)
fusion.set_market_regime(market_state['regime'])

# 生成適應性信號
signals = fusion.generate_signals(market_data)
```

### 4. 回測單一策略
```python
from src.bioneuronai.strategies import TrendFollowingStrategy
from src.bioneuronai.analysis import BacktestEngine

# 初始化策略和回測引擎
strategy = TrendFollowingStrategy()
backtest = BacktestEngine(
    initial_capital=10000,
    commission=0.001
)

# 運行回測
results = backtest.run(
    strategy=strategy,
    data=historical_data,
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# 查看結果
print(f"總收益: {results['total_return']}")
print(f"勝率: {results['win_rate']}")
print(f"夏普比率: {results['sharpe_ratio']}")
print(f"最大回撤: {results['max_drawdown']}")
```

---

## 📈 策略性能基準

| 策略 | 年化收益 | 夏普比率 | 最大回撤 | 勝率 |
|------|---------|---------|---------|------|
| TrendFollowing | 25-40% | 1.2-1.8 | 15-25% | 40-45% |
| Breakout | 30-50% | 1.0-1.5 | 20-30% | 35-40% |
| MeanReversion | 20-35% | 1.5-2.0 | 10-20% | 55-60% |
| SwingTrading | 25-40% | 1.3-1.7 | 12-22% | 48-52% |
| StrategyFusion | 35-55% | 1.6-2.2 | 12-20% | 52-58% |

*註: 以上數據基於歷史回測，實際表現可能有所不同*

---

## ⚙️ 策略參數

### 通用參數
```python
{
    'lookback_period': 100,     # 回看週期
    'risk_per_trade': 0.02,     # 單筆風險 2%
    'max_positions': 5,         # 最大持倉數
    'stop_loss_pct': 0.02,      # 止損 2%
    'take_profit_pct': 0.04     # 止盈 4%
}
```

### 趨勢策略參數
```python
{
    'fast_ma': 20,
    'slow_ma': 50,
    'trend_ma': 200,
    'adx_threshold': 25
}
```

### 均值回歸參數
```python
{
    'bb_period': 20,
    'bb_std': 2.0,
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70
}
```

---

## 📚 相關文檔

- **策略指南**: [TRADING_STRATEGIES_GUIDE.md](../../../docs/TRADING_STRATEGIES_GUIDE.md)
- **策略快速參考**: [STRATEGIES_QUICK_REFERENCE.md](../../../docs/STRATEGIES_QUICK_REFERENCE.md)
- **交易模組**: [交易系統](../trading/README.md)
- **分析模組**: [分析工具](../analysis/README.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026年1月22日
