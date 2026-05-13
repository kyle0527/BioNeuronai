# CLI 模組 (CLI)

> 路徑：`src/bioneuronai/cli/`
> 更新日期：2026-05-12
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

| 命令 | 說明 |
|------|------|
| `backtest` | 歷史數據正式回測（replay service + AI，保存 runtime artifacts）|
| `strategy-backtest` | 逐一評估策略模板，輸出競爭排行榜；支援 Walk-Forward IS/OOS 驗證 |
| `readiness-gate` | 正式交易前 BTC/ETH 多時間框架 PASS/FAIL gate；使用 replay service，不送真實訂單 |
| `simulate` | 紙交易模擬（next_tick 推進，不產生真實訂單）|
| `collect-signal-data` | 收集 unified_trainer 所需的 signal JSONL 訓練資料 |
| `backtest-data` | 列出 repo 內可用的歷史回放資料目錄 |
| `backtest-runs` | 列出或檢視 replay runtime runs |
| `trade` | 交易監控；支援 testnet、`--paper-live`、live guard（預設載入 AI 模型） |
| `plan` | 透過 `TradingPlanController` 生成每日 10 步驟 SOP 交易計劃 |
| `news` | 新聞情緒分析 |
| `pretrade` | 進場前技術面 / 基本面 / 風險驗核 |
| `evolve` | 遺傳演算法策略競技場（找出最優策略組合）|
| `status` | 系統健康狀態（逐一檢查各模組是否可導入）|
| `chat` | 與 AI 交易助理對話（繁體中文 / English，支援市場上下文注入）|

說明：

1. CLI 是正式操作入口之一，但不是唯一入口；HTTP 介面由 `api/` 負責。
2. 若命令背後功能屬於特定模組，實作與規則仍應維持在該模組，不應反向塞回 CLI。

---

## 維護邊界

1. 本文件只描述 CLI 入口、命令範圍與模組邊界。
2. 若子命令新增、刪除或更名，需同步更新此文件。
3. 命令背後的業務邏輯應由原模組維護，例如：
   - `plan` → `planning/`
   - `news` → `analysis/news`
   - `pretrade` → `planning/pretrade_automation`
   - `trade` → `core/trading_engine`
   - `backtest` / `strategy-backtest` / `readiness-gate` / `simulate` / `collect-signal-data` / `backtest-data` / `backtest-runs` → `backtest/`
   - `evolve` → `strategies/strategy_arena`
   - `chat` → `nlp/chat_engine`

---

> 上層目錄：[BioNeuronai README](../README.md)
