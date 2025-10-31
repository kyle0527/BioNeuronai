from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import typer
import numpy as np


class BioNeuron:
    """Bio-inspired neuron with short-term input memory and Hebbian update.
    (Minimal refactor of your original code; adds type hints and novelty_score.)
    """

    def __init__(
        self,
        num_inputs: int,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        self.num_inputs = num_inputs
        rng = np.random.default_rng(seed)
        self.weights = rng.uniform(0.1, 0.9, num_inputs).astype(np.float32)
        self.threshold = float(threshold)
        self.learning_rate = float(learning_rate)
        self.memory_len = int(memory_len)
        self.input_memory: List[np.ndarray] = []

    def forward(self, inputs: Sequence[float]) -> float:
        assert len(inputs) == self.num_inputs
        x = np.asarray(inputs, dtype=np.float32)

        # short-term memory
        self.input_memory.append(x)
        if len(self.input_memory) > self.memory_len:
            self.input_memory.pop(0)

        potential = float(np.dot(self.weights, x))
        return min(1.0, potential) if potential >= self.threshold else 0.0

    def hebbian_learn(self, inputs: Sequence[float], output: float) -> None:
        x = np.asarray(inputs, dtype=np.float32)
        delta = self.learning_rate * x * float(output)
        self.weights = np.clip(self.weights + delta, 0.0, 1.0)

    def novelty_score(self) -> float:
        """Simple novelty proxy: mean abs diff of last two inputs (0~1 scaled)."""
        if len(self.input_memory) < 2:
            return 0.0
        a, b = self.input_memory[-1], self.input_memory[-2]
        denom = np.maximum(1e-6, np.mean(np.abs(b)))
        score = float(np.clip(np.mean(np.abs(a - b)) / denom, 0.0, 5.0) / 5.0)
        return score


class BioLayer:
    def __init__(
        self,
        n_neurons: int,
        input_dim: int,
        *,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        rng = np.random.default_rng(seed)
        self.neurons = []
        for _ in range(n_neurons):
            neuron_seed = None if seed is None else int(rng.integers(0, 1_000_000))
            self.neurons.append(
                BioNeuron(
                    input_dim,
                    threshold=threshold,
                    learning_rate=learning_rate,
                    memory_len=memory_len,
                    seed=neuron_seed,
                )
            )

    def forward(self, inputs: Sequence[float]) -> List[float]:
        return [n.forward(inputs) for n in self.neurons]

    def learn(self, inputs: Sequence[float], outputs: Sequence[float]) -> None:
        for n, out in zip(self.neurons, outputs):
            n.hebbian_learn(inputs, out)


class BioNet:
    """Two-layer demo 2 -> 3 -> 3; returns (l2_out, l1_out)."""

    def __init__(
        self,
        *,
        threshold: float = 0.8,
        learning_rate: float = 0.01,
        memory_len: int = 5,
        seed: int | None = None,
    ) -> None:
        self.layer1 = BioLayer(
            3,
            2,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
        )
        self.layer2 = BioLayer(
            3,
            3,
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=None if seed is None else seed + 1,
        )

    def forward(self, inputs: Sequence[float]) -> Tuple[List[float], List[float]]:
        l1_out = self.layer1.forward(inputs)
        l2_out = self.layer2.forward(l1_out)
        return l2_out, l1_out

    def learn(self, inputs: Sequence[float]) -> None:
        l2_out, l1_out = self.forward(inputs)
        target = float(sum(l2_out) / len(l2_out))
        self.layer2.learn(l1_out, [target] * 3)
        self.layer1.learn(inputs, l1_out)

    def average_novelty(self) -> float:
        values = [n.novelty_score() for n in self.layer1.neurons]
        if not values:
            return 0.0
        return float(np.mean(values))

    def collect_weights(self) -> List[List[float]]:
        return [n.weights.astype(float).tolist() for n in self.layer1.neurons]


@dataclass
class CLIState:
    net: BioNet
    novelty_history: List[float]

    def register_inputs(self, inputs: Sequence[float]) -> Tuple[List[float], float]:
        outputs, _ = self.net.forward(inputs)
        self.net.learn(inputs)
        novelty = self.net.average_novelty()
        self.novelty_history.append(novelty)
        return outputs, novelty


app = typer.Typer(help="BioNeuron demo CLI with batch and interactive modes")


def _parse_inputs(raw_values: Iterable[str]) -> List[float]:
    values = [float(v) for v in raw_values]
    if len(values) != 2:
        raise typer.BadParameter("需要正好兩個數字作為輸入")
    return values


def _get_state(ctx: typer.Context) -> CLIState:
    if ctx.obj is None:
        raise typer.BadParameter("CLI state 尚未初始化")
    return ctx.obj


@app.callback()
def main(
    ctx: typer.Context,
    threshold: float = typer.Option(0.8, min=0.0, max=1.5, help="觸發閾值"),
    learning_rate: float = typer.Option(
        0.01, min=0.0, max=1.0, help="Hebbian 學習速率"
    ),
    memory_len: int = typer.Option(5, min=1, max=20, help="輸入記憶長度"),
    seed: int | None = typer.Option(None, help="隨機權重種子"),
) -> None:
    """配置並初始化 BioNet 實例。"""

    ctx.ensure_object(dict)
    ctx.obj = CLIState(
        net=BioNet(
            threshold=threshold,
            learning_rate=learning_rate,
            memory_len=memory_len,
            seed=seed,
        ),
        novelty_history=[],
    )


def _format_stats(state: CLIState) -> str:
    weights = state.net.collect_weights()
    threshold = state.net.layer1.neurons[0].threshold if state.net.layer1.neurons else 0.0
    avg_novelty = state.net.average_novelty()
    lines = [
        "=== BioNeuron 統計 ===",
        f"觸發閾值: {threshold:.3f}",
        f"平均新穎性: {avg_novelty:.3f}",
        "權重 (第一層):",
    ]
    for idx, weight_vector in enumerate(weights, start=1):
        weight_str = ", ".join(f"{w:.3f}" for w in weight_vector)
        lines.append(f"  神經元 {idx}: [{weight_str}]")
    return "\n".join(lines)


def _process_line(state: CLIState, line: str) -> Tuple[List[float], float]:
    tokens = [token for token in line.replace(",", " ").split() if token]
    if not tokens:
        raise ValueError("空白行")
    values = _parse_inputs(tokens)
    return state.register_inputs(values)


def _run_batch(ctx: typer.Context, source: Iterable[str]) -> None:
    state = _get_state(ctx)
    for idx, raw in enumerate(source, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            outputs, novelty = _process_line(state, line)
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"第 {idx} 行發生錯誤: {exc}", err=True)
            continue
        typer.echo(
            f"輸入 {line} -> 輸出: {[round(o, 3) for o in outputs]}, 新穎性: {novelty:.3f}"
        )


@app.command(help="讀取批次輸入檔並逐行推論")
def batch(
    ctx: typer.Context,
    file: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
) -> None:
    """Process a file containing two-number inputs per line."""

    with file.open("r", encoding="utf-8") as fh:
        _run_batch(ctx, fh)


@app.command(help="進入互動式選單")
def interactive(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    typer.echo("== BioNeuron 互動選單 ==")
    while True:
        typer.echo("[1] 單筆推論  [2] 查看統計  [3] 載入批次檔  [q] 離開")
        choice = typer.prompt("請選擇操作").strip().lower()
        if choice in {"q", "quit", "exit"}:
            typer.echo("已離開互動模式")
            break
        if choice == "1":
            payload = typer.prompt("輸入兩個數字 (a b)")
            try:
                outputs, novelty = _process_line(state, payload)
            except Exception as exc:  # noqa: BLE001
                typer.secho(f"輸入錯誤: {exc}", fg=typer.colors.RED)
                continue
            typer.secho(
                f"輸出: {[round(o, 3) for o in outputs]} | 平均新穎性: {novelty:.3f}",
                fg=typer.colors.GREEN,
            )
        elif choice == "2":
            typer.echo(_format_stats(state))
        elif choice == "3":
            path_input = typer.prompt("請輸入批次檔路徑")
            path = Path(path_input).expanduser()
            if not path.exists() or not path.is_file():
                typer.secho("找不到批次檔案", fg=typer.colors.RED)
                continue
            with path.open("r", encoding="utf-8") as fh:
                _run_batch(ctx, fh)
        else:
            typer.secho("未知選項，請再試一次", fg=typer.colors.YELLOW)


@app.command(help="顯示權重與新穎性統計")
def stats(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    typer.echo(_format_stats(state))


def cli_loop() -> None:
    app()


# TODO: 之後若改 LIF + STDP，保留此 API，不破壞上層介面.
