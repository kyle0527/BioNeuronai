# 風險管理模組 (Risk Management)

> 路徑：`src/bioneuronai/risk_management/`
> 更新日期：2026-06-15
> 架構層級：Layer 1 — 風險與倉位管理

本模組提供兩層風控能力：**傳統倉位管理**（`position_manager.py`）與 **AI 信心校準動態倉位**（`confidence_calibrator.py`）。

---

## 目錄

1. [實際結構](#實際結構)
2. [模組分工](#模組分工)
3. [對外匯出](#對外匯出)
4. [RiskManager（傳統風控）](#riskmanager傳統風控)
5. [AIConfidenceCalibrator（AI 風控）](#aiconfidencecalibratorai-風控)
6. [接入現況](#接入現況)
7. [已知斷點](#已知斷點)
8. [使用範例](#使用範例)

---

## 實際結構

```text
risk_management/
├── __init__.py                # 匯出 RiskManager 等傳統符號
├── position_manager.py        # 風險參數 + Kelly 倉位 + 投組風險
├── confidence_calibrator.py   # Temperature Scaling + Fractional Kelly + 對齊度
└── README.md
```

檔案對照：
1. [position_manager.py](position_manager.py)
2. [confidence_calibrator.py](confidence_calibrator.py)

---

## 模組分工

| 模組 | 職責 | 典型呼叫者 |
|------|------|-----------|
| `RiskManager` | 風險等級參數、倉位計算、投組評估 | `TradingEngine`、plan controller |
| `AIConfidenceCalibrator` | 校準 AI 信心、宏觀微觀對齊、Kelly 倉位乘數 | `pretrade_automation`、`strategy_fusion` |
| `AIReflectionLoop` | 事後 refit temperature | `planning/reflection_loop.py`（間接） |

---

## 對外匯出

```python
# 傳統風控（__init__.py 正式匯出）
from bioneuronai.risk_management import (
    RiskManager,
    RiskParameters,
    RiskLevel,
    PositionType,
    PositionSizing,
    PortfolioRisk,
    RiskAlert,
)

# AI 信心校準（單例工廠）
from bioneuronai.risk_management.confidence_calibrator import (
    AIConfidenceCalibrator,
    get_confidence_calibrator,
)
```

---

## RiskManager（傳統風控）

```python
rm = RiskManager()
sizing = await rm.calculate_position_size(
    symbol="BTCUSDT",
    entry_price=45000.0,
    stop_loss_price=44000.0,
    account_balance=10000.0,
    risk_level="MODERATE",
)
```

### 風險等級參數

| 等級 | 單筆風險 | 日最大風險 | 投組最大風險 | 最大回撤 | 最大槓桿 |
|------|---------:|-----------:|-------------:|---------:|---------:|
| `CONSERVATIVE` | 1% | 3% | 15% | 10% | 2x |
| `MODERATE` | 2% | 5% | 25% | 15% | 3x |
| `AGGRESSIVE` | 3% | 8% | 40% | 25% | 5x |
| `HIGH_RISK` | 5% | 15% | 60% | 40% | 10x |

---

## AIConfidenceCalibrator（AI 風控）

核心理念：將 AI 機率輸出轉為可執行的倉位大小（參考 López de Prado 做法）。

三大功能：

1. **Temperature Scaling** — 校準原始信心，抑制過度自信
2. **Fractional Kelly** — 用校準後機率與 net_odds 計算倉位比例
3. **Macro-Micro Alignment** — 宏觀情緒與微觀方向的連續對齊度（0~1）

主要方法：

| 方法 | 說明 |
|------|------|
| `calibrate_confidence(raw)` | 原始信心 → 校準信心 |
| `compute_alignment(macro, micro_dir, micro_conf)` | 宏觀微觀對齊度 |
| `compute_position_multiplier(...)` | 最終倉位乘數 |
| `record_decision(...)` | 記錄決策（供 refit 使用） |
| `record_outcome(record, pnl_pct)` | 回填交易結果 |
| `record_outcome_by_index(index, pnl_pct)` | 依 pretrade 寫入的 index 回填（主線 B） |
| `refit_temperature(min_samples)` | 重新擬合 Temperature |

單例取得：

```python
calibrator = get_confidence_calibrator()
```

---

## 接入現況

| 呼叫點 | 使用的功能 | 狀態 |
|--------|-----------|------|
| `pretrade_automation.py` | 校準 + 對齊 + 倉位乘數 → `position_size` | ✅ 計算完成 |
| `strategy_fusion.py` | `compute_alignment` → `signal.alignment_score` | ✅ |
| `reflection_loop.py` | `refit_temperature()` | ✅ CLI `reflect` + `autonomous --reflect-every` |
| `autonomous_operator._execute_paper` | pretrade quantity × risk_multiplier | ✅ 2026-06-15 |
| 主線 B 平倉 | `record_outcome_by_index()` | ✅ 2026-06-15 |
| 主線 A 平倉 | `record_outcome()` | ❌ 尚未呼叫 |

---

## 已知斷點

1. **主線 A 未回填 calibrator**：`record_decision()` 在 pretrade 有呼叫，但 TradingEngine 平倉尚未呼叫 `record_outcome()`。
2. **記憶來源分裂**：`reflection_loop` 讀 EpisodicMemory（主線 A），calibrator 讀自身 `_records`（主線 B pretrade），兩者尚未統一。

P2 / P5 主線 B 修正見 [`docs/PROJECT_STATUS.md`](../../../docs/PROJECT_STATUS.md)。

---

## 使用範例

```python
from bioneuronai.risk_management.confidence_calibrator import get_confidence_calibrator

calibrator = get_confidence_calibrator()

calibrated = calibrator.calibrate_confidence(raw_confidence=0.82)
alignment = calibrator.compute_alignment(
    macro_sentiment=-0.4,
    micro_direction="long",
    micro_confidence=0.75,
)
multiplier = calibrator.compute_position_multiplier(
    ai_confidence=calibrated,
    alignment_score=alignment,
    net_odds=0.06,
)
```

---

> 上層目錄：[BioNeuronai README](../README.md)｜操作手冊：[manuals/11_RISK_MANAGEMENT.md](../../../docs/manuals/11_RISK_MANAGEMENT.md)