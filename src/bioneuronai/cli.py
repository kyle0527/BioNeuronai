from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np
import typer

from .core import BioNet, BioNeuron

app = typer.Typer(help="BioNeuronAI command line interface with rich sub-commands")


@dataclass
class TableCell:
    text: str
    color: Optional[typer.colors.Color] = None
    align: str = "left"


class DashboardStreamer:
    """Minimal dashboard streamer used for CLI demonstrations."""

    def __init__(self, enabled: bool, endpoint: Optional[str]) -> None:
        self.enabled = enabled
        self.endpoint = endpoint or "memory://dashboard"

    def send(self, payload: dict) -> None:
        if not self.enabled:
            return
        message = json.dumps({"endpoint": self.endpoint, "payload": payload})
        typer.echo(
            typer.style(f"[dashboard] {message}", fg=typer.colors.BRIGHT_CYAN)
        )


def _load_batch(
    input_file: Optional[Path],
    batch_size: int,
    num_inputs: int,
    seed: Optional[int],
) -> List[List[float]]:
    if input_file is not None:
        if not input_file.exists():
            raise typer.BadParameter(f"找不到檔案: {input_file}")
        rows: List[List[float]] = []
        for line in input_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            values = [float(part) for part in line.replace(",", " ").split()]
            if len(values) != num_inputs:
                raise typer.BadParameter(
                    f"輸入維度不一致，期待 {num_inputs} 個數值，實際為 {len(values)}"
                )
            rows.append(values)
        if not rows:
            raise typer.BadParameter("檔案中沒有有效資料列")
        return rows

    rng = np.random.default_rng(seed)
    samples = rng.uniform(0.0, 1.0, size=(batch_size, num_inputs))
    return samples.round(4).tolist()


def _format_table(headers: Sequence[str], rows: Sequence[Sequence[TableCell]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell.text))

    header_line = " | ".join(h.ljust(widths[idx]) for idx, h in enumerate(headers))
    header_line = typer.style(header_line, fg=typer.colors.BRIGHT_BLUE, bold=True)
    separator = "-+-".join("-" * width for width in widths)

    body_lines = []
    for row in rows:
        formatted_cells = []
        for idx, cell in enumerate(row):
            if cell.align == "right":
                padded = cell.text.rjust(widths[idx])
            else:
                padded = cell.text.ljust(widths[idx])
            if cell.color is not None:
                formatted_cells.append(typer.style(padded, fg=cell.color))
            else:
                formatted_cells.append(padded)
        body_lines.append(" | ".join(formatted_cells))

    return "\n".join([header_line, separator, *body_lines])


def _float_cell(value: float) -> TableCell:
    if value >= 0.7:
        color = typer.colors.BRIGHT_GREEN
    elif value >= 0.3:
        color = typer.colors.YELLOW
    else:
        color = typer.colors.RED
    return TableCell(text=f"{value:.3f}", color=color, align="right")


def _inputs_cell(values: Sequence[float]) -> TableCell:
    text = "[" + ", ".join(f"{v:.3f}" for v in values) + "]"
    return TableCell(text=text)


@app.command("single-neuron")
def single_neuron(
    num_inputs: int = typer.Option(2, help="神經元輸入維度"),
    threshold: float = typer.Option(0.8, help="觸發閾值"),
    learning_rate: float = typer.Option(0.01, help="Hebbian 學習率"),
    memory_len: int = typer.Option(5, help="短期記憶長度"),
    batch_size: int = typer.Option(5, help="隨機批次大小"),
    input_file: Optional[Path] = typer.Option(None, help="指定輸入檔案"),
    seed: Optional[int] = typer.Option(None, help="隨機種子"),
    stream_dashboard: bool = typer.Option(
        False, "--stream-dashboard/--no-stream-dashboard", help="推送至儀表板"
    ),
    dashboard_endpoint: Optional[str] = typer.Option(
        None, help="儀表板接收端點 (選用)"
    ),
) -> None:
    """單顆 BioNeuron 的推論/學習流程。"""

    batch = _load_batch(input_file, batch_size, num_inputs, seed)
    neuron = BioNeuron(
        num_inputs=num_inputs,
        threshold=threshold,
        learning_rate=learning_rate,
        memory_len=memory_len,
        seed=seed,
    )
    streamer = DashboardStreamer(stream_dashboard, dashboard_endpoint)

    rows: List[List[TableCell]] = []
    for idx, inputs in enumerate(batch, start=1):
        output = neuron.forward(inputs)
        neuron.hebbian_learn(inputs, output)
        novelty = neuron.novelty_score()
        rows.append(
            [
                TableCell(text=str(idx), align="right"),
                _inputs_cell(inputs),
                _float_cell(output),
                _float_cell(novelty),
            ]
        )
        streamer.send(
            {
                "mode": "single-neuron",
                "step": idx,
                "inputs": inputs,
                "output": output,
                "novelty": novelty,
            }
        )

    table = _format_table(["Step", "Inputs", "Output", "Novelty"], rows)
    typer.echo(table)


@app.command("network")
def network(
    batch_size: int = typer.Option(5, help="隨機批次大小"),
    input_file: Optional[Path] = typer.Option(None, help="指定輸入檔案 (二維)"),
    seed: Optional[int] = typer.Option(None, help="隨機種子"),
    steps: int = typer.Option(1, help="重複訓練輪數"),
    stream_dashboard: bool = typer.Option(
        False, "--stream-dashboard/--no-stream-dashboard", help="推送至儀表板"
    ),
    dashboard_endpoint: Optional[str] = typer.Option(
        None, help="儀表板接收端點 (選用)"
    ),
) -> None:
    """建構兩層 BioNet 並顯示層輸出/novelty。"""

    batch = _load_batch(input_file, batch_size, 2, seed)
    net = BioNet()
    streamer = DashboardStreamer(stream_dashboard, dashboard_endpoint)

    rows: List[List[TableCell]] = []
    step_counter = 0
    for epoch in range(steps):
        for inputs in batch:
            step_counter += 1
            l2_out, l1_out = net.forward(inputs)
            net.learn(inputs)
            novelty = net.layer1.neurons[0].novelty_score()
            rows.append(
                [
                    TableCell(text=str(step_counter), align="right"),
                    _inputs_cell(inputs),
                    TableCell(
                        text="[" + ", ".join(f"{v:.3f}" for v in l1_out) + "]"
                    ),
                    TableCell(
                        text="[" + ", ".join(f"{v:.3f}" for v in l2_out) + "]"
                    ),
                    _float_cell(novelty),
                ]
            )
            streamer.send(
                {
                    "mode": "network",
                    "step": step_counter,
                    "inputs": inputs,
                    "layer1": l1_out,
                    "layer2": l2_out,
                    "novelty": novelty,
                }
            )

    headers = ["Step", "Inputs", "Layer1", "Layer2", "Novelty"]
    table = _format_table(headers, rows)
    typer.echo(table)


@app.command("import-dataset")
def import_dataset(
    path: Path = typer.Argument(..., help="資料集路徑 (純文字/CSV)"),
    delimiter: str = typer.Option(",", help="欄位分隔符"),
    has_header: bool = typer.Option(False, help="是否包含標題列"),
    stream_dashboard: bool = typer.Option(
        False, "--stream-dashboard/--no-stream-dashboard", help="推送至儀表板"
    ),
    dashboard_endpoint: Optional[str] = typer.Option(
        None, help="儀表板接收端點 (選用)"
    ),
) -> None:
    """匯入資料集並輸出統計摘要。"""

    if not path.exists():
        raise typer.BadParameter(f"找不到資料集檔案: {path}")

    content = path.read_text(encoding="utf-8").splitlines()
    rows: List[List[float]] = []
    for idx, line in enumerate(content):
        if idx == 0 and has_header:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        parts = [part for part in stripped.split(delimiter) if part]
        rows.append([float(part) for part in parts])

    if not rows:
        raise typer.BadParameter("資料集沒有有效資料列")

    data = np.asarray(rows, dtype=np.float32)
    num_rows, num_cols = data.shape

    headers = ["Column", "Mean", "Std", "Min", "Max"]
    table_rows: List[List[TableCell]] = []
    stats_payload = []
    for col_idx in range(num_cols):
        column = data[:, col_idx]
        stats = {
            "column": col_idx,
            "mean": float(np.mean(column)),
            "std": float(np.std(column)),
            "min": float(np.min(column)),
            "max": float(np.max(column)),
        }
        stats_payload.append(stats)
        table_rows.append(
            [
                TableCell(text=f"x{col_idx}", align="right"),
                _float_cell(stats["mean"]),
                _float_cell(stats["std"]),
                _float_cell(stats["min"]),
                _float_cell(stats["max"]),
            ]
        )

    streamer = DashboardStreamer(stream_dashboard, dashboard_endpoint)
    streamer.send(
        {
            "mode": "import-dataset",
            "rows": num_rows,
            "cols": num_cols,
            "stats": stats_payload,
        }
    )

    typer.echo(
        typer.style(
            f"Loaded dataset with {num_rows} rows × {num_cols} columns",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(_format_table(headers, table_rows))


@app.command("observe-metrics")
def observe_metrics(
    batch_size: int = typer.Option(10, help="隨機批次大小"),
    input_file: Optional[Path] = typer.Option(None, help="指定輸入檔案"),
    seed: Optional[int] = typer.Option(None, help="隨機種子"),
    stream_dashboard: bool = typer.Option(
        False, "--stream-dashboard/--no-stream-dashboard", help="推送至儀表板"
    ),
    dashboard_endpoint: Optional[str] = typer.Option(
        None, help="儀表板接收端點 (選用)"
    ),
) -> None:
    """觀察 BioNet 指標 (平均輸出、權重範圍、novelty)。"""

    batch = _load_batch(input_file, batch_size, 2, seed)
    net = BioNet()
    streamer = DashboardStreamer(stream_dashboard, dashboard_endpoint)

    novelty_scores: List[float] = []
    layer2_means: List[float] = []
    for inputs in batch:
        l2_out, _ = net.forward(inputs)
        net.learn(inputs)
        novelty_scores.append(net.layer1.neurons[0].novelty_score())
        layer2_means.append(float(np.mean(l2_out)))

    l1_weights = np.concatenate([n.weights for n in net.layer1.neurons])
    l2_weights = np.concatenate([n.weights for n in net.layer2.neurons])

    headers = ["Metric", "Value"]
    rows = [
        [
            TableCell(text="Avg Layer2 Output"),
            _float_cell(float(np.mean(layer2_means))),
        ],
        [
            TableCell(text="Layer1 Weight Range"),
            TableCell(
                text=f"{float(np.min(l1_weights)):.3f}~{float(np.max(l1_weights)):.3f}",
                color=typer.colors.BRIGHT_MAGENTA,
                align="right",
            ),
        ],
        [
            TableCell(text="Layer2 Weight Range"),
            TableCell(
                text=f"{float(np.min(l2_weights)):.3f}~{float(np.max(l2_weights)):.3f}",
                color=typer.colors.BRIGHT_MAGENTA,
                align="right",
            ),
        ],
        [
            TableCell(text="Avg Novelty"),
            _float_cell(float(np.mean(novelty_scores))),
        ],
    ]

    streamer.send(
        {
            "mode": "observe-metrics",
            "avg_layer2": float(np.mean(layer2_means)),
            "avg_novelty": float(np.mean(novelty_scores)),
            "layer1_range": [float(np.min(l1_weights)), float(np.max(l1_weights))],
            "layer2_range": [float(np.min(l2_weights)), float(np.max(l2_weights))],
        }
    )

    typer.echo(_format_table(headers, rows))


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover - 手動呼叫入口
    main()
