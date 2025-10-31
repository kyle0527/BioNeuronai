from typing import Sequence

import numpy as np

from bioneuronai.core import BioNeuron, BioLayer, BioNet
from bioneuronai.improved_core import ImprovedBioNeuron


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
        neuron.learn(inputs, output)
        
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
    def test_network_forward(self):
        """測試網路前向傳播"""
        net = BioNet()
        inputs = [0.5, 0.8]
        l2_out, l1_out = net.forward(inputs)
        
        assert len(l2_out) == 3
        assert len(l1_out) == 3
        assert all(0.0 <= out <= 1.0 for out in l2_out + l1_out)

    def test_network_learning(self):
        """測試網路學習"""
        net = BioNet()
        inputs = [0.6, 0.4]

        # 執行學習
        net.learn(inputs)

        # 至少網路應該能正常運行
        l2_out, l1_out = net.forward(inputs)
        assert len(l2_out) == 3
        assert len(l1_out) == 3


class TestSharedNeuronAPI:
    def test_bioneuron_learn_matches_expected(self):
        neuron = BioNeuron(num_inputs=2, learning_rate=0.2, seed=7)
        inputs: Sequence[float] = [0.5, 0.25]
        neuron.forward(inputs)
        baseline = neuron.weights.copy()

        neuron.learn(inputs, 1.0)

        expected = baseline + neuron.learning_rate * np.asarray(inputs, dtype=np.float32)
        expected = np.clip(expected, 0.0, 1.0)
        np.testing.assert_allclose(neuron.weights, expected)

    def test_improved_neuron_unsupervised_alignment(self):
        neuron_api = ImprovedBioNeuron(num_inputs=2, learning_rate=0.05, seed=21)
        neuron_reference = ImprovedBioNeuron(num_inputs=2, learning_rate=0.05, seed=21)
        inputs: Sequence[float] = [0.3, 0.6]

        neuron_api.forward(inputs)
        neuron_reference.forward(inputs)

        neuron_api.learn(inputs, 0.0, enhanced=False)

        current_output = neuron_reference.forward(inputs)
        delta = neuron_reference.learning_rate * np.asarray(inputs, dtype=np.float32) * current_output
        manual = neuron_reference.weights + delta
        manual = manual - neuron_reference.learning_config.weight_decay * neuron_reference.weights
        manual = np.clip(manual, 0.0, 2.0)

        np.testing.assert_allclose(neuron_api.weights, manual)

    def test_improved_neuron_enhanced_alignment(self):
        neuron_api = ImprovedBioNeuron(num_inputs=2, learning_rate=0.05, seed=11)
        neuron_reference = ImprovedBioNeuron(num_inputs=2, learning_rate=0.05, seed=11)
        inputs: Sequence[float] = [0.4, 0.2]
        target = 0.9

        neuron_api.forward(inputs)
        neuron_reference.forward(inputs)

        neuron_api.learn(inputs, target, enhanced=True)

        current_output = neuron_reference.forward(inputs)
        error = target - current_output
        delta = neuron_reference.learning_rate * error * np.asarray(inputs, dtype=np.float32) * (target + 0.1)
        manual = neuron_reference.weights + delta
        manual = manual - neuron_reference.learning_config.weight_decay * neuron_reference.weights
        manual = np.clip(manual, 0.0, 2.0)

        np.testing.assert_allclose(neuron_api.weights, manual)
