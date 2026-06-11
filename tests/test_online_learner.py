"""OnlineLearner：LoRA 在線更新迴路的端到端驗證（用輕量替身模型）。

驗證重點：
1. 累積 N 筆結果後自動觸發一次更新
2. 更新真的改變 LoRA 權重（梯度有流動）、骨幹凍結不動
3. checkpoint 儲存與載入可逆
"""

import time

import pytest

torch = pytest.importorskip("torch")
import torch.nn as nn  # noqa: E402

from bioneuronai.core.online_learner import OnlineLearner  # noqa: E402
from bioneuronai.memory.episodic_memory import EpisodicMemory, ExperienceRecord  # noqa: E402


class DummyLoRAModel(nn.Module):
    """符合 OnlineLearner 介面契約的最小模型。"""

    def __init__(self):
        super().__init__()
        self.backbone = nn.Linear(64, 8)
        self.lora_A = nn.Parameter(torch.randn(8, 4) * 0.1)
        self.lora_B = nn.Parameter(torch.randn(4, 65) * 0.1)

    def freeze_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = False

    def lora_parameters(self):
        return [self.lora_A, self.lora_B]

    def forward_signal(self, patches):
        h = self.backbone(patches).mean(dim=1)          # (B, 8)
        raw = h @ self.lora_A @ self.lora_B              # (B, 65)
        decoded = {
            "confidence_probs": torch.softmax(raw[:, 3:6], dim=-1),
            "uncertainty": torch.sigmoid(raw[:, 6]),
        }
        return raw, decoded

    def load_balance_loss(self):
        return torch.tensor(0.0)


def make_experience(i, outcome="WIN"):
    return ExperienceRecord(
        record_id=f"exp{i}",
        symbol="BTCUSDT",
        timestamp=time.time(),
        numeric_patches=[[float(i % 7) / 7.0] * 64 for _ in range(16)],
        decoded_direction="LONG" if i % 2 == 0 else "SHORT",
        decoded_confidence=0.7,
        decoded_uncertainty=0.4,
        outcome=outcome,
        pnl_pct=0.01 if outcome == "WIN" else -0.01,
    )


@pytest.fixture
def learner(tmp_path):
    model = DummyLoRAModel()
    memory = EpisodicMemory(data_dir=tmp_path / "memory")
    return OnlineLearner(
        model=model,
        memory=memory,
        update_every_n=6,
        batch_size=4,
        gradient_accumulation=1,
        checkpoint_dir=tmp_path / "ckpt",
    )


def test_update_triggers_after_n_outcomes(learner):
    metrics = None
    for i in range(6):
        metrics = learner.record_outcome(
            make_experience(i, outcome="WIN" if i % 2 == 0 else "LOSS")
        )
    assert metrics is not None and metrics, "第 6 筆應觸發 LoRA 更新"
    assert metrics["update_step"] == 1
    assert "loss" in metrics


def test_pending_outcome_does_not_count(learner):
    result = learner.record_outcome(make_experience(0, outcome="PENDING"))
    assert result is None
    assert learner._pending_count == 0


def test_update_changes_lora_but_not_backbone(learner):
    model = learner.model
    lora_before = model.lora_A.detach().clone()
    backbone_before = model.backbone.weight.detach().clone()

    for i in range(6):
        learner.record_outcome(make_experience(i, outcome="LOSS"))

    assert not torch.equal(lora_before, model.lora_A.detach()), "LoRA 權重應已更新"
    assert torch.equal(backbone_before, model.backbone.weight.detach()), "骨幹應保持凍結"


def test_checkpoint_save_and_load_roundtrip(tmp_path, learner):
    for i in range(6):
        learner.record_outcome(make_experience(i))
    learner._save_lora_checkpoint()

    lora_trained = learner.model.lora_A.detach().clone()

    # 模擬重啟：新模型 + 新 learner，載入 checkpoint 後權重一致
    fresh_model = DummyLoRAModel()
    fresh_memory = EpisodicMemory(data_dir=tmp_path / "memory2")
    fresh_learner = OnlineLearner(
        model=fresh_model,
        memory=fresh_memory,
        update_every_n=6,
        batch_size=4,
        gradient_accumulation=1,
        checkpoint_dir=learner.checkpoint_dir,
    )
    assert fresh_learner.load_latest_lora() is True
    assert torch.allclose(fresh_model.lora_A.detach(), lora_trained)
    assert fresh_learner._update_count == learner._update_count


def test_insufficient_samples_skips_update(tmp_path):
    model = DummyLoRAModel()
    memory = EpisodicMemory(data_dir=tmp_path / "memory")
    learner = OnlineLearner(
        model=model,
        memory=memory,
        update_every_n=2,
        batch_size=8,           # 大於可用樣本 → 跳過
        gradient_accumulation=1,
        checkpoint_dir=tmp_path / "ckpt",
    )
    metrics = None
    for i in range(2):
        metrics = learner.record_outcome(make_experience(i))
    assert metrics == {}
