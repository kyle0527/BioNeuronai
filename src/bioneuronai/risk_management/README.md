# 風險管理模組 (Risk Management)

> 路徑：`src/bioneuronai/risk_management/`
> 更新日期：2026-04-20
> 架構層級：Layer 1 — 風險與倉位管理

`risk_management` 目前集中在 `position_manager.py`，提供風險參數、倉位計算、投資組合風險評估與風險告警。

---

## 目錄

1. [實際結構](#實際結構)
2. [對外匯出](#對外匯出)
3. [核心類別](#核心類別)
4. [風險等級參數](#風險等級參數)
5. [使用方式](#使用方式)
6. [注意事項](#注意事項)

---

## 實際結構

```text
risk_management/
├── __init__.py          # 匯出 7 個符號 (30 行)
├── position_manager.py  # 風險參數 + 倉位管理 (1,029 行)
└── README.md
```

---

## 對外匯出

```python
from bioneuronai.risk_management import (
    RiskManager,
    RiskParameters,
    RiskLevel,
    PositionType,
    PositionSizing,
    PortfolioRisk,
    RiskAlert,
)
```

---

## 核心類別

### `RiskManager`

實際初始化方式：

```python
from bioneuronai.risk_management import RiskManager

rm = RiskManager()
```

`RiskManager.__init__()` 目前不接收 `risk_level` 參數。風險等級在計算方法中以字串傳入，例如 `"MODERATE"`。

主要公開方法：

| 方法 | 型態 | 說明 |
|------|------|------|
| `calculate_position_size(...)` | async | 根據帳戶餘額、進場價、止損價與風險等級計算倉位 |
| `assess_portfolio_risk(...)` | async | 評估目前持倉與市場資料下的投資組合風險 |
| `monitor_risk_limits(...)` | async | 檢查風險限制並產生告警 |
| `optimize_risk_exposure(...)` | async | 依相關性、集中度與風險限制提出曝險調整 |
| `get_risk_summary()` | sync | 取得目前風險狀態摘要 |

---

## 風險等級參數

實作中的預設風險參數：

| 等級 | 單筆風險 | 日最大風險 | 投組最大風險 | 最大回撤限制 | 最大槓桿 |
|------|---------:|-----------:|-------------:|-------------:|---------:|
| `CONSERVATIVE` | 1% | 3% | 15% | 10% | 2x |
| `MODERATE` | 2% | 5% | 25% | 15% | 3x |
| `AGGRESSIVE` | 3% | 8% | 40% | 25% | 5x |
| `HIGH_RISK` | 5% | 15% | 60% | 40% | 10x |

---

## 使用方式

```python
import asyncio
from bioneuronai.risk_management import RiskManager

async def main():
    rm = RiskManager()
    sizing = await rm.calculate_position_size(
        symbol="BTCUSDT",
        entry_price=45000.0,
        stop_loss_price=44000.0,
        account_balance=10000.0,
        risk_level="MODERATE",
    )
    print(sizing)

asyncio.run(main())
```

投資組合風險評估使用 `assess_portfolio_risk()`，不是 `evaluate_portfolio_risk()`。

---

## 注意事項

1. `RiskLevel` enum 存在於此模組，但目前 `RiskManager` 內部預設參數 key 使用字串。
2. 多數主要計算方法是 async，呼叫端需 `await`。
3. 若後續要讓 `RiskManager(risk_level=...)` 成為正式 API，需要同步修改實作與 README。

---

> 上層目錄：[BioNeuronai README](../README.md)
