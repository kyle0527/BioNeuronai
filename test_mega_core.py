#!/usr/bin/env python3
"""
快速測試一億參數核心
"""

import sys
import os
import numpy as np

# 設置 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_mega_core():
    """測試一億參數核心"""
    print("測試 BioNeuronAI 一億參數核心...")
    
    try:
        # 導入模組
        from bioneuronai.mega_core import (
            MegaBioNeuron, NetworkTopology, 
            create_hundred_million_param_network
        )
        print("✓ 成功導入一億參數核心模組")
        
        # 測試單個超大神經元
        print("\n1. 測試 MegaBioNeuron...")
        neuron = MegaBioNeuron(num_inputs=1000, sparsity=0.8)
        test_input = np.random.random(1000)
        output = neuron.forward(test_input)
        print(f"   - 輸入維度: {len(test_input)}")
        print(f"   - 輸出值: {output:.4f}")
        print(f"   - 記憶體使用: {neuron.get_memory_usage()} bytes")
        
        # 測試學習
        neuron.hebbian_learn(test_input, target=0.8)
        novelty = neuron.calculate_novelty()
        print(f"   - 新穎性評分: {novelty:.4f}")
        
        # 測試網路拓撲
        print("\n2. 測試 NetworkTopology...")
        topology = NetworkTopology(
            input_dim=1000,
            hidden_layers=[2000, 3000, 1500],
            output_dim=500
        )
        print(f"   - 預估參數量: {topology.total_parameters:,}")
        
        # 創建一億參數網路
        print("\n3. 創建一億參數網路...")
        mega_net = create_hundred_million_param_network()
        
        # 獲取網路統計
        stats = mega_net.get_network_stats()
        print(f"   - 實際參數量: {stats['total_parameters']:,}")
        print(f"   - 記憶體使用: {stats['total_memory_mb']:.1f} MB")
        print(f"   - 層數: {len(mega_net.layers)}")
        
        # 測試前向傳播
        print("\n4. 測試前向傳播...")
        test_input = np.random.random(mega_net.topology.input_dim)
        output = mega_net.forward(test_input)
        print(f"   - 輸入維度: {len(test_input)}")
        print(f"   - 輸出維度: {len(output)}")
        print(f"   - 輸出範圍: [{np.min(output):.3f}, {np.max(output):.3f}]")
        
        # 測試學習
        print("\n5. 測試學習過程...")
        target = np.random.random(len(output))
        mega_net.learn(test_input, target)
        
        updated_stats = mega_net.get_network_stats()
        print(f"   - 訓練步數: {updated_stats['training_steps']}")
        print(f"   - 當前學習率: {updated_stats['current_lr']:.6f}")
        print(f"   - 網路新穎性: {updated_stats['network_novelty']:.4f}")
        
        print("\n✓ 所有測試通過！一億參數核心運行正常")
        return True
        
    except ImportError as e:
        print(f"✗ 導入錯誤: {e}")
        return False
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mega_core()
    sys.exit(0 if success else 1)