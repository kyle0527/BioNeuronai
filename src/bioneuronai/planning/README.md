# 規劃模組 (Planning)

> 路徑：`src/bioneuronai/planning/`
> 更新日期：2026-07-11
> 架構層級：Layer 3 — 高階規劃與交易前檢查

`planning` 負責把分析結果整理成可執行的交易計畫、進場前檢查結論，以及自主運行編排；模型與訂單執行統一委派給共享 `InferenceEngine` 與 `TradingEngine`。

---

## 目錄

1. [模組定位](#模組定位)
2. [與 TradingEngine 的關係](#與-tradingengine-的關係)
3. [實際結構](#實際結構)
4. [主流程](#主流程)
5. [核心檔案](#核心檔案)
6. [已知斷點與擴充點](#已知斷點與擴充點)
7. [對外匯出](#對外匯出)
8. [維護邊界](#維護邊界)

---

## 模組定位

`planning` 目前承接 5 類工作：

1. 10 步驟交易計畫建立
2. 市場環境分析與風險摘要
3. 交易對篩選
4. 單筆交易前檢查（含 AI 信心校準倉位）
5. 自主運行編排、自適應控制與反思學習（2026-06-15 已接入 CLI / 自主迴圈）

相鄰模組邊界：

| 模組 | 關係 |
|------|------|
| `analysis/` | 新聞、關鍵字、daily report |
| `strategies/` | 策略選擇與策略訊號 |
| `trading/` | 虛擬帳戶與成交事實 |
| `risk_management/` | `confidence_calibrator` 被 pretrade 呼叫 |
| `memory/` | `reflection_loop` 讀取由統一 TradingEngine 平倉回調寫入的 EpisodicMemory |

---

## 與 TradingEngine 的關係

| 維度 | TradingEngine | AutonomousOperator |
|------|------------------------|------------------------------|
| CLI | `main.py trade` | `main.py autonomous` |
| 模型 | shared `unified_v2_100m` | 同一 shared instance |
| 執行 | 唯一 connector / order executor | 委派給 TradingEngine |
| 學習閉環 | ActionRecord → LoRA | shared callback + Ledger → AdaptiveHub |
| Pretrade | 可獨立呼叫 | 每輪必經 |

詳見 [`docs/PROJECT_STATUS.md`](../../../docs/PROJECT_STATUS.md) 1.4。

---

## 實際結構

```text
planning/
├── __init__.py              # PEP 562 延遲載入
├── plan_controller.py       # 10 步驟交易計畫
├── market_analyzer.py       # 市場條件整合分析
├── pair_selector.py         # 24h 行情篩選交易對
├── pretrade_automation.py   # 盤前檢查 + calibrator 動態倉位
├── autonomous_operator.py   # run_once / run_forever 自主迴圈
├── adaptation_controller.py # 連敗/回撤/學習狀態規則
├── decision_ledger.py       # append-only JSONL 決策紀錄
├── goal_manager.py          # 目標追蹤（監測版）
├── reflection_loop.py       # 反思循環（✅ CLI reflect + autonomous --reflect-every）
└── README.md
```

檔案對照：
1. [plan_controller.py](plan_controller.py)
2. [market_analyzer.py](market_analyzer.py)
3. [pair_selector.py](pair_selector.py)
4. [pretrade_automation.py](pretrade_automation.py)
5. [autonomous_operator.py](autonomous_operator.py)
6. [adaptation_controller.py](adaptation_controller.py)
7. [decision_ledger.py](decision_ledger.py)
8. [goal_manager.py](goal_manager.py)
9. [reflection_loop.py](reflection_loop.py)

---

## 主流程

### 交易計畫路徑

```text
TradingPlanController
  -> MarketAnalyzer
  -> StrategySelector / PairSelector
  -> RiskManager
  -> 10-step plan result
```

### 單筆進場前檢查路徑

```text
PreTradeCheckSystem
  -> BinanceFuturesConnector
  -> NewsAdapter (RAG 事件上下文)
  -> TradingRetriever (RAG 檢索層)
  -> TradingCostCalculator
  -> AIConfidenceCalibrator（校準信心 + 對齊度 + 倉位乘數）
  -> risk / liquidity / news / order checks
```

### 自主運行路徑

```text
AutonomousOperator.run_forever
  -> _settle_open_positions()          # 更新持倉、觸發 SL/TP
  -> TradingPlanController
  -> shared InferenceEngine（數值決策 + 中英說明）
  -> PreTradeCheckSystem（多候選 symbol）
  -> AdaptationController（含 learning_state）
  -> DecisionLedger.append()
  -> _execute_paper_order()（若 execute_paper 且允許）
       -> 優先 pretrade quantity × risk_multiplier
       -> 既有持倉則 skipped（existing_position）
       -> TradingEngine.execute_prepared_order()
       -> TradingEngine 持有的唯一 PaperBinanceFuturesConnector
  -> _on_shared_paper_close()
       -> TradingEngine T2 / EpisodicMemory / LoRA
       -> ledger / calibrator / AdaptiveLearningHub
  -> _maybe_run_reflection()（若 reflect_every_cycles > 0）
```

### 反思學習路徑（2026-06-15 已接入）

```text
# 獨立 CLI
python main.py reflect --sample-size 50

# 或自主迴圈排程（需 --cycles > 1）
autonomous --reflect-every N

AIReflectionLoop.run_reflection_cycle()
  -> EpisodicMemory.sample_hot()
  -> 虧損特徵分析
  -> AIConfidenceCalibrator.refit_temperature()
  -> ledger reflection_cycle（自主迴圈觸發時）
  -> learning_report_*.json
```

⚠️ 初期仍可能因 EpisodicMemory 真實成交樣本不足而跳過 refit。

---

## 核心檔案

### `pretrade_automation.py`

- 主類：`PreTradeCheckSystem`
- 主入口：`execute_pretrade_check(symbol, intended_action)`
- 已接通 `get_confidence_calibrator()`：計算校準信心、宏觀微觀對齊度、動態倉位乘數
- 輸出 `order_parameters.quantity`（已含 calibrator 調整）
- `RiskCalculation.calibration_record_index`：供平倉回填 `record_outcome_by_index`

### `autonomous_operator.py`

- 主類：`AutonomousOperator`
- `run_once()` / `run_forever()`：持續 observe → plan → pretrade → adapt → ledger
- `_resolve_paper_quantity()`：優先 pretrade quantity，fallback `paper_notional_fraction`
- `_has_open_position()`：重複進場跳過，ledger 記 `skipped=true`
- `_check_stale_positions()`：卡單自動 reduce-only 平倉（`--max-position-hold-cycles`）
- `_on_paper_close()`：outcome 回寫 ledger + hub + calibrator
- `_maybe_run_reflection()`：`reflect_every_cycles` 排程
- `register_state_provider()`：接入 LoRA 等外部學習統計

### `reflection_loop.py`

- 主類：`AIReflectionLoop`
- 主入口：`run_reflection_cycle(k=50)`
- CLI：`python main.py reflect`
- 自主排程：`AutonomousOperatorConfig.reflect_every_cycles`
- 依賴 `EpisodicMemory`（主線 A 平倉才會寫入）

### `adaptation_controller.py`

- 依 plan、pretrade、ledger、learning_state 調整 risk_multiplier / confidence_floor / next_interval
- 不直接修改模型權重

### `decision_ledger.py`

- JSONL 路徑預設：`data/bioneuronai/planning/autonomous/decision_ledger.jsonl`
- record type：`autonomous_cycle`、`trade_outcome`、`reflection_cycle`

---

## 已知斷點與擴充點

| 斷點 | 說明 | 優先級 |
|------|------|--------|
| ~~執行層忽略 pretrade quantity~~ | 2026-06-15 已優先採用 | — |
| ~~未檢查既有持倉~~ | 2026-06-15 已檢查 | — |
| ~~calibrator outcome 未回填~~ | 2026-06-15 B 線平倉已回填 | — |
| ~~reflection_loop 未接入~~ | 2026-06-15 CLI + `--reflect-every` | — |
| reflection 樣本來源 | 仍讀 EpisodicMemory，B 線單獨跑樣本可能不足 | P5 後續 |
| GoalTracker 不行動 | 只寫 ledger | P4 |

---

## 對外匯出

```python
from bioneuronai.planning import (
    AdaptationController,
    AutonomousOperator,
    AutonomousOperatorConfig,
    DecisionLedger,
    TradingPlanController,
    MarketAnalyzer,
    PairSelector,
    PreTradeCheckSystem,
)

# 反思迴圈（尚未列入 __all__，需直接 import）
from bioneuronai.planning.reflection_loop import AIReflectionLoop
```

---

## 維護邊界

1. 自主運行層只編排計畫，不複製模型與訂單執行責任。
2. Paper 執行必須經 `TradingEngine.execute_prepared_order()` 與其唯一 connector。
3. 不在此層重複記錄 `analysis/`、`strategies/`、`core/` 內部細節。

---

> 上層目錄：[BioNeuronai README](../README.md)｜現況：[PROJECT_STATUS](../../../docs/PROJECT_STATUS.md)
