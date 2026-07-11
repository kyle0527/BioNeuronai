# 專案現況與進度（2026-07-11）

> 這份文件是當前最準確的進度記錄。README 是它的摘要版。
> 每次有重大架構變更時更新此文件。

**標記慣例（誠實原則）**：
- ✅ 完成：有實作 + 實際運行驗證，或可由正式入口直接驗證
- 🧩 已留擴充點：介面/骨架存在且契約固定，但核心實作未完成
- ❌ 未開始：連介面都沒有

---

## 目錄

1. [系統真實執行流程](#一系統真實執行流程)
   - [1.1 主線 A：市場 tick → 信號生成](#11-主線-a市場-tick--信號生成)
   - [1.2 信號 → 執行（auto_trade 閘門）](#12-信號--執行auto_trade-閘門)
   - [1.3 平倉 → T2 → LoRA 更新](#13-平倉--t2--lora-更新)
   - [1.4 雙執行主線對照](#14-雙執行主線對照)
2. [各模組準確現況](#二各模組準確現況)
3. [架構設計決策](#三架構設計決策)
4. [下一步優先工作](#四下一步優先工作)
5. [已知限制與商用化缺口](#五已知限制與商用化缺口)
6. [不應再看的文件](#六不應再看的文件已過時)

---

## 一、系統真實執行流程

### 1.1 主線 A：市場 tick → 信號生成

```
WebSocket (Binance ticker stream)
  → on_ticker_update(data)
  → _process_market_data(data, symbol)
      ├─ VirtualAccount.update_price(symbol, close, high, low)   # paper 時每 tick 同步
      │       └─ _check_trigger_orders()                          # SL/TP 即時觸發
      ├─ NewsAdapter.get_event_context(symbol)   # event_score, event_context
      └─ generate_trading_signal(...)
              ├─ [T0] _record_decision()          # ActionRecord 快照
              ├─ _generate_strategy_signal()
              │       └─ StrategySelector.get_actionable_signal()
              │               ├─ 5 個子策略平行計算
              │               ├─ Meta-Learner 神經網路調整權重
              │               ├─ generate_fusion_signal()
              │               │       └─ get_direction_bias() 方向框架（minimal，攔截逆勢共識）
              │               └─ event_score 非對稱過濾（極空/極多時攔截逆勢）
              ├─ InferenceEngine.predict_with_explanation()
              │       # unified v2：數值 + 中英文脈絡 → 決策 + 說明
              └─ _fuse_signals()                  # 策略 70% + AI 25% + event_score 5%
```

> 注意：新聞 **direction_bias** 在 `generate_fusion_signal()` 層生效；
> `TradingEngine._fuse_signals()` 仍使用 **event_score** 加權，兩者尚未統一。

### 1.2 信號 → 執行（auto_trade 閘門）

```
_handle_trading_signal(signal)
  │
  ├─ signal.action == "HOLD" → 不做任何事
  │
  └─ auto_trade == False (預設) → 只印 log，不下單
       auto_trade == True  → execute_trade(signal)
                                  ├─ 新聞風控檢查
                                  ├─ 計算倉位
                                  ├─ 成本效益驗證
                                  ├─ connector.place_order()
                                  └─ [T1] ActionRecord 進場快照
```

啟用自動交易：
- CLI: `python main.py trade --paper-live` 或 `--auto-trade`
- 程式: `engine.enable_auto_trading()`

### 1.3 平倉 → T2 → LoRA 更新（統一執行層）

```
SL/TP 觸發 or 強平
  → VirtualAccount._on_position_closed callback
  → TradingEngine._on_paper_close()
  → notify_trade_closed()
        ├─ [T2] ActionRecord.fill_exit()
        ├─ EpisodicMemory.push()
        ├─ OnlineLearner.record_outcome()
        ├─ LoRA 微更新（每 100 筆完整記錄觸發）
        └─ AdaptiveLearningHub.record_trade() → 重注入 selector 權重
```

### 1.4 兩種控制入口、單一模型與執行層

`trade` 與 `autonomous` 保留不同的驅動方式，但不再各自擁有模型或 paper connector。

| 維度 | 主線 A：TradingEngine | 主線 B：AutonomousOperator |
|------|----------------------|---------------------------|
| CLI 入口 | `main.py trade` | `main.py autonomous` |
| 驅動 | WebSocket 即時 tick | `run_forever` 定時迴圈 |
| 信號/決策 | StrategySelector + shared InferenceEngine | Plan → shared InferenceEngine → Pretrade → AdaptationController |
| Paper 執行 | `TradingEngine.execute_prepared_order()` | 委派 `TradingEngine.execute_prepared_order()` |
| 模型 | `unified_v2_100m` shared instance | 同一個 shared instance |
| Connector | TradingEngine 持有 | 使用同一個 TradingEngine connector |
| ActionRecord | ✅ T0/T1/T2 | 平倉透過 shared callback 同步回寫 |
| EpisodicMemory | ✅ | 透過 TradingEngine shared callback |
| OnlineLearner / LoRA | ✅ | 透過 TradingEngine shared callback |
| Decision Ledger | ❌ | ✅ append-only JSONL |
| AdaptiveLearningHub | ✅ | ✅ |
| Pretrade calibrator | 經 pretrade 間接使用 | ✅ 計算 alignment / quantity |
| 執行層採用 pretrade quantity | N/A（engine 自有倉位邏輯） | ✅ 優先 `order_parameters.quantity`（2026-06-15）；無效時 fallback `paper_notional_fraction` |
| 持倉檢查再進場 | base_strategy 有檢查 | ✅ 2026-06-15 檢查 virtual account；跳過時 `skipped=existing_position` |

**Autonomous 平倉路徑**：
```
VirtualAccount 平倉回調
  → AutonomousOperator._on_shared_paper_close()
      ├─ TradingEngine._on_paper_close() → T2 / memory / LoRA / adaptive hub
      └─ AutonomousOperator._on_paper_close() → decision ledger / calibrator
```

---

## 二、各模組準確現況

### 2.1 新聞模組

| 模組 | 現在的角色 | 說明 |
|---|---|---|
| `CryptoNewsAnalyzer` | 新聞抓取 + 情緒評分 | event_score (-10 到 +10) |
| `NewsAdapter` | event_context + direction_bias | `get_event_context()` / `get_direction_bias()` |
| `EventContract` | 新聞事件衰減與事後驗證 | confirmed_bullish / false_signal |
| `PreTradeCheckSystem` | RAG 風控（下單前） | 重大負面新聞攔截 |
| **方向框架（minimal）** | ✅ 完成（2026-06-12） | `generate_fusion_signal()` 以 direction_bias 攔截逆勢共識 |
| **時序聚合（full）** | 🧩 P1 | 多事件加權，尚未實作 |

### 2.2 AI 模型層

| 模型 | 狀態 | 說明 |
|---|---|---|
| Unified TinyLLM v2 | ✅ 未訓練端到端已接通 | 98,403,413 參數；16×64 數值 + 中英文脈絡 → 65 維決策 + 說明 logits |
| v2 trained checkpoint | ❌ 尚未產生 | `active_model.json` 明確標記 `trained: false`；目前固定 seed 初始化只供運作驗證 |
| LoRA (v2) | ✅ 已整合於模型內 | 由同一 checkpoint 與 OnlineLearner 更新，不再有獨立文字模型 |
| TinyLLM v1 / MLP | 📦 已封存 | 位於 `archived/legacy_v1_20260711/`，現役 loader 明確拒絕 |

### 2.3 記憶與在線學習（主線 A）

| 模組 | 狀態 | 說明 |
|---|---|---|
| `ActionRecord` | ✅ T0/T1/T2 全接通 | VirtualAccount 平倉回調自動觸發 T2 |
| `EpisodicMemory` | ✅ 完成 | 熱緩衝 (50k) + 冷永久金庫 |
| `OnlineLearner` | ✅ 已接通 | 每 100 筆完整記錄觸發 LoRA 微更新 |
| `VirtualAccount` 平倉回調 | ✅ 完成 | SL_HIT / TP_HIT / LIQUIDATION / MANUAL |

### 2.4 策略層

| 模組 | 狀態 | 說明 |
|---|---|---|
| StrategySelector | ✅ 主線 | 5 子策略 + Meta-Learner 融合 |
| AIStrategyFusion | ✅ 可用 | 含 direction_bias 方向框架 |
| Meta-Learner | ✅ 可用 | 68 維輸入，17,797 參數 |
| PhaseRouter | ⚠️ 可選 | `strategy_type="phase_router"` |
| RLMetaAgent | ⚠️ 可選 | `strategy_type="rl_fusion"` + 模型檔 |
| self_improvement.py | ⚠️ 存在 | 需手動呼叫 |

### 2.5 回測系統與 RL 訓練

| 模組 | 狀態 | 說明 |
|---|---|---|
| Backtest 子系統 | ✅ 可獨立運行 | `backtest/` |
| Walk-forward 驗證 | ✅ 架構已建 | `docs/adr/0002-walk-forward-validation.md` |
| **歷史資料 RL 訓練** | ✅ 完成（2026-06-12） | `training/rl_trainer.py`：`HistoricalReplayEnv` + `RLTrainer`（REINFORCE） |

### 2.6 自適應閉環與自主迴圈

| 模組 | 狀態 | 說明 |
|---|---|---|
| `AdaptiveLearningHub` | ✅ 完成 | 策略×幣對×體制 EWMA；JSON 持久化 |
| TradingEngine 平倉 → hub | ✅ 完成 | notify_trade_closed → 重注入 selector |
| `core/reward.py` | ✅ 完成 | 多目標 reward，ActionRecord / EpisodicMemory 統一使用 |
| `AutonomousOperator.run_forever` | ✅ 完成 | 結算 → 規劃 → 執行 → 等待 → 下一輪 |
| outcome 回寫 ledger | ✅ 完成 | 平倉 → trade_outcome → AdaptationController 規則生效 |
| `AdaptationController` | ✅ 完成 | 連敗/回撤/學習狀態 → 降風險或暫停 |
| `GoalTracker` | 🧩 最小版 | 只監測記錄，風險自動回饋未實作 |
| 學習狀態 provider | ✅ 完成 | `register_state_provider("lora", ...)` |
| **卡單自動平倉** | ✅ 完成（2026-06-12） | `max_position_hold_cycles` 超限 → reduce-only 強制出場 |

---

## 三、架構設計決策

### TinyLLM v2 vs v1

v1：1024 維扁平輸入，512 維輸出（23 維有效，479 維空置）。
v2：16×64 patch + 文字/圖像（可選），65 維全監督，MoE + LoRA。
v1 → v2 遷移需重訓輸入投影層與輸出頭。

### 新聞方向偏好框架

**目標**：新聞提出主要方向建議，策略在框架內執行。
**現狀（2026-06-12）**：`get_direction_bias()` + `generate_fusion_signal()` 方向框架已接通（minimal）。
**剩餘**：多事件時序聚合；`TradingEngine._fuse_signals()` 與 StrategyFusion 層語意統一。

### 在線學習 vs 歷史 RL 訓練

**在線學習（主線 A，已接通）**：
- Paper 平倉 → ActionRecord T2 → EpisodicMemory → LoRA（每 100 筆）

**歷史 RL 訓練（離線，2026-06-12 完成）**：
- `HistoricalReplayEnv` → `RLTrainer` → 更新 `MetaLearnerModel`

---

## 四、下一步優先工作

### P1：新聞時序聚合（`NewsAdapter.get_direction_bias()`）

1. 多事件加權，取代單一主導事件推導。
2. `implemented_level` 從 `"minimal"` 改為 `"full"`。

### P2：主線 B 執行層對齊（2026-06-15 已實作）

1. ✅ `_execute_paper_order()` 優先採用 pretrade `order_parameters.quantity`（× `risk_multiplier`）；無效時 fallback `paper_notional_fraction`。
2. ✅ 下單前檢查 `_open_executions` 與 virtual account 持倉，重複進場回傳 `skipped: existing_position`。
3. ✅ 平倉時依 `risk_calculation.calibration_record_index` 回填 `confidence_calibrator.record_outcome()`。

### P3：TinyLLM v2 接上交易引擎（2026-07-11 已完成未訓練基線）

1. ✅ `FeaturePipeline.to_v2_patch()` 是 1024→64 的唯一映射。
2. ✅ `SignalInterpreter` 解碼 v2 65 維輸出。
3. ✅ TradingEngine、ChatEngine、AutonomousOperator 共用同一模型實例。
4. ✅ AutonomousOperator 的 paper 執行委派給 TradingEngine，不再維護第二套正式執行器。
5. ✅ 真實未來 K 線資料收集器輸出 65 維目標與中英說明；舊 512 維自我標註被拒絕。
6. ❌ 尚缺以完整真實資料完成訓練後的 `model/unified_v2_100m.pth`。

### P4：目標層級自動回饋（`planning/goal_manager.py`）

1. `recommended_risk_scale` → AdaptationController。
2. 多時間尺度目標分層。
3. Sharpe/Sortino（需報酬序列持久化）。

### P5：反思迴圈接入（`planning/reflection_loop.py`）（2026-06-15 已實作）

1. ✅ CLI：`python main.py reflect --sample-size 50`。
2. ✅ `autonomous --reflect-every N`（`run_forever` 每 N 輪寫入 ledger `reflection_cycle`）。
3. ⚠️ 仍依 EpisodicMemory 熱緩衝；主線 B 本身不寫 memory，需主線 A paper-live 累積樣本後才有資料。

---

## 五、已知限制與商用化缺口（誠實清單）

### 自主迴圈已知限制

1. **重複進場**：2026-06-15 已於 `_execute_paper_order` 檢查；卡單平倉仍依 `max_position_hold_cycles`（CLI：`--max-position-hold-cycles`）。
2. **執行脫節**：2026-06-15 已優先採 pretrade quantity；僅在 quantity 無效時 fallback。
3. **策略身份**：autonomous 平倉一律記 `strategy="autonomous_paper"`，hub 無法細分策略來源。
4. **GoalTracker 只監測不行動**（見 P4）。
5. **LoRA 成效未長時間驗證**：hub 每筆生效；LoRA 每 100 筆，漂移合理性未驗證。
6. **reflection_loop**：已接入 CLI `reflect` 與 `autonomous --reflect-every`；樣本仍來自 EpisodicMemory（主線 A）。
7. **模型能力**：統一 v2 已能完整運作，但目前未訓練；輸出只可驗證資料流，不代表語言或交易表現。
8. **資料遷移**：既有 512 維 signal_history 是 v1 模型輸出，不能直接當 v2 ground truth；需重新收集真實未來結果資料。

### 商用化缺口（非 AI 主線）

- **正式驗證**：✅ Docker + CLI/API 手冊驗收；✅ `tests/` pytest 套件（與遠端 main 對齊）
- **CI**：✅ Docker 驗證 + `unit-tests` job（`pytest tests -q`）
- **API 認證 / rate limiting**：❌
- **監控告警**：❌ 只有 log
- **訂單重試 / dead-letter**：❌
- **SQLite 索引 / 歸檔**：❌
- **多實例 / 負載均衡**：❌

---

## 六、不應再看的文件（已過時）

| 文件 | 問題 |
|---|---|
| `docs/AGENTIC_PROFIT_UPGRADE_PLAN.md` | 已被 INTEGRATED_RECOMMENDATION.md 取代 |
| `docs/STRATEGY_FUSION_PLAN_B/C/D.md` | 早期探索，已整合進主線 |
| `docs/TECH_DEBT_STATUS_20260513.md` | 2026-05-13 快照 |
| `docs/OPERATION_VALIDATION_REPORT_20260511.md` | 舊版驗證報告 |
| `docs/CODE_FIX_GUIDE.md` | 靜態規範，不代表最新實作狀態 |

> 較新的操作驗證請看 `OPERATION_VALIDATION_REPORT_20260603.md` 與 `manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md`。
