"""
BioNeuronAI 核心改進版本
包含更好的學習算法和新功能
"""

from __future__ import annotations
from typing import List, Sequence, Tuple, Optional
import numpy as np


class ImprovedBioNeuron:
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
    ) -> None:
        self.num_inputs = num_inputs
        rng = np.random.default_rng(seed)
        self.weights = rng.uniform(0.1, 0.9, num_inputs).astype(np.float32)
        self.initial_threshold = float(threshold)
        self.threshold = float(threshold)
        self.learning_rate = float(learning_rate)
        self.memory_len = int(memory_len)
        self.weight_decay = float(weight_decay)
        self.adaptive_threshold = adaptive_threshold
        
        # 擴展的記憶系統
        self.input_memory: List[np.ndarray] = []
        self.output_memory: List[float] = []
        self.threshold_history: List[float] = []
        
        # 統計信息
        self.activation_count = 0
        self.total_inputs = 0

    def forward(self, inputs: Sequence[float]) -> float:
        """改進的前向傳播"""
        assert len(inputs) == self.num_inputs
        x = np.asarray(inputs, dtype=np.float32)
        potential = float(np.dot(self.weights, x))
        return self._finalize_potential(x, potential)

    def _finalize_potential(self, x: np.ndarray, potential: float) -> float:
        """Finalize activation given a precomputed potential."""

        self.input_memory.append(x.copy())
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

        if potential >= self.threshold:
            output = min(1.0, potential)
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

    def improved_hebbian_learn(
        self,
        inputs: Sequence[float],
        target: Optional[float] = None,
        output_override: float | None = None,
    ) -> None:
        """改進的Hebbian學習規則

        特點:
        - 支持有監督和無監督學習
        - 加入權重衰減
        - 考慮輸出誤差
        """
        x = np.asarray(inputs, dtype=np.float32)
        if output_override is not None:
            current_output = float(output_override)
        else:
            current_output = self.forward(inputs)

        if target is not None:
            # 有監督學習：基於誤差的學習
            error = target - current_output
            # 使用誤差調節的Hebbian規則
            delta = self.learning_rate * error * x * (target + 0.1)  # 避免零更新
        else:
            # 無監督Hebbian學習
            delta = self.learning_rate * x * current_output

        if self.weight_decay > 0:
            self.weights *= (1.0 - self.weight_decay)

        np.add(self.weights, delta, out=self.weights, casting="unsafe")
        np.clip(self.weights, 0.0, 2.0, out=self.weights)

    def enhanced_novelty_score(self) -> float:
        """增強的新穎性評分
        
        考慮:
        - 輸入變化率
        - 輸出變化率  
        - 權重變化
        """
        if len(self.input_memory) < 2:
            return 0.0
        
        # 輸入新穎性
        input_novelty = self._calculate_input_novelty()
        
        # 輸出新穎性
        output_novelty = self._calculate_output_novelty()
        
        # 加權組合
        total_novelty = 0.7 * input_novelty + 0.3 * output_novelty
        
        return float(np.clip(total_novelty, 0.0, 1.0))

    def _calculate_input_novelty(self) -> float:
        """計算輸入新穎性"""
        if len(self.input_memory) < 2:
            return 0.0
        
        current = self.input_memory[-1]
        previous = self.input_memory[-2]
        
        # 使用餘弦相似度來測量差異
        dot_product = np.dot(current, previous)
        norms = np.linalg.norm(current) * np.linalg.norm(previous)
        
        if norms < 1e-8:
            return 0.0
        
        similarity = float(dot_product / norms)
        novelty = float(1.0 - similarity)
        
        return float(max(0.0, novelty))

    def _calculate_output_novelty(self) -> float:
        """計算輸出新穎性"""
        if len(self.output_memory) < 2:
            return 0.0
        
        recent_outputs = self.output_memory[-min(3, len(self.output_memory)):]
        variance = np.var(recent_outputs)
        
        # 將方差映射到 0-1 範圍
        return min(1.0, variance * 4.0)

    def get_statistics(self) -> dict:
        """獲取神經元統計信息"""
        activation_rate = self.activation_count / max(1, self.total_inputs)
        
        return {
            'activation_rate': activation_rate,
            'current_threshold': self.threshold,
            'weight_mean': float(np.mean(self.weights)),
            'weight_std': float(np.std(self.weights)),
            'total_inputs': self.total_inputs,
            'memory_usage': len(self.input_memory)
        }

    def reset_statistics(self) -> None:
        """重置統計信息"""
        self.activation_count = 0
        self.total_inputs = 0
        self.threshold = self.initial_threshold
        self.input_memory.clear()
        self.output_memory.clear()
        self.threshold_history.clear()



class CuriosityDrivenNet:
    """好奇心驅動的神經網路，支援向量化推理與批次學習。"""

    def __init__(
        self,
        input_dim: int = 2,
        hidden_dim: int = 3,
        *,
        use_vectorized: bool = True,
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

    def get_network_stats(self) -> dict:
        """獲取網路統計信息"""
        stats = [neuron.get_statistics() for neuron in self.neurons]

        return {
            "avg_activation_rate": float(np.mean([s["activation_rate"] for s in stats])),
            "avg_threshold": float(np.mean([s["current_threshold"] for s in stats])),
            "neuron_count": len(self.neurons),
            "individual_stats": stats,
        }



# 向後兼容的別名
CuriositDrivenNet = CuriosityDrivenNet
BioNeuronV2 = ImprovedBioNeuron
