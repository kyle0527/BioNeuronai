# 🚀 BioNeuronai v2.1 快速開始指南

## 📑 目錄

1. 📦 安裝
2. 🧪 驗證安裝
3. 🎯 快速使用案例
4. 🏗️ 整合到現有系統
5. ⚙️ 配置文件示例
6. 📊 監控儀表板
7. 🐛 故障排除
8. 📚 進階主題
9. 📞 技術支持

---

## 📦 安裝

### 方式 1: 自動安裝腳本 (推薦)

```bash
# 運行自動安裝驗證腳本
python setup_v2.1.py
```

這個腳本會自動:
- ✅ 檢查 Python 版本 (需要 >= 3.11)
- ✅ 安裝所有依賴 (numpy, stable-baselines3, gymnasium, etc.)
- ✅ 驗證模組導入
- ✅ 運行快速功能測試
- ✅ 生成安裝報告

### 方式 2: 手動安裝

```bash
# 1. 安裝基礎依賴
pip install numpy>=1.24.0 pandas>=2.0.0 torch>=2.0.0

# 2. 安裝強化學習依賴
pip install stable-baselines3==2.2.1 gymnasium==0.29.1

# 3. 安裝數據驗證依賴
pip install pydantic>=2.0.0 sqlalchemy>=2.0.0

# 4. (可選) 安裝訓練監控工具
pip install tensorboard wandb
```

---

## 🧪 驗證安裝

### 測試 1: 基因演算法

```python
from bioneuronai.core.self_improvement import PopulationManager

# 創建種群管理器
manager = PopulationManager(
    population_size=100,
    survival_rate=0.20,
    mutation_rate=0.15
)

# 運行一代演化
result = manager.run_generation()
print(f"第 {result['generation']} 代:")
print(f"  最佳適應度: {result['best_fitness']:.2f}")
print(f"  平均適應度: {result['avg_fitness']:.2f}")
```

**預期輸出**:
```
第 1 代:
  最佳適應度: 45.23
  平均適應度: 12.87
```

### 測試 2: RL Meta-Agent

```python
from bioneuronai.strategies.rl_fusion_agent import RLMetaAgent

# 創建 RL 代理
agent = RLMetaAgent(n_strategies=5)

# 查看環境信息
print(f"觀察空間: {agent.env.observation_space}")
print(f"動作空間: {agent.env.action_space}")

# 模擬預測
import numpy as np
state = np.random.randn(agent.env.observation_space.shape[0])
action, _ = agent.model.predict(state, deterministic=True)
print(f"模擬動作: 方向={action[0]}, 倉位={action[1]*10}%")
```

**預期輸出**:
```
觀察空間: Box(-inf, inf, (21,), float32)
動作空間: MultiDiscrete([3 11])
模擬動作: 方向=1, 倉位=50%
```

### 測試 3: 新聞預測循環

```python
from bioneuronai.analysis.news_prediction_loop import NewsPrediction

# 創建測試預測
pred = NewsPrediction(
    prediction_id="test_001",
    news_title="Bitcoin 突破 50K",
    target_symbol="BTCUSDT",
    predicted_direction="up",
    predicted_magnitude=0.05,
    confidence=0.8,
    price_at_prediction=48000.0
)

# 模擬驗證
pred.validate(actual_price=49500.0)
print(f"預測狀態: {pred.status}")
print(f"是否正確: {pred.is_correct}")
print(f"準確度分數: {pred.accuracy_score:.2f}")
```

**預期輸出**:
```
預測狀態: validated
是否正確: True
準確度分數: 0.85
```

---

## 🎯 快速使用案例

### 案例 1: 運行基因演算法優化策略參數

```python
from bioneuronai.core.self_improvement import PopulationManager

# 初始化
manager = PopulationManager(population_size=100)

# 運行 50 代演化
print("開始演化...")
for gen in range(50):
    result = manager.run_generation()

    if gen % 10 == 0:
        print(f"第 {gen} 代: 最佳={result['best_fitness']:.2f}, 平均={result['avg_fitness']:.2f}")

# 獲取最優策略
best_genes = manager.get_best_genes(top_n=5)
for i, gene in enumerate(best_genes, 1):
    print(f"\n排名 {i}: {gene.strategy_type}")
    print(f"  MA 快線: {gene.ma_fast}, 慢線: {gene.ma_slow}")
    print(f"  RSI 週期: {gene.rsi_period}")
    print(f"  適應度: {gene.fitness_score:.2f}")
```

### 案例 2: 訓練 RL Meta-Agent

```python
from bioneuronai.strategies.rl_fusion_agent import RLMetaAgent
import pandas as pd

# 準備訓練數據
training_data = pd.read_csv("historical_signals.csv")
# 假設包含列: timestamp, strategy1_signal, strategy2_signal, ..., close_price

# 創建並訓練 RL 代理
agent = RLMetaAgent(n_strategies=5)

print("開始訓練...")
agent.train(training_data, total_timesteps=100000)

# 保存模型
agent.save("models/rl_fusion_agent_v1.zip")
print("模型已保存到 models/rl_fusion_agent_v1.zip")

# 評估性能
eval_result = agent.evaluate(eval_episodes=10)
print(f"平均獎勵: {eval_result['mean_reward']:.2f}")
print(f"勝率: {eval_result['win_rate']:.1%}")
```

### 案例 3: 新聞預測與驗證

```python
from bioneuronai.analysis.news_prediction_loop import NewsPredictionLoop
from bioneuronai.data import get_database_manager
from bioneuronai.data.binance_connector import BinanceFuturesConnector

# 初始化組件
db = get_database_manager()
price_fetcher = BinanceFuturesConnector()
keyword_manager = MarketKeywords()  # 需要實現

# 創建預測循環
loop = NewsPredictionLoop(
    db_manager=db,
    price_fetcher=price_fetcher,
    keyword_manager=keyword_manager
)

# 場景: 分析新聞並記錄預測
news_data = {
    'news_id': 'news_20260122_001',
    'title': 'Bitcoin 將突破歷史新高',
    'source': 'CoinDesk',
    'target_symbol': 'BTCUSDT',
    'predicted_direction': 'up',
    'predicted_magnitude': 0.10,  # 預測上漲 10%
    'confidence': 0.85,
    'keywords_used': ['突破', '歷史新高', '牛市'],
    'sentiment_score': 0.9,
    'check_after_hours': 4  # 4小時後驗證
}

pred_id = loop.log_prediction(news_data)
print(f"✅ 預測已記錄: {pred_id}")

# 定期驗證 (可放在排程任務)
import time
time.sleep(4 * 3600)  # 等待 4 小時 (實際使用 schedule 模組)

validated = loop.validate_pending_predictions()
print(f"✅ 驗證了 {validated} 條預測")

# 查看統計
stats = loop.get_accuracy_stats()
print(f"總預測: {stats['total']}, 正確: {stats['correct']}, 準確率: {stats['accuracy_rate']:.1%}")
```

---

## 🏗️ 整合到現有系統

### 步驟 1: 在 TradingEngine 中啟用基因演算法

```python
# 文件: src/bioneuronai/core/trading_engine.py

from .self_improvement import PopulationManager

class TradingEngine:
    def __init__(self, config):
        self.config = config

        # 啟用基因演算法
        if config.use_genetic_algo:
            self.population_manager = PopulationManager(
                population_size=100,
                survival_rate=0.20
            )
        else:
            self.population_manager = None

    def optimize_strategies(self):
        """優化策略參數"""
        if self.population_manager:
            # 使用基因演算法
            result = self.population_manager.run_generation()
            best_genes = self.population_manager.get_best_genes(top_n=10)

            # 將最優基因轉換為策略實例
            strategies = [self._gene_to_strategy(gene) for gene in best_genes]
            return strategies
        else:
            # 使用傳統參數優化
            return self._traditional_optimize()
```

### 步驟 2: 在 StrategyFusion 中整合 RL Meta-Agent

```python
# 文件: src/bioneuronai/trading_strategies/strategy_fusion.py

from ..strategies.rl_fusion_agent import RLMetaAgent

class StrategyFusion:
    def __init__(self, config):
        self.config = config

        # 啟用 RL 融合
        if config.use_rl_fusion:
            self.rl_agent = RLMetaAgent.load("models/rl_fusion_agent.zip")
        else:
            self.rl_agent = None

    def fuse_signals(self, strategy_signals, market_state):
        """融合策略信號"""
        if self.rl_agent:
            # 使用 RL Meta-Agent
            state = {
                'strategy_signals': strategy_signals,
                'market_state': market_state,
                'position': self.current_position
            }
            direction, position_size = self.rl_agent.predict(state)
            return self._format_signal(direction, position_size)
        else:
            # 使用傳統投票機制
            return self._voting_fusion(strategy_signals)
```

### 步驟 3: 在 CryptoNewsAnalyzer 中啟用預測循環

```python
# 文件: src/bioneuronai/analysis/news_analyzer.py

from .news_prediction_loop import NewsPredictionLoop

class CryptoNewsAnalyzer:
    def __init__(self, config, db_manager, price_fetcher, keyword_manager):
        self.config = config

        # 啟用預測循環
        if config.use_prediction_loop:
            self.prediction_loop = NewsPredictionLoop(
                db_manager=db_manager,
                price_fetcher=price_fetcher,
                keyword_manager=keyword_manager
            )
        else:
            self.prediction_loop = None

    def analyze_news(self, article):
        """分析新聞"""
        # 情感分析
        sentiment_result = self._sentiment_analysis(article)

        # 如果啟用預測循環，記錄預測
        if self.prediction_loop and sentiment_result.confidence > 0.7:
            pred_id = self.prediction_loop.log_prediction({
                'news_id': article.id,
                'title': article.title,
                'source': article.source,
                'target_symbol': sentiment_result.target_symbol,
                'predicted_direction': sentiment_result.direction,
                'predicted_magnitude': sentiment_result.magnitude,
                'confidence': sentiment_result.confidence,
                'keywords_used': sentiment_result.keywords,
                'sentiment_score': sentiment_result.score,
                'check_after_hours': 4
            })
            logger.info(f"預測已記錄: {pred_id}")

        return sentiment_result
```

---

## ⚙️ 配置文件示例

> ⚠️ 本節部分過時：
> 這裡示範的是 v2.1 時期的配置模型，並非目前專案的長期標準。
> 特別是以下內容需重新對照後再使用：
> - 在 `config/trading_config.py` 中定義一套新的 `TradingConfig` schema
> - 直接把 Binance 憑證欄位視為該配置模型的一部分
> - 將它當作當前 `src/schemas/` 單一事實來源的替代
>
> 後續若要落地，應以 `src/schemas/`、現行模組結構與最新憑證流規劃為準。

```python
# config/trading_config.py

from pydantic import BaseModel

class TradingConfig(BaseModel):
    """交易配置"""

    # === 基因演算法配置 ===
    use_genetic_algo: bool = True
    genetic_population_size: int = 100
    genetic_survival_rate: float = 0.20
    genetic_mutation_rate: float = 0.15
    genetic_max_generations: int = 50

    # === RL Meta-Agent 配置 ===
    use_rl_fusion: bool = True
    rl_model_path: str = "models/rl_fusion_agent.zip"
    rl_n_strategies: int = 5
    rl_training_timesteps: int = 100000

    # === 新聞預測循環配置 ===
    use_prediction_loop: bool = True
    prediction_check_after_hours: float = 4.0
    prediction_min_confidence: float = 0.7
    prediction_enable_human_feedback: bool = True

    # === 資料庫配置 ===
    database_path: str = "trading_data/trading.db"

    # === API 配置 ===
    binance_api_key: str = ""
    binance_api_secret: str = ""

# 使用範例
config = TradingConfig(
    use_genetic_algo=True,
    use_rl_fusion=True,
    use_prediction_loop=True
)
```

---

## 📊 監控儀表板

### 使用 TensorBoard 監控 RL 訓練

```bash
# 啟動 TensorBoard
tensorboard --logdir=logs/rl_training

# 瀏覽器打開: http://localhost:6006
```

### 自定義監控腳本

```python
import schedule
import time
from bioneuronai.data import get_database_manager

db = get_database_manager()

def monitor_genetic_algo():
    """監控基因演算法"""
    history = db.get_evolution_history(last_n=10)

    avg_fitness = sum(h['avg_fitness'] for h in history) / len(history)
    best_fitness = max(h['best_fitness'] for h in history)

    print(f"🧬 基因演算法:")
    print(f"   最近 10 代平均適應度: {avg_fitness:.2f}")
    print(f"   最佳適應度: {best_fitness:.2f}")

def monitor_rl_training():
    """監控 RL 訓練"""
    progress = db.get_rl_training_progress("rl_fusion_v1", last_n=100)

    avg_reward = sum(p['mean_reward'] for p in progress) / len(progress)

    print(f"🤖 RL Meta-Agent:")
    print(f"   最近 100 步平均獎勵: {avg_reward:.2f}")

def monitor_prediction_accuracy():
    """監控預測準確率"""
    stats = db.get_prediction_accuracy()

    print(f"📰 新聞預測:")
    print(f"   總預測: {stats['total']}")
    print(f"   準確率: {stats['accuracy_rate']:.1%}")

# 排程每小時監控
schedule.every(1).hours.do(monitor_genetic_algo)
schedule.every(1).hours.do(monitor_rl_training)
schedule.every(1).hours.do(monitor_prediction_accuracy)

print("監控系統已啟動...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🐛 故障排除

### 問題 1: ModuleNotFoundError: No module named 'stable_baselines3'

**解決方案**:
```bash
pip install stable-baselines3==2.2.1 gymnasium==0.29.1
```

### 問題 2: RL 訓練速度慢

**解決方案**:
```python
# 使用 GPU 加速
agent = RLMetaAgent(n_strategies=5, device='cuda')

# 或減少訓練步數
agent.train(data, total_timesteps=50000)  # 從 100K 降到 50K
```

### 問題 3: 基因演算法收斂慢

**解決方案**:
```python
# 增大種群或提高淘汰率
manager = PopulationManager(
    population_size=200,  # 從 100 增加到 200
    survival_rate=0.15    # 從 0.20 降到 0.15 (更激烈競爭)
)
```

### 問題 4: 新聞預測準確率低

**解決方案**:
```python
# 調整驗證時間窗口
pred_data = {..., 'check_after_hours': 2.0}  # 從 4h 改為 2h

# 或提高最低置信度閾值
if sentiment.confidence > 0.8:  # 從 0.7 提高到 0.8
    loop.log_prediction(pred_data)
```

---

## 📚 進階主題

### 自定義適應度函數

```python
# 修改 src/bioneuronai/core/self_improvement.py

class EvolutionEngine:
    def _calculate_fitness(self, result: BacktestResult) -> float:
        """自定義適應度計算"""
        # 原始公式
        fitness = (
            result.total_return * 0.3 +
            result.sharpe_ratio * 0.3 +
            (1 - result.max_drawdown) * 0.2 +
            result.win_rate * 0.1 +
            result.profit_factor * 0.1
        )

        # 新增懲罰: 交易次數太少
        if result.total_trades < 50:
            fitness *= 0.8

        # 新增獎勵: 高 Calmar Ratio
        calmar = result.total_return / result.max_drawdown if result.max_drawdown > 0 else 0
        if calmar > 3.0:
            fitness *= 1.2

        return max(0, fitness)
```

### 自定義 RL 獎勵函數

```python
# 修改 src/bioneuronai/strategies/rl_fusion_agent.py

class StrategyFusionEnv:
    def _calculate_reward(self, pnl: float) -> float:
        """自定義獎勵計算"""
        # 基礎獎勵
        reward = pnl

        # 交易成本
        if self.last_action != self.current_action:
            reward -= self.transaction_cost

        # 持倉成本
        if self.current_action != 0:  # 持有倉位
            reward -= self.holding_cost

        # 新增: 懲罰頻繁交易
        if self.trade_count_in_window > 10:
            reward -= 0.1

        # 新增: 獎勵高 Sharpe
        if self.sharpe_ratio > 2.0:
            reward += 0.5

        return reward
```

---

## 📞 技術支持

- **文檔**: [docs/SYSTEM_UPGRADE_V2.1_REPORT.md](docs/SYSTEM_UPGRADE_V2.1_REPORT.md)
- **GitHub Issues**: [提交問題](https://github.com/BioNeuronai/issues)
- **Email**: support@bioneuronai.com

---

**祝您使用愉快！🎉**
