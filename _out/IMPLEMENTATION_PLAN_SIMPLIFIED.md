# BioNeuronai 簡化實作方案（核心功能優先）

**日期**: 2026-01-26  
**原則**: **能跑為主，視覺化後做**  
**參考**: Stable-Baselines3 官方文檔 + DEAP 基因演算法庫

---

## 📚 業界最佳實踐參考

### 1. Stable-Baselines3 (RL)
- **簡單優先**: 使用默認 MlpPolicy，不用自定義網絡
- **Callback機制**: 訓練中保存最佳模型
- **VecEnv**: 多進程並行訓練（加速）
- **參數調優**: 先用默認參數跑起來，再調

```python
# SB3 最簡單範例
from stable_baselines3 import PPO

model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=25000)
model.save("ppo_model")
```

### 2. DEAP (基因演算法)
- **Toolbox機制**: 註冊所有操作（evaluate, mutate, crossover, select）
- **簡單循環**: 不用複雜架構，for loop就能跑
- **內建函數**: 使用 tools.selBest, tools.cxTwoPoint等現成工具

```python
# DEAP 核心循環
for gen in range(NGEN):
    offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.1)
    fits = toolbox.map(toolbox.evaluate, offspring)
    population = toolbox.select(offspring, k=len(population))
```

---

## 🎯 簡化後的 3 大核心改進

### 改進 1: RL Meta-Agent 核心版

#### 目標
讓 PPO Agent 能夠融合 5 個策略信號，做出最終交易決策

#### 不做的事（暫時）
- ❌ 自定義 Transformer Policy Network
- ❌ Curriculum Learning 分階段訓練
- ❌ 複雜的 Reward Function
- ❌ TensorBoard 可視化

#### 只做核心功能
```python
# 文件: src/bioneuronai/strategies/rl_meta_agent_simple.py

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
import logging

logger = logging.getLogger(__name__)

class SimpleTradingEnv(gym.Env):
    """極簡 RL 交易環境"""
    
    def __init__(self):
        super().__init__()
        
        # 狀態空間: 5個策略信號 × 2 (direction, strength) = 10 維
        self.observation_space = spaces.Box(
            low=-1, high=1, shape=(10,), dtype=np.float32
        )
        
        # 動作空間: 0=Hold, 1=Long, 2=Short
        self.action_space = spaces.Discrete(3)
        
        # 內部狀態
        self.current_step = 0
        self.capital = 10000.0
        self.position = 0  # 0=無倉位, 1=多頭, -1=空頭
        self.entry_price = 0.0
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.capital = 10000.0
        self.position = 0
        return self._get_obs(), {}
    
    def step(self, action):
        # 執行動作
        reward = self._execute_action(action)
        
        # 更新步驟
        self.current_step += 1
        terminated = self.current_step >= 1000
        
        return self._get_obs(), reward, terminated, False, {}
    
    def _get_obs(self):
        """獲取觀察（模擬5個策略信號）"""
        # 這裡應該從實際策略獲取信號
        # 暫時返回隨機值作為示例
        return np.random.randn(10).astype(np.float32)
    
    def _execute_action(self, action):
        """執行交易動作並計算獎勵"""
        # 簡化版獎勵計算
        if action == 0:  # Hold
            return 0.01  # 小獎勵鼓勵觀望
        elif action == 1:  # Long
            # 這裡應該計算實際PnL
            return np.random.randn() * 0.1
        else:  # Short
            return np.random.randn() * 0.1


def train_simple_rl_agent():
    """訓練極簡 RL Meta-Agent"""
    logger.info("🚀 開始訓練 RL Meta-Agent (簡化版)")
    
    # 創建環境
    env = SimpleTradingEnv()
    
    # 創建 PPO Agent（使用默認參數）
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
    )
    
    # 創建評估回調
    eval_env = SimpleTradingEnv()
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="./rl_models/",
        log_path="./rl_logs/",
        eval_freq=5000,
        deterministic=True,
    )
    
    # 訓練
    logger.info("⏳ 訓練中... (total_timesteps=50000)")
    model.learn(
        total_timesteps=50000,
        callback=eval_callback,
        progress_bar=True
    )
    
    # 保存模型
    model.save("./rl_models/rl_meta_agent_simple")
    logger.info("✅ 訓練完成！模型已保存")
    
    return model


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_simple_rl_agent()
```

---

### 改進 2: 基因演算法核心版

#### 目標
使用 DEAP 庫實現簡單的基因演算法，優化策略參數

#### 不做的事（暫時）
- ❌ 島嶼模型（多族群）
- ❌ 協同演化
- ❌ 3D 視覺化

#### 只做核心功能
```python
# 文件: src/bioneuronai/core/genetic_algorithm_simple.py

import random
import numpy as np
from deap import base, creator, tools, algorithms
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

# 創建適應度類別（最大化收益）
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

class SimpleGeneticOptimizer:
    """簡單基因演算法優化器"""
    
    def __init__(self, population_size=50):
        self.population_size = population_size
        self.toolbox = base.Toolbox()
        self._setup_toolbox()
    
    def _setup_toolbox(self):
        """設置 DEAP Toolbox"""
        
        # 基因編碼：[ma_fast, ma_slow, rsi_period, stop_loss, take_profit]
        # 範圍: [5-30, 40-100, 7-21, 1.5-3.0, 2.0-5.0]
        self.toolbox.register("ma_fast", random.randint, 5, 30)
        self.toolbox.register("ma_slow", random.randint, 40, 100)
        self.toolbox.register("rsi_period", random.randint, 7, 21)
        self.toolbox.register("stop_loss", random.uniform, 1.5, 3.0)
        self.toolbox.register("take_profit", random.uniform, 2.0, 5.0)
        
        # 個體生成器
        self.toolbox.register(
            "individual",
            tools.initCycle,
            creator.Individual,
            (
                self.toolbox.ma_fast,
                self.toolbox.ma_slow,
                self.toolbox.rsi_period,
                self.toolbox.stop_loss,
                self.toolbox.take_profit,
            ),
            n=1
        )
        
        # 族群生成器
        self.toolbox.register(
            "population",
            tools.initRepeat,
            list,
            self.toolbox.individual
        )
        
        # 評估函數（需要自定義）
        self.toolbox.register("evaluate", self._evaluate_individual)
        
        # 交配算子
        self.toolbox.register("mate", tools.cxTwoPoint)
        
        # 突變算子
        self.toolbox.register(
            "mutate",
            tools.mutPolynomialBounded,
            low=[5, 40, 7, 1.5, 2.0],
            up=[30, 100, 21, 3.0, 5.0],
            eta=20.0,
            indpb=0.2
        )
        
        # 選擇算子
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def _evaluate_individual(self, individual: List) -> Tuple[float,]:
        """評估個體適應度"""
        # 解碼基因
        ma_fast, ma_slow, rsi_period, stop_loss, take_profit = individual
        
        # 這裡應該進行實際回測
        # 暫時返回隨機適應度作為示例
        fitness = random.random()
        
        return (fitness,)
    
    def optimize(self, n_generations=20):
        """執行基因演算法優化"""
        logger.info(f"🧬 開始基因演算法優化 (族群={self.population_size}, 世代={n_generations})")
        
        # 初始化族群
        population = self.toolbox.population(n=self.population_size)
        
        # 統計信息
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # 演化循環
        for gen in range(n_generations):
            logger.info(f"\n=== 第 {gen+1}/{n_generations} 代 ===")
            
            # 選擇下一代
            offspring = self.toolbox.select(population, len(population))
            offspring = list(map(self.toolbox.clone, offspring))
            
            # 交配
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < 0.5:  # 交配機率 50%
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values
            
            # 突變
            for mutant in offspring:
                if random.random() < 0.2:  # 突變機率 20%
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values
            
            # 評估新個體
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            # 更新族群
            population[:] = offspring
            
            # 記錄統計
            record = stats.compile(population)
            logger.info(f"  平均適應度: {record['avg']:.4f}")
            logger.info(f"  最佳適應度: {record['max']:.4f}")
        
        # 返回最佳個體
        best_ind = tools.selBest(population, 1)[0]
        logger.info(f"\n✅ 優化完成！")
        logger.info(f"最佳參數: {best_ind}")
        logger.info(f"最佳適應度: {best_ind.fitness.values[0]:.4f}")
        
        return best_ind, population


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    optimizer = SimpleGeneticOptimizer(population_size=50)
    best_individual, final_population = optimizer.optimize(n_generations=20)
```

---

### 改進 3: RLHF 自動驗證核心版

#### 目標
自動化新聞預測驗證，定時檢查並更新權重

#### 不做的事（暫時）
- ❌ 品質儀表板（網頁UI）
- ❌ 複雜的人工反饋系統
- ❌ 數據可視化圖表

#### 只做核心功能
```python
# 文件: src/bioneuronai/analysis/rlhf_auto_validator.py

import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class AutoPredictionValidator:
    """自動化預測驗證器（RLHF）"""
    
    def __init__(self, db_manager, check_interval_minutes=60):
        self.db = db_manager
        self.check_interval = check_interval_minutes
        self.running = False
        self._thread = None
    
    def start(self):
        """啟動自動驗證"""
        if self.running:
            logger.warning("⚠️  驗證器已在運行")
            return
        
        # 設置定時任務
        schedule.every(self.check_interval).minutes.do(self._check_predictions)
        
        # 背景執行緒
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"⏰ 自動驗證器已啟動 (每 {self.check_interval} 分鐘檢查一次)")
    
    def stop(self):
        """停止自動驗證"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("⏹️  自動驗證器已停止")
    
    def _run_loop(self):
        """背景循環"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次排程
    
    def _check_predictions(self):
        """檢查並驗證到期的預測"""
        try:
            logger.info("🔍 檢查待驗證的新聞預測...")
            
            # 從資料庫獲取待驗證預測
            pending = self._get_pending_predictions()
            
            if not pending:
                logger.debug("   無待驗證預測")
                return
            
            now = datetime.now()
            validated_count = 0
            correct_count = 0
            
            for pred in pending:
                # 檢查是否到驗證時間
                check_time = pred['prediction_time'] + timedelta(hours=pred['check_after_hours'])
                
                if now >= check_time:
                    # 驗證預測
                    is_correct = self._validate_prediction(pred)
                    
                    validated_count += 1
                    if is_correct:
                        correct_count += 1
                    
                    # 更新權重
                    self._update_weights(pred, is_correct)
            
            if validated_count > 0:
                accuracy = correct_count / validated_count
                logger.info(f"✅ 本次驗證: {validated_count} 個預測")
                logger.info(f"   準確率: {accuracy:.1%} ({correct_count}/{validated_count})")
        
        except Exception as e:
            logger.error(f"❌ 驗證失敗: {e}", exc_info=True)
    
    def _get_pending_predictions(self) -> List[dict]:
        """獲取待驗證預測"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT * FROM news_predictions 
                WHERE status = 'pending'
                AND datetime(prediction_time) < datetime('now')
            """)
            
            columns = [desc[0] for desc in cursor.description]
            predictions = []
            
            for row in cursor.fetchall():
                pred = dict(zip(columns, row))
                # 轉換時間字串
                pred['prediction_time'] = datetime.fromisoformat(pred['prediction_time'])
                predictions.append(pred)
            
            return predictions
        
        except Exception as e:
            logger.error(f"❌ 獲取預測失敗: {e}")
            return []
    
    def _validate_prediction(self, pred: dict) -> bool:
        """驗證單個預測"""
        try:
            # 獲取當前價格
            current_price = self._get_current_price(pred['target_symbol'])
            
            # 計算價格變化
            price_change_pct = (current_price - pred['price_at_prediction']) / pred['price_at_prediction'] * 100
            
            # 判斷預測是否正確
            predicted_direction = pred['predicted_direction']
            
            if predicted_direction == 'bullish':
                is_correct = price_change_pct > 0
            elif predicted_direction == 'bearish':
                is_correct = price_change_pct < 0
            else:  # neutral
                is_correct = abs(price_change_pct) < 1
            
            # 更新資料庫
            self.db.conn.execute("""
                UPDATE news_predictions 
                SET status = ?,
                    is_correct = ?,
                    price_at_validation = ?,
                    actual_change_pct = ?,
                    validation_time = ?
                WHERE prediction_id = ?
            """, (
                'correct' if is_correct else 'wrong',
                int(is_correct),
                current_price,
                price_change_pct,
                datetime.now().isoformat(),
                pred['prediction_id']
            ))
            self.db.conn.commit()
            
            status = "✅" if is_correct else "❌"
            logger.info(f"   {status} {pred['target_symbol']}: {predicted_direction} (實際變化 {price_change_pct:+.2f}%)")
            
            return is_correct
        
        except Exception as e:
            logger.error(f"❌ 驗證預測失敗: {e}")
            return False
    
    def _get_current_price(self, symbol: str) -> float:
        """獲取當前價格（需要整合實際API）"""
        # 這裡應該調用 Binance API
        # 暫時返回模擬價格
        import random
        return 50000 * (1 + random.uniform(-0.05, 0.05))
    
    def _update_weights(self, pred: dict, is_correct: bool):
        """更新關鍵字權重（RLHF核心）"""
        try:
            # 獲取相關關鍵字
            news_title = pred.get('news_title', '')
            
            # 權重調整量
            adjustment = 0.08 if is_correct else -0.08
            
            # 這裡應該更新 KeywordManager 的權重
            # 暫時只記錄日誌
            logger.info(f"   🔧 權重調整: {adjustment:+.2f} (基於預測結果)")
        
        except Exception as e:
            logger.error(f"❌ 權重更新失敗: {e}")


# 簡單的啟動腳本
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from bioneuronai.data.database_manager import DatabaseManager
    
    # 初始化資料庫
    db = DatabaseManager()
    
    # 創建驗證器
    validator = AutoPredictionValidator(db, check_interval_minutes=60)
    
    # 啟動
    validator.start()
    
    logger.info("🚀 RLHF 自動驗證器正在運行...")
    logger.info("   按 Ctrl+C 停止")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        validator.stop()
        logger.info("👋 再見！")
```

---

## 📦 整合啟動腳本

```python
# 文件: scripts/run_all_simplified.py

"""
簡化版系統整合啟動
"""

import logging
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("🚀 BioNeuronai 簡化版系統啟動")
    logger.info("=" * 80)
    
    # 1. RLHF 自動驗證（背景執行）
    logger.info("\n[1/3] 啟動 RLHF 自動驗證...")
    from bioneuronai.data.database_manager import DatabaseManager
    from bioneuronai.analysis.rlhf_auto_validator import AutoPredictionValidator
    
    db = DatabaseManager()
    validator = AutoPredictionValidator(db, check_interval_minutes=60)
    validator.start()
    
    # 2. 基因演算法優化（運行一次）
    logger.info("\n[2/3] 執行基因演算法優化...")
    from bioneuronai.core.genetic_algorithm_simple import SimpleGeneticOptimizer
    
    ga_optimizer = SimpleGeneticOptimizer(population_size=30)
    best_params, _ = ga_optimizer.optimize(n_generations=10)
    
    # 3. RL Meta-Agent 訓練
    logger.info("\n[3/3] 訓練 RL Meta-Agent...")
    from bioneuronai.strategies.rl_meta_agent_simple import train_simple_rl_agent
    
    rl_model = train_simple_rl_agent()
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 所有系統啟動完成！")
    logger.info("=" * 80)
    logger.info("\n💡 提示:")
    logger.info("   - RLHF 驗證器在背景運行中...")
    logger.info("   - RL 模型已保存至: ./rl_models/")
    logger.info("   - 基因演算法最佳參數: %s", best_params)
    
    # 保持運行（RLHF 持續工作）
    logger.info("\n按 Ctrl+C 停止系統")
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        validator.stop()
        logger.info("\n👋 系統已停止")


if __name__ == "__main__":
    main()
```

---

## 📋 安裝依賴

```bash
# 安裝核心依賴
pip install stable-baselines3==2.2.1
pip install gymnasium==0.29.1
pip install deap
pip install schedule

# 驗證安裝
python -c "import stable_baselines3; import deap; import schedule; print('✅ 所有依賴已安裝')"
```

---

## 🚀 快速開始

```bash
# 1. 進入專案目錄
cd C:\D\E\BioNeuronai

# 2. 運行簡化版系統
python scripts/run_all_simplified.py
```

---

## ✅ 完成檢查清單

### Phase 1: 核心功能（本次實作）
- [ ] RL Meta-Agent 基本環境
- [ ] PPO 訓練循環（50K steps）
- [ ] 基因演算法（DEAP）
- [ ] 自動預測驗證（RLHF）
- [ ] 整合啟動腳本

### Phase 2: 功能增強（下次迭代）
- [ ] 實際回測數據整合
- [ ] Reward Function 優化
- [ ] 基因演算法多目標優化
- [ ] 人工反饋介面

### Phase 3: 視覺化（最後做）
- [ ] TensorBoard 訓練曲線
- [ ] 預測品質儀表板
- [ ] 基因演算法適應度圖表

---

## 💡 設計原則

1. **能跑為主**: 先實現基本功能，再優化
2. **使用現成工具**: Stable-Baselines3 + DEAP，不重造輪子
3. **簡單架構**: 避免過度設計，保持代碼簡潔
4. **漸進式增強**: 核心 → 功能 → 視覺化

---

## 📊 預期成果

- ✅ RL Agent 能夠訓練並保存模型
- ✅ 基因演算法能夠優化參數
- ✅ RLHF 自動驗證在背景運行
- ✅ 所有功能獨立可測試
- ✅ 代碼總量 < 500 行

---

**實作時間估計**: 4-6 小時  
**難度**: ⭐⭐⭐ (中等)  
**收益**: ⭐⭐⭐⭐⭐ (核心功能完整，可立即使用)
