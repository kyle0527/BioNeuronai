"""
強化學習策略融合代理 (Reinforcement Learning Meta-Agent)
==========================================================

核心理念：AI 自主學習如何融合策略
不再是「投票」或「加權平均」，而是讓 AI 自己「悟」出融合邏輯

獨創性：
- AI 可能發現人類無法理解的融合規律
- 例如：當趨勢策略+新聞極度看多時，AI 可能學會「反向做空」（Fade the trend）
- 這種逆向思維是傳統方法不會考慮的

核心技術：
1. 使用 PPO (Proximal Policy Optimization) 算法
2. 輸入狀態：所有子策略信號 + 市場狀態 + 新聞情緒
3. 輸出動作：最終交易決策（多頭%、空頭%、觀望）
4. 獎勵函數：基於交易結果的盈虧和風險調整收益

工作流程：
1. 收集所有策略信號
2. RL Agent 評估當前狀態
3. 輸出最終決策（可能與所有策略都不同）
4. 執行交易並獲得反饋
5. 更新 RL Agent 權重

依賴：
- stable-baselines3 (PPO)
- gymnasium (RL environment)
- torch (neural network)
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import Dict, List, Optional, Any, TYPE_CHECKING, cast
from dataclasses import dataclass
from pathlib import Path
import logging

if TYPE_CHECKING:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import BaseCallback

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import BaseCallback
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    PPO = None  # type: ignore
    DummyVecEnv = None  # type: ignore
    BaseCallback = object  # type: ignore
    print("⚠️  警告: stable-baselines3 未安裝，請執行: pip install stable-baselines3")

logger = logging.getLogger(__name__)


# ============================================================================
# 數據結構定義
# ============================================================================

@dataclass
class StrategySignal:
    """單一策略信號"""
    strategy_name: str
    direction: str  # 'long', 'short', 'neutral'
    strength: float  # 0-1
    confidence: float  # 0-1
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0


@dataclass
class MarketState:
    """市場狀態"""
    price: float
    volatility: float  # 0-1 normalized
    trend_strength: float  # -1 to 1
    volume_ratio: float  # 0-1 normalized
    news_sentiment: float  # -1 to 1
    time_of_day: float  # 0-1 (normalized hour)
    news_duration_hours: float = 0.0  # 新聞持續時間（小時）
    related_news_count: int = 0  # 相關新聞數量
    

@dataclass
class RLAction:
    """RL Agent 動作"""
    action_type: str  # 'long', 'short', 'hold'
    position_size: float  # 0-1 (percentage of capital)
    confidence: float  # 0-1
    

@dataclass
class TradeResult:
    """交易結果"""
    pnl: float  # profit/loss
    return_pct: float
    holding_time: int  # bars
    max_drawdown: float
    sharpe: float


# ============================================================================
# RL 交易環境 (Gymnasium Environment)
# ============================================================================

class StrategyFusionEnv(gym.Env):
    """
    策略融合 RL 環境
    
    State Space:
    - 策略信號 (N strategies × 3 features = direction, strength, confidence)
    - 市場狀態 (8 features: price, volatility, trend, volume, news_sentiment, time_of_day, news_duration_hours, related_news_count)
    - 當前倉位 (2 features: position_type, position_size)
    
    Action Space:
    - Discrete: [0=Hold, 1=Long, 2=Short]
    - + Continuous: position_size [0, 1]
    
    Reward:
    - 基於交易盈虧
    - 風險調整（夏普比率）
    - 回撤懲罰
    """
    
    metadata = {'render_modes': ['human']}
    
    def __init__(
        self,
        num_strategies: int = 5,
        initial_capital: float = 10000.0,
        transaction_cost: float = 0.001,  # 0.1%
        max_position_size: float = 0.5,  # 最大50%倉位
    ):
        super().__init__()
        
        self.num_strategies = num_strategies
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.max_position_size = max_position_size
        
        # State space: strategy signals + market state + position
        # Strategy signals: num_strategies × 3 (direction_encoded, strength, confidence)
        # Market state: 8 features (price, volatility, trend, volume, news_sentiment, time_of_day, news_duration, related_news_count)
        # Position: 2 features
        obs_dim = (num_strategies * 3) + 8 + 2
        
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(obs_dim,),
            dtype=np.float32
        )
        
        # Action space: MultiDiscrete
        # [action_type (0=hold, 1=long, 2=short), position_size_bucket (0-10)]
        self.action_space = spaces.MultiDiscrete([3, 11])
        
        # Internal state
        self.current_step = 0
        self.capital = initial_capital
        self.position_type = 0  # 0=no position, 1=long, -1=short
        self.position_size = 0.0
        self.entry_price = 0.0
        self.current_price = 100.0
        
        # History
        self.trade_history: List[Dict] = []
        self.equity_curve: List[float] = []
        
        # Market data (will be set externally)
        self.market_data: Optional[List[Dict]] = None
        self.strategy_signals_history: Optional[List[List['StrategySignal']]] = None
        
        logger.info(f"🎮 RL 環境初始化: 策略數={num_strategies}, 資金={initial_capital}")
    
    def reset(self, seed=None, options=None):  # type: ignore
        """重置環境"""
        super().reset(seed=seed)
        
        self.current_step = 0
        self.capital = self.initial_capital
        self.position_type = 0
        self.position_size = 0.0
        self.entry_price = 0.0
        self.trade_history = []
        self.equity_curve = [self.capital]
        
        # 返回初始觀察
        obs = self._get_observation()
        info = {}
        
        return obs, info
    
    def step(self, action):
        """執行一步"""
        # 解析動作
        action_type = action[0]
        position_size_bucket = action[1]  # 0-10
        
        # 轉換為實際倉位大小
        position_size = (position_size_bucket / 10.0) * self.max_position_size
        
        # 計算獎勵
        reward = self._calculate_reward(action_type, position_size)
        
        # 更新倉位
        self._update_position(action_type, position_size)
        
        # 更新資金
        self._update_capital()
        
        # 記錄equity
        self.equity_curve.append(self.capital)
        
        # 檢查是否結束
        self.current_step += 1
        terminated = self.current_step >= len(self.market_data) - 1 if self.market_data is not None else False
        truncated = False
        
        # 破產檢查
        if self.capital < self.initial_capital * 0.5:
            terminated = True
            reward -= 100  # 破產懲罰
        
        # 獲取新觀察
        obs = self._get_observation()
        info = {
            'capital': self.capital,
            'position': self.position_type,
            'return': (self.capital - self.initial_capital) / self.initial_capital
        }
        
        return obs, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """構建觀察向量"""
        obs: List[float] = []
        
        # 1. 策略信號 (假設已設置)
        if self.strategy_signals_history and self.current_step < len(self.strategy_signals_history):
            signals: List[StrategySignal] = self.strategy_signals_history[self.current_step]
            for signal in signals[:self.num_strategies]:
                # Direction encoded: long=1, short=-1, neutral=0
                if signal.direction == 'long':
                    direction = 1.0
                elif signal.direction == 'short':
                    direction = -1.0
                else:
                    direction = 0.0
                obs.extend([direction, signal.strength, signal.confidence])
        else:
            # 默認值
            obs.extend([0.0] * (self.num_strategies * 3))
        
        # 2. 市場狀態 (假設已設置)
        if self.market_data and self.current_step < len(self.market_data):
            market = self.market_data[self.current_step]
            obs.extend([
                market.get('price_normalized', 0.0),
                market.get('volatility', 0.0),
                market.get('trend_strength', 0.0),
                market.get('volume_ratio', 0.0),
                market.get('news_sentiment', 0.0),
                market.get('time_of_day', 0.0),
                market.get('news_duration_hours', 0.0),
                float(market.get('related_news_count', 0)),
            ])
        else:
            obs.extend([0.0] * 8)
        
        # 3. 當前倉位
        obs.extend([float(self.position_type), self.position_size])
        
        return cast(np.ndarray, np.array(obs, dtype=np.float32))
    
    def _calculate_reward(self, action_type: int, position_size: float) -> float:
        """計算獎勵"""
        reward = 0.0
        
        # 如果持有倉位，計算浮動盈虧
        if self.position_type != 0 and self.market_data:
            if self.current_step < len(self.market_data):
                current_price = self.market_data[self.current_step].get('price', self.current_price)
                price_change = (current_price - self.entry_price) / self.entry_price
                
                # 多頭/空頭盈虧
                pnl = price_change * self.position_size * self.capital * self.position_type
                
                # 交易成本
                if action_type != 0:  # 如果改變倉位
                    pnl -= abs(self.capital * position_size * self.transaction_cost)
                
                reward = pnl / self.initial_capital * 100  # 正規化為百分比
        
        # 持倉時間過長懲罰（鼓勵快進快出）
        if self.position_type != 0:
            holding_time = self.current_step - getattr(self, 'entry_step', self.current_step)
            if holding_time > 50:  # 持倉超過50個bar
                reward -= 0.1
        
        return reward
    
    def _update_position(self, action_type: int, position_size: float):
        """更新倉位"""
        if self.market_data and self.current_step < len(self.market_data):
            current_price = self.market_data[self.current_step].get('price', 100.0)
            
            # 平倉
            if self.position_type != 0 and action_type == 0:
                # 計算平倉盈虧
                price_change = (current_price - self.entry_price) / self.entry_price
                pnl = price_change * self.position_size * self.capital * self.position_type
                self.capital += pnl
                
                # 記錄交易
                self.trade_history.append({
                    'entry_price': self.entry_price,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'return_pct': pnl / self.capital * 100
                })
                
                # 重置倉位
                self.position_type = 0
                self.position_size = 0.0
            
            # 開倉
            elif action_type != 0:
                # 先平掉舊倉位
                if self.position_type != 0:
                    self._update_position(0, 0)  # 遞歸平倉
                
                # 開新倉
                self.position_type = 1 if action_type == 1 else -1
                self.position_size = position_size
                self.entry_price = current_price
                self.entry_step = self.current_step
    
    def _update_capital(self):
        """更新資金（浮動盈虧）"""
        if self.position_type != 0 and self.market_data:
            if self.current_step < len(self.market_data):
                current_price = self.market_data[self.current_step].get('price', self.current_price)

                # 不實際修改 capital，只記錄
                self.current_price = current_price
    
    def render(self):
        """渲染環境（可選）"""
        if self.current_step % 10 == 0:
            print(f"Step {self.current_step}: Capital=${self.capital:.2f}, Position={self.position_type}, Size={self.position_size:.2%}")


# ============================================================================
# RL Meta-Agent (強化學習融合代理)
# ============================================================================

class RLMetaAgent:
    """
    RL Meta-Agent - 強化學習策略融合代理
    
    使用 PPO 算法學習如何融合多個策略信號
    """
    
    def __init__(
        self,
        num_strategies: int = 5,
        model_path: Optional[Path] = None,
        training_mode: bool = True,
    ):
        if not SB3_AVAILABLE:
            raise ImportError("需要安裝 stable-baselines3: pip install stable-baselines3")
        
        self.num_strategies = num_strategies
        self.model_path = Path(model_path) if model_path else Path("./rl_models")
        self.model_path.mkdir(exist_ok=True, parents=True)
        self.training_mode = training_mode
        
        # 創建環境
        self.env = StrategyFusionEnv(num_strategies=num_strategies)
        
        # 創建或載入模型
        self.model = None
        self._initialize_model()
        
        # 訓練記錄
        self.training_history: List[Dict[str, float]] = []
        
        logger.info(f"🤖 RL Meta-Agent 初始化: 策略數={num_strategies}, 訓練模式={training_mode}")
    
    def _initialize_model(self):
        """初始化 PPO 模型"""
        model_file = self.model_path / "ppo_strategy_fusion.zip"
        
        if model_file.exists() and not self.training_mode:
            # 載入已訓練模型
            self.model = PPO.load(model_file, env=self.env)  # type: ignore
            logger.info(f"📂 載入模型: {model_file}")
        else:
            # 創建新模型
            self.model = PPO(  # type: ignore
                policy="MlpPolicy",
                env=self.env,
                learning_rate=3e-4,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                verbose=1,
                tensorboard_log="./rl_logs/"
            )
            logger.info("✨ 創建新模型")
    
    def train(
        self,
        total_timesteps: int = 100000,
        market_data: Optional[List[Dict]] = None,
        strategy_signals_history: Optional[List[List['StrategySignal']]] = None,
    ):
        """
        訓練 RL Agent
        
        Args:
            total_timesteps: 總訓練步數
            market_data: 市場數據歷史
            strategy_signals_history: 策略信號歷史
        """
        logger.info(f"🎓 開始訓練: {total_timesteps} 步")
        
        # 設置環境數據
        self.env.market_data = market_data
        self.env.strategy_signals_history = strategy_signals_history
        
        # 訓練
        self.model.learn(  # type: ignore
            total_timesteps=total_timesteps,
            callback=self._training_callback,
            progress_bar=True,
        )
        
        # 保存模型
        self.save_model()
        
        logger.info("✅ 訓練完成")
    
    def _training_callback(self, locals_dict, globals_dict):
        """訓練回調"""
        # 每1000步記錄一次
        if locals_dict['self'].num_timesteps % 1000 == 0:
            self.training_history.append({
                'timestep': locals_dict['self'].num_timesteps,
                'mean_reward': locals_dict.get('mean_reward', 0),
            })
        return True
    
    def predict(
        self,
        strategy_signals: List['StrategySignal'],
        market_state: 'MarketState',
        current_position: Optional[Dict] = None,
    ) -> 'RLAction':
        """
        預測最佳動作
        
        Args:
            strategy_signals: 當前所有策略信號
            market_state: 當前市場狀態
            current_position: 當前倉位信息
            
        Returns:
            RL Agent 的動作決策
        """
        # 構建觀察
        obs = self._build_observation(strategy_signals, market_state, current_position)
        
        # 預測
        action, _states = self.model.predict(obs, deterministic=not self.training_mode)  # type: ignore
        
        # 解析動作
        action_type_idx = action[0]
        position_size_bucket = action[1]
        
        action_type = ['hold', 'long', 'short'][action_type_idx]
        position_size = (position_size_bucket / 10.0) * 0.5  # max 50%
        
        return RLAction(
            action_type=action_type,
            position_size=position_size,
            confidence=0.8,  # 可以從模型輸出計算
        )
    
    def _build_observation(
        self,
        strategy_signals: List['StrategySignal'],
        market_state: 'MarketState',
        current_position: Optional[Dict] = None,
    ) -> np.ndarray:
        """構建觀察向量"""
        obs = []
        
        # 策略信號
        for signal in strategy_signals[:self.num_strategies]:
            if signal.direction == 'long':
                direction = 1.0
            elif signal.direction == 'short':
                direction = -1.0
            else:
                direction = 0.0
            obs.extend([direction, signal.strength, signal.confidence])
        
        # 填充不足
        if len(strategy_signals) < self.num_strategies:
            obs.extend([0.0] * ((self.num_strategies - len(strategy_signals)) * 3))
        
        # 市場狀態
        obs.extend([
            (market_state.price - 100) / 100,  # 正規化
            market_state.volatility,
            market_state.trend_strength,
            market_state.volume_ratio,
            market_state.news_sentiment,
            market_state.time_of_day,
            market_state.news_duration_hours,
            float(market_state.related_news_count),
        ])
        
        # 當前倉位
        if current_position:
            pos_type = current_position.get('type', 0)
            pos_size = current_position.get('size', 0.0)
        else:
            pos_type, pos_size = 0, 0.0
        
        obs.extend([float(pos_type), pos_size])
        
        return cast(np.ndarray, np.array(obs, dtype=np.float32))
    
    def save_model(self, filename: str = "ppo_strategy_fusion"):
        """保存模型"""
        filepath = self.model_path / f"{filename}.zip"
        self.model.save(filepath)  # type: ignore
        logger.info(f"💾 模型已保存: {filepath}")
    
    def load_model(self, filename: str = "ppo_strategy_fusion"):
        """載入模型"""
        filepath = self.model_path / f"{filename}.zip"
        if filepath.exists():
            self.model = PPO.load(filepath, env=self.env)  # type: ignore
            logger.info(f"📂 模型已載入: {filepath}")
        else:
            logger.warning(f"⚠️  模型文件不存在: {filepath}")
    
    def evaluate(self, test_data: Any, test_signals: Any) -> Dict:
        """評估模型性能"""
        self.env.market_data = test_data
        self.env.strategy_signals_history = test_signals
        
        obs, _ = self.env.reset()
        done = False
        
        while not done:
            action, _ = self.model.predict(obs, deterministic=True)  # type: ignore
            obs, _, terminated, truncated, _ = self.env.step(action)
            done = terminated or truncated
        
        final_capital = self.env.capital
        total_return = (final_capital - self.env.initial_capital) / self.env.initial_capital
        
        results = {
            'total_return': total_return,
            'final_capital': final_capital,
            'num_trades': len(self.env.trade_history),
            'sharpe_ratio': self._calculate_sharpe(self.env.equity_curve),
        }
        
        logger.info(f"📊 評估結果: 收益={total_return:.2%}, 交易次數={results['num_trades']}")
        
        return results
    
    def _calculate_sharpe(self, equity_curve: List[float]) -> float:
        """計算夏普比率"""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = np.diff(equity_curve) / equity_curve[:-1]
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)  # 年化
        return float(sharpe)


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 RL Meta-Agent - 強化學習策略融合代理")
    print("=" * 80)
    
    if not SB3_AVAILABLE:
        print("❌ 需要安裝 stable-baselines3")
        print("   請執行: pip install stable-baselines3")
        exit(1)
    
    # 創建 Agent
    agent = RLMetaAgent(num_strategies=4)
    
    # 模擬數據
    print("\n📊 準備訓練數據...")
    mock_market_data = [
        {'price': 100 + i * 0.1, 'volatility': 0.5, 'trend_strength': 0.2,
         'volume_ratio': 0.6, 'news_sentiment': 0.1, 'time_of_day': (i % 24) / 24}
        for i in range(100)
    ]
    
    mock_signals = [
        [
            StrategySignal('trend', 'long', 0.7, 0.8),
            StrategySignal('mean_reversion', 'short', 0.6, 0.7),
            StrategySignal('breakout', 'long', 0.5, 0.6),
            StrategySignal('swing', 'neutral', 0.4, 0.5),
        ]
        for _ in range(100)
    ]
    
    # 訓練
    print("\n🎓 開始訓練...")
    try:
        agent.train(
            total_timesteps=10000,
            market_data=mock_market_data,
            strategy_signals_history=mock_signals,
        )
        print("✅ 訓練完成!")
    except Exception as e:
        print(f"❌ 訓練失敗: {e}")
    
    # 測試預測
    print("\n🔮 測試預測...")
    test_signals = [
        StrategySignal('trend', 'long', 0.8, 0.9),
        StrategySignal('breakout', 'long', 0.7, 0.8),
    ]
    test_market = MarketState(
        price=105.0,
        volatility=0.6,
        trend_strength=0.3,
        volume_ratio=0.7,
        news_sentiment=0.2,
        time_of_day=0.5,
    )
    
    action = agent.predict(test_signals, test_market)
    print(f"   決策: {action.action_type}, 倉位: {action.position_size:.2%}")
    
    print("\n" + "=" * 80)
    print("🎉 RL Meta-Agent 測試完成!")
    print("=" * 80)
