"""使用 CuriositDrivenNet 與 OpenAI Gym 環境示範好奇心驅動探索"""

from __future__ import annotations

import argparse
import dataclasses
import math
from typing import Callable, Iterable, List, Optional, Sequence

import numpy as np

from bioneuronai.improved_core import CuriositDrivenNet

try:  # pragma: no cover - 動態依賴
    import gymnasium as gym  # type: ignore
except ImportError:  # pragma: no cover - 動態依賴
    try:
        import gym  # type: ignore
    except ImportError:  # pragma: no cover - 動態依賴
        gym = None  # type: ignore


GYM_IMPORT_ERROR = (
    "需要安裝 gymnasium 或 gym 以執行 `examples/rl_curiosity_demo.py`，"
    "請參考文檔安裝額外依賴。"
)


def _ensure_gym_available() -> None:
    if gym is None:  # pragma: no cover - 直接錯誤訊息
        raise ImportError(GYM_IMPORT_ERROR)


def _reset_env(env):
    reset_result = env.reset()
    if isinstance(reset_result, tuple) and len(reset_result) == 2:
        observation, _info = reset_result
    else:  # gym 舊版
        observation = reset_result
    return observation


def _step_env(env, action):
    result = env.step(action)
    if isinstance(result, tuple) and len(result) == 5:
        observation, reward, terminated, truncated, info = result
        done = terminated or truncated
    else:  # gym 舊版
        observation, reward, done, info = result
    return observation, float(reward), bool(done), info


def _flatten_observation(observation: Sequence[float] | np.ndarray) -> List[float]:
    arr = np.asarray(observation, dtype=np.float32)
    return arr.reshape(-1).tolist()


def _infer_input_dim(observation_sample) -> int:
    arr = np.asarray(observation_sample, dtype=np.float32)
    return int(arr.reshape(-1).shape[0])


@dataclasses.dataclass
class DemoMetrics:
    episode_returns: List[float]
    episode_intrinsic: List[float]
    curiosity_history: List[float]
    intrinsic_scale: float
    env_id: str

    def moving_average_curiosity(self, window: int = 10) -> List[float]:
        if not self.curiosity_history:
            return []
        padded = [0.0] * max(0, window - 1) + self.curiosity_history
        ma = []
        for idx in range(window - 1, len(padded)):
            segment = padded[idx - window + 1 : idx + 1]
            ma.append(float(np.mean(segment)))
        return ma


def run_curiosity_demo(
    env_id: str = "CartPole-v1",
    episodes: int = 5,
    max_steps: int = 200,
    intrinsic_scale: float = 0.5,
    curiosity_threshold: float = 0.3,
    curiosity_transform: Optional[Callable[[Sequence[float]], float]] = None,
    env_factory: Optional[Callable[[], object]] = None,
    plot: bool = True,
) -> DemoMetrics:
    """執行好奇心驅動探索示範"""

    if env_factory is not None:
        env = env_factory()
    else:
        _ensure_gym_available()
        env = gym.make(env_id)

    try:
        observation = _reset_env(env)
        input_dim = _infer_input_dim(observation)
        net = CuriositDrivenNet(
            input_dim=input_dim,
            hidden_dim=max(4, input_dim),
            curiosity_transform=curiosity_transform,
        )
        net.curiosity_threshold = curiosity_threshold

        curiosity_history: List[float] = []
        episode_returns: List[float] = []
        episode_intrinsic: List[float] = []

        for _episode in range(episodes):
            total_reward = 0.0
            intrinsic_return = 0.0
            steps = 0
            observation = _flatten_observation(observation)

            for _ in range(max_steps):
                action = env.action_space.sample()
                curiosity_level = net.curious_learn(observation)
                curiosity_history.append(curiosity_level)
                intrinsic_return += curiosity_level

                next_observation, reward, done, _info = _step_env(env, action)
                total_reward += float(reward) + intrinsic_scale * curiosity_level
                observation = _flatten_observation(next_observation)
                steps += 1

                if done:
                    break

            episode_returns.append(total_reward)
            if steps > 0:
                episode_intrinsic.append(intrinsic_return / steps)
            else:
                episode_intrinsic.append(0.0)

            observation = _reset_env(env)

        metrics = DemoMetrics(
            episode_returns=episode_returns,
            episode_intrinsic=episode_intrinsic,
            curiosity_history=curiosity_history,
            intrinsic_scale=intrinsic_scale,
            env_id=env_id,
        )

        if plot:
            _maybe_plot_curiosity_curve(metrics)

        _print_summary(metrics)
        return metrics
    finally:
        if hasattr(env, "close"):
            env.close()


def _maybe_plot_curiosity_curve(metrics: DemoMetrics) -> None:
    try:  # pragma: no cover - 可選依賴
        import matplotlib.pyplot as plt
    except ImportError:  # pragma: no cover - 可選依賴
        print("未安裝 matplotlib，跳過曲線繪製。")
        return

    window = min(20, max(1, int(math.sqrt(len(metrics.curiosity_history) or 1))))
    moving_avg = metrics.moving_average_curiosity(window=window) or metrics.curiosity_history

    plt.figure(figsize=(8, 4))
    plt.plot(metrics.curiosity_history, label="Instant Curiosity", alpha=0.4)
    plt.plot(range(window - 1, window - 1 + len(moving_avg)), moving_avg, label=f"Moving Avg (window={window})")
    plt.title(f"Curiosity-driven exploration on {metrics.env_id}")
    plt.xlabel("Step")
    plt.ylabel("Intrinsic curiosity reward")
    plt.legend()
    output_path = "examples/rl_curiosity_demo_curve.png"
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"已將探索曲線儲存至 {output_path}")


def _print_summary(metrics: DemoMetrics) -> None:
    avg_return = float(np.mean(metrics.episode_returns)) if metrics.episode_returns else 0.0
    avg_intrinsic = float(np.mean(metrics.episode_intrinsic)) if metrics.episode_intrinsic else 0.0
    print("=== Curiosity Demo Summary ===")
    print(f"環境: {metrics.env_id}")
    print(f"平均總回報(含內在獎勵): {avg_return:.3f}")
    print(f"平均內在獎勵: {avg_intrinsic:.3f}")
    if metrics.curiosity_history:
        print(f"最大好奇心水位: {max(metrics.curiosity_history):.3f}")


def main(argv: Optional[Iterable[str]] = None) -> DemoMetrics:
    parser = argparse.ArgumentParser(description="Curiosity-driven RL demo")
    parser.add_argument("--env", dest="env_id", default="CartPole-v1", help="要使用的 gym 環境 ID")
    parser.add_argument("--episodes", type=int, default=5, help="演示回合數")
    parser.add_argument("--max-steps", type=int, default=200, help="每回合最多步數")
    parser.add_argument("--intrinsic-scale", type=float, default=0.5, help="內在獎勵加權係數")
    parser.add_argument("--threshold", type=float, default=0.3, help="觸發學習的好奇心水位")
    parser.add_argument("--no-plot", action="store_true", help="禁用探索曲線輸出")

    args = parser.parse_args(list(argv) if argv is not None else None)

    return run_curiosity_demo(
        env_id=args.env_id,
        episodes=args.episodes,
        max_steps=args.max_steps,
        intrinsic_scale=args.intrinsic_scale,
        curiosity_threshold=args.threshold,
        plot=not args.no_plot,
    )


if __name__ == "__main__":  # pragma: no cover - CLI 入口
    main()
