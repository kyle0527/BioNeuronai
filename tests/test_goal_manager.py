"""GoalTracker：目標層級追蹤（最小版）的行為驗證。"""

from bioneuronai.planning.goal_manager import GoalConfig, GoalTracker


def test_insufficient_data_before_min_trades():
    tracker = GoalTracker(GoalConfig(min_trades_to_judge=10))
    report = tracker.evaluate(learning_state={"trades": 3, "ewma_pnl_pct": -0.5})
    assert report.status == "INSUFFICIENT_DATA"
    assert report.recommended_risk_scale == 1.0


def test_on_track_when_all_goals_met():
    tracker = GoalTracker(GoalConfig(min_trades_to_judge=5))
    report = tracker.evaluate(
        learning_state={
            "trades": 20,
            "ewma_pnl_pct": 0.002,
            "ewma_win_rate": 0.55,
            "consecutive_losses": 1,
        },
        ledger_summary={"max_drawdown_pct": 1.0},
    )
    assert report.status == "ON_TRACK"
    assert report.violations == []


def test_single_violation_is_at_risk():
    tracker = GoalTracker(GoalConfig(min_trades_to_judge=5))
    report = tracker.evaluate(
        learning_state={
            "trades": 20,
            "ewma_pnl_pct": -0.001,   # 唯一違反項
            "ewma_win_rate": 0.55,
            "consecutive_losses": 0,
        },
    )
    assert report.status == "AT_RISK"
    assert len(report.violations) == 1
    assert report.recommended_risk_scale == 0.75


def test_multiple_violations_is_off_track():
    tracker = GoalTracker(GoalConfig(min_trades_to_judge=5))
    report = tracker.evaluate(
        learning_state={
            "trades": 20,
            "ewma_pnl_pct": -0.01,
            "ewma_win_rate": 0.2,
            "consecutive_losses": 6,
        },
        ledger_summary={"max_drawdown_pct": 8.0},
    )
    assert report.status == "OFF_TRACK"
    assert len(report.violations) == 4
    assert report.recommended_risk_scale == 0.5


def test_report_serializes_for_ledger():
    tracker = GoalTracker()
    payload = tracker.evaluate(learning_state={"trades": 0}).to_dict()
    assert set(payload) == {"status", "violations", "recommended_risk_scale", "goal_name"}
