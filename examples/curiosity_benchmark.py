#!/usr/bin/env python3
"""簡易基準腳本：紀錄好奇心獎勵與回合報酬曲線."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np

try:
    import gymnasium as gym
except ImportError as exc:
    raise ImportError(
        "請安裝 gymnasium 以執行此腳本: `pip install gymnasium`."
    ) from exc

from bioneuronai.improved_core import CuriositDrivenNet


def run_benchmark(
    episodes: int,
    max_steps: int,
    output: Path,
) -> Dict[str, List[Dict[str, float]]]:
    env = gym.make("CartPole-v1")
    observation_size = int(np.prod(env.observation_space.shape))
    curiosity_net = CuriositDrivenNet(
        input_dim=observation_size,
        hidden_dim=8,
        curiosity_threshold=0.05,
        reward_scale=2.0,
        reward_clip=(0.0, 1.0),
    )

    episode_records: List[Dict[str, float]] = []
    step_curves: List[List[Dict[str, float]]] = []

    for episode in range(episodes):
        observation, _ = env.reset(seed=episode)
        ep_curiosity = 0.0
        ep_extrinsic = 0.0
        episode_curve: List[Dict[str, float]] = []

        for step in range(max_steps):
            action = env.action_space.sample()
            observation, reward, terminated, truncated, _ = env.step(action)
            stats = curiosity_net.step(observation, learn=True)

            curiosity_reward = float(stats["curiosity_reward"])
            ep_curiosity += curiosity_reward
            ep_extrinsic += float(reward)

            episode_curve.append(
                {
                    "step": float(step),
                    "curiosity_reward": curiosity_reward,
                    "extrinsic_reward": float(reward),
                }
            )

            if terminated or truncated:
                break

        episode_records.append(
            {
                "episode": float(episode),
                "length": float(len(episode_curve)),
                "curiosity_reward": ep_curiosity,
                "extrinsic_reward": ep_extrinsic,
            }
        )
        step_curves.append(episode_curve)

    metrics = {
        "episode_rewards": episode_records,
        "step_curves": step_curves,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2))

    env.close()
    return metrics


def plot_curves(metrics: Dict[str, List[Dict[str, float]]], figure_path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("未安裝 matplotlib，略過繪圖。")
        return

    plt.figure(figsize=(8, 4))
    for idx, curve in enumerate(metrics["step_curves"]):
        if not curve:
            continue
        steps = [point["step"] for point in curve]
        curiosity = [point["curiosity_reward"] for point in curve]
        extrinsic = [point["extrinsic_reward"] for point in curve]
        plt.plot(steps, curiosity, label=f"Ep{idx} Curiosity")
        plt.plot(steps, extrinsic, linestyle="--", label=f"Ep{idx} Extrinsic")

    plt.xlabel("Step")
    plt.ylabel("Reward")
    plt.title("Curiosity vs. Extrinsic Reward Curves")
    plt.legend()
    plt.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(figure_path)
    plt.close()
    print(f"曲線圖已儲存至 {figure_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=5, help="模擬回合數")
    parser.add_argument("--max-steps", type=int, default=200, help="每回合最大步數")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("examples/artifacts/curiosity_benchmark.json"),
        help="輸出 JSON 指標路徑",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=Path("examples/artifacts/curiosity_benchmark.png"),
        help="輸出圖檔路徑",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = run_benchmark(args.episodes, args.max_steps, args.output)

    rewards = metrics["episode_rewards"]
    curiosity_values = [record["curiosity_reward"] for record in rewards]
    extrinsic_values = [record["extrinsic_reward"] for record in rewards]

    print(
        "基準結果 -- 平均好奇心獎勵: "
        f"{np.mean(curiosity_values):.3f}, 平均外在獎勵: {np.mean(extrinsic_values):.3f}"
    )

    plot_curves(metrics, args.figure)


if __name__ == "__main__":
    main()
