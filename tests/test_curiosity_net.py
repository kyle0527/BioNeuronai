import numpy as np
import pytest

from bioneuronai.improved_core import CuriositDrivenNet


def test_forward_returns_reward_and_level():
    net = CuriositDrivenNet(
        input_dim=2,
        hidden_dim=2,
        curiosity_threshold=0.1,
        reward_scale=2.0,
        reward_clip=(0.0, 5.0),
    )

    outputs, novelties, curiosity_level, curiosity_reward = net.forward([0.2, 0.4])

    assert len(outputs) == 2
    assert len(novelties) == 2
    assert isinstance(curiosity_reward, float)
    assert curiosity_level == pytest.approx(np.mean(novelties))
    assert 0.0 <= curiosity_reward <= 5.0


def test_curiosity_learning_threshold_and_scaling():
    net = CuriositDrivenNet(input_dim=1, hidden_dim=1, curiosity_threshold=0.9, reward_scale=1.0)
    neuron = net.neurons[0]
    initial_weights = neuron.weights.copy()

    curiosity_level, curiosity_reward = net.curious_learn([0.0])
    np.testing.assert_allclose(neuron.weights, initial_weights)
    assert curiosity_reward == pytest.approx(0.0)
    assert curiosity_level <= 1.0

    net.configure_curiosity(threshold=0.0, reward_scale=2.5)
    curiosity_level, curiosity_reward = net.curious_learn([1.0])
    assert curiosity_level >= 0.0
    assert curiosity_reward >= 0.0
    assert not np.array_equal(neuron.weights, initial_weights)
    assert curiosity_reward <= 2.5


