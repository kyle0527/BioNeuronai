import asyncio
import sys
from pathlib import Path

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_decision_ledger_summary_counts_losses(tmp_path):
    from bioneuronai.planning.decision_ledger import DecisionLedger

    ledger = DecisionLedger(tmp_path / "ledger.jsonl")
    ledger.append({"final_action": "paper_trade", "outcome": {"pnl": 5.0}})
    ledger.append({"final_action": "paper_trade", "outcome": {"pnl": -2.0}})
    ledger.append({"final_action": "wait", "outcome": {"pnl": -1.0, "max_drawdown_pct": 3.2}})

    summary = ledger.summarize()

    assert summary["record_count"] == 3
    assert summary["wins"] == 1
    assert summary["losses"] == 2
    assert summary["consecutive_losses"] == 2
    assert summary["max_drawdown_pct"] == 3.2
    assert summary["action_counts"]["paper_trade"] == 2


def test_adaptation_controller_selects_paper_trade_for_clean_candidate():
    from bioneuronai.planning.adaptation_controller import AdaptationController

    decision = AdaptationController().evaluate(
        mode="paper_auto",
        plan={"execution_ready": True},
        pretrade_results=[
            {
                "symbol": "BTCUSDT",
                "fundamentals": {"no_major_negative": True, "overall_status": "GOOD"},
                "overall_assessment": {"status": "EXECUTE"},
            }
        ],
        ledger_summary={"consecutive_losses": 0, "max_drawdown_pct": 0.0},
        intended_action="BUY",
    )

    assert decision.action.value == "paper_trade"
    assert decision.can_execute is True
    assert decision.selected_symbol == "BTCUSDT"


def test_adaptation_controller_stops_on_drawdown():
    from bioneuronai.planning.adaptation_controller import AdaptationController

    decision = AdaptationController().evaluate(
        mode="paper_auto",
        plan={"execution_ready": True},
        pretrade_results=[
            {"symbol": "BTCUSDT", "overall_assessment": {"status": "EXECUTE"}}
        ],
        ledger_summary={"max_drawdown_pct": 6.0},
        intended_action="BUY",
    )

    assert decision.action.value == "stop"
    assert decision.can_execute is False
    assert decision.risk_multiplier == 0.0


class _FakePlanController:
    async def create_comprehensive_plan(self, klines, account_balance, symbol):
        return {
            "status": "COMPLETED",
            "execution_ready": True,
            "steps_results": {
                9: {
                    "recommended_pair": "ETHUSDT",
                    "pairs": [{"symbol": "ETHUSDT"}, {"symbol": "BTCUSDT"}],
                }
            },
        }


class _FakePretradeChecker:
    def execute_pretrade_check(self, symbol, signal_source="AI_FUSION", intended_action="BUY"):
        return {
            "symbol": symbol,
            "overall_assessment": {
                "status": "EXECUTE",
                "score_percentage": 90,
                "technical_status": "STRONG",
                "fundamental_status": "GOOD",
                "risk_status": "ACCEPTABLE",
                "recommendation": "ok",
            },
            "fundamentals": {
                "no_major_negative": True,
                "overall_status": "GOOD",
            },
        }


def test_autonomous_operator_run_once_records_decision(tmp_path):
    from bioneuronai.planning.autonomous_operator import (
        AutonomousOperator,
        AutonomousOperatorConfig,
    )
    from bioneuronai.planning.decision_ledger import DecisionLedger

    config = AutonomousOperatorConfig(
        mode="advisor",
        symbol="BTCUSDT",
        max_pairs=2,
        ledger_path=str(tmp_path / "ledger.jsonl"),
    )
    operator = AutonomousOperator(
        config,
        plan_controller=_FakePlanController(),
        pretrade_checker=_FakePretradeChecker(),
        ledger=DecisionLedger(config.ledger_path),
    )

    record = asyncio.run(operator.run_once())

    assert record["final_action"] == "advise_only"
    assert record["candidates"] == ["ETHUSDT", "BTCUSDT"]
    assert record["pretrade_summary"][0]["status"] == "EXECUTE"
    assert Path(config.ledger_path).exists()
