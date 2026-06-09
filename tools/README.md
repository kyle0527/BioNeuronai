# tools/ — 開發與運維工具

> 更新日期: 2026-06-09
> 原則: 這份索引只描述目前還存在、且仍建議使用的工具。歷次生成物不在此維護。

---

## 工具總覽

```text
tools/
├── gen_backtest_charts.py              # 回測圖表輸出
├── generate_project_report.ps1         # 專案結構/統計報告生成
├── generate_tree_ultimate_chinese.ps1  # 樹狀圖生成與差異比對
├── train_meta_learner.py               # Meta-learner 訓練入口
├── tree.mmd                            # 目前保留的樹狀圖輸出
├── data_download/                      # 歷史資料下載與回測輔助工具
└── README.md
```

---

## 目前保留的工具

### gen_backtest_charts.py

將既有回測結果轉成圖表輸出，適合對 `backtest/runtime/<run_id>` 做視覺化檢查。

```powershell
python tools/gen_backtest_charts.py
```

### train_meta_learner.py

Meta-learner 訓練入口。只在要重訓策略融合權重時使用。

```powershell
python tools/train_meta_learner.py
```

### generate_project_report.ps1

生成專案結構與統計報告。歷史 `PROJECT_REPORT_*.txt` 已清理，若需要請重新生成，不保留快照堆積。

```powershell
.\tools\generate_project_report.ps1
```

### generate_tree_ultimate_chinese.ps1

生成目前專案樹狀圖，必要時可對照前一次輸出做差異比對。歷次 `tree_*.mmd` 快照已清理；預設只保留當前 `tree.mmd`。

```powershell
.\tools\generate_tree_ultimate_chinese.ps1
```

---

## data_download 子目錄

`tools/data_download/` 目前是仍在使用的下載/回測輔助區，包含：

- `download-kline.py`
- `download-aggTrade.py`
- `download-trade.py`
- `download-futures-*.py`
- `data_feeder.py`
- `mock_api.py`
- `run_backtest.py`
- `utility.py`
- `enums.py`

這一區的用途是補資料、餵歷史資料、或做下載層驗證，不是日常操作主入口。

---

## 清理原則

- `tools/` 只保留仍會手動執行的腳本與少量代表性輸出。
- 歷次生成的報告、樹圖、臨時驗證快照不長期堆在版控內。
- 若工具已消失或不再建議使用，應先更新本文件，再決定是否歸檔對應說明。

---

> 上層目錄: [根目錄 README](../README.md)
