# Google Colab 使用手冊

> **更新日期**：2026-07-17  
> **倉庫**：`https://github.com/kyle0527/BioNeuronai`（公開 clone）  
> **目標**：在 Colab 上建立 **Python 3.13** 環境、GPU torch、跑通 smoke；可選短訓練。  
> **本機 Paper 交易長跑**仍以 [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) 為準。

---

## 1. 你需要先確認的 Runtime

1. 選單 **Runtime → Change runtime type**  
2. **Hardware accelerator → GPU**（例如 T4）  
3. 儲存並重新連線  

在儲存格中檢查：

```python
import sys, torch
print(sys.version)
print(torch.__version__, torch.cuda.is_available())
!nvidia-smi -L
```

期望：

- `cuda True`  
- GPU 名稱出現（如 Tesla T4）  
- 系統 Python 可能是 **3.12.x**（正常）；專案會裝在 **micromamba 3.13** 裡  

若仍是 `+cpu` 且 `cuda False`：重設 runtime 為 GPU 後重連。

---

## 2. 推薦：用官方 Notebook

1. 將本倉的 `notebooks/BioNeuronAI_Colab.ipynb` 上傳到 Colab，或  
2. 先 clone 再開：

```python
!git clone https://github.com/kyle0527/BioNeuronai.git
# 左側檔案瀏覽 → BioNeuronAI_Colab.ipynb → 用 Colab 開啟
```

依 notebook 單元由上到下執行。

---

## 3. 手動一步到位（等同 notebook）

```python
# 1) clone
!git clone https://github.com/kyle0527/BioNeuronai.git
%cd /content/BioNeuronai

# 2) 一鍵安裝（約數分鐘～十幾分鐘）
!bash tools/colab/setup_colab.sh

# 3) 之後一律用 3.13 環境的 python
PY = "/content/micromamba/envs/bioneuronai/bin/python"
!{PY} -c "import sys,torch; print(sys.version); print(torch.__version__, torch.cuda.is_available())"
!{PY} main.py status
```

詳細腳本說明：`tools/colab/README.md`。

---

## 4. 可選：短訓練 dry-run

需先有信號資料（本機 `collect-signal-data` 產物上傳到 Drive，或 Colab 內另備資料）。對齊 [13_CLOUD_TRAINING_RUNBOOK.md](13_CLOUD_TRAINING_RUNBOOK.md)：

```bash
# 使用 micromamba env 的 python
export PY=/content/micromamba/envs/bioneuronai/bin/python
$PY -m nlp.training.unified_trainer \
  --sig-only \
  --signal-data /path/to/data.jsonl \
  --max-signal-samples 4 \
  --epochs 1 \
  --batch 2 \
  --output /content/drive/MyDrive/bioneuronai_runs/dryrun \
  --no-save
```

**不要**在實驗中直接改寫並 promote `config/active_model.json`；promote 回本機驗證後再做。

---

## 5. 常見問題

| 現象 | 處理 |
|------|------|
| `pip install -e .` 報 requires-python | 不要用系統 3.12；用 `.../envs/bioneuronai/bin/python` |
| torch 變成 +cpu | 重跑 setup 且勿 `SKIP_TORCH`；確認 GPU runtime |
| TA-Lib 編譯失敗 | 看 setup 日誌；可暫略過技術指標相關模組 |
| Session 斷線 | 重跑 setup 或 Drive 固定 clone 路徑 |
| 想跑 paper 長跑 | 請用本機 [14](14_TESTNET_AND_LIVE_TRADING.md)，非 Colab 主用途 |

---

## 6. 與本機五步工作流

Colab 用於 **環境 + GPU 訓練／smoke**；  
本機步驟 ③ 調整 → ④ 手冊 → ⑤ 照手冊 Paper 實操 仍以本機為準。
