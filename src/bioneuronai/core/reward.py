"""多目標 Reward Shaping — 自主學習的目標函數

單一 PnL reward 會讓模型學出「賭大」行為；自主運作需要同時權衡：
- 盈虧（主目標）
- 持倉效率（資金佔用時間越短越好）
- 信心校準（高信心虧損要額外懲罰，否則模型學不會「不確定時收手」）
- 風控紀律（爆倉是不可接受的失敗，懲罰遠重於一般虧損）

所有權重集中在 RewardConfig，方便實驗與回測比較。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RewardConfig:
    """多目標 reward 權重配置。"""

    # 持倉效率：超過一天的持倉，時間因子最低降到 min_time_factor
    time_horizon_sec: float = 86400.0
    min_time_factor: float = 0.5

    # 不確定性懲罰：uncertainty=1 時 reward 打 (1 - scale) 折
    uncertainty_scale: float = 0.5

    # 過度自信懲罰：confidence 超過閾值且虧損時，按超出量加重懲罰
    overconfidence_threshold: float = 0.7
    overconfidence_scale: float = 1.0

    # 風控紀律：爆倉的固定額外懲罰（以 pnl_pct 尺度計）
    liquidation_penalty: float = 0.05

    # 交易內最大回撤懲罰（若有提供 max_adverse_excursion_pct）
    drawdown_scale: float = 0.3

    # reward 裁剪範圍，避免極端樣本主導梯度
    clip: float = 1.0


def compute_reward(
    pnl_pct: float,
    hold_duration_sec: float = 0.0,
    uncertainty: float = 0.5,
    confidence: float = 0.0,
    exit_reason: str = "MANUAL",
    max_adverse_excursion_pct: Optional[float] = None,
    config: Optional[RewardConfig] = None,
) -> float:
    """計算多目標 reward。

    Args:
        pnl_pct: 已實現損益比例（含手續費）
        hold_duration_sec: 持倉時間（秒）
        uncertainty: 模型決策時的不確定性 (0-1)
        confidence: 模型決策時的信心 (0-1)
        exit_reason: SL_HIT / TP_HIT / MANUAL / TIMEOUT / LIQUIDATION
        max_adverse_excursion_pct: 持倉期間最大浮虧比例（可選）
        config: 權重配置，None 則用預設
    """
    cfg = config or RewardConfig()

    # 主目標：盈虧 × 時間效率 × 不確定性校準
    time_factor = max(cfg.min_time_factor, 1.0 - hold_duration_sec / cfg.time_horizon_sec)
    uncertainty_factor = 1.0 - uncertainty * cfg.uncertainty_scale
    reward = pnl_pct * time_factor * uncertainty_factor

    # 過度自信懲罰：高信心 + 虧損 → 額外負向信號
    if pnl_pct < 0 and confidence > cfg.overconfidence_threshold:
        excess = confidence - cfg.overconfidence_threshold
        reward -= excess * abs(pnl_pct) * cfg.overconfidence_scale

    # 爆倉是風控失敗，不只是虧損
    if str(exit_reason).upper() == "LIQUIDATION":
        reward -= cfg.liquidation_penalty

    # 持倉期間吃過大浮虧（即使最後獲利）也應被抑制
    if max_adverse_excursion_pct is not None and max_adverse_excursion_pct > 0:
        reward -= max_adverse_excursion_pct * cfg.drawdown_scale

    return max(-cfg.clip, min(cfg.clip, reward))


__all__ = ["RewardConfig", "compute_reward"]
