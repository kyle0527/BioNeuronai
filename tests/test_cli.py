from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

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
