
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioneuronai.core import BioNeuron, BioLayer, BioNet, NetworkBuilder



class TestBioNeuron:
    def test_initialization(self):
        """測試神經元初始化"""
        neuron = BioNeuron(num_inputs=3, threshold=0.5, seed=42)
        assert neuron.num_inputs == 3
        assert neuron.threshold == 0.5
        assert len(neuron.weights) == 3
        assert len(neuron.input_memory) == 0
        assert isinstance(neuron, BaseNeuron)

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

    def test_public_learn_method(self):
        """測試統一 learn 介面"""

        neuron = BioNeuron(num_inputs=2, learning_rate=0.05, seed=21)
        inputs = [0.9, 0.1]

        # 初次學習會自動前向傳播
        output = neuron.learn(inputs)
        assert 0.0 <= output <= 1.0

        # 使用指定目標再次學習 (不應觸發例外)
        supervised_output = neuron.learn(inputs, target=0.75)
        assert supervised_output == 0.75

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

    def test_save_and_load_roundtrip(self, tmp_path):
        """序列化後應能完整還原神經元狀態"""
        neuron = BioNeuron(
            num_inputs=2,
            threshold=0.55,
            learning_rate=0.08,
            seed=7,
            online_window=4,
            stability_coefficient=0.12,
        )

        # 進行數次在線學習
        samples = [[1.0, 0.5], [0.2, 0.9], [0.7, 0.3]]
        for sample in samples:
            neuron.online_learn(sample)

        state_path = tmp_path / "neuron_state.npz"
        neuron.save_state(state_path)

        restored = BioNeuron.load_state(state_path)
        assert restored.num_inputs == neuron.num_inputs
        assert restored.threshold == pytest.approx(neuron.threshold)
        assert np.allclose(restored.weights, neuron.weights)
        assert restored.online_window == neuron.online_window
        assert np.allclose(restored.baseline_weights, neuron.baseline_weights)
        assert len(restored.input_memory) == len(neuron.input_memory)
        for a, b in zip(restored.input_memory, neuron.input_memory):
            np.testing.assert_array_almost_equal(a, b)

    def test_online_learning_stability(self):
        """在線學習模式應限制權重劇烈漂移"""
        neuron = BioNeuron(
            num_inputs=2,
            learning_rate=0.3,
            seed=1,
            online_window=3,
            stability_coefficient=0.2,
        )
        # 強化某一模式
        for _ in range(10):
            neuron.online_learn([1.0, 1.0], target=1.0)
        learned_weights = neuron.weights.copy()

        # 切換到截然不同的模式
        for _ in range(30):
            neuron.online_learn([0.0, 0.0], target=0.0)

        assert np.all(neuron.weights <= 1.0)
        # 權重仍維持在初始學得值的合理範圍
        assert np.all(neuron.weights >= learned_weights * 0.3)


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
        final_out, layer_outputs = net.forward(inputs)

        assert len(final_out) == 3
        assert len(layer_outputs) == 2
        flattened = [value for layer in layer_outputs for value in layer]
        assert all(0.0 <= out <= 1.0 for out in final_out + flattened)

    def test_network_learning(self):
        """測試網路學習"""
        net = BioNet()
        inputs = [0.6, 0.4]

        # 執行學習
        net.learn(inputs)

        # 至少網路應該能正常運行

        final_out, layer_outputs = net.forward(inputs)
        assert len(final_out) == 3
        assert len(layer_outputs) == 2

    def test_custom_topology_from_dict(self):
        builder = NetworkBuilder()
        config = {
            "input_dim": 2,
            "layers": [
                {"size": 4, "params": {"threshold": 0.3}},
                {"size": 2, "params": {"threshold": 0.9}},
            ],
        }
        net = BioNet(config=config, builder=builder)

        final_out, layer_outputs = net.forward([0.2, 0.7])
        assert len(layer_outputs) == 2
        assert len(layer_outputs[0]) == 4
        assert len(final_out) == 2

    def test_load_from_json(self, tmp_path: Path):
        config = {
            "input_dim": 3,
            "layers": [
                {"size": 5},
                {"size": 1, "params": {"threshold": 0.4}},
            ],
        }
        json_path = tmp_path / "net.json"
        json_path.write_text(json.dumps(config), encoding="utf-8")

        net = BioNet(config=json_path)
        final_out, layer_outputs = net.forward([0.1, 0.2, 0.3])

        assert len(layer_outputs) == 2
        assert len(layer_outputs[0]) == 5
        assert len(final_out) == 1

    def test_mixed_neuron_types(self):
        class ScalingNeuron(BioNeuron):
            def __init__(self, *, scale: float = 0.5, **kwargs):
                super().__init__(**kwargs)
                self.scale = scale

            def forward(self, inputs):  # type: ignore[override]
                base = super().forward(inputs)
                return min(1.0, base * self.scale)

        builder = NetworkBuilder({"ScalingNeuron": ScalingNeuron})
        config = {
            "input_dim": 2,
            "layers": [
                {"size": 2, "neuron_type": "ScalingNeuron", "params": {"scale": 0.8}},
                {"size": 3},
            ],
        }

        net = BioNet(config=config, builder=builder)
        final_out, layer_outputs = net.forward([0.9, 0.1])

        assert len(layer_outputs) == 2
        assert len(layer_outputs[0]) == 2
        assert len(final_out) == 3
        assert any(out < 1.0 for out in layer_outputs[0])

        l2_out, l1_out = net.forward(inputs)
        assert len(l2_out) == 3
        assert len(l1_out) == 3



    def test_network_state_roundtrip(self, tmp_path):
        """網路狀態序列化往返"""
        net = BioNet()
        net.configure_online_learning(window_size=4, stability_coefficient=0.1)
        patterns = [[0.1, 0.9], [0.8, 0.2], [0.5, 0.5]]
        for pattern in patterns:
            net.learn(pattern)

        state_file = tmp_path / "net_state.npz"
        net.save_state(state_file)

        restored = BioNet.load_state(state_file)
        for layer_original, layer_restored in zip(
            (net.layer1, net.layer2), (restored.layer1, restored.layer2)
        ):
            for neuron_orig, neuron_restored in zip(
                layer_original.neurons, layer_restored.neurons
            ):
                np.testing.assert_array_almost_equal(
                    neuron_orig.weights, neuron_restored.weights
                )
                assert neuron_orig.threshold == pytest.approx(
                    neuron_restored.threshold
                )
                assert neuron_orig.online_window == neuron_restored.online_window
                np.testing.assert_array_almost_equal(
                    neuron_orig.baseline_weights, neuron_restored.baseline_weights
                )


