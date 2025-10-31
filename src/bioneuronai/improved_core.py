"""
BioNeuronAI 核心改進版本
包含更好的學習算法和新功能
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np

from .neurons.base import (
    AdaptiveThresholdStrategy,
    BaseNeuron,
    ThresholdStrategy,
    WeightDecayHebbianStrategy,
)


class ImprovedBioNeuron(BaseNeuron):
    """改進版本的生物啟發神經元。

    特色：
    - 支援可注入的學習與閾值調整策略
    - 內建自適應閾值與權重衰減 Hebbian 規則
    - 強化的新穎性評分與統計資訊
    """

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        weight_decay: float = 0.001,
        adaptive_threshold: bool = False,
        seed: int | None = None,
        *,
        learning_strategy: Optional[WeightDecayHebbianStrategy] = None,
        threshold_strategy: Optional[ThresholdStrategy] = None,
    ) -> None:
        self.weight_decay = float(weight_decay)
        self.adaptive_threshold = adaptive_threshold

        if learning_strategy is None:
            learning_strategy = WeightDecayHebbianStrategy(
                learning_rate=learning_rate,
                weight_decay=self.weight_decay,
            )
        if threshold_strategy is None:
            threshold_strategy = (
                AdaptiveThresholdStrategy() if adaptive_threshold else None
            )

        super().__init__(
            num_inputs=num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
            learning_strategy=learning_strategy,
            threshold_strategy=threshold_strategy,
        )

        self.threshold_history: List[float] = []
        self.activation_count = 0
        self.total_inputs = 0

    # ------------------------------------------------------------------
    # Forward path customisation
    # ------------------------------------------------------------------
    def forward(self, inputs: Sequence[float] | np.ndarray) -> float:
        return super().forward(inputs)

    def activation(self, potentials: np.ndarray) -> np.ndarray:
        threshold = float(self.threshold)
        above = potentials >= threshold
        sub_threshold = np.clip(
            potentials / max(threshold, 1e-6) * 0.1,
            0.0,
            0.1,
        )
        outputs = np.where(above, np.minimum(1.0, potentials), sub_threshold)
        return outputs.astype(np.float32)

    def _post_forward(
        self, inputs: np.ndarray, potentials: np.ndarray, outputs: np.ndarray
    ) -> None:
        _ = inputs, potentials  # Unused but kept for extensibility
        self.activation_count += int(np.sum(outputs >= self.threshold))
        self.total_inputs += outputs.size

    # ------------------------------------------------------------------
    # Learning helpers
    # ------------------------------------------------------------------
    def improved_hebbian_learn(
        self, inputs: Sequence[float], target: Optional[float] = None
    ) -> None:
        if target is None:
            self.learn(inputs)
        else:
            self.learn(inputs, target=float(target))

    # ------------------------------------------------------------------
    # Novelty estimations
    # ------------------------------------------------------------------
    def enhanced_novelty_score(self) -> float:
        if len(self.input_memory) < 2:
            return 0.0

        input_novelty = self._calculate_input_novelty()
        output_novelty = self._calculate_output_novelty()
        total_novelty = 0.7 * input_novelty + 0.3 * output_novelty
        return float(np.clip(total_novelty, 0.0, 1.0))

    def _calculate_input_novelty(self) -> float:
        if len(self.input_memory) < 2:
            return 0.0

        current = self.input_memory[-1]
        previous = self.input_memory[-2]
        dot_product = float(np.dot(current, previous))
        norms = float(np.linalg.norm(current) * np.linalg.norm(previous))

        if norms < 1e-8:
            return 0.0

        similarity = dot_product / norms
        novelty = 1.0 - similarity
        return float(max(0.0, novelty))

    def _calculate_output_novelty(self) -> float:
        if len(self.output_memory) < 2:
            return 0.0

        window = list(self.output_memory)[-min(3, len(self.output_memory)) :]
        variance = float(np.var(window))
        return float(min(1.0, variance * 4.0))

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def get_statistics(self) -> dict:
        activation_rate = self.activation_count / max(1, self.total_inputs)
        return {
            "activation_rate": activation_rate,
            "current_threshold": self.threshold,
            "weight_mean": float(np.mean(self.weights)),
            "weight_std": float(np.std(self.weights)),
            "total_inputs": self.total_inputs,
            "memory_usage": len(self.input_memory),
        }

    def reset_statistics(self) -> None:
        self.activation_count = 0
        self.total_inputs = 0
        self.threshold_history.clear()
        super().reset()


class CuriositDrivenNet:
    """好奇心驅動的神經網路，使用新穎性評分調節學習強度。"""

    def __init__(self, input_dim: int = 2, hidden_dim: int = 3):
        self.neurons = [
            ImprovedBioNeuron(
                num_inputs=input_dim,
                adaptive_threshold=True,
                seed=42 + i,
            )
            for i in range(hidden_dim)
        ]
        self.curiosity_threshold = 0.5

    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[float]]:
        outputs = []
        novelties = []
        for neuron in self.neurons:
            outputs.append(neuron.forward(inputs))
            novelties.append(neuron.enhanced_novelty_score())
        return outputs, novelties

    def curious_learn(self, inputs: Sequence[float]) -> float:
        outputs, novelties = self.forward(inputs)
        _ = outputs  # unused directly but keeps API symmetrical
        avg_curiosity = float(np.mean(novelties))

        if avg_curiosity > self.curiosity_threshold:
            for neuron, novelty in zip(self.neurons, novelties):
                enhanced_lr = neuron.learning_rate * (1 + novelty)
                original_lr = neuron.learning_rate
                neuron.learning_rate = enhanced_lr
                neuron.learn(inputs)
                neuron.learning_rate = original_lr

        return avg_curiosity

    def get_network_stats(self) -> dict:
        stats = [neuron.get_statistics() for neuron in self.neurons]
        return {
            "avg_activation_rate": float(
                np.mean([s["activation_rate"] for s in stats])
            ),
            "avg_threshold": float(
                np.mean([s["current_threshold"] for s in stats])
            ),
            "neuron_count": len(self.neurons),
            "individual_stats": stats,
        }


# 向後兼容的別名
BioNeuronV2 = ImprovedBioNeuron

