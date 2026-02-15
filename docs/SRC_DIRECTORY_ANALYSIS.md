# BioNeuronai src/ 目錄結構分析報告

> **版本**: v1.0  
> **生成日期**: 2026年2月15日  
> **分析範圍**: C:\D\E\BioNeuronai\src

---

## 📑 目錄

1. [目錄結構總覽](#目錄結構總覽)
2. [模組依賴關係圖](#模組依賴關係圖)
3. [Mock 機制分析](#mock-機制分析)
4. [各模組詳細說明](#各模組詳細說明)
5. [導入連結分析](#導入連結分析)
6. [檔案清單](#檔案清單)

---

## 目錄結構總覽

```
src/
├── schemas/                    # 📦 數據結構定義 (Single Source of Truth)
│   ├── alerts.py              # 告警系統數據結構
│   ├── api.py                 # API 接口數據結構
│   ├── backtesting.py         # 回測數據結構
│   ├── commands.py            # 命令系統數據結構
│   ├── database.py            # 資料庫數據結構
│   ├── enums.py               # 全局枚舉定義
│   ├── events.py              # 事件系統數據結構
│   ├── external_data.py       # 外部數據結構 (新聞、情緒等)
│   ├── market.py              # 市場數據結構
│   ├── ml_models.py           # 機器學習模型數據結構
│   ├── orders.py              # 訂單數據結構
│   ├── portfolio.py           # 投資組合數據結構
│   ├── positions.py           # 持倉數據結構
│   ├── rag.py                 # RAG 系統數據結構
│   ├── risk.py                # 風險管理數據結構
│   ├── strategy.py            # 策略數據結構
│   ├── trading.py             # 交易信號數據結構
│   ├── types.py               # 基礎類型定義
│   └── __init__.py            # 統一導出接口
│
├── bioneuronai/               # 🤖 核心交易系統
│   ├── analysis/              # 📊 市場分析模組
│   │   ├── daily_report/      # 每日報告
│   │   ├── feature_engineering.py
│   │   ├── market_regime.py   # 市場狀態識別
│   │   └── news/              # 新聞分析
│   │
│   ├── backtest/              # 🎭 回測模擬引擎 (Mock 機制)
│   │   ├── mock_connector.py  # ⭐ Mock Binance 連接器
│   │   ├── data_stream.py     # 歷史數據流生成器
│   │   ├── virtual_account.py # 虛擬帳戶模擬
│   │   ├── backtest_engine.py # 回測引擎主類
│   │   └── __init__.py
│   │
│   ├── backtesting/           # 📈 回測框架 (Phase 2 專案)
│   │   ├── historical_backtest.py  # 歷史回測引擎
│   │   ├── walk_forward.py    # Walk-Forward 測試
│   │   ├── cost_calculator.py # 交易成本計算
│   │   └── __init__.py
│   │
│   ├── core/                  # 🧠 核心交易引擎
│   │   ├── trading_engine.py  # 主交易引擎
│   │   ├── inference_engine.py # AI 推理引擎
│   │   ├── self_improvement.py # 自我改進系統
│   │   └── __init__.py
│   │
│   ├── data/                  # 💾 數據管理
│   │   ├── binance_futures.py # Binance 期貨連接器
│   │   ├── database.py        # SQLite 資料庫
│   │   ├── database_manager.py # 資料庫管理器
│   │   ├── web_data_fetcher.py # 網路數據抓取
│   │   ├── exchange_rate_service.py
│   │   └── __init__.py
│   │
│   ├── risk_management/       # ⚠️ 風險管理
│   │   ├── position_manager.py
│   │   └── __init__.py
│   │
│   ├── strategies/            # 📐 交易策略集
│   │   ├── selector/          # 策略選擇器
│   │   │   ├── core.py
│   │   │   ├── evaluator.py
│   │   │   ├── evaluator_new.py
│   │   │   ├── types.py
│   │   │   └── configs.py
│   │   ├── base_strategy.py   # 策略基類
│   │   ├── trend_following.py # 趨勢追蹤
│   │   ├── mean_reversion.py  # 均值回歸
│   │   ├── breakout_trading.py # 突破交易
│   │   ├── swing_trading.py   # 波段交易
│   │   ├── rl_fusion_agent.py # 強化學習融合代理
│   │   ├── strategy_fusion.py # 策略融合
│   │   ├── strategy_arena.py  # 策略競技場
│   │   ├── portfolio_optimizer.py
│   │   └── phase_router.py
│   │
│   ├── trading/               # 💼 交易管理
│   │   ├── market_analyzer.py # 市場分析器
│   │   ├── risk_manager.py    # 風險管理器
│   │   ├── plan_controller.py # 交易計劃控制器
│   │   ├── plan_generator.py  # 交易計劃生成器
│   │   ├── strategy_selector.py
│   │   ├── strategy_selector_v2.py
│   │   ├── pair_selector.py
│   │   ├── sop_automation.py  # SOP 自動化
│   │   ├── pretrade_automation.py
│   │   └── trading_plan_system.py
│   │
│   ├── trading_strategies.py  # 舊版策略接口
│   ├── historical_data_loader.py
│   └── __init__.py
│
├── rag/                       # 🔍 RAG 系統 (檢索增強生成)
│   ├── core/                  # 核心組件
│   │   ├── embeddings.py      # 向量嵌入服務
│   │   └── retriever.py       # 統一檢索器
│   │
│   ├── internal/              # 內部知識庫
│   │   ├── knowledge_base.py  # 知識庫管理
│   │   ├── faiss_index.py     # FAISS 向量索引
│   │   └── __init__.py
│   │
│   ├── services/              # 外部服務適配器
│   │   ├── news_adapter.py    # 新聞 API 適配器
│   │   └── __init__.py
│   │
│   ├── monitoring/            # 監控系統
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── nlp/                       # 🧪 自然語言處理模組
│   ├── training/              # 訓練相關
│   │   ├── train_with_ai_teacher.py
│   │   ├── advanced_trainer.py
│   │   ├── auto_evolve.py
│   │   ├── data_manager.py
│   │   └── view_training_history.py
│   │
│   ├── tools/                 # 工具集
│   │   └── create_model_package.py
│   │
│   ├── tiny_llm.py            # 輕量級 LLM
│   ├── rag_system.py          # RAG 系統
│   ├── bilingual_tokenizer.py # 雙語分詞器
│   ├── bpe_tokenizer.py       # BPE 分詞器
│   ├── inference_utils.py     # 推理工具
│   ├── generation_utils.py    # 生成工具
│   ├── hallucination_detection.py  # 幻覺檢測
│   ├── uncertainty_quantification.py  # 不確定性量化
│   ├── honest_generation.py   # 誠實生成
│   ├── quantization.py        # 量化
│   ├── lora.py                # LoRA 適配器
│   ├── model_export.py        # 模型導出
│   └── __init__.py
│
├── trading_data/              # 📁 交易數據存儲
├── __init__.py
└── trading_system.log         # 系統日誌

```

### 統計數據

| 類別 | 數量 |
|------|------|
| **總檔案數** | 122 個 Python 檔案 |
| **schemas 模組** | 19 個數據結構定義檔 |
| **bioneuronai 模組** | 70+ 個功能模組 |
| **rag 模組** | 8 個 RAG 組件 |
| **nlp 模組** | 15 個 NLP 工具 |
| **Mock 相關檔案** | 5 個 (含 mock_connector.py) |

---

## 模組依賴關係圖

### 核心依賴層級

```
第 0 層 (基礎)
  ↓
schemas/          ← 所有模組的 Single Source of Truth
  ├── types.py         (基礎類型)
  ├── enums.py         (全局枚舉)
  └── ...

第 1 層 (數據層)
  ↓
bioneuronai.data/  ← 數據獲取與存儲
  ├── binance_futures.py  (API 連接)
  ├── database.py         (持久化)
  └── web_data_fetcher.py (外部數據)

第 2 層 (分析層)
  ↓
bioneuronai.analysis/  ← 市場分析
bioneuronai.strategies/ ← 策略生成
rag/                   ← 知識檢索

第 3 層 (決策層)
  ↓
bioneuronai.core/  ← 交易引擎
  ├── inference_engine.py  (AI 推理)
  └── trading_engine.py    (交易執行)

第 4 層 (管理層)
  ↓
bioneuronai.trading/  ← 交易管理
bioneuronai.risk_management/ ← 風險控制

第 5 層 (測試層)
  ↓
bioneuronai.backtest/     ← Mock 模擬
bioneuronai.backtesting/  ← 回測框架
```

### 跨模組依賴關係

```
┌─────────────────────────────────────────────────────────────┐
│                    BioNeuronai 模組依賴圖                     │
└─────────────────────────────────────────────────────────────┘

schemas/  ◄───────────────────────────────────────┐
  │                                                │
  │ (所有模組都依賴 schemas)                       │
  │                                                │
  ├──► bioneuronai.data/                          │
  │      ├── binance_futures.py                   │
  │      ├── database.py                          │
  │      └── web_data_fetcher.py ──┐              │
  │                                 │              │
  ├──► bioneuronai.analysis/       │              │
  │      ├── news/  ◄──────────────┤              │
  │      └── market_regime.py      │              │
  │                                 │              │
  ├──► bioneuronai.strategies/     │              │
  │      ├── selector/              │              │
  │      ├── trend_following.py    │              │
  │      └── strategy_fusion.py ───┼─► rag/  ─────┤
  │                                 │     │        │
  ├──► bioneuronai.core/           │     │        │
  │      ├── inference_engine.py ──┤     │        │
  │      ├── trading_engine.py  ◄──┤     │        │
  │      └── self_improvement.py ──┼─────┤        │
  │                                 │     │        │
  ├──► bioneuronai.trading/        │     │        │
  │      ├── market_analyzer.py  ◄─┤     │        │
  │      ├── risk_manager.py       │     │        │
  │      └── plan_controller.py    │     │        │
  │                                 │     │        │
  └──► bioneuronai.backtest/  ◄────┴─────┴────────┘
         ├── mock_connector.py   (偽裝 binance_futures)
         ├── data_stream.py      (歷史數據流)
         └── virtual_account.py  (虛擬帳戶)

```

---

## Mock 機制分析

### 1. Mock 相關檔案清單

| 檔案路徑 | 類型 | 功能說明 |
|---------|------|----------|
| [bioneuronai/backtest/mock_connector.py](../src/bioneuronai/backtest/mock_connector.py) | **核心 Mock 類** | 完全模擬 BinanceFuturesConnector 的接口 |
| [bioneuronai/backtest/data_stream.py](../src/bioneuronai/backtest/data_stream.py) | 數據流生成器 | 將歷史數據轉換為即時數據流 (防偷看) |
| [bioneuronai/backtest/virtual_account.py](../src/bioneuronai/backtest/virtual_account.py) | 虛擬帳戶 | 模擬帳戶狀態、訂單撮合、資金變動 |
| [bioneuronai/backtest/backtest_engine.py](../src/bioneuronai/backtest/backtest_engine.py) | 回測引擎 | 統籌 Mock 系統，封裝便捷接口 |
| [bioneuronai/backtesting/historical_backtest.py](../src/bioneuronai/backtesting/historical_backtest.py) | 回測框架 | 包含 `_generate_mock_signals()` 方法 |
| [analysis/daily_report/news_sentiment.py](../src/bioneuronai/analysis/daily_report/news_sentiment.py) | 測試數據生成 | `_get_mock_news_data()` 用於測試 |
| [strategies/rl_fusion_agent.py](../src/bioneuronai/strategies/rl_fusion_agent.py) | 測試數據 | 包含 `mock_market_data`, `mock_signals` |

### 2. MockBinanceConnector 核心架構

```python
# 檔案: src/bioneuronai/backtest/mock_connector.py (766 行)

class MockBinanceConnector:
    """
    🎭 完全偽裝的 Binance 連接器
    
    設計原則:
    1. 接口完全一致 - 所有方法簽名與真實 Connector 相同
    2. 返回格式相同 - 數據結構模擬 Binance API 響應
    3. 狀態一致性 - 內部維護虛擬帳戶狀態
    4. 無縫切換 - 只需替換連接器實例
    """
    
    def __init__(self, data_dir, symbol, start_date, end_date):
        # 初始化歷史數據流
        self.data_stream = HistoricalDataStream(...)
        
        # 初始化虛擬帳戶
        self.virtual_account = VirtualAccount(...)
    
    # === 完全模擬的方法 ===
    def get_ticker_price(self, symbol: str) -> float:
        """返回當前時間點的歷史價格"""
        
    def place_order(self, symbol, side, quantity, ...) -> OrderResult:
        """模擬訂單撮合，更新虛擬帳戶"""
        
    def get_balance(self) -> Dict:
        """返回虛擬帳戶餘額"""
        
    def get_positions(self) -> List[Dict]:
        """返回虛擬持倉"""
    
    # ... 完整實現 BinanceFuturesConnector 的所有方法
```

### 3. Mock 使用場景

#### 場景 1: 直接替換連接器 (無需修改 TradingEngine)

```python
from bioneuronai.backtest import MockBinanceConnector
from bioneuronai.core.trading_engine import TradingEngine

# 創建 Mock 連接器
mock_connector = MockBinanceConnector(
    data_dir="data_downloads/binance_historical",
    symbol="BTCUSDT",
    start_date="2025-01-01",
    end_date="2025-12-31"
)

# 創建交易引擎並替換連接器
engine = TradingEngine()
engine.connector = mock_connector  # 🎭 完全無感知替換

# 正常運行，TradingEngine 完全不知道這是模擬的
engine.run()
```

#### 場景 2: 使用 BacktestEngine 封裝接口

```python
from bioneuronai.backtest import BacktestEngine, BacktestConfig

# 配置回測
config = BacktestConfig(
    symbol="BTCUSDT",
    start_date="2025-01-01",
    end_date="2025-06-30",
    initial_balance=10000.0
)

# 創建回測引擎
bt_engine = BacktestEngine(config)

# 獲取 MockConnector
connector = bt_engine.get_connector()

# 在 TradingEngine 中使用
engine = TradingEngine()
engine.connector = connector
```

#### 場景 3: self_improvement.py 中的 Mock 使用

```python
# 檔案: src/bioneuronai/core/self_improvement.py (第 615-829 行)

from bioneuronai.backtest import MockBinanceConnector

# 在自我改進回測中使用 Mock
connector = MockBinanceConnector(
    data_dir="data_downloads/binance_historical",
    symbol="BTCUSDT",
    start_date="2025-01-01",
    end_date="2025-03-31",
    initial_balance=100000.0
)

# 傳遞給評估器
market_data = {
    "connector": connector,  # ← 傳入 MockBinanceConnector 實例
    "symbol": "BTCUSDT"
}

# 運行策略評估 (完全無感知使用 Mock 數據)
result = evaluator.evaluate_strategy(strategy_config, market_data)
```

### 4. Mock 與真實環境的對比

| 特性 | BinanceFuturesConnector (真實) | MockBinanceConnector (模擬) |
|------|-------------------------------|----------------------------|
| **數據來源** | Binance API (實時) | 本地歷史數據檔案 |
| **訂單執行** | 真實撮合，資金變動 | 虛擬撮合，無實際資金 |
| **時間流動** | 真實時間 | 可加速/減速回放 |
| **網路延遲** | 真實網路延遲 | 無延遲 (本地計算) |
| **API 限制** | 有速率限制 | 無限制 |
| **成本** | 真實交易手續費 | 可配置模擬手續費 |
| **風險** | 真實資金風險 | 零風險 |
| **接口** | 完全一致 | 完全一致 ✅ |

### 5. Mock 機制關鍵代碼片段

#### 時間流控制 (data_stream.py)

```python
class HistoricalDataStream:
    """歷史數據流生成器 - 防止偷看未來"""
    
    def __init__(self, data_dir, symbol, start_date, end_date):
        self.all_data = self._load_historical_data(...)
        self.current_idx = 0  # 當前回放位置
    
    def get_current_bar(self) -> KlineBar:
        """只返回當前時間點的數據，不能偷看未來"""
        return self.all_data[self.current_idx]
    
    def advance(self):
        """前進到下一個時間點"""
        self.current_idx += 1
```

#### 訂單撮合 (virtual_account.py)

```python
class VirtualAccount:
    """虛擬帳戶 - 模擬真實帳戶行為"""
    
    def place_order(self, side, quantity, price) -> VirtualOrder:
        """模擬訂單撮合"""
        # 檢查餘額
        if not self._check_balance(quantity, price):
            return OrderResult(status="FAILED", error="Insufficient balance")
        
        # 模擬滑點
        execution_price = self._apply_slippage(price)
        
        # 計算手續費
        fee = self._calculate_fee(quantity, execution_price)
        
        # 更新帳戶狀態
        self._update_balance(side, quantity, execution_price, fee)
        
        return OrderResult(status="FILLED", ...)
```

---

## 各模組詳細說明

### 1. schemas/ - 數據結構層 (Single Source of Truth)

**作用**: 定義整個系統的所有數據結構，確保類型安全和一致性。

**核心檔案**:

| 檔案 | 行數估計 | 主要內容 |
|------|---------|---------|
| `types.py` | ~100 | 基礎類型 (Decimal, UUID, Timestamp 等) |
| `enums.py` | ~500 | 所有枚舉 (OrderSide, SignalType, RiskLevel 等) |
| `backtesting.py` | ~600 | BacktestConfig, BacktestResult, TradeRecord 等 |
| `orders.py` | ~300 | OrderRequest, OrderResult, OrderStatus 等 |
| `positions.py` | ~200 | BinancePosition, AccountBalance 等 |
| `trading.py` | ~250 | TradingSignal, SignalStrength, MarketCondition |
| `external_data.py` | ~400 | ExternalDataSnapshot, MarketSentiment 等 |

**依賴關係**:
- ✅ **被所有模組依賴** (bioneuronai, rag, nlp)
- ❌ **不依賴任何其他模組** (零依賴設計)

**導入示例**:
```python
# 其他模組導入 schemas
from schemas.backtesting import BacktestConfig, BacktestResult
from schemas.enums import OrderSide, PositionType
from schemas.external_data import ExternalDataSnapshot
```

---

### 2. bioneuronai/ - 核心交易系統

#### 2.1 bioneuronai.data/ - 數據層

**作用**: 數據獲取、存儲、管理

**核心檔案**:

| 檔案 | 功能 | 主要類 |
|------|------|--------|
| `binance_futures.py` | Binance 期貨 API 連接 | BinanceFuturesConnector |
| `database.py` | SQLite 資料庫操作 | TradingDatabase |
| `database_manager.py` | 資料庫管理器 | DatabaseManager |
| `web_data_fetcher.py` | 網路數據抓取 | WebDataFetcher |

**依賴**:
- ✅ `schemas.external_data`
- ✅ `schemas.market`

#### 2.2 bioneuronai.backtest/ - Mock 模擬引擎

**作用**: 無縫回測模擬，完全偽裝 BinanceFuturesConnector

**核心檔案**:

| 檔案 | 行數 | 功能 |
|------|------|------|
| `mock_connector.py` | **766** | ⭐ MockBinanceConnector 主類 |
| `data_stream.py` | ~300 | 歷史數據流生成器 |
| `virtual_account.py` | ~400 | 虛擬帳戶狀態管理 |
| `backtest_engine.py` | ~500 | 回測引擎統籌 |

**依賴**:
- ✅ `bioneuronai.data.binance_futures` (模擬其接口)
- ✅ `bioneuronai.trading_strategies.MarketData`

**被引用**:
- ✅ `bioneuronai.core.self_improvement` (第 616, 823 行)
- ✅ 直接在 TradingEngine 中替換

#### 2.3 bioneuronai.backtesting/ - 回測框架

**作用**: Phase 2 專案，提供完整的回測和 Walk-Forward 測試框架

**核心檔案**:

| 檔案 | 行數 | 功能 |
|------|------|------|
| `historical_backtest.py` | **629** | 歷史回測引擎 |
| `walk_forward.py` | **726** | Walk-Forward 測試 |
| `cost_calculator.py` | ~200 | 交易成本計算 |

**依賴**:
- ✅ `schemas.backtesting` (BacktestConfig, BacktestResult, TradeRecord)
- ✅ `schemas.enums` (OrderSide, PositionType)

**Mock 使用**:
- ✅ `_generate_mock_signals()` 方法 (第 572 行) - 用於生成測試信號

#### 2.4 bioneuronai.core/ - 核心引擎

**作用**: AI 推理、交易執行、自我改進

**核心檔案**:

| 檔案 | 功能 | Mock 連結 |
|------|------|-----------|
| `trading_engine.py` | 主交易引擎 | ✅ 可注入 MockConnector |
| `inference_engine.py` | AI 推理引擎 | ✅ 使用 mock_klines (第 1263 行) |
| `self_improvement.py` | 自我改進系統 | ✅ 直接使用 MockBinanceConnector (第 616-829 行) |

**依賴**:
- ✅ `bioneuronai.analysis`
- ✅ `bioneuronai.data.binance_futures`
- ✅ `bioneuronai.backtest` (用於回測)

#### 2.5 bioneuronai.strategies/ - 策略層

**作用**: 各種交易策略實現

**核心檔案**:
- `trend_following.py` - 趨勢追蹤
- `mean_reversion.py` - 均值回歸
- `breakout_trading.py` - 突破交易
- `swing_trading.py` - 波段交易
- `rl_fusion_agent.py` - 強化學習融合 (含 mock_market_data, 第 621-643 行)
- `strategy_fusion.py` - 策略融合 (使用 RAG)
- `selector/` - 策略選擇器子模組

**依賴**:
- ✅ `schemas.strategy`
- ✅ `schemas.rag` (EventContext)

#### 2.6 bioneuronai.trading/ - 交易管理層

**作用**: 交易計劃、風險管理、市場分析

**核心檔案**:
- `market_analyzer.py` - 市場分析器
- `risk_manager.py` - 風險管理器
- `plan_controller.py` - 交易計劃控制器
- `sop_automation.py` - SOP 自動化

**依賴**:
- ✅ `schemas.external_data`
- ✅ `bioneuronai.data`

---

### 3. rag/ - RAG 系統

**作用**: 檢索增強生成，提供知識檢索和語義搜索

**目錄結構**:

```
rag/
├── core/                    # 核心組件
│   ├── embeddings.py       # 向量嵌入服務 (288 行)
│   └── retriever.py        # 統一檢索器 (337 行)
│
├── internal/                # 內部知識庫
│   ├── knowledge_base.py   # 知識庫管理 (461 行)
│   └── faiss_index.py      # FAISS 向量索引
│
├── services/                # 外部服務
│   └── news_adapter.py     # 新聞 API 適配器
│
└── monitoring/              # 監控系統
    └── __init__.py
```

**依賴**:
- ✅ `schemas.rag`
- ❌ 不直接依賴 bioneuronai (獨立模組)

**被引用**:
- ✅ `bioneuronai.strategies.strategy_fusion` (第 51 行)
- ✅ `bioneuronai.analysis.news.evaluator` (第 34 行)

---

### 4. nlp/ - 自然語言處理

**作用**: 文本處理、模型訓練、推理生成

**核心檔案**:
- `tiny_llm.py` - 輕量級語言模型
- `rag_system.py` - RAG 系統
- `training/train_with_ai_teacher.py` - AI 教師訓練 (含 "mockup" 文本, 第 144 行)
- `bilingual_tokenizer.py` - 雙語分詞器
- `hallucination_detection.py` - 幻覺檢測

**依賴**:
- ✅ `bioneuronai` (透過 `from bioneuronai import load_llm`)

---

## 導入連結分析

### 從 schemas 導入 (最頻繁)

```python
# 18 處直接從 schemas 導入
from schemas.backtesting import BacktestConfig, BacktestResult
from schemas.enums import OrderSide, PositionType
from schemas.external_data import ExternalDataSnapshot, MarketSentiment
from schemas.rag import EventContext
from schemas.strategy import StrategyConfig
```

### 從 bioneuronai 導入

```python
# 內部模組互相導入
from bioneuronai.analysis.news import CryptoNewsAnalyzer
from bioneuronai.data.binance_futures import OrderResult
from bioneuronai.backtest import MockBinanceConnector  # ← Mock 相關
from bioneuronai.trading_strategies import MarketData
```

### Mock 相關導入追蹤

**MockBinanceConnector 被導入的位置**:

1. **bioneuronai/core/self_improvement.py** (第 616, 823 行)
   ```python
   from ..backtest import MockBinanceConnector
   ```

2. **bioneuronai/backtest/__init__.py** (第 27 行)
   ```python
   from .mock_connector import MockBinanceConnector
   ```

3. **任何需要回測的地方** (通過 `from bioneuronai.backtest import MockBinanceConnector`)

---

## 檔案清單

### 完整檔案列表 (按模組分類)

#### schemas/ (19 個檔案)

```
schemas/
├── alerts.py
├── api.py
├── backtesting.py         ← Phase 2 回測數據結構
├── commands.py
├── database.py
├── enums.py               ← 全局枚舉
├── events.py
├── external_data.py       ← 外部數據結構
├── market.py
├── ml_models.py
├── orders.py
├── portfolio.py
├── positions.py
├── rag.py                 ← RAG 數據結構
├── risk.py
├── strategy.py
├── trading.py
├── types.py               ← 基礎類型
└── __init__.py            ← 統一導出
```

#### bioneuronai/ (70+ 個檔案)

<details>
<summary>展開查看完整列表</summary>

```
bioneuronai/
├── analysis/
│   ├── daily_report/
│   │   └── news_sentiment.py      ← 含 _get_mock_news_data()
│   ├── feature_engineering.py
│   ├── market_regime.py
│   └── news/
│       └── evaluator.py           ← 使用 schemas.rag
│
├── backtest/                       ← ⭐ Mock 機制核心
│   ├── __init__.py
│   ├── mock_connector.py          ← ⭐⭐ MockBinanceConnector (766 行)
│   ├── data_stream.py             ← 歷史數據流
│   ├── virtual_account.py         ← 虛擬帳戶
│   └── backtest_engine.py         ← 回測引擎
│
├── backtesting/                    ← Phase 2 回測框架
│   ├── __init__.py
│   ├── historical_backtest.py     ← 歷史回測 (629 行)
│   ├── walk_forward.py            ← Walk-Forward (726 行)
│   └── cost_calculator.py         ← 交易成本計算
│
├── core/
│   ├── __init__.py
│   ├── trading_engine.py          ← 主交易引擎
│   ├── inference_engine.py        ← AI 推理 (含 mock_klines)
│   └── self_improvement.py        ← 自我改進 (使用 MockBinanceConnector)
│
├── data/
│   ├── __init__.py
│   ├── binance_futures.py         ← 真實 API 連接器 (被 Mock 模擬)
│   ├── database.py
│   ├── database_manager.py
│   ├── web_data_fetcher.py        ← 網路數據抓取
│   └── exchange_rate_service.py
│
├── risk_management/
│   ├── __init__.py
│   └── position_manager.py
│
├── strategies/
│   ├── selector/                   ← 策略選擇器子模組
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── evaluator.py
│   │   ├── evaluator_new.py
│   │   ├── types.py               ← 使用 schemas.strategy
│   │   └── configs.py
│   ├── __init__.py
│   ├── base_strategy.py
│   ├── trend_following.py
│   ├── mean_reversion.py
│   ├── breakout_trading.py
│   ├── swing_trading.py
│   ├── rl_fusion_agent.py         ← 含 mock_market_data
│   ├── strategy_fusion.py         ← 使用 schemas.rag
│   ├── strategy_arena.py
│   ├── portfolio_optimizer.py
│   └── phase_router.py
│
├── trading/
│   ├── __init__.py
│   ├── market_analyzer.py         ← 使用 schemas.external_data
│   ├── risk_manager.py
│   ├── plan_controller.py
│   ├── plan_generator.py
│   ├── strategy_selector.py
│   ├── strategy_selector_v2.py
│   ├── pair_selector.py
│   ├── sop_automation.py
│   ├── pretrade_automation.py     ← 使用 MarketData
│   └── trading_plan_system.py
│
├── __init__.py
├── trading_strategies.py          ← 舊版接口 (含 MarketData)
└── historical_data_loader.py
```

</details>

#### rag/ (8 個檔案)

```
rag/
├── core/
│   ├── embeddings.py              ← 向量嵌入服務 (288 行)
│   └── retriever.py               ← 統一檢索器 (337 行)
│
├── internal/
│   ├── __init__.py
│   ├── knowledge_base.py          ← 知識庫管理 (461 行)
│   └── faiss_index.py             ← FAISS 索引
│
├── services/
│   ├── __init__.py
│   └── news_adapter.py            ← 新聞適配器
│
├── monitoring/
│   └── __init__.py                ← 監控系統
│
└── __init__.py
```

#### nlp/ (15 個檔案)

```
nlp/
├── training/
│   ├── train_with_ai_teacher.py   ← 含 "mockup" 文本
│   ├── advanced_trainer.py
│   ├── auto_evolve.py
│   ├── data_manager.py
│   └── view_training_history.py
│
├── tools/
│   └── create_model_package.py
│
├── __init__.py
├── tiny_llm.py
├── rag_system.py
├── bilingual_tokenizer.py
├── bpe_tokenizer.py
├── inference_utils.py
├── generation_utils.py
├── hallucination_detection.py
├── uncertainty_quantification.py
├── honest_generation.py
├── quantization.py
├── lora.py
└── model_export.py
```

---

## 總結

### ✅ Mock 機制確認

| 項目 | 狀態 | 說明 |
|------|------|------|
| **核心 Mock 類** | ✅ 存在 | `mock_connector.py` (766 行) |
| **完整接口偽裝** | ✅ 完成 | MockBinanceConnector 完全模擬真實 API |
| **無縫集成** | ✅ 實現 | TradingEngine 無需修改即可切換 |
| **被實際使用** | ✅ 確認 | `self_improvement.py` 中多處使用 |
| **測試數據生成** | ✅ 存在 | 多處 `mock_signals`, `mock_market_data` |

### ✅ 模組連結確認

| 依賴類型 | 狀態 | 說明 |
|---------|------|------|
| **schemas 為基礎** | ✅ 確認 | 所有模組都依賴 schemas |
| **跨模組導入** | ✅ 清晰 | 18+ 處從 schemas 導入 |
| **Mock 連結** | ✅ 明確 | 3 處直接導入 MockBinanceConnector |
| **RAG 集成** | ✅ 確認 | strategies 和 analysis 使用 RAG |
| **循環依賴** | ✅ 無 | 層級清晰，無循環依賴 |

### 📊 統計摘要

- **總檔案數**: 122 個 Python 檔案
- **Mock 相關**: 5 個核心檔案 + 多處使用
- **schemas 模組**: 19 個數據結構定義
- **核心代碼行數**: 
  - MockBinanceConnector: 766 行
  - historical_backtest.py: 629 行
  - walk_forward.py: 726 行
  - knowledge_base.py: 461 行
  - embeddings.py: 288 行
  - retriever.py: 337 行

---

**報告生成時間**: 2026年2月15日  
**分析工具**: VS Code + Python AST Analysis  
**維護者**: BioNeuronai 開發團隊

如需更新此報告，請重新運行分析工具或手動編輯此檔案。
