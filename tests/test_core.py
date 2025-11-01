import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from bioneuronai import BaseBioNeuron, ImprovedBioNeuron
from bioneuronai.core import BioNeuron, BioLayer, BioNet
from bioneuronai.improved_core import CuriositDrivenNet
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

import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioneuronai.core import BioNeuron, BioLayer, BioNet, NetworkBuilder



class TestBioNeuron:
    def test_initialization(self):
        neuron = BioNeuron(num_inputs=3, threshold=0.5, seed=42)
        assert neuron.num_inputs == 3
        assert neuron.threshold == 0.5
        assert len(neuron.weights) == 3
        assert len(neuron.input_memory) == 0
        assert isinstance(neuron, BaseNeuron)

    def test_forward_pass(self):
        neuron = BioNeuron(num_inputs=2, threshold=0.5, seed=42)
        inputs = [0.8, 0.6]
        output = neuron.forward(inputs)

        assert 0.0 <= output <= 1.0
        assert len(neuron.input_memory) == 1
        np.testing.assert_array_almost_equal(
            neuron.input_memory[0], np.asarray(inputs, dtype=np.float32), decimal=6
        )

    def test_forward_batch_matches_single(self):
        neuron = BioNeuron(num_inputs=3, seed=1)
        batch = np.array(
            [
                [0.2, 0.4, 0.6],
                [0.1, 0.3, 0.5],
                [0.9, 0.8, 0.1],
            ],
            dtype=np.float32,
        )
        outputs_single = [neuron.forward(row) for row in batch]
        neuron.reset()
        outputs_batch = neuron.forward_batch(batch)
        np.testing.assert_allclose(outputs_batch, outputs_single, rtol=1e-5, atol=1e-6)

    def test_memory_limit(self):
        neuron = BioNeuron(num_inputs=2, memory_len=3, seed=42)
        for i in range(5):
            neuron.forward([i, i])

        assert len(neuron.input_memory) == 3
        assert np.isclose(neuron.input_memory[0][0], 2.0)

    def test_hebbian_learning(self):
        neuron = BioNeuron(num_inputs=2, learning_rate=0.1, seed=42)
        initial_weights = neuron.weights.copy()

        inputs = [1.0, 0.5]
        output = 0.8
        neuron.hebbian_learn(inputs, output)

        # 權重應該有所變化
        assert not np.array_equal(initial_weights, neuron.weights)
        assert np.all((0.0 <= neuron.weights) & (neuron.weights <= 1.0))

    def test_batch_learning_updates(self):
        neuron = BioNeuron(num_inputs=2, learning_rate=0.2, seed=0)
        batch_inputs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        outputs = np.array([1.0, 0.5], dtype=np.float32)
        initial_weights = neuron.weights.copy()
        neuron.learn_batch(batch_inputs, outputs=outputs)
        expected_delta = 0.2 * (batch_inputs * outputs[:, None]).mean(axis=0)
        np.testing.assert_allclose(
            neuron.weights,
            np.clip(initial_weights + expected_delta, 0.0, 1.0),
            rtol=1e-5,
            atol=1e-6,
        )

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
        neuron = BioNeuron(num_inputs=2, seed=42)

        # 沒有足夠記憶時
        assert neuron.novelty_score() == 0.0
        neuron.forward([1.0, 1.0])
        neuron.forward([1.0, 1.0])
        novelty_same = neuron.novelty_score()
        neuron.forward([0.0, 0.0])
        novelty_diff = neuron.novelty_score()
        assert novelty_diff > novelty_same

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
        layer = BioLayer(n_neurons=3, input_dim=2)
        outputs = layer.forward([0.5, 0.8])
        assert len(outputs) == 3
        assert all(0.0 <= out <= 1.0 for out in outputs)

    def test_layer_learning(self):
        layer = BioLayer(n_neurons=2, input_dim=2)
        inputs = [0.6, 0.4]
        outputs = [0.8, 0.3]
        initial_weights = [n.weights.copy() for n in layer.neurons]
        layer.learn(inputs, outputs)
        for original, neuron in zip(initial_weights, layer.neurons):
            assert not np.array_equal(original, neuron.weights)


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
        l2_out, l1_out = net.forward(inputs)

        assert len(l2_out) == 3
        assert len(l1_out) == 3
        final_out, layer_outputs = net.forward(inputs)

        assert len(final_out) == 3
        assert len(layer_outputs) == 2
        flattened = [value for layer in layer_outputs for value in layer]
        assert all(0.0 <= out <= 1.0 for out in final_out + flattened)

    def test_network_learning(self):
        """測試動態網路學習流程"""
        net = self._build_default_net()
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


class TestStrategies:
    def test_adaptive_threshold_strategy(self):
        strategy = AdaptiveThresholdStrategy(window=3)
        neuron = BioNeuron(num_inputs=1, threshold=0.5, memory_len=3, seed=0)
        neuron.threshold_strategy = strategy
        neuron.output_memory.extend([0.9, 0.95, 1.0])
        neuron.threshold = 0.5
        strategy.adjust(
            neuron,
            inputs=np.ones((1, 1), dtype=np.float32),
            potentials=np.ones(1, dtype=np.float32),
            outputs=np.ones(1, dtype=np.float32),
        )
        assert neuron.threshold > 0.5

    def test_weight_decay_hebbian_strategy(self):
        strategy = WeightDecayHebbianStrategy(learning_rate=0.2, weight_decay=0.1)
        neuron = BioNeuron(
            num_inputs=2,
            threshold=0.2,
            learning_rate=0.2,
            memory_len=2,
            seed=0,
            learning_strategy=strategy,
        )
        batch_inputs = np.array([[1.0, 1.0], [0.5, 0.5]], dtype=np.float32)
        outputs = np.array([1.0, 0.5], dtype=np.float32)
        initial_weights = neuron.weights.copy()
        neuron.learn_batch(batch_inputs, outputs=outputs)
        manual_delta = 0.2 * (batch_inputs * outputs[:, None]).mean(axis=0)
        expected = np.clip(
            initial_weights + manual_delta - 0.1 * initial_weights,
            0.0,
            2.0,
        )
        np.testing.assert_allclose(neuron.weights, expected, rtol=1e-5, atol=1e-6)


class TestImprovedBioNeuron:
    def test_improved_batch_forward(self):
        neuron = ImprovedBioNeuron(num_inputs=2, adaptive_threshold=True, seed=1)
        batch = np.array([[0.8, 0.2], [0.1, 0.9]], dtype=np.float32)
        outputs_single = [neuron.forward(row) for row in batch]
        neuron.reset_statistics()
        outputs_batch = neuron.forward_batch(batch)
        np.testing.assert_allclose(outputs_batch, outputs_single, rtol=1e-5, atol=1e-6)

    def test_improved_learning_with_target(self):
        neuron = ImprovedBioNeuron(
            num_inputs=2,
            learning_rate=0.2,
            weight_decay=0.05,
            adaptive_threshold=False,
            seed=0,
        )
        initial_weights = neuron.weights.copy()
        neuron.improved_hebbian_learn([1.0, 0.5], target=0.9)
        assert not np.array_equal(initial_weights, neuron.weights)
class TestBaseBioNeuron:
    def test_base_is_abstract(self):
        with pytest.raises(TypeError):
            BaseBioNeuron(num_inputs=2)  # type: ignore[abstract]


class TestImprovedBioNeuron:
    def test_inherits_base_and_memory(self):
        neuron = ImprovedBioNeuron(num_inputs=2, seed=123)
        assert isinstance(neuron, BaseBioNeuron)
        assert neuron.input_memory == []

    def test_unsupervised_hebbian_updates(self):
        neuron = ImprovedBioNeuron(num_inputs=2, learning_rate=0.05, seed=1)
        inputs = [0.4, 0.6]
        neuron.forward(inputs)
        initial_weights = neuron.weights.copy()
        neuron.hebbian_learn(inputs)
        assert not np.array_equal(initial_weights, neuron.weights)
        # 進行無監督學習時，不應額外寫入輸入記憶
        assert len(neuron.input_memory) == 1

    def test_supervised_and_alias_learning(self):
        neuron = ImprovedBioNeuron(num_inputs=2, learning_rate=0.05, seed=2)
        inputs = [0.9, 0.1]
        initial_weights = neuron.weights.copy()
        neuron.hebbian_learn(inputs, target=0.8)
        alias_weights = neuron.weights.copy()
        neuron.improved_hebbian_learn(inputs, target=0.2)
        assert not np.array_equal(initial_weights, alias_weights)
        assert not np.array_equal(alias_weights, neuron.weights)

    def test_output_only_learning_updates_weights(self):
        neuron = ImprovedBioNeuron(num_inputs=2, learning_rate=0.05, seed=5)
        inputs = [0.3, 0.7]
        baseline = neuron.weights.copy()
        neuron.hebbian_learn(inputs, output=0.6)
        assert not np.array_equal(baseline, neuron.weights)

    def test_novelty_score_alias(self):
        neuron = ImprovedBioNeuron(num_inputs=2, seed=10)
        neuron.forward([1.0, 0.0])
        neuron.forward([0.0, 1.0])
        assert 0.0 <= neuron.novelty_score() <= 1.0


class TestCuriosityDrivenNet:
    def test_curious_learning_path(self):
        net = CuriositDrivenNet(input_dim=2, hidden_dim=2)
        inputs = [0.2, 0.7]
        outputs, novelties = net.forward(inputs)
        assert len(outputs) == 2
        assert len(novelties) == 2
        assert all(0.0 <= out <= 1.0 for out in outputs)
        curiosity = net.curious_learn(inputs)
        assert 0.0 <= curiosity <= 1.0

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


