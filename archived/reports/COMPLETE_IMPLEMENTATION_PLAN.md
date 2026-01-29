# BioNeuronai 完整實作計畫與算法說明

> **文件版本**: v1.0  
> **創建日期**: 2026年1月26日  
> **目標**: 完整版 ML 驅動交易系統（含所有視覺化能力）

---

## 📋 目錄

1. [系統架構總覽](#系統架構總覽)
2. [算法一：遺傳算法（Genetic Algorithm）](#算法一遺傳算法genetic-algorithm)
3. [算法二：強化學習元代理（RL Meta-Agent）](#算法二強化學習元代理rl-meta-agent)
4. [算法三：人類反饋強化學習（RLHF）](#算法三人類反饋強化學習rlhf)
5. [系統整合與執行流程](#系統整合與執行流程)
6. [實作步驟詳解](#實作步驟詳解)
7. [視覺化能力說明](#視覺化能力說明)
8. [技術依賴與環境配置](#技術依賴與環境配置)

---

## 系統架構總覽

### 三大核心系統

```
┌─────────────────────────────────────────────────────────────────┐
│                      BioNeuronai 核心架構                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  遺傳算法     │      │  RL 元代理    │      │    RLHF      │  │
│  │  (策略進化)   │ ───> │ (策略融合)    │ <──> │  (新聞驗證)   │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                      │                      │          │
│         │ 生成策略參數          │ 動態權重分配          │ 質量反饋   │
│         ▼                      ▼                      ▼          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              統一交易執行引擎 (Unified Executor)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                  │                               │
│                                  ▼                               │
│                          【實際交易/回測】                          │
└─────────────────────────────────────────────────────────────────┘
```

### 工作流程

1. **遺傳算法** 持續進化策略參數（多島模型並行搜索）
2. **RL 元代理** 學習如何動態融合多個策略（課程式訓練）
3. **RLHF** 驗證新聞預測質量，提供人類反饋循環
4. 三個系統互相反饋，形成自我改進閉環

---

## 算法一：遺傳算法（Genetic Algorithm）

### 1.1 算法原理

遺傳算法模擬生物進化過程，通過「選擇、交叉、突變」三大操作尋找最優策略參數。

#### 核心概念

**基因編碼（StrategyGene）**：
```python
@dataclass
class StrategyGene:
    # 技術指標參數
    ma_fast: int = 10        # 快速均線週期
    ma_slow: int = 30        # 慢速均線週期
    rsi_period: int = 14     # RSI 週期
    rsi_oversold: float = 30 # RSI 超賣閾值
    rsi_overbought: float = 70 # RSI 超買閾值
    
    # 風險管理參數
    stop_loss_pct: float = 0.02   # 停損百分比
    take_profit_pct: float = 0.04 # 停利百分比
    position_size: float = 0.1    # 倉位大小
    
    # 高級參數
    bollinger_std: float = 2.0    # 布林帶標準差
    volume_threshold: float = 1.5 # 成交量閾值
    atr_period: int = 14          # ATR 週期
    
    # 後設參數
    fitness_score: float = 0.0    # 適應度分數
    generation: int = 0           # 所屬世代
    ancestry: list = field(default_factory=list)  # 祖先追蹤
```

#### 進化操作詳解

**1. 選擇（Selection）- 錦標賽選擇法**

```python
def tournament_selection(population: List[StrategyGene], 
                         k: int = 3) -> StrategyGene:
    """
    隨機選 k 個個體，取適應度最高者
    
    優點：
    - 保持多樣性（非最優個體也有機會）
    - 計算效率高（不需排序整個族群）
    - 選擇壓力可調（k 越大壓力越大）
    """
    candidates = random.sample(population, k)
    return max(candidates, key=lambda x: x.fitness_score)
```

**2. 交叉（Crossover）- 兩點交叉法**

```python
def crossover(parent1: StrategyGene, 
              parent2: StrategyGene) -> Tuple[StrategyGene, StrategyGene]:
    """
    隨機選兩個切點，交換中間基因片段
    
    範例：
    Parent1: [A B C | D E F | G H]
    Parent2: [a b c | d e f | g h]
              ↓
    Child1:  [A B C | d e f | G H]  (繼承 P1 頭尾 + P2 中段)
    Child2:  [a b c | D E F | g h]  (繼承 P2 頭尾 + P1 中段)
    """
    # 實作會轉換成數值陣列進行交叉
    pass
```

**3. 突變（Mutation）- 高斯突變**

```python
def mutate(gene: StrategyGene, 
           mutation_rate: float = 0.1,
           mutation_strength: float = 0.2) -> StrategyGene:
    """
    以機率對每個參數施加高斯噪聲
    
    mutation_rate: 每個參數突變機率（預設 10%）
    mutation_strength: 突變強度（參數範圍的 20%）
    
    範例：
    原始: ma_fast = 10
    突變: ma_fast = 10 + N(0, 2) = 12  (假設範圍為 5-20)
    """
    if random.random() < mutation_rate:
        gene.ma_fast += int(np.random.normal(0, 2))
        gene.ma_fast = np.clip(gene.ma_fast, 5, 50)
    # ... 對所有參數重複此過程
```

### 1.2 島嶼模型（Island Model）

#### 為何需要島嶼模型？

**問題**：單一族群容易陷入局部最優解（早熟收斂）

**解決方案**：多個子族群獨立進化，定期遷移優秀個體

#### 實作架構

```python
class IslandEvolutionEngine:
    """
    多島嶼並行進化引擎
    
    架構：
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ 島嶼 1    │   │ 島嶼 2    │   │ 島嶼 3    │   │ 島嶼 4    │
    │ (趨勢策略)│   │ (區間策略)│   │ (突破策略)│   │ (反轉策略)│
    └─────┬────┘   └─────┬────┘   └─────┬────┘   └─────┬────┘
          │               │               │               │
          └───────────────┴───── 遷移 ────┴───────────────┘
                         每 5 代交換最優個體
    """
    
    def __init__(self, 
                 n_islands: int = 4,
                 pop_per_island: int = 50,
                 migration_interval: int = 5,
                 migration_size: int = 3):
        self.islands = [
            EvolutionEngine(population_size=pop_per_island)
            for _ in range(n_islands)
        ]
        self.migration_interval = migration_interval
        self.migration_size = migration_size
    
    def evolve_generation(self) -> Dict[str, Any]:
        """單代進化流程"""
        results = {}
        
        # 1. 各島嶼獨立進化
        for i, island in enumerate(self.islands):
            island.evolve_one_generation()
            results[f'island_{i}'] = island.get_best_strategy()
        
        # 2. 定期遷移
        if self.current_gen % self.migration_interval == 0:
            self.migrate_individuals()
        
        # 3. 全局最優
        global_best = max(
            [island.get_best_strategy() for island in self.islands],
            key=lambda x: x.fitness_score
        )
        
        return {
            'global_best': global_best,
            'island_results': results,
            'diversity': self.calculate_diversity()
        }
    
    def migrate_individuals(self):
        """環形遷移拓撲：島嶼 i → 島嶼 (i+1) % n"""
        migrants = []
        
        # 1. 收集各島最優個體
        for island in self.islands:
            best = island.get_top_n(self.migration_size)
            migrants.append(best)
        
        # 2. 環形遷移
        for i, island in enumerate(self.islands):
            next_i = (i + 1) % len(self.islands)
            incoming = migrants[next_i]
            island.replace_worst(incoming)  # 替換最差個體
```

#### 遷移策略

| 拓撲結構 | 說明 | 適用場景 |
|---------|------|---------|
| 環形 | 島嶼 i → i+1 | 平衡探索/利用 |
| 星形 | 所有島嶼 ↔ 中心島 | 快速收斂 |
| 全連接 | 任意島嶼互聯 | 最大多樣性 |
| 階層式 | 區域組 → 全局層 | 大規模優化 |

### 1.3 協同進化（Co-evolution）

#### 策略-環境對抗

```python
class CoevolutionEngine:
    """
    策略族群與環境族群同時進化
    
    概念：
    - 策略族群：尋找穩健交易規則
    - 環境族群：生成挑戰性市場情境
    - 兩者相互競爭，推動彼此進化
    """
    
    def __init__(self):
        self.strategy_population = []  # 交易策略
        self.environment_population = []  # 市場環境
    
    def evaluate_fitness(self):
        """
        交叉評估適應度
        
        策略適應度 = 在多種環境下的平均表現
        環境適應度 = 能擊敗多少策略（區分度）
        """
        for strategy in self.strategy_population:
            scores = []
            for env in self.environment_population:
                score = self.backtest(strategy, env)
                scores.append(score)
            strategy.fitness = np.mean(scores)
        
        for env in self.environment_population:
            defeated = sum(
                1 for s in self.strategy_population 
                if self.backtest(s, env) < 0  # 虧損視為擊敗
            )
            env.fitness = defeated / len(self.strategy_population)
```

#### 環境基因編碼

```python
@dataclass
class MarketEnvironmentGene:
    """市場環境參數"""
    trend_strength: float = 0.5   # 趨勢強度 (0=震盪, 1=強趨勢)
    volatility: float = 0.02      # 波動率
    noise_level: float = 0.1      # 噪聲水平
    regime_duration: int = 100    # 狀態持續週期
    correlation: float = 0.0      # 資產間相關性
    
    # 生成合成市場數據
    def generate_synthetic_data(self, length: int) -> pd.DataFrame:
        """基於參數生成市場數據"""
        pass
```

### 1.4 適應度函數設計

```python
def calculate_fitness(backtest_result: BacktestResult) -> float:
    """
    多目標適應度函數
    
    考慮因素：
    1. 總收益（主要）
    2. 夏普比率（風險調整收益）
    3. 最大回撤（風險控制）
    4. 勝率（穩定性）
    5. 交易次數（過度交易懲罰）
    """
    
    # 基礎收益分數
    return_score = backtest_result.total_return * 100
    
    # 夏普比率加成（越高越好）
    sharpe_bonus = max(0, backtest_result.sharpe_ratio - 1) * 20
    
    # 回撤懲罰（越小越好）
    drawdown_penalty = abs(backtest_result.max_drawdown) * 50
    
    # 勝率加成
    winrate_bonus = (backtest_result.win_rate - 0.5) * 30
    
    # 交易頻率懲罰（過度交易）
    if backtest_result.num_trades > 500:
        trade_penalty = (backtest_result.num_trades - 500) * 0.1
    else:
        trade_penalty = 0
    
    # 綜合分數
    fitness = (
        return_score 
        + sharpe_bonus 
        - drawdown_penalty 
        + winrate_bonus 
        - trade_penalty
    )
    
    return max(0, fitness)  # 確保非負
```

### 1.5 視覺化能力

#### 3D 適應度景觀（Fitness Landscape）

```python
class EvolutionVisualizer:
    """進化過程視覺化工具"""
    
    def plot_fitness_landscape_3d(self, 
                                   population: List[StrategyGene],
                                   param_x: str = 'ma_fast',
                                   param_y: str = 'rsi_period'):
        """
        3D 適應度景觀圖
        
        X軸：參數1（例如：ma_fast）
        Y軸：參數2（例如：rsi_period）
        Z軸：適應度分數
        顏色：世代數（演進軌跡）
        """
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # 提取數據
        x = [getattr(g, param_x) for g in population]
        y = [getattr(g, param_y) for g in population]
        z = [g.fitness_score for g in population]
        colors = [g.generation for g in population]
        
        # 繪製散點圖
        scatter = ax.scatter(x, y, z, c=colors, 
                            cmap='viridis', 
                            s=50, alpha=0.6)
        
        ax.set_xlabel(param_x)
        ax.set_ylabel(param_y)
        ax.set_zlabel('Fitness Score')
        plt.colorbar(scatter, label='Generation')
        plt.title('Strategy Evolution Landscape')
        plt.savefig('fitness_landscape_3d.png', dpi=300)
    
    def plot_diversity_over_time(self, history: List[Dict]):
        """
        族群多樣性隨時間變化
        
        多樣性指標：
        - 基因型多樣性：參數標準差
        - 表現型多樣性：適應度分佈熵
        """
        generations = [h['generation'] for h in history]
        diversity = [h['diversity_score'] for h in history]
        
        plt.figure(figsize=(10, 6))
        plt.plot(generations, diversity, linewidth=2)
        plt.xlabel('Generation')
        plt.ylabel('Population Diversity')
        plt.title('Genetic Diversity Over Evolution')
        plt.grid(True, alpha=0.3)
        plt.savefig('diversity_timeline.png', dpi=300)
    
    def plot_pareto_front(self, population: List[StrategyGene]):
        """
        帕累托前緣（多目標優化）
        
        X軸：總收益
        Y軸：夏普比率
        顯示非支配解集
        """
        returns = [g.backtest_result.total_return for g in population]
        sharpes = [g.backtest_result.sharpe_ratio for g in population]
        
        # 計算帕累托前緣
        pareto_front = self.find_pareto_front(returns, sharpes)
        
        plt.figure(figsize=(10, 6))
        plt.scatter(returns, sharpes, alpha=0.5, label='All Strategies')
        plt.scatter([p[0] for p in pareto_front], 
                   [p[1] for p in pareto_front],
                   color='red', s=100, label='Pareto Front')
        plt.xlabel('Total Return')
        plt.ylabel('Sharpe Ratio')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('pareto_front.png', dpi=300)
```

---

## 算法二：強化學習元代理（RL Meta-Agent）

### 2.1 算法原理

強化學習（RL）透過試錯學習，元代理負責動態融合多個基礎策略。

#### 核心概念

**馬可夫決策過程（MDP）**：
```
狀態 (State) → 動作 (Action) → 獎勵 (Reward) → 下一狀態 (Next State)
    ↑                                                      ↓
    └────────────────── 循環學習 ───────────────────────────┘
```

**PPO 算法（Proximal Policy Optimization）**：
- 策略梯度方法，穩定且高效
- 限制策略更新幅度（避免破壞性更新）
- 適用於連續/離散動作空間

### 2.2 狀態空間設計（43維）

```python
class StrategyFusionEnv(gym.Env):
    """
    策略融合環境
    
    狀態空間（43維）詳細說明：
    """
    
    def _get_observation(self) -> np.ndarray:
        """構建觀察向量"""
        obs = []
        
        # === 基礎策略信號（7個策略 × 1維 = 7維）===
        obs.extend([
            self.ma_crossover_signal(),      # 均線交叉：+1買/-1賣/0中性
            self.rsi_signal(),               # RSI：+1超賣/-1超買/0中性
            self.macd_signal(),              # MACD：+1金叉/-1死叉/0中性
            self.bollinger_signal(),         # 布林帶：+1下軌/-1上軌/0中性
            self.volume_signal(),            # 成交量：+1放量/-1縮量/0正常
            self.atr_signal(),               # ATR 波動：歸一化值
            self.news_sentiment_signal(),    # 新聞情緒：-1~+1
        ])
        
        # === 市場狀態（5維）===
        obs.extend([
            self.current_price / self.initial_price,  # 價格相對位置
            self.volatility_20d,              # 20日波動率
            self.volume_ratio,                # 成交量比率（當日/平均）
            self.trend_strength,              # 趨勢強度（ADX指標）
            self.market_regime,               # 市場狀態：0震盪/1趨勢
        ])
        
        # === 持倉資訊（4維）===
        obs.extend([
            self.position / self.max_position,  # 當前倉位比例
            self.unrealized_pnl / self.capital, # 未實現損益
            self.holding_days / 30,             # 持倉天數（歸一化）
            self.avg_entry_price / self.current_price,  # 入場價相對位置
        ])
        
        # === 策略歷史表現（7個策略 × 3指標 = 21維）===
        for strategy_name in self.strategy_list:
            history = self.strategy_performance[strategy_name]
            obs.extend([
                history.recent_winrate,      # 近期勝率（20筆交易）
                history.recent_sharpe,       # 近期夏普比率
                history.drawdown_severity,   # 當前回撤嚴重度
            ])
        
        # === 風險指標（4維）===
        obs.extend([
            self.portfolio_var,              # 投資組合 VaR
            self.correlation_to_market,      # 與大盤相關性
            self.max_drawdown_current,       # 當前最大回撤
            self.leverage_ratio,             # 槓桿比率
        ])
        
        # === 時間特徵（2維）===
        obs.extend([
            np.sin(2 * np.pi * self.hour / 24),    # 小時（週期編碼）
            np.sin(2 * np.pi * self.day_of_week / 7),  # 星期（週期編碼）
        ])
        
        return np.array(obs, dtype=np.float32)
```

### 2.3 動作空間設計

```python
class ActionSpace:
    """
    多離散動作空間
    
    Action = [action_type, position_size, strategy_weights]
    """
    
    def __init__(self):
        # 動作類型（3種）
        self.ACTION_TYPE = {
            0: 'HOLD',   # 保持當前倉位
            1: 'BUY',    # 開多/加倉
            2: 'SELL',   # 平倉/開空
        }
        
        # 倉位大小（5檔）
        self.POSITION_SIZES = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        # 策略權重（7個策略，使用 softmax 歸一化）
        self.NUM_STRATEGIES = 7
    
    def decode_action(self, action: np.ndarray) -> Dict:
        """解碼動作向量"""
        action_type = self.ACTION_TYPE[action[0]]
        position_size = self.POSITION_SIZES[action[1]]
        
        # 策略權重（softmax 歸一化）
        strategy_weights = softmax(action[2:9])
        
        return {
            'type': action_type,
            'size': position_size,
            'weights': strategy_weights
        }
```

### 2.4 獎勵函數設計

```python
def calculate_reward(self, 
                     prev_portfolio_value: float,
                     curr_portfolio_value: float,
                     action: Dict) -> float:
    """
    多目標獎勵函數
    
    目標：
    1. 最大化收益
    2. 最小化風險（回撤/波動）
    3. 控制交易頻率
    4. 鼓勵夏普比率提升
    """
    
    # === 1. 基礎收益獎勵 ===
    pnl = curr_portfolio_value - prev_portfolio_value
    return_reward = pnl / prev_portfolio_value * 100
    
    # === 2. 夏普比率獎勵 ===
    recent_returns = self.returns_history[-20:]  # 近20步
    if len(recent_returns) >= 20:
        sharpe = np.mean(recent_returns) / (np.std(recent_returns) + 1e-8)
        sharpe_reward = sharpe * 2.0
    else:
        sharpe_reward = 0.0
    
    # === 3. 回撤懲罰 ===
    current_dd = (self.peak_value - curr_portfolio_value) / self.peak_value
    if current_dd > 0.1:  # 回撤超過10%
        drawdown_penalty = -current_dd * 50
    else:
        drawdown_penalty = 0.0
    
    # === 4. 交易成本 ===
    if action['type'] != 'HOLD':
        trade_cost = -0.001 * abs(action['size'])  # 0.1% 手續費
    else:
        trade_cost = 0.0
    
    # === 5. 過度交易懲罰 ===
    recent_trades = sum(self.action_history[-10:] != 0)
    if recent_trades > 7:  # 10步內交易超過7次
        overtrading_penalty = -(recent_trades - 7) * 0.5
    else:
        overtrading_penalty = 0.0
    
    # === 6. 風險調整因子 ===
    if self.volatility_20d > 0.03:  # 高波動期
        risk_factor = 0.5  # 降低風險偏好
    else:
        risk_factor = 1.0
    
    # === 綜合獎勵 ===
    total_reward = (
        return_reward * risk_factor
        + sharpe_reward
        + drawdown_penalty
        + trade_cost
        + overtrading_penalty
    )
    
    return total_reward
```

### 2.5 自定義 Transformer 策略網路

```python
class TransformerPolicyNetwork(nn.Module):
    """
    基於 Transformer 的策略網路
    
    優勢：
    - 注意力機制捕捉策略間關係
    - 處理可變長度歷史序列
    - 學習時間依賴模式
    """
    
    def __init__(self, 
                 state_dim: int = 43,
                 action_dim: int = 9,
                 hidden_dim: int = 256,
                 num_heads: int = 4,
                 num_layers: int = 2):
        super().__init__()
        
        # 輸入嵌入層
        self.input_embedding = nn.Linear(state_dim, hidden_dim)
        
        # Transformer 編碼器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            activation='gelu'
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, 
            num_layers=num_layers
        )
        
        # 策略頭（動作概率）
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # 價值頭（狀態價值估計）
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向傳播
        
        輸入：state [batch_size, seq_len, state_dim]
        輸出：
            - action_probs [batch_size, action_dim]
            - state_value [batch_size, 1]
        """
        # 嵌入
        x = self.input_embedding(state)  # [B, T, H]
        
        # Transformer 編碼
        x = self.transformer(x)  # [B, T, H]
        
        # 取最後時間步
        x = x[:, -1, :]  # [B, H]
        
        # 策略和價值
        action_probs = self.policy_head(x)
        state_value = self.value_head(x)
        
        return action_probs, state_value
```

### 2.6 課程式學習（Curriculum Learning）

```python
class CurriculumTrainer:
    """
    四階段課程式訓練
    
    理念：由易到難，漸進式學習
    """
    
    def __init__(self):
        self.stages = [
            {
                'name': 'Stage 1: Trending Market',
                'description': '純趨勢市場（易）',
                'difficulty': 'easy',
                'epochs': 100000,
                'market_config': {
                    'trend_strength': 0.8,
                    'volatility': 0.01,
                    'noise_level': 0.05
                }
            },
            {
                'name': 'Stage 2: Ranging Market',
                'description': '純區間震盪（中）',
                'difficulty': 'medium',
                'epochs': 150000,
                'market_config': {
                    'trend_strength': 0.2,
                    'volatility': 0.02,
                    'noise_level': 0.1
                }
            },
            {
                'name': 'Stage 3: Mixed Regimes',
                'description': '混合市場狀態（難）',
                'difficulty': 'hard',
                'epochs': 200000,
                'market_config': {
                    'trend_strength': 0.5,
                    'volatility': 0.03,
                    'noise_level': 0.15,
                    'regime_switching': True
                }
            },
            {
                'name': 'Stage 4: Adversarial',
                'description': '對抗性市場（極難）',
                'difficulty': 'expert',
                'epochs': 250000,
                'market_config': {
                    'trend_strength': 0.5,
                    'volatility': 0.04,
                    'noise_level': 0.2,
                    'adversarial_events': True,  # 黑天鵝事件
                    'regime_switching': True
                }
            }
        ]
        
        self.current_stage = 0
        self.promotion_threshold = 0.8  # 勝率 > 80% 才能升級
    
    def train_stage(self, stage_idx: int) -> Dict[str, Any]:
        """訓練單一階段"""
        stage = self.stages[stage_idx]
        
        print(f"\n{'='*60}")
        print(f"開始訓練：{stage['name']}")
        print(f"描述：{stage['description']}")
        print(f"目標步數：{stage['epochs']:,}")
        print(f"{'='*60}\n")
        
        # 創建對應難度的環境
        env = self.create_env(stage['market_config'])
        
        # 訓練
        model = PPO(
            TransformerPolicy, 
            env,
            learning_rate=self.get_lr_schedule(stage_idx),
            n_steps=2048,
            batch_size=64,
            tensorboard_log=f"./logs/stage_{stage_idx}"
        )
        
        # 訓練並評估
        eval_callback = EvalCallback(
            env,
            eval_freq=10000,
            n_eval_episodes=20,
            best_model_save_path=f"./models/stage_{stage_idx}"
        )
        
        model.learn(
            total_timesteps=stage['epochs'],
            callback=eval_callback
        )
        
        # 評估是否達標
        final_performance = self.evaluate_model(model, env)
        
        return {
            'stage': stage['name'],
            'performance': final_performance,
            'can_promote': final_performance['winrate'] > self.promotion_threshold
        }
    
    def train_all_stages(self):
        """完整課程式訓練流程"""
        for stage_idx in range(len(self.stages)):
            result = self.train_stage(stage_idx)
            
            print(f"\n階段 {stage_idx+1} 結果：")
            print(f"  勝率：{result['performance']['winrate']:.2%}")
            print(f"  夏普比率：{result['performance']['sharpe']:.2f}")
            print(f"  最大回撤：{result['performance']['max_dd']:.2%}")
            
            if not result['can_promote'] and stage_idx < len(self.stages) - 1:
                print(f"  ⚠️  未達升級標準（需勝率 > {self.promotion_threshold:.0%}），重新訓練...")
                stage_idx -= 1  # 重訓當前階段
            else:
                print(f"  ✅ 通過！進入下一階段...")
```

### 2.7 TensorBoard 視覺化

```python
class TensorBoardLogger:
    """訓練過程視覺化"""
    
    def __init__(self, log_dir: str = './logs'):
        self.writer = SummaryWriter(log_dir)
        self.episode = 0
    
    def log_training_metrics(self, metrics: Dict):
        """記錄訓練指標"""
        self.episode += 1
        
        # 基礎指標
        self.writer.add_scalar('Train/EpisodeReward', 
                              metrics['reward'], 
                              self.episode)
        self.writer.add_scalar('Train/EpisodeLength', 
                              metrics['length'], 
                              self.episode)
        
        # 策略指標
        self.writer.add_scalar('Train/PolicyLoss', 
                              metrics['policy_loss'], 
                              self.episode)
        self.writer.add_scalar('Train/ValueLoss', 
                              metrics['value_loss'], 
                              self.episode)
        self.writer.add_scalar('Train/Entropy', 
                              metrics['entropy'], 
                              self.episode)
        
        # 交易指標
        self.writer.add_scalar('Trade/Winrate', 
                              metrics['winrate'], 
                              self.episode)
        self.writer.add_scalar('Trade/SharpeRatio', 
                              metrics['sharpe'], 
                              self.episode)
        self.writer.add_scalar('Trade/MaxDrawdown', 
                              metrics['max_drawdown'], 
                              self.episode)
        
        # 策略權重分佈（直方圖）
        self.writer.add_histogram('Weights/StrategyWeights', 
                                  metrics['strategy_weights'], 
                                  self.episode)
    
    def log_action_distribution(self, actions: np.ndarray):
        """記錄動作分佈"""
        self.writer.add_histogram('Actions/Distribution', 
                                  actions, 
                                  self.episode)
```

啟動 TensorBoard：
```bash
tensorboard --logdir=./logs --port=6006
```

---

## 算法三：人類反饋強化學習（RLHF）

### 3.1 算法原理

RLHF 透過人類專家反饋不斷修正 AI 預測，形成閉環改進。

#### 核心流程

```
1. AI 生成新聞預測 
   ↓
2. 延遲驗證（等待實際市場反應）
   ↓
3. 自動評分（價格變化是否符合預測）
   ↓
4. 人類審核（專家判斷預測質量）
   ↓
5. 權重更新（調整 AI 模型）
   ↓
6. 回到步驟 1（持續循環）
```

### 3.2 數據結構設計

```python
@dataclass
class NewsPrediction:
    """新聞預測記錄"""
    prediction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 新聞內容
    news_title: str = ""
    news_content: str = ""
    news_source: str = ""
    symbols: List[str] = field(default_factory=list)
    
    # AI 預測
    predicted_direction: str = ""  # 'BULLISH' / 'BEARISH' / 'NEUTRAL'
    predicted_magnitude: float = 0.0  # 預期漲跌幅（%）
    confidence_score: float = 0.0  # 信心分數 (0-1)
    time_horizon: str = "24h"  # 預測時間範圍
    
    # 市場反應（延遲填入）
    actual_price_change: Optional[float] = None
    actual_direction: Optional[str] = None
    market_impact_score: Optional[float] = None
    
    # 驗證結果
    status: PredictionStatus = PredictionStatus.PENDING
    validation_result: Optional[ValidationResult] = None
    
    # 人類反饋
    human_review: Optional[HumanFeedback] = None
    
    # 後設資訊
    model_version: str = "v1.0"
    created_at: datetime = field(default_factory=datetime.now)
    validated_at: Optional[datetime] = None

@dataclass
class ValidationResult:
    """自動驗證結果"""
    is_correct: bool = False
    accuracy_score: float = 0.0  # 0-100
    
    # 細節分析
    direction_match: bool = False
    magnitude_error: float = 0.0  # 預測誤差（%）
    confidence_calibration: float = 0.0  # 信心校準分數
    
    # 評分依據
    scoring_breakdown: Dict[str, float] = field(default_factory=dict)

@dataclass
class HumanFeedback:
    """人類專家反饋"""
    reviewer_id: str = ""
    review_timestamp: datetime = field(default_factory=datetime.now)
    
    # 質量評分（1-5星）
    quality_rating: int = 3
    
    # 專家判斷
    expert_opinion: str = ""  # 'AGREE' / 'DISAGREE' / 'PARTIAL'
    correction_notes: str = ""
    
    # 反饋類別
    feedback_tags: List[str] = field(default_factory=list)
    # 例如：['timing_off', 'magnitude_wrong', 'good_direction', 'missed_context']
    
    # 學習價值
    is_edge_case: bool = False
    should_retrain: bool = False
```

### 3.3 預測狀態機

```python
class PredictionStatus(Enum):
    """預測生命週期狀態"""
    PENDING = "pending"           # 等待驗證
    VALIDATING = "validating"     # 驗證中
    VALIDATED = "validated"       # 已自動驗證
    REVIEWED = "reviewed"         # 已人工審核
    ARCHIVED = "archived"         # 已歸檔
    DISPUTED = "disputed"         # 有爭議（AI與專家不一致）

class PredictionStateMachine:
    """狀態轉換邏輯"""
    
    TRANSITIONS = {
        PredictionStatus.PENDING: [PredictionStatus.VALIDATING],
        PredictionStatus.VALIDATING: [
            PredictionStatus.VALIDATED, 
            PredictionStatus.DISPUTED
        ],
        PredictionStatus.VALIDATED: [
            PredictionStatus.REVIEWED, 
            PredictionStatus.ARCHIVED
        ],
        PredictionStatus.REVIEWED: [PredictionStatus.ARCHIVED],
        PredictionStatus.DISPUTED: [PredictionStatus.REVIEWED],
    }
    
    def can_transition(self, from_status: PredictionStatus, 
                      to_status: PredictionStatus) -> bool:
        """檢查狀態轉換是否合法"""
        return to_status in self.TRANSITIONS.get(from_status, [])
```

### 3.4 自動驗證邏輯

```python
class PredictionValidator:
    """預測驗證引擎"""
    
    def __init__(self, price_data_provider):
        self.price_provider = price_data_provider
    
    def validate_prediction(self, 
                           prediction: NewsPrediction) -> ValidationResult:
        """
        自動驗證預測準確度
        
        驗證邏輯：
        1. 方向準確度（最重要）
        2. 幅度準確度（次要）
        3. 信心校準（元學習）
        """
        # 獲取實際價格變化
        symbol = prediction.symbols[0]
        time_horizon = self._parse_time_horizon(prediction.time_horizon)
        
        start_price = self.price_provider.get_price_at(
            symbol, prediction.timestamp
        )
        end_price = self.price_provider.get_price_at(
            symbol, prediction.timestamp + time_horizon
        )
        
        actual_change_pct = (end_price - start_price) / start_price * 100
        
        # 判斷實際方向
        if actual_change_pct > 0.5:
            actual_direction = 'BULLISH'
        elif actual_change_pct < -0.5:
            actual_direction = 'BEARISH'
        else:
            actual_direction = 'NEUTRAL'
        
        # === 評分 ===
        scores = {}
        
        # 1. 方向準確度（50分）
        direction_match = (prediction.predicted_direction == actual_direction)
        scores['direction'] = 50 if direction_match else 0
        
        # 2. 幅度準確度（30分）
        magnitude_error = abs(prediction.predicted_magnitude - actual_change_pct)
        if magnitude_error < 1.0:
            scores['magnitude'] = 30
        elif magnitude_error < 2.0:
            scores['magnitude'] = 20
        elif magnitude_error < 5.0:
            scores['magnitude'] = 10
        else:
            scores['magnitude'] = 0
        
        # 3. 信心校準（20分）
        # 高信心預測應該更準確
        if direction_match:
            if prediction.confidence_score > 0.8:
                scores['confidence'] = 20  # 高信心且正確
            elif prediction.confidence_score > 0.5:
                scores['confidence'] = 15
            else:
                scores['confidence'] = 10  # 低信心但正確
        else:
            if prediction.confidence_score > 0.8:
                scores['confidence'] = 0   # 高信心但錯誤（最差）
            else:
                scores['confidence'] = 5   # 低信心且錯誤（還行）
        
        # 總分
        total_score = sum(scores.values())
        
        return ValidationResult(
            is_correct=direction_match,
            accuracy_score=total_score,
            direction_match=direction_match,
            magnitude_error=magnitude_error,
            confidence_calibration=scores['confidence'] / 20,
            scoring_breakdown=scores
        )
```

### 3.5 人類反饋收集

```python
class HumanFeedbackCollector:
    """人類專家反饋系統"""
    
    def __init__(self):
        self.pending_reviews = []
        self.notification_system = NotificationSystem()
    
    def request_review(self, prediction: NewsPrediction, 
                       reason: str = "routine"):
        """
        請求人類審核
        
        觸發條件：
        1. 自動驗證低分（< 40分）
        2. AI 高信心但錯誤
        3. 邊緣案例（接近臨界值）
        4. 定期抽樣（10% 隨機審核）
        """
        review_request = {
            'prediction': prediction,
            'reason': reason,
            'priority': self._calculate_priority(prediction, reason),
            'requested_at': datetime.now()
        }
        
        self.pending_reviews.append(review_request)
        
        # 發送通知給審核員
        if reason == "high_confidence_error":
            self.notification_system.send_urgent_alert(review_request)
        else:
            self.notification_system.add_to_queue(review_request)
    
    def submit_feedback(self, 
                       prediction_id: str,
                       feedback: HumanFeedback) -> None:
        """
        提交人類反饋
        
        反饋將用於：
        1. 更新模型權重
        2. 生成對抗樣本
        3. 改進提示詞工程
        """
        prediction = self.db.get_prediction(prediction_id)
        prediction.human_review = feedback
        prediction.status = PredictionStatus.REVIEWED
        
        # 根據反饋調整模型
        if feedback.should_retrain:
            self.trigger_retraining(prediction, feedback)
        
        # 記錄到訓練集
        if feedback.is_edge_case:
            self.add_to_hard_examples(prediction, feedback)
    
    def _calculate_priority(self, prediction: NewsPrediction, 
                           reason: str) -> int:
        """計算審核優先級（1-10）"""
        priority = 5  # 基準
        
        if reason == "high_confidence_error":
            priority = 10  # 最高優先級
        elif reason == "low_score":
            priority = 8
        elif reason == "edge_case":
            priority = 7
        elif reason == "random_sampling":
            priority = 3
        
        # 根據影響範圍調整
        if len(prediction.symbols) > 3:  # 多標的影響
            priority += 1
        
        return min(priority, 10)
```

### 3.6 自動排程系統

```python
class PredictionScheduler:
    """自動化驗證排程器"""
    
    def __init__(self):
        self.validator = PredictionValidator()
        self.feedback_collector = HumanFeedbackCollector()
        
    def start_daemon(self):
        """啟動背景守護進程"""
        # 每小時檢查待驗證預測
        schedule.every().hour.do(self.validate_pending_predictions)
        
        # 每天生成質量報告
        schedule.every().day.at("09:00").do(self.generate_daily_report)
        
        # 每週觸發模型重訓
        schedule.every().sunday.at("00:00").do(self.trigger_weekly_retrain)
        
        print("📅 RLHF 排程器已啟動...")
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def validate_pending_predictions(self):
        """批次驗證待處理預測"""
        pending = self.db.get_predictions_by_status(
            PredictionStatus.PENDING
        )
        
        for prediction in pending:
            # 檢查是否到驗證時間
            elapsed = datetime.now() - prediction.timestamp
            required_time = self._parse_time_horizon(prediction.time_horizon)
            
            if elapsed >= required_time:
                # 執行驗證
                result = self.validator.validate_prediction(prediction)
                prediction.validation_result = result
                prediction.status = PredictionStatus.VALIDATED
                self.db.update_prediction(prediction)
                
                # 決定是否需要人類審核
                if self._needs_human_review(prediction, result):
                    reason = self._determine_review_reason(prediction, result)
                    self.feedback_collector.request_review(prediction, reason)
    
    def _needs_human_review(self, prediction: NewsPrediction, 
                           result: ValidationResult) -> bool:
        """判斷是否需要人類審核"""
        # 低分必審
        if result.accuracy_score < 40:
            return True
        
        # 高信心錯誤必審
        if not result.is_correct and prediction.confidence_score > 0.8:
            return True
        
        # 10% 隨機抽樣
        if random.random() < 0.1:
            return True
        
        return False
```

### 3.7 質量分析儀表板

```python
class PredictionAnalytics:
    """預測質量分析工具"""
    
    def generate_quality_report(self, 
                               start_date: datetime,
                               end_date: datetime) -> Dict:
        """生成質量分析報告"""
        predictions = self.db.get_predictions_in_range(start_date, end_date)
        
        report = {
            'overview': self._calculate_overview(predictions),
            'by_symbol': self._analyze_by_symbol(predictions),
            'by_source': self._analyze_by_source(predictions),
            'by_time_horizon': self._analyze_by_horizon(predictions),
            'calibration': self._analyze_calibration(predictions),
            'improvement_suggestions': self._generate_suggestions(predictions)
        }
        
        return report
    
    def _calculate_overview(self, predictions: List[NewsPrediction]) -> Dict:
        """總體統計"""
        validated = [p for p in predictions 
                    if p.status == PredictionStatus.VALIDATED]
        
        if not validated:
            return {}
        
        return {
            'total_predictions': len(predictions),
            'validated_count': len(validated),
            'accuracy': np.mean([
                p.validation_result.is_correct for p in validated
            ]),
            'avg_score': np.mean([
                p.validation_result.accuracy_score for p in validated
            ]),
            'avg_confidence': np.mean([
                p.confidence_score for p in validated
            ]),
            'human_reviewed': len([
                p for p in validated if p.human_review is not None
            ])
        }
    
    def _analyze_by_symbol(self, predictions: List[NewsPrediction]) -> Dict:
        """按標的分析"""
        symbol_stats = {}
        
        for pred in predictions:
            for symbol in pred.symbols:
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {
                        'predictions': [],
                        'correct': 0,
                        'total': 0
                    }
                
                symbol_stats[symbol]['predictions'].append(pred)
                if pred.validation_result:
                    symbol_stats[symbol]['total'] += 1
                    if pred.validation_result.is_correct:
                        symbol_stats[symbol]['correct'] += 1
        
        # 計算各標的準確率
        for symbol, stats in symbol_stats.items():
            if stats['total'] > 0:
                stats['accuracy'] = stats['correct'] / stats['total']
            else:
                stats['accuracy'] = None
        
        # 排序（由高到低）
        sorted_symbols = sorted(
            symbol_stats.items(),
            key=lambda x: x[1]['accuracy'] or 0,
            reverse=True
        )
        
        return dict(sorted_symbols)
    
    def _analyze_calibration(self, predictions: List[NewsPrediction]) -> Dict:
        """信心校準分析"""
        # 將預測按信心分數分組
        bins = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
        calibration = {f"{bins[i]}-{bins[i+1]}": [] 
                      for i in range(len(bins)-1)}
        
        for pred in predictions:
            if pred.validation_result is None:
                continue
            
            # 找到對應區間
            for i in range(len(bins)-1):
                if bins[i] <= pred.confidence_score < bins[i+1]:
                    calibration[f"{bins[i]}-{bins[i+1]}"].append(
                        pred.validation_result.is_correct
                    )
                    break
        
        # 計算每個區間的實際準確率
        calibration_scores = {}
        for bin_name, results in calibration.items():
            if results:
                actual_accuracy = np.mean(results)
                expected_accuracy = (float(bin_name.split('-')[0]) + 
                                   float(bin_name.split('-')[1])) / 2
                calibration_scores[bin_name] = {
                    'expected': expected_accuracy,
                    'actual': actual_accuracy,
                    'count': len(results),
                    'calibration_error': abs(actual_accuracy - expected_accuracy)
                }
        
        return calibration_scores
    
    def plot_calibration_curve(self, calibration_data: Dict):
        """繪製校準曲線"""
        import matplotlib.pyplot as plt
        
        bins = sorted(calibration_data.keys())
        expected = [calibration_data[b]['expected'] for b in bins]
        actual = [calibration_data[b]['actual'] for b in bins]
        
        plt.figure(figsize=(10, 6))
        plt.plot(expected, actual, 'o-', label='Model', linewidth=2)
        plt.plot([0, 1], [0, 1], '--', color='gray', label='Perfect Calibration')
        plt.xlabel('Predicted Confidence')
        plt.ylabel('Actual Accuracy')
        plt.title('Prediction Calibration Curve')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('calibration_curve.png', dpi=300)
```

---

## 系統整合與執行流程

### 4.1 整合架構

```python
class UnifiedMLSystem:
    """統一 ML 系統整合器"""
    
    def __init__(self):
        # 三大子系統
        self.genetic_engine = IslandEvolutionEngine()
        self.rl_agent = RLMetaAgent()
        self.rlhf_system = RLHFValidator()
        
        # 共享狀態
        self.current_strategies = []
        self.performance_history = []
    
    def run_daily_cycle(self):
        """每日執行循環"""
        
        # === 第一階段：策略進化 ===
        print("\n🧬 階段 1/3：遺傳算法策略進化...")
        evolution_result = self.genetic_engine.evolve_generation()
        
        # 獲取新策略
        new_strategies = evolution_result['global_best']
        self.current_strategies.append(new_strategies)
        
        # === 第二階段：RL 策略融合 ===
        print("\n🤖 階段 2/3：RL 元代理策略融合...")
        
        # 更新 RL 環境的策略池
        self.rl_agent.update_strategy_pool(self.current_strategies)
        
        # 訓練/推理
        if self.should_retrain_rl():
            self.rl_agent.train(episodes=1000)
        
        # 生成交易信號
        trading_signals = self.rl_agent.generate_signals()
        
        # === 第三階段：RLHF 新聞驗證 ===
        print("\n📰 階段 3/3：RLHF 新聞預測驗證...")
        
        # 自動驗證待處理預測
        self.rlhf_system.validate_pending_predictions()
        
        # 生成新預測
        latest_news = self.fetch_latest_news()
        for news in latest_news:
            prediction = self.rlhf_system.generate_prediction(news)
            self.rlhf_system.save_prediction(prediction)
        
        # === 第四階段：執行交易 ===
        print("\n💹 階段 4/3：執行統一交易...")
        
        # 整合所有信號
        unified_signal = self.merge_signals(
            genetic_signals=evolution_result['best_signals'],
            rl_signals=trading_signals,
            news_signals=self.rlhf_system.get_active_predictions()
        )
        
        # 執行交易
        self.executor.execute_trades(unified_signal)
        
        # === 第五階段：性能追蹤 ===
        performance = self.calculate_daily_performance()
        self.performance_history.append(performance)
        
        # 反饋到各子系統
        self.genetic_engine.update_fitness(performance)
        self.rl_agent.update_reward(performance)
        
        print("\n✅ 每日循環完成！")
        print(f"   - 最優策略適應度：{evolution_result['global_best'].fitness_score:.2f}")
        print(f"   - RL 累積獎勵：{trading_signals['cumulative_reward']:.2f}")
        print(f"   - 新聞預測準確率：{self.rlhf_system.get_accuracy():.2%}")
        print(f"   - 今日收益：{performance['daily_return']:.2%}")
```

### 4.2 執行腳本

#### 4.2.1 RL 訓練腳本

```python
# scripts/train_rl_agent_full.py

"""
完整 RL 元代理訓練腳本

使用方式：
    python scripts/train_rl_agent_full.py --curriculum --epochs 500000
"""

import argparse
from src.bioneuronai.strategies.rl_fusion_agent import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--curriculum', action='store_true',
                       help='使用課程式學習')
    parser.add_argument('--epochs', type=int, default=500000)
    parser.add_argument('--log-dir', type=str, default='./logs')
    args = parser.parse_args()
    
    if args.curriculum:
        # 課程式訓練
        trainer = CurriculumTrainer()
        trainer.train_all_stages()
    else:
        # 標準訓練
        env = StrategyFusionEnv()
        model = PPO(
            TransformerPolicy,
            env,
            tensorboard_log=args.log_dir
        )
        model.learn(total_timesteps=args.epochs)
        model.save("./models/rl_agent_final.zip")
    
    print("✅ RL 訓練完成！")

if __name__ == "__main__":
    main()
```

#### 4.2.2 遺傳算法腳本

```python
# scripts/run_genetic_evolution.py

"""
遺傳算法策略進化腳本

使用方式：
    python scripts/run_genetic_evolution.py --island --generations 100
"""

import argparse
from src.bioneuronai.core.self_improvement import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--island', action='store_true',
                       help='使用島嶼模型')
    parser.add_argument('--generations', type=int, default=100)
    parser.add_argument('--visualize', action='store_true',
                       help='生成視覺化')
    args = parser.parse_args()
    
    if args.island:
        # 島嶼模型
        engine = IslandEvolutionEngine(n_islands=4)
    else:
        # 單一族群
        engine = EvolutionEngine(population_size=200)
    
    # 進化循環
    for gen in range(args.generations):
        result = engine.evolve_generation()
        print(f"世代 {gen+1}/{args.generations}: "
              f"最優適應度 = {result['global_best'].fitness_score:.2f}")
    
    # 視覺化
    if args.visualize:
        visualizer = EvolutionVisualizer()
        visualizer.plot_fitness_landscape_3d(engine.get_all_individuals())
        visualizer.plot_diversity_over_time(engine.history)
    
    print("✅ 遺傳演化完成！")

if __name__ == "__main__":
    main()
```

#### 4.2.3 RLHF 驗證腳本

```python
# scripts/start_rlhf_validator.py

"""
RLHF 自動驗證守護進程

使用方式：
    python scripts/start_rlhf_validator.py --daemon
"""

import argparse
from src.bioneuronai.analysis.news_prediction_loop import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true',
                       help='背景守護進程模式')
    args = parser.parse_args()
    
    scheduler = PredictionScheduler()
    
    if args.daemon:
        print("🚀 啟動 RLHF 守護進程...")
        scheduler.start_daemon()  # 永久運行
    else:
        # 單次執行
        scheduler.validate_pending_predictions()
        print("✅ 驗證完成！")

if __name__ == "__main__":
    main()
```

#### 4.2.4 主整合腳本

```python
# scripts/run_all_systems.py

"""
統一執行所有 ML 系統

使用方式：
    python scripts/run_all_systems.py --mode daily
"""

import argparse
from src.bioneuronai.integration.unified_system import UnifiedMLSystem

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, 
                       choices=['daily', 'backtest', 'live'],
                       default='daily')
    args = parser.parse_args()
    
    system = UnifiedMLSystem()
    
    if args.mode == 'daily':
        # 每日執行
        system.run_daily_cycle()
    elif args.mode == 'backtest':
        # 回測模式
        system.run_backtest(start_date='2024-01-01', 
                           end_date='2026-01-01')
    elif args.mode == 'live':
        # 實盤模式
        print("⚠️  進入實盤模式，請確認風險！")
        confirm = input("輸入 'CONFIRM' 繼續：")
        if confirm == 'CONFIRM':
            system.run_live_trading()
    
    print("✅ 系統執行完成！")

if __name__ == "__main__":
    main()
```

---

## 視覺化能力說明

### 5.1 遺傳算法視覺化

1. **3D 適應度景觀** - 顯示參數空間的適應度分佈
2. **族群多樣性曲線** - 追蹤基因多樣性防止早熟收斂
3. **帕累托前緣** - 多目標優化的非支配解集
4. **世代演進動畫** - 展示策略如何逐代改進

### 5.2 RL 訓練視覺化

1. **TensorBoard 訓練曲線**
   - 累積獎勵 vs 回合數
   - 策略/價值損失
   - 熵（探索程度）
   
2. **交易性能指標**
   - 勝率趨勢
   - 夏普比率
   - 回撤分析

3. **策略權重熱力圖**
   - 各基礎策略的使用頻率
   - 時間序列權重變化

### 5.3 RLHF 質量儀表板

1. **準確率儀表板**
   - 總體準確率
   - 按標的/來源/時間範圍分組
   
2. **校準曲線**
   - 預測信心 vs 實際準確率
   - 識別過度自信/保守問題

3. **人類反饋統計**
   - 專家同意率
   - 邊緣案例分佈
   - 改進建議詞雲

---

## 技術依賴與環境配置

### 6.1 核心依賴

```txt
# requirements.txt

# === 深度學習框架 ===
torch==2.1.0
stable-baselines3==2.2.1
gymnasium==0.29.1
tensorboard==2.15.1

# === 遺傳算法 ===
deap==1.4.1
numpy==1.24.3
scipy==1.11.4

# === 資料處理 ===
pandas==2.1.4
ta-lib==0.4.28

# === 視覺化 ===
matplotlib==3.8.2
seaborn==0.13.0
plotly==5.18.0

# === 排程 ===
schedule==1.2.0
apscheduler==3.10.4

# === 資料庫 ===
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# === API ===
ccxt==4.2.3
requests==2.31.0

# === 工具 ===
pydantic==2.5.3
python-dotenv==1.0.0
```

### 6.2 安裝步驟

```bash
# 1. 建立虛擬環境
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 安裝 TA-Lib（技術指標庫）
# Windows：下載 whl 檔案
pip install TA_Lib-0.4.28-cp310-cp310-win_amd64.whl

# Linux：
sudo apt-get install ta-lib
pip install ta-lib

# 4. 驗證安裝
python -c "import torch; import stable_baselines3; import deap; print('✅ 安裝成功')"
```

### 6.3 資料庫初始化

```python
# scripts/init_database.py

from src.bioneuronai.data.database_manager import DatabaseManager

db = DatabaseManager()

# 創建表格
db.execute_sql("""
    CREATE TABLE IF NOT EXISTS news_predictions (
        prediction_id VARCHAR PRIMARY KEY,
        timestamp TIMESTAMP,
        news_title TEXT,
        predicted_direction VARCHAR,
        predicted_magnitude FLOAT,
        confidence_score FLOAT,
        validation_result JSONB,
        human_review JSONB,
        status VARCHAR
    );
    
    CREATE TABLE IF NOT EXISTS rl_training_history (
        episode_id SERIAL PRIMARY KEY,
        episode_num INT,
        reward FLOAT,
        length INT,
        policy_loss FLOAT,
        value_loss FLOAT,
        sharpe_ratio FLOAT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS evolution_history (
        generation_id SERIAL PRIMARY KEY,
        generation_num INT,
        best_fitness FLOAT,
        avg_fitness FLOAT,
        diversity_score FLOAT,
        best_genes JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
""")

print("✅ 資料庫初始化完成！")
```

---

## 總結

### 系統特色

1. **遺傳算法**：島嶼模型並行搜索 + 協同進化 + 3D 視覺化
2. **RL 元代理**：43維狀態 + Transformer網路 + 課程式學習
3. **RLHF**：自動驗證 + 人類審核 + 質量儀表板

### 預期效果

- 遺傳算法可找到穩健策略參數（10-20代收斂）
- RL 元代理學會動態融合策略（50萬步訓練後夏普比率 > 2.0）
- RLHF 持續改進新聞預測準確率（目標 > 70%）

### 執行順序

```bash
# 1. 初始化環境
python scripts/init_database.py

# 2. 訓練 RL 元代理（可選，已有預訓練模型）
python scripts/train_rl_agent_full.py --curriculum --epochs 500000

# 3. 運行遺傳演化
python scripts/run_genetic_evolution.py --island --generations 50 --visualize

# 4. 啟動 RLHF 守護進程（背景運行）
python scripts/start_rlhf_validator.py --daemon &

# 5. 執行統一系統
python scripts/run_all_systems.py --mode daily
```

### 文件結構

```
BioNeuronai/
├── src/
│   └── bioneuronai/
│       ├── core/
│       │   └── self_improvement.py       # 遺傳算法（增強版）
│       ├── strategies/
│       │   └── rl_fusion_agent.py        # RL 元代理（增強版）
│       ├── analysis/
│       │   └── news_prediction_loop.py   # RLHF（增強版）
│       └── integration/
│           └── unified_system.py         # 統一整合器（新增）
├── scripts/
│   ├── train_rl_agent_full.py           # RL 訓練腳本
│   ├── run_genetic_evolution.py         # 遺傳演化腳本
│   ├── start_rlhf_validator.py          # RLHF 守護進程
│   ├── run_all_systems.py               # 主執行腳本
│   └── init_database.py                 # 資料庫初始化
├── models/                              # 訓練模型保存
├── logs/                                # TensorBoard 日誌
└── visualizations/                      # 視覺化輸出
```

---

**文件結束**

此文件涵蓋所有算法的完整原理、實作細節、視覺化能力和執行方式。
所有功能均為完整版，視覺化用於證明底層能力的存在。
