# CLI 模組 (CLI)

> 路徑：`src/bioneuronai/cli/`
> 更新日期：2026-04-23
> 定位：統一命令列入口

`cli/` 負責把系統能力組裝成可直接執行的命令列介面。它本身不持有核心交易邏輯，而是把 `backtest`、`planning`、`analysis`、`core` 等模組串成單一入口。

---

## 目錄

1. [模組定位](#模組定位)
2. [實際結構](#實際結構)
3. [主入口](#主入口)
4. [目前命令範圍](#目前命令範圍)
5. [維護邊界](#維護邊界)

---

## 模組定位

`cli/` 目前專注於：

1. 提供 `python -m bioneuronai.cli.main <command>` 的統一入口
2. 把多個模組的功能包裝成明確子命令
3. 維持命令列參數解析與輸出格式一致

---

## 實際結構

```text
cli/
├── __init__.py  # 匯出 cli_main
├── main.py      # argparse parser、命令路由、各命令實作
└── README.md
```

檔案對照：
1. [__init__.py](__init__.py)
2. [main.py](main.py)

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到命令與入口層級。

---

## 主入口

主要入口：

```python
from bioneuronai.cli import cli_main
```

實際命令實作集中在 `main.py`，`__init__.py` 只做 lazy import，避免 module execution warning。

---

## 目前命令範圍

`main.py` 目前涵蓋的主命令包括：

1. `backtest`
2. `simulate`
3. `collect-signal-data`
4. `backtest-data`
5. `backtest-runs`
6. `trade`
7. `plan`
8. `news`
9. `pretrade`
10. `evolve`
11. `status`
12. `chat`

說明：

1. CLI 是正式操作入口之一，但不是唯一入口；HTTP 介面由 `api/` 負責。
2. 若命令背後功能屬於特定模組，實作與規則仍應維持在該模組，不應反向塞回 CLI。

---

## 維護邊界

1. 本文件只描述 CLI 入口、命令範圍與模組邊界。
2. 若子命令新增、刪除或更名，需同步更新此文件。
3. 命令背後的業務邏輯應由原模組維護，例如：
   - `plan` -> `planning/`
   - `news` -> `analysis/news`
   - `trade` -> `core/`
   - `collect-signal-data` -> `backtest/`

---

> 上層目錄：[BioNeuronai README](../README.md)
