# BioNeuronai 風險管理系統使用手冊
> **版本**: v2.1.0  
> **更新日期**: 2026-01-22  
> **模組**: `src.bioneuronai.trading.risk_manager`


## 📑 目錄

1. 🎯 系統概述
2. 🎛️ 核心功能
3. ⚙️ 風險等級配置
4. 📚 使用範例
5. 🎯 最佳實踐
6. 🔧 故障排除
7. 📖 延伸閱讀
8. 📞 技術支持

---

## 🎯 系統概述

BioNeuronai 風險管理系統提供**企業級風險控制**功能，基於 Investopedia 等業界最佳實踐設計，包含：

### 核心特性

- ✅ **4 個風險等級**: CONSERVATIVE / MODERATE / AGGRESSIVE / HIGH_RISK
- ✅ **即時風險監控**: 自動檢測倉位、槓桿、回撤超限
- ✅ **智能倉位計算**: Kelly Criterion + 波動率調整 + 流動性約束
- ✅ **交易統計分析**: 勝率、Profit Factor、Sharpe Ratio、最大回撤
- ✅ **多維度風險評估**: VaR、Expected Shortfall、相關性分析

### 系統架構

```
RiskManager
├── 倉位計算 (Position Sizing)
│   ├── 基於風險計算
│   ├── Kelly Criterion
│   ├── 波動率調整
│   └── 流動性約束
├── 組合風險評估
│   ├── VaR 計算
│   ├── 最大回撤分析
│   └── 相關性矩陣
├── 交易檢查與記錄
│   ├── check_can_trade()  → 綜合檢查
│   ├── record_trade()     → 記錄交易
│   ├── get_risk_statistics() → 統計報告
│   └── update_balance()   → 更新餘額
└── 風險限制監控
    ├── 單筆交易風險
    ├── 每日風險總額
    ├── 槓桿限制
    └── 集中度風險
```

---

## 🎛️ 核心功能

### 1. check_can_trade() - 交易前檢查

**功能**: 綜合檢查是否可以進行交易

**檢查項目**:
1. ✅ 信號置信度 ≥ 50%
2. ✅ 回撤 ≤ 風險等級限制
3. ✅ 每日交易次數 ≤ 10 次
4. ✅ 帳戶餘額 ≥ $100
5. ✅ 無高優先級風險警報（1小時內）
6. ✅ 槓桿使用率 < 90%

**使用方式**:

```python
from src.bioneuronai.trading.risk_manager import RiskManager

risk_manager = RiskManager()

# 檢查是否可以交易
can_trade, reason = risk_manager.check_can_trade(
    signal_confidence=0.75,  # 信號置信度 75%
    account_balance=10000.0, # 帳戶餘額 $10,000
    risk_level="MODERATE"    # 風險等級：中等
)

if can_trade:
    print("✅ 可以交易")
else:
    print(f"❌ 不可交易: {reason}")
```

**回傳值**:
- `(True, "交易檢查通過")` - 可以交易
- `(False, "原因描述")` - 不可交易，附帶原因

---

### 2. record_trade() - 記錄交易

**功能**: 記錄交易信息用於統計分析和績效追蹤

**必需字段**:

```python
trade_info = {
    'symbol': 'BTCUSDT',           # 交易對
    'side': 'BUY',                 # BUY/SELL
    'size': 0.1,                   # 交易數量
    'entry_price': 50000.0,        # 進場價格
    'exit_price': 52000.0,         # 出場價格（平倉時）
    'pnl': 200.0,                  # 盈虧（平倉時）
    'timestamp': datetime.now(),   # 時間戳
    'stop_loss_distance': 0.02     # 止損距離（可選）
}

risk_manager.record_trade(trade_info)
```

**自動功能**:
- 📊 更新每日交易計數
- 📈 計算歷史回撤
- 🔔 觸發風險警報（如有）

---

### 3. get_risk_statistics() - 獲取風險統計

**功能**: 返回完整的交易統計和風險指標

**統計指標**:

| 指標 | 說明 | 計算公式 |
|------|------|----------|
| **win_rate** | 勝率 | 獲利交易數 / 總交易數 |
| **avg_profit** | 平均盈利 | 總盈利 / 獲利交易數 |
| **avg_loss** | 平均虧損 | 總虧損 / 虧損交易數 |
| **profit_factor** | 盈虧比 | 總盈利 / 總虧損 |
| **max_drawdown** | 最大回撤 | (峰值餘額 - 最低餘額) / 峰值餘額 |
| **sharpe_ratio** | 夏普比率 | (平均回報 - 無風險利率) / 標準差 |
| **avg_risk_reward** | 平均風險回報比 | 平均盈利 / 平均虧損 |

**使用範例**:

```python
stats = risk_manager.get_risk_statistics()

print(f"總交易數: {stats['total_trades']}")
print(f"勝率: {stats['win_rate']:.1%}")
print(f"Profit Factor: {stats['profit_factor']}")
print(f"最大回撤: {stats['max_drawdown']:.2%}")
print(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
print(f"淨盈利: ${stats['net_profit']:,.2f}")
```

**輸出範例**:

```json
{
  "total_trades": 150,
  "closed_trades": 142,
  "open_positions": 8,
  "win_rate": 0.6268,
  "winning_trades": 89,
  "losing_trades": 53,
  "avg_profit": 187.32,
  "avg_loss": 95.47,
  "profit_factor": 2.08,
  "max_drawdown": 0.1245,
  "sharpe_ratio": 1.87,
  "avg_risk_reward": 1.96,
  "total_profit": 16671.48,
  "total_loss": 5060.91,
  "net_profit": 11610.57,
  "daily_trade_count": 3,
  "current_balance": 21610.57,
  "peak_balance": 22500.00
}
```

---

### 4. update_balance() - 更新餘額

**功能**: 更新帳戶餘額並自動計算回撤和峰值

**使用方式**:

```python
# 初始餘額
risk_manager.update_balance(10000.0)

# 交易後更新
risk_manager.update_balance(10250.0)  # 盈利 $250

# 虧損後更新
risk_manager.update_balance(9980.0)   # 虧損 $270
```

**自動功能**:
- 📈 更新峰值餘額（歷史最高）
- 📉 計算當前回撤百分比
- 🚨 檢測是否超過風險等級回撤限制
- 📝 記錄歷史回撤數據

**警報觸發**:

```
當回撤超過風險等級限制時：
⚠️ 當前回撤: 12.45% ($1,245.00)
🚨 回撤達到 MODERATE 等級限制: 12.45% > 15.00%
建議: 考慮停止交易或降低倉位
```

---

## ⚙️ 風險等級配置

### 風險參數對照表

| 參數 | CONSERVATIVE<br/>(保守) | MODERATE<br/>(中等) | AGGRESSIVE<br/>(積極) | HIGH_RISK<br/>(高風險) |
|------|------------------------|---------------------|---------------------|----------------------|
| **單筆交易風險** | 1% | 2% | 3% | 5% |
| **每日風險上限** | 3% | 5% | 8% | 15% |
| **組合風險上限** | 15% | 25% | 40% | 60% |
| **最大回撤限制** | 10% | 15% | 25% | 40% |
| **最大相關性** | 60% | 70% | 80% | 90% |
| **最大槓桿** | 2x | 3x | 5x | 10x |
| **倉位集中度** | 20% | 25% | 30% | 40% |
| **行業集中度** | 40% | 50% | 60% | 80% |

### 選擇風險等級指南

#### 🟢 CONSERVATIVE（保守）- 適合：
- 📖 新手交易者
- 💰 退休金或長期資金
- 😌 低風險承受能力
- **預期年化回報**: 8-15%
- **預期最大回撤**: < 10%

#### 🟡 MODERATE（中等）- 適合：
- 📚 有經驗的交易者
- 💵 可承受中等波動
- 📊 平衡風險與收益
- **預期年化回報**: 15-30%
- **預期最大回撤**: 10-15%

#### 🟠 AGGRESSIVE（積極）- 適合：
- 🎯 專業交易者
- 💸 高風險承受能力
- 🚀 追求高回報
- **預期年化回報**: 30-60%
- **預期最大回撤**: 15-25%

#### 🔴 HIGH_RISK（高風險）- 適合：
- ⚡ 資深專業交易者
- 🎰 可承受極高風險
- 🔥 極端市場條件
- **預期年化回報**: 60%+
- **預期最大回撤**: 25-40%

---

## 📚 使用範例

### 完整交易流程範例

```python
from src.bioneuronai.trading.risk_manager import RiskManager
from datetime import datetime

# 1. 初始化風險管理器
risk_manager = RiskManager()

# 2. 設置初始餘額
initial_balance = 10000.0
risk_manager.update_balance(initial_balance)
print(f"💰 初始餘額: ${initial_balance:,.2f}")

# 3. 交易前檢查
signal_confidence = 0.78
can_trade, reason = risk_manager.check_can_trade(
    signal_confidence=signal_confidence,
    account_balance=risk_manager.current_balance,
    risk_level="MODERATE"
)

if not can_trade:
    print(f"❌ 交易檢查失敗: {reason}")
    exit()

print(f"✅ 交易檢查通過 (置信度: {signal_confidence:.1%})")

# 4. 計算倉位大小
entry_price = 50000.0
stop_loss_price = 49000.0  # 2% 止損

position_sizing = await risk_manager.calculate_position_size(
    symbol="BTCUSDT",
    entry_price=entry_price,
    stop_loss_price=stop_loss_price,
    account_balance=risk_manager.current_balance,
    risk_level="MODERATE"
)

print(f"📊 建議倉位: {position_sizing.recommended_size:.4f} BTC")
print(f"💵 風險金額: ${position_sizing.risk_amount:.2f}")
print(f"🎯 風險回報比: 1:{position_sizing.risk_reward_ratio:.1f}")

# 5. 執行交易（模擬）
print("\n🔵 開倉交易...")
trade_entry = {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'size': position_sizing.recommended_size,
    'entry_price': entry_price,
    'timestamp': datetime.now()
}
risk_manager.record_trade(trade_entry)

# 6. 平倉交易（模擬盈利）
exit_price = 52000.0  # 上漲 4%
pnl = position_sizing.recommended_size * (exit_price - entry_price)

print(f"\n🟢 平倉交易... (價格: ${exit_price:,.2f})")
trade_exit = {
    'symbol': 'BTCUSDT',
    'side': 'SELL',
    'size': position_sizing.recommended_size,
    'entry_price': entry_price,
    'exit_price': exit_price,
    'pnl': pnl,
    'timestamp': datetime.now(),
    'stop_loss_distance': 0.02
}
risk_manager.record_trade(trade_exit)

# 7. 更新餘額
new_balance = risk_manager.current_balance + pnl
risk_manager.update_balance(new_balance)

print(f"\n💰 更新後餘額: ${new_balance:,.2f}")
print(f"📈 本次盈虧: ${pnl:,.2f} ({pnl/initial_balance:.2%})")

# 8. 查看統計數據
stats = risk_manager.get_risk_statistics()
print("\n📊 風險統計報告:")
print(f"  總交易數: {stats['total_trades']}")
print(f"  勝率: {stats['win_rate']:.1%}")
print(f"  Profit Factor: {stats['profit_factor']}")
print(f"  淨盈利: ${stats['net_profit']:,.2f}")
```

### 批量交易監控範例

```python
# 監控多個交易的風險
trades = [
    {'symbol': 'BTCUSDT', 'pnl': 250.0},
    {'symbol': 'ETHUSDT', 'pnl': -120.0},
    {'symbol': 'SOLUSDT', 'pnl': 180.0},
]

for trade in trades:
    risk_manager.record_trade(trade)

    # 每次交易後檢查風險
    can_continue, reason = risk_manager.check_can_trade(
        signal_confidence=0.7,
        account_balance=risk_manager.current_balance,
        risk_level="MODERATE"
    )

    if not can_continue:
        print(f"🛑 停止交易: {reason}")
        break
```

---

## 🎯 最佳實踐

### 1. 風險管理原則

#### 📌 1% 規則
**每筆交易風險不超過帳戶的 1-2%**

```python
# ✅ 正確做法
account_balance = 10000
max_risk_per_trade = account_balance * 0.01  # $100
```

#### 📌 回撤管理
**達到最大回撤 50% 時強制休息**

```python
stats = risk_manager.get_risk_statistics()
if stats['max_drawdown'] > 0.075:  # 7.5% (50% of 15% limit)
    print("⚠️ 接近回撤限制，降低倉位或暫停交易")
```

#### 📌 Kelly Criterion
**實際倉位 = Kelly 倉位 × 0.5** (保守係數)

```python
# Kelly Criterion 已內建在 calculate_position_size()
# 自動乘以 0.5 安全係數
```

### 2. 監控與警報

#### 設置自動風險檢查

```python
# 每小時檢查一次風險狀態
import schedule

def risk_health_check():
    stats = risk_manager.get_risk_statistics()

    if stats['max_drawdown'] > 0.10:
        send_alert("⚠️ 回撤警報: " + stats['max_drawdown'])

    if stats['profit_factor'] < 1.5:
        send_alert("📉 Profit Factor 過低: " + stats['profit_factor'])

schedule.every(1).hours.do(risk_health_check)
```

### 3. 回測驗證

```python
# 使用歷史數據驗證風險參數
from src.bioneuronai.historical_data_loader import HistoricalDataLoader

loader = HistoricalDataLoader()
df = loader.load_klines("BTCUSDT", "1h", "um", year_month="2024-01")

# 模擬交易並記錄
for row in df.itertuples():
    # 執行交易邏輯
    # risk_manager.record_trade(...)
    pass

# 檢查回測結果
stats = risk_manager.get_risk_statistics()
print(f"回測勝率: {stats['win_rate']:.1%}")
print(f"回測 Sharpe: {stats['sharpe_ratio']:.2f}")
```

---

## 🔧 故障排除

### 常見問題

#### ❓ 問題 1: "無法存取類別 RiskManager 的屬性 check_can_trade"

**原因**: Pylance 未重新加載模組

**解決方案**:
```bash
# 重啟 Python 環境
# VSCode: Ctrl+Shift+P -> "Python: Restart Language Server"

# 或強制重新導入
import importlib
import src.bioneuronai.trading.risk_manager as rm_module
importlib.reload(rm_module)
```

#### ❓ 問題 2: 勝率計算為 0

**原因**: 沒有已平倉交易（缺少 `pnl` 字段）

**解決方案**:
```python
# 確保平倉交易包含 pnl
trade_info = {
    'symbol': 'BTCUSDT',
    'pnl': 250.0,  # ✅ 必須包含此字段
    # ... 其他字段
}
```

#### ❓ 問題 3: check_can_trade() 總是返回 False

**檢查清單**:
```python
# 1. 檢查餘額
print(f"餘額: ${risk_manager.current_balance}")

# 2. 檢查回撤
print(f"峰值: ${risk_manager.peak_balance}")
print(f"回撤: {(risk_manager.peak_balance - risk_manager.current_balance) / risk_manager.peak_balance:.2%}")

# 3. 檢查警報
alerts = [a for a in risk_manager.risk_alerts 
          if (datetime.now() - a.timestamp).seconds < 3600]
print(f"活躍警報: {len(alerts)}")

# 4. 檢查每日交易數
print(f"今日交易數: {risk_manager.daily_trade_count}")
```

---

## 📖 延伸閱讀

### 參考資料

1. **Investopedia - Risk Management Techniques**
   - 1% Rule
   - Stop-Loss 設置
   - Position Sizing

2. **Kelly Criterion**
   - 最優倉位計算
   - 保守係數應用

3. **VaR (Value at Risk)**
   - 95%/99% 置信區間
   - Expected Shortfall

4. **Sharpe Ratio**
   - 風險調整後收益
   - 基準比較

### 相關文檔

- [CRYPTO_TRADING_README.md](CRYPTO_TRADING_README.md) - 加密貨幣交易完整指南
- [CODE_FIX_GUIDE.md](docs/CODE_FIX_GUIDE.md) - 代碼開發規範
- [BINANCE_API_IMPLEMENTATION.md](BINANCE_API_IMPLEMENTATION.md) - API 實現文檔

---

## 📞 技術支持

遇到問題？請檢查：

1. ✅ [GitHub Issues](https://github.com/kyle0527/BioNeuronai/issues)
2. ✅ [PROJECT_STATUS_ANALYSIS.md](PROJECT_STATUS_ANALYSIS.md)
3. ✅ [常見問題故障排除](#故障排除)

---

**最後更新**: 2026-01-22  
**作者**: BioNeuronai Development Team  
**版本**: v2.1.0
