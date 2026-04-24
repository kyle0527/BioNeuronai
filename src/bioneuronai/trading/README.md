# 交易模組 (Trading)

**路徑**: `src/bioneuronai/trading/`  
**更新日期**: 2026-04-20

---

## 目錄

1. [目前定位](#目前定位)
2. [實際結構](#實際結構)
3. [後續方向](#後續方向)
4. [目前已落地的內容](#目前已落地的內容)
5. [注意](#注意)

---

## 目前定位

此資料夾已不再承載：

- 10 步驟交易計劃
- 市場分析
- 交易對篩選
- 交易前檢查

上述高階規劃功能已移至：

- [plan_controller.py](../planning/plan_controller.py)
- [market_analyzer.py](../planning/market_analyzer.py)
- [pair_selector.py](../planning/pair_selector.py)
- [pretrade_automation.py](../planning/pretrade_automation.py)

---

## 實際結構

```text
trading/
├── __init__.py
├── virtual_account.py
└── README.md
```

檔案對照：
1. [__init__.py](__init__.py)
2. [virtual_account.py](virtual_account.py)

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到檔案與公開介面層級。

---

## 後續方向

`trading/` 將逐步收斂為真正的交易執行事實層，包含：

- 訂單狀態
- 帳戶狀態
- 持倉狀態
- 資金與盈虧快照
- 執行契約與同步

也就是：

- `strategies/` 負責決策
- `planning/` 負責高階規劃與 pretrade
- `trading/` 負責實際交易執行狀態與訂單事實

---

## 目前已落地的內容

- [virtual_account.py](virtual_account.py)

這個檔案目前承接 replay / mock execution 所需的第一層交易事實：

- 虛擬帳戶餘額
- 可用資金
- 掛單與成交
- 倉位與未實現盈虧
- 手續費、滑點、保證金
- 帳戶 / 倉位 / 掛單快照查詢
- pending entry order 查詢

目前 `backtest/` 已開始透過這裡提供的查詢介面讀取：

- `get_account_snapshot()`
- `get_position_snapshot()`
- `get_open_orders_snapshot()`
- `has_open_position()`
- `has_pending_entry_order()`

也就是說，`backtest/` 不再只把它當成內部資料物件，而是已經開始把它當成正式交易事實來源。

---

## 注意

- 目前不要再把新的規劃 / 分析 / pretrade 檔案放回此資料夾。
- 若需要交易計劃與檢查能力，請改用 `bioneuronai.planning`。

---

> 上層目錄：[BioNeuronai README](../README.md)
