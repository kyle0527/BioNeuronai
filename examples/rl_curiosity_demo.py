#!/usr/bin/env python3
"""Reinforcement learning curiosity demo using Gymnasium environments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

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
