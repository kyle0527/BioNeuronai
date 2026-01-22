# BioNeuronai 交易系統

**路徑**: `src/bioneuronai/`  
**版本**: v2.3  
**更新日期**: 2026-01-22

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [子模組導航](#子模組導航)
3. [系統架構](#系統架構)
4. [快速開始](#快速開始)
5. [相關文檔](#相關文檔)

---

## 🎯 系統概述

BioNeuronai 是一個 AI 驅動的加密貨幣期貨交易系統，整合了市場分析、策略融合、風險管理和自動化執行功能。

### 系統特點
- ✅ 多策略融合交易
- ✅ AI 新聞情緒分析
- ✅ 自動風險控制
- ✅ SOP 標準流程自動化
- ✅ 實時市場分析
- ✅ SQLite 數據持久化
- ✅ RAG 知識增強

---

## 📦 子模組導航

### 核心系統
- **[core/](core/README.md)** - 交易引擎與自我改進系統
  - 主交易引擎
  - 自我改進機制

### 數據層
- **[schemas/](schemas/README.md)** - Pydantic v2 數據模型
  - 訂單、倉位、市場數據模型
  - 完整類型安全與驗證

- **[data/](data/README.md)** - 數據連接與存儲
  - Binance Futures API 連接器
  - SQLite 數據庫管理
  - 匯率服務

### 分析層
- **[analysis/](analysis/README.md)** - 市場分析工具
  - 新聞情緒分析
  - 市場關鍵字識別
  - 回測引擎

### 策略層
- **[strategies/](strategies/README.md)** - 交易策略庫
  - 趨勢跟隨策略
  - 突破交易策略
  - 均值回歸策略
  - 波段交易策略
  - 策略融合系統

### 執行層
- **[trading/](trading/README.md)** - 交易執行系統
  - 風險管理器
  - 策略選擇器
  - SOP 自動化
  - 交易前檢查
  - 市場分析器
  - 交易計劃系統

### 風險控制
- **[risk_management/](risk_management/README.md)** - 倉位管理
  - 動態倉位計算
  - 風險敞口控制

### AI 增強
- **[rag/](rag/README.md)** - 檢索增強生成系統
  - 文本嵌入 (rag/core/)
  - 知識庫管理 (rag/internal/)
  - 服務接口 (rag/services/)

---

## 🏗️ 系統架構

```
數據流向
│
├── [輸入層] 市場數據
│   ├── Binance API (data/)
│   ├── 新聞源 (analysis/)
│   └── 歷史數據
│
├── [分析層] 信號生成
│   ├── 新聞分析 (analysis/)
│   ├── 市場狀態評估 (trading/)
│   └── 策略信號 (strategies/)
│
├── [決策層] 交易決策
│   ├── 策略選擇 (trading/)
│   ├── 策略融合 (strategies/)
│   └── 風險評估 (risk_management/)
│
├── [執行層] 訂單管理
│   ├── 交易前檢查 (trading/)
│   ├── 倉位計算 (risk_management/)
│   └── 訂單執行 (data/)
│
└── [存儲層] 數據持久化
    ├── SQLite 數據庫 (data/)
    ├── JSON 備份
    └── 知識庫 (rag/)
```

---

## 🚀 快速開始

### 1. 基本導入
```python
from src.bioneuronai.core import TradingEngine
from src.bioneuronai.data import BinanceFuturesConnector
from src.bioneuronai.trading import SOPAutomation, RiskManager
from src.bioneuronai.strategies import StrategyFusion
from src.bioneuronai.analysis import CryptoNewsAnalyzer
```

### 2. 初始化系統
```python
# 連接器
connector = BinanceFuturesConnector(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)

# 核心組件
engine = TradingEngine()
sop = SOPAutomation(connector)
risk_mgr = RiskManager()
```

### 3. 執行完整流程
```python
# SOP 自動化流程
results = sop.run_full_sop(
    symbols=['BTCUSDT', 'ETHUSDT'],
    initial_capital=10000
)

# 檢查結果並執行
if results['risk_check']['passed']:
    for signal in results['signals']:
        engine.execute_trade(signal)
```

---

## 📊 系統統計

| 項目 | 數量 |
|------|------|
| Python 文件 | 102 個 |
| 代碼行數 | 40,509 行 |
| 數據模型 | 45+ 個 |
| 交易策略 | 5 種 |
| 數據庫表 | 6 張 |
| API 端點 | 20+ 個 |
| 自動化流程 | 2 套 (SOP + Pretrade) |

---

## 🔧 配置文件

系統配置位於 `config/` 目錄：

- `trading_config.py` - 交易參數配置
- `trading_costs.py` - 交易成本配置
- `market_keywords.json` - 市場關鍵字庫

---

## 📚 相關文檔

### 用戶手冊
- [用戶手冊](../../docs/USER_MANUAL.md)
- [加密貨幣交易指南](../../docs/CRYPTO_TRADING_GUIDE.md)
- [SOP 操作手冊](../../docs/CRYPTO_TRADING_SOP.md)

### 開發文檔
- [項目結構](../../PROJECT_STRUCTURE.md)
- [代碼修復指南](../../docs/CODE_FIX_GUIDE.md)
- [數據庫升級指南](../../docs/DATABASE_UPGRADE_GUIDE.md)

### 策略文檔
- [交易策略指南](../../docs/TRADING_STRATEGIES_GUIDE.md)
- [風險管理手冊](../../docs/RISK_MANAGEMENT_MANUAL.md)
- [策略快速參考](../../docs/STRATEGIES_QUICK_REFERENCE.md)

---

## ⚠️ 重要提醒

### 生產環境使用
1. **API 密鑰安全**: 使用環境變量存儲
2. **測試先行**: 先在 testnet 驗證
3. **風險控制**: 設定合理的倉位和止損
4. **監控告警**: 配置實時監控系統
5. **備份數據**: 定期備份數據庫

### 錯誤處理原則
- ❌ 不使用模擬數據降級
- ❌ 不跳過關鍵檢查步驟
- ✅ 遇錯即停 (Fail Fast)
- ✅ 完整日誌記錄

---

## 📈 性能指標

| 模組 | 平均延遲 | 可靠性 |
|------|---------|--------|
| 交易引擎 | < 100ms | 99.9% |
| 策略計算 | < 50ms | 100% |
| 風險檢查 | < 10ms | 100% |
| 新聞分析 | < 2s | 99.5% |
| 數據庫操作 | < 5ms | 99.9% |

---

## 🛣️ 開發路線圖

### v2.3 (當前)
- ✅ SQLite 數據庫整合
- ✅ SOP 自動化系統
- ✅ 交易前自動檢查
- ✅ 策略融合 v2

### v2.4 (規劃中)
- ⏳ 實時監控儀表板
- ⏳ 多交易所支持
- ⏳ 策略參數自動優化

### v3.0 (未來)
- 📋 機器學習策略
- 📋 分佈式回測
- 📋  社交交易功能

---

**最後更新**: 2026年1月22日  
**維護者**: BioNeuronai Team  
**授權**: MIT License
