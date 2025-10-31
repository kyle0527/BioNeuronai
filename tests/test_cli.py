
from pathlib import Path

from typer.testing import CliRunner



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

from bioneuronai.core import app


def test_stats_command_outputs_threshold() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "BioNeuron 統計" in result.output
    assert "觸發閾值" in result.output


def test_batch_command_processes_file(tmp_path: Path) -> None:
    runner = CliRunner()
    file = tmp_path / "inputs.txt"
    file.write_text("0.1 0.2\n錯誤\n0.3,0.4\n", encoding="utf-8")
    result = runner.invoke(app, ["batch", str(file)])
    assert result.exit_code == 0
    assert "輸入 0.1 0.2" in result.output
    # Error line should be reported but not abort execution
    assert "第 2 行發生錯誤" in result.output
    assert "輸入 0.3,0.4" in result.output


def test_batch_command_missing_file() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["batch", "missing.txt"])
    assert result.exit_code != 0
    assert "Invalid value for 'FILE'" in result.output

import os
import subprocess
import sys
from pathlib import Path


def run_cli(args, input_text=None):
    cmd = [sys.executable, "-m", "bioneuronai.cli", *args]
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
    )
    return subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )


def test_batch_mode_outputs_table_and_summary():
    result = run_cli(["--batch", "0.2 0.4", "0.1 0.9", "--summary"])
    stdout = result.stdout

    assert "== BioNeuron CLI ==" in stdout
    assert stdout.count("Layer 1 | N1") >= 2
    assert "統計摘要：" in stdout
    assert "新穎度平均" in stdout


def test_file_mode_reads_inputs(tmp_path):
    data_file = tmp_path / "inputs.txt"
    data_file.write_text("0.1 0.2\n0.3,0.4\n", encoding="utf-8")

    result = run_cli(["--file", str(data_file)])
    stdout = result.stdout

    assert "== BioNeuron CLI ==" in stdout
    assert stdout.count("Layer 1 | N1") >= 2
    assert "統計摘要" not in stdout


def test_summary_mode_without_inputs():
    result = run_cli(["--summary"])
    stdout = result.stdout

    assert "尚無數據可供摘要" in stdout
    assert "請選擇操作" not in stdout


def test_interactive_receives_summary_after_exit():
    result = run_cli(["--batch", "0.2 0.4", "--interactive", "--summary"], input_text="4\n")
    stdout = result.stdout

    assert stdout.count("Layer 1 | N1") >= 1
    assert "再見！" in stdout
    assert "統計摘要：" in stdout


