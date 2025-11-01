"""
測試一億參數 BioNeuronAI 核心
===========================

測試 mega_core 模組的各項功能
"""

import numpy as np
import sys
import os

# 添加 src 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bioneuronai.mega_core import (
    MegaBioNeuron, MegaBioLayer, MegaBioNet,
    NetworkTopology, create_hundred_million_param_network
)


class TestMegaBioNeuron:
    """測試 MegaBioNeuron 類別"""
    
    def test_neuron_creation(self):
        """測試神經元創建"""
        neuron = MegaBioNeuron(num_inputs=100, sparsity=0.8)
        assert neuron.num_inputs == 100
        assert neuron.sparsity == 0.8
        expected_connections = int(100 * (1 - 0.8))
        assert len(neuron.sparse_weights) == expected_connections
        
    def test_forward_pass(self):
        """測試前向傳播"""
        neuron = MegaBioNeuron(num_inputs=50, sparsity=0.5)
        inputs = np.random.random(50)
        output = neuron.forward(inputs)
        assert isinstance(output, float)
        assert -2.0 <= output <= 2.0  # 合理的輸出範圍
        
    def test_learning(self):
        """測試學習功能"""
        neuron = MegaBioNeuron(num_inputs=20, sparsity=0.6)
        inputs = np.random.random(20)
        
        # 記錄學習前的權重
        initial_weights = neuron.sparse_weights.copy()
        
        # 進行學習
        neuron.hebbian_learn(inputs, target=0.8)
        
        # 驗證權重已更新
        assert not np.array_equal(initial_weights, neuron.sparse_weights)
        
    def test_novelty_calculation(self):
        """測試新穎性計算"""
        neuron = MegaBioNeuron(num_inputs=10)
        
        # 初始狀態新穎性應該為 0
        assert neuron.calculate_novelty() == 0.0
        
        # 添加一些輸入歷史
        neuron.forward(np.ones(10))
        neuron.forward(np.zeros(10))
        
        # 現在應該有新穎性
        novelty = neuron.calculate_novelty()
        assert 0.0 <= novelty <= 1.0
        
    def test_memory_usage(self):
        """測試記憶體使用計算"""
        neuron = MegaBioNeuron(num_inputs=1000, sparsity=0.9)
        memory = neuron.get_memory_usage()
        assert memory > 0
        assert isinstance(memory, int)


class TestMegaBioLayer:
    """測試 MegaBioLayer 類別"""
    
    def test_layer_creation(self):
        """測試層創建"""
        layer = MegaBioLayer(num_neurons=10, input_dim=20)
        assert len(layer.neurons) == 10
        assert layer.input_dim == 20
        
    def test_layer_forward(self):
        """測試層前向傳播"""
        layer = MegaBioLayer(num_neurons=5, input_dim=10)
        inputs = np.random.random(10)
        outputs = layer.forward(inputs)
        
        assert len(outputs) == 5  # 5個神經元輸出
        assert all(isinstance(output, float) for output in outputs)
        
    def test_layer_learning(self):
        """測試層學習"""
        layer = MegaBioLayer(num_neurons=3, input_dim=5)
        inputs = np.random.random(5)
        
        # 無監督學習
        layer.learn(inputs)
        
        # 有監督學習
        targets = np.random.random(3)
        layer.learn(inputs, targets)
        
    def test_layer_statistics(self):
        """測試層統計"""
        layer = MegaBioLayer(num_neurons=5, input_dim=10)
        stats = layer.get_layer_stats()
        
        assert 'num_neurons' in stats
        assert 'memory_usage_mb' in stats
        assert 'avg_novelty' in stats
        assert stats['num_neurons'] == 5


class TestNetworkTopology:
    """測試 NetworkTopology 類別"""
    
    def test_topology_creation(self):
        """測試拓撲創建"""
        topology = NetworkTopology(
            input_dim=100,
            hidden_layers=[200, 300],
            output_dim=50
        )
        
        assert topology.input_dim == 100
        assert topology.hidden_layers == [200, 300]
        assert topology.output_dim == 50
        assert topology.total_parameters > 0
        
    def test_parameter_calculation(self):
        """測試參數量計算"""
        topology = NetworkTopology(
            input_dim=2,
            hidden_layers=[3],
            output_dim=1
        )
        
        # 手動計算: (2*3 + 3) + (3*1 + 1) = 6+3+3+1 = 13
        expected_params = (2 * 3 + 3) + (3 * 1 + 1)
        assert topology.total_parameters == expected_params


class TestMegaBioNet:
    """測試 MegaBioNet 類別"""
    
    def test_small_network_creation(self):
        """測試小型網路創建"""
        topology = NetworkTopology(
            input_dim=10,
            hidden_layers=[20, 15],
            output_dim=5
        )
        
        network = MegaBioNet(topology=topology, sparsity=0.5)
        assert len(network.layers) == 3  # 2隱藏層 + 1輸出層
        assert network.topology.input_dim == 10
        
    def test_network_forward(self):
        """測試網路前向傳播"""
        topology = NetworkTopology(
            input_dim=5,
            hidden_layers=[10],
            output_dim=3
        )
        
        network = MegaBioNet(topology=topology)
        inputs = np.random.random(5)
        outputs = network.forward(inputs)
        
        assert len(outputs) == 3
        assert all(isinstance(output, (float, np.floating)) for output in outputs)
        
    def test_network_learning(self):
        """測試網路學習"""
        topology = NetworkTopology(
            input_dim=5,
            hidden_layers=[8],
            output_dim=3
        )
        
        network = MegaBioNet(topology=topology)
        inputs = np.random.random(5)
        targets = np.random.random(3)
        
        initial_steps = network.training_steps
        
        # 關閉新穎性門控以確保學習發生
        network.learn(inputs, targets, use_novelty_gating=False)
        
        # 確認訓練步數增加
        assert network.training_steps == initial_steps + 1
        
    def test_network_statistics(self):
        """測試網路統計"""
        topology = NetworkTopology(
            input_dim=10,
            hidden_layers=[15],
            output_dim=5
        )
        
        network = MegaBioNet(topology=topology)
        stats = network.get_network_stats()
        
        required_keys = [
            'total_parameters', 'total_memory_mb', 'training_steps',
            'current_lr', 'network_novelty', 'layer_stats'
        ]
        
        for key in required_keys:
            assert key in stats
            
    def test_checkpoint_saving(self):
        """測試檢查點儲存"""
        topology = NetworkTopology(
            input_dim=5,
            hidden_layers=[10],
            output_dim=3
        )
        
        network = MegaBioNet(topology=topology)
        checkpoint_path = "/tmp/test_checkpoint.json"
        
        # 儲存檢查點
        network.save_checkpoint(checkpoint_path)
        
        # 驗證檔案存在
        assert os.path.exists(checkpoint_path)
        
        # 清理
        os.remove(checkpoint_path)


class TestHundredMillionParamNetwork:
    """測試一億參數網路"""
    
    def test_creation(self):
        """測試一億參數網路創建"""
        network = create_hundred_million_param_network()
        
        # 驗證基本屬性
        assert isinstance(network, MegaBioNet)
        assert network.actual_parameters > 10_000_000  # 至少1千萬參數
        assert len(network.layers) > 1
        
    def test_forward_pass(self):
        """測試一億參數網路前向傳播"""
        network = create_hundred_million_param_network()
        
        # 準備輸入
        inputs = np.random.random(network.topology.input_dim)
        
        # 前向傳播
        outputs = network.forward(inputs)
        
        # 驗證輸出
        assert len(outputs) == network.topology.output_dim
        assert all(isinstance(output, (float, np.floating)) for output in outputs)
        
    def test_performance_metrics(self):
        """測試性能指標"""
        network = create_hundred_million_param_network()
        stats = network.get_network_stats()
        
        # 驗證關鍵指標
        assert stats['total_parameters'] > 1_000_000  # 至少百萬參數
        assert stats['total_memory_mb'] > 0  # 使用了記憶體
        assert 0 <= stats['target_vs_actual_params']['efficiency'] <= 1  # 效率在合理範圍


def test_integration():
    """整合測試"""
    print("執行 BioNeuronAI 一億參數核心整合測試...")
    
    # 創建網路
    network = create_hundred_million_param_network()
    
    # 生成測試資料
    inputs = np.random.random(network.topology.input_dim)
    targets = np.random.random(network.topology.output_dim)
    
    # 測試完整流程
    outputs = network.forward(inputs)
    
    # 關閉新穎性門控以確保學習發生
    network.learn(inputs, targets, use_novelty_gating=False)
    stats = network.get_network_stats()
    
    # 驗證結果
    assert len(outputs) == len(targets)
    assert stats['training_steps'] > 0
    
    print("✓ 整合測試通過")


def run_all_tests():
    """運行所有測試"""
    test_classes = [
        TestMegaBioNeuron,
        TestMegaBioLayer, 
        TestNetworkTopology,
        TestMegaBioNet,
        TestHundredMillionParamNetwork
    ]
    
    total_tests = 0
    passed_tests = 0
    
    print("開始執行 BioNeuronAI 一億參數核心測試...")
    print("=" * 60)
    
    for test_class in test_classes:
        print(f"\n測試 {test_class.__name__}:")
        
        instance = test_class()
        methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for method_name in methods:
            try:
                method = getattr(instance, method_name)
                method()
                print(f"  ✓ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {e}")
            total_tests += 1
    
    # 執行整合測試
    print(f"\n測試整合:")
    try:
        test_integration()
        print(f"  ✓ test_integration")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ test_integration: {e}")
    total_tests += 1
    
    print("\n" + "=" * 60)
    print(f"測試結果: {passed_tests}/{total_tests} 通過 ({passed_tests/total_tests*100:.1f}%)")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)