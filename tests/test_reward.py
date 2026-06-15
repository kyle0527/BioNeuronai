"""多目標 reward shaping 的行為驗證。"""

from bioneuronai.core.reward import RewardConfig, compute_reward


def test_profit_gives_positive_reward():
    assert compute_reward(pnl_pct=0.02) > 0


def test_loss_gives_negative_reward():
    assert compute_reward(pnl_pct=-0.02) < 0


def test_long_hold_reduces_reward():
    fast = compute_reward(pnl_pct=0.02, hold_duration_sec=600)
    slow = compute_reward(pnl_pct=0.02, hold_duration_sec=86400 * 2)
    assert fast > slow > 0


def test_overconfident_loss_punished_harder():
    humble = compute_reward(pnl_pct=-0.03, confidence=0.5)
    overconfident = compute_reward(pnl_pct=-0.03, confidence=0.95)
    assert overconfident < humble


def test_liquidation_punished_harder_than_stop_loss():
    sl = compute_reward(pnl_pct=-0.03, exit_reason="SL_HIT")
    liq = compute_reward(pnl_pct=-0.03, exit_reason="LIQUIDATION")
    assert liq < sl


def test_adverse_excursion_reduces_reward():
    clean = compute_reward(pnl_pct=0.02, max_adverse_excursion_pct=0.0)
    scary = compute_reward(pnl_pct=0.02, max_adverse_excursion_pct=0.05)
    assert clean > scary


def test_high_uncertainty_dampens_magnitude():
    confident = compute_reward(pnl_pct=0.02, uncertainty=0.0)
    unsure = compute_reward(pnl_pct=0.02, uncertainty=1.0)
    assert confident > unsure > 0


def test_reward_clipped():
    cfg = RewardConfig(clip=1.0)
    assert compute_reward(pnl_pct=50.0, config=cfg) == 1.0
    assert compute_reward(pnl_pct=-50.0, config=cfg) == -1.0
