"""AdaptationController：含學習狀態的自我修正規則驗證。"""

from bioneuronai.planning.adaptation_controller import (
    AdaptationController,
    AutonomousAction,
    AutonomousMode,
)


PLAN_OK = {"execution_ready": True}
PRETRADE_OK = [
    {"symbol": "BTCUSDT", "overall_assessment": {"status": "EXECUTE"}},
]
LEDGER_EMPTY = {"record_count": 0, "realized_count": 0, "consecutive_losses": 0}


def evaluate(controller=None, **overrides):
    controller = controller or AdaptationController()
    kwargs = {
        "mode": AutonomousMode.PAPER_AUTO.value,
        "plan": PLAN_OK,
        "pretrade_results": PRETRADE_OK,
        "ledger_summary": LEDGER_EMPTY,
        "intended_action": "BUY",
    }
    kwargs.update(overrides)
    return controller.evaluate(**kwargs)


def test_baseline_paper_auto_executes():
    decision = evaluate()
    assert decision.action == AutonomousAction.PAPER_TRADE
    assert decision.can_execute is True
    assert decision.risk_multiplier == 1.0


def test_legacy_callers_without_learning_state_still_work():
    # learning_state 為可選參數，舊呼叫端不受影響
    decision = evaluate(learning_state=None)
    assert decision.can_execute is True


def test_negative_expectancy_reduces_risk():
    decision = evaluate(
        learning_state={"trades": 30, "ewma_pnl_pct": -0.004, "consecutive_losses": 0}
    )
    assert decision.risk_multiplier <= 0.5
    assert any("learning_expectancy_negative" in r for r in decision.reasons)
    assert decision.confidence_floor >= 0.65


def test_learning_consecutive_losses_slows_down():
    decision = evaluate(
        learning_state={"trades": 30, "ewma_pnl_pct": 0.001, "consecutive_losses": 4}
    )
    assert decision.risk_multiplier <= 0.5
    assert decision.next_interval_minutes == 120


def test_insufficient_learning_samples_ignored():
    decision = evaluate(
        learning_state={"trades": 3, "ewma_pnl_pct": -0.05, "consecutive_losses": 2}
    )
    assert decision.risk_multiplier == 1.0
    assert decision.can_execute is True


def test_hub_risk_multiplier_takes_more_conservative_value():
    decision = evaluate(learning_state={"trades": 0, "risk_multiplier": 0.75})
    assert decision.risk_multiplier == 0.75


def test_avoided_symbol_blocks_execution():
    decision = evaluate(
        learning_state={"trades": 20, "ewma_pnl_pct": 0.002, "avoid_symbols": ["BTCUSDT"]}
    )
    assert decision.can_execute is False
    assert "symbol_deprioritized_by_learning" in decision.reasons
    assert decision.action in (AutonomousAction.WAIT, AutonomousAction.OBSERVE)


def test_drawdown_stop_still_dominates():
    decision = evaluate(
        ledger_summary={"consecutive_losses": 0, "max_drawdown_pct": 9.0},
        learning_state={"trades": 50, "ewma_pnl_pct": 0.01},
    )
    assert decision.action == AutonomousAction.STOP
    assert decision.risk_multiplier == 0.0
