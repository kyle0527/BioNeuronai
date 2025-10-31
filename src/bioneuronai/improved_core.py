"""
BioNeuronAI 核心改進版本
包含更好的學習算法和新功能
"""

from __future__ import annotations
from typing import List, Sequence, Tuple, Optional
import numpy as np

from .neuron_base import BaseBioNeuron


class ImprovedBioNeuron(BaseBioNeuron):
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
        super().__init__(
            num_inputs=num_inputs,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
        )
        self.initial_threshold = float(threshold)
        self.threshold = float(threshold)
        self.weight_decay = float(weight_decay)
        self.adaptive_threshold = adaptive_threshold

        # 擴展的記憶系統
        self.output_memory: List[float] = []
        self.threshold_history: List[float] = []

    def forward(self, inputs: Sequence[float]) -> float:
        """改進的前向傳播"""
        assert len(inputs) == self.num_inputs
        x = np.asarray(inputs, dtype=np.float32)

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
            # 使用誤差調節的Hebbian規則
            delta = self.learning_rate * error * x * (target + 0.1)  # 避免零更新
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

    def novelty_score(self) -> float:
        """與基底類介面一致的增強新穎性分數。"""

        return self.enhanced_novelty_score()

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


class CuriositDrivenNet:
    """好奇心驅動的神經網路
    
    使用新穎性評分來調節學習強度
    """
    
    def __init__(self, input_dim: int = 2, hidden_dim: int = 3):
        self.neurons = [
            ImprovedBioNeuron(
                num_inputs=input_dim, 
                adaptive_threshold=True,
                seed=42 + i
            ) for i in range(hidden_dim)
        ]
        self.curiosity_threshold = 0.5
    
    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[float]]:
        """前向傳播並返回輸出和新穎性評分"""
        outputs = []
        novelties = []
        
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
        outputs, novelties = self.forward(inputs)
        avg_curiosity = np.mean(novelties)

        # 只有當新穎性足夠高時才學習
        if avg_curiosity > self.curiosity_threshold:
            for neuron, novelty, output in zip(self.neurons, novelties, outputs):
                # 新穎性高的神經元學習更強
                enhanced_lr = neuron.learning_rate * (1 + novelty)
                original_lr = neuron.learning_rate
                neuron.learning_rate = enhanced_lr
                neuron.hebbian_learn(inputs, output=output)
                neuron.learning_rate = original_lr
        
        return avg_curiosity
    
    def get_network_stats(self) -> dict:
        """獲取網路統計信息"""
        stats = [neuron.get_statistics() for neuron in self.neurons]
        
        return {
            'avg_activation_rate': np.mean([s['activation_rate'] for s in stats]),
            'avg_threshold': np.mean([s['current_threshold'] for s in stats]),
            'neuron_count': len(self.neurons),
            'individual_stats': stats
        }


# 向後兼容的別名
BioNeuronV2 = ImprovedBioNeuron
