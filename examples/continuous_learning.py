"""Continuous learning demonstration for BioNeuronAI networks."""

from __future__ import annotations

import asyncio
import random
from pathlib import Path
from typing import Iterator, List

from bioneuronai.checkpoint import CheckpointManager
from bioneuronai.core import BioNet


def generate_stream(seed: int = 0) -> Iterator[List[float]]:
    rng = random.Random(seed)
    base_patterns = [
        [0.2, 0.8],
        [0.8, 0.2],
        [0.5, 0.5],
        [0.1, 0.9],
    ]
    while True:
        pattern = rng.choice(base_patterns)
        noise = [rng.uniform(-0.05, 0.05) for _ in pattern]
        yield [max(0.0, min(1.0, v + n)) for v, n in zip(pattern, noise)]


async def continuous_learning(iterations: int = 200) -> None:
    net = BioNet()
    manager = CheckpointManager(net, history_limit=5)
    replay_buffer: List[List[float]] = []
    stream = generate_stream()

    checkpoint_path = Path(__file__).with_suffix(".json")

    for step in range(1, iterations + 1):
        sample = next(stream)
        net.learn(sample)
        replay_buffer.append(sample)
        if len(replay_buffer) > 16:
            replay_buffer.pop(0)

        # Occasional replay to avoid catastrophic forgetting
        if step % 25 == 0:
            for replay_sample in replay_buffer:
                net.learn(replay_sample)

        # Periodically snapshot and persist asynchronously
        if step % 50 == 0:
            state = manager.snapshot()
            await manager.save_async(checkpoint_path, state)

    final_state = manager.snapshot()
    await manager.save_async(checkpoint_path, final_state)
    print("Continuous learning complete. Last snapshot saved to", checkpoint_path)


if __name__ == "__main__":  # pragma: no cover - example script
    asyncio.run(continuous_learning())

