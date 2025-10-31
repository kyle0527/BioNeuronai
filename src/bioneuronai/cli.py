from __future__ import annotations

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
