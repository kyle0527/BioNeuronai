# 專案現況與進度（2026-07-11）

> 這份文件是當前最準確的**模組進度**記錄。README 是其摘要版。  
> **產品優先級、驗證哲學、預設流程定義**以 [`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md) 為準（2026-07-11 已確認）。  
> 每次有重大架構變更時更新此文件。

**標記慣例（誠實原則）**：
- ✅ 完成：有實作 + 實際運行驗證，或可由正式入口直接驗證
- 🧩 已留擴充點：介面/骨架存在且契約固定，但核心實作未完成
- ❌ 未開始：連介面都沒有

---

## 目錄

0. [已確定方向與本階段重點](#零已確定方向與本階段重點)
   - [0.1 優先順序](#01-優先順序不可顛倒)
   - [0.2 預設入口](#02-預設入口)
   - [0.3 正式驗收](#03-正式驗收必守)
   - [0.4 學習寫入](#04-學習寫入過渡-vs-終局)
   - [0.5 明確延後](#05-明確延後非本階段-p0)
1. [系統真實執行流程](#一系統真實執行流程)
   - [1.1 主線 A：市場 tick → 信號生成](#11-主線-a市場-tick--信號生成)
   - [1.2 信號 → 執行（auto_trade 閘門）](#12-信號--執行auto_trade-閘門)
   - [1.3 平倉 → T2 → LoRA 更新（統一執行層）](#13-平倉--t2--lora-更新統一執行層)
   - [1.4 兩種控制入口、單一模型與執行層](#14-兩種控制入口單一模型與執行層)
2. [各模組準確現況](#二各模組準確現況)
   - [2.1 新聞](#21-新聞模組)
   - [2.2 AI 模型](#22-ai-模型層)
   - [2.3 記憶與在線學習](#23-記憶與在線學習主線-a)
   - [2.4 策略](#24-策略層)
   - [2.5 回測與 RL](#25-回測系統與-rl-訓練)
   - [2.6 自適應與自主迴圈](#26-自適應閉環與自主迴圈)
3. [架構設計決策](#三架構設計決策)
4. [下一步優先工作](#四下一步優先工作)
5. [已知限制與延後項](#五已知限制與延後項)
   - [5.1 自主迴圈限制](#51-自主迴圈與預設流程相關限制)
   - [5.2 正式驗證哲學](#52-正式驗證現行哲學)
   - [5.3 商用周邊延後](#53-商用周邊明確延後非本階段重點)
6. [不應再看的文件（已過時）](#六不應再看的文件已過時)

---

## 零、已確定方向與本階段重點

> 完整論述見 [`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md)。此處為操作與開發對齊用摘要。

### 0.1 優先順序（不可顛倒）

1. **工程自主**：預設流程在幣安虛擬帳戶／Paper 真實時序下能自己跑（決策→下單→平倉→**正確記帳**）。  
2. **穩定確認**：長跑、重啟、卡單、重複進場行為可預期。  
3. **訓練改善**：基線訓練與在線學習開滿，改善決策品質。  
4. **終局**：自主運行時即改善（交易即訓練）——不是永久「只跑不學」。

**當前主戰場 = 階段 1–2（預設流程跑通）**，不是多帳戶／API 認證，也不是先把模型練到有績效再談自主。

### 0.2 預設入口

| 角色 | 入口 | 說明 |
|------|------|------|
| AI 自主主路徑 | `python main.py autonomous`（`--cycles N` + paper 執行參數） | 定時規劃閉環；paper 經 shared TradingEngine |
| 即時 tick 觀測 | `python main.py trade --paper-live` | WebSocket；完整 T0–T2 觀測 |
| 長期大區間 | 下載歷史 → `backtest`／`readiness-gate` | 與日常 paper **互補** |

### 0.3 正式驗收（必守）

| 要 | 不要 |
|----|------|
| 虛擬帳戶／Paper 真實操作 | 以 `tests/`、pytest 當功能完成證明 |
| 長期：先下載歷史再回測 | 用 mock 單元測試假裝時機正確 |
| 看 ledger／runtime／帳戶狀態產物 | 用未訓練模型的 PnL 證明「AI 已可用」 |

### 0.4 學習寫入（過渡 vs 終局）

- **終局**：平倉 → 記錄 → Hub／LoRA → 影響後續。  
- **過渡（流程未穩或 untrained）**：可先「只記錄」或限制寫入，避免噪音／bug 污染狀態；**記帳正確後再開滿**。  
- **正確證據**：決策／進場／出場可對帳——這是邊跑邊學的前提，不是另開的「訓練專案作業」。

### 0.5 明確延後（非本階段 P0）

多帳戶、多租戶、API 認證、rate limit、產品化告警平台、多實例負載均衡等商用周邊：**後續再加**，不阻塞預設流程驗收。

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

> **排序原則（2026-07-11）**：先服務「預設流程跑通」與「記帳正確」，再服務智能改善。  
> 新聞 full、Goal 自動回饋等屬增強，**不應插隊擋住工程自主驗收**。詳見 [`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md)。

### P0（本階段）：預設自主流程跑通與對帳

1. 鎖死預設入口操作說明：`autonomous`（paper）為 AI 自主主路徑；`trade --paper-live` 為 tick 觀測。  
2. 虛擬帳戶真實路徑：進場 → 持倉 → 平倉（含 SL/TP／卡單）可觀察。  
3. 記帳對帳：ledger／ActionRecord／帳戶餘額對同一筆業務。  
4. 學習寫入分級可預期（只記錄 → Hub → LoRA）；未穩前不強制開滿。  
5. 長跑與重啟行為文件化並用真實入口驗收（**非 pytest**）。

### P1：新聞時序聚合（`NewsAdapter.get_direction_bias()`）— 流程通後增強

1. 多事件加權，取代單一主導事件推導。  
2. `implemented_level` 從 `"minimal"` 改為 `"full"`。

### P2：主線 B 執行層對齊（2026-06-15 已實作）

1. ✅ `_execute_paper_order()` 優先採用 pretrade `order_parameters.quantity`（× `risk_multiplier`）；無效時 fallback `paper_notional_fraction`。  
2. ✅ 下單前檢查 `_open_executions` 與 virtual account 持倉，重複進場回傳 `skipped: existing_position`。  
3. ✅ 平倉時依 `risk_calculation.calibration_record_index` 回填 `confidence_calibrator.record_outcome()`。  
4. ✅ Paper 執行委派 `TradingEngine.execute_prepared_order()`；平倉 shared callback 同步引擎學習鏈與 ledger。

### P3：TinyLLM v2 接上交易引擎（2026-07-11 已完成未訓練基線）

1. ✅ `FeaturePipeline.to_v2_patch()` 是 1024→64 的唯一映射。  
2. ✅ `SignalInterpreter` 解碼 v2 65 維輸出。  
3. ✅ TradingEngine、ChatEngine、AutonomousOperator 共用同一模型實例。  
4. ✅ AutonomousOperator 的 paper 執行委派給 TradingEngine，不再維護第二套正式執行器。  
5. ✅ 真實未來 K 線資料收集器輸出 65 維目標與中英說明；舊 512 維自我標註被拒絕。  
6. ❌ 尚缺以完整真實資料完成訓練後的 `model/unified_v2_100m.pth`（**屬階段 3「訓練改善」，不阻擋工程自主驗收**）。

### P4：目標層級自動回饋（`planning/goal_manager.py`）— 非本階段阻塞

1. `recommended_risk_scale` → AdaptationController。  
2. 多時間尺度目標分層。  
3. Sharpe/Sortino（需報酬序列持久化）。

### P5：反思迴圈接入（`planning/reflection_loop.py`）（2026-06-15 已實作）

1. ✅ CLI：`python main.py reflect --sample-size 50`。  
2. ✅ `autonomous --reflect-every N`（`run_forever` 每 N 輪寫入 ledger `reflection_cycle`）。  
3. ⚠️ 樣本仍依 EpisodicMemory 熱緩衝；需 paper 路徑實際累積成交記憶後才有資料可反思。

---

## 五、已知限制與延後項

### 5.1 自主迴圈與預設流程相關限制

1. **重複進場**：2026-06-15 已於 `_execute_paper_order` 檢查；卡單平倉仍依 `max_position_hold_cycles`（CLI：`--max-position-hold-cycles`）。  
2. **quantity fallback**：優先 pretrade quantity；僅在無效時 fallback `paper_notional_fraction`。  
3. **策略身份**：autonomous 平倉常記 `strategy="autonomous_paper"`，Hub 細分策略來源仍粗。  
4. **GoalTracker 只監測不行動**（見 P4；**不阻塞**工程自主）。  
5. **LoRA／Hub 長時間行為**：未以長週期真實 paper 定稿；流程通後再驗「邊跑邊改善」。  
6. **reflection_loop**：已接 CLI；依賴記憶樣本是否真實累積。  
7. **模型能力**：unified v2 路徑可跑，目前 `trained: false`；**只可驗證資料流與工程閉環，不可當智能已達成**。  
8. **資料遷移**：舊 512 維 signal_history 不能當 v2 ground truth。  
9. **新聞語意**：Fusion 層 direction_bias（minimal）與 `_fuse_signals` 的 event_score 加權尚未完全統一。

### 5.2 正式驗證（現行哲學）

| 項目 | 狀態 | 說明 |
|------|------|------|
| CLI／API／手冊式真實操作驗收 | ✅ 正式標準 | 見 `manuals/01_*`、`TESTING_AND_VALIDATION_GUIDE.md`、`CURRENT_DIRECTION.md` |
| 虛擬帳戶／Paper 日常驗證 | ✅ 正式標準 | 幣安虛擬／本機 paper，真實時序 |
| 歷史下載 + 回測長期驗證 | ✅ 正式標準 | 大區間、readiness-gate |
| `tests/` pytest | ⚠️ **非**功能完成標準 | 僅可作開發防呆；**不得**寫成「正式驗收已靠單元測試完成」 |
| Docker 操作驗證 | 可用 | 非本階段唯一入口；本機 Python 3.13 優先 |

### 5.3 商用周邊（明確延後，非本階段重點）

下列項目**有長期價值**，但依 2026-07-11 方向 **後續再加**，**不列入預設流程 P0**：

- API 認證／rate limiting  
- 多帳戶／多租戶  
- 產品化監控告警  
- 訂單重試／dead-letter 平台化  
- SQLite 索引／歸檔強化  
- 多實例／負載均衡  

---

## 六、不應再看的文件（已過時）

| 文件 | 問題 |
|---|---|
| `docs/AGENTIC_PROFIT_UPGRADE_PLAN.md` | 已被 INTEGRATED_RECOMMENDATION.md 取代 |
| `docs/STRATEGY_FUSION_PLAN_B/C/D.md` | 早期探索，已整合進主線 |
| `docs/TECH_DEBT_STATUS_20260513.md` | 2026-05-13 快照 |
| `docs/OPERATION_VALIDATION_REPORT_20260511.md` | 舊版驗證報告 |
| `docs/EXECUTION_PLAN.md` | Step 1–4 已被實作覆蓋（2026-07-11）；殘餘項見本檔 P1/P4 |
| `docs/CODE_FIX_GUIDE.md` | 靜態規範，不代表最新實作狀態 |
| 仍寫「pytest 為正式驗收」「B 線無學習」「v2 為 stub／現役 v1」的段落 | 與 `CURRENT_DIRECTION.md` 衝突；以方向文與本檔第零、五節為準 |

> 方向與優先級：[`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md)。  
> 操作驗證：`manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md`；`OPERATION_VALIDATION_REPORT_20260603.md` 為 v1 模型時期快照（交易所連線與管線走查仍可參考），v2 統一模型的新驗證報告尚待產出。
