# BioNeuronai 風險管理使用手冊

**套件版本**：v2.1
**更新日期**：2026-06-15
**模組路徑**：`src/bioneuronai/risk_management/`
**程式參考**：[`risk_management/README.md`](../../src/bioneuronai/risk_management/README.md)

---

## 目錄

1. [概述與雙層架構](#1-概述與雙層架構)
2. [RiskManager（傳統風控）](#2-riskmanager傳統風控)
3. [風險等級與參數](#3-風險等級與參數)
4. [倉位計算邏輯](#4-倉位計算邏輯)
5. [投資組合風險評估](#5-投資組合風險評估)
6. [風險警報系統](#6-風險警報系統)
7. [AIConfidenceCalibrator（AI 風控）](#7-aiconfidencecalibratorai-風控)
8. [進場前驗核中的風險整合](#8-進場前驗核中的風險整合)
9. [自主迴圈與 TradingEngine 的風控差異](#9-自主迴圈與-tradingengine-的風控差異)
10. [風險設定檔修改指引](#10-風險設定檔修改指引)
11. [已知限制（2026-06-15）](#11-已知限制2026-06-15)
12. [最佳實踐建議](#12-最佳實踐建議)
13. [相關文件](#13-相關文件)

---

## 1. 概述與雙層架構

`risk_management/` 提供**兩層**風控，職責不同，不可混為一談：

| 層級 | 模組 | 主要呼叫者 | 職責 |
|------|------|-----------|------|
| 傳統風控 | `position_manager.py` → `RiskManager` | `TradingEngine`、plan 流程 | Kelly、投組 VaR、風險等級參數 |
| AI 風控 | `confidence_calibrator.py` → `AIConfidenceCalibrator` | `pretrade_automation`、`strategy_fusion` | 信心校準、宏觀微觀對齊、動態倉位乘數 |

```
                    ┌─────────────────────┐
                    │   TradingEngine     │
                    │   → RiskManager     │
                    └─────────────────────┘

┌──────────────────────────────────────────────────┐
│ PreTradeCheckSystem._calculate_risk()              │
│   1. 內部 RiskCalculation（固定 risk_percentage） │
│   2. AIConfidenceCalibrator（步驟 7.5 動態乘數）  │
│   → order_parameters.quantity                    │
└──────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
  strategy_fusion                 autonomous（✅ 2026-06-15 見 §9）
  alignment_score                 優先採 pretrade quantity
```

所有計算在**本地端**完成，不需外部風控服務。

---

## 2. RiskManager（傳統風控）

### 匯入方式

```python
from bioneuronai.risk_management import RiskManager, RiskParameters
```

> `get_risk_params()` 定義在 `position_manager.py`，**尚未**列入 `risk_management/__init__.py` 的 `__all__`。請使用：

```python
from bioneuronai.risk_management.position_manager import get_risk_params

params = get_risk_params("MODERATE")
```

### 初始化

```python
rm = RiskManager()  # 不接受 risk_level 建構參數
```

風險等級在**每次計算方法**中以字串傳入，例如 `risk_level="MODERATE"`。

### 主要方法

| 方法 | 型態 | 說明 |
|------|------|------|
| `calculate_position_size(...)` | async | 依止損距離與風險等級計算倉位 |
| `assess_portfolio_risk(...)` | async | 投組 VaR、回撤、集中度 |
| `monitor_risk_limits(...)` | async | 風險限制檢查與告警 |
| `optimize_risk_exposure(...)` | async | 曝險調整建議 |
| `get_risk_summary()` | sync | 風險狀態摘要 |

---

## 3. 風險等級與參數

| 等級 | 識別碼 | 適合對象 |
|------|--------|----------|
| 保守 | `CONSERVATIVE` | 新手 |
| 中等（常用） | `MODERATE` | 一般交易者 |
| 積極 | `AGGRESSIVE` | 有經驗者 |
| 高風險 | `HIGH_RISK` | 專業投機（需自覺風險） |

### 參數對照表（與 `position_manager.py` 一致）

| 參數 | CONSERVATIVE | MODERATE | AGGRESSIVE | HIGH_RISK |
|------|:------------:|:--------:|:----------:|:---------:|
| `max_risk_per_trade` | 1% | **2%** | 3% | 5% |
| `max_daily_risk` | 3% | **5%** | 8% | 15% |
| `max_portfolio_risk` | 15% | **25%** | 40% | 60% |
| `max_drawdown_limit` | 10% | **15%** | 25% | 40% |
| `max_leverage` | 2x | **3x** | 5x | 10x |

設定檔參考：`config/risk_config_optimized.json`

---

## 4. 倉位計算邏輯

`RiskManager.calculate_position_size()` 流程概要：

1. 計算止損距離百分比
2. 依 `max_risk_per_trade` 推算風險基礎倉位
3. Kelly / 波動率 / 流動性 / 相關性 / 集中度調整
4. 取最小值為最終建議倉位

### PositionSizing 主要欄位

| 欄位 | 說明 |
|------|------|
| `recommended_size` | 建議倉位（標的數量） |
| `risk_amount` | 最大預期虧損（USD） |
| `stop_loss_distance` | 止損距離（比例） |
| `risk_reward_ratio` | 風報比 |
| `confidence_score` | 計算信心 (0~1) |

### 範例

```
帳戶 $10,000｜MODERATE｜進場 $76,000｜止損 $73,000
止損距離 ≈ 3.95%
最大虧損 = $10,000 × 2% = $200
建議倉位 ≈ $200 / (3.95% × $76,000) ≈ 0.0666 BTC
```

---

## 5. 投資組合風險評估

`assess_portfolio_risk()` 產出 `PortfolioRisk`，含：

| 指標 | 說明 |
|------|------|
| `var_1day_95` / `var_1day_99` | 日 VaR |
| `expected_shortfall` | CVaR |
| `maximum_drawdown` | 最大回撤 |
| `leverage_ratio` | 實際槓桿 |
| `concentration_risk` | 集中度 |

---

## 6. 風險警報系統

| 嚴重度 | 建議行動 |
|--------|----------|
| `LOW` | 觀察 |
| `MEDIUM` | 縮小倉位 |
| `HIGH` | 減倉 |
| `CRITICAL` | 停止交易、平倉 |

`RiskAlert` 含 `alert_type`、`severity`、`message`、`suggested_action`。

---

## 7. AIConfidenceCalibrator（AI 風控）

檔案：`confidence_calibrator.py`

### 匯入

```python
from bioneuronai.risk_management.confidence_calibrator import get_confidence_calibrator

calibrator = get_confidence_calibrator()  # 單例
```

### 三大功能

1. **Temperature Scaling** — `calibrate_confidence(raw)` 抑制過度自信
2. **Macro-Micro Alignment** — `compute_alignment(macro_sentiment, micro_direction, micro_confidence)`
3. **Fractional Kelly 乘數** — `compute_position_multiplier(ai_confidence, alignment_score, net_odds)`

### 學習相關方法

| 方法 | 用途 | 現況 |
|------|------|------|
| `record_decision(...)` | 進場時記錄校準決策 | ✅ pretrade 有呼叫 |
| `record_outcome(record, pnl_pct)` | 平倉回填結果 | ❌ 主線 A 尚未呼叫 |
| `record_outcome_by_index(index, pnl_pct)` | 依 pretrade index 回填 | ✅ 主線 B 平倉 |
| `refit_temperature(min_samples)` | 重新擬合 T | ✅ `reflect` / `--reflect-every`（需足夠樣本） |

### CLI 觀察方式

執行 pretrade 時終端機會印出：

```
✓ [AI 信心校準] 原始: xx% → 校準後: yy%
✓ [AI 雙層對齊] 宏觀: ... | 微觀: ... → 對齊度: ...
✓ [AI 動態倉位] 乘數: ... | 原倉位: ... → 新倉位: ...
```

---

## 8. 進場前驗核中的風險整合

`python main.py pretrade` 的風險路徑（**實際程式**，非 API 六步驟簡化版）：

```
PreTradeCheckSystem.execute_pretrade_check()
  → 技術檢查（signal_strength 等）
  → 基本面 / 新聞檢查
  → _calculate_risk()
       ├─ RiskCalculation：account_balance × risk_percentage → max_loss_amount
       ├─ 依止損距離算 base position_size
       ├─ [7.5] AIConfidenceCalibrator
       │      ├─ calibrate_confidence
       │      ├─ compute_alignment
       │      ├─ compute_position_multiplier
       │      └─ record_decision + calibration_record_index
       ├─ position_size *= position_multiplier
       └─ 成本效益驗證
  → _configure_order_parameters() → quantity = risk_calc.position_size
  → 整體 assessment（EXECUTE / CAUTIOUS_EXECUTE / REJECT 等）
```

**重點**：
- pretrade **不走** `RiskManager.calculate_position_size()`
- pretrade **有走** `AIConfidenceCalibrator`
- 最終 `order_parameters.quantity` 已含 calibrator 調整

### strategy_fusion 中的對齊度

`AIStrategyFusion.generate_fusion_signal()` 會計算 `signal.alignment_score`（用 event_score 轉 macro_sentiment），供融合信號參考，與 pretrade 的 calibrator 呼叫是**不同入口**、共用同一 calibrator 單例。

---

## 9. 自主迴圈與 TradingEngine 的風控差異

| 場景 | 風控來源 | 倉位如何決定 |
|------|----------|--------------|
| `pretrade` | RiskCalculation + calibrator | `order_parameters.quantity` |
| `trade`（engine） | RiskManager + engine 內邏輯 | engine `execute_trade` |
| `autonomous --execute-paper` | AdaptationController `risk_multiplier` + pretrade quantity | 優先 `order_parameters.quantity × risk_multiplier`；無效時 fallback `paper_notional_fraction` |

2026-06-15 起主線 B 執行層已對齊 pretrade quantity。驗收時請對照 ledger `paper_execution.quantity_source`（`pretrade_quantity` 或 `notional_fraction`）。

AdaptationController 還會依 ledger 連敗、回撤、learning_state 調整 `risk_multiplier` 與 `confidence_floor`（見 `autonomous` 輸出）。

---

## 10. 風險設定檔修改指引

### 設定檔

```
config/risk_config_optimized.json
```

### API 方式（若 API 已啟用）

```http
GET /api/v1/risk/config
PUT /api/v1/risk/config
Content-Type: application/json

{"risk_level": "CONSERVATIVE"}
```

### 程式指定 RiskManager 等級

```python
import asyncio
from bioneuronai.risk_management import RiskManager

async def main():
    rm = RiskManager()
    sizing = await rm.calculate_position_size(
        symbol="BTCUSDT",
        entry_price=76000.0,
        stop_loss_price=73000.0,
        account_balance=10000.0,
        risk_level="CONSERVATIVE",
    )
    print(sizing)

asyncio.run(main())
```

---

## 11. 已知限制（2026-06-15）

| 限制 | 說明 |
|------|------|
| 主線 A 未回填 calibrator | TradingEngine 平倉尚未呼叫 `record_outcome()` |
| reflection 樣本來源 | `reflect` 讀 EpisodicMemory（主線 A），B 線單獨跑可能樣本不足 |
| pretrade ≠ RiskManager | 文件舊版「Step 3 RiskManager 介入」描述不準確，已於本手冊修正 |
| `get_risk_params` 匯出路徑 | 需從 `position_manager` import，非套件頂層 |

主線 B P2/P5 修正詳見 [`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)。

---

## 12. 最佳實踐建議

### 新手

1. 從 `CONSERVATIVE` 或 pretrade 預設 2% 風險比例開始
2. 先用 `pretrade` 看 calibrator 輸出，再用 `autonomous --mode advisor` 看 adaptation
3. 完整學習閉環驗證用 `trade --paper-live`，不要用 autonomous 代替

### 中階

1. 對照 pretrade `quantity` 與 autonomous `paper_execution.quantity`（確認是否已修 P2）
2. 觀察 `adaptive_hub.json` 是否在平倉後更新
3. 注意 `alignment_score` 極低時 fusion 可能攔截信號

### 警報回應

| 等級 | 行動 |
|------|------|
| MEDIUM | 暫停開新倉 |
| HIGH | 減倉 ≥50% |
| CRITICAL | 全平、停止系統、查 ledger / log |

---

## 13. 相關文件

| 文件 | 說明 |
|------|------|
| [04_CLI_OPERATION.md](04_CLI_OPERATION.md) | `pretrade` / `autonomous` / `trade` CLI |
| [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md) | 分析模組操作 |
| [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md) | `/api/v1/pretrade`、`/api/v1/risk/config` |
| [../PROJECT_STATUS.md](../PROJECT_STATUS.md) | 風控相關缺口 P2 |
| [../../src/bioneuronai/risk_management/README.md](../../src/bioneuronai/risk_management/README.md) | 模組級 API 參考 |