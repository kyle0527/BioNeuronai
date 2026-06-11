"""擴充點契約測試：規劃中能力的介面必須存在且行為誠實。

原則：還沒實作的能力必須 (1) 介面存在（外部可依賴契約開發）
(2) 明確表示未完成（NotImplementedError / 中性回傳 / 警告），
不可默默假裝成功。
"""

from types import SimpleNamespace

import pytest


# ── P2：歷史 RL 訓練管線（骨架，必須明確未實作）────────────────────────

def test_rl_trainer_interface_exists_but_raises():
    from bioneuronai.training import HistoricalReplayEnv, RLTrainer, RLTrainerConfig

    config = RLTrainerConfig(symbol="BTCUSDT", learning_target="meta_learner")
    trainer = RLTrainer(config)
    env = HistoricalReplayEnv(config)

    with pytest.raises(NotImplementedError):
        trainer.train()
    with pytest.raises(NotImplementedError):
        trainer.evaluate()
    with pytest.raises(NotImplementedError):
        trainer.export_weights("/tmp/w.json")
    with pytest.raises(NotImplementedError):
        env.reset()
    with pytest.raises(NotImplementedError):
        env.step(0)


# ── P1：新聞方向偏好（最小過渡版，契約固定）────────────────────────────

def make_news_adapter():
    from rag.services.news_adapter import NewsAdapter
    return NewsAdapter(enable_event_detection=False)


def test_direction_bias_contract_and_neutral_default(monkeypatch):
    adapter = make_news_adapter()
    monkeypatch.setattr(adapter, "get_event_context", lambda symbol: None)

    bias = adapter.get_direction_bias("BTCUSDT")
    assert set(bias) >= {"direction", "strength", "reason"}
    assert bias["direction"] == "NEUTRAL"
    assert bias["strength"] == 0.0
    assert bias["implemented_level"] == "minimal"  # 誠實標注未完成


def test_direction_bias_weak_event_stays_neutral(monkeypatch):
    adapter = make_news_adapter()
    ctx = SimpleNamespace(
        event_score=2.0, decay_factor=1.0, source_confidence=0.9, headline=None
    )
    monkeypatch.setattr(adapter, "get_event_context", lambda symbol: ctx)
    bias = adapter.get_direction_bias("BTCUSDT")
    assert bias["direction"] == "NEUTRAL"


def test_direction_bias_strong_events_give_direction(monkeypatch):
    adapter = make_news_adapter()
    bull = SimpleNamespace(
        event_score=8.0, decay_factor=0.9, source_confidence=0.8, headline="ETF approved"
    )
    monkeypatch.setattr(adapter, "get_event_context", lambda symbol: bull)
    bias = adapter.get_direction_bias("BTCUSDT")
    assert bias["direction"] == "LONG"
    assert 0 < bias["strength"] <= 1.0

    bear = SimpleNamespace(
        event_score=-7.0, decay_factor=1.0, source_confidence=0.7, headline=None
    )
    monkeypatch.setattr(adapter, "get_event_context", lambda symbol: bear)
    assert adapter.get_direction_bias("BTCUSDT")["direction"] == "SHORT"


def test_direction_bias_error_returns_neutral(monkeypatch):
    adapter = make_news_adapter()

    def boom(symbol):
        raise RuntimeError("feed down")

    monkeypatch.setattr(adapter, "get_event_context", boom)
    bias = adapter.get_direction_bias("BTCUSDT")
    assert bias["direction"] == "NEUTRAL"
    assert "error" in bias["reason"]


# ── P3：TinyLLM v2 模式旗標（必須警告未實作，不可默默假裝切換）──────────

def test_enable_v2_mode_warns_not_implemented(caplog):
    pytest.importorskip("torch")
    import logging

    from bioneuronai.core.inference_engine import InferenceEngine

    engine = InferenceEngine(warmup=False)
    with caplog.at_level(logging.WARNING):
        engine.enable_v2_mode()
    assert engine.use_v2_mode is True
    assert any("尚未實作" in record.message for record in caplog.records)
