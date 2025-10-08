#!/usr/bin/env python3
"""
改進的 BioNeuronAI 範例 - 解決學習問題並添加更多實用功能
"""

import numpy as np
from bioneuronai.core import BioNeuron, BioNet


def demo_improved_learning():
    """演示改進的學習機制"""
    print("=== 改進的學習機制演示 ===")
    
    # 使用更低的閾值和學習率進行更精細的控制
    neuron = BioNeuron(num_inputs=2, threshold=0.3, learning_rate=0.02, seed=42)
    
    # AND 邏輯訓練數據
    training_data = [
        ([0.0, 0.0], 0.0),
        ([0.0, 1.0], 0.0),
        ([1.0, 0.0], 0.0),
        ([1.0, 1.0], 1.0),
    ]
    
    print("訓練前權重:", neuron.weights)
    
    # 更長的訓練過程，使用差異化學習
    for epoch in range(100):
        for inputs, target in training_data:
            output = neuron.forward(inputs)
            # 計算誤差並調整學習強度
            error = target - output
            adjusted_target = target if error > 0 else max(0, output - 0.1)
            neuron.hebbian_learn(inputs, adjusted_target)
    
    print("訓練後權重:", neuron.weights)
    
    # 測試結果
    print("\n測試結果:")
    correct = 0
    for inputs, expected in training_data:
        output = neuron.forward(inputs)
        prediction = 1.0 if output > 0.5 else 0.0
        is_correct = abs(prediction - expected) < 0.1
        correct += is_correct
        status = "✓" if is_correct else "✗" 
        print(f"{status} 輸入 {inputs} -> 輸出 {output:.3f} -> 預測 {prediction} (期望 {expected})")
    
    accuracy = correct / len(training_data) * 100
    print(f"\n準確率: {accuracy:.1f}%")


def demo_pattern_recognition():
    """演示模式識別能力"""
    print("\n=== 模式識別演示 ===")
    
    # 創建一個用於模式識別的神經元
    neuron = BioNeuron(num_inputs=4, threshold=0.5, learning_rate=0.05, seed=42)
    
    # 定義兩個不同的模式
    pattern_A = [1.0, 0.0, 1.0, 0.0]  # 模式 A
    pattern_B = [0.0, 1.0, 0.0, 1.0]  # 模式 B
    
    print(f"模式 A: {pattern_A}")
    print(f"模式 B: {pattern_B}")
    
    # 訓練識別模式 A
    print("\n訓練識別模式 A...")
    for _ in range(50):
        # 模式 A 的變體（加入小量噪音）
        noisy_A = [p + np.random.normal(0, 0.1) for p in pattern_A]
        output = neuron.forward(noisy_A)
        neuron.hebbian_learn(noisy_A, 1.0)
        
        # 模式 B 應該產生低輸出
        noisy_B = [p + np.random.normal(0, 0.1) for p in pattern_B]
        output = neuron.forward(noisy_B)
        neuron.hebbian_learn(noisy_B, 0.0)
    
    # 測試模式識別
    print("\n測試模式識別:")
    for name, pattern in [("A", pattern_A), ("B", pattern_B)]:
        output = neuron.forward(pattern)
        novelty = neuron.novelty_score()
        print(f"模式 {name}: 輸出={output:.3f}, 新穎性={novelty:.3f}")
        
        # 測試含噪音的版本
        for i in range(3):
            noisy = [p + np.random.normal(0, 0.2) for p in pattern]
            output = neuron.forward(noisy)
            print(f"  含噪音版本{i+1}: 輸出={output:.3f}")


def demo_adaptive_threshold():
    """演示自適應閾值調整"""
    print("\n=== 自適應閾值演示 ===")
    
    class AdaptiveBioNeuron(BioNeuron):
        """帶自適應閾值的神經元"""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.threshold_history = []
            self.adaptation_rate = 0.01
        
        def adaptive_threshold(self, recent_outputs):
            """根據最近輸出調整閾值"""
            if len(recent_outputs) < 5:
                return
                
            avg_output = np.mean(recent_outputs)
            if avg_output > 0.8:  # 如果輸出過高，提高閾值
                self.threshold = min(1.0, self.threshold + self.adaptation_rate)
            elif avg_output < 0.2:  # 如果輸出過低，降低閾值
                self.threshold = max(0.0, self.threshold - self.adaptation_rate)
            
            self.threshold_history.append(self.threshold)
    
    # 創建自適應神經元
    adaptive_neuron = AdaptiveBioNeuron(num_inputs=2, threshold=0.5, seed=42)
    outputs = []
    
    print("自適應學習過程:")
    # 輸入逐漸增強的模式
    for step in range(20):
        intensity = 0.1 + (step / 20) * 0.8  # 從 0.1 漸增到 0.9
        inputs = [intensity, intensity]
        
        output = adaptive_neuron.forward(inputs)
        outputs.append(output)
        
        # 每 5 步調整一次閾值
        if (step + 1) % 5 == 0:
            adaptive_neuron.adaptive_threshold(outputs[-5:])
        
        if step % 5 == 0:
            threshold = adaptive_neuron.threshold
            print(f"步驟 {step+1:2d}: 強度={intensity:.2f}, 輸出={output:.3f}, 閾值={threshold:.3f}")
    
    print(f"\n閾值變化: {adaptive_neuron.threshold_history[-3:]}")


def demo_ensemble_learning():
    """演示集成學習"""
    print("\n=== 集成學習演示 ===")
    
    # 創建多個不同配置的神經元
    ensemble = [
        BioNeuron(num_inputs=2, threshold=0.3, learning_rate=0.01, seed=i)
        for i in range(42, 47)  # 5個神經元，不同隨機種子
    ]
    
    # 測試數據
    test_patterns = [
        [0.1, 0.9],
        [0.5, 0.5], 
        [0.9, 0.1],
        [0.8, 0.8]
    ]
    
    print("集成預測結果:")
    for i, pattern in enumerate(test_patterns):
        outputs = []
        novelties = []
        
        for j, neuron in enumerate(ensemble):
            output = neuron.forward(pattern)
            novelty = neuron.novelty_score()
            outputs.append(output)
            novelties.append(novelty)
        
        # 集成決策：平均輸出和最大新穎性
        avg_output = np.mean(outputs)
        max_novelty = np.max(novelties)
        consensus = np.std(outputs)  # 標準差表示一致性
        
        print(f"模式 {i+1} {pattern}:")
        print(f"  個別輸出: {[f'{o:.2f}' for o in outputs]}")
        print(f"  集成輸出: {avg_output:.3f}, 最大新穎性: {max_novelty:.3f}")
        print(f"  一致性 (越低越好): {consensus:.3f}")


def main():
    """主函數"""
    print("BioNeuronAI 進階範例")
    print("=" * 60)
    
    demo_improved_learning()
    demo_pattern_recognition() 
    demo_adaptive_threshold()
    demo_ensemble_learning()
    
    print("\n進階演示完成！")
    print("\n💡 建議:")
    print("1. 實驗不同的閾值和學習率組合")
    print("2. 嘗試更複雜的輸入模式")
    print("3. 觀察新穎性評分在不同場景下的表現")
    print("4. 考慮實現更多的學習規則變體")


if __name__ == "__main__":
    main()