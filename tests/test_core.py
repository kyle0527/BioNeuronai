import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from bioneuronai.core import BioLayer, BioNet, BioNeuron
from bioneuronai.improved_core import ImprovedBioNeuron
from bioneuronai.neurons.base import (
    AdaptiveThresholdStrategy,
    WeightDecayHebbianStrategy,
)


class TestBioNeuron:
    def test_initialization(self):
        neuron = BioNeuron(num_inputs=3, threshold=0.5, seed=42)
        assert neuron.num_inputs == 3
        assert neuron.threshold == 0.5
        assert len(neuron.weights) == 3
        assert len(neuron.input_memory) == 0

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
        neuron.hebbian_learn([1.0, 0.5], 0.8)

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

    def test_novelty_score(self):
        neuron = BioNeuron(num_inputs=2, seed=42)
        assert neuron.novelty_score() == 0.0
        neuron.forward([1.0, 1.0])
        neuron.forward([1.0, 1.0])
        novelty_same = neuron.novelty_score()
        neuron.forward([0.0, 0.0])
        novelty_diff = neuron.novelty_score()
        assert novelty_diff > novelty_same


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
    def test_network_forward(self):
        net = BioNet()
        l2_out, l1_out = net.forward([0.5, 0.8])
        assert len(l2_out) == 3
        assert len(l1_out) == 3
        assert all(0.0 <= out <= 1.0 for out in l2_out + l1_out)

    def test_network_learning(self):
        net = BioNet()
        net.learn([0.6, 0.4])
        l2_out, l1_out = net.forward([0.6, 0.4])
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


