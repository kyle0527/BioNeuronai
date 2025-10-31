import pathlib
import sys

import numpy as np

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bioneuronai.improved_core import CuriositDrivenNet
from examples import rl_curiosity_demo


def _make_alternating_inputs(dim: int, steps: int) -> list[list[float]]:
    base = np.linspace(0.0, 1.0, dim, dtype=np.float32)
    alternating = []
    for idx in range(steps):
        if idx % 2 == 0:
            alternating.append((base + idx * 0.01).tolist())
        else:
            alternating.append(((1.0 - base) + idx * 0.01).tolist())
    return alternating


def test_curiosity_transform_custom():
    net = CuriositDrivenNet(input_dim=3, hidden_dim=4)
    net.curiosity_threshold = 0.0

    def transform(novelties: list[float]) -> float:
        return float(np.max(novelties) * 2.0)

    net.set_curiosity_transform(transform)

    inputs = _make_alternating_inputs(3, 5)
    scores = net.curious_learn_batch(inputs)

    assert len(scores) == len(inputs)
    assert all(score >= 0.0 for score in scores)
    assert any(score > 0.0 for score in scores), "自訂轉換應放大新穎性"


class _MockSpace:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape

    def sample(self):
        return np.zeros(self.shape, dtype=np.float32)


class _MockEnv:
    observation_space = _MockSpace((4,))
    action_space = _MockSpace((1,))

    def __init__(self) -> None:
        self._step_count = 0

    def reset(self):
        self._step_count = 0
        return np.zeros(self.observation_space.shape, dtype=np.float32), {}

    def step(self, _action):
        self._step_count += 1
        obs = np.ones(self.observation_space.shape, dtype=np.float32) * self._step_count
        reward = 1.0
        terminated = self._step_count >= 3
        truncated = False
        info = {}
        return obs, reward, terminated, truncated, info

    def close(self):
        pass


def test_rl_curiosity_demo_smoke():
    metrics = rl_curiosity_demo.run_curiosity_demo(
        env_id="Mock-v0",
        episodes=2,
        max_steps=4,
        intrinsic_scale=0.1,
        env_factory=_MockEnv,
        plot=False,
    )

    assert len(metrics.episode_returns) == 2
    assert metrics.curiosity_history, "應記錄好奇心歷史"
    moving_avg = metrics.moving_average_curiosity(window=2)
    assert len(moving_avg) == len(metrics.curiosity_history), "移動平均長度應與歷史一致"
