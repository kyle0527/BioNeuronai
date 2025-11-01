#!/usr/bin/env python3


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

import numpy as np

try:
    import gymnasium as gym

except ImportError as exc:  # pragma: no cover - optional dependency
    raise SystemExit(
        "Gymnasium is required for this demo. Install it with `pip install gymnasium`."
    ) from exc

from bioneuronai.curiosity import CuriosityDrivenNet


@dataclass
class EpisodeStats:
    extrinsic: float = 0.0
    intrinsic: float = 0.0

    @property
    def combined(self) -> float:
        return self.extrinsic + self.intrinsic


def run_episode(env: gym.Env, network: CuriosityDrivenNet, max_steps: int) -> EpisodeStats:
    stats = EpisodeStats()
    observation, _ = env.reset()

    for _ in range(max_steps):
        action = env.action_space.sample()
        _, novelties = network.forward(observation)
        intrinsic = network.intrinsic_reward(novelties, gain=network.config.intrinsic_gain)

        observation, reward, terminated, truncated, _ = env.step(action)
        stats.extrinsic += float(reward)
        stats.intrinsic += intrinsic

        # Curiosity gated update encourages exploration in novel regions
        network.curious_learn(observation)

        if terminated or truncated:
            break

    return stats


def main(env_id: str, episodes: int, max_steps: int, hidden_dim: int) -> None:
    env = gym.make(env_id)
    obs_size = int(np.prod(env.observation_space.shape or (1,)))
    curiosity_net = CuriosityDrivenNet(input_dim=obs_size, hidden_dim=hidden_dim, intrinsic_gain=0.5)

    for episode in range(1, episodes + 1):
        stats = run_episode(env, curiosity_net, max_steps)
        print(
            f"Episode {episode:02d}: extrinsic={stats.extrinsic:.2f}, "
            f"intrinsic={stats.intrinsic:.2f}, combined={stats.combined:.2f}"
        )

    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", default="CartPole-v1", help="Gymnasium environment id")
    parser.add_argument("--episodes", type=int, default=5, help="Number of episodes to run")
    parser.add_argument("--max-steps", type=int, default=200, help="Maximum steps per episode")
    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=8,
        help="Number of curiosity neurons driving the intrinsic reward",
    )
    args = parser.parse_args()
    main(args.env, args.episodes, args.max_steps, args.hidden_dim)
except ImportError as exc:
    raise ImportError(
        "本範例需要 gymnasium，請先安裝 `pip install gymnasium`."
    ) from exc

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
except ImportError as exc:
    raise ImportError(
        "本範例需要 stable-baselines3，請先安裝 `pip install stable-baselines3`."
    ) from exc

from bioneuronai.improved_core import CuriositDrivenNet


class CuriosityRewardWrapper(gym.Wrapper):
    """於環境中注入好奇心獎勵."""

    def __init__(
        self,
        env: gym.Env,
        curiosity_net: CuriositDrivenNet,
        curiosity_weight: float = 1.0,
    ) -> None:
        super().__init__(env)
        self.curiosity_net = curiosity_net
        self.curiosity_weight = float(curiosity_weight)

    def step(self, action):  # type: ignore[override]
        observation, reward, terminated, truncated, info = self.env.step(action)
        stats = self.curiosity_net.step(observation, learn=True)

        curiosity_reward = float(stats["curiosity_reward"]) * self.curiosity_weight
        info.update(
            {
                "curiosity_reward": curiosity_reward,
                "curiosity_level": float(stats["curiosity_level"]),
                "extrinsic_reward": float(reward),
            }
        )
        total_reward = float(reward) + curiosity_reward
        return observation, total_reward, terminated, truncated, info

    def reset(self, **kwargs):  # type: ignore[override]
        observation, info = self.env.reset(**kwargs)
        return observation, info


class CuriosityLoggingCallback(BaseCallback):
    """記錄訓練過程的好奇心與外在獎勵曲線."""

    def __init__(self, log_path: Path, verbose: int = 0) -> None:
        super().__init__(verbose)
        self.log_path = log_path
        self.step_curiosity: List[float] = []
        self.step_extrinsic: List[float] = []
        self.episode_summaries: List[dict] = []
        self._episode_curiosity = 0.0
        self._episode_extrinsic = 0.0

    def _on_training_start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _on_step(self) -> bool:
        info = self.locals.get("infos", [{}])[-1]
        curiosity_reward = float(info.get("curiosity_reward", 0.0))
        extrinsic_reward = float(info.get("extrinsic_reward", 0.0))
        done_flags = self.locals.get("dones")

        self.step_curiosity.append(curiosity_reward)
        self.step_extrinsic.append(extrinsic_reward)
        self._episode_curiosity += curiosity_reward
        self._episode_extrinsic += extrinsic_reward

        if done_flags and bool(done_flags[-1]):
            self.episode_summaries.append(
                {
                    "timesteps": self.num_timesteps,
                    "curiosity_reward": self._episode_curiosity,
                    "extrinsic_reward": self._episode_extrinsic,
                }
            )
            self._episode_curiosity = 0.0
            self._episode_extrinsic = 0.0

        return True

    def _on_training_end(self) -> None:
        metrics = {
            "step_curiosity": self.step_curiosity,
            "step_extrinsic": self.step_extrinsic,
            "episode_summaries": self.episode_summaries,
        }
        self.log_path.write_text(json.dumps(metrics, indent=2))
        if self.verbose:
            print(f"好奇心訓練紀錄已儲存至 {self.log_path}")


def plot_metrics(metrics_path: Path, figure_path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("未安裝 matplotlib，略過曲線繪製。")
        return

    data = json.loads(metrics_path.read_text())
    curiosity = np.array(data["step_curiosity"], dtype=float)
    extrinsic = np.array(data["step_extrinsic"], dtype=float)

    plt.figure(figsize=(8, 4))
    plt.plot(curiosity, label="Curiosity Reward")
    plt.plot(extrinsic, label="Extrinsic Reward", alpha=0.7)
    plt.xlabel("Step")
    plt.ylabel("Reward")
    plt.title("Curiosity vs. Extrinsic Reward")
    plt.legend()
    plt.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(figure_path)
    plt.close()
    print(f"獎勵曲線圖已輸出至 {figure_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timesteps",
        type=int,
        default=5000,
        help="訓練總步數",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("examples/artifacts"),
        help="儲存指標的資料夾",
    )
    parser.add_argument(
        "--curiosity-weight",
        type=float,
        default=1.0,
        help="好奇心獎勵佔總獎勵的權重",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    env = gym.make("CartPole-v1")
    observation_size = int(np.prod(env.observation_space.shape))
    curiosity_net = CuriositDrivenNet(
        input_dim=observation_size,
        hidden_dim=8,
        curiosity_threshold=0.05,
        reward_scale=2.0,
        reward_clip=(0.0, 1.0),
    )

    wrapped_env = CuriosityRewardWrapper(env, curiosity_net, args.curiosity_weight)
    model = PPO("MlpPolicy", wrapped_env, verbose=0)

    log_path = args.log_dir / "rl_curiosity_metrics.json"
    callback = CuriosityLoggingCallback(log_path, verbose=1)
    model.learn(total_timesteps=args.timesteps, callback=callback)

    metrics = json.loads(log_path.read_text())
    if metrics["episode_summaries"]:
        extrinsic = [m["extrinsic_reward"] for m in metrics["episode_summaries"]]
        curiosity = [m["curiosity_reward"] for m in metrics["episode_summaries"]]
        print(
            f"平均外在獎勵: {np.mean(extrinsic):.2f}, "
            f"平均好奇心獎勵: {np.mean(curiosity):.2f}"
        )

    plot_metrics(log_path, args.log_dir / "rl_curiosity_plot.png")

    wrapped_env.close()


if __name__ == "__main__":

