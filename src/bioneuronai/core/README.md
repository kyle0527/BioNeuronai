# Core 核心模組

核心交易引擎和自我改進系統。

## 📋 模組概述

Core 模組是 BioNeuronai 交易系統的核心，包含主要的交易引擎和自我改進機制。

## 🎯 主要組件

### 1. TradingEngine (交易引擎)

主要的交易執行引擎，負責策略執行、風險管理和訂單管理。

**主要功能：**
- 多策略融合交易
- 實時市場數據處理
- 自動風險管理
- 訂單執行和監控
- 新聞情緒整合

**使用示例：**
```python
from bioneuronai.core import TradingEngine

# 初始化引擎
engine = TradingEngine()

# 啟動交易
await engine.start_trading()

# 執行單次交易
signal = engine.generate_signal("BTCUSDT")
if signal:
    result = await engine.execute_trade(signal)
```

### 2. SelfImprovementSystem (自我改進系統)

基於交易結果的自適應學習和策略優化系統。

**主要功能：**
- 交易性能分析
- 策略參數優化
- 失敗案例學習
- 自動調整風險參數

**使用示例：**
```python
from bioneuronai.core import SelfImprovementSystem

# 初始化自我改進系統
improver = SelfImprovementSystem()

# 分析交易結果
await improver.analyze_trade_result(trade_result)

# 獲取優化建議
suggestions = await improver.get_improvement_suggestions()
```

## 📦 導出 API

```python
from bioneuronai.core import (
    TradingEngine,         # 主交易引擎
    SelfImprovementSystem, # 自我改進系統
)
```

## 🔗 依賴關係

**內部依賴：**
- `analysis` - 新聞分析服務
- `data_models` - 數據模型定義
- `connectors` - 交易所連接器
- `risk_management` - 風險管理
- `strategy_fusion` - 策略融合

**外部依賴：**
- `ccxt` - 交易所 API
- `pandas` - 數據處理
- `numpy` - 數值計算

## 🎨 架構設計

```
core/
├── trading_engine.py       # 主交易引擎
├── self_improvement.py     # 自我改進系統
└── __init__.py            # 模組導出
```

## 📝 相關文檔

- [交易引擎詳細文檔](../../docs/TRADING_ENGINE.md)
- [策略融合指南](../../docs/STRATEGY_FUSION.md)
- [風險管理說明](../../docs/RISK_MANAGEMENT.md)

## 🔧 配置說明

核心模組的配置位於 `config/trading_config.py`：

```python
TRADING_CONFIG = {
    "max_position_size": 0.1,    # 最大倉位比例
    "risk_per_trade": 0.02,      # 每筆交易風險
    "max_daily_trades": 10,       # 每日最大交易次數
}
```

## ⚠️ 注意事項

1. **風險警告**：TradingEngine 會執行真實交易，請先在測試環境中驗證
2. **API 密鑰**：需要配置有效的交易所 API 密鑰
3. **資金管理**：確保帳戶有足夠的餘額
4. **網絡連接**：需要穩定的網絡連接

## 🚀 快速開始

```python
import asyncio
from bioneuronai.core import TradingEngine

async def main():
    # 初始化交易引擎
    engine = TradingEngine()
    
    # 啟動監控和交易
    await engine.start_trading()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 性能指標

- 交易執行延遲：< 100ms
- 策略計算時間：< 50ms
- 風險檢查時間：< 10ms
- 支持並發交易：多幣對同時交易

## 🔄 版本歷史

- v2.1.0 - 模組化重構，改進 API 結構
- v2.0.0 - 新增自我改進系統
- v1.0.0 - 初始版本
