import numpy as np
import pytest

from bioneuronai.core import BioLayer
from bioneuronai.network_builder import NetworkBuilder
from bioneuronai.neurons import AntiHebbNeuron, LIFNeuron


class TestLIFNeuron:
    def test_spike_and_learning(self):
        neuron = LIFNeuron(
            num_inputs=2,
            threshold=0.3,
            learning_rate=0.05,
            leak=0.0,
            refractory_period=1,
            seed=0,
        )
        neuron.weights = np.array([0.5, 0.5], dtype=np.float32)
        output = neuron.forward([1.0, 1.0])
        assert output == 1.0

        before = neuron.weights.copy()
        neuron.learn([1.0, 1.0])
        assert np.all(neuron.weights > before)

    def test_novelty_score_changes(self):
        neuron = LIFNeuron(num_inputs=2, threshold=0.5, leak=0.1, seed=1)
        neuron.weights = np.array([0.6, 0.2], dtype=np.float32)
        neuron.forward([0.2, 0.2])
        neuron.forward([0.2, 0.2])
        baseline = neuron.novelty_score()
        neuron.forward([0.9, 0.1])
        assert neuron.novelty_score() > baseline


class TestAntiHebbNeuron:
    def test_weights_decrease_for_correlated_activity(self):
        neuron = AntiHebbNeuron(num_inputs=2, threshold=0.3, learning_rate=0.1, seed=2)
        neuron.weights = np.array([0.9, 0.9], dtype=np.float32)
        neuron.forward([1.0, 1.0])
        before = neuron.weights.copy()
        neuron.learn([1.0, 1.0])
        assert np.all(neuron.weights < before)

    def test_novelty_considers_weight_variance(self):
        neuron = AntiHebbNeuron(num_inputs=2, seed=3)
        neuron.weights = np.array([0.1, 0.9], dtype=np.float32)
        neuron.forward([0.2, 0.3])
        high_variance = neuron.novelty_score()
        neuron.weights = np.array([0.1, 0.1], dtype=np.float32)
        neuron.forward([0.2, 0.4])
        low_variance = neuron.novelty_score()
        assert high_variance > low_variance


class TestNetworkBuilder:
    def test_build_and_learn(self):
        builder = NetworkBuilder()
        config = {
            "input_dim": 2,
            "layers": [
                {"type": "lif", "count": 2, "params": {"threshold": 0.4, "leak": 0.0}},
                {"type": "anti_hebb", "count": 1, "params": {"threshold": 0.2}},
            ],
        }
        network = builder.build_from_config(config)
        final, activations = network.forward([1.0, 0.5])
        assert len(activations) == 2
        assert len(final) == 1

        first_layer_neuron = network.layers[0].neurons[0]
        before = first_layer_neuron.weights.copy()
        network.learn([1.0, 0.5])
        assert not np.allclose(before, first_layer_neuron.weights)

    def test_register_custom_type(self):
        builder = NetworkBuilder()

        class DummyNeuron(LIFNeuron):
            pass

        builder.register_neuron_type("dummy", DummyNeuron)
        assert "dummy" in builder.get_registered_types()

    def test_learn_with_explicit_targets(self):
        builder = NetworkBuilder()
        config = {
            "input_dim": 2,
            "layers": [
                {"type": "bio", "count": 2},
                {"type": "anti_hebb", "count": 1},
            ],
        }
        network = builder.build_from_config(config)
        for neuron in network.layers[0].neurons:
            neuron.weights = np.array([0.9, 0.9], dtype=np.float32)
        network.layers[1].neurons[0].weights = np.array([0.5, 0.5], dtype=np.float32)
        # Establish state and ensure memories populated
        network.forward([0.3, 0.7])

        first_before = network.layers[0].neurons[0].weights.copy()
        second_before = network.layers[1].neurons[0].weights.copy()

        targets = [[0.2, 0.9], [0.1]]
        network.learn([0.3, 0.7], targets=targets)

        assert not np.allclose(first_before, network.layers[0].neurons[0].weights)
        assert not np.allclose(second_before, network.layers[1].neurons[0].weights)

    def test_learn_validates_target_shapes(self):
        builder = NetworkBuilder()
        config = {
            "input_dim": 2,
            "layers": [{"type": "bio", "count": 2}],
        }
        network = builder.build_from_config(config)
        network.forward([0.1, 0.2])

        with pytest.raises(ValueError):
            network.learn([0.1, 0.2], targets=[[0.1]])

        with pytest.raises(ValueError):
            network.learn([0.1, 0.2], targets=[[0.1, 0.2], [0.3]])


class TestBioLayer:
    def test_learn_validates_output_length(self):
        layer = BioLayer(n_neurons=2, input_dim=2)
        layer.forward([0.5, 0.5])
        with pytest.raises(ValueError):
            layer.learn([0.5, 0.5], outputs=[0.1])
