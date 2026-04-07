# 風險管理模組 (Risk Management)

**路徑**: `src/bioneuronai/risk_management/`  
**版本**: v2.1  
**更新日期**: 2026-02-15  
**架構層級**: Layer 1 — 核心引擎層（風險控制）

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [核心組件](#核心組件)
4. [風險等級體系](#風險等級體系)
5. [導出 API](#導出-api)
6. [使用示例](#使用示例)
7. [設計原則](#設計原則)
8. [相關文檔](#相關文檔)

---

## 🎯 模組概述

風險管理模組是全系統風險參數的**單一事實來源 (Single Source of Truth)**。所有與風險相關的參數、倉位計算、槓桿控制、風險評估與資金管理，統一在此模組定義。其他模組（`trading`、`core`、`strategies`）皆透過匯入本模組取得風險參數，不得自行定義。

### 模組職責
- ✅ 統一風險參數定義（四級風險等級）
- ✅ 動態倉位大小計算
- ✅ 槓桿控制與上限管理
- ✅ 投資組合風險評估
- ✅ 風險預警與告警機制
- ✅ 資金管理規則

---

## 🏗️ 架構總覽

```
src/bioneuronai/risk_management/
├── __init__.py            # 模組入口，匯出 7 個符號 (30 行)
└── position_manager.py    # 風險參數 + 倉位管理 (1,000 行)
                             ─────────
                             合計 ~1,030 行
```

---

## 🎯 核心組件

### `position_manager.py` — 統一風險與倉位管理 (1,000 行)

**主要類與類型**:
- `RiskManager` — 風險管理器主類
- `RiskLevel` (Enum) — 四級風險等級
- `PositionType` (Enum) — 倉位類型
- `RiskParameters` (dataclass) — 風險參數組
- `PositionSizing` (dataclass) — 倉位計算結果
- `PortfolioRisk` (dataclass) — 投資組合風險
- `RiskAlert` (dataclass) — 風險告警

**工廠函式**: `get_risk_params(level)` — 根據風險等級取得預設參數

---

## 🛡️ 風險等級體系

| 等級 | 單筆風險 | 最大槓桿 | 日最大虧損 | 適用場景 |
|------|---------|---------|-----------|---------|
| `CONSERVATIVE` | 1% | 3x | 3% | 穩健型 / 新手 |
| `MODERATE` | 2% | 5x | 5% | 標準操作 |
| `AGGRESSIVE` | 3% | 10x | 8% | 進取型 |
| `HIGH_RISK` | 5% | 20x | 15% | 高風險高回報 |

---

## 📦 導出 API

```python
from bioneuronai.risk_management import (
    RiskManager,        # 風險管理器主類
    RiskParameters,     # 風險參數 (dataclass)
    RiskLevel,          # 風險等級 (Enum)
    PositionType,       # 倉位類型 (Enum)
    PositionSizing,     # 倉位計算結果 (dataclass)
    PortfolioRisk,      # 投資組合風險 (dataclass)
    RiskAlert,          # 風險告警 (dataclass)
)
```

---

## 💡 使用示例

### 基本倉位計算
```python
from bioneuronai.risk_management import RiskManager, RiskLevel

rm = RiskManager(risk_level=RiskLevel.MODERATE)

# 計算倉位大小
sizing = rm.calculate_position_size(
    account_balance=10000,
    entry_price=45000,
    stop_loss_price=44000,
    symbol="BTCUSDT"
)
print(f"建議倉位: {sizing.quantity}")
print(f"風險金額: {sizing.risk_amount}")
```

### 取得風險參數
```python
from bioneuronai.risk_management.position_manager import get_risk_params, RiskLevel

params = get_risk_params(RiskLevel.CONSERVATIVE)
print(f"單筆最大風險: {params.max_risk_per_trade}")
print(f"最大槓桿: {params.max_leverage}")
```

### 投資組合風險評估
```python
rm = RiskManager(risk_level=RiskLevel.MODERATE)
portfolio_risk = rm.evaluate_portfolio_risk(positions)
if portfolio_risk.total_exposure > 0.5:
    print("⚠️ 投資組合曝險過高")
```

---

## 🔧 設計原則

1. **單一事實來源**: 所有風險參數統一定義於 `position_manager.py`
2. **不可繞過**: 其他模組不得自行定義風險參數或覆蓋本模組的設定
3. **Fail Fast**: 風險檢查失敗時立即中止，不降級處理
4. **可配置性**: 透過 `config/risk_config_optimized.json` 可自訂參數

---

## 📚 相關文檔

- **風險管理手冊**: [RISK_MANAGEMENT_MANUAL.md](../../../docs/RISK_MANAGEMENT_MANUAL.md)
- **交易成本指南**: [TRADING_COSTS_GUIDE.md](../../../docs/TRADING_COSTS_GUIDE.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 2 月 15 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
