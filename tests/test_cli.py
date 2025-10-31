from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bioneuronai.cli import app

FIXTURES = Path(__file__).parent / "fixtures"


def _run_cli(args: list[str]) -> tuple[int, str]:
    runner = CliRunner()
    result = runner.invoke(app, args)
    return result.exit_code, result.output


def test_single_neuron_from_file() -> None:
    exit_code, output = _run_cli(
        [
            "single-neuron",
            "--input-file",
            str(FIXTURES / "single_inputs.txt"),
            "--num-inputs",
            "2",
            "--learning-rate",
            "0.05",
        ]
    )
    assert exit_code == 0
    assert "Step" in output
    assert "Inputs" in output
    # 應至少包含三筆資料列
    assert output.count("[") >= 3


def test_single_neuron_stream_dashboard() -> None:
    exit_code, output = _run_cli(
        [
            "single-neuron",
            "--batch-size",
            "2",
            "--seed",
            "1",
            "--stream-dashboard",
        ]
    )
    assert exit_code == 0
    dashboard_lines = [
        line for line in output.splitlines() if line.startswith("[dashboard]")
    ]
    assert len(dashboard_lines) == 2
    payload = json.loads(dashboard_lines[0].split(" ", 1)[1])
    assert payload["payload"]["mode"] == "single-neuron"


def test_network_with_seed() -> None:
    exit_code, output = _run_cli(
        [
            "network",
            "--batch-size",
            "2",
            "--seed",
            "42",
            "--steps",
            "2",
        ]
    )
    assert exit_code == 0
    # 2 steps * 2 batches = 4 entries
    assert output.count("[") >= 4
    assert "Layer1" in output and "Layer2" in output


def test_import_dataset_summary() -> None:
    dataset = FIXTURES / "sample_dataset.csv"
    exit_code, output = _run_cli(
        [
            "import-dataset",
            str(dataset),
            "--delimiter",
            ",",
            "--has-header",
            "--stream-dashboard",
        ]
    )
    assert exit_code == 0
    assert "Loaded dataset" in output
    assert "Column" in output and "Mean" in output
    dashboard_lines = [
        line for line in output.splitlines() if line.startswith("[dashboard]")
    ]
    assert dashboard_lines, "應該有儀表板推送資訊"


def test_observe_metrics_outputs() -> None:
    exit_code, output = _run_cli(
        [
            "observe-metrics",
            "--batch-size",
            "5",
            "--seed",
            "123",
        ]
    )
    assert exit_code == 0
    assert "Avg Layer2 Output" in output
    assert "Avg Novelty" in output
