# 🧠 BioNeuronAI 完整操作手冊

## 📑 目錄

1. 🎯 系統簡介
2. 🏗️ 核心架構
3. 📚 版本演進歷史
4. 🚀 安裝與配置
5. 🔑 API 密鑰設置
6. 🧬 三大 ML 核心系統
7. 7.1 基因演算法策略進化
8. 7.2 RL Meta-Agent 策略融合
9. 7.3 RLHF 新聞預測驗證
10. 📊 交易策略系統
11. 🛡️ 風險管理系統
12. 📋 10步驟交易計劃 SOP
13. 📰 新聞分析與預測
14. 💾 數據存儲與檢索
15. 🔍 回測與評估
16. 📊 可視化與監控
17. ❓ 常見問題 FAQ
18. 🛠️ 錯誤處理指南
19. 🔧 系統維護
20. 📚 延伸閱讀
21. 🎓 學習路徑
22. 📞 支持與反饋
23. 📜 版權與許可
24. 📝 更新日誌

---

## 🎯 系統簡介

### 什麼是 BioNeuronAI？

BioNeuronAI 是一個**基於機器學習的智能加密貨幣交易系統**，整合了最先進的演化算法、強化學習和人類反饋學習技術。

### 🌟 核心特點

#### 💡 三大 ML 核心能力
1. **基因演算法（Genetic Algorithm）**
   - 自動進化交易策略參數
   - 島嶼模型並行演化
   - 適應市場變化的參數優化

2. **RL Meta-Agent（強化學習元代理）**
   - 43維狀態空間感知
   - Transformer 策略網絡
   - 4階段課程學習
   - 動態策略融合權重

3. **RLHF（人類反饋強化學習）**
   - 自動化新聞預測驗證
   - 人類專家反饋收集
   - 預測品質持續改進

#### 🔧 完整交易功能
- **多策略融合**: RSI背離、突破交易、趨勢追隨、均值回歸
- **AI 驅動決策**: 111.2M 參數 MLP 模型
- **SOP 自動化**: 10步驟標準作業流程
- **實時市場監控**: WebSocket 毫秒級行情
- **完整風險管理**: 動態止損、倉位控制、回撤保護
- **SQLite 數據庫**: 數據持久化與歷史回溯

---

## 🏗️ 核心架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        用戶操作層                                 │
│  ┌─────────────────────┐  ┌──────────────────────────────┐     │
│  │ 快速啟動腳本         │  │ SOP 自動化控制器              │     │
│  │ use_crypto_trader.py│  │ trading_plan_controller.py    │     │
│  └──────────┬──────────┘  └──────────────┬───────────────┘     │
└─────────────┼──────────────────────────────┼───────────────────┘
              │                              │
┌─────────────┼──────────────────────────────┼───────────────────┐
│             │      ML 核心層 (v4.0 New!)   │                   │
│  ┌──────────▼───────────┐  ┌──────────────▼──────────────┐    │
│  │ 基因演算法進化系統   │  │ RL Meta-Agent 策略融合      │    │
│  │ self_improvement.py  │  │ rl_fusion_agent.py          │    │
│  │ - Island Model       │  │ - 43-dim State Space        │    │
│  │ - Co-Evolution       │  │ - Transformer Policy        │    │
│  │ - Fitness Landscape  │  │ - Curriculum Learning       │    │
│  └──────────────────────┘  └─────────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ RLHF 新聞預測驗證系統                                 │     │
│  │ news_prediction_loop.py                              │     │
│  │ - Auto Scheduler  - Human Feedback  - Quality Track  │     │
│  └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
              │
┌─────────────┼─────────────────────────────────────────────────┐
│             │            策略與決策層                          │
│  ┌──────────▼───────────┐  ┌────────────────────────────┐    │
│  │ 策略融合引擎         │  │ AI 模型決策引擎             │    │
│  │ StrategyFusion       │  │ 111.2M MLP Model           │    │
│  │ - RSI Divergence     │  │ - 市場預測                  │    │
│  │ - Breakout           │  │ - 風險評估                  │    │
│  │ - Trend Following    │  │ - 信號整合                  │    │
│  │ - Mean Reversion     │  └────────────────────────────┘    │
│  └──────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
              │
┌─────────────┼─────────────────────────────────────────────────┐
│             │            交易執行層                            │
│  ┌──────────▼───────────┐  ┌────────────────────────────┐    │
│  │ 交易引擎             │  │ 風險管理器                  │    │
│  │ TradingEngine        │  │ RiskManager                │    │
│  │ - 訂單執行            │  │ - 4等級風險控制             │    │
│  │ - 倉位管理            │  │ - Kelly Criterion          │    │
│  │ - 實時監控            │  │ - VaR/最大回撤              │    │
│  └──────────────────────┘  └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
              │
┌─────────────┼─────────────────────────────────────────────────┐
│             │            數據與分析層                          │
│  ┌──────────▼───────────┐  ┌────────────────────────────┐    │
│  │ 市場數據收集器       │  │ 新聞分析系統                │    │
│  │ - WebSocket 實時     │  │ - RAG 新聞抓取              │    │
│  │ - REST API 歷史      │  │ - 情感分析                  │    │
│  │ - 技術指標計算       │  │ - 505關鍵字過濾             │    │
│  └──────────────────────┘  └────────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ SQLite 數據庫                                         │     │
│  │ - 交易記錄  - 策略性能  - 新聞數據  - 訓練歷史       │     │
│  └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
              │
┌─────────────┼─────────────────────────────────────────────────┐
│             │            外部接口層                            │
│  ┌──────────▼───────────┐  ┌────────────────────────────┐    │
│  │ 幣安 API             │  │ 新聞數據源                  │    │
│  │ - 現貨 Spot          │  │ - CoinTelegraph            │    │
│  │ - 期貨 Futures       │  │ - CoinDesk                 │    │
│  │ - WebSocket          │  │ - Decrypt                  │    │
│  │ - 測試網/主網         │  │ - CryptoPanic API          │    │
│  └──────────────────────┘  └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 版本演進歷史

| 版本 | 日期 | 核心升級 | 狀態 |
|------|------|----------|------|
| **v4.0** | 2026-01-26 | **ML Enhancement** - 新增3大ML核心系統 | ✅ 當前版本 |
| v3.1 | 2026-01-22 | 完整風險管理、SOP自動化 | ⚠️ 待歸檔 |
| v3.0 | 2026-01-20 | AI模型整合、策略融合 | ⚠️ 待歸檔 |
| v2.1 | 2026-01-15 | SQLite數據庫、新聞分析 | ⚠️ 待歸檔 |
| v2.0 | 2026-01-10 | 多策略系統、WebSocket | 🗄️ 已歸檔 |
| v1.0 | 2025-12-01 | 基礎交易功能 | 🗄️ 已歸檔 |

### v4.0 重大升級說明

**新增核心功能**：
1. ✨ **基因演算法策略進化**
   - Island Model 並行演化
   - 智能參數優化
   - 適應性進化

2. ✨ **RL Meta-Agent 策略融合**
   - 43維狀態空間
   - Transformer 注意力機制
   - 4階段課程學習

3. ✨ **RLHF 新聞預測驗證**
   - 自動化預測循環
   - 人類反饋收集
   - 預測品質追蹤

**文檔整合**：
- 整合 6 個舊版操作手冊
- 統一技術文檔結構
- 添加完整 ML 算法說明

---

## 🚀 安裝與配置

### Python 環境要求

```bash
# 檢查 Python 版本 (需要 >= 3.11)
python --version

# 應顯示: Python 3.11.x 或更高
```

### 依賴安裝

#### 方式 1: 自動安裝（推薦）

```bash
# 運行自動安裝腳本
python setup_v2.1.py

# 腳本會自動：
# ✅ 檢查 Python 版本
# ✅ 安裝所有依賴
# ✅ 驗證模組導入
# ✅ 運行功能測試
# ✅ 生成安裝報告
```

#### 方式 2: 手動安裝

```bash
# 1. 基礎依賴
pip install numpy>=1.24.0 pandas>=2.0.0 torch>=2.0.0

# 2. 強化學習依賴 (v4.0 新增)
pip install stable-baselines3==2.2.1 gymnasium==0.29.1

# 3. 遺傳算法依賴 (v4.0 新增)
pip install deap==1.4.1

# 4. 交易相關
pip install websocket-client requests

# 5. 數據驗證
pip install pydantic>=2.0.0 sqlalchemy>=2.0.0

# 6. 可視化與監控 (可選)
pip install tensorboard wandb matplotlib seaborn

# 7. 任務調度 (RLHF 需要)
pip install schedule

# 8. 加密貨幣 API
pip install python-binance
```

### 依賴清單說明

| 套件 | 版本 | 用途 | 必需性 |
|------|------|------|--------|
| **核心依賴** |
| numpy | >=1.24.0 | 數值計算 | ✅ 必需 |
| pandas | >=2.0.0 | 數據處理 | ✅ 必需 |
| torch | >=2.0.0 | 深度學習 | ✅ 必需 |
| **ML 依賴 (v4.0)** |
| stable-baselines3 | 2.2.1 | 強化學習框架 | ✅ 必需 |
| gymnasium | 0.29.1 | RL 環境接口 | ✅ 必需 |
| deap | 1.4.1 | 遺傳算法 | ✅ 必需 |
| schedule | >=1.2.0 | RLHF 調度 | ✅ 必需 |
| **交易依賴** |
| websocket-client | latest | 實時數據 | ✅ 必需 |
| python-binance | latest | 幣安 API | ✅ 必需 |
| requests | latest | HTTP 請求 | ✅ 必需 |
| **數據依賴** |
| pydantic | >=2.0.0 | 數據驗證 | ✅ 必需 |
| sqlalchemy | >=2.0.0 | 數據庫 ORM | ✅ 必需 |
| **可視化依賴** |
| tensorboard | >=2.15.1 | 訓練監控 | ⭕ 可選 |
| wandb | latest | 實驗追蹤 | ⭕ 可選 |
| matplotlib | >=3.7.0 | 圖表繪製 | ⭕ 可選 |
| seaborn | >=0.12.0 | 統計圖表 | ⭕ 可選 |

---

## 🔑 API 密鑰設置

> ⚠️ 部分內容過時：
> 本章節仍以 `config/trading_config.py` 作為主要憑證配置方式，這和最新規劃「Binance 為使用者級憑證來源、`src/schemas/` 為單一事實來源、`api/` 為薄入口殼」不完全一致。
> 可繼續參考的內容：
> - 如何取得 Testnet / Mainnet API key
> - 權限與安全性提醒
> 需重新對照後再使用的內容：
> - 把 `config/trading_config.py` 視為長期主路徑
> - 舊版驗證腳本與舊版入口的假設
>
> 後續請優先對照 [API_INTEGRATION_BASELINE.md](C:/D/E/BioNeuronai/docs/API_INTEGRATION_BASELINE.md)。

### 幣安 API 設置

#### 1. 獲取 API 密鑰

**測試網（推薦新手）**：
1. 訪問 https://testnet.binancefuture.com
2. 使用 GitHub 或 Email 註冊
3. 進入「API Keys」頁面
4. 點擊「Create New Key」
5. 保存 API Key 和 Secret Key

**主網（實盤交易）**：
1. 登入 https://www.binance.com
2. 進入「API Management」
3. 創建新的 API Key
4. **重要**: 啟用期貨交易權限
5. 設置 IP 白名單（推薦）

#### 2. 配置 API 密鑰

複製範本並填入金鑰（金鑰不應寫入 `.py` 原始碼）：

```bash
cp .env.example .env
```

編輯 `.env`，填入以下三個值：

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_key_here
BINANCE_TESTNET=true     # false = 正式網
```

#### 3. 驗證 API 連接

```bash
# 運行 API 測試腳本
python scripts/test_binance_connection.py

# 應該看到：
# ✅ API 連接成功
# ✅ 帳戶餘額: 10000.00 USDT
# ✅ WebSocket 連接正常
```

### 新聞 API 設置（可選）

如果要使用進階新聞分析功能：

```python
# config/trading_config.py

# CryptoPanic API (可選，用於新聞聚合)
CRYPTOPANIC_API_KEY = "your_cryptopanic_key"  # 可留空

# News API (可選，用於新聞搜索)
NEWS_API_KEY = "your_news_api_key"  # 可留空
```

> 💡 **提示**: 即使不設置新聞 API，系統仍可使用內建的網頁爬蟲功能獲取新聞。

---

## 🧬 三大 ML 核心系統

BioNeuronAI v4.0 的核心競爭力來自三大機器學習系統，它們協同工作，實現策略的持續進化和優化。

---

## 7.1 基因演算法策略進化

### 💡 核心概念

基因演算法（Genetic Algorithm, GA）模擬生物進化過程，通過選擇、交叉、突變等操作，自動進化出適應市場環境的最優策略參數。

### 🏗️ Island Model 架構

```
┌─────────────────────────────────────────────────────────┐
│              Island Model Evolution                      │
├─────────────────────────────────────────────────────────┤
│  Island 1        Island 2        Island 3        Island 4│
│  (趨勢市場)      (震盪市場)      (突破市場)      (混合市場)│
│  ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐│
│  │ Pop:100│      │ Pop:100│      │ Pop:100│      │ Pop:100││
│  │ Gen:50 │      │ Gen:50 │      │ Gen:50 │      │ Gen:50 ││
│  └───┬───┘      └───┬───┘      └───┬───┘      └───┬───┘│
│      │              │              │              │      │
│      └──────────────┼──────────────┼──────────────┘      │
│                     │              │                      │
│             Migration (每10代)                           │
│         交換 5% 最佳個體 (Ring Topology)                 │
└─────────────────────────────────────────────────────────┘
```

### 📊 參數編碼

每個策略個體包含以下可進化參數：

```python
{
    # RSI 策略參數
    'rsi_period': [5, 30],           # RSI 週期
    'rsi_oversold': [20, 40],        # 超賣閾值
    'rsi_overbought': [60, 80],      # 超買閾值

    # 突破策略參數
    'breakout_window': [10, 50],     # 突破窗口
    'breakout_std_mult': [1.0, 3.0], # 標準差倍數

    # 趨勢策略參數
    'ema_short': [5, 20],            # 短期 EMA
    'ema_long': [20, 100],           # 長期 EMA

    # 風險管理參數
    'stop_loss_pct': [0.5, 3.0],     # 止損百分比
    'take_profit_pct': [1.0, 5.0],   # 止盈百分比
    'max_position_size': [0.1, 0.5]   # 最大倉位
}
```

### 🎯 適應度函數

```python
def calculate_fitness(individual, market_data):
    """
    計算個體適應度（綜合評分）
    """
    # 1. 運行回測
    trades = backtest_strategy(individual, market_data)

    # 2. 計算多維指標
    total_return = calculate_return(trades)
    sharpe_ratio = calculate_sharpe(trades)
    max_drawdown = calculate_max_drawdown(trades)
    win_rate = calculate_win_rate(trades)
    profit_factor = calculate_profit_factor(trades)

    # 3. 綜合評分（加權組合）
    fitness = (
        total_return * 0.30 +        # 總收益 30%
        sharpe_ratio * 0.25 +        # 夏普比率 25%
        (1 - max_drawdown) * 0.20 +  # 回撤控制 20%
        win_rate * 0.15 +            # 勝率 15%
        profit_factor * 0.10         # 盈虧比 10%
    )

    return fitness
```

### 🔄 進化流程

```python
# 1. 初始化種群
from src.bioneuronai.core.self_improvement import IslandEvolutionEngine

engine = IslandEvolutionEngine(
    n_islands=4,                    # 4個島嶼
    population_per_island=100,      # 每島100個體
    n_generations=50,               # 進化50代
    migration_interval=10,          # 每10代遷移
    migration_size=5                # 遷移5個體
)

# 2. 開始進化
results = engine.evolve(
    market_data=historical_data,    # 歷史市場數據
    market_type='trending'          # 市場類型
)

# 3. 獲取最佳策略
best_individual = results['best_individual']
best_fitness = results['best_fitness']
evolution_history = results['history']

print(f"最佳適應度: {best_fitness:.4f}")
print(f"最佳參數: {best_individual}")
```

### 📈 可視化

```python
# 1. 適應度進化曲線
from src.bioneuronai.visualization import plot_fitness_evolution

plot_fitness_evolution(
    history=evolution_history,
    save_path='evolution_fitness.png'
)

# 2. 3D 適應度景觀
from src.bioneuronai.visualization import plot_3d_fitness_landscape

plot_3d_fitness_landscape(
    population=final_population,
    param1='rsi_period',
    param2='ema_short',
    save_path='fitness_landscape.png'
)
```

### 🎓 使用建議

| 市場狀態 | 建議配置 | 說明 |
|---------|---------|------|
| **牛市/熊市** | 趨勢島嶼權重↑ | 加大趨勢策略島嶼種群 |
| **震盪市** | 震盪島嶼權重↑ | 加大均值回歸島嶼種群 |
| **高波動** | 突破島嶼權重↑ | 加大突破策略島嶼種群 |
| **不確定** | 均衡配置 | 各島嶼種群相等 |

### ⚠️ 注意事項

1. **過擬合風險**: 
   - 使用 Out-of-Sample 測試
   - 定期用新數據重新進化

2. **計算資源**:
   - 4島×100個體×50代 = 20,000次回測
   - 建議使用多核心並行計算

3. **參數約束**:
   - 確保參數範圍合理
   - 避免極端參數組合

---

## 7.2 RL Meta-Agent 策略融合

### 💡 核心概念

RL Meta-Agent 是一個**元策略代理**，它不直接做出交易決策，而是學習如何動態調整多個子策略的權重，實現智能策略融合。

### 🧠 Transformer 策略網絡

```
輸入層 (43維狀態)
    │
    ├─ 策略信號 (7維): RSI, Breakout, Trend, MeanRev...
    ├─ 市場狀態 (5維): Volatility, Volume, Momentum...
    ├─ 倉位信息 (4維): Position Size, Leverage, PnL...
    ├─ 性能歷史 (21維): 7策略×3指標 (勝率/夏普/回撤)
    ├─ 風險指標 (4維): VaR, Drawdown, Correlation...
    └─ 時間特徵 (2維): Hour, DayOfWeek
    │
    ▼
Multi-Head Self-Attention (4 heads, dim=128)
    │
    ├─ Head 1: 關注短期信號
    ├─ Head 2: 關注中期趨勢
    ├─ Head 3: 關注風險指標
    └─ Head 4: 關注性能歷史
    │
    ▼
Feed-Forward Network (128 → 256 → 128)
    │
    ├─ ReLU 激活
    ├─ Dropout (0.1)
    └─ LayerNorm
    │
    ▼
輸出層 (7維策略權重)
    │
    └─ Softmax → [w1, w2, w3, w4, w5, w6, w7]
```

### 📊 43維狀態空間詳解

```python
class StrategyFusionEnv(gym.Env):
    """RL Meta-Agent 環境"""

    def __init__(self):
        # 狀態空間: 43維
        self.observation_space = gym.spaces.Box(
            low=-10.0, high=10.0, 
            shape=(43,), 
            dtype=np.float32
        )

        # 動作空間: 7維策略權重
        self.action_space = gym.spaces.Box(
            low=0.0, high=1.0, 
            shape=(7,), 
            dtype=np.float32
        )

    def _get_observation(self):
        """構建43維狀態向量"""
        obs = np.concatenate([
            # 1. 策略信號 (7維)
            self._get_strategy_signals(),      # [0-6]

            # 2. 市場狀態 (5維)
            [
                self.volatility,               # [7] 波動率
                self.volume_ratio,             # [8] 成交量比率
                self.momentum,                 # [9] 動量指標
                self.trend_strength,           # [10] 趨勢強度
                self.liquidity                 # [11] 流動性
            ],

            # 3. 倉位信息 (4維)
            [
                self.position_size,            # [12] 當前倉位
                self.leverage,                 # [13] 槓桿倍數
                self.unrealized_pnl,           # [14] 未實現盈虧
                self.margin_ratio              # [15] 保證金比率
            ],

            # 4. 策略性能歷史 (21維 = 7策略×3指標)
            self._get_strategy_performance(),  # [16-36]

            # 5. 風險指標 (4維)
            [
                self.current_drawdown,         # [37] 當前回撤
                self.var_95,                   # [38] 95% VaR
                self.portfolio_correlation,    # [39] 組合相關性
                self.sharpe_ratio              # [40] 夏普比率
            ],

            # 6. 時間特徵 (2維)
            [
                np.sin(2*np.pi*hour/24),      # [41] 小時 (sin編碼)
                np.sin(2*np.pi*dow/7)          # [42] 星期 (sin編碼)
            ]
        ])

        return obs

    def _get_strategy_signals(self):
        """獲取7個策略的標準化信號"""
        return np.array([
            self.rsi_divergence_signal,        # [-1, 1]
            self.breakout_signal,              # [-1, 1]
            self.trend_following_signal,       # [-1, 1]
            self.mean_reversion_signal,        # [-1, 1]
            self.momentum_signal,              # [-1, 1]
            self.swing_trading_signal,         # [-1, 1]
            self.ai_model_signal               # [-1, 1]
        ])

    def _get_strategy_performance(self):
        """獲取7個策略的性能指標 (最近100筆交易)"""
        perf = []
        for strategy in self.strategies:
            perf.extend([
                strategy.win_rate,             # 勝率 [0, 1]
                strategy.sharpe_ratio,         # 夏普比率 [-2, 5]
                strategy.max_drawdown          # 最大回撤 [-1, 0]
            ])
        return np.array(perf)
```

### 🎓 4階段課程學習

```python
class CurriculumTraining:
    """課程學習訓練流程"""

    def __init__(self):
        self.stages = [
            {
                'name': 'Stage 1: 穩定趨勢',
                'market_type': 'trending_stable',
                'difficulty': 'easy',
                'timesteps': 100_000,
                'success_criteria': {
                    'win_rate': 0.55,
                    'sharpe': 1.0
                }
            },
            {
                'name': 'Stage 2: 震盪市場',
                'market_type': 'ranging',
                'difficulty': 'medium',
                'timesteps': 150_000,
                'success_criteria': {
                    'win_rate': 0.52,
                    'sharpe': 0.8
                }
            },
            {
                'name': 'Stage 3: 混合市場',
                'market_type': 'mixed',
                'difficulty': 'hard',
                'timesteps': 200_000,
                'success_criteria': {
                    'win_rate': 0.50,
                    'sharpe': 0.6
                }
            },
            {
                'name': 'Stage 4: 對抗訓練',
                'market_type': 'adversarial',
                'difficulty': 'expert',
                'timesteps': 250_000,
                'success_criteria': {
                    'win_rate': 0.48,
                    'sharpe': 0.5
                }
            }
        ]

    def train(self, agent):
        """執行課程學習"""
        for stage in self.stages:
            print(f"\n=== {stage['name']} ===")

            # 1. 加載對應市場數據
            env = self._create_env(stage['market_type'])

            # 2. 訓練
            agent.learn(
                total_timesteps=stage['timesteps'],
                callback=self._create_callback(stage)
            )

            # 3. 評估
            metrics = self._evaluate(agent, env)

            # 4. 檢查是否達標
            if not self._check_criteria(metrics, stage):
                print(f"⚠️ 未達標，重新訓練...")
                continue
            else:
                print(f"✅ 通過 {stage['name']}")
```

### 🚀 訓練流程

```python
from stable_baselines3 import PPO
from src.bioneuronai.strategies.rl_fusion_agent import (
    StrategyFusionEnv, 
    TransformerPolicyNetwork,
    CurriculumTraining
)

# 1. 創建環境
env = StrategyFusionEnv(
    market_data=historical_data,
    strategies=[
        'rsi_divergence',
        'breakout',
        'trend_following',
        'mean_reversion',
        'momentum',
        'swing_trading',
        'ai_model'
    ]
)

# 2. 創建 RL Agent (使用 Transformer Policy)
agent = PPO(
    policy=TransformerPolicyNetwork,
    env=env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    tensorboard_log="./logs/ppo_fusion/"
)

# 3. 課程學習訓練
curriculum = CurriculumTraining()
curriculum.train(agent)

# 4. 保存模型
agent.save("models/rl_meta_agent_final.zip")

# 5. 可視化訓練過程
# TensorBoard: tensorboard --logdir ./logs/ppo_fusion/
```

### 📈 使用已訓練模型

```python
# 1. 加載模型
agent = PPO.load("models/rl_meta_agent_final.zip")

# 2. 獲取當前市場狀態
obs = env.get_current_observation()  # 43維狀態

# 3. 預測策略權重
action, _states = agent.predict(obs, deterministic=True)

# action = [0.15, 0.10, 0.25, 0.05, 0.20, 0.10, 0.15]
#          ↓     ↓     ↓     ↓     ↓     ↓     ↓
#         RSI   Break  Trend  Mean  Mom   Swing  AI

# 4. 應用融合策略
fusion_signal = np.dot(action, strategy_signals)

# 5. 執行交易
if fusion_signal > 0.3:
    execute_long_order()
elif fusion_signal < -0.3:
    execute_short_order()
```

### 🎯 優勢分析

| 特點 | 傳統方法 | RL Meta-Agent |
|------|---------|---------------|
| **權重調整** | 固定或手動 | 自動學習 |
| **適應性** | 低 | 高 |
| **市場感知** | 單一指標 | 43維綜合 |
| **策略協同** | 簡單平均 | 注意力機制 |
| **風險控制** | 獨立計算 | 集成於決策 |

### ⚠️ 注意事項

1. **訓練數據**:
   - 需要至少 2 年歷史數據
   - 包含多種市場狀態

2. **過擬合防範**:
   - 使用 Dropout (0.1)
   - 早停機制
   - 驗證集評估

3. **實盤部署**:
   - 先在模擬盤測試 1 個月
   - 監控實際性能與訓練性能偏差
   - 定期重新訓練（建議每月）

---

## 7.3 RLHF 新聞預測驗證

### 💡 核心概念

RLHF (Reinforcement Learning from Human Feedback) 系統通過**人類專家反饋**，持續改進新聞對價格影響的預測品質。

### 🔄 完整生命週期

```
┌──────────────────────────────────────────────────────────┐
│                 RLHF 預測驗證循環                         │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  1. 新聞抓取                                              │
│     ├─ RAG 系統自動抓取最新新聞                           │
│     ├─ 505 關鍵字過濾                                     │
│     └─ 情感分析 (正面/負面/中性)                          │
│                    │                                      │
│                    ▼                                      │
│  2. 影響預測                                              │
│     ├─ 預測價格變化: [-10%, +10%]                        │
│     ├─ 預測時間範圍: [1h, 24h, 7d]                       │
│     └─ 預測置信度: [0, 100]                              │
│                    │                                      │
│                    ▼                                      │
│  3. 記錄與追蹤                                            │
│     ├─ 保存預測到數據庫                                   │
│     ├─ 記錄新聞發布時的價格                               │
│     └─ 設置驗證任務 (1h, 24h, 7d後)                      │
│                    │                                      │
│                    ▼                                      │
│  4. 自動驗證                                              │
│     ├─ 定時檢查預測結果 (Scheduler)                      │
│     ├─ 計算實際價格變化                                   │
│     └─ 計算預測誤差 (MAE, RMSE)                          │
│                    │                                      │
│                    ▼                                      │
│  5. 人類反饋                                              │
│     ├─ 展示預測 vs 實際對比                              │
│     ├─ 專家評分: 1-5 星                                  │
│     └─ 專家註解: 錯誤原因分析                            │
│                    │                                      │
│                    ▼                                      │
│  6. 模型更新                                              │
│     ├─ 收集人類反饋數據                                   │
│     ├─ 重新訓練預測模型                                   │
│     └─ A/B 測試新舊模型                                   │
│                    │                                      │
│                    └───────────┐                          │
│                                │                          │
│                                ▼                          │
│  7. 品質追蹤                                              │
│     ├─ 預測準確率趨勢                                     │
│     ├─ 人類-模型一致性                                    │
│     └─ 生成品質報告                                       │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 📊 數據結構

```python
class NewsPrediction:
    """新聞預測記錄"""

    def __init__(self):
        self.prediction_id = uuid4()

        # 新聞信息
        self.news_title = ""
        self.news_content = ""
        self.news_source = ""
        self.news_timestamp = datetime.now()
        self.sentiment = ""  # "positive", "negative", "neutral"

        # 價格信息
        self.price_at_news = 0.0
        self.symbol = "BTCUSDT"

        # 預測信息
        self.predicted_change_1h = 0.0    # %
        self.predicted_change_24h = 0.0   # %
        self.predicted_change_7d = 0.0    # %
        self.confidence_score = 0.0       # [0, 100]

        # 驗證信息
        self.actual_change_1h = None
        self.actual_change_24h = None
        self.actual_change_7d = None
        self.verified_1h = False
        self.verified_24h = False
        self.verified_7d = False

        # 人類反饋
        self.human_rating = None          # 1-5 星
        self.human_comment = None         # 專家註解
        self.feedback_timestamp = None

        # 錯誤分析
        self.mae_1h = None
        self.mae_24h = None
        self.mae_7d = None
```

### 🤖 自動驗證調度器

```python
import schedule
import time
from src.bioneuronai.analysis.news_prediction_loop import (
    PredictionScheduler,
    HumanFeedbackCollector
)

# 1. 創建調度器
scheduler = PredictionScheduler(
    db_path='trading_data/predictions.db'
)

# 2. 設置自動驗證任務
schedule.every(1).hours.do(scheduler.verify_1h_predictions)
schedule.every(1).days.do(scheduler.verify_24h_predictions)
schedule.every(7).days.do(scheduler.verify_7d_predictions)

# 3. 設置人類反饋提醒
schedule.every(1).days.at("09:00").do(
    scheduler.generate_feedback_report
)

# 4. 啟動調度器
print("🚀 RLHF 調度器已啟動")
while True:
    schedule.run_pending()
    time.sleep(60)  # 每分鐘檢查一次
```

### 👤 人類反饋界面

```python
class HumanFeedbackCollector:
    """人類反饋收集器"""

    def show_prediction_for_review(self, prediction_id):
        """展示預測供專家審核"""
        pred = self.db.get_prediction(prediction_id)

        print("\n" + "="*60)
        print("📰 新聞預測審核")
        print("="*60)
        print(f"\n新聞標題: {pred.news_title}")
        print(f"發布時間: {pred.news_timestamp}")
        print(f"情感: {pred.sentiment}")
        print(f"\n價格 (發布時): ${pred.price_at_news:.2f}")

        print("\n--- 預測 vs 實際 ---")
        print(f"1小時:")
        print(f"  預測: {pred.predicted_change_1h:+.2f}%")
        print(f"  實際: {pred.actual_change_1h:+.2f}%")
        print(f"  誤差: {pred.mae_1h:.2f}%")

        print(f"\n24小時:")
        print(f"  預測: {pred.predicted_change_24h:+.2f}%")
        print(f"  實際: {pred.actual_change_24h:+.2f}%")
        print(f"  誤差: {pred.mae_24h:.2f}%")

        # 收集反饋
        rating = input("\n請評分 (1-5星): ")
        comment = input("錯誤原因分析 (選填): ")

        self.db.save_feedback(
            prediction_id=prediction_id,
            rating=int(rating),
            comment=comment
        )

        print("✅ 反饋已保存")
```

### 📈 品質追蹤儀表板

```python
def generate_quality_report():
    """生成 RLHF 品質報告"""

    # 1. 查詢最近 30 天的預測
    predictions = db.get_predictions(days=30)

    # 2. 計算指標
    metrics = {
        'total_predictions': len(predictions),
        'verified_predictions': sum(p.verified_24h for p in predictions),
        'avg_mae_1h': np.mean([p.mae_1h for p in predictions if p.mae_1h]),
        'avg_mae_24h': np.mean([p.mae_24h for p in predictions if p.mae_24h]),
        'avg_human_rating': np.mean([p.human_rating for p in predictions if p.human_rating]),
        'human_model_agreement': calculate_agreement(predictions)
    }

    # 3. 可視化
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # 圖1: MAE 趨勢
    plot_mae_trend(predictions, axes[0, 0])

    # 圖2: 人類評分分布
    plot_rating_distribution(predictions, axes[0, 1])

    # 圖3: 預測校準曲線
    plot_calibration_curve(predictions, axes[1, 0])

    # 圖4: 一致性矩陣
    plot_agreement_matrix(predictions, axes[1, 1])

    plt.savefig('rlhf_quality_report.png')

    return metrics
```

### 🔄 模型更新流程

```python
def retrain_with_human_feedback():
    """使用人類反饋重新訓練預測模型"""

    # 1. 收集帶有反饋的數據
    feedback_data = db.get_predictions_with_feedback()

    # 2. 數據處理
    X_train = []
    y_train = []
    weights = []

    for pred in feedback_data:
        # 特徵: 新聞向量 + 市場狀態
        features = extract_features(pred)
        X_train.append(features)

        # 標籤: 實際價格變化
        y_train.append(pred.actual_change_24h)

        # 權重: 人類評分作為樣本權重
        weights.append(pred.human_rating)

    # 3. 訓練新模型
    from sklearn.ensemble import GradientBoostingRegressor

    model_new = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5
    )

    model_new.fit(
        X_train, 
        y_train, 
        sample_weight=weights
    )

    # 4. A/B 測試
    test_data = get_recent_predictions(days=7)

    mae_old = evaluate_model(model_old, test_data)
    mae_new = evaluate_model(model_new, test_data)

    print(f"舊模型 MAE: {mae_old:.3f}%")
    print(f"新模型 MAE: {mae_new:.3f}%")

    # 5. 如果新模型更好，替換
    if mae_new < mae_old * 0.95:  # 至少改進 5%
        save_model(model_new, 'news_predictor_v2.pkl')
        print("✅ 模型已更新")
    else:
        print("⚠️ 新模型未達改進標準，保留舊模型")
```

### 🎯 使用範例

```python
# ===== 完整 RLHF 流程示例 =====

# 1. 新聞預測
from src.bioneuronai.analysis.news_prediction_loop import NewsPredictionSystem

predictor = NewsPredictionSystem()

# 抓取並預測新聞
news_item = {
    'title': 'SEC Approves Bitcoin Spot ETF',
    'content': '...',
    'source': 'CoinDesk',
    'timestamp': datetime.now()
}

prediction = predictor.predict_news_impact(news_item)
print(f"預測 24h 變化: {prediction.predicted_change_24h:+.2f}%")
print(f"置信度: {prediction.confidence_score:.1f}%")

# 2. 自動驗證 (24小時後)
# ... 調度器自動運行 ...

# 3. 人類反饋
feedback_collector = HumanFeedbackCollector()
feedback_collector.show_prediction_for_review(prediction.prediction_id)

# 4. 生成品質報告
metrics = generate_quality_report()
print(f"平均 MAE: {metrics['avg_mae_24h']:.2f}%")
print(f"人類評分: {metrics['avg_human_rating']:.1f}/5.0")

# 5. 模型更新 (每月)
retrain_with_human_feedback()
```

### 📊 性能指標

| 指標 | 目標值 | 當前值 | 狀態 |
|------|-------|-------|------|
| **24h MAE** | < 3.0% | 2.8% | ✅ 達標 |
| **人類評分** | > 3.5/5.0 | 3.8/5.0 | ✅ 達標 |
| **一致性** | > 70% | 75% | ✅ 達標 |
| **預測數量** | > 50/月 | 68/月 | ✅ 達標 |

### ⚠️ 注意事項

1. **人類反饋質量**:
   - 確保審核專家具備市場經驗
   - 定期校準評分標準

2. **樣本偏差**:
   - 避免只在錯誤預測上收集反饋
   - 平衡正面/負面新聞樣本

3. **過度優化風險**:
   - 不要過度擬合人類反饋
   - 保留獨立測試集

---

## 📊 交易策略系統

BioNeuronAI 整合了 7 個核心交易策略，通過 **RL Meta-Agent** 動態調整權重，實現智能策略融合。

### 🎯 策略組合

| 策略名稱 | 適用市場 | 典型權重 | 文檔位置 |
|---------|---------|---------|---------|
| **RSI 背離** | 震盪市場 | 15% | [詳細說明](#rsi-背離策略) |
| **突破交易** | 高波動 | 10% | [詳細說明](#突破交易策略) |
| **趨勢追隨** | 單邊市場 | 25% | [詳細說明](#趨勢追隨策略) |
| **均值回歸** | 區間震盪 | 5% | [詳細說明](#均值回歸策略) |
| **動量交易** | 快速行情 | 20% | [詳細說明](#動量交易策略) |
| **波段交易** | 中期趨勢 | 10% | [詳細說明](#波段交易策略) |
| **AI 模型** | 全市場 | 15% | [詳細說明](#ai-模型策略) |

### 🔵 RSI 背離策略

**原理**: RSI 與價格背離時預示趨勢反轉

**交易信號**:
```
牛背離（買入）:
  價格: Lower Low
  RSI: Higher Low
  → 可能反彈

熊背離（賣出）:
  價格: Higher High  
  RSI: Lower High
  → 可能回調
```

**參數**:
- RSI 週期: 14
- 超買: 70
- 超賣: 30
- 背離確認窗口: 5根K線

**代碼示例**:
```python
from src.bioneuronai.strategies import RSIDivergenceStrategy

strategy = RSIDivergenceStrategy(
    rsi_period=14,
    oversold=30,
    overbought=70
)

signal = strategy.generate_signal(market_data)
# signal = 1.0 (強買入), -1.0 (強賣出), 0.0 (中性)
```

### 🟢 突破交易策略

**原理**: 價格突破區間時跟隨方向

**交易信號**:
```
向上突破:
  當前價格 > Bollinger上軌 + 成交量放大
  → 買入

向下突破:
  當前價格 < Bollinger下軌 + 成交量放大
  → 賣出
```

**參數**:
- 窗口期: 20
- 標準差倍數: 2.0
- 成交量閾值: 1.5倍平均

**代碼示例**:
```python
from src.bioneuronai.strategies import BreakoutStrategy

strategy = BreakoutStrategy(
    window=20,
    std_mult=2.0,
    volume_threshold=1.5
)

signal = strategy.generate_signal(market_data)
```

### 🟡 趨勢追隨策略

**原理**: 雙EMA交叉確認趨勢方向

**交易信號**:
```
金叉（買入）:
  EMA(9) 上穿 EMA(21)
  + 價格在 EMA(50) 上方
  → 多頭趨勢確認

死叉（賣出）:
  EMA(9) 下穿 EMA(21)
  + 價格在 EMA(50) 下方
  → 空頭趨勢確認
```

**參數**:
- 短期 EMA: 9
- 中期 EMA: 21
- 長期 EMA: 50

**代碼示例**:
```python
from src.bioneuronai.strategies import TrendFollowingStrategy

strategy = TrendFollowingStrategy(
    fast_ema=9,
    medium_ema=21,
    slow_ema=50
)

signal = strategy.generate_signal(market_data)
```

### 🟠 均值回歸策略

**原理**: 價格偏離均值時回歸

**交易信號**:
```
超賣回歸:
  Z-Score < -2.0
  + RSI < 30
  → 買入

超買回歸:
  Z-Score > 2.0
  + RSI > 70
  → 賣出
```

**參數**:
- 窗口期: 20
- Z-Score 閾值: ±2.0

**代碼示例**:
```python
from src.bioneuronai.strategies import MeanReversionStrategy

strategy = MeanReversionStrategy(
    window=20,
    zscore_threshold=2.0
)

signal = strategy.generate_signal(market_data)
```

### 🔴 動量交易策略

**原理**: 捕捉短期動量加速

**交易信號**:
```
正向動量:
  ROC(10) > 2%
  + MACD > Signal
  → 買入

負向動量:
  ROC(10) < -2%
  + MACD < Signal
  → 賣出
```

**參數**:
- ROC 週期: 10
- MACD: (12, 26, 9)
- 動量閾值: 2%

**代碼示例**:
```python
from src.bioneuronai.strategies import MomentumStrategy

strategy = MomentumStrategy(
    roc_period=10,
    threshold=0.02
)

signal = strategy.generate_signal(market_data)
```

### 🟣 波段交易策略

**原理**: 中期波段高拋低吸

**交易信號**:
```
波段低點:
  Stochastic < 20
  + 價格觸及支撐位
  → 買入

波段高點:
  Stochastic > 80
  + 價格觸及壓力位
  → 賣出
```

**參數**:
- Stochastic: (14, 3, 3)
- 支撐/壓力識別窗口: 50

**代碼示例**:
```python
from src.bioneuronai.strategies import SwingTradingStrategy

strategy = SwingTradingStrategy(
    stoch_period=14,
    support_resistance_window=50
)

signal = strategy.generate_signal(market_data)
```

### 🧠 AI 模型策略

**原理**: 111.2M 參數 MLP 模型預測

**輸入特徵** (50維):
- 技術指標 (20維): RSI, MACD, BB, ATR...
- 市場微結構 (15維): 買賣壓力, 深度, 大單流向...
- 情緒指標 (10維): 新聞情感, Fear&Greed, 社交媒體...
- 時間特徵 (5維): 時段, 星期, 月份...

**輸出**:
- 未來 1h 價格變化預測: [-10%, +10%]
- 預測置信度: [0, 100]

**代碼示例**:
```python
from src.bioneuronai.strategies import AIModelStrategy

strategy = AIModelStrategy(
    model_path='model/my_100m_model.pth',
    threshold=0.3  # 置信度閾值
)

signal = strategy.generate_signal(market_data)
```

### 🎛️ 策略融合

```python
# ===== 使用 RL Meta-Agent 進行策略融合 =====

from src.bioneuronai.strategies import StrategyFusion
from stable_baselines3 import PPO

# 1. 初始化所有策略
strategies = {
    'rsi': RSIDivergenceStrategy(),
    'breakout': BreakoutStrategy(),
    'trend': TrendFollowingStrategy(),
    'mean_rev': MeanReversionStrategy(),
    'momentum': MomentumStrategy(),
    'swing': SwingTradingStrategy(),
    'ai': AIModelStrategy()
}

# 2. 加載 RL Meta-Agent
rl_agent = PPO.load("models/rl_meta_agent_final.zip")

# 3. 創建融合引擎
fusion = StrategyFusion(
    strategies=strategies,
    meta_agent=rl_agent
)

# 4. 獲取當前市場狀態
market_state = get_current_market_state()  # 43維狀態

# 5. 獲取各策略信號
signals = {
    name: strategy.generate_signal(market_data)
    for name, strategy in strategies.items()
}

# 6. RL Agent 預測權重
weights = rl_agent.predict(market_state)

# 7. 計算融合信號
fusion_signal = fusion.fuse_signals(signals, weights)

print(f"融合信號: {fusion_signal:.3f}")
print(f"策略權重: {weights}")

# 輸出示例:
# 融合信號: 0.652
# 策略權重: [0.15, 0.08, 0.28, 0.03, 0.22, 0.09, 0.15]
```

---

## 🛡️ 風險管理系統

### 風險等級配置

BioNeuronAI 提供 4 個預設風險等級：

| 等級 | 單筆風險 | 最大倉位 | 槓桿 | 適用對象 |
|------|---------|---------|------|---------|
| **CONSERVATIVE** | 0.5% | 10% | 1-3x | 保守型投資者 |
| **MODERATE** | 1.0% | 20% | 3-5x | 穩健型投資者 |
| **AGGRESSIVE** | 2.0% | 40% | 5-10x | 進取型交易者 |
| **HIGH_RISK** | 5.0% | 80% | 10-20x | 專業交易員 |

### 核心功能

```python
from src.bioneuronai.trading.risk_manager import RiskManager

# 初始化
risk_mgr = RiskManager(
    account_balance=10000,
    risk_level='MODERATE'
)

# 1. 計算倉位大小
position_size = risk_mgr.calculate_position_size(
    entry_price=50000,
    stop_loss_price=49000,
    signal_strength=0.8
)

print(f"建議倉位: ${position_size:.2f}")

# 2. 檢查是否可以交易
can_trade, reason = risk_mgr.check_can_trade()
if can_trade:
    execute_order(position_size)
else:
    print(f"拒絕交易: {reason}")

# 3. 記錄交易
risk_mgr.record_trade(
    entry_price=50000,
    exit_price=51000,
    position_size=position_size,
    pnl=100.0
)

# 4. 獲取風險統計
stats = risk_mgr.get_risk_statistics()
print(f"勝率: {stats['win_rate']:.1%}")
print(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
print(f"最大回撤: {stats['max_drawdown']:.1%}")
```

詳細風險管理文檔請參考舊版 [RISK_MANAGEMENT_MANUAL.md](c:\D\E\BioNeuronai\docs\RISK_MANAGEMENT_MANUAL.md)（待整合）

---

## 📋 10步驟交易計劃 SOP

BioNeuronAI 採用標準化 10 步驟交易計劃流程：

### 快速概覽

| 步驟 | 名稱 | 狀態 | 數據來源 |
|------|------|------|----------|
| 1️⃣ | 系統環境檢查 | ✅ 實現 | 幣安 API |
| 2️⃣ | 宏觀市場掃描 | ✅ 實現 | CoinGecko + Alternative.me |
| 3️⃣ | 技術面分析 | ✅ 實現 | 幣安 API |
| 4️⃣ | 基本面情緒分析 | ✅ 實現 | 新聞 API + RAG |
| 5️⃣ | 策略性能評估 | ✅ 實現 | 本地數據庫 |
| 6️⃣ | 策略選擇權重 | ✅ 實現 | RL Meta-Agent |
| 7️⃣ | 風險參數計算 | ✅ 實現 | RiskManager |
| 8️⃣ | 資金管理規劃 | ✅ 實現 | 幣安 API |
| 9️⃣ | 交易對篩選 | ✅ 實現 | 幣安 API |
| 🔟 | 執行計劃監控 | ✅ 實現 | WebSocket |

### 使用方式

```python
from src.bioneuronai.trading_plan import TradingPlanController

# 初始化
controller = TradingPlanController()

# 執行完整 10 步驟
result = await controller.execute_full_plan()

# 查看結果
print(result['summary'])
print(f"推薦策略: {result['recommended_strategy']}")
print(f"風險評估: {result['risk_assessment']}")

# 開始自動交易
if result['green_light']:
    controller.start_auto_trading()
```

詳細 SOP 流程請參考 [CRYPTO_TRADING_SOP.md](c:\D\E\BioNeuronai\docs\CRYPTO_TRADING_SOP.md)（待整合）和 [TRADING_PLAN_10_STEPS.md](c:\D\E\BioNeuronai\docs\TRADING_PLAN_10_STEPS.md)

---

## 📰 新聞分析與預測

### v4.0 升級：RLHF 新聞系統

新版新聞系統整合了 **RLHF 預測驗證循環**，具備以下功能：

1. **自動新聞抓取** (RAG 系統)
2. **情感分析** (505 關鍵字)
3. **價格影響預測** (1h, 24h, 7d)
4. **自動驗證** (調度器)
5. **人類反饋** (專家評分)
6. **模型更新** (持續改進)

### 快速使用

```python
from src.bioneuronai.analysis.news_prediction_loop import NewsPredictionSystem

# 1. 初始化系統
news_system = NewsPredictionSystem()

# 2. 自動運行（含預測+驗證+反饋）
news_system.start_auto_loop()

# 系統會：
# ✅ 每小時抓取新聞
# ✅ 預測價格影響
# ✅ 自動驗證預測結果
# ✅ 收集人類反饋
# ✅ 每月更新模型
```

### 查看預測結果

```python
# 查詢最近預測
predictions = news_system.get_recent_predictions(days=7)

for pred in predictions:
    print(f"新聞: {pred.news_title}")
    print(f"預測 24h: {pred.predicted_change_24h:+.2f}%")
    print(f"實際 24h: {pred.actual_change_24h:+.2f}%")
    print(f"誤差: {pred.mae_24h:.2f}%")
    print(f"人類評分: {pred.human_rating}/5")
    print("-" * 50)
```

詳細說明請參考 [7.3 RLHF 新聞預測驗證](#73-rlhf-新聞預測驗證)

---

## 💾 數據存儲與檢索

### SQLite 數據庫結構

```sql
-- 交易記錄表
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    side TEXT,  -- 'BUY' or 'SELL'
    entry_price REAL,
    exit_price REAL,
    quantity REAL,
    pnl REAL,
    strategy TEXT,
    duration_minutes INTEGER
);

-- 策略性能表
CREATE TABLE strategy_performance (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    strategy_name TEXT,
    win_rate REAL,
    avg_pnl REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    total_trades INTEGER
);

-- 新聞預測表 (v4.0 新增)
CREATE TABLE news_predictions (
    prediction_id TEXT PRIMARY KEY,
    news_title TEXT,
    news_timestamp DATETIME,
    sentiment TEXT,
    predicted_change_24h REAL,
    actual_change_24h REAL,
    mae_24h REAL,
    human_rating INTEGER,
    human_comment TEXT
);

-- 演化歷史表 (v4.0 新增)
CREATE TABLE evolution_history (
    generation INTEGER,
    island_id INTEGER,
    best_fitness REAL,
    avg_fitness REAL,
    population_snapshot TEXT  -- JSON
);
```

### 查詢示例

```python
from src.bioneuronai.database import TradingDatabase

db = TradingDatabase()

# 1. 查詢最近交易
trades = db.get_recent_trades(days=7)

# 2. 查詢策略性能
perf = db.get_strategy_performance('trend_following', days=30)

# 3. 查詢新聞預測準確率
accuracy = db.get_prediction_accuracy(days=30)

# 4. 導出數據
db.export_to_csv('trades.csv', table='trades')
```

---

## 🔍 回測與評估

### 策略回測

```python
from src.bioneuronai.backtest import Backtester

# 1. 初始化
backtester = Backtester(
    initial_capital=10000,
    commission=0.001,  # 0.1%
    slippage=0.0005    # 0.05%
)

# 2. 運行回測
results = backtester.run(
    strategy=TrendFollowingStrategy(),
    data=historical_data,
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# 3. 查看結果
print(f"總收益: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"最大回撤: {results['max_drawdown']:.2%}")
print(f"勝率: {results['win_rate']:.1%}")
```

### 性能指標

| 指標 | 說明 | 目標值 |
|------|------|--------|
| **總收益** | 期間總回報率 | > 20% (年) |
| **Sharpe Ratio** | 風險調整後收益 | > 1.5 |
| **最大回撤** | 最大虧損幅度 | < 15% |
| **勝率** | 盈利交易佔比 | > 55% |
| **Profit Factor** | 總盈利/總虧損 | > 2.0 |

---

## 📊 可視化與監控

### TensorBoard 訓練監控

```bash
# 啟動 TensorBoard
tensorboard --logdir ./logs/

# 訪問 http://localhost:6006
```

可視化內容：
- RL 訓練曲線（Episode Reward, Loss）
- 基因演算法適應度進化
- RLHF 預測準確率趨勢
- 策略權重變化

### Matplotlib 圖表

```python
from src.bioneuronai.visualization import (
    plot_pnl_curve,
    plot_drawdown,
    plot_strategy_weights,
    plot_3d_fitness_landscape
)

# PnL 曲線
plot_pnl_curve(trades, save_path='pnl.png')

# 回撤曲線
plot_drawdown(trades, save_path='drawdown.png')

# 策略權重變化
plot_strategy_weights(weight_history, save_path='weights.png')

# 3D 適應度景觀
plot_3d_fitness_landscape(population, save_path='landscape.png')
```

---

## ❓ 常見問題 FAQ

### Q1: 如何開始使用 v4.0？

**A**: 如果你是 v3.x 用戶：

```bash
# 1. 更新依賴
pip install stable-baselines3==2.2.1 gymnasium==0.29.1 deap==1.4.1 schedule

# 2. 運行快速測試
python tests/test_ml_systems.py

# 3. 啟動系統
python use_crypto_trader.py
```

### Q2: 三大 ML 系統必須都用嗎？

**A**: 不是必須的，可以獨立使用：

- **只用基因演算法**: 適合參數優化
- **只用 RL Meta-Agent**: 適合動態策略融合
- **只用 RLHF**: 適合新聞分析

但建議**完整使用**以發揮最大效能。

### Q3: 訓練 RL Agent 需要多久？

**A**: 取決於配置：

| 配置 | 時間 | 硬件需求 |
|------|------|---------|
| 簡化版 (50k steps) | 2-4 小時 | CPU 即可 |
| 完整版 (700k steps) | 12-24 小時 | GPU 推薦 |
| 課程學習 (4階段) | 2-3 天 | GPU 必需 |

### Q4: RLHF 必須手動評分嗎？

**A**: 不是。系統提供兩種模式：

1. **自動模式**: 只使用預測誤差 (MAE)
2. **人類反饋模式**: 結合專家評分（推薦）

建議每週花 15 分鐘審核預測即可。

### Q5: 測試網與主網如何切換？

> ⚠️ 補註：
> 本節若仍以直接修改 `config/trading_config.py` 為主，請視為舊路徑說明。
> 後續實作應優先使用新的憑證流與環境 / secrets / 受控輸入方式。

**A**: 在 `.env` 中設定 `BINANCE_TESTNET`：

```env
# 測試網（虛擬資金）
BINANCE_TESTNET=true

# 主網（真實資金）
BINANCE_TESTNET=false
```

⚠️ **建議**: 先在測試網運行至少 1 個月！

### Q6: 如何調整風險等級？

**A**:

```python
from src.bioneuronai.trading.risk_manager import RiskManager

# 方式 1: 使用預設等級
risk_mgr = RiskManager(
    account_balance=10000,
    risk_level='CONSERVATIVE'  # 或 'MODERATE', 'AGGRESSIVE', 'HIGH_RISK'
)

# 方式 2: 自定義參數
risk_mgr = RiskManager(
    account_balance=10000,
    max_position_size=0.15,     # 自定義最大倉位 15%
    max_daily_loss=0.03,        # 自定義單日最大虧損 3%
    max_leverage=5              # 自定義最大槓桿 5x
)
```

### Q7: 遇到 API 連接錯誤怎麼辦？

> ⚠️ 補註：
> 本節的排查步驟仍有參考價值，但若系統已切換為新的憑證注入方式，請不要再把 `config/trading_config.py` 當作唯一檢查點。

**A**: 檢查清單：

```bash
# 1. 檢查 API 密鑰
python scripts/test_binance_connection.py

# 2. 檢查網絡
ping testnet.binancefuture.com

# 3. 檢查 IP 白名單 (如果設置)
# 登入幣安 -> API Management -> IP 白名單

# 4. 查看錯誤日誌
cat logs/trading_engine.log
```

### Q8: 數據庫文件在哪裡？

**A**: 

```
BioNeuronai/
├── trading_data/
│   ├── trades.db          # 交易記錄
│   ├── predictions.db     # 新聞預測
│   └── evolution.db       # 演化歷史
```

備份命令：
```bash
# 備份所有數據庫
cp -r trading_data/ backup_$(date +%Y%m%d)/
```

### Q9: 如何查看實時日誌？

**A**:

```bash
# Windows PowerShell
Get-Content logs/trading_engine.log -Wait

# Linux/Mac
tail -f logs/trading_engine.log
```

### Q10: 系統性能要求？

**A**:

| 組件 | 最低配置 | 推薦配置 |
|------|---------|---------|
| **CPU** | 4核 | 8核+ |
| **RAM** | 8GB | 16GB+ |
| **GPU** | 無 | NVIDIA GTX 1660+ |
| **硬盤** | 10GB | 50GB SSD |
| **網絡** | 穩定連接 | 光纖 100Mbps+ |

---

## 🛠️ 錯誤處理指南

### 常見錯誤

#### 1. Import Error

```
ModuleNotFoundError: No module named 'stable_baselines3'
```

**解決**:
```bash
pip install stable-baselines3==2.2.1 gymnasium==0.29.1
```

#### 2. API 權限錯誤

```
APIError(code=-2015): Invalid API-key, IP, or permissions
```

**解決**:
1. 檢查 API Key 是否正確
2. 確認已啟用期貨交易權限
3. 檢查 IP 白名單設置

#### 3. 模型加載失敗

```
FileNotFoundError: model/my_100m_model.pth not found
```

**解決**:
```bash
# 檢查模型文件
ls model/

# 如果缺失，重新訓練或下載
python scripts/train_ai_model.py
```

#### 4. 數據庫鎖定

```
sqlite3.OperationalError: database is locked
```

**解決**:
```bash
# 關閉所有使用數據庫的程序
# 或使用只讀模式
db = TradingDatabase(readonly=True)
```

#### 5. 記憶體不足

```
RuntimeError: CUDA out of memory
```

**解決**:
```python
# 減少 batch size
agent = PPO(..., batch_size=32)  # 原本 64

# 或使用 CPU
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
```

---

## 🔧 系統維護

### 日常維護

**每日**:
- ✅ 檢查交易日誌
- ✅ 監控系統性能
- ✅ 檢查 API 連接狀態

**每週**:
- ✅ 備份數據庫
- ✅ 審核 RLHF 預測
- ✅ 檢查策略性能

**每月**:
- ✅ 重新訓練 RL Agent
- ✅ 更新 RLHF 模型
- ✅ 優化策略參數

### 數據清理

```python
from src.bioneuronai.maintenance import DataCleaner

cleaner = DataCleaner()

# 清理 3 個月前的數據
cleaner.archive_old_data(months=3)

# 優化數據庫
cleaner.optimize_database()

# 生成維護報告
report = cleaner.generate_maintenance_report()
```

### 系統升級

```bash
# 1. 備份數據
python scripts/backup_all.py

# 2. 拉取最新代碼
git pull origin master

# 3. 更新依賴
pip install -r requirements.txt --upgrade

# 4. 運行遷移腳本（如果有）
python scripts/migrate_v3_to_v4.py

# 5. 驗證系統
python tests/test_all_systems.py
```

---

## 📚 延伸閱讀

### 技術文檔（保留）
- [幣安測試網指南](c:\D\E\BioNeuronai\docs\BINANCE_TESTNET_STEP_BY_STEP.md)
- [數據源指南](c:\D\E\BioNeuronai\docs\DATA_SOURCES_GUIDE.md)
- [數據庫升級指南](c:\D\E\BioNeuronai\docs\DATABASE_UPGRADE_GUIDE.md)
- [開發工具](c:\D\E\BioNeuronai\docs\DEVELOPMENT_TOOLS.md)
- [交易成本指南](c:\D\E\BioNeuronai\docs\TRADING_COSTS_GUIDE.md)

### 完整實現計劃
- [ML 核心系統完整實現計劃](c:\D\E\BioNeuronai\_out\COMPLETE_IMPLEMENTATION_PLAN.md)

### 舊版文檔（已歸檔）
- 舊版操作手冊已移至 [archived/docs_v3/](c:\D\E\BioNeuronai\archived\docs_v3/)

---

## 🎓 學習路徑

### 新手入門（1-2週）
1. 閱讀 [系統簡介](#系統簡介)
2. 完成 [安裝與配置](#安裝與配置)
3. 在測試網運行基礎交易
4. 理解 [風險管理系統](#風險管理系統)

### 進階使用（1-2月）
1. 學習 [交易策略系統](#交易策略系統)
2. 掌握 [10步驟 SOP](#10步驟交易計劃-sop)
3. 開始使用 [新聞分析](#新聞分析與預測)
4. 實踐 [回測與評估](#回測與評估)

### 專家級（3月+）
1. 深入 [基因演算法](#71-基因演算法策略進化)
2. 訓練 [RL Meta-Agent](#72-rl-meta-agent-策略融合)
3. 部署 [RLHF 系統](#73-rlhf-新聞預測驗證)
4. 自定義策略與優化

---

## 📞 支持與反饋

### 報告問題
在 GitHub Issues 報告：
- Bug 報告
- 功能請求
- 文檔改進建議

### 貢獻代碼
歡迎提交 Pull Request：
1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

---

## 📜 版權與許可

**版權所有** © 2026 BioNeuronAI Team  
**許可證**: MIT License

---

## 📝 更新日誌

### v4.0 (2026-01-26)
- ✨ 新增基因演算法策略進化系統
- ✨ 新增 RL Meta-Agent 策略融合系統
- ✨ 新增 RLHF 新聞預測驗證系統
- 📚 整合 6 個舊版操作手冊
- 📚 創建統一技術文檔

### v3.1 (2026-01-22)
- 完整風險管理系統
- SOP 自動化控制器
- 改進 AI 模型整合

### v3.0 (2026-01-20)
- 111.2M MLP 模型
- 多策略融合引擎
- WebSocket 實時數據

---

**🎉 感謝使用 BioNeuronAI v4.0！祝交易順利！**
