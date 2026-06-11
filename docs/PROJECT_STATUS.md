# 專案現況與進度（2026-06-11）

> 這份文件是當前最準確的進度記錄。README 是它的摘要版。
> 每次有重大架構變更時更新此文件。

**標記慣例（誠實原則）**：
- ✅ 完成：有實作 + 有單元測試或實際運行驗證
- 🧩 已留擴充點：介面/骨架存在且契約固定，但核心實作未完成——
  呼叫會明確告知（NotImplementedError / 中性回傳 / 警告 log），不會默默假裝成功
- ❌ 未開始：連介面都沒有

---

## 一、系統真實執行流程

### 1.1 市場 tick → 信號生成（實際執行路徑）

```
WebSocket (Binance ticker stream)
  → on_ticker_update(data)
  → _process_market_data(data, symbol)
      ├─ VirtualAccount.update_price(symbol, close, high, low)   # paper trading 時每 tick 同步
      │       └─ _check_trigger_orders()                          # SL/TP 即時觸發
      ├─ NewsAdapter.get_event_context(symbol)   # event_score, event_context
      └─ generate_trading_signal(...)
              ├─ [T0] _record_decision()          # ActionRecord 快照（已接通）
              ├─ _generate_strategy_signal()
              │       └─ StrategySelector.get_actionable_signal()
              │               ├─ 5 個子策略平行計算
              │               ├─ Meta-Learner 神經網路調整權重
              │               └─ event_score 非對稱過濾（極空/極多時攔截逆勢）
              ├─ InferenceEngine.predict()        # 若模型已載入
              │       └─ TinyLLM v1 (1024→512)
              └─ _fuse_signals()                  # 策略 70% + AI 25% + 新聞 5%
```

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
                                  └─ [T1] ActionRecord 進場快照（已接通）
```

啟用自動交易需要：
- CLI: `python main.py trade --paper-live` 或 `--auto-trade`
- 程式: `engine.enable_auto_trading()`

### 1.3 平倉 → T2 → LoRA 更新（完整迴路）

```
SL/TP 觸發 or 強平
  → VirtualAccount._finalize_fill() / _liquidate_position()
  → _on_position_closed callback（已接通，2026-06-07）
  → TradingEngine._on_paper_close()
  → notify_trade_closed()
        ├─ [T2] ActionRecord.fill_exit()        # pnl_pct, reward 計算
        ├─ EpisodicMemory.push()                # 熱緩衝 or 極端事件冷庫
        ├─ OnlineLearner.record_outcome()
        └─ LoRA 微更新（每 100 筆完整記錄觸發）
```

exit_reason 自動判定：
- `OrderType.STOP_MARKET` → `SL_HIT`
- `OrderType.TAKE_PROFIT_MARKET` → `TP_HIT`
- `_liquidate_position()` → `LIQUIDATION`
- 其他 reduce_only → `MANUAL`

---

## 二、各模組準確現況

### 2.1 新聞模組

| 模組 | 現在的角色 | 說明 |
|---|---|---|
| `CryptoNewsAnalyzer` | 新聞抓取 + 情緒評分 | 計算 event_score (-10 到 +10) |
| `NewsAdapter` | 傳遞 event_context 給策略層 | `get_event_context(symbol)` |
| `EventContract` | 新聞事件衰減與事後驗證 | confirmed_bullish / false_signal 標籤 |
| `PreTradeCheckSystem` | RAG 風控（下單前） | 若發現重大負面新聞則攔截 |
| **新聞作為主信號** | 🧩 **已留擴充點（minimal）** | `NewsAdapter.get_direction_bias()` 已存在（2026-06-11），由 event_score 推導保守 bias；完整版（多事件時序聚合 + 接入 `_fuse_signals()` 作為方向框架）尚未實作 |

**重要**：策略是主信號來源，新聞是「交戰規則」攔截器。原始設計是讓新聞分析近期事件後提出主要方向建議。`get_direction_bias()` 的回傳契約已固定（`{"direction", "strength", "reason"}`），但其 `implemented_level="minimal"` 欄位明確標注目前只是過渡版——呼叫端不可把它當唯一信號。

### 2.2 AI 模型層

| 模型 | 狀態 | 說明 |
|---|---|---|
| TinyLLM v1 | ✅ 可用 | `my_100m_model_trained_20260510.pth`，1024→512 輸入/輸出 |
| TinyLLM v2 | 🧩 架構完成，**未接通推論引擎** | `nlp/tiny_llm_v2.py` 架構與 LoRA 完成；`InferenceEngine.enable_v2_mode()` 只設旗標並發出明確警告，predict() 仍走 v1 路徑（P3） |
| LoRA (v1, `nlp/lora.py`) | ⚠️ 已有但未連接 | 可忽略，v2 已整合 LoRA |
| LoRA (v2, 整合在 TinyLLMv2) | ✅ 已整合 | 骨幹凍結後 0.25%（~203K）參數可訓練 |

### 2.3 記憶與在線學習

| 模組 | 狀態 | 說明 |
|---|---|---|
| `ActionRecord` | ✅ T0/T1/T2 全接通 | VirtualAccount 平倉回調自動觸發 T2 |
| `EpisodicMemory` | ✅ 完成 | 熱緩衝 (50k) + 冷永久金庫（極端事件） |
| `ExtremeEventVault` | ✅ 完成 | 3σ 價格變動 / 爆倉潮 / 高信心巨虧 永久記錄 |
| `OnlineLearner` | ✅ 完成，已接通 | 每 100 筆完整記錄觸發一次 LoRA 微更新 |
| `VirtualAccount` 平倉回調 | ✅ 完成 | SL_HIT / TP_HIT / LIQUIDATION / MANUAL 自動通知 |

### 2.4 策略層

| 模組 | 狀態 | 說明 |
|---|---|---|
| StrategySelector | ✅ 主線 | 5 種子策略動態選擇 |
| AIStrategyFusion | ✅ 可用 | TrendFollowing / SwingTrading / MeanReversion / Breakout / DirectionChange |
| Meta-Learner | ✅ 可用 | 68 維輸入，5 策略 Softmax 權重，17,797 參數 |
| PhaseRouter | ⚠️ 可選 | 需 `strategy_type="phase_router"` |
| RLMetaAgent | ⚠️ 可選 | 需 `strategy_type="rl_fusion"` + 模型檔案存在 |
| self_improvement.py (遺傳算法) | ⚠️ 存在 | 需手動呼叫，未自動化 |

### 2.5 回測系統

| 模組 | 狀態 | 說明 |
|---|---|---|
| Backtest 子系統 | ✅ 可獨立運行 | `backtest/` 目錄 |
| Walk-forward 驗證 | ✅ 架構已建 | `docs/adr/0002-walk-forward-validation.md` |
| **歷史資料 RL 訓練** | 🧩 骨架已建（2026-06-11） | `src/bioneuronai/training/rl_trainer.py`：`RLTrainerConfig` / `HistoricalReplayEnv` / `RLTrainer` 介面契約已固定，所有方法 NotImplementedError（P2） |

### 2.6 自適應閉環與自主迴圈（2026-06-11 新增）

| 模組 | 狀態 | 說明 |
|---|---|---|
| `core/adaptive_hub.py` AdaptiveLearningHub | ✅ 完成 | 策略×幣對×體制 EWMA 績效 → 動態策略權重 / 迴避清單 / 風險倍率；JSON 持久化跨重啟 |
| TradingEngine 平倉 → 權重回饋 | ✅ 完成 | `notify_trade_closed` → hub 記錄 → 重算權重 → 注入 selector；啟動時自動恢復 |
| `core/reward.py` 多目標 reward | ✅ 完成 | 盈虧 × 時間效率 × 不確定性校準 + 過度自信懲罰 + 爆倉懲罰；ActionRecord / EpisodicMemory 統一使用 |
| AutonomousOperator `run_forever` 持續迴圈 | ✅ 完成 | 結算上輪倉位 → 規劃 → 學習狀態注入決策 → 執行 → 依建議間隔等待；STOP 自動停機 |
| outcome 回寫 decision ledger | ✅ 完成 | paper 平倉回調 → `trade_outcome` 紀錄 → AdaptationController 的連敗/回撤/勝率規則真正生效（修復原死碼） |
| AdaptationController 學習狀態規則 | ✅ 完成 | 期望值為負/連敗 → 降風險提門檻；被標記迴避的幣對 → 本輪不執行；`learning_state` 為可選參數向後相容 |
| `planning/goal_manager.py` GoalTracker | 🧩 最小版 | 對照目標輸出 ON_TRACK/AT_RISK/OFF_TRACK + 違反項，每輪寫入 ledger；**只監測記錄，`recommended_risk_scale` 尚未自動回饋到風險參數**；多時間尺度（1h/1d/1w）欄位已留未分層 |
| 學習狀態 provider 擴充點 | ✅ 完成 | `operator.register_state_provider("lora", learner.get_stats)` → 併入每輪 learning_state 記入 ledger |
| 卡單偵測 | 🧩 偵測版 | `max_position_hold_cycles` 超限 → 標記 + 警告 + 寫入紀錄；**自動強制出場尚未實作**（接點在 `_check_stale_positions`） |
| 測試 | ✅ 54 個單元測試 | `tests/`，CI `unit-tests` job 自動執行 |

---

## 三、架構設計決策

### TinyLLM v2 vs v1

v1 使用 1024 維扁平向量輸入（10 類市場特徵）和 512 維輸出（23 維有效，479 維空置）。  
v2 重設計為：
- 輸入：16 根 K 線 × 64 特徵（patch 化，保留時序結構）+ 文字 token + 圖像 token（可選）
- 中間：MoE（6 專家，top-2 路由）+ Cross-attention 文字融合
- 輸出：65 維全監督（方向/信心/槓桿/止損止盈/持倉時間/多時框一致性/20 種形態/不確定性/市場狀態）
- LoRA：整合在模型內，凍結後 0.25% 參數可訓練

v1 → v2 遷移：骨幹 12 層 attention 權重格式相容，但輸入投影層和輸出頭不相容，需重新訓練。

### 新聞架構目標 vs 現狀

**目標**：新聞模組分析當前 + 最近一段時間的新聞 → 提出主要交易方向建議 → 策略信號配合方向執行  
**現狀**：策略信號是主信號，新聞只用於非對稱過濾（極空極多時才介入）

修正路徑：在 `_process_market_data()` 的策略信號生成之前，加入：
```python
news_direction_bias = self.news_adapter.get_direction_bias(symbol)
# bias: {"direction": "LONG"/"SHORT"/"NEUTRAL", "strength": 0-1, "reason": str}
```
然後讓 `_fuse_signals()` 以 news_direction_bias 為主要框架。

### 在線學習 vs 歷史 RL 訓練

這是兩條平行的路：

**在線學習（已完整接通）**：
- 從每筆 paper trading 交易的結果更新 TinyLLM LoRA 權重
- VirtualAccount 平倉 → 回調 → ActionRecord T2 → EpisodicMemory → LoRA 更新
- 每 100 筆完整記錄（T0+T1+T2）觸發一次 gradient update

**歷史資料 RL 訓練（尚未建立）**：
- 目的：用歷史 K 線資料做策略強化學習，驗證信號品質
- 架構：歷史 K 線 → 模擬環境（gym） → 策略 Agent → reward = PnL
- 與 backtest 的差異：RL 是迭代學習（update weights），backtest 是靜態驗證

---

## 四、下一步優先工作（每項的擴充點都已存在，按介面契約實作即可）

### P1：新聞 → 主信號（擴充點：`NewsAdapter.get_direction_bias()`，已有 minimal 版）

已完成（2026-06-11）：方法存在，契約固定
`{"direction": "LONG"/"SHORT"/"NEUTRAL", "strength": 0-1, "reason": str}`，
目前由單一主導事件的 event_score 保守推導（|score| ≥ 3 才給方向）。

剩餘工作：
1. 多事件時序聚合（取代單一主導事件）
2. 修改 `_fuse_signals()`，讓 bias 作為方向框架（而非分數加權 5%）
3. 完成後把 `implemented_level` 從 `"minimal"` 改為 `"full"` 並更新此文件

### P2：歷史 RL 訓練管線（擴充點：`src/bioneuronai/training/rl_trainer.py`，骨架已建）

已完成（2026-06-11）：`RLTrainerConfig` / `HistoricalReplayEnv`（gym 風格
reset/step）/ `RLTrainer`（train/evaluate/export_weights）介面契約固定，
全部 NotImplementedError，測試保證「未實作必須明確報錯」。

剩餘工作（前置依賴皆已存在，列在模組 docstring）：
1. `HistoricalReplayEnv` 接 `backtest/HistoricalDataStream`，reward 用 `core/reward.compute_reward`
2. `RLTrainer.train()` 實作（學習目標三選一：Meta-Learner / LoRA / 遺傳算法）
3. `export_weights()` 落地到 `core/adaptive_hub` 的權重通道

### P3：TinyLLM v2 接上交易引擎（擴充點：`InferenceEngine.enable_v2_mode()`，誠實 stub）

已完成（2026-06-11）：旗標 + 明確警告（「v2 路徑尚未實作，predict 仍走 v1」），
測試保證警告不會被拿掉。

剩餘工作：
1. `FeaturePipeline` 輸出 16×64 patch 格式
2. `SignalInterpreterV2` 解碼 65 維輸出
3. v2 訓練權重檔（架構不相容 v1，輸入投影層和輸出頭需重訓）

### P4：目標層級自動回饋（擴充點：`planning/goal_manager.py`，監測版已可用）

已完成（2026-06-11）：GoalTracker 每輪評估並寫入 ledger。
剩餘工作：
1. `recommended_risk_scale` 自動回饋到 AdaptationController（接點：
   `AutonomousOperator._evaluate_adaptation`）
2. 多時間尺度目標分層（`GoalConfig.horizon` 欄位已留）
3. Sharpe/Sortino 指標（需逐筆報酬序列持久化）

### P5：卡單自動處置（擴充點：`AutonomousOperator._check_stale_positions`，偵測版已可用）

剩餘工作：偵測到超限持倉時下反向 reduce-only 單強制出場，
走 `_on_paper_close` 既有的 outcome 回寫路徑。

---

## 五、已知限制與商用化缺口（誠實清單）

### 自主迴圈已知限制
1. **重複進場**：`run_forever` 每輪若 adaptation 允許就會再下單，未檢查既有持倉
   （同 symbol 會累加倉位並覆寫 `opened_cycle` 追蹤）。實盤化前必須加持倉檢查。
2. **GoalTracker 只監測不行動**（見 P4）。
3. **卡單只偵測不處置**（見 P5）。
4. **LoRA 學習與策略權重閉環是兩條速度不同的迴路**：hub（顯性，每筆生效）
   已閉合；LoRA（隱性，每 100 筆）的更新成效尚未在長時間 paper run 中驗證。
5. **未做長時間連續運行驗證**：閉環的各元件有單元測試，但「跑一週 paper
   trading 權重漂移是否合理」尚未驗證。

### 商用化缺口（非 AI 主線，列入記錄）
| 項目 | 狀態 |
|---|---|
| 單元測試 | ✅ 54 個（2026-06-11 起步），核心交易引擎/推論引擎尚未覆蓋 |
| CI | ✅ unit-tests + Docker 驗證；❌ 無 lint / type check |
| API 認證 / rate limiting | ❌ 所有 endpoint 公開 |
| 監控告警（metrics / Slack / email） | ❌ 只有 log |
| 訂單重試 / dead-letter | ❌ 失敗即丟棄 |
| SQLite 索引 / 歸檔 | ❌ 無索引，無限增長 |
| 多實例 / 負載均衡 | ❌ 單機單實例 |

---

## 六、不應再看的文件（已過時）

| 文件 | 問題 |
|---|---|
| `docs/AGENTIC_PROFIT_UPGRADE_PLAN.md` | 第一版規劃，已被 INTEGRATED_RECOMMENDATION.md 取代 |
| `docs/STRATEGY_FUSION_PLAN_B/C/D.md` | 早期策略探索文件，計劃已整合進主線 |
| `docs/TECH_DEBT_STATUS_20260513.md` | 2026-05-13 快照，部分問題已修正，部分已有新問題 |
| `docs/OPERATION_VALIDATION_REPORT_20260511.md` | 舊版本驗證報告，架構已變動 |
