import asyncio
import random
from typing import List

import numpy as np
import pytest

from bioneuronai.base import BaseBioNeuron
from bioneuronai.checkpoint import CheckpointManager
from bioneuronai.core import BioLayer, BioNet, BioNeuron


def test_neuron_serialization_roundtrip(tmp_path):
    neuron = BioNeuron(num_inputs=3, threshold=0.6, learning_rate=0.05, memory_len=4, seed=1)
    sample = [0.2, 0.5, 0.1]
    neuron.forward(sample)
    neuron.hebbian_learn(sample, 0.9)

    serialized = neuron.to_dict()
    assert serialized["state"]["config"]["num_inputs"] == 3
    assert "weights" in serialized["state"]

    path = tmp_path / "neuron.json"
    neuron.save(path)
    loaded = BaseBioNeuron.load(path)

    assert isinstance(loaded, BioNeuron)
    np.testing.assert_allclose(loaded.weights, neuron.weights)
    assert len(loaded.input_memory) == len(neuron.input_memory)
    assert pytest.approx(loaded.last_statistics["threshold"], rel=1e-6) == neuron.threshold


def test_checkpoint_snapshot_and_rollback():
    net = BioNet()
    manager = CheckpointManager(net, history_limit=3)

    for _ in range(5):
        net.learn([0.3, 0.7])

    snapshot = manager.snapshot()
    previous_weight = np.array(snapshot["layers"][0]["neurons"][0]["state"]["weights"], dtype=np.float32)

    net.layer1.neurons[0].weights += 0.5
    manager.rollback(1)

    np.testing.assert_allclose(net.layer1.neurons[0].weights, previous_weight)


def test_async_save(tmp_path):
    net = BioNet()
    manager = CheckpointManager(net)
    state = manager.snapshot()
    path = tmp_path / "checkpoint.json"

    asyncio.run(manager.save_async(path, state))

    assert path.exists()
    loaded_state = manager.load(path, push_history=False)
    assert loaded_state["layers"]


def test_continuous_learning_stability():
    net = BioNet()
    manager = CheckpointManager(net, history_limit=2)
    replay_buffer = []
    rng = random.Random(0)

    def sample() -> List[float]:
        base = rng.choice([[0.2, 0.8], [0.6, 0.4], [0.9, 0.1]])
        noise = [rng.uniform(-0.05, 0.05) for _ in base]
        return [min(1.0, max(0.0, b + n)) for b, n in zip(base, noise)]

    for step in range(1, 121):
        current = sample()
        net.learn(current)
        replay_buffer.append(current)
        if len(replay_buffer) > 12:
            replay_buffer.pop(0)

        if step % 20 == 0:
            for replay in replay_buffer:
                net.learn(replay)
            manager.snapshot()

    for layer in net.get_layers():
        for neuron in layer.neurons:
            assert np.all(np.isfinite(neuron.weights))
            assert len(neuron.input_memory) <= neuron.memory_len

    # mutate network and ensure rollback restores stable state
    net.layer2.neurons[0].weights += 1.5
    manager.rollback(1)

    last_snapshot = manager.history[-1]
    expected_weights = np.array(last_snapshot["layers"][1]["neurons"][0]["state"]["weights"], dtype=np.float32)
    np.testing.assert_allclose(net.layer2.neurons[0].weights, expected_weights)


def test_network_save_and_load_roundtrip(tmp_path):
    net = BioNet()
    for _ in range(3):
        net.learn([0.4, 0.6])

    path = tmp_path / "network.json"
    saved_state = net.save(path)

    assert path.exists()
    restored = BioNet.load(path)

    assert isinstance(restored, BioNet)
    original_layer = BioLayer.from_dict(saved_state["layers"][0])
    np.testing.assert_allclose(
        restored.layer1.neurons[0].weights,
        original_layer.neurons[0].weights,
    )



def test_network_load_state_trims_extra_layers():
    net = BioNet()
    baseline_state = net.to_dict()

    # Manually attach an extra layer to ensure get_layers discovers it.
    net.layer3 = BioLayer(2, 3)
    assert len(net.get_layers()) == 3

    net.load_state(baseline_state)
    layers_after = net.get_layers()

    assert len(layers_after) == len(baseline_state["layers"])
    assert not hasattr(net, "layer3")

