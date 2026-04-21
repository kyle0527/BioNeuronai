# Core 核心模組

**路徑**: `src/bioneuronai/core/`  
**版本**: v2.1  
**更新日期**: 2026-04-20
**架構層級**: Layer 1 — 核心引擎層

---

## 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [核心組件](#核心組件)
4. [導出 API](#導出-api)
5. [依賴關係](#依賴關係)
6. [使用示例](#使用示例)
7. [配置說明](#配置說明)
8. [注意事項](#注意事項)
9. [性能指標](#性能指標)
10. [相關文檔](#相關文檔)

---

## 模組概述

Core 模組是 BioNeuronai 的中樞神經，承上啟下地協調數據層、策略層與交易執行層。它包含三大子系統：交易引擎、AI 推理管線與基因演算法進化系統。

### 模組職責
- ✅ 主交易引擎（策略執行 + 風險管理 + 訂單管理）
- ✅ AI 推理管線（模型載入 → 特徵工程 → 預測 → 訊號解讀）
- ✅ 基因演算法自我進化系統（族群管理 + 淘汰 + 交配突變）
- ✅ 新聞情緒與市場微結構整合

---

## 架構總覽

```
src/bioneuronai/core/
├── __init__.py            # 模組入口，匯出 11 個符號 (53 行)
├── trading_engine.py      # 主交易引擎 (1,724 行)
├── inference_engine.py    # AI 推理管線 (1,437 行)
└── self_improvement.py    # 基因演算法進化系統 (955 行)
                             ─────────
                             合計 4,169 行
```

---

## 核心組件

### 1. TradingEngine — 主交易引擎 (1,724 行)

系統最核心的交易執行模組，整合策略信號、風險控制、訂單管理與新聞情緒。

**主要類**: `TradingEngine` · `Position` (dataclass)

**核心能力**:
- 策略選擇 (`StrategySelector`) 與融合 (`AIStrategyFusion`) 信號接收與執行
- 實時市場數據處理（K 線、訂單簿）
- 自動風險管理（止損 / 止盈 / 爆倉防護）
- 新聞情緒即時整合（`CryptoNewsAnalyzer`）
- RAG 事件上下文整合（`NewsAdapter.get_event_context()`）
- 市場微結構分析（`MarketMicrostructure`）
- 平倉後策略權重更新：`notify_trade_closed(strategy_name, realized_pnl, entry_price, stop_loss_price)`

**整合組件**: `StrategySelector` · `AIStrategyFusion` · `NewsAdapter` · `BinanceFuturesConnector` · `DatabaseManager` · `RiskManager` · `RegimeAnalysis`

---

### 2. InferenceEngine — AI 推理管線 (1,437 行)

完整的 AI 推理管線，從原始市場數據到可執行交易訊號的端到端處理。

**主要類**:
- `ModelLoader` — 模型載入管理（支援 PyTorch .pth）
- `FeaturePipeline` — 特徵工程處理管線
- `Predictor` — 模型推理預測器
- `SignalInterpreter` — 預測結果→交易訊號轉譯
- `InferenceEngine` — 統一推理引擎
- `TradingSignal` (dataclass) — 交易訊號
- `SignalType` (Enum) — 7 種訊號類型
- `RiskLevel` (Enum) — 風險等級

**推理流程**:
```
原始數據 → FeaturePipeline → Predictor → SignalInterpreter → TradingSignal
                                  ↑
                             ModelLoader (PyTorch)
```

**工廠函式**: `create_inference_engine(model_name="my_100m_model", min_confidence=0.5)`

---

### 3. SelfImprovementSystem — 基因演算法進化系統 (955 行)

以遺傳演算法實現的策略「養蠱場」，負責核心層的自我改進能力。

**主要類**: `SelfImprovementSystem` · `StrategyGene` (dataclass)

**核心機制**:

| 階段 | 說明 |
|------|------|
| 族群管理 | 維護策略基因族群，每個 `StrategyGene` 包含完整策略參數 |
| 每日回測 | 對族群進行歷史回測，計算適應度 |
| 淘汰 | 移除適應度最低的 20% 個體 |
| 繁衍 | 最優 20% 個體進行交配 + 隨機突變 |
| 多樣性 | 維持基因多樣性，防止早熟收斂 |

**進化目標**: 最大化 Sharpe Ratio · 最小化 Max Drawdown · 穩定勝率

> 補充：策略層的 `StrategyArena` / `StrategyPortfolioOptimizer` 現在已改接正式 replay。  
> Core 內的 `SelfImprovementSystem` 仍屬獨立自我改進子系統，不等同於策略層的正式競爭主線。

---

## 導出 API

```python
from bioneuronai.core import (
    # 交易引擎
    TradingEngine,           # 主交易引擎

    # 自我進化
    SelfImprovementSystem,   # 基因演算法進化系統

    # AI 推理管線
    InferenceEngine,         # 統一推理引擎
    ModelLoader,             # 模型載入器
    FeaturePipeline,         # 特徵處理管線
    Predictor,               # 預測器
    SignalInterpreter,       # 訊號解讀器

    # 數據類型
    TradingSignal,           # 交易訊號 (dataclass)
    SignalType,              # 訊號類型 (Enum: 7種)
    RiskLevel,               # 風險等級 (Enum)

    # 工廠函式
    create_inference_engine,  # 快速建立推理引擎
)
```

---

## 依賴關係

**內部依賴 (下游)**:

| 模組 | 用途 |
|------|------|
| `data` | `BinanceFuturesConnector` · `DatabaseManager` |
| `strategies` | `StrategySelector` · `AIStrategyFusion` · 各策略類 |
| `analysis` | `CryptoNewsAnalyzer` · `MarketMicrostructure` · `RegimeAnalysis` |
| `risk_management` | `RiskManager` · `RiskParameters` |
| `schemas` | 數據模型定義 |

**外部依賴**:
- `torch` — PyTorch 深度學習框架
- `numpy` — 數值計算
- `pandas` — 數據處理

---

## 使用示例

### 交易引擎
```python
from bioneuronai.core import TradingEngine

engine = TradingEngine(testnet=True, enable_ai_model=False)

# 開始 WebSocket 監控（每次 ticker 更新自動呼叫策略管線）
engine.start_monitoring("BTCUSDT")

# 手動產生交易信號
signal = engine.generate_trading_signal(
    symbol="BTCUSDT",
    current_price=50000.0,
    klines=klines,
)
if signal:
    engine.execute_trade(signal)

# 平倉後更新策略權重（實際損益 → AI Fusion 學習）
engine.notify_trade_closed(
    strategy_name="trend_following",
    realized_pnl=85.0,
    entry_price=49800.0,
    stop_loss_price=49200.0,
)
```

### AI 推理
```python
from bioneuronai.core import create_inference_engine

engine = create_inference_engine(model_name="my_100m_model")
signal = engine.predict(
    symbol="BTCUSDT",
    current_price=50000.0,
    klines=klines,
)
print(f"訊號: {signal.signal_type}, 信心: {signal.confidence}")
```

### 基因演算法進化
```python
from bioneuronai.core import SelfImprovementSystem

improver = SelfImprovementSystem()
improver.initialize()
result = improver.evolve_once(market_data)
best_genes = improver.get_best_strategies(top_n=5)
```

---

## 配置說明

核心配置位於 `config/trading_config.py`：

```python
TRADING_CONFIG = {
    "max_position_size": 0.1,   # 最大倉位比例
    "risk_per_trade": 0.02,     # 每筆交易風險
    "max_daily_trades": 10,     # 每日最大交易次數
}
```

進化系統預設存儲: `data/bioneuronai/evolution/`

---

## 注意事項

1. **風險警告**: `TradingEngine` 可執行真實交易，請先在 testnet 驗證
2. **API 密鑰**: 需配置有效的 Binance API 密鑰（環境變量存儲）
3. **模型文件**: 推理引擎需要 PyTorch `.pth` 模型檔案
4. **遇錯即停**: 系統遵循 Fail Fast 原則，不使用模擬數據降級

---

## 性能指標

| 指標 | 目標 |
|------|------|
| 交易執行延遲 | < 100ms |
| 策略計算時間 | < 50ms |
| 風險檢查時間 | < 10ms |
| 並發能力 | 多幣對同時交易 |

---

## 相關文檔

- **策略進化指南**: [STRATEGY_EVOLUTION_GUIDE.md](../../../archived/docs_v2_1_legacy/STRATEGY_EVOLUTION_GUIDE.legacy_20260406.md)
- **風險管理手冊**: [RISK_MANAGEMENT_MANUAL.md](../../../archived/docs_v2_1_legacy/RISK_MANAGEMENT_MANUAL.legacy_20260406.md)
- **代碼修復指南**: [CODE_FIX_GUIDE.md](../../../docs/CODE_FIX_GUIDE.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 4 月 5 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
