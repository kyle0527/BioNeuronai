"""LoRA 在線學習器：從交易結果中即時更新模型

設計原則：
- 骨幹永久凍結，只更新 LoRA A/B 矩陣（防災難性遺忘）
- 每累積 N 筆完整的 ActionRecord 觸發一次微更新
- 損失 = 策略損失（方向預測）+ 信心校準損失 + 不確定性損失 + MoE 均衡損失
- 更新後自動存 checkpoint
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from bioneuronai.memory.episodic_memory import EpisodicMemory, ExperienceRecord

logger = logging.getLogger(__name__)


class OnlineLearner:
    """LoRA 在線微更新器。

    使用方式：
        learner = OnlineLearner(model, memory, device="cpu")
        # 每次交易出場後：
        learner.record_outcome(action_record)
        # 達到 update_every_n 筆後自動觸發更新
    """

    def __init__(
        self,
        model: Any,                         # TinyLLMv2 實例
        memory: EpisodicMemory,
        device: str = "cpu",
        lr: float = 3e-4,
        batch_size: int = 32,
        update_every_n: int = 100,          # 每 N 筆完整記錄更新一次
        gradient_accumulation: int = 4,
        max_grad_norm: float = 1.0,
        checkpoint_dir: str | Path = "data/bioneuronai/checkpoints/lora",
        max_lora_checkpoints: int = 10,
    ) -> None:
        self.model = model
        self.memory = memory
        self.device = device
        self.batch_size = batch_size
        self.update_every_n = update_every_n
        self.gradient_accumulation = gradient_accumulation
        self.max_grad_norm = max_grad_norm
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_lora_checkpoints = max_lora_checkpoints

        # 凍結骨幹，只訓練 LoRA
        self.model.freeze_backbone()
        lora_params = self.model.lora_parameters()
        self.optimizer = optim.AdamW(lora_params, lr=lr, weight_decay=0.01)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=1000, eta_min=lr * 0.1
        )

        self._pending_count = 0
        self._update_count = 0
        self._total_loss_history: List[float] = []

        logger.info(
            "OnlineLearner ready | lora_params=%d | update_every=%d | device=%s",
            sum(p.numel() for p in lora_params),
            update_every_n,
            device,
        )

    def record_outcome(self, experience: ExperienceRecord) -> Optional[Dict[str, float]]:
        """交易出場後呼叫，累計達到閾值則觸發更新。"""
        if experience.outcome == "PENDING":
            return None
        self.memory.push(experience)
        self._pending_count += 1
        if self._pending_count >= self.update_every_n:
            self._pending_count = 0
            return self._run_update()
        return None

    def _run_update(self) -> Dict[str, float]:
        """從熱緩衝採樣並執行一輪 LoRA 更新。"""
        samples = self.memory.sample_hot(self.batch_size * self.gradient_accumulation)
        if len(samples) < self.batch_size:
            logger.warning("OnlineLearner: 樣本不足 %d，跳過更新", self.batch_size)
            return {}

        self.model.train()
        self.optimizer.zero_grad()

        total_loss = 0.0
        direction_loss_sum = 0.0
        confidence_loss_sum = 0.0
        uncertainty_loss_sum = 0.0

        # 分批梯度累積
        for step in range(self.gradient_accumulation):
            batch = samples[step * self.batch_size: (step + 1) * self.batch_size]
            if not batch:
                break
            losses = self._compute_batch_loss(batch)
            loss = losses["total"] / self.gradient_accumulation
            loss.backward()
            total_loss += float(loss.item())
            direction_loss_sum += float(losses["direction"].item())
            confidence_loss_sum += float(losses["confidence"].item())
            uncertainty_loss_sum += float(losses["uncertainty"].item())

        nn.utils.clip_grad_norm_(self.model.lora_parameters(), self.max_grad_norm)
        self.optimizer.step()
        self.scheduler.step()
        self.model.eval()

        self._update_count += 1
        self._total_loss_history.append(total_loss)

        metrics = {
            "update_step": self._update_count,
            "loss": round(total_loss, 5),
            "direction_loss": round(direction_loss_sum, 5),
            "confidence_loss": round(confidence_loss_sum, 5),
            "uncertainty_loss": round(uncertainty_loss_sum, 5),
            "lr": self.optimizer.param_groups[0]["lr"],
        }
        logger.info("LoRA update #%d | loss=%.5f | samples=%d", self._update_count, total_loss, len(samples))

        if self._update_count % 10 == 0:
            self._save_lora_checkpoint()

        return metrics

    def _compute_batch_loss(self, batch: List[ExperienceRecord]) -> Dict[str, torch.Tensor]:
        """從一批 ExperienceRecord 建構訓練信號，計算損失。"""
        device = self.device

        # 數值 patch 輸入
        patches_list = [r.numeric_patches for r in batch if r.numeric_patches]
        if not patches_list:
            zero = torch.zeros(1, dtype=torch.float32, device=device)
            return {"total": zero, "direction": zero, "confidence": zero, "uncertainty": zero}

        patches = torch.tensor(patches_list, dtype=torch.float32, device=device)  # (B, 16, 64)

        # 前向推論
        raw_signal, decoded = self.model.forward_signal(patches)

        # ── 1. 方向分類損失（監督信號：WIN → 正確方向 / LOSS → 反向）
        direction_targets = []
        for r in batch:
            if r.outcome == "WIN":
                # 模型方向正確，強化
                target = 0 if r.decoded_direction == "LONG" else (2 if r.decoded_direction == "SHORT" else 1)
            elif r.outcome == "LOSS":
                # 模型方向錯誤，懲罰（用反向作為 target）
                target = 2 if r.decoded_direction == "LONG" else (0 if r.decoded_direction == "SHORT" else 1)
            else:
                target = 1  # BREAKEVEN → NEUTRAL
            direction_targets.append(target)

        dir_target_t = torch.tensor(direction_targets, dtype=torch.long, device=device)
        dir_logits = raw_signal[:, :3]
        direction_loss = nn.CrossEntropyLoss()(dir_logits, dir_target_t)

        # ── 2. 信心校準損失（高信心應對應高勝率）
        confidence_raw = decoded["confidence_probs"]
        weighted_conf = (confidence_raw * torch.tensor([0.3, 0.6, 0.9], device=device)).sum(dim=-1)
        actual_win = torch.tensor(
            [1.0 if r.outcome == "WIN" else 0.0 for r in batch],
            dtype=torch.float32, device=device
        )
        confidence_loss = nn.BCELoss()(weighted_conf.clamp(0.001, 0.999), actual_win)

        # ── 3. 不確定性損失（虧損案例應有高不確定性，盈利案例應有低不確定性）
        uncertainty_pred = decoded["uncertainty"]
        uncertainty_target = torch.tensor(
            [1.0 if r.outcome == "LOSS" else 0.0 for r in batch],
            dtype=torch.float32, device=device
        )
        uncertainty_loss = nn.BCELoss()(uncertainty_pred.clamp(0.001, 0.999), uncertainty_target)

        # ── 4. MoE 負載均衡損失
        moe_balance_loss = self.model.load_balance_loss().to(device)

        total = direction_loss + 0.5 * confidence_loss + 0.3 * uncertainty_loss + 0.1 * moe_balance_loss
        return {
            "total": total,
            "direction": direction_loss,
            "confidence": confidence_loss,
            "uncertainty": uncertainty_loss,
            "moe_balance": moe_balance_loss,
        }

    def _save_lora_checkpoint(self) -> None:
        """儲存 LoRA 權重快照（只存 LoRA A/B，不含骨幹）。"""
        ts = int(time.time())
        path = self.checkpoint_dir / f"lora_step_{self._update_count:06d}_{ts}.pt"
        lora_state = {
            k: v for k, v in self.model.state_dict().items()
            if "lora_A" in k or "lora_B" in k
        }
        torch.save({
            "step": self._update_count,
            "timestamp": ts,
            "lora_state": lora_state,
            "loss_history": self._total_loss_history[-100:],
        }, path)

        # 超過上限時刪最舊的
        checkpoints = sorted(self.checkpoint_dir.glob("lora_step_*.pt"))
        while len(checkpoints) > self.max_lora_checkpoints:
            checkpoints[0].unlink()
            checkpoints.pop(0)

        logger.info("LoRA checkpoint saved: %s", path.name)

    def load_latest_lora(self) -> bool:
        """啟動時載入最新 LoRA checkpoint。"""
        checkpoints = sorted(self.checkpoint_dir.glob("lora_step_*.pt"))
        if not checkpoints:
            return False
        latest = checkpoints[-1]
        ckpt = torch.load(latest, map_location=self.device)
        missing, unexpected = self.model.load_state_dict(ckpt["lora_state"], strict=False)
        self._update_count = ckpt.get("step", 0)
        logger.info(
            "Loaded LoRA from %s | step=%d | missing=%d | unexpected=%d",
            latest.name, self._update_count, len(missing), len(unexpected)
        )
        return True

    def get_stats(self) -> Dict[str, Any]:
        recent = self._total_loss_history[-20:]
        return {
            "update_count": self._update_count,
            "pending_count": self._pending_count,
            "update_every_n": self.update_every_n,
            "recent_avg_loss": round(float(np.mean(recent)) if recent else 0, 5),
            "loss_trend": "improving" if len(recent) > 5 and recent[-1] < recent[0] else "stable",
        }
