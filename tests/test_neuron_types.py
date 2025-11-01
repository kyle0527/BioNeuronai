import numpy as np
import pytest

from bioneuronai.neuron_types import LIFNeuron, STDPNeuron, NEURON_REGISTRY
from bioneuronai.neuron_types.stdp import PlasticityConfig


def test_lif_spike_and_reset():
    neuron = LIFNeuron(
        num_inputs=1,
        threshold=0.5,
        rest_potential=0.0,
        reset_potential=0.0,
        membrane_time_constant=1.0,
        refractory_period=1.0,
        seed=1,
    )
    neuron.weights[:] = 1.0

    spiked = neuron.step([1.0], dt=1.0)
    assert spiked is True
    assert neuron.state.membrane_potential == pytest.approx(0.0)

    # Refractory period should prevent immediate re-firing
    spiked_again = neuron.step([1.0], dt=0.5)
    assert spiked_again is False
    assert neuron.state.membrane_potential == pytest.approx(0.0)


def test_stdp_weight_updates_are_bounded():
    cfg = PlasticityConfig(lr=0.05, a_plus=0.02, a_minus=0.015, w_min=-0.5, w_max=0.5)
    neuron = STDPNeuron(num_inputs=2, threshold=0.5, membrane_time_constant=5.0, plasticity=cfg)
    neuron.weights[:] = 0.0

    for _ in range(50):
        neuron.step([1.0, 0.0], dt=1.0)

    assert np.all(np.isfinite(neuron.weights))
    assert np.all(neuron.weights <= cfg.w_max + 1e-6)
    assert np.all(neuron.weights >= cfg.w_min - 1e-6)


def test_anti_hebbian_reduces_weights_on_inactive_neuron():
    cfg = PlasticityConfig(lr=0.1, a_plus=0.01, a_minus=0.01, w_min=-1.0, w_max=1.0)
    neuron = STDPNeuron(
        num_inputs=2,
        threshold=10.0,  # prevent spiking
        membrane_time_constant=5.0,
        plasticity=cfg,
    )
    neuron.weights[:] = 0.5

    pre_weight = neuron.weights.copy()
    for _ in range(10):
        neuron.step([1.0, 0.5], dt=1.0)

    assert np.all(neuron.weights < pre_weight)


def test_registry_creates_instances_from_config():
    config = {
        "neurons": [
            {
                "name": "lif_fast",
                "type": "lif",
                "params": {"num_inputs": 1, "threshold": 0.2},
            },
            {
                "name": "plastic",
                "type": "stdp",
                "params": {"num_inputs": 2},
            },
        ]
    }

    created = NEURON_REGISTRY.register_from_config(config)
    assert set(created.keys()) == {"lif_fast", "plastic"}
    assert isinstance(created["lif_fast"], LIFNeuron)
    assert isinstance(created["plastic"], STDPNeuron)
