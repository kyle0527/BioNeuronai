from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from bioneuronai import (
    BioLayer,
    BioNet,
    BioNetConfig,
    BioNeuron,
    LayerConfig,
    NeuronConfig,
)


class TestBioNeuron:
    def test_initialization(self):
        """測試神經元初始化"""
        neuron = BioNeuron(num_inputs=3, threshold=0.5, seed=42)
        assert neuron.num_inputs == 3
        assert neuron.threshold == 0.5
        assert len(neuron.weights) == 3
        assert len(neuron.input_memory) == 0

    def test_forward_pass(self):
        """測試前向傳播"""
        neuron = BioNeuron(num_inputs=2, threshold=0.5, seed=42)
        inputs = [0.8, 0.6]
        output = neuron.forward(inputs)
        
        # 檢查輸出在有效範圍內
        assert 0.0 <= output <= 1.0
        # 檢查記憶體更新
        assert len(neuron.input_memory) == 1
        np.testing.assert_array_almost_equal(neuron.input_memory[0], inputs, decimal=6)

    def test_memory_limit(self):
        """測試記憶體長度限制"""
        neuron = BioNeuron(num_inputs=2, memory_len=3, seed=42)
        
        # 添加超過記憶體限制的輸入
        for i in range(5):
            neuron.forward([i, i])
        
        assert len(neuron.input_memory) == 3
        # 最舊的記憶應該被移除
        assert neuron.input_memory[0][0] == 2.0

    def test_hebbian_learning(self):
        """測試 Hebbian 學習"""
        neuron = BioNeuron(num_inputs=2, learning_rate=0.1, seed=42)
        initial_weights = neuron.weights.copy()
        
        inputs = [1.0, 0.5]
        output = 0.8
        neuron.hebbian_learn(inputs, output)
        
        # 權重應該有所變化
        assert not np.array_equal(initial_weights, neuron.weights)
        # 權重應該在有效範圍內
        assert np.all(neuron.weights >= 0.0)
        assert np.all(neuron.weights <= 1.0)

    def test_novelty_score(self):
        """測試新穎性評分"""
        neuron = BioNeuron(num_inputs=2, seed=42)
        
        # 沒有足夠記憶時
        assert neuron.novelty_score() == 0.0
        
        # 添加相同輸入
        neuron.forward([1.0, 1.0])
        neuron.forward([1.0, 1.0])
        novelty1 = neuron.novelty_score()
        
        # 添加不同輸入
        neuron.forward([0.0, 0.0])
        novelty2 = neuron.novelty_score()
        
        # 不同輸入應該有更高的新穎性
        assert novelty2 > novelty1


class TestBioLayer:
    def test_layer_forward(self):
        """測試層級前向傳播"""
        layer = BioLayer(n_neurons=3, input_dim=2)
        inputs = [0.5, 0.8]
        outputs = layer.forward(inputs)
        
        assert len(outputs) == 3
        assert all(0.0 <= out <= 1.0 for out in outputs)

    def test_layer_learning(self):
        """測試層級學習"""
        layer = BioLayer(n_neurons=2, input_dim=2)
        inputs = [0.6, 0.4]
        outputs = [0.8, 0.3]
        
        # 記錄初始權重
        initial_weights = [n.weights.copy() for n in layer.neurons]
        
        layer.learn(inputs, outputs)
        
        # 檢查權重是否更新
        for i, neuron in enumerate(layer.neurons):
            assert not np.array_equal(initial_weights[i], neuron.weights)


class TestBioNet:
    def _build_default_net(self) -> BioNet:
        config = BioNetConfig(
            input_dim=2,
            layers=[
                LayerConfig(neurons=[NeuronConfig("BioNeuron", count=3)]),
                LayerConfig(neurons=[NeuronConfig("BioNeuron", count=3)]),
            ],
        )
        return BioNet(config)

    def test_network_forward(self):
        """測試動態網路前向傳播"""
        net = self._build_default_net()
        inputs = [0.5, 0.8]
        activations = net.forward(inputs)

        assert len(activations) == 2
        assert all(len(layer_out) == 3 for layer_out in activations)
        assert all(0.0 <= out <= 1.0 for layer_out in activations for out in layer_out)

    def test_network_learning(self):
        """測試動態網路學習流程"""
        net = self._build_default_net()
        inputs = [0.6, 0.4]
        activations = net.forward(inputs)

        net.learn(inputs, activations)

        # 重新前向傳播應能取得相同維度的輸出
        new_outputs = net.forward(inputs)
        assert [len(layer) for layer in new_outputs] == [3, 3]

    def test_mixed_neuron_learning(self):
        """同層混合 BioNeuron 與 ImprovedBioNeuron 時仍可學習"""
        config = BioNetConfig(
            input_dim=2,
            layers=[
                LayerConfig(
                    neurons=[
                        NeuronConfig("BioNeuron", params={"seed": 1, "learning_rate": 0.2}),
                        NeuronConfig(
                            "ImprovedBioNeuron",
                            params={"seed": 2, "adaptive_threshold": True, "learning_rate": 0.2},
                        ),
                    ]
                )
            ],
        )
        net = BioNet(config)
        inputs = [0.3, 0.7]
        before_weights = [neuron.weights.copy() for neuron in net.layers[0]]

        target_activations = [[0.9, 0.7]]
        net.learn(inputs, target_activations)

        after_weights = [neuron.weights.copy() for neuron in net.layers[0]]
        assert any(not np.array_equal(before, after) for before, after in zip(before_weights, after_weights))

    def test_arbitrary_topology_forward(self):
        """任意拓樸設定能正確執行前向傳播"""
        config = BioNetConfig(
            input_dim=3,
            layers=[
                LayerConfig(
                    neurons=[
                        NeuronConfig("BioNeuron", count=2),
                        NeuronConfig("ImprovedBioNeuron", params={"adaptive_threshold": True}),
                    ]
                ),
                LayerConfig(neurons=[NeuronConfig("BioNeuron", count=4)]),
                LayerConfig(
                    neurons=[
                        NeuronConfig("ImprovedBioNeuron", params={"adaptive_threshold": True}),
                        NeuronConfig("BioNeuron"),
                    ]
                ),
            ],
        )
        net = BioNet(config)
        outputs = net.forward([0.1, 0.2, 0.3])

        assert [len(layer) for layer in outputs] == net.layer_sizes