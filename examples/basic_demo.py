#!/usr/bin/env python3
"""
BioNeuronAI 基本使用範例
演示如何使用 BioNeuron 進行模式學習、新穎性檢測，以及保存/載入持久化狀態。

教學重點：
1. 建立神經元並啟用在線學習模式，透過滑動窗口避免災難性遺忘。
2. 使用 `save_state()` 與 `load_state()` 在磁碟間傳遞權重、記憶與閾值。
3. 將持久化流程整合至 `BioNet`，作為部署前快照範例。
"""

from pathlib import Path

import numpy as np
# matplotlib is optional and is imported locally in plot_learning_curve()
# to avoid import-time errors when matplotlib is not installed.
from bioneuronai.core import BioNeuron, BioNet


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

    # 展示在線學習模式：啟用滑動窗口與穩定化
    neuron.configure_online_learning(window_size=5, stability_coefficient=0.1)
    for inputs, _ in training_data:
        neuron.online_learn(inputs)
    print("在線模式啟用後的權重:", neuron.weights)


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
    
    net = BioNet()
    
    # 生成一些測試數據
    np.random.seed(42)
    test_patterns = [
        [0.2, 0.8],
        [0.7, 0.3],
        [0.9, 0.1],
        [0.1, 0.9],
        [0.5, 0.5]
    ]
    
    print("網路學習過程:")
    for epoch in range(3):
        print(f"\n第 {epoch + 1} 輪:")
        for i, pattern in enumerate(test_patterns):
            l2_out, l1_out = net.forward(pattern)
            novelty = net.layer1.neurons[0].novelty_score()
            
            print(f"  模式 {i+1} {pattern}: 輸出={l2_out[0]:.3f}, 新穎性={novelty:.3f}")
            
            # 學習
            net.learn(pattern)

    # 保存並重新載入網路狀態
    snapshot = Path("basic_net_state.npz")
    net.configure_online_learning(window_size=5, stability_coefficient=0.05)
    net.save_state(snapshot)
    restored = BioNet.load_state(snapshot)
    restored.configure_online_learning(window_size=5, stability_coefficient=0.05)
    l2_out_restored, _ = restored.forward(test_patterns[-1])
    print(f"\n重新載入後的輸出: {l2_out_restored[0]:.3f} (狀態保存於 {snapshot})")


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
    plot_learning_curve()

    print("\n您可以刪除 basic_net_state.npz 以清理示例產生的檔案。")
    
    print("\n演示完成！")


if __name__ == "__main__":
    main()