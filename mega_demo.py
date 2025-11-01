#!/usr/bin/env python3
"""
一億參數 BioNeuronAI 核心示範
============================

這個腳本展示如何使用 BioNeuronAI 的一億參數超大規模核心。
包含網路創建、訓練和效能測試。
"""

import sys
import time
import numpy as np
from pathlib import Path

# 添加 src 路徑以便導入
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from bioneuronai.mega_core import (
        MegaBioNet, NetworkTopology, 
        create_hundred_million_param_network,
        demo_mega_network
    )
    print("✓ 成功導入 BioNeuronAI 一億參數核心模組")
except ImportError as e:
    print(f"✗ 導入失敗: {e}")
    print("請確保已安裝 bioneuronai 套件")
    sys.exit(1)


def test_network_scalability():
    """測試網路可擴展性"""
    print("\n" + "="*60)
    print("測試網路可擴展性")
    print("="*60)
    
    # 測試不同規模的網路
    test_configs = [
        {
            'name': '小型網路 (1萬參數)',
            'topology': NetworkTopology(
                input_dim=100,
                hidden_layers=[200, 150],
                output_dim=50
            ),
            'sparsity': 0.5
        },
        {
            'name': '中型網路 (100萬參數)', 
            'topology': NetworkTopology(
                input_dim=500,
                hidden_layers=[1000, 800, 600],
                output_dim=200
            ),
            'sparsity': 0.7
        },
        {
            'name': '大型網路 (1000萬參數)',
            'topology': NetworkTopology(
                input_dim=1000,
                hidden_layers=[3000, 4000, 2000],
                output_dim=500
            ),
            'sparsity': 0.85
        }
    ]
    
    for config in test_configs:
        print(f"\n測試 {config['name']}:")
        print(f"預估參數量: {config['topology'].total_parameters:,}")
        
        # 創建網路
        start_time = time.time()
        network = MegaBioNet(
            topology=config['topology'],
            sparsity=config['sparsity']
        )
        create_time = time.time() - start_time
        
        # 測試前向傳播
        test_input = np.random.random(config['topology'].input_dim)
        
        start_time = time.time()
        output = network.forward(test_input)
        forward_time = time.time() - start_time
        
        # 顯示結果
        stats = network.get_network_stats()
        print(f"  - 實際參數量: {stats['total_parameters']:,}")
        print(f"  - 記憶體使用: {stats['total_memory_mb']:.1f} MB")
        print(f"  - 創建時間: {create_time:.3f} 秒")
        print(f"  - 前向傳播時間: {forward_time:.3f} 秒")
        print(f"  - 參數效率: {stats['target_vs_actual_params']['efficiency']:.2%}")


def test_learning_capabilities():
    """測試學習能力"""
    print("\n" + "="*60)
    print("測試學習能力")
    print("="*60)
    
    # 創建中等規模的網路進行學習測試
    topology = NetworkTopology(
        input_dim=50,
        hidden_layers=[200, 300, 150],
        output_dim=20
    )
    
    network = MegaBioNet(topology=topology, sparsity=0.8)
    
    print(f"訓練網路 (參數量: {network.actual_parameters:,})")
    
    # 生成訓練資料
    num_samples = 1000
    input_dim = topology.input_dim
    output_dim = topology.output_dim
    
    # 創建簡單的映射任務 (輸入模式 -> 輸出模式)
    np.random.seed(42)
    train_inputs = []
    train_outputs = []
    
    for i in range(num_samples):
        # 生成隨機輸入
        x = np.random.random(input_dim)
        # 簡單的映射函數 (前20維的平均值影響輸出)
        pattern = np.mean(x[:20])
        y = np.random.random(output_dim) * pattern
        
        train_inputs.append(x)
        train_outputs.append(y)
    
    # 訓練過程
    print("\n開始訓練...")
    training_losses = []
    novelty_scores = []
    
    for epoch in range(10):
        epoch_loss = 0.0
        epoch_novelty = 0.0
        
        start_time = time.time()
        
        for i in range(min(100, num_samples)):  # 每個 epoch 訓練100個樣本
            # 前向傳播
            predicted = network.forward(train_inputs[i])
            
            # 計算損失 (簡單的均方誤差)
            loss = np.mean((np.array(predicted) - np.array(train_outputs[i]))**2)
            epoch_loss += loss
            
            # 學習
            network.learn(train_inputs[i], train_outputs[i])
            
            # 記錄新穎性
            stats = network.get_network_stats()
            epoch_novelty += stats['network_novelty']
        
        epoch_time = time.time() - start_time
        avg_loss = epoch_loss / min(100, num_samples)
        avg_novelty = epoch_novelty / min(100, num_samples)
        
        training_losses.append(avg_loss)
        novelty_scores.append(avg_novelty)
        
        print(f"Epoch {epoch+1:2d}: "
              f"Loss={avg_loss:.4f}, "
              f"Novelty={avg_novelty:.3f}, "
              f"LR={network.global_learning_rate:.4f}, "
              f"Time={epoch_time:.2f}s")
    
    # 顯示學習曲線
    print(f"\n訓練完成!")
    print(f"最終損失: {training_losses[-1]:.4f}")
    print(f"最終新穎性: {novelty_scores[-1]:.3f}")
    print(f"損失改善: {((training_losses[0] - training_losses[-1]) / training_losses[0] * 100):.1f}%")


def test_memory_efficiency():
    """測試記憶體效率"""
    print("\n" + "="*60)
    print("測試記憶體效率")
    print("="*60)
    
    # 比較不同稀疏度設置
    sparsity_levels = [0.0, 0.5, 0.8, 0.9, 0.95]
    
    base_topology = NetworkTopology(
        input_dim=1000,
        hidden_layers=[2000, 1500],
        output_dim=500
    )
    
    print(f"基礎拓撲參數量: {base_topology.total_parameters:,}")
    print(f"\n稀疏度對記憶體使用的影響:")
    
    for sparsity in sparsity_levels:
        network = MegaBioNet(
            topology=base_topology,
            sparsity=sparsity
        )
        
        stats = network.get_network_stats()
        memory_mb = stats['total_memory_mb']
        efficiency = stats['target_vs_actual_params']['efficiency']
        
        print(f"  稀疏度 {sparsity:4.0%}: "
              f"記憶體 {memory_mb:6.1f} MB, "
              f"參數效率 {efficiency:5.1%}")


def benchmark_performance():
    """效能基準測試"""
    print("\n" + "="*60)
    print("效能基準測試")
    print("="*60)
    
    # 創建一億參數網路
    network = create_hundred_million_param_network()
    
    # 準備測試資料
    input_sizes = [100, 500, 1000, 2000]
    batch_sizes = [1, 10, 50]
    
    print(f"網路參數量: {network.actual_parameters:,}")
    print(f"記憶體使用: {network.get_network_stats()['total_memory_mb']:.1f} MB")
    
    print(f"\n效能測試結果:")
    print(f"{'輸入大小':<10} {'批量大小':<10} {'前向時間(ms)':<15} {'學習時間(ms)':<15} {'吞吐量(樣本/秒)':<15}")
    print("-" * 70)
    
    for input_size in input_sizes:
        if input_size > network.topology.input_dim:
            continue
            
        for batch_size in batch_sizes:
            # 生成測試資料
            test_inputs = [
                np.random.random(input_size) 
                for _ in range(batch_size)
            ]
            
            # 測試前向傳播
            start_time = time.time()
            for inputs in test_inputs:
                padded_input = np.pad(inputs, (0, max(0, network.topology.input_dim - input_size)))
                output = network.forward(padded_input)
            forward_time = (time.time() - start_time) * 1000 / batch_size
            
            # 測試學習
            start_time = time.time()
            for inputs in test_inputs:
                padded_input = np.pad(inputs, (0, max(0, network.topology.input_dim - input_size)))
                network.learn(padded_input)
            learn_time = (time.time() - start_time) * 1000 / batch_size
            
            # 計算吞吐量
            total_time_per_sample = (forward_time + learn_time) / 1000
            throughput = 1.0 / total_time_per_sample if total_time_per_sample > 0 else 0
            
            print(f"{input_size:<10} {batch_size:<10} {forward_time:<15.2f} {learn_time:<15.2f} {throughput:<15.1f}")


def main():
    """主要示範函數"""
    print("BioNeuronAI 一億參數核心完整示範")
    print("="*60)
    
    try:
        # 1. 執行基本示範
        print("\n1. 執行基本一億參數網路示範...")
        demo_network = demo_mega_network()
        
        # 2. 測試可擴展性
        test_network_scalability()
        
        # 3. 測試學習能力
        test_learning_capabilities()
        
        # 4. 測試記憶體效率
        test_memory_efficiency()
        
        # 5. 效能基準測試
        benchmark_performance()
        
        print("\n" + "="*60)
        print("所有測試完成! BioNeuronAI 一億參數核心運行正常")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n測試被使用者中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()