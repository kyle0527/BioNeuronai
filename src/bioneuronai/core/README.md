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

### 3. InferenceEngine (推理引擎)

AI 模型推理引擎，支持交易決策預測。

**主要功能：**
- 模型加載與管理
- 實時推理預測
- 批量預測處理
- 模型性能監控

**使用示例：**
```python
from bioneuronai.core import InferenceEngine

# 初始化推理引擎
engine = InferenceEngine(model_path='model/my_100m_model.pth')

# 執行推理
prediction = engine.predict(features)

# 批量推理
predictions = engine.batch_predict(feature_list)
```

## 📦 導出 API

```python
from bioneuronai.core import (
    TradingEngine,         # 主交易引擎
    SelfImprovementSystem, # 自我改進系統
    InferenceEngine,       # AI 推理引擎
)
```

## 🔗 依賴關係

**內部依賴：**
- `analysis` - 市場分析服務（新聞情緒、關鍵字識別、特徵工程、市場狀態檢測）
- `data` - 數據連接器和數據庫管理
- `trading` - 交易執行和風險管理
- `strategies` - 交易策略庫
- `schemas` - 數據模型定義

**外部依賴：**
- `ccxt` - 交易所 API
- `pandas` - 數據處理
- `numpy` - 數值計算

## 🎨 架構設計

```
core/
├── trading_engine.py       # 主交易引擎
├── self_improvement.py     # 自我改進系統
├── inference_engine.py     # AI 推理引擎
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
