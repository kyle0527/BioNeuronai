from __future__ import annotations
e
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

import argparse
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import List, Sequence, Tuple

from .core import BioNet


@dataclass
class LayerSnapshot:
    name: str
    outputs: List[float]
    thresholds: List[float]
    novelties: List[float]


@dataclass
class InferenceRecord:
    inputs: Tuple[float, float]
    layers: List[LayerSnapshot]


class CLIApp:
    def __init__(self) -> None:
        self.net = BioNet()
        self.history: List[InferenceRecord] = []
        self._header_printed = False

    def ensure_header(self) -> None:
        if not self._header_printed:
            print("== BioNeuron CLI ==")
            self._header_printed = True

    def run_pair(self, pair: Tuple[float, float]) -> None:
        self.ensure_header()
        l2_out, l1_out = self.net.forward(pair)

        layer_snapshots = [
            LayerSnapshot(
                name="Layer 1",
                outputs=list(l1_out),
                thresholds=[n.threshold for n in self.net.layer1.neurons],
                novelties=[n.novelty_score() for n in self.net.layer1.neurons],
            ),
            LayerSnapshot(
                name="Layer 2",
                outputs=list(l2_out),
                thresholds=[n.threshold for n in self.net.layer2.neurons],
                novelties=[n.novelty_score() for n in self.net.layer2.neurons],
            ),
        ]

        self.history.append(InferenceRecord(inputs=pair, layers=layer_snapshots))

        print(format_table(layer_snapshots))
        self.net.learn(pair)

    def display_summary(self) -> None:
        self.ensure_header()
        print(format_summary(self.history))

    def interactive_loop(self) -> None:
        self.ensure_header()
        menu = (
            "1) 輸入兩個數字",
            "2) 從檔案載入",
            "3) 顯示統計摘要",
            "4) 離開",
        )
        try:
            while True:
                for line in menu:
                    print(line)
                choice = input("請選擇操作：").strip()
                if choice == "1":
                    raw = input("請輸入兩個數字 (a b)：").strip()
                    if not raw:
                        print("輸入不可為空。")
                        continue
                    try:
                        pair = parse_pair(raw)
                    except ValueError as exc:
                        print(f"格式錯誤：{exc}")
                        continue
                    self.run_pair(pair)
                elif choice == "2":
                    path_str = input("請輸入檔案路徑：").strip()
                    if not path_str:
                        print("路徑不可為空。")
                        continue
                    try:
                        pairs = parse_file(Path(path_str))
                    except (OSError, ValueError) as exc:
                        print(f"讀取失敗：{exc}")
                        continue
                    for pair in pairs:
                        self.run_pair(pair)
                elif choice == "3":
                    self.display_summary()
                elif choice in {"4", "q", "Q", "quit"}:
                    print("再見！")
                    break
                else:
                    print("無效的選項，請重新選擇。")
        except (KeyboardInterrupt, EOFError):
            print("\n再見！")


def parse_pair(text: str) -> Tuple[float, float]:
    parts = text.replace(",", " ").split()
    if len(parts) != 2:
        raise ValueError("需要兩個數字，以空白或逗號分隔")
    try:
        return float(parts[0]), float(parts[1])
    except ValueError as exc:
        raise ValueError("無法解析為浮點數") from exc


def parse_file(path: Path) -> List[Tuple[float, float]]:
    content = path.read_text(encoding="utf-8")
    pairs = []
    for line in content.splitlines():
        striped = line.strip()
        if not striped or striped.startswith("#"):
            continue
        pairs.append(parse_pair(striped))
    if not pairs:
        raise ValueError("檔案中沒有有效的數據列")
    return pairs


def format_table(layers: Sequence[LayerSnapshot]) -> str:
    headers = ["Layer", "Neuron", "Output", "Threshold", "Novelty"]
    rows: List[Tuple[str, str, str, str, str]] = []
    for layer in layers:
        for idx, (out, th, nov) in enumerate(
            zip(layer.outputs, layer.thresholds, layer.novelties), start=1
        ):
            rows.append(
                (
                    layer.name,
                    f"N{idx}",
                    f"{out:.3f}",
                    f"{th:.2f}",
                    f"{nov:.3f}",
                )
            )
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]

    def fmt_row(row: Sequence[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    sep = "-+-".join("-" * w for w in widths)
    lines = [fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


def format_summary(history: Sequence[InferenceRecord]) -> str:
    if not history:
        return "尚無數據可供摘要。"

    aggregates: dict[str, dict[str, List[float]]] = {}
    for record in history:
        for layer in record.layers:
            data = aggregates.setdefault(layer.name, {"outputs": [], "novelties": []})
            data["outputs"].extend(layer.outputs)
            data["novelties"].extend(layer.novelties)

    lines = ["統計摘要："]
    for layer_name in sorted(aggregates):
        data = aggregates[layer_name]
        outputs = data["outputs"]
        novelties = data["novelties"]
        lines.append(
            f"- {layer_name} 平均輸出={mean(outputs):.3f} 最大輸出={max(outputs):.3f} 最小輸出={min(outputs):.3f}"
        )
        lines.append(
            f"  新穎度平均={mean(novelties):.3f} 最高={max(novelties):.3f} 最低={min(novelties):.3f}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BioNeuron AI CLI with batch, file, and interactive modes."
    )
    parser.add_argument(
        "--batch",
        nargs="+",
        metavar="PAIR",
        help="直接提供多組輸入，如 --batch \"0.5 0.4\" \"0.2 0.9\"",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="從檔案讀取輸入，檔案每行為兩個數字，可用逗號或空白分隔",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="處理完輸入後顯示統計摘要",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="強制進入互動式選單，即便提供了批次或檔案輸入",
    )
    return parser


def process_batch_arguments(app: CLIApp, batch_args: Sequence[str]) -> None:
    for raw in batch_args:
        pair = parse_pair(raw)
        app.run_pair(pair)


def process_file_argument(app: CLIApp, file_path: Path) -> None:
    pairs = parse_file(file_path)
    for pair in pairs:
        app.run_pair(pair)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    app = CLIApp()

    has_processed = False
    summary_requested = bool(args.summary)
    if args.batch:
        try:
            process_batch_arguments(app, args.batch)
            has_processed = True
        except ValueError as exc:
            parser.error(str(exc))

    if args.file is not None:
        try:
            process_file_argument(app, args.file)
            has_processed = True
        except (OSError, ValueError) as exc:
            parser.error(str(exc))

    if summary_requested and not args.interactive:
        app.display_summary()
        has_processed = True

    if args.interactive:
        app.interactive_loop()
        if summary_requested:
            app.display_summary()
    elif not has_processed:
        app.interactive_loop()

    return 0


def cli_loop() -> None:
    """Backward-compatible entry for existing imports."""
    app = CLIApp()
    app.interactive_loop()


if __name__ == "__main__":
    raise SystemExit(main())

