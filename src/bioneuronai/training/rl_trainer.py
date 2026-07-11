"""歷史資料 RL 訓練管線 — P2 實作完成

設計目標（docs/PROJECT_STATUS.md P2）：
- 用歷史 K 線資料做策略強化學習，與 backtest 的差異是「迭代更新權重」而非靜態驗證
- 資料來源：複用 backtest/HistoricalDataStream（已存在）
- 環境：gym 風格 reset()/step()，observation = 特徵視窗，action = 方向決策
- reward：複用 core/reward.compute_reward（多目標，已存在）
- 學習目標：Meta-Learner 權重
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.optim as optim

from backtest.data_stream import DEFAULT_DATA_DIR, HistoricalDataStream
from bioneuronai.core.reward import compute_reward
from bioneuronai.strategies.meta_learner.feature_extractor import FeatureExtractor
from bioneuronai.strategies.meta_learner.model import STRATEGY_NAMES, MetaLearnerModel

# 嘗試從 trainer 導入模擬策略方向的函數
try:
    from bioneuronai.strategies.meta_learner.trainer import _simulate_strategy_direction
except ImportError:
    # 回退：若無法導入則在此自定義模擬邏輯
    def _simulate_strategy_direction(ohlcv: np.ndarray, strategy_name: str) -> float:
        c = ohlcv[:, 3].astype(float)
        h = ohlcv[:, 2].astype(float)
        low = ohlcv[:, 1].astype(float)
        if len(c) < 26:
            return 0.0
        if strategy_name == "trend_following":
            sma20 = np.mean(c[-20:])
            sma50 = np.mean(c[-50:]) if len(c) >= 50 else np.mean(c)
            return 1.0 if sma20 > sma50 else -1.0
        elif strategy_name == "mean_reversion":
            sma20 = np.mean(c[-20:])
            std20 = np.std(c[-20:])
            if std20 == 0:
                return 0.0
            z_score = (c[-1] - sma20) / std20
            if z_score > 1.5:
                return -1.0
            elif z_score < -1.5:
                return 1.0
            return 0.0
        elif strategy_name == "breakout":
            high20 = np.max(h[-21:-1])
            low20 = np.min(low[-21:-1])
            if c[-1] > high20:
                return 1.0
            elif c[-1] < low20:
                return -1.0
            return 0.0
        elif strategy_name == "swing_trading":
            if len(c) < 15:
                return 0.0
            deltas = np.diff(c[-15:])
            gains = deltas[deltas > 0]
            losses = -deltas[deltas < 0]
            avg_gain = np.mean(gains) if len(gains) > 0 else 0
            avg_loss = np.mean(losses) if len(losses) > 0 else 1e-8
            rsi = 100 - (100 / (1 + avg_gain / avg_loss))
            if rsi < 35:
                return 1.0
            elif rsi > 65:
                return -1.0
            return 0.0
        elif strategy_name == "direction_change":
            if len(c) < 5:
                return 0.0
            recent_trend = c[-1] - c[-5]
            prev_trend = c[-5] - c[-10] if len(c) >= 10 else 0
            if prev_trend > 0 and recent_trend < 0:
                return -1.0
            elif prev_trend < 0 and recent_trend > 0:
                return 1.0
            return 0.0
        return 0.0

logger = logging.getLogger(__name__)


@dataclass
class RLTrainerConfig:
    """RL 訓練設定（已完成實作）。"""

    symbol: str = "BTCUSDT"
    interval: str = "1h"
    data_dir: Optional[str] = None
    episode_length: int = 500
    total_episodes: int = 100
    learning_target: str = "meta_learner"   # meta_learner / lora / genetic
    reward_config: Optional[Any] = None      # core.reward.RewardConfig
    seed: int = 42
    extra: Dict[str, Any] = field(default_factory=dict)


class HistoricalReplayEnv:
    """gym 風格歷史回放環境。

    契約：
        obs = env.reset()                          # 重置到隨機/指定起點
        obs, reward, done, info = env.step(action) # action: 0=LONG 1=NEUTRAL 2=SHORT
    """

    def __init__(self, config: RLTrainerConfig) -> None:
        self.config = config
        self.stream = HistoricalDataStream(
            symbol=self.config.symbol,
            interval=self.config.interval,
            data_dir=self.config.data_dir or DEFAULT_DATA_DIR,
            speed_multiplier=0,
        )
        self.feature_extractor = FeatureExtractor()
        self.current_step = 0
        self.start_index = 80

    def reset(self) -> np.ndarray:
        """重置環境，載入資料並隨機 seek 到起點"""
        self.stream.load_data()
        total_bars = len(self.stream._data) if self.stream._data is not None else 0
        if total_bars < 120:
            raise ValueError(f"歷史資料長度不足，至少需要 120 根 K 線，目前僅有 {total_bars} 根")

        # 安全起點：至少 80 根 K 線以供特徵計算；安全終點：保留足夠長度供 episode 走完
        max_start = total_bars - self.config.episode_length - 10
        if max_start <= 80:
            self.start_index = 80
        else:
            self.start_index = random.randint(80, max_start)

        self.current_step = 0
        self.stream.seek(self.start_index)
        return self._get_observation()

    def _get_observation(self) -> np.ndarray:
        """從歷史 K 線視窗中提取 60 維市場特徵，與 8 維的事件特徵 (預設全零) 合併為 68 維"""
        klines = self.stream.get_klines_until_now(limit=80)
        ohlcv = np.array([
            [k["open"], k["high"], k["low"], k["close"], k["volume"]]
            for k in klines
        ], dtype=np.float32)

        market_feats = self.feature_extractor.extract(ohlcv)
        if market_feats is None:
            market_feats = np.zeros(60, dtype=np.float32)

        # event_features (8維) 暫時填 0.0，後續可擴充串接真實新聞情緒評分
        event_feats = np.zeros(8, dtype=np.float32)
        obs = np.concatenate([market_feats, event_feats])
        return obs

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """步進環境

        Args:
            action: 0=LONG 1=NEUTRAL 2=SHORT

        Returns:
            Tuple[observation, reward, done, info]
        """
        if self.stream._data is None:
            raise RuntimeError("歷史資料流未初始化")

        # 1. 步進索引與更新
        next_idx = self.start_index + self.current_step + 1
        if next_idx >= len(self.stream._data):
            done = True
            return self._get_observation(), 0.0, done, {}

        self.stream.seek(next_idx)
        self.current_step += 1

        # 2. 計算未來 5 根 K 線的實際收益作為 reward 參考
        curr_idx = self.start_index + self.current_step
        future_bars = self.stream._data.iloc[curr_idx : curr_idx + 5]
        if len(future_bars) > 0:
            start_close = float(future_bars.iloc[0]["close"])
            end_close = float(future_bars.iloc[-1]["close"])
            forward_return = (end_close - start_close) / start_close
        else:
            forward_return = 0.0

        # 3. 將 action 轉換為方向乘數，並使用 core.reward 計算 reward
        direction = 0.0
        if action == 0:
            direction = 1.0
        elif action == 2:
            direction = -1.0

        pnl_pct = direction * forward_return
        reward = compute_reward(pnl_pct=pnl_pct, config=self.config.reward_config)

        # 4. 判斷 done
        done = (self.current_step >= self.config.episode_length) or (next_idx + 5 >= len(self.stream._data))

        obs = self._get_observation()
        info = {
            "forward_return": forward_return,
            "pnl_pct": pnl_pct,
            "current_time": self.stream.get_current_time(),
        }
        return obs, reward, done, info


class RLTrainer:
    """歷史資料 RL 訓練器 — REINFORCE 政策梯度優化。

    契約：
        trainer = RLTrainer(RLTrainerConfig(symbol="BTCUSDT"))
        report = trainer.train()        # 跑完整訓練，回傳績效報告
        trainer.export_weights(path)    # 匯出可被 adaptive_hub / selector 使用的權重
    """

    def __init__(self, config: Optional[RLTrainerConfig] = None) -> None:
        self.config = config or RLTrainerConfig()
        self.env = HistoricalReplayEnv(self.config)
        self.model = MetaLearnerModel()
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3)

    def train(self) -> Dict[str, Any]:
        """使用 REINFORCE (Policy Gradient) 訓練 Meta-Learner。

        優化目標：在狀態 s 下選擇最能獲利的基礎策略機率最優化。
        """
        logger.info("開始 RL 訓練 Meta-Learner 模型 | episodes=%d", self.config.total_episodes)
        self.model.train()

        episode_rewards: List[float] = []

        for ep in range(self.config.total_episodes):
            obs = self.env.reset()
            done = False

            log_probs: List[torch.Tensor] = []
            rewards: List[float] = []

            while not done:
                # 取得 68 維特徵，分別餵入 model
                market_feats = torch.tensor(obs[:60], dtype=torch.float32).unsqueeze(0)
                event_feats = torch.tensor(obs[60:], dtype=torch.float32).unsqueeze(0)

                # 網路輸出 5 個基礎策略的 softmax 權重
                probs = self.model(market_feats, event_feats)[0]

                # 根據權重分佈進行策略採樣 (Categorical Policy)
                dist = torch.distributions.Categorical(probs)
                action_idx = dist.sample()
                log_prob = dist.log_prob(action_idx)

                # 取得採樣到的策略之方向信號並對應環境 action
                klines = self.env.stream.get_klines_until_now(limit=80)
                ohlcv = np.array([
                    [k["open"], k["high"], k["low"], k["close"], k["volume"]]
                    for k in klines
                ], dtype=np.float32)

                selected_strategy = STRATEGY_NAMES[action_idx.item()]
                direction = _simulate_strategy_direction(ohlcv, selected_strategy)

                # 環境方向轉換
                if direction > 0.5:
                    env_action = 0  # LONG
                elif direction < -0.5:
                    env_action = 2  # SHORT
                else:
                    env_action = 1  # NEUTRAL

                # 步進
                next_obs, reward, done, info = self.env.step(env_action)

                log_probs.append(log_prob)
                rewards.append(reward)
                obs = next_obs

            # 計算當前 episode 累計與折扣收益並進行 Policy Gradient 更新
            total_ep_reward = sum(rewards)
            episode_rewards.append(total_ep_reward)

            discounted_return_values: List[float] = []
            G = 0.0
            gamma = 0.99
            for r in reversed(rewards):
                G = r + gamma * G
                discounted_return_values.insert(0, G)

            discounted_returns = torch.tensor(
                discounted_return_values,
                dtype=torch.float32,
            )
            if len(discounted_returns) > 1:
                discounted_returns = (
                    discounted_returns - discounted_returns.mean()
                ) / (discounted_returns.std() + 1e-8)

            policy_loss = torch.tensor(0.0)
            for lp, G_t in zip(log_probs, discounted_returns):
                policy_loss = policy_loss - lp * G_t

            self.optimizer.zero_grad()
            policy_loss.backward()
            self.optimizer.step()

            if (ep + 1) % 10 == 0 or ep == 0:
                logger.info(
                    "Episode %d/%d | Total Reward: %.4f | Policy Loss: %.4f",
                    ep + 1, self.config.total_episodes, total_ep_reward, policy_loss.item()
                )

        report = {
            "symbol": self.config.symbol,
            "total_episodes": self.config.total_episodes,
            "mean_reward": float(np.mean(episode_rewards)),
            "std_reward": float(np.std(episode_rewards)),
            "max_reward": float(np.max(episode_rewards)),
            "min_reward": float(np.min(episode_rewards)),
            "final_episode_reward": float(episode_rewards[-1]),
        }
        logger.info("RL 訓練結束 | 報告: %s", report)
        return report

    def evaluate(self, episodes: int = 10) -> Dict[str, Any]:
        """評估模式，直接使用 Greedy ArgMax 策略選擇"""
        self.model.eval()
        rewards: List[float] = []

        with torch.no_grad():
            for ep in range(episodes):
                obs = self.env.reset()
                done = False
                ep_reward = 0.0

                while not done:
                    market_feats = torch.tensor(obs[:60], dtype=torch.float32).unsqueeze(0)
                    event_feats = torch.tensor(obs[60:], dtype=torch.float32).unsqueeze(0)

                    probs = self.model(market_feats, event_feats)[0]
                    action_idx = torch.argmax(probs)

                    klines = self.env.stream.get_klines_until_now(limit=80)
                    ohlcv = np.array([
                        [k["open"], k["high"], k["low"], k["close"], k["volume"]]
                        for k in klines
                    ], dtype=np.float32)

                    selected_strategy = STRATEGY_NAMES[int(action_idx.item())]
                    direction = _simulate_strategy_direction(ohlcv, selected_strategy)

                    if direction > 0.5:
                        env_action = 0
                    elif direction < -0.5:
                        env_action = 2
                    else:
                        env_action = 1

                    next_obs, reward, done, info = self.env.step(env_action)
                    ep_reward += reward
                    obs = next_obs

                rewards.append(ep_reward)

        report = {
            "evaluation_episodes": episodes,
            "mean_reward": float(np.mean(rewards)),
            "max_reward": float(np.max(rewards)),
            "min_reward": float(np.min(rewards)),
        }
        logger.info("RL 評估結束 | 報告: %s", report)
        return report

    def export_weights(self, path: str) -> None:
        """導出訓練好的模型權重"""
        save_path = Path(path)
        self.model.save(save_path)
        logger.info("RL 模型權重已順利匯出至: %s", save_path)


__all__ = ["RLTrainerConfig", "HistoricalReplayEnv", "RLTrainer"]
