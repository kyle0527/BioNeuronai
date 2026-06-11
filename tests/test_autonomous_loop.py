"""自主閉環的端到端驗證（以 stub 元件隔離外部依賴）。

驗證重點：
1. trade outcome 會回寫 decision ledger，被 summarize_decisions 看見
2. 學習中樞的狀態會影響下一輪 adaptation（自我修正閉環真的閉合）
3. run_forever 連續多輪、STOP 時自動停機
"""

import asyncio
from types import SimpleNamespace

import pytest

from bioneuronai.core.adaptive_hub import AdaptiveLearningHub
from bioneuronai.planning.adaptation_controller import (
    AdaptationController,
    AutonomousAction,
)
from bioneuronai.planning.autonomous_operator import (
    AutonomousOperator,
    AutonomousOperatorConfig,
)
from bioneuronai.planning.decision_ledger import DecisionLedger


class StubPlanController:
    async def create_comprehensive_plan(self, klines, account_balance, symbol):
        return {"status": "READY", "execution_ready": True, "steps_results": {}}


class StubPretradeChecker:
    def execute_pretrade_check(self, symbol, intended_action, signal_source):
        return {
            "symbol": symbol,
            "overall_assessment": {"status": "EXECUTE", "score_percentage": 90},
            "order_parameters": {},
        }


class FakeVirtualAccount:
    def __init__(self):
        self._close_callback = None
        self.price_updates = []

    def set_close_callback(self, callback):
        self._close_callback = callback

    def update_price(self, symbol, price):
        self.price_updates.append((symbol, price))


class FakeConnector:
    """替身 paper 連接器：可由測試手動觸發平倉回調。"""

    def __init__(self, price=100.0):
        self.price = price
        self.virtual_account = FakeVirtualAccount()
        self.orders = []

    def get_ticker_price(self, symbol):
        return SimpleNamespace(close=self.price)

    def place_order(self, **kwargs):
        self.orders.append(kwargs)
        return SimpleNamespace(to_dict=lambda: dict(kwargs))

    def get_paper_state(self):
        return {"orders": len(self.orders)}

    def close_position(self, symbol, exit_price, reason="SL_HIT"):
        entry = self.orders[-1] if self.orders else {}
        side = entry.get("side", "BUY")
        qty = float(entry.get("quantity", 1.0))
        direction = 1.0 if side == "BUY" else -1.0
        pnl = (exit_price - self.price) * qty * direction
        self.virtual_account._close_callback(symbol, pnl, self.price, exit_price, reason)


def make_operator(tmp_path, mode="paper_auto", execute_paper=True, connector=None):
    ledger = DecisionLedger(tmp_path / "ledger.jsonl")
    hub = AdaptiveLearningHub(state_path=tmp_path / "hub.json", min_samples=3)
    operator = AutonomousOperator(
        AutonomousOperatorConfig(
            mode=mode,
            symbol="BTCUSDT",
            execute_paper=execute_paper,
        ),
        plan_controller=StubPlanController(),
        pretrade_checker=StubPretradeChecker(),
        adaptation_controller=AdaptationController(),
        ledger=ledger,
        learning_hub=hub,
    )
    operator._paper_connector = connector or FakeConnector()
    operator._paper_connector.virtual_account.set_close_callback(operator._on_paper_close)
    return operator


def test_cycle_executes_paper_trade_and_logs_learning_state(tmp_path):
    operator = make_operator(tmp_path)
    record = asyncio.run(operator.run_once())

    assert record["final_action"] == AutonomousAction.PAPER_TRADE.value
    assert record["paper_execution"] is not None
    assert record["learning_state"] is not None
    assert "BTCUSDT" in operator._open_executions


def test_trade_outcome_feeds_ledger_and_hub(tmp_path):
    connector = FakeConnector(price=100.0)
    operator = make_operator(tmp_path, connector=connector)
    asyncio.run(operator.run_once())

    # 模擬止損出場（-5%）
    connector.close_position("BTCUSDT", exit_price=95.0, reason="SL_HIT")

    assert "BTCUSDT" not in operator._open_executions
    summary = operator.ledger.summarize()
    assert summary["realized_count"] == 1
    assert summary["losses"] == 1
    assert operator.learning_hub.global_stats.trades == 1
    assert operator.learning_hub.global_stats.last_pnl_pct == pytest.approx(-0.05)


def test_losing_streak_triggers_self_correction(tmp_path):
    """連續虧損 → 下一輪 adaptation 自動降風險：閉環成立的直接證據。"""
    connector = FakeConnector(price=100.0)
    operator = make_operator(tmp_path, connector=connector)

    for _ in range(4):
        record = asyncio.run(operator.run_once())
        if record["paper_execution"] is not None:
            connector.close_position("BTCUSDT", exit_price=95.0, reason="SL_HIT")

    final = asyncio.run(operator.run_once())
    adaptation = final["adaptation"]
    assert adaptation["risk_multiplier"] <= 0.5
    assert any(
        "consecutive_losses" in reason or "expectancy_negative" in reason
        for reason in adaptation["reasons"]
    )


def test_run_forever_executes_multiple_cycles(tmp_path):
    operator = make_operator(tmp_path, mode="advisor", execute_paper=False)
    records = asyncio.run(operator.run_forever(max_cycles=3, interval_scale=0.0))
    assert len(records) == 3
    assert all(r["final_action"] == AutonomousAction.ADVISE_ONLY.value for r in records)
    assert [r["cycle"] for r in records] == [1, 2, 3]


def test_run_forever_stops_on_drawdown_stop(tmp_path):
    operator = make_operator(tmp_path, mode="paper_auto", execute_paper=False)
    # 預先注入大幅回撤的歷史結果 → 第一輪就應 STOP
    operator.ledger.append({
        "type": "trade_outcome",
        "outcome": {"pnl": -500.0, "max_drawdown_pct": 10.0},
    })
    records = asyncio.run(operator.run_forever(max_cycles=5, interval_scale=0.0))
    assert len(records) == 1
    assert records[0]["final_action"] == AutonomousAction.STOP.value


def test_legacy_adaptation_controller_without_learning_state(tmp_path):
    """注入不支援 learning_state 的舊版 controller 仍可運作。"""

    class LegacyController:
        def evaluate(self, *, mode, plan, pretrade_results, ledger_summary, intended_action):
            return AdaptationController().evaluate(
                mode=mode,
                plan=plan,
                pretrade_results=pretrade_results,
                ledger_summary=ledger_summary,
                intended_action=intended_action,
            )

    ledger = DecisionLedger(tmp_path / "ledger.jsonl")
    operator = AutonomousOperator(
        AutonomousOperatorConfig(mode="advisor"),
        plan_controller=StubPlanController(),
        pretrade_checker=StubPretradeChecker(),
        adaptation_controller=LegacyController(),
        ledger=ledger,
        learning_hub=AdaptiveLearningHub(state_path=tmp_path / "hub.json"),
    )
    record = asyncio.run(operator.run_once())
    assert record["final_action"] == AutonomousAction.ADVISE_ONLY.value
