# backtesting/ — 歷史回測與 Walk-Forward 測試

> **更新日期**: 2026-04-07  
> **版本**: v2.2

---

## 目錄

- [模組概述](#模組概述)
- [與 backtest/ 的區別](#與-backtest-的區別)
- [檔案說明](#檔案說明)
- [核心類別](#核心類別)
- [使用方式](#使用方式)
- [Walk-Forward 測試](#walk-forward-測試)

---

## 模組概述

`backtesting/` 提供基於**真實歷史數據**的策略回測與 Walk-Forward 驗證系統，支持：

- 從 Binance API 載入歷史 K 線數據
- 逐筆模擬策略信號執行
- 精確交易成本計算（手續費 + 滑點 + 資金費率）
- 滾動窗口 Walk-Forward 測試（防止過擬合）

目前定位：
- `backtesting/` 是研究型分析工具箱
- 專案正式的 replay / mock exchange 主路徑以根目錄的 `backtest/` 為主
- 若要讓上層模組無感切換真實 / 模擬資料源，請優先使用 `backtest/`

---

## 與 backtest/ 的區別

| 特性 | `backtest/` | `backtesting/` |
|------|-------------|----------------|
| 設計理念 | Yield 生成器即時模擬 | 歷史數據批量回測 |
| 數據來源 | MockBinanceConnector 偽裝 | Binance API 真實歷史 K 線 |
| 防偷看 | 嚴格防偷看機制 | 依序處理 K 線 |
| Walk-Forward | 無 | ✅ 滾動窗口驗證 |
| 交易成本 | MockBinanceConnector 內建帳戶邏輯 | TradingCostCalculator 獨立計算 |

---

## 檔案說明

```
backtesting/
├── __init__.py               # 模組匯出（9 個公開類別）
├── cost_calculator.py        # 交易成本計算器 (301 行)
├── historical_backtest.py    # 歷史數據回測引擎 (629 行)
└── walk_forward.py           # Walk-Forward 測試框架 (726 行)
```

---

## 核心類別

### cost_calculator.py

| 類別 | 說明 |
|------|------|
| `TradingCost` | 交易成本數據類（手續費 / 滑點 / 資金費率） |
| `OrderInfo` | 訂單資訊 Pydantic 模型 |
| `TradingCostCalculator` | 成本計算器（Maker/Taker 費率、滑點估算、每日資金費率） |

### historical_backtest.py

| 類別 | 說明 |
|------|------|
| `HistoricalDataLoader` | 從 Binance Futures API 載入歷史 K 線 |
| `BacktestEngine` | 回測引擎核心（信號處理、買賣執行、倉位更新、績效計算） |
| `HistoricalBacktest` | 高階回測入口（整合數據載入 + 引擎 + 成本計算） |

### walk_forward.py

| 類別 | 說明 |
|------|------|
| `WalkForwardWindow` | 滾動窗口定義（訓練期 + 測試期） |
| `WindowResult` | 單一窗口結果（Sharpe 退化率、過擬合判斷） |
| `WalkForwardConfig` | 設定檔（窗口大小、步長、最佳化目標） |
| `WalkForwardResult` | 整體結果（過擬合率、穩健度評分） |
| `WalkForwardTester` | Walk-Forward 測試主控制器 |

---

## 使用方式

### 基本歷史回測

```python
from backtesting import HistoricalBacktest
from schemas.backtesting import BacktestConfig

config = BacktestConfig(
    symbol="BTCUSDT",
    interval="1h",
    initial_capital=10000.0,
    leverage=10,
)
bt = HistoricalBacktest(config=config)
result = await bt.run()
print(f"淨利: {result.net_profit}, Sharpe: {result.sharpe_ratio}")
```

### 交易成本計算

```python
from backtesting import TradingCostCalculator, OrderInfo

calc = TradingCostCalculator(maker_fee=0.0002, taker_fee=0.0004)
cost = calc.calculate_total_cost(
    order_size_usd=10000.0,
    price=50000.0,
    is_maker=False,
    volume_24h=1e9,
)
print(f"總成本: {cost.total_cost_pct:.4%}")
```

---

## Walk-Forward 測試

Walk-Forward 測試將歷史數據分為多個**訓練期 + 測試期**滾動窗口，用於：
- 驗證策略的時間穩定性
- 檢測過擬合（比較訓練期 vs 測試期 Sharpe Ratio）
- 計算穩健度評分

```python
from backtesting import WalkForwardTester, WalkForwardConfig

config = WalkForwardConfig(
    train_days=90,
    test_days=30,
    step_days=30,
    n_optimization_trials=50,
)
tester = WalkForwardTester(config=config)
result = await tester.run(symbol="BTCUSDT", interval="1h")
print(f"過擬合率: {result.overfitting_rate:.1%}")
print(f"穩健度: {result.robustness_score:.2f}")
```

---

> 📖 上層目錄：[根目錄 README](../README.md)
