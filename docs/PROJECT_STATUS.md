# 專案現況與進度（2026-06-07）

> 這份文件是當前最準確的進度記錄。README 是它的摘要版。
> 每次有重大架構變更時更新此文件。

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
| **新聞作為主信號** | **規劃中，尚未實作** | 目前新聞是過濾器，不是決策者 |

**重要**：策略是主信號來源，新聞是「交戰規則」攔截器。原始設計是讓新聞分析近期事件後提出主要方向建議，目前的實作方向相反。這是 P1 待修正的架構缺口。

### 2.2 AI 模型層

| 模型 | 狀態 | 說明 |
|---|---|---|
| TinyLLM v1 | ✅ 可用 | `my_100m_model_trained_20260510.pth`，1024→512 輸入/輸出 |
| TinyLLM v2 | ✅ 架構完成，未接通 | `nlp/tiny_llm_v2.py`，三模態 + MoE + 65 維全監督 |
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
| **歷史資料 RL 訓練** | ❌ 缺失 | 需要建立：歷史 K 線 → RL 環境 → 策略驗證管線 |

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

## 四、下一步優先工作

### P1：修正新聞架構（新聞 → 主信號）

在 `NewsAdapter` 新增 `get_direction_bias(symbol)` 方法：
```python
# 回傳格式
{"direction": "LONG"/"SHORT"/"NEUTRAL", "strength": 0-1, "reason": str}
```
修改 `_fuse_signals()`，讓新聞偏好作為方向框架（而非分數加權 5%）。

### P2：建立歷史 RL 訓練管線

- 建立 `src/bioneuronai/training/rl_trainer.py`
- 使用已有的 backtest 歷史資料作為訓練環境
- 連接到 `self_improvement.py` 的遺傳算法

### P3：TinyLLM v2 接上交易引擎

- 修改 `InferenceEngine` 支援 v2 的 patch 輸入格式
- 遷移策略：v1 和 v2 並存，v2 在有訓練好的模型後接管

---

## 五、不應再看的文件（已過時）

| 文件 | 問題 |
|---|---|
| `docs/AGENTIC_PROFIT_UPGRADE_PLAN.md` | 第一版規劃，已被 INTEGRATED_RECOMMENDATION.md 取代 |
| `docs/STRATEGY_FUSION_PLAN_B/C/D.md` | 早期策略探索文件，計劃已整合進主線 |
| `docs/TECH_DEBT_STATUS_20260513.md` | 2026-05-13 快照，部分問題已修正，部分已有新問題 |
| `docs/OPERATION_VALIDATION_REPORT_20260511.md` | 舊版本驗證報告，架構已變動 |
