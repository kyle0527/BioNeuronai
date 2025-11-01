import time

import numpy as np
import pytest

from bioneuronai.core import BioLayer
from bioneuronai.improved_core import CuriosityDrivenNet


def _synchronize_layer_weights(target: BioLayer, weights: np.ndarray) -> None:
    target._weight_matrix[:, :] = weights  # type: ignore[attr-defined]
    target._bind_weight_matrix()  # type: ignore[attr-defined]


def _synchronize_curiosity_weights(target: CuriosityDrivenNet, weights: np.ndarray) -> None:
    target._weight_matrix[:, :] = weights  # type: ignore[attr-defined]
    target._bind_weight_matrix()  # type: ignore[attr-defined]


@pytest.mark.parametrize("n_neurons,input_dim", [(32, 16), (16, 8)])
def test_biolayer_vectorized_matches_python(n_neurons: int, input_dim: int) -> None:
    rng = np.random.default_rng(42)
    shared_weights = rng.random((n_neurons, input_dim), dtype=np.float32)

    layer_vec = BioLayer(n_neurons=n_neurons, input_dim=input_dim, use_vectorized=True)
    layer_py = BioLayer(n_neurons=n_neurons, input_dim=input_dim, use_vectorized=False)

    _synchronize_layer_weights(layer_vec, shared_weights)
    _synchronize_layer_weights(layer_py, shared_weights)

    sample = rng.random(input_dim, dtype=np.float32)
    vec_outputs = layer_vec.forward(sample, use_vectorized=True)
    py_outputs = layer_py.forward(sample, use_vectorized=False)

    assert np.allclose(vec_outputs, py_outputs, atol=1e-6)

    batch_inputs = rng.random((32, input_dim), dtype=np.float32)
    batch_outputs = rng.random((32, n_neurons), dtype=np.float32)

    layer_vec.learn(batch_inputs, batch_outputs, use_vectorized=True)
    layer_py.learn(batch_inputs, batch_outputs, use_vectorized=False)

    assert np.allclose(layer_vec._weight_matrix, layer_py._weight_matrix, atol=1e-6)  # type: ignore[attr-defined]


def test_biolayer_vectorized_benchmark() -> None:
    rng = np.random.default_rng(123)
    n_neurons, input_dim = 64, 32
    inputs = rng.random((64, input_dim), dtype=np.float32)
    outputs = rng.random((64, n_neurons), dtype=np.float32)

    layer_vec = BioLayer(n_neurons=n_neurons, input_dim=input_dim, use_vectorized=True)
    layer_py = BioLayer(n_neurons=n_neurons, input_dim=input_dim, use_vectorized=False)
    shared_weights = rng.random((n_neurons, input_dim), dtype=np.float32)
    _synchronize_layer_weights(layer_vec, shared_weights)
    _synchronize_layer_weights(layer_py, shared_weights)

    def measure_forward(layer: BioLayer, use_vectorized: bool) -> float:
        start = time.perf_counter()
        for sample in inputs:
            layer.forward(sample, use_vectorized=use_vectorized)
        return time.perf_counter() - start

    def measure_learn(layer: BioLayer, use_vectorized: bool) -> float:
        start = time.perf_counter()
        for _ in range(5):
            layer.learn(inputs, outputs, use_vectorized=use_vectorized)
        return time.perf_counter() - start

    vec_forward = measure_forward(layer_vec, True)
    py_forward = measure_forward(layer_py, False)

    vec_learn = measure_learn(layer_vec, True)
    py_learn = measure_learn(layer_py, False)

    assert vec_forward <= py_forward * 1.5
    assert vec_learn <= py_learn * 1.5


@pytest.mark.parametrize("hidden_dim,input_dim", [(6, 4), (4, 3)])
def test_curiosity_net_vectorized_matches_python(hidden_dim: int, input_dim: int) -> None:
    rng = np.random.default_rng(7)
    shared_weights = rng.random((hidden_dim, input_dim), dtype=np.float32)

    net_vec = CuriosityDrivenNet(input_dim=input_dim, hidden_dim=hidden_dim, use_vectorized=True)
    net_py = CuriosityDrivenNet(input_dim=input_dim, hidden_dim=hidden_dim, use_vectorized=False)

    _synchronize_curiosity_weights(net_vec, shared_weights)
    _synchronize_curiosity_weights(net_py, shared_weights)

    sample = rng.random(input_dim, dtype=np.float32)
    vec_outputs, vec_novelties = net_vec.forward(sample, use_vectorized=True)
    py_outputs, py_novelties = net_py.forward(sample, use_vectorized=False)

    assert np.allclose(vec_outputs, py_outputs, atol=1e-6)
    assert np.allclose(vec_novelties, py_novelties, atol=1e-6)

    net_vec = CuriosityDrivenNet(input_dim=input_dim, hidden_dim=hidden_dim, use_vectorized=True)
    net_py = CuriosityDrivenNet(input_dim=input_dim, hidden_dim=hidden_dim, use_vectorized=False)
    _synchronize_curiosity_weights(net_vec, shared_weights)
    _synchronize_curiosity_weights(net_py, shared_weights)
    net_vec.curiosity_threshold = 0.0
    net_py.curiosity_threshold = 0.0

    curiosity_vec = net_vec.curious_learn(sample, use_vectorized=True)
    curiosity_py = net_py.curious_learn(sample, use_vectorized=False)

    assert np.isclose(curiosity_vec, curiosity_py, atol=1e-6)
    assert np.allclose(net_vec._weight_matrix, net_py._weight_matrix, atol=1e-6)  # type: ignore[attr-defined]


def test_curiosity_net_vectorized_benchmark() -> None:
    rng = np.random.default_rng(11)
    hidden_dim, input_dim = 8, 4
    inputs = rng.random((48, input_dim), dtype=np.float32)

    net_vec = CuriosityDrivenNet(input_dim=input_dim, hidden_dim=hidden_dim, use_vectorized=True)
    net_py = CuriosityDrivenNet(input_dim=input_dim, hidden_dim=hidden_dim, use_vectorized=False)
    shared_weights = rng.random((hidden_dim, input_dim), dtype=np.float32)
    _synchronize_curiosity_weights(net_vec, shared_weights)
    _synchronize_curiosity_weights(net_py, shared_weights)
    net_vec.curiosity_threshold = 0.0
    net_py.curiosity_threshold = 0.0

    def measure_learn(net: CuriosityDrivenNet, use_vectorized: bool) -> float:
        start = time.perf_counter()
        for sample in inputs:
            net.curious_learn(sample, use_vectorized=use_vectorized)
        return time.perf_counter() - start

    vec_time = measure_learn(net_vec, True)
    py_time = measure_learn(net_py, False)

    assert vec_time <= py_time * 1.8
