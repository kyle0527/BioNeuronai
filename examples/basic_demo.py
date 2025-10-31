#!/usr/bin/env python3
"""BioNeuronAI 基本使用範例

展示以下功能：
1. BioNeuron 神經元的基本使用與新穎性偵測
2. 透過 BioNetConfig 宣告任意拓樸、混合神經元組成的網路
3. 如何將 JSON 組態轉換為網路並進行學習
"""

import json
from typing import List

import numpy as np

from bioneuronai import BioNet, BioNetConfig, BioNeuron, LayerConfig, NeuronConfig


def demo_programmatic_config() -> None:
    """展示如何以程式碼組裝異質網路配置."""

    print("\n=== 程式化定義網路拓樸 ===")
    config = BioNetConfig(
        input_dim=2,
        layers=[
            LayerConfig(
                neurons=[
                    NeuronConfig("BioNeuron", count=2, params={"threshold": 0.6}),
                    NeuronConfig("ImprovedBioNeuron", params={"adaptive_threshold": True}),
                ]
            ),
            LayerConfig(neurons=[NeuronConfig("BioNeuron", count=3)]),
        ],
    )
    net = BioNet(config)
    print(net.summary())


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


def demo_network_adaptation() -> None:
    """演示如何以 JSON 組態宣告異質拓樸並進行學習."""

    print("\n=== 網路適應性學習 (JSON 組態) ===")

    config_payload = {
        "input_dim": 2,
        "layers": [
            {
                "neurons": [
                    {"type": "BioNeuron", "count": 2, "params": {"threshold": 0.7}},
                    {
                        "type": "ImprovedBioNeuron",
                        "params": {"adaptive_threshold": True, "learning_rate": 0.02},
                    },
                ]
            },
            {"neurons": [{"type": "BioNeuron", "count": 2}]},
        ],
    }

    print("宣告 JSON 組態:\n" + json.dumps(config_payload, indent=2, ensure_ascii=False))
    config = BioNetConfig.from_dict(config_payload)
    net = BioNet(config)
    print(net.summary())

    rng = np.random.default_rng(42)
    test_patterns: List[List[float]] = rng.random((5, config.input_dim)).round(2).tolist()

    for epoch in range(2):
        print(f"\n第 {epoch + 1} 輪學習:")
        for pattern in test_patterns:
            activations = net.forward(pattern)
            final_outputs = activations[-1]
            print(f"  輸入 {pattern} -> 最終輸出 {final_outputs}")
            net.learn(pattern, activations)

    print("\n最終層大小:", net.layer_sizes)


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
    demo_programmatic_config()
    demo_network_adaptation()
    plot_learning_curve()
    
    print("\n演示完成！")


if __name__ == "__main__":
    main()
