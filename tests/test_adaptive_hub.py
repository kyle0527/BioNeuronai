"""AdaptiveLearningHub：自適應閉環中樞的行為驗證。"""

from bioneuronai.core.adaptive_hub import AdaptiveLearningHub


def make_hub(tmp_path, **kwargs):
    return AdaptiveLearningHub(state_path=tmp_path / "hub.json", **kwargs)


def test_weights_shift_toward_winning_strategy(tmp_path):
    hub = make_hub(tmp_path, min_samples=3)
    for _ in range(10):
        hub.record_trade("trend_following", "BTCUSDT", pnl_pct=0.01)
        hub.record_trade("mean_reversion", "BTCUSDT", pnl_pct=-0.01)
    weights = hub.get_strategy_weights()
    assert weights["trend_following"] > weights["mean_reversion"]
    assert abs(sum(weights.values()) - 1.0) < 1e-6


def test_min_weight_floor_prevents_permanent_ban(tmp_path):
    hub = make_hub(tmp_path, min_samples=1, min_weight=0.05)
    for _ in range(50):
        hub.record_trade("winner", "BTCUSDT", pnl_pct=0.05)
        hub.record_trade("loser", "BTCUSDT", pnl_pct=-0.05)
    weights = hub.get_strategy_weights()
    assert weights["loser"] >= 0.04  # floor 後再正規化，仍保有探索空間


def test_should_avoid_after_repeated_losses_on_symbol(tmp_path):
    hub = make_hub(tmp_path, min_samples=3, avoid_consecutive_losses=4)
    for _ in range(5):
        hub.record_trade("breakout", "ETHUSDT", pnl_pct=-0.02)
    assert hub.should_avoid("breakout", "ETHUSDT") is True
    # 同策略在其他幣對不受影響
    assert hub.should_avoid("breakout", "BTCUSDT") is False
    assert {"strategy": "breakout", "symbol": "ETHUSDT"} in hub.get_avoid_list()


def test_insufficient_samples_never_avoided(tmp_path):
    hub = make_hub(tmp_path, min_samples=10)
    for _ in range(3):
        hub.record_trade("breakout", "ETHUSDT", pnl_pct=-0.05)
    assert hub.should_avoid("breakout", "ETHUSDT") is False


def test_risk_multiplier_shrinks_on_losing_streak(tmp_path):
    hub = make_hub(tmp_path, min_samples=3)
    assert hub.get_risk_multiplier() == 1.0
    for _ in range(5):
        hub.record_trade("trend_following", "BTCUSDT", pnl_pct=-0.02)
    assert hub.get_risk_multiplier() == 0.5


def test_state_survives_restart(tmp_path):
    hub = make_hub(tmp_path)
    for _ in range(6):
        hub.record_trade("swing_trading", "BTCUSDT", pnl_pct=0.015, market_regime="TRENDING_BULL")

    reloaded = make_hub(tmp_path)
    assert reloaded.global_stats.trades == 6
    assert reloaded.strategy_stats["swing_trading"].trades == 6
    assert reloaded.pair_stats["swing_trading"]["BTCUSDT"].trades == 6
    assert reloaded.regime_stats["TRENDING_BULL"].trades == 6
    assert reloaded.get_strategy_weights() == hub.get_strategy_weights()


def test_corrupt_state_file_starts_clean(tmp_path):
    state = tmp_path / "hub.json"
    state.write_text("{ not valid json", encoding="utf-8")
    hub = AdaptiveLearningHub(state_path=state)
    assert hub.global_stats.trades == 0


def test_learning_state_summary(tmp_path):
    hub = make_hub(tmp_path, min_samples=2, avoid_consecutive_losses=3)
    for _ in range(4):
        hub.record_trade("breakout", "DOGEUSDT", pnl_pct=-0.03)
    state = hub.get_learning_state()
    assert state["trades"] == 4
    assert state["consecutive_losses"] == 4
    assert state["ewma_pnl_pct"] < 0
    assert "DOGEUSDT" in state["avoid_symbols"]
    assert state["risk_multiplier"] == 0.5
    assert "breakout" in state["strategy_weights"]
