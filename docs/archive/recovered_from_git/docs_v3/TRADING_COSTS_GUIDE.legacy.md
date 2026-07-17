# 💰 交易成本配置系統

## 📑 目錄

1. 🎯 為什麼需要這個系統？
2. 📊 包含的成本項目
3. 🛠️ 使用方式
4. 📈 實際案例分析
5. 💡 AI 應該如何使用這些數據？
6. ⚠️ 重要注意事項
7. 🔗 相關文檔
8. 📊 快速參考表

---

## 🎯 為什麼需要這個系統？

### 問題
之前 AI 分析交易時，常常忽略以下成本：
- ❌ 只看價格漲跌，沒考慮手續費
- ❌ 忽略資金費率（每8小時扣一次）
- ❌ 不知道價差和滑點影響
- ❌ 無法計算真實盈虧平衡點

### 解決方案 ✅
將所有固定成本寫入配置文件，AI 可以：
- ✅ 精確計算每筆交易的總成本
- ✅ 自動計算盈虧平衡價格
- ✅ 建議合理的止盈止損點位
- ✅ 評估交易是否值得執行

---

## 📊 包含的成本項目

### 1️⃣ 交易手續費（Trading Fees）
```python
標準用戶（VIP 0）:
- Maker（掛單）: 0.02%
- Taker（吃單）: 0.05%

VIP 用戶（基於30日交易量）:
- VIP 1-9: 0.016% - 0.00% (Maker)
- VIP 1-9: 0.040% - 0.017% (Taker)

BNB 折扣: -10%（如果使用 BNB 支付）
```

### 2️⃣ 資金費率（Funding Rate）
```python
結算時間: 每8小時一次（UTC 00:00, 08:00, 16:00）

典型費率:
- BTC: ±0.01%
- ETH: ±0.012%
- 山寨幣: ±0.02%

極端情況: 最高 ±0.75%

計算方式:
做多 + 正費率 = 支付費用
做空 + 正費率 = 收取費用
```

### 3️⃣ 價差成本（Spread）
```python
BTC: 0.01% (1 基點)
ETH: 0.015% (1.5 基點)
主流幣: 0.02% (2 基點)
小幣種: 0.05% (5 基點)

注意: 進出場各付一次，共 2 倍
```

### 4️⃣ 滑點成本（Slippage）
```python
根據訂單大小:
- < $100K: 0.01% - 0.1%
- $100K - $500K: 1.5倍
- > $1M: 3倍

根據市場狀況:
- 正常: 1倍
- 波動: 2倍
- 極端: 5倍
```

---

## 🛠️ 使用方式

### 方法1：在策略中直接使用

```python
from config.trading_costs import TradingCostCalculator

# 創建計算器
calc = TradingCostCalculator(
    vip_level=0,      # VIP 等級
    use_bnb=True      # 使用 BNB 折扣
)

# 計算交易成本
costs = calc.calculate_entry_exit_costs(
    position_size_usd=1000,
    entry_price=50000,
    exit_price=51000,
    symbol="BTCUSDT",
    holding_hours=24
)

print(f"總成本: ${costs['total_cost']}")
print(f"成本佔比: {costs['cost_percentage']}%")
print(f"盈虧平衡: ${costs['breakeven_price']}")
```

### 方法2：計算最小獲利目標

```python
# 計算至少需要多少漲幅才有1%淨利潤
min_target = calc.get_minimum_profit_target(
    position_size_usd=1000,
    symbol="BTCUSDT",
    desired_profit_margin=0.01  # 期望1%淨利潤
)

print(f"最小獲利目標: {min_target}%")
# 輸出: 最小獲利目標: 1.07%
```

### 方法3：在 AI 交易決策中整合

```python
# 在 trading_engine.py 中
from config.trading_costs import TradingCostCalculator

class TradingEngine:
    def __init__(self):
        self.cost_calculator = TradingCostCalculator(
            vip_level=0,
            use_bnb=True
        )

    def analyze_trade_opportunity(self, signal):
        """分析交易機會（考慮成本）"""

        # 1. 計算預期獲利
        expected_profit_pct = signal['target_price'] / signal['entry_price'] - 1

        # 2. 計算交易成本
        costs = self.cost_calculator.calculate_entry_exit_costs(
            position_size_usd=signal['position_size'],
            entry_price=signal['entry_price'],
            exit_price=signal['target_price'],
            symbol=signal['symbol'],
            holding_hours=signal['expected_duration_hours']
        )

        # 3. 計算淨利潤
        gross_profit = signal['position_size'] * expected_profit_pct
        net_profit = gross_profit - costs['total_cost']
        net_profit_pct = (net_profit / signal['position_size']) * 100

        # 4. 決策
        if net_profit_pct < 1.0:  # 淨利潤低於1%
            return {
                "action": "REJECT",
                "reason": f"淨利潤太低 ({net_profit_pct:.2f}%)，不值得交易",
                "costs_breakdown": costs
            }
        else:
            return {
                "action": "APPROVE",
                "expected_net_profit": net_profit,
                "expected_net_profit_pct": net_profit_pct,
                "breakeven_price": costs['breakeven_price'],
                "costs_breakdown": costs
            }
```

---

## 📈 實際案例分析

### 案例1: BTC 短線交易（2%目標）

```
倉位: $1,000
入場: $50,000
目標: $51,000 (+2%)
持倉: 24小時

成本分析:
✅ 開倉手續費: $0.45 (0.05% taker)
✅ 平倉手續費: $0.51 (0.05% taker)
✅ 資金費用: $0.30 (0.01% × 3次)
✅ 價差成本: $0.20 (0.01% × 2)
✅ 滑點成本: $0.20 (0.01% × 2)
───────────────────
總成本: $1.66 (0.17%)

毛利潤: $20.00
淨利潤: $18.34
淨利潤率: 1.83% ✅ 值得交易
```

### 案例2: ETH 超短線（0.5%目標）❌

```
倉位: $5,000
入場: $3,000
目標: $3,015 (+0.5%)
持倉: 2小時

成本分析:
開倉手續費: $2.25
平倉手續費: $2.26
資金費用: $0.00 (未跨結算時間)
價差成本: $1.50
滑點成本: $1.00
───────────────────
總成本: $7.01 (0.14%)

毛利潤: $25.00
淨利潤: $17.99
淨利潤率: 0.36% ⚠️ 風險高

結論: 目標太小，扣除成本後利潤不足
```

### 案例3: 山寨幣博取10%

```
倉位: $500
入場: $1.00
目標: $1.10 (+10%)
持倉: 48小時

成本分析:
開倉手續費: $0.25
平倉手續費: $0.28
資金費用: $0.60 (0.02% × 6次)
價差成本: $0.50 (0.05% × 2)
滑點成本: $0.50 (0.05% × 2)
───────────────────
總成本: $2.13 (0.43%)

毛利潤: $50.00
淨利潤: $47.87
淨利潤率: 9.57% ✅✅ 高獲利交易
```

---

## 💡 AI 應該如何使用這些數據？

### 在交易信號生成時

```python
# BAD ❌ - 只看技術指標
if rsi < 30:
    return "BUY"

# GOOD ✅ - 考慮成本的完整分析
if rsi < 30:
    # 計算如果現在買，目標價是多少
    costs = calc.calculate_entry_exit_costs(...)

    # 目標價 = 入場價 × (1 + 最小獲利目標)
    min_target_pct = costs['cost_percentage'] / 100 + 0.015  # +1.5%淨利潤
    target_price = entry_price * (1 + min_target_pct)

    # 檢查是否有足夠上漲空間
    resistance_price = get_next_resistance()
    if target_price < resistance_price:
        return "BUY"
    else:
        return "WAIT"  # 空間不足，等更好的機會
```

### 在風險管理中

```python
# 動態調整止盈止損
def calculate_stop_levels(entry_price, position_size, symbol):
    costs = calc.calculate_entry_exit_costs(
        position_size_usd=position_size,
        entry_price=entry_price,
        exit_price=entry_price,  # 假設平價出場
        symbol=symbol,
        holding_hours=24
    )

    # 止損: -2%（固定）
    stop_loss = entry_price * 0.98

    # 止盈: 至少要覆蓋成本 + 2% 淨利潤
    min_profit_pct = costs['cost_percentage'] / 100 + 0.02
    take_profit = entry_price * (1 + min_profit_pct)

    return {
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_reward_ratio": min_profit_pct / 0.02  # 應該 > 1.5
    }
```

### 在績效分析中

```python
# 計算真實回報率（扣除所有成本）
def calculate_true_return(trade_history):
    total_pnl = 0

    for trade in trade_history:
        # 計算毛利潤
        gross_pnl = (trade['exit_price'] - trade['entry_price']) * trade['quantity']

        # 計算成本
        costs = calc.calculate_entry_exit_costs(
            position_size_usd=trade['position_value'],
            entry_price=trade['entry_price'],
            exit_price=trade['exit_price'],
            symbol=trade['symbol'],
            holding_hours=trade['duration_hours']
        )

        # 淨利潤
        net_pnl = gross_pnl - costs['total_cost']
        total_pnl += net_pnl

    return total_pnl
```

---

## ⚠️ 重要注意事項

### 1. 費率可能變化
```python
# 建議每季度檢查一次
LAST_UPDATED = "2026-01-19"

# 如果幣安調整費率結構，需要更新:
# - VIP_FEES
# - STANDARD_FEES
# - FUNDING_RATE_REFERENCE
```

### 2. 資金費率是動態的
```python
# 配置文件中的是「平均值」
# 實際交易時應該查詢實時費率:

import ccxt

exchange = ccxt.binance()
funding_rate = exchange.fetch_funding_rate('BTC/USDT:USDT')
print(funding_rate['fundingRate'])  # 當前實時費率
```

### 3. 滑點取決於訂單大小
```python
# 大單會有更多滑點
if position_size > 100000:
    # 考慮分批進場
    # 或使用 TWAP/VWAP 算法
```

---

## 🔗 相關文檔

- [交易配置](./trading_config.py) - 一般交易參數
- [10步驟交易計劃](../docs/TRADING_PLAN_10_STEPS.md) - 完整交易流程
- [交易 SOP](../docs/CRYPTO_TRADING_SOP.md) - 標準作業流程

---

## 📊 快速參考表

| 成本項目 | 標準用戶 | VIP 用戶 | 備註 |
|---------|---------|---------|------|
| 開倉手續費 | 0.05% | 0.02-0.04% | Taker |
| 平倉手續費 | 0.05% | 0.02-0.04% | Taker |
| 資金費率/8h | 0.01% | 0.01% | 做多付費 |
| 價差成本 | 0.01% | 0.01% | BTC |
| 滑點成本 | 0.01% | 0.01% | 小單 |
| **總計/往返** | **0.22%** | **0.15%** | BTC 24h |

**結論**: 至少需要 **0.25% - 0.30%** 的價格變動才能覆蓋成本！
