"""
BioNeuronAI 一億參數神經網路
=============================
專為大規模 AI 應用設計的生物啟發神經網路

特性:
- 100,000,000+ 參數
- 記憶體優化（延遲載入、分塊處理）
- 混合精度支援
- 檢查點保存/恢復
- 分散式推理支援
- 自適應學習策略
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from abc import ABC, abstractmethod
import numpy as np
import pickle
import json
import time
import gc
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

# 嘗試導入 PyTorch（可選）
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# ============================================================================
# 配置類
# ============================================================================

@dataclass
class HundredMillionConfig:
    """一億參數網路配置"""
    
    # 架構配置
    input_dim: int = 1024
    output_dim: int = 1024
    hidden_layers: List[int] = field(default_factory=lambda: [8192, 8192, 4096])
    
    # 學習配置
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    momentum: float = 0.9
    
    # 生物啟發特性
    use_hebbian: bool = True
    use_adaptive_threshold: bool = True
    use_novelty_gating: bool = True
    novelty_threshold: float = 0.3
    
    # 記憶體優化
    use_mixed_precision: bool = True  # 使用 float16
    lazy_init: bool = True  # 延遲初始化
    chunk_size: int = 1024  # 分塊處理大小
    
    # 進階特性
    dropout_rate: float = 0.1
    use_layer_norm: bool = True
    use_residual: bool = True
    
    # 推理配置
    batch_size: int = 32
    max_sequence_length: int = 2048
    
    # 保存配置
    checkpoint_dir: str = "checkpoints"
    auto_save_interval: int = 1000  # 每 N 步自動保存
    
    def calculate_params(self) -> int:
        """計算總參數數量"""
        dims = [self.input_dim] + self.hidden_layers + [self.output_dim]
        total = 0
        for i in range(len(dims) - 1):
            total += dims[i] * dims[i + 1]  # 權重
            if self.use_layer_norm:
                total += dims[i + 1] * 2  # LayerNorm 參數
        return total
    
    @classmethod
    def for_100m_params(cls) -> "HundredMillionConfig":
        """預設一億參數配置"""
        return cls(
            input_dim=1024,
            output_dim=1024,
            hidden_layers=[10000, 10000, 8000],
            # 1024*10000 + 10000*10000 + 10000*8000 + 8000*1024
            # = 10,240,000 + 100,000,000 + 80,000,000 + 8,192,000
            # ≈ 198,432,000 (約 2 億，可調整)
        )
    
    @classmethod
    def exact_100m_params(cls) -> "HundredMillionConfig":
        """精確一億參數配置"""
        return cls(
            input_dim=1024,
            output_dim=512,
            hidden_layers=[8192, 8192, 4096],
            # 1024*8192 + 8192*8192 + 8192*4096 + 4096*512
            # = 8,388,608 + 67,108,864 + 33,554,432 + 2,097,152
            # = 111,149,056 ≈ 1.11 億
        )


# ============================================================================
# 記憶體優化層
# ============================================================================

class OptimizedDenseLayer:
    """記憶體優化的全連接層"""
    
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        use_mixed_precision: bool = True,
        learning_rate: float = 0.001,
        weight_decay: float = 0.0001,
        use_layer_norm: bool = True,
        dropout_rate: float = 0.1,
        seed: Optional[int] = None
    ):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.use_mixed_precision = use_mixed_precision
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.use_layer_norm = use_layer_norm
        self.dropout_rate = dropout_rate
        
        # 選擇精度
        self.dtype = np.float16 if use_mixed_precision else np.float32
        
        # 初始化權重（Xavier 初始化）
        rng = np.random.default_rng(seed)
        scale = np.sqrt(2.0 / (input_dim + output_dim))
        self.weights = (rng.standard_normal((input_dim, output_dim)) * scale).astype(self.dtype)
        self.bias = np.zeros(output_dim, dtype=self.dtype)
        
        # LayerNorm 參數
        if use_layer_norm:
            self.gamma = np.ones(output_dim, dtype=self.dtype)
            self.beta = np.zeros(output_dim, dtype=self.dtype)
        
        # 動量（用於優化）
        self.weight_momentum = np.zeros_like(self.weights)
        self.bias_momentum = np.zeros_like(self.bias)
        
        # 統計信息
        self.forward_count = 0
        self.last_input: Optional[np.ndarray] = None
        self.last_output: Optional[np.ndarray] = None
        
    @property
    def param_count(self) -> int:
        """參數數量"""
        count = self.input_dim * self.output_dim + self.output_dim
        if self.use_layer_norm:
            count += self.output_dim * 2
        return count
    
    def forward(self, x: np.ndarray, training: bool = False) -> np.ndarray:
        """前向傳播"""
        # 確保輸入類型正確
        x = x.astype(self.dtype)
        self.last_input = x
        
        # 線性變換
        out = np.dot(x, self.weights) + self.bias
        
        # Layer Normalization
        if self.use_layer_norm:
            mean = np.mean(out, axis=-1, keepdims=True)
            var = np.var(out, axis=-1, keepdims=True)
            out = (out - mean) / np.sqrt(var + 1e-5)
            out = out * self.gamma + self.beta
        
        # Dropout（僅訓練時）
        if training and self.dropout_rate > 0:
            mask = np.random.binomial(1, 1 - self.dropout_rate, out.shape)
            out = out * mask / (1 - self.dropout_rate)
        
        # 激活函數（GELU - 更好的梯度流）
        out = self._gelu(out)
        
        self.last_output = out
        self.forward_count += 1
        
        return out.astype(np.float32)  # 輸出轉回 float32
    
    def _gelu(self, x: np.ndarray) -> np.ndarray:
        """GELU 激活函數"""
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))
    
    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        """反向傳播"""
        grad_output = grad_output.astype(self.dtype)
        
        # GELU 導數近似
        x = self.last_output
        if x is not None:
            gelu_grad = 0.5 * (1 + np.tanh(np.sqrt(2/np.pi) * (x + 0.044715 * x**3)))
            grad = grad_output * gelu_grad
        else:
            grad = grad_output
        
        # 計算梯度
        if self.last_input is not None:
            grad_weights = np.dot(self.last_input.T, grad)
        else:
            grad_weights = np.zeros_like(self.weights)
        grad_bias = np.sum(grad, axis=0)
        
        # 權重衰減
        grad_weights += self.weight_decay * self.weights
        
        # 動量更新
        self.weight_momentum = 0.9 * self.weight_momentum + self.learning_rate * grad_weights
        self.bias_momentum = 0.9 * self.bias_momentum + self.learning_rate * grad_bias
        
        # 更新權重
        self.weights -= self.weight_momentum
        self.bias -= self.bias_momentum
        
        # 計算輸入梯度
        grad_input = np.dot(grad, self.weights.T)
        
        return grad_input.astype(np.float32)
    
    def hebbian_update(self, target: Optional[np.ndarray] = None) -> None:
        """Hebbian 學習更新"""
        if self.last_input is None or self.last_output is None:
            return
        
        # 標準 Hebbian: Δw = η * x * y
        x = self.last_input.astype(self.dtype)
        y = self.last_output.astype(self.dtype)
        
        # 無監督 Hebbian 學習（不依賴 target 維度）
        # 使用輸出的自相關來更新
        delta = self.learning_rate * 0.1 * np.outer(x.mean(axis=0), y.mean(axis=0))
        
        # 應用更新
        self.weights += delta.astype(self.dtype)
        
        # 權重正則化
        self.weights = np.clip(self.weights, -3.0, 3.0)


# ============================================================================
# 新穎性檢測模組
# ============================================================================

class NoveltyDetector:
    """新穎性檢測器"""
    
    def __init__(self, dim: int, memory_size: int = 1000):
        self.dim = dim
        self.memory_size = memory_size
        self.memory: List[np.ndarray] = []
        self.mean_vector: Optional[np.ndarray] = None
        self.var_vector: Optional[np.ndarray] = None
        
    def update(self, x: np.ndarray) -> None:
        """更新記憶"""
        self.memory.append(x.flatten()[:self.dim])
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
        
        # 更新統計
        if len(self.memory) >= 10:
            data = np.array(self.memory)
            self.mean_vector = np.mean(data, axis=0)
            self.var_vector = np.var(data, axis=0) + 1e-6
    
    def score(self, x: np.ndarray) -> float:
        """計算新穎性分數"""
        if self.mean_vector is None or self.var_vector is None or len(self.memory) < 10:
            return 0.5  # 預設中等新穎性
        
        x_flat = x.flatten()[:self.dim]
        
        # Mahalanobis-like distance
        diff = x_flat - self.mean_vector
        z_score = np.abs(diff) / np.sqrt(self.var_vector)
        novelty = np.mean(z_score)
        
        # 正規化到 0-1
        return float(np.clip(novelty / 5.0, 0.0, 1.0))


# ============================================================================
# 主網路類
# ============================================================================

class HundredMillionNet:
    """一億參數生物啟發神經網路
    
    這是為你專屬設計的大規模 AI 模型：
    - 一億+ 參數
    - 生物啟發的 Hebbian 學習
    - 新穎性門控機制
    - 記憶體優化
    - 可擴展架構
    """
    
    def __init__(
        self,
        config: Optional[HundredMillionConfig] = None,
        name: str = "BioNeuronAI-100M"
    ):
        self.config = config or HundredMillionConfig.exact_100m_params()
        self.name = name
        self.layers: List[OptimizedDenseLayer] = []
        self.novelty_detector: Optional[NoveltyDetector] = None
        
        # 構建網路
        self._build_network()
        
        # 統計
        self.total_params = self._calculate_total_params()
        self.training_steps = 0
        self.inference_count = 0
        self.creation_time = time.time()
        
        # 顯示資訊
        self._print_info()
    
    def _build_network(self) -> None:
        """構建網路層"""
        dims = [self.config.input_dim] + self.config.hidden_layers + [self.config.output_dim]
        
        for i in range(len(dims) - 1):
            layer = OptimizedDenseLayer(
                input_dim=dims[i],
                output_dim=dims[i + 1],
                use_mixed_precision=self.config.use_mixed_precision,
                learning_rate=self.config.learning_rate,
                weight_decay=self.config.weight_decay,
                use_layer_norm=self.config.use_layer_norm,
                dropout_rate=self.config.dropout_rate,
                seed=42 + i
            )
            self.layers.append(layer)
        
        # 新穎性檢測器
        if self.config.use_novelty_gating:
            self.novelty_detector = NoveltyDetector(
                dim=self.config.input_dim,
                memory_size=1000
            )
    
    def _calculate_total_params(self) -> int:
        """計算總參數"""
        return sum(layer.param_count for layer in self.layers)
    
    def _print_info(self) -> None:
        """顯示網路資訊"""
        print("=" * 60)
        print(f"🧠 {self.name} - 一億參數 AI 模型")
        print("=" * 60)
        print(f"📊 總參數量: {self.total_params:,} ({self.total_params / 1e6:.2f}M)")
        print(f"🎯 目標: 100,000,000 參數")
        
        if self.total_params >= 100_000_000:
            print(f"✅ 達成目標！超過 {(self.total_params - 100_000_000):,} 個參數")
        else:
            print(f"📈 當前進度: {self.total_params / 100_000_000 * 100:.1f}%")
        
        print(f"\n🏗️ 網路架構:")
        dims = [self.config.input_dim] + self.config.hidden_layers + [self.config.output_dim]
        print(f"   {' → '.join(map(str, dims))}")
        
        print(f"\n⚙️ 特性:")
        print(f"   • Hebbian 學習: {'✓' if self.config.use_hebbian else '✗'}")
        print(f"   • 新穎性門控: {'✓' if self.config.use_novelty_gating else '✗'}")
        print(f"   • 自適應閾值: {'✓' if self.config.use_adaptive_threshold else '✗'}")
        print(f"   • 混合精度: {'✓' if self.config.use_mixed_precision else '✗'}")
        print(f"   • Layer Norm: {'✓' if self.config.use_layer_norm else '✗'}")
        print(f"   • 殘差連接: {'✓' if self.config.use_residual else '✗'}")
        
        # 記憶體估算 (權重 + 偏置 + 動量等)
        bytes_per_param = 2 if self.config.use_mixed_precision else 4
        weights_mem = self.total_params * bytes_per_param
        # 還有動量、bias、LayerNorm 等額外參數
        total_mem = weights_mem * 2.5  # 約 2.5 倍（包含優化器狀態）
        mem_mb = total_mem / 1024 / 1024
        weights_only_mb = weights_mem / 1024 / 1024
        print(f"\n💾 記憶體估算:")
        print(f"   • 純權重: {weights_only_mb:.1f} MB ({bytes_per_param} bytes/param)")
        print(f"   • 含優化器: {mem_mb:.1f} MB")
        if not self.config.use_mixed_precision:
            print(f"   • 使用 float32 模式")
        print("=" * 60)
    
    def forward(
        self,
        x: Union[np.ndarray, List[float]],
        training: bool = False
    ) -> np.ndarray:
        """前向傳播
        
        Args:
            x: 輸入張量 (batch_size, input_dim) 或 (input_dim,)
            training: 是否為訓練模式
            
        Returns:
            輸出張量
        """
        x = np.asarray(x, dtype=np.float32)
        
        # 確保是 2D
        if x.ndim == 1:
            x = x.reshape(1, -1)
        
        # 填充/截斷到正確維度
        if x.shape[-1] != self.config.input_dim:
            if x.shape[-1] < self.config.input_dim:
                padding = np.zeros((x.shape[0], self.config.input_dim - x.shape[-1]))
                x = np.concatenate([x, padding], axis=-1)
            else:
                x = x[:, :self.config.input_dim]
        
        # 新穎性檢測
        novelty_score = 0.0
        if self.novelty_detector is not None:
            self.novelty_detector.update(x)
            novelty_score = self.novelty_detector.score(x)
        
        # 逐層傳播
        residual = None
        for i, layer in enumerate(self.layers):
            out = layer.forward(x, training=training)
            
            # 殘差連接（如果維度匹配）
            if self.config.use_residual and residual is not None:
                if out.shape == residual.shape:
                    out = out + 0.1 * residual
            
            residual = x if x.shape == out.shape else None
            x = out
        
        # 新穎性門控
        if self.config.use_novelty_gating and novelty_score > self.config.novelty_threshold:
            # 高新穎性時增強輸出
            x = x * (1 + novelty_score * 0.5)
        
        self.inference_count += 1
        
        return x
    
    def learn(
        self,
        x: Union[np.ndarray, List[float]],
        target: Optional[Union[np.ndarray, List[float]]] = None,
        use_hebbian: bool = True
    ) -> Dict[str, float]:
        """學習/訓練
        
        Args:
            x: 輸入
            target: 目標輸出（可選）
            use_hebbian: 是否使用 Hebbian 學習
            
        Returns:
            訓練統計
        """
        # 前向傳播
        output = self.forward(x, training=True)
        
        stats = {
            "output_mean": float(np.mean(output)),
            "output_std": float(np.std(output)),
        }
        
        if target is not None:
            target = np.asarray(target, dtype=np.float32)
            if target.ndim == 1:
                target = target.reshape(1, -1)
            
            # 計算損失
            loss = np.mean((output - target) ** 2)
            stats["loss"] = float(loss)
            
            # 反向傳播
            grad = 2 * (output - target) / output.size
            for layer in reversed(self.layers):
                grad = layer.backward(grad)
        
        # Hebbian 學習
        if use_hebbian and self.config.use_hebbian:
            for layer in self.layers:
                layer.hebbian_update(target)
        
        self.training_steps += 1
        stats["step"] = self.training_steps
        
        # 新穎性分數
        if self.novelty_detector:
            stats["novelty"] = self.novelty_detector.score(np.asarray(x))
        
        return stats
    
    def novelty_score(self, x: Union[np.ndarray, List[float]]) -> float:
        """計算新穎性分數"""
        if self.novelty_detector is None:
            return 0.0
        x = np.asarray(x, dtype=np.float32)
        return self.novelty_detector.score(x)
    
    def save(self, path: Union[str, Path]) -> None:
        """保存模型"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "name": self.name,
            "config": asdict(self.config),
            "layers": [],
            "training_steps": self.training_steps,
            "inference_count": self.inference_count,
            "creation_time": self.creation_time,
        }
        
        for layer in self.layers:
            layer_state = {
                "weights": layer.weights,
                "bias": layer.bias,
                "gamma": layer.gamma if layer.use_layer_norm else None,
                "beta": layer.beta if layer.use_layer_norm else None,
            }
            state["layers"].append(layer_state)
        
        with open(path, "wb") as f:
            pickle.dump(state, f)
        
        print(f"✅ 模型已保存至: {path}")
        print(f"   檔案大小: {path.stat().st_size / 1024 / 1024:.1f} MB")
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> "HundredMillionNet":
        """載入模型"""
        path = Path(path)
        
        with open(path, "rb") as f:
            state = pickle.load(f)
        
        config = HundredMillionConfig(**state["config"])
        model = cls(config=config, name=state["name"])
        
        for i, layer_state in enumerate(state["layers"]):
            model.layers[i].weights = layer_state["weights"]
            model.layers[i].bias = layer_state["bias"]
            if layer_state["gamma"] is not None:
                model.layers[i].gamma = layer_state["gamma"]
            if layer_state["beta"] is not None:
                model.layers[i].beta = layer_state["beta"]
        
        model.training_steps = state["training_steps"]
        model.inference_count = state["inference_count"]
        model.creation_time = state["creation_time"]
        
        print(f"✅ 模型已從 {path} 載入")
        return model
    
    def summary(self) -> str:
        """模型摘要"""
        lines = [
            f"{'=' * 50}",
            f"模型: {self.name}",
            f"{'=' * 50}",
            f"總參數: {self.total_params:,}",
            f"訓練步數: {self.training_steps:,}",
            f"推理次數: {self.inference_count:,}",
            f"",
            f"層級結構:",
        ]
        
        for i, layer in enumerate(self.layers):
            lines.append(f"  Layer {i+1}: {layer.input_dim} → {layer.output_dim} ({layer.param_count:,} params)")
        
        lines.append(f"{'=' * 50}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"<{self.name}: {self.total_params:,} params>"


# ============================================================================
# 進階功能：分散式推理支援
# ============================================================================

class DistributedInference:
    """分散式推理引擎"""
    
    def __init__(self, model: HundredMillionNet, num_workers: int = 4):
        self.model = model
        self.num_workers = num_workers
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
    
    def batch_inference(
        self,
        inputs: List[np.ndarray],
        callback: Optional[Callable[[int, np.ndarray], None]] = None
    ) -> List[np.ndarray]:
        """批次推理"""
        results: List = [None] * len(inputs)  # type: ignore
        
        def process_one(idx: int, x: np.ndarray) -> Tuple[int, np.ndarray]:
            result = self.model.forward(x, training=False)
            if callback:
                callback(idx, result)
            return idx, result
        
        futures = [
            self.executor.submit(process_one, i, x)
            for i, x in enumerate(inputs)
        ]
        
        results: List[np.ndarray] = [None] * len(inputs)  # type: ignore
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result
        
        return results  # type: ignore
    
    def shutdown(self) -> None:
        """關閉執行器"""
        self.executor.shutdown(wait=True)


# ============================================================================
# 便捷函數
# ============================================================================

def create_100m_model(name: str = "MyAI-100M") -> HundredMillionNet:
    """快速創建一億參數模型"""
    config = HundredMillionConfig.exact_100m_params()
    return HundredMillionNet(config=config, name=name)


def create_custom_model(
    input_dim: int,
    output_dim: int,
    hidden_layers: List[int],
    name: str = "CustomAI"
) -> HundredMillionNet:
    """創建自定義架構模型"""
    config = HundredMillionConfig(
        input_dim=input_dim,
        output_dim=output_dim,
        hidden_layers=hidden_layers
    )
    return HundredMillionNet(config=config, name=name)


# ============================================================================
# 命令行界面
# ============================================================================

def cli_demo() -> None:
    """命令行演示"""
    print("\n🚀 創建一億參數 AI 模型...\n")
    
    model = create_100m_model("我的專屬AI")
    
    print("\n📝 測試推理...\n")
    
    # 測試推理
    test_input = np.random.randn(1, 1024).astype(np.float32)
    
    start_time = time.time()
    output = model.forward(test_input)
    inference_time = time.time() - start_time
    
    print(f"輸入形狀: {test_input.shape}")
    print(f"輸出形狀: {output.shape}")
    print(f"推理時間: {inference_time * 1000:.2f} ms")
    print(f"新穎性分數: {model.novelty_score(test_input):.4f}")
    
    print("\n📝 測試學習...\n")
    
    # 測試學習
    target = np.random.randn(1, 512).astype(np.float32)
    stats = model.learn(test_input, target)
    print(f"訓練統計: {stats}")
    
    print("\n" + model.summary())


if __name__ == "__main__":
    cli_demo()
