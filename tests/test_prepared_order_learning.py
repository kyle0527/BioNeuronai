"""Prepared paper order 與 ActionRecord/LoRA 閉環的契約測試。"""

from types import SimpleNamespace

import numpy as np

from bioneuronai.core.trading_engine import TradingEngine
from bioneuronai.data.paper_binance import PaperBinanceFuturesConnector
from bioneuronai.memory.episodic_memory import EpisodicMemory


class FilledConnector:
    def place_order(self, **_kwargs):
        return SimpleNamespace(
            status="FILLED",
            order_id="paper-001",
            price=101.25,
            error="",
        )


class LearnerSpy:
    def __init__(self):
        self.calls = []

    def record_outcome(self, experience, *, memory_already_recorded=False):
        self.calls.append((experience, memory_already_recorded))
        return None


def test_prepared_paper_order_preserves_actual_ai_snapshot_and_records_once(tmp_path):
    """成交後只能用本輪真實模型輸入建立 T0/T1，T2 只推入記憶一次。"""
    engine = TradingEngine.__new__(TradingEngine)
    engine.connector = FilledConnector()
    engine.episodic_memory = EpisodicMemory(data_dir=tmp_path / "memory")
    engine.online_learner = LearnerSpy()
    engine.adaptive_hub = None
    engine.strategy = SimpleNamespace()
    engine._pending_action_records = {}
    engine._pending_strategy_names = {}

    patches = np.arange(16 * 64, dtype=np.float32).reshape(16, 64) / 1000.0
    raw_signal = np.linspace(-1.0, 1.0, 65, dtype=np.float32)
    result = engine.execute_prepared_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.2,
        stop_loss=99.0,
        take_profit=105.0,
        learning_context={
            "numeric_patches": patches.tolist(),
            "raw_signal": raw_signal.tolist(),
            "signal": {
                "confidence": 0.73,
                "suggested_leverage": 3,
                "suggested_position_size": 0.2,
                "market_regime": "ranging_wide",
            },
            "price_at_decision": 101.0,
            "text_context": "News memory: no active strategic event.",
        },
    )

    assert result.order_id == "paper-001"
    record = engine._pending_action_records["BTCUSDT"]
    assert record.numeric_patches == patches.tolist()
    assert record.raw_signal == raw_signal.tolist()
    assert record.entry_price == 101.25
    assert record.actual_position_size == 20.25

    engine.notify_trade_closed(
        strategy_name="autonomous_paper",
        realized_pnl=1.0,
        entry_price=101.25,
        symbol="BTCUSDT",
        exit_price=106.25,
        exit_reason="TP_HIT",
    )

    assert engine.episodic_memory.get_stats()["total_pushed"] == 1
    assert engine.online_learner.calls[0][1] is True


def test_paper_connector_restores_open_position_and_protective_order(tmp_path):
    """AI 自主程序重啟後仍看得到實倉與保護單，不能重複進場。"""
    first = PaperBinanceFuturesConnector(log_dir=tmp_path, initial_balance=500.0)
    account = first.virtual_account
    account.update_price("BTCUSDT", 100.0)
    account.place_order("BTCUSDT", "BUY", "MARKET", 1.0)
    account.place_order(
        "BTCUSDT",
        "SELL",
        "STOP_MARKET",
        1.0,
        stop_price=90.0,
        reduce_only=True,
    )

    resumed = PaperBinanceFuturesConnector(log_dir=tmp_path, initial_balance=999.0)

    assert resumed.get_paper_state()["restored_from_state"] is True
    assert resumed.virtual_account.has_open_position("BTCUSDT")
    assert len(
        resumed.virtual_account.get_open_orders(
            symbol="BTCUSDT", reduce_only=True
        )
    ) == 1


def test_paper_connector_deduplicates_persisted_autonomous_intent(tmp_path):
    """同一 AI intent 在重試或重啟後只能對帳至原訂單，不得再次開倉。"""
    first = PaperBinanceFuturesConnector(log_dir=tmp_path, initial_balance=500.0)

    def set_local_price(symbol, fallback_price=None):
        price = float(fallback_price or 100.0)
        first.virtual_account.update_price(symbol, price)
        return price

    first._refresh_virtual_price = set_local_price
    first_result = first.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1.0,
        stop_loss=90.0,
        client_order_id="autonomous-test-intent",
    )
    retried_result = first.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1.0,
        stop_loss=90.0,
        client_order_id="autonomous-test-intent",
    )

    resumed = PaperBinanceFuturesConnector(log_dir=tmp_path, initial_balance=999.0)
    resumed_result = resumed.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1.0,
        stop_loss=90.0,
        client_order_id="autonomous-test-intent",
    )

    assert first_result.order_id == retried_result.order_id == resumed_result.order_id
    assert resumed.virtual_account.get_position("BTCUSDT").quantity == 1.0
    assert len(resumed.virtual_account.get_open_orders(symbol="BTCUSDT")) == 1
