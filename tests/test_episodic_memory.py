"""EpisodicMemory：熱緩衝 / 冷金庫 / outcome 更新的驗證。"""

import time

from bioneuronai.memory.episodic_memory import EpisodicMemory, ExperienceRecord


def make_record(record_id="r1", symbol="BTCUSDT", **kwargs):
    defaults = dict(
        record_id=record_id,
        symbol=symbol,
        timestamp=time.time(),
        numeric_patches=[[0.0] * 64 for _ in range(16)],
        decoded_direction="LONG",
        outcome="WIN",
        pnl_pct=0.01,
    )
    defaults.update(kwargs)
    return ExperienceRecord(**defaults)


def test_push_and_sample_hot(tmp_path):
    memory = EpisodicMemory(data_dir=tmp_path)
    for i in range(20):
        memory.push(make_record(record_id=f"r{i}"))
    batch = memory.sample_hot(8)
    assert len(batch) == 8
    assert all(isinstance(r, ExperienceRecord) for r in batch)


def test_high_confidence_big_loss_goes_to_cold_vault(tmp_path):
    memory = EpisodicMemory(data_dir=tmp_path)
    record = make_record(
        decoded_confidence=0.9, outcome="LOSS", pnl_pct=-0.08
    )
    is_extreme = memory.push(record)
    assert is_extreme is True
    assert memory.cold_vault.total_count == 1

    # 冷庫持久化：重啟後仍在
    reopened = EpisodicMemory(data_dir=tmp_path)
    assert reopened.cold_vault.total_count == 1


def test_normal_trade_stays_hot_only(tmp_path):
    memory = EpisodicMemory(data_dir=tmp_path)
    is_extreme = memory.push(make_record())
    assert is_extreme is False
    assert memory.cold_vault.total_count == 0


def test_update_outcome_sets_result_and_reward(tmp_path):
    memory = EpisodicMemory(data_dir=tmp_path)
    record = make_record(outcome="PENDING", pnl_pct=0.0)
    memory.push(record)

    updated = memory.update_outcome(
        record, exit_price=51000.0, pnl_pct=0.02, hold_duration_sec=3600
    )
    assert updated.outcome == "WIN"
    assert updated.reward > 0

    losing = make_record(record_id="r-loss", outcome="PENDING")
    memory.update_outcome(losing, exit_price=49000.0, pnl_pct=-0.02, hold_duration_sec=3600)
    assert losing.outcome == "LOSS"
    assert losing.reward < 0


def test_stats_report(tmp_path):
    memory = EpisodicMemory(data_dir=tmp_path)
    memory.push(make_record(outcome="WIN", pnl_pct=0.01, reward=0.01))
    memory.push(make_record(record_id="r2", outcome="LOSS", pnl_pct=-0.01, reward=-0.01))
    stats = memory.get_stats()
    assert stats["total_pushed"] == 2
    assert stats["hot_buffer_size"] == 2
