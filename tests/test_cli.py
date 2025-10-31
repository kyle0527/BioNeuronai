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
