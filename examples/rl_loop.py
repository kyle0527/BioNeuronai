"""簡易強化學習迴圈：使用 BioNeuronAI 進行探索控制。"""

from __future__ import annotations

import random
from typing import List, Sequence

from bioneuronai import BioNeuron

ARMS: Sequence[float] = (0.15, 0.45, 0.75)


def encode_state(step: int, max_steps: int, last_reward: float) -> List[float]:
    progress = step / max_steps
    reward_signal = min(1.0, max(0.0, last_reward))
    return [progress, reward_signal]


def run_episode(max_steps: int = 30) -> None:
    gate = BioNeuron(num_inputs=2, threshold=0.55, learning_rate=0.08, seed=99)
    action_values = [0.0 for _ in ARMS]
    counts = [0 for _ in ARMS]
    last_reward = 0.0

    for step in range(1, max_steps + 1):
        state_vec = encode_state(step, max_steps, last_reward)
        activation = gate.forward(state_vec)
        novelty = gate.novelty_score()

        if novelty > 0.25:
            action = random.randrange(len(ARMS))
        else:
            action = max(range(len(ARMS)), key=lambda idx: action_values[idx])

        reward = 1.0 if random.random() < ARMS[action] else 0.0
        counts[action] += 1
        action_values[action] += (reward - action_values[action]) / counts[action]
        last_reward = reward

        gate.learn(state_vec, target=reward)

        print(
            f"步驟 {step:02d} | 選擇手臂 {action} | 回饋 {reward:.0f} | "
            f"新穎性 {novelty:.3f} | 活化值 {activation:.3f}"
        )

    print("\n估計報酬:")
    for idx, value in enumerate(action_values):
        print(f"  手臂 {idx}: {value:.3f} (實際 {ARMS[idx]:.2f})")


def main() -> None:
    print("=== BioNeuronAI 強化學習探索示範 ===")
    run_episode()


if __name__ == "__main__":
    main()
