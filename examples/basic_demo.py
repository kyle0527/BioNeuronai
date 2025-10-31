#!/usr/bin/env python3
"""
BioNeuronAI 基本使用範例
演示如何使用 BioNeuron 進行模式學習和新穎性檢測
"""

import json
import sys
from pathlib import Path

import numpy as np

# matplotlib is optional and is imported locally in plot_learning_curve()
# to avoid import-time errors when matplotlib is not installed.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioneuronai.core import BioNeuron, BioNet, NetworkBuilder


class ScalingNeuron(BioNeuron):
    """簡單的縮放型神經元，示範如何混合不同類型神經元"""

    def __init__(self, *, scale: float = 0.5, **kwargs):
        super().__init__(**kwargs)
        self.scale = scale

    def forward(self, inputs):  # type: ignore[override]
        base = super().forward(inputs)
        return min(1.0, base * self.scale)


def demo_basic_neuron():
    """演示單一神經元的基本功能"""
    print("=== 基本神經元演示 ===")
    
    # 創建神經元
    neuron = BioNeuron(num_inputs=2, threshold=0.6, learning_rate=0.05, seed=42)
    
    # 訓練數據：簡單的 AND 邏輯
    training_data = [
        ([0.0, 0.0], 0.0),
        ([0.0, 1.0], 0.0),
        ([1.0, 0.0], 0.0),
        ([1.0, 1.0], 1.0),
    ]
    
    print("訓練前的權重:", neuron.weights)
    
    # 訓練過程
    for epoch in range(50):
        for inputs, target in training_data:
            output = neuron.forward(inputs)
            # 使用目標值進行學習
            neuron.hebbian_learn(inputs, target)
    
    print("訓練後的權重:", neuron.weights)
    
    # 測試
    print("\n測試結果:")
    for inputs, expected in training_data:
        output = neuron.forward(inputs)
        print(f"輸入 {inputs} -> 輸出 {output:.3f} (期望 {expected})")


def demo_novelty_detection():
    """演示新穎性檢測功能"""
    print("\n=== 新穎性檢測演示 ===")
    
    neuron = BioNeuron(num_inputs=2, memory_len=10, seed=42)
    
    # 規律性數據
    print("輸入規律性數據:")
    for i in range(5):
        inputs = [0.5, 0.5]  # 相同輸入
        output = neuron.forward(inputs)
        novelty = neuron.novelty_score()
        print(f"步驟 {i+1}: 輸入 {inputs} -> 新穎性 {novelty:.3f}")
    
    # 變化數據
    print("\n輸入變化數據:")
    varied_inputs = [[0.1, 0.9], [0.8, 0.2], [0.3, 0.7], [0.9, 0.1]]
    for i, inputs in enumerate(varied_inputs):
        output = neuron.forward(inputs)
        novelty = neuron.novelty_score()
        print(f"步驟 {i+6}: 輸入 {inputs} -> 新穎性 {novelty:.3f}")


def demo_network_adaptation():
    """演示網路適應性學習"""
    print("\n=== 網路適應性學習演示 ===")

    builder = NetworkBuilder({"ScalingNeuron": ScalingNeuron})
    custom_config = {
        "input_dim": 2,
        "layers": [
            {"size": 3, "neuron_type": "ScalingNeuron", "params": {"scale": 0.7}},
            {"size": 4},
            {"size": 2, "neuron_type": "ScalingNeuron", "params": {"scale": 1.2}},
        ],
    }
    net = BioNet(config=custom_config, builder=builder)

    # 生成一些測試數據
    np.random.seed(42)
    test_patterns = [
        [0.2, 0.8],
        [0.7, 0.3],
        [0.9, 0.1],
        [0.1, 0.9],
        [0.5, 0.5],
    ]
    
    print("網路學習過程:")
    for epoch in range(3):
        print(f"\n第 {epoch + 1} 輪:")
        for i, pattern in enumerate(test_patterns):
            final_out, layer_outputs = net.forward(pattern)
            novelty = net.layers[0].neurons[0].novelty_score()

            print(
                f"  模式 {i+1} {pattern}: 最終輸出={final_out}"
                f" | 第一層={layer_outputs[0]} | 新穎性={novelty:.3f}"
            )

            # 學習
            net.learn(pattern)


def demo_loading_from_json(tmp_dir: Path | None = None):
    """演示如何從 JSON 設定建構網路"""
    print("\n=== JSON 設定載入示例 ===")

    config = {
        "input_dim": 3,
        "layers": [
            {"size": 2, "params": {"threshold": 0.4}},
            {"size": 2},
        ],
    }
    tmp_dir = tmp_dir or Path.cwd()
    json_path = tmp_dir / "demo_network.json"
    json_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"設定檔已寫入：{json_path}")

    net = BioNet(config=json_path)
    final_out, layer_outputs = net.forward([0.1, 0.5, 0.9])
    print(f"最終輸出：{final_out} | 各層輸出：{layer_outputs}")

    try:
        json_path.unlink()
    except OSError:
        pass


def plot_learning_curve():
    """繪製學習曲線（需要 matplotlib）"""
    try:
        import matplotlib.pyplot as plt
        
        print("\n=== 學習曲線分析 ===")
        
        neuron = BioNeuron(num_inputs=2, learning_rate=0.1, seed=42)
        
        # 固定目標模式
        target_pattern = [0.8, 0.6]
        target_output = 1.0
        
        outputs = []
        novelties = []
        
        # 收集學習數據
        for i in range(100):
            # 添加噪音
            noisy_input = [
                target_pattern[0] + np.random.normal(0, 0.1),
                target_pattern[1] + np.random.normal(0, 0.1)
            ]
            
            output = neuron.forward(noisy_input)
            novelty = neuron.novelty_score()
            
            outputs.append(output)
            novelties.append(novelty)
            
            # 學習
            neuron.hebbian_learn(noisy_input, target_output)
        
        # 繪圖
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        ax1.plot(outputs)
        ax1.set_title('神經元輸出隨時間變化')
        ax1.set_ylabel('輸出值')
        ax1.grid(True)
        
        ax2.plot(novelties)
        ax2.set_title('新穎性評分隨時間變化')
        ax2.set_xlabel('時間步')
        ax2.set_ylabel('新穎性評分')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('learning_curve.png', dpi=150)
        print("學習曲線已保存為 learning_curve.png")
        
    except ImportError:
        print("matplotlib 未安裝，跳過繪圖演示")


def main():
    """主函數"""
    print("BioNeuronAI 使用範例")
    print("=" * 50)
    
    demo_basic_neuron()
    demo_novelty_detection()
    demo_network_adaptation()
    demo_loading_from_json()
    plot_learning_curve()

    print("\n演示完成！")


if __name__ == "__main__":
    main()
