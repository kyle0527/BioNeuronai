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
from typing import List, Sequence, Tuple, Optional, Dict
import numpy as np

from .neuron_base import LearningConfig, NeuronBase


class ImprovedBioNeuron(NeuronBase):
    """改進版本的生物啟發神經元
    
    新增功能:
    - 改進的Hebbian學習規則
    - 自適應閾值
    - 更好的新穎性檢測
    - 權重衰減機制
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

        super().__init__(
            num_inputs=num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
            config=LearningConfig(
                weight_decay=weight_decay,
                adaptive_threshold=adaptive_threshold,
            ),
        )
        self.initial_threshold = float(threshold)
        self.threshold_history: list[float] = []
        )
        self.initial_threshold = float(threshold)
        self.threshold = float(threshold)
        self.weight_decay = float(weight_decay)
        self.adaptive_threshold = adaptive_threshold

        # 擴展的記憶系統
        self.output_memory: List[float] = []
        self.threshold_history: List[float] = []
        self.activation_count = 0
        self.total_inputs = 0
        self._last_output: float | None = None

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
    def forward(self, inputs: Sequence[float]) -> float:
        """改進的前向傳播"""
        assert len(inputs) == self.num_inputs
        x = np.asarray(inputs, dtype=np.float32)
        potential = float(np.dot(self.weights, x))
        return self._finalize_potential(x, potential)

        # 更新記憶
        self._remember_input(x)

        # 計算潛能與輸出
        potential = self._compute_potential(x)
        output, activated = self._activation_response(potential)

        # 更新輸出記憶
        self.output_memory.append(output)
        if len(self.output_memory) > self.memory_len:
            self.output_memory.pop(0)
        
        self._record_activation(activated)
        
        # 自適應閾值調整
    def _finalize_potential(self, x: np.ndarray, potential: float) -> float:
        """Finalize activation given a precomputed potential."""

        self.input_memory.append(x.copy())
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

        if potential >= self.threshold:
            self.activation_count += 1
        else:
            output = max(0.0, potential / self.threshold * 0.1)

        self.output_memory.append(output)
        if len(self.output_memory) > self.memory_len:
            self.output_memory.pop(0)

        self.total_inputs += 1

        if self.adaptive_threshold and len(self.output_memory) >= self.memory_len:
            self._adapt_threshold()

        return output

    def _adapt_threshold(self) -> None:
        """自適應閾值調整"""
        recent_avg = np.mean(self.output_memory)
        target_activation = 0.3  # 目標激活率

        if recent_avg > target_activation + 0.1:
            self.threshold = min(2.0, self.threshold * 1.05)
        elif recent_avg < target_activation - 0.1:
            self.threshold = max(0.1, self.threshold * 0.95)
        
        self.threshold_history.append(self.threshold)

    def hebbian_learn(
        self,
        inputs: Sequence[float],
        output: float | None = None,
        *,
        target: Optional[float] = None,
    ) -> None:
    def improved_hebbian_learn(
        self,
        inputs: Sequence[float],
        target: Optional[float] = None,

        """改進的Hebbian學習規則

        特點:
        - 支持有監督和無監督學習
        - 加入權重衰減
        - 考慮輸出誤差
        """
        x = np.asarray(inputs, dtype=np.float32)
        if output is not None:
            current_output = float(output)
        else:
            potential = self._compute_potential(x)
            current_output, _ = self._activation_response(potential)

        if target is not None:
            # 有監督學習：基於誤差的學習
            error = target - current_output
            delta = self.learning_rate * error * vector * (target + 0.1)
        else:
            # 無監督Hebbian學習
            delta = self.learning_rate * x * current_output

        # 應用權重更新和衰減
        self.weights = self.weights + delta - self.weight_decay * self.weights

        # 保持權重在合理範圍內
        self._clip_weights(min_value=0.0, max_value=2.0)

    def _compute_potential(self, x: np.ndarray) -> float:
        """計算輸入向量的加權潛能。"""

        return float(np.dot(self.weights, x))

    def _activation_response(self, potential: float) -> Tuple[float, bool]:
        """根據當前潛能取得輸出值與是否達到閾值。"""

        if potential >= self.threshold:
            return min(1.0, potential), True
        # 次閾值響應
        return max(0.0, potential / self.threshold * 0.1), False

    def improved_hebbian_learn(
        self, inputs: Sequence[float], target: Optional[float] = None
    ) -> None:
        """Backward compatible wrapper for the old method name."""

        self.hebbian_learn(inputs, target=target)

    # ------------------------------------------------------------------
    # Novelty estimations
    # ------------------------------------------------------------------
    def enhanced_novelty_score(self) -> float:
        """增強的新穎性評分

        考慮:
        - 輸入變化率
        - 輸出變化率  
        - 權重變化
        """
        if len(self.input_memory) < 2:
            return 0.0

        input_novelty = self._calculate_input_novelty()
        output_novelty = self._calculate_output_novelty()
        total_novelty = 0.7 * input_novelty + 0.3 * output_novelty

        # 加權組合
        total_novelty = 0.7 * input_novelty + 0.3 * output_novelty

        return float(np.clip(total_novelty, 0.0, 1.0))

    def novelty_score(self) -> float:
        """與基底類介面一致的增強新穎性分數。"""

        return self.enhanced_novelty_score()

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

    def learn(self, inputs: Sequence[float], target: float | None = None) -> float:
        """Unified entrypoint that satisfies :class:`~bioneuronai.neuron_base.BaseNeuron`."""

        if target is None:
            output = self.improved_hebbian_learn(inputs)
            return output

        cached_output = self._last_output
        if cached_output is None:
            cached_output = self.forward(inputs)

        self.improved_hebbian_learn(
            inputs,
            target=float(target),
            current_output=cached_output,
        )
        return float(target)





    def __init__(
        self,
        input_dim: int = 2,
        hidden_dim: int = 3,
        curiosity_transform: Optional[Callable[[Sequence[float]], float]] = None,
    ) -> None:
        self.neurons = [
            ImprovedBioNeuron(
                num_inputs=input_dim,
                adaptive_threshold=True,
                seed=42 + i,
            )
            for i in range(hidden_dim)
        ]

        self.curiosity_threshold = 0.5
        self.use_vectorized = use_vectorized
        self._weight_matrix = np.stack([n.weights for n in self.neurons]).astype(np.float32)
        self._bind_weight_matrix()

    def _bind_weight_matrix(self) -> None:
        for idx, neuron in enumerate(self.neurons):
            neuron.weights = self._weight_matrix[idx]

    def _get_learning_rates(self) -> np.ndarray:
        return np.asarray([n.learning_rate for n in self.neurons], dtype=np.float32)

    def _get_weight_decays(self) -> np.ndarray:
        return np.asarray([n.weight_decay for n in self.neurons], dtype=np.float32)

    def forward(
        self,
        inputs: Sequence[float] | Sequence[Sequence[float]],
        *,
        use_vectorized: bool | None = None,
    ) -> Tuple[List[float] | List[List[float]], List[float] | List[List[float]]]:
        vectorized = self.use_vectorized if use_vectorized is None else use_vectorized
        inputs_arr = np.asarray(inputs, dtype=np.float32)

        if inputs_arr.ndim == 1:
            return self._forward_single(inputs_arr, vectorized)
        if inputs_arr.ndim == 2:
            outputs_batch: List[List[float]] = []
            novelties_batch: List[List[float]] = []
            for sample in inputs_arr:
                out, nov = self._forward_single(sample, vectorized)
                outputs_batch.append(out)
                novelties_batch.append(nov)
            return outputs_batch, novelties_batch

        raise ValueError("輸入必須為一維或二維向量")

    def _forward_single(
        self, x: np.ndarray, vectorized: bool
    ) -> Tuple[List[float], List[float]]:
        if not vectorized:
            outputs: List[float] = []
            novelties: List[float] = []
            for neuron in self.neurons:
                outputs.append(neuron.forward(x))
                novelties.append(neuron.enhanced_novelty_score())
            return outputs, novelties

        potentials = self._weight_matrix @ x
        outputs: List[float] = []
        novelties: List[float] = []
        for idx, neuron in enumerate(self.neurons):
            outputs.append(neuron._finalize_potential(x, float(potentials[idx])))
            novelties.append(neuron.enhanced_novelty_score())
        return outputs, novelties

    def curious_learn(
        self,
        inputs: Sequence[float] | Sequence[Sequence[float]],
        *,
        use_vectorized: bool | None = None,
    ) -> float:
        vectorized = self.use_vectorized if use_vectorized is None else use_vectorized
        inputs_arr = np.asarray(inputs, dtype=np.float32)
        outputs, novelties = self.forward(inputs_arr, use_vectorized=vectorized)

        outputs_arr = np.asarray(outputs, dtype=np.float32)
        novelties_arr = np.asarray(novelties, dtype=np.float32)

        if inputs_arr.ndim == 1:
            inputs_arr = inputs_arr.reshape(1, -1)
        if outputs_arr.ndim == 1:
            outputs_arr = outputs_arr.reshape(1, -1)
        if novelties_arr.ndim == 1:
            novelties_arr = novelties_arr.reshape(1, -1)

        if outputs_arr.shape != novelties_arr.shape:
            raise ValueError("輸出與新穎性張量形狀不一致")

        avg_curiosity = float(np.mean(novelties_arr))

        if avg_curiosity <= self.curiosity_threshold:
            return avg_curiosity

        if not vectorized:
            for sample_inputs, sample_outputs, sample_novelties in zip(
                inputs_arr, outputs_arr, novelties_arr
            ):
                for neuron, novelty, output in zip(
                    self.neurons, sample_novelties, sample_outputs
                ):
                    base_lr = neuron.learning_rate
                    neuron.learning_rate = base_lr * (1.0 + float(novelty))
                    neuron.improved_hebbian_learn(
                        sample_inputs, output_override=float(output)
                    )
                    neuron.learning_rate = base_lr
            return avg_curiosity

        base_lr = self._get_learning_rates()
        weight_decay = self._get_weight_decays()

        for sample_inputs, sample_outputs, sample_novelties in zip(
            inputs_arr, outputs_arr, novelties_arr
        ):
            effective_lr = base_lr * (1.0 + sample_novelties)
            self._weight_matrix *= (1.0 - weight_decay)[:, None]
            delta = (effective_lr * sample_outputs)[:, None] * sample_inputs[None, :]
            np.add(self._weight_matrix, delta, out=self._weight_matrix, casting="unsafe")
            np.clip(self._weight_matrix, 0.0, 2.0, out=self._weight_matrix)

        return avg_curiosity


        self.curiosity_threshold = float(curiosity_threshold)
        self.reward_scale = float(reward_scale)
        self.reward_clip = reward_clip

    def configure_curiosity(
        self,
        *,
        threshold: Optional[float] = None,
        reward_scale: Optional[float] = None,
        reward_clip: Optional[Tuple[float, float]] = None,
    ) -> None:
        """更新好奇心閾值或獎勵縮放等參數"""

        if threshold is not None:
            self.curiosity_threshold = float(threshold)
        if reward_scale is not None:
            self.reward_scale = float(reward_scale)
        if reward_clip is not None:
            self.reward_clip = reward_clip

    def forward(
        self, inputs: Sequence[float]
    ) -> Tuple[List[float], List[float], float, float]:
        """前向傳播，回傳輸出、新穎性、好奇心水平與獎勵"""

        outputs: List[float] = []
        novelties: List[float] = []

        for neuron in self.neurons:
            output = neuron.forward(inputs)
            novelty = neuron.novelty_score()
            outputs.append(output)
            novelties.append(novelty)

        
        return outputs, novelties

    def curious_learn(self, inputs: Sequence[float]) -> float:
        """基於好奇心的學習

        Returns:
            平均好奇心水平
        """
        _, novelties = self.forward(inputs)
        curiosity_level = float(self._curiosity_transform(novelties))

        # 只有當新穎性足夠高時才學習
        if curiosity_level > self.curiosity_threshold:
            for neuron, novelty in zip(self.neurons, novelties):
                enhanced_lr = neuron.learning_rate * (1 + novelty)
                original_lr = neuron.learning_rate
                neuron.learning_rate = enhanced_lr
                neuron.learn(inputs)
                neuron.learn(inputs, target=output)
                neuron.learning_rate = original_lr

        return avg_curiosity


        curiosity_level = float(np.mean(novelties)) if novelties else 0.0
        curiosity_reward = self._calculate_curiosity_reward(curiosity_level)

        return outputs, novelties, curiosity_level, curiosity_reward

    def step(self, inputs: Sequence[float], learn: bool = True) -> Dict[str, object]:
        """計算好奇心響應，可選擇是否進行學習"""

        outputs, novelties, curiosity_level, curiosity_reward = self.forward(inputs)

        if learn:
            self._apply_curiosity_learning(inputs, novelties, curiosity_level)

        return {
            "outputs": outputs,
            "novelties": novelties,
            "curiosity_level": curiosity_level,
            "curiosity_reward": curiosity_reward,
        }

    def curious_learn(self, inputs: Sequence[float]) -> Tuple[float, float]:
        """觸發好奇心學習，並回傳好奇心水平與獎勵"""

        stats = self.step(inputs, learn=True)
        return stats["curiosity_level"], stats["curiosity_reward"]

    def _apply_curiosity_learning(
        self,
        inputs: Sequence[float],
        novelties: Sequence[float],
        curiosity_level: float,
    ) -> None:
        """根據平均好奇心調節學習強度"""

        if curiosity_level < self.curiosity_threshold:
            return

        for neuron, novelty in zip(self.neurons, novelties):
            enhanced_lr = neuron.learning_rate * (1 + novelty)
            original_lr = neuron.learning_rate
            neuron.learning_rate = enhanced_lr
            neuron.improved_hebbian_learn(inputs)
            neuron.learning_rate = original_lr

    def _calculate_curiosity_reward(self, curiosity_level: float) -> float:
        """依據好奇心強度計算獎勵"""

        surplus = max(0.0, curiosity_level - self.curiosity_threshold)
        reward = surplus * self.reward_scale

        if self.reward_clip is not None:
            min_reward, max_reward = self.reward_clip
            reward = float(np.clip(reward, min_reward, max_reward))

        return float(reward)

    

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

        return {

            "avg_activation_rate": float(np.mean([s["activation_rate"] for s in stats])),
            "avg_threshold": float(np.mean([s["current_threshold"] for s in stats])),
            "neuron_count": len(self.neurons),
            "individual_stats": stats,
        }



# 向後兼容的別名
CuriositDrivenNet = CuriosityDrivenNet
BioNeuronV2 = ImprovedBioNeuron

            'avg_activation_rate': np.mean([s['activation_rate'] for s in stats]),
            'avg_threshold': np.mean([s['current_threshold'] for s in stats]),
            'neuron_count': len(self.neurons),
            'individual_stats': stats,
            'curiosity_threshold': self.curiosity_threshold,
            'reward_scale': self.reward_scale
        }


def __getattr__(name: str):  # pragma: no cover - simple compatibility shim
    if name in {"CuriosityDrivenNet", "CuriositDrivenNet"}:
        from .curiosity import CuriosityDrivenNet



