# BioNeuronai 核心交易系統

> 路徑：`src/bioneuronai/`
> 套件版本：v2.1（`pyproject.toml`）
> 更新日期：2026-06-15

`bioneuronai` 是交易系統主體，負責把資料接入、分析、策略選擇、AI 融合、風險管理、交易規劃、API 與 CLI 串成可操作的主流程。

---

## 目錄

1. [子模組導覽](#子模組導覽)
2. [雙執行主線](#雙執行主線)
3. [策略主線模式](#策略主線模式)
4. [分層概念](#分層概念)
5. [文件鏈](#文件鏈)

---

## 子模組導覽

| 模組 | 層級定位 | 詳細文件 |
|------|----------|----------|
| `data/` | Layer 0：交易所、paper connector、DB、新聞 fetcher | [data README](data/README.md) |
| `core/` | Layer 1：TradingEngine、InferenceEngine、AdaptiveHub | [core README](core/README.md) |
| `risk_management/` | Layer 1：RiskManager + AIConfidenceCalibrator | [risk README](risk_management/README.md) |
| `strategies/` | Layer 2：selector、fusion、Meta-Learner | [strategies README](strategies/README.md) |
| `planning/` | Layer 3：plan、pretrade、autonomous、reflection | [planning README](planning/README.md) |
| `trading/` | Layer 3：VirtualAccount、成交事實 | [trading README](trading/README.md) |
| `memory/` | Layer 1：EpisodicMemory（主線 A 學習） | — |
| `training/` | 離線：歷史 RL 訓練管線 | — |
| `analysis/` | Layer 4：新聞、特徵、regime | [analysis README](analysis/README.md) |
| `api/` | 對外：FastAPI | [api README](api/README.md) |
| `cli/` | 對外：CLI 入口 | [cli README](cli/README.md) |
| `models/` | legacy checkpoint 相容 | [models README](models/README.md) |

---

## 雙執行主線

| | 主線 A | 主線 B |
|---|---|---|
| 模組 | `core/trading_engine.py` | `planning/autonomous_operator.py` |
| CLI | `main.py trade` | `main.py autonomous` |
| 學習 | LoRA + EpisodicMemory | Ledger + AdaptiveHub |

詳見 [`docs/PROJECT_STATUS.md`](../../docs/PROJECT_STATUS.md) 1.4。

---

## 策略主線模式

由 `strategy_type` 指定（皆經 TradingEngine）：

```text
[fusion — 預設]
TradingEngine -> StrategySelector -> AIStrategyFusion -> risk / execution

[phase_router]
TradingEngine -> TradingPhaseRouter -> risk / execution

[rl_fusion]
TradingEngine -> StrategySelector -> RLMetaAgent -> risk / execution
```

`fusion` 為預設正式主線。`planning/` 的自主迴圈是**平行**編排路徑，不取代上述模式。

---

## 分層概念

```text
Layer 4  analysis        新聞、關鍵字、特徵、regime
Layer 3  planning        計劃、pretrade、autonomous、reflection
Layer 3  trading         虛擬帳戶、paper 成交狀態
Layer 2  strategies      策略選擇、fusion、競技/路由（研究）
Layer 1  core/risk/memory  引擎、推理、風控、記憶
Layer 0  data/schemas    外部資料、DB、API
```

---

## 文件鏈

1. 本文件 → 各子模組 README
2. 現況權威 → [`docs/PROJECT_STATUS.md`](../../docs/PROJECT_STATUS.md)
3. 架構導覽 → [`docs/ARCHITECTURE_OVERVIEW.md`](../../docs/ARCHITECTURE_OVERVIEW.md)

---

> 上層目錄：[src README](../README.md)