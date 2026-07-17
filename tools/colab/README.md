# Colab 安裝腳本

**用途**：在 Google Colab（或類 Linux + GPU）建立 **Python 3.13** 環境並安裝 BioNeuronAI。

**前提**（你已驗證）：

- Runtime 選 **GPU**（例如 Tesla T4）
- 系統可能是 Python 3.12；腳本會用 **micromamba** 另建 3.13，符合 `pyproject.toml` 的 `requires-python`

## 快速用法

在 Colab notebook 中：

```python
!git clone https://github.com/kyle0527/BioNeuronai.git
%cd BioNeuronai
!bash tools/colab/setup_colab.sh
```

之後每個新 cell 若 shell 重開，需重新 activate：

```python
import os
os.environ["MAMBA_ROOT_PREFIX"] = "/content/micromamba"
import subprocess, pathlib
root = pathlib.Path("/content/BioNeuronai")
# 建議直接用完整路徑呼叫 env 內 python：
py = "/content/micromamba/envs/bioneuronai/bin/python"
!{py} -c "import torch; print(torch.__version__, torch.cuda.is_available())"
!{py} main.py status
```

完整逐步單元見：`notebooks/BioNeuronAI_Colab.ipynb`  
操作說明：`docs/manuals/21_COLAB.md`

## 環境變數

| 變數 | 預設 | 說明 |
|------|------|------|
| `BIONEURONAI_ROOT` | 當前目錄 | 專案根 |
| `MAMBA_ROOT_PREFIX` | `/content/micromamba` | micromamba 根 |
| `ENV_NAME` | `bioneuronai` | conda 環境名 |
| `SKIP_TORCH=1` | 關 | 不重裝 torch |
| `SMOKE_ONLY=1` | 關 | 只跑 smoke |

## 注意

- **不要**用 pyproject 的 `torch==…+cpu` 覆蓋 GPU 版。
- Paper 長跑交易驗收仍以**本機**為主；Colab 偏 smoke + GPU 訓練。
- API key 用 Colab Secrets，勿寫進 git。
