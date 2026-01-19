# Automation 自動化模組

SOP 自動化和交易前檢查系統。

## 📋 模組概述

Automation 模組實現交易流程的自動化，包括標準操作程序（SOP）和交易前的多重檢查。

## 🎯 主要組件

### 1. SOPAutomation (SOP 自動化系統)

執行完整的 SOP 交易流程，包括環境檢查、市場分析、風險評估。

**主要功能：**
- 四步驟 SOP 流程自動化
- 交易環境全面檢查
- 市場狀態分析
- 風險參數評估
- 交易計劃生成

**SOP 流程步驟：**

1. **步驟一：環境檢查** ✅
   - API 連接測試
   - 帳戶餘額檢查
   - 網絡延遲測試
   - 系統時間同步

2. **步驟二：市場分析** 📊
   - 市場狀況評估
   - 新聞情緒分析
   - 技術指標計算
   - 流動性評估

3. **步驟三：風險評估** ⚖️
   - 持倉風險計算
   - 最大損失評估
   - 槓桿使用檢查
   - 風險限額驗證

4. **步驟四：執行準備** 🎯
   - 交易對選擇
   - 倉位大小計算
   - 止損止盈設置
   - 訂單參數準備

**使用示例：**
```python
from bioneuronai.automation import SOPAutomation

# 初始化 SOP 系統
sop = SOPAutomation()

# 執行完整 SOP 流程
result = await sop.run_full_sop()

if result["ready_to_trade"]:
    print("✅ SOP 檢查通過，可以開始交易")
    print(f"建議交易對: {result['recommended_pairs']}")
    print(f"建議倉位: {result['position_size']}")
else:
    print("❌ SOP 檢查未通過")
    print(f"原因: {result['issues']}")
```

**分步執行：**
```python
# 單獨執行各步驟
env_check = await sop.step1_environment_check()
market_check = await sop.step2_market_analysis()
risk_check = await sop.step3_risk_assessment()
exec_prep = await sop.step4_execution_preparation()
```

### 2. PreTradeAutomation (交易前檢查系統)

在執行每筆交易前進行詳細的安全和合規性檢查。

**主要功能：**
- 單筆交易前驗證
- 12 項安全檢查
- 實時市場狀況評估
- 風險限額驗證
- 新聞事件警報

**檢查項目：**

1. ✅ **基本信息驗證**
   - 交易對有效性
   - 交易方向正確性
   - 信號來源驗證

2. 💰 **資金檢查**
   - 帳戶餘額充足性
   - 保證金要求
   - 可用資金計算

3. 📊 **市場狀況**
   - 流動性評估
   - 價差檢查
   - 交易量分析
   - 異常波動檢測

4. ⚖️ **風險控制**
   - 倉位大小限制
   - 槓桿使用限制
   - 單日交易次數
   - 總風險暴露

5. 📰 **新聞事件**
   - 重大新聞檢測
   - 市場情緒評估
   - 緊急事件警報

**使用示例：**
```python
from bioneuronai.automation import PreTradeAutomation

# 初始化檢查系統
pretrade = PreTradeAutomation()

# 執行交易前檢查
check_result = await pretrade.check_before_trade(
    symbol="BTCUSDT",
    action="BUY",
    amount=0.1,
    source="AI_FUSION"
)

if check_result["approved"]:
    print("✅ 交易檢查通過")
    # 執行交易
    await execute_trade(check_result["parameters"])
else:
    print("❌ 交易被拒絕")
    print(f"原因: {check_result['rejection_reasons']}")
    print(f"建議: {check_result['suggestions']}")
```

**檢查結果結構：**
```python
{
    "approved": bool,              # 是否批准
    "confidence_score": float,     # 信心分數 (0-100)
    "checks_passed": int,          # 通過的檢查數
    "checks_failed": int,          # 失敗的檢查數
    "rejection_reasons": List[str], # 拒絕原因
    "warnings": List[str],         # 警告信息
    "suggestions": List[str],      # 改進建議
    "parameters": Dict,            # 建議參數
}
```

## 📦 導出 API

```python
from bioneuronai.automation import (
    SOPAutomation,        # SOP 自動化系統
    PreTradeAutomation,   # 交易前檢查系統
)

# 向後兼容別名
from bioneuronai.automation import (
    SOPAutomationSystem,   # 實際類名
    PreTradeCheckSystem,   # 實際類名
)
```

## 🔗 依賴關係

**內部依賴：**
- `analysis.CryptoNewsAnalyzer` - 新聞情緒分析
- `connectors.BinanceFuturesConnector` - 交易所連接
- `risk_management.RiskManager` - 風險管理

**外部依賴：**
- `ccxt` - 交易所 API
- `pandas` - 數據處理
- `asyncio` - 異步操作

## 🎨 架構設計

```
automation/
├── sop_automation.py          # SOP 自動化核心
├── pretrade_automation.py     # 交易前檢查
└── __init__.py               # 模組導出
```

## 🔧 配置說明

```python
# SOP 配置
SOP_CONFIG = {
    "min_balance_usdt": 100,        # 最小餘額
    "max_api_latency_ms": 500,      # 最大延遲
    "min_liquidity_score": 0.7,     # 最小流動性分數
    "max_spread_percent": 0.5,      # 最大價差百分比
}

# 交易前檢查配置
PRETRADE_CONFIG = {
    "max_position_size": 0.1,       # 最大倉位比例
    "max_leverage": 3,              # 最大槓桿
    "max_daily_trades": 10,         # 每日最大交易次數
    "min_confidence_score": 60,     # 最小信心分數
}
```

## 📝 使用場景

### 場景 1：每日交易前 SOP

```python
async def daily_trading_routine():
    sop = SOPAutomation()
    
    # 執行完整 SOP
    result = await sop.run_full_sop()
    
    if result["ready_to_trade"]:
        print("🎯 今日交易計劃:")
        print(f"推薦交易對: {result['recommended_pairs']}")
        print(f"市場狀況: {result['market_condition']}")
        print(f"風險評級: {result['risk_level']}")
        
        # 開始交易
        await start_trading(result)
    else:
        print("❌ 今日不適合交易")
        print(f"原因: {result['issues']}")
```

### 場景 2：單筆交易驗證

```python
async def validate_single_trade(signal):
    pretrade = PreTradeAutomation()
    
    # 執行檢查
    check = await pretrade.check_before_trade(
        symbol=signal.symbol,
        action=signal.action,
        amount=signal.amount,
        source=signal.source
    )
    
    if check["approved"]:
        print(f"✅ 交易批准 (信心度: {check['confidence_score']}%)")
        return True
    else:
        print(f"❌ 交易拒絕")
        for reason in check['rejection_reasons']:
            print(f"  • {reason}")
        return False
```

### 場景 3：自動化交易流程

```python
async def automated_trading_flow():
    sop = SOPAutomation()
    pretrade = PreTradeAutomation()
    
    # 1. 執行 SOP
    sop_result = await sop.run_full_sop()
    if not sop_result["ready_to_trade"]:
        return
    
    # 2. 生成交易信號
    signal = generate_trading_signal()
    
    # 3. 交易前檢查
    check = await pretrade.check_before_trade(
        symbol=signal.symbol,
        action=signal.action,
        amount=signal.amount,
        source=signal.source
    )
    
    # 4. 執行交易
    if check["approved"]:
        await execute_trade(check["parameters"])
```

## ⚠️ 注意事項

1. **安全第一**：所有檢查都是為了保護資金安全
2. **不要跳過**：不建議跳過任何檢查步驟
3. **配置合理**：根據風險承受能力調整配置
4. **日誌記錄**：所有檢查結果都會被記錄

## 🚀 快速開始

```python
import asyncio
from bioneuronai.automation import SOPAutomation, PreTradeAutomation

async def main():
    # 1. 每日 SOP
    sop = SOPAutomation()
    sop_result = await sop.run_full_sop()
    
    if sop_result["ready_to_trade"]:
        # 2. 交易前檢查
        pretrade = PreTradeAutomation()
        check = await pretrade.check_before_trade(
            symbol="BTCUSDT",
            action="BUY",
            amount=0.1,
            source="MANUAL"
        )
        
        if check["approved"]:
            print("✅ 可以執行交易")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📈 性能指標

- SOP 完整流程：30-60 秒
- 交易前檢查：2-5 秒
- 環境檢查：< 5 秒
- 市場分析：10-20 秒

## 🔄 版本歷史

- v2.1.0 - 模組化重構，改進檢查流程
- v2.0.0 - 新增 12 項交易前檢查
- v1.5.0 - 優化 SOP 流程
- v1.0.0 - 初始版本
