"""歷史資料 RL 訓練管線 — P2 擴充點（介面骨架，尚未實作）

⚠️ 狀態：NOT IMPLEMENTED。這個檔案存在的目的是固定介面契約，
讓後續實作（或外部貢獻者）有明確的接入點，而不是讓人誤以為功能已完成。
所有方法在實作完成前一律 raise NotImplementedError。

設計目標（docs/PROJECT_STATUS.md P2）：
- 用歷史 K 線資料做策略強化學習，與 backtest 的差異是「迭代更新權重」
  而非靜態驗證
- 資料來源：複用 backtest/HistoricalDataStream（已存在）
- 環境：gym 風格 reset()/step()，observation = 特徵視窗，action = 方向決策
- reward：複用 core/reward.compute_reward（多目標，已存在）
- 學習目標：可選 (a) Meta-Learner 權重 (b) TinyLLM v2 LoRA (c) 連接
  core/self_improvement.py 的遺傳算法做策略參數搜索

完成的前置依賴（皆已存在）：
- backtest.HistoricalDataStream     歷史 K 線回放
- core.reward.compute_reward        多目標 reward
- core.adaptive_hub                 訓練結果 → 策略權重的落地通道
- memory.episodic_memory            訓練樣本緩衝
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

_NOT_IMPLEMENTED_MSG = (
    "歷史 RL 訓練管線尚未實作（P2 規劃中）。"
    "介面契約見本模組 docstring 與 docs/PROJECT_STATUS.md。"
    "在線學習（LoRA）已可用：core/online_learner.py。"
)


@dataclass
class RLTrainerConfig:
    """RL 訓練設定（介面已定，欄位可能隨實作調整）。"""

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
    """gym 風格歷史回放環境 — 介面骨架。

    契約：
        obs = env.reset()                          # 重置到隨機/指定起點
        obs, reward, done, info = env.step(action) # action: 0=LONG 1=NEUTRAL 2=SHORT
    """

    def __init__(self, config: RLTrainerConfig) -> None:
        self.config = config

    def reset(self) -> Any:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    def step(self, action: int) -> Tuple[Any, float, bool, Dict[str, Any]]:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)


class RLTrainer:
    """歷史資料 RL 訓練器 — 介面骨架。

    契約：
        trainer = RLTrainer(RLTrainerConfig(symbol="BTCUSDT"))
        report = trainer.train()        # 跑完整訓練，回傳績效報告
        trainer.export_weights(path)    # 匯出可被 adaptive_hub / selector 使用的權重
    """

    def __init__(self, config: Optional[RLTrainerConfig] = None) -> None:
        self.config = config or RLTrainerConfig()

    def train(self) -> Dict[str, Any]:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    def evaluate(self, episodes: int = 10) -> Dict[str, Any]:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    def export_weights(self, path: str) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)


__all__ = ["RLTrainerConfig", "HistoricalReplayEnv", "RLTrainer"]
