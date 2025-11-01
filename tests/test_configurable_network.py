import json

import pytest

from bioneuronai.core import BioNet, BioNeuron
from bioneuronai.networks import (
    LayerConfig,
    NetworkConfig,
    build_network,
)


def test_build_arbitrary_depth():
    config = NetworkConfig(
        input_dim=4,
        layers=[
            LayerConfig(size=5, neuron="BioNeuron"),
            LayerConfig(size=4, neuron="BioNeuron"),
            LayerConfig(size=3, neuron="BioNeuron"),
        ],
    )
    network = build_network(config)
    final, layers = network.forward([0.1, 0.2, 0.3, 0.4])
    assert len(layers) == 3
    assert len(final) == 3
    assert all(len(output) == size for output, size in zip(layers, [5, 4, 3]))

    # Learning should run without raising for arbitrary depth
    final_after, _ = network.learn([0.5, 0.5, 0.5, 0.5])
    assert len(final_after) == 3


def test_heterogeneous_neuron_types():
    try:
        from bioneuronai.improved_core import ImprovedBioNeuron
    except ImportError:  # pragma: no cover - optional dependency missing
        pytest.skip("ImprovedBioNeuron not available")

    config = NetworkConfig(
        input_dim=2,
        layers=[
            LayerConfig(size=2, neuron="BioNeuron"),
            LayerConfig(size=2, neuron="ImprovedBioNeuron", parameters={"adaptive_threshold": True}),
        ],
    )
    network = build_network(config)
    _, layers = network.forward([0.6, 0.9])
    assert len(layers) == 2
    assert all(isinstance(neuron, BioNeuron) for neuron in network.layers[0].neurons)
    assert all(isinstance(neuron, ImprovedBioNeuron) for neuron in network.layers[1].neurons)


def test_serialisation_roundtrip():
    original = NetworkConfig(
        input_dim=3,
        layers=[
            LayerConfig(size=3, neuron="BioNeuron", parameters={"threshold": 0.7}),
            LayerConfig(size=2, neuron="BioNeuron", parameters={"learning_rate": 0.05}),
        ],
        metadata={"name": "demo"},
    )
    data = original.to_dict()
    json_blob = json.dumps(data)
    restored = NetworkConfig.from_dict(json.loads(json_blob))
    assert restored.input_dim == original.input_dim
    assert restored.metadata == original.metadata
    assert [layer.to_dict() for layer in restored.layers] == [layer.to_dict() for layer in original.layers]

    # Config should be reusable for BioNet
    net = BioNet(network_config=restored)
    outputs, history = net.forward([0.2, 0.3, 0.4])
    assert len(outputs) == restored.layers[-1].size
    assert len(history) == len(restored.layers)
    assert history[-1] == outputs
    assert net.to_config().to_dict() == restored.to_dict()
