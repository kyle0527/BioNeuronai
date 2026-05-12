# Core 核心模組

**路徑**: `src/bioneuronai/core/`  
**版本**: v2.2
**更新日期**: 2026-05-13
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

```text
src/bioneuronai/core/
├── __init__.py            # 模組入口，匯出 core 層主要符號
├── trading_engine.py      # 主交易引擎
├── inference_engine.py    # AI 推理管線
└── self_improvement.py    # 基因演算法進化系統
```

檔案對照：
1. [__init__.py](__init__.py)
2. [trading_engine.py](trading_engine.py)
3. [inference_engine.py](inference_engine.py)
4. [self_improvement.py](self_improvement.py)

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到檔案與主要公開類別層級。

---

## 核心組件

### 1. TradingEngine — 主交易引擎

系統最核心的交易執行模組，整合策略信號、風險控制、訂單管理與新聞情緒。

**主要類**: `TradingEngine` · `Position` (dataclass)

**策略主線模式**（由 `strategy_type` 參數指定）：

| 模式 | 說明 |
|------|---------|
| `fusion` (預設) | `StrategySelector` + `AIStrategyFusion` 分析融合正式主線 |
| `phase_router` | `TradingPhaseRouter` 將市場分成多個交易階段分別路由 |
| `rl_fusion` | RL Meta-Agent（PPO，需 stable-baselines3）後處理策略融合輸出 |

**多模態融合權重**（依市場 regime 動態調整）：

| 市場構型 | strategy | ai | news |
|---------|----------|----|------|
| `strong_trend` | 0.70 | 0.25 | 0.05 |
| `ranging` | 0.50 | 0.40 | 0.10 |
| `high_volatility` | 0.45 | 0.40 | 0.15 |
| `news_event` | 0.35 | 0.35 | 0.30 |
| `default` | 0.60 | 0.30 | 0.10 |

**核心能力**:
- 策略選擇 (`StrategySelector`) 與融合 (`AIStrategyFusion`) 信號接收與執行
- 即時市場數據處理（K 線、訂單簿）
- `paper_trading=True` 時使用主網行情 + 本地虛擬成交，不送 Binance 訂單
- 自動風險管理（止損 / 止盈 / 爆倉防護）
- 新聞情緒即時整合（`CryptoNewsAnalyzer`）
- RAG 事件上下文整合（`NewsAdapter.get_event_context()`）
- 市場微結構分析（`MarketMicrostructure`）
- 進場前 RAG 新聞檢查：`PreTradeCheckSystem`

**主要公開方法**:
- `start_monitoring(symbol)` — 啟動 WebSocket 監控迴圈
- `stop_monitoring()` — 停止監控
- `generate_trading_signal(symbol, current_price, klines, event_score, event_context)` — 產生交易信號
- `load_ai_model(model_name, warmup)` — 載入 AI 推理模型
- `enable_auto_trading()` / `disable_auto_trading()` — 自動交易開關
- `get_real_time_price(symbol)` — 取得即時報價

**整合組件**: `StrategySelector` · `TradingPhaseRouter` · `RLMetaAgent` · `AIStrategyFusion` · `NewsAdapter` · `BinanceFuturesConnector` · `DatabaseManager` · `RiskManager` · `RegimeAnalysis`

---

### 2. InferenceEngine — AI 推理管線

完整的 AI 推理管線，從原始市場數據到可執行交易訊號的端到端處理。

**主要類**:
- `ModelLoader` — 模型載入管理，支援多種路徑解析策略：
  - `MODEL_PATH` / `MODEL_DIR` 環境變數（包含 GCS URI）
  - `config/active_model.json` promote 機制（由 API `POST /api/v1/model/promote` 寫入）
  - 本地 `model/` 目錄（預設回退）
  - 自動判斷 checkpoint 類型：TinyLLM（包含數値 signal head） / 舊版 100M MLP（`bioneuronai.models.legacy`）
- `FeaturePipeline` — 1024 維特徵向量工程處理管線
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
                         ModelLoader (TinyLLM / Legacy MLP)
```

**工廠函式**: `create_inference_engine(model_name="my_100m_model", min_confidence=0.5)`

---

### 3. SelfImprovementSystem — 基因演算法進化系統
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

補充：
1. `__init__.py` 在 `torch` 或相關依賴不可用時會做優雅降級，將主要符號設為 `None`
2. `CryptoFuturesTrader = TradingEngine` 是相容 alias，但不在 `__all__` 主匯出列表中

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

# 預設使用 fusion 模式（StrategySelector + AI Fusion）
engine = TradingEngine(testnet=True, enable_ai_model=True)
engine.load_ai_model("my_100m_model", warmup=False)

# Paper-live：讀主網行情，訂單只進本地 VirtualAccount
paper_engine = TradingEngine(
    testnet=False,
    enable_ai_model=True,
    paper_trading=True,
    paper_initial_balance=10000.0,
)
paper_engine.load_ai_model("my_100m_model", warmup=False)

# 使用 PhaseRouter 策略主線
engine = TradingEngine(testnet=True, strategy_type="phase_router")

# 使用 RL Meta-Agent（需安裝 stable-baselines3 且存有 RL 模型）
engine = TradingEngine(testnet=True, strategy_type="rl_fusion")

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

1. **風險警告**: `TradingEngine` 可執行真實交易，請先用 `paper_trading=True` 或 testnet 長時間驗證。
2. **Paper-live 邊界**: `paper_trading=True` 使用正式行情，但訂單寫入本地虛擬帳戶，不送 Binance order API。
3. **API 密鑰**: testnet / live 自動交易需配置有效 Binance API key；paper-live 不需要私鑰即可讀 public market data。
4. **模型文件**: 推理引擎需要 PyTorch `.pth` 模型檔案；API/CLI 預設會嘗試載入 `my_100m_model`。
5. **遇錯即停**: 系統遵循 Fail Fast 原則，不使用假資料掩蓋錯誤。

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

- **代碼修復指南**: [CODE_FIX_GUIDE.md](../../../docs/CODE_FIX_GUIDE.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 5 月 13 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
