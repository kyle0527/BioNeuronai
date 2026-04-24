# 方案 D：深度強化學習 Agent（Deep RL Fusion Agent）

> 建立日期：2026-04-24  
> 版本：v1.0  
> 系列文件：策略融合路線圖 [4/4]  
> 前置文件：`STRATEGY_FUSION_ROADMAP_OVERVIEW.md`

---

## 一、核心概念

### 1.1 強化學習的思維轉換

前面三個方案（A、B、C）都是**監督式思維**：人類先決定什麼是好的融合，然後用規則或ML模型去執行。

強化學習（RL）是完全不同的範式：

> **「不告訴 AI 怎麼融合，讓它在一個環境中行動，從結果（盈虧）學習最優策略。」**

```
傳統方法（方案 A/B/C）：
  人類定義規則/標籤 → 模型執行

強化學習（方案 D）：
  Agent 自由行動 → 市場給予獎勵 → Agent 更新策略
  不斷循環，直到找到能穩定賺錢的行為模式
```

### 1.2 為什麼 RL 在交易中有潛力

1. **無需標籤**：不需要人工定義「正確答案」，只需定義「好的結果」（正的 Sharpe）
2. **可以學到非直觀規律**：例如「當所有策略都看多時，反而做空」（Fade the Crowd）
3. **時序依賴**：RL 的狀態天然包含歷史訊息，適合金融時序
4. **多目標最優化**：一個獎勵函數可以同時最優化報酬、風險、回撤

### 1.3 BioNeuronAI 已有的 RL 基礎

`src/bioneuronai/strategies/rl_fusion_agent.py` 已有完整骨架：

```
✅ StrategyFusionEnv（gymnasium 環境）
  - observation_space 定義（策略信號 × N + 市場特徵 + 持倉狀態）
  - action_space 定義（MultiDiscrete: 方向 × 倉位大小）
  - step()、reset()、_get_observation() 方法
  - _calculate_reward() 基礎獎勵計算

✅ RLFusionAgent 類別
  - PPO 訓練流程骨架
  - save/load 方法
  - predict() 推論

⚠️ 尚未完成：
  - 真實市場資料接入（目前用假資料）
  - 策略信號的即時計算與傳入
  - 完整獎勵函數（Sharpe、最大回撤）
  - 訓練資料生成流程
  - 與 AIStrategyFusion 的整合
```

---

## 二、技術架構設計

### 2.1 觀察空間（State Space）

Agent 在每個時間步能看到的全部資訊：

```
觀察向量（共約 27 個維度）：

─────────────────────────────────────────────
A. 各策略信號（每策略 3 個數值，共 4 策略 = 12 維）
─────────────────────────────────────────────
  trend_following_direction:   -1 / 0 / +1
  trend_following_strength:    0.0 ~ 1.0
  trend_following_confidence:  0.0 ~ 1.0

  mean_reversion_direction:    -1 / 0 / +1
  mean_reversion_strength:     0.0 ~ 1.0
  mean_reversion_confidence:   0.0 ~ 1.0

  swing_trading_direction:     -1 / 0 / +1
  swing_trading_strength:      0.0 ~ 1.0
  swing_trading_confidence:    0.0 ~ 1.0

  breakout_direction:          -1 / 0 / +1
  breakout_strength:           0.0 ~ 1.0
  breakout_confidence:         0.0 ~ 1.0

─────────────────────────────────────────────
B. 市場特徵（8 維）
─────────────────────────────────────────────
  price_normalized:            0.0 ~ 1.0（窗口內正規化）
  volatility:                  0.0 ~ 1.0（ATR 比值正規化）
  trend_strength:              -1.0 ~ 1.0（ADX方向化）
  volume_ratio:                0.0 ~ 2.0（相對成交量）
  news_event_score:            -1.0 ~ 1.0
  time_of_day:                 0.0 ~ 1.0（UTC 小時 / 24）
  market_regime:               0.0 ~ 1.0（體制 label 正規化）
  bid_ask_spread:              0.0 ~ 1.0（可選，若有資料）

─────────────────────────────────────────────
C. 當前持倉狀態（4 維）
─────────────────────────────────────────────
  position_type:               -1 / 0 / +1（空/無/多）
  position_size:               0.0 ~ 1.0
  unrealized_pnl_pct:          -0.1 ~ 0.1（浮動損益%）
  bars_since_entry:            0 ~ 1.0（正規化）

─────────────────────────────────────────────
D. 帳戶狀態（3 維）
─────────────────────────────────────────────
  equity_normalized:           0.0 ~ 2.0（相對初始資金）
  drawdown:                    0.0 ~ 1.0（當前回撤%）
  recent_win_rate:             0.0 ~ 1.0（最近 10 筆）

全部正規化到 [-1.0, 1.0] 範圍
```

### 2.2 動作空間（Action Space）

```
目前骨架（MultiDiscrete）：
  [action_type, position_size_bucket]
  action_type: 0=觀望, 1=做多, 2=做空
  position_size_bucket: 0~10（對應 0%~50% 倉位）

建議改進（保持 MultiDiscrete，但語意更清晰）：
  action_type: 0=觀望, 1=做多_小倉, 2=做多_中倉, 3=做多_大倉,
               4=做空_小倉, 5=做空_中倉, 6=做空_大倉, 7=平倉

  小倉 = 1% 資本，中倉 = 2%，大倉 = 3%
  （與現有風險管理系統對齊：position_size_pct 1-3%）
```

### 2.3 獎勵函數設計（最關鍵的部分）

獎勵函數設計不好，Agent 會學到「不交易就不虧」的錯誤策略。

**多目標複合獎勵：**

```python
def _calculate_reward(self, action, prev_equity, current_equity, trade_result):
    """
    複合獎勵函數

    目標：同時最大化收益、控制回撤、避免過度交易
    """
    reward = 0.0

    # ─── 主要獎勵：步驟收益 ───────────────────────────────
    step_return = (current_equity - prev_equity) / prev_equity
    reward += step_return * 1000  # 縮放，讓數值在合理範圍

    # ─── 風險調整：波動懲罰 ───────────────────────────────
    if len(self.equity_curve) > 20:
        recent_returns = np.diff(self.equity_curve[-21:]) / self.equity_curve[-21:-1]
        volatility = np.std(recent_returns)
        reward -= volatility * 500  # 波動越大扣越多

    # ─── 回撤懲罰 ─────────────────────────────────────────
    peak = max(self.equity_curve)
    current_drawdown = (peak - current_equity) / peak
    if current_drawdown > 0.05:   # 回撤超過 5% 開始懲罰
        reward -= current_drawdown * 200
    if current_drawdown > 0.15:   # 回撤超過 15% 加重懲罰
        reward -= current_drawdown * 500

    # ─── 交易成本懲罰 ─────────────────────────────────────
    if action in (1, 2, 3, 4, 5, 6):  # 非觀望動作
        reward -= 0.5  # 每次開倉固定懲罰（鼓勵只在真正有信號時交易）

    # ─── 持倉過久懲罰 ─────────────────────────────────────
    if self.position_type != 0:
        bars_held = self.current_step - self.entry_step
        if bars_held > 72:  # 1h 資料：持倉超過 72 小時（3天）
            reward -= 0.1 * (bars_held - 72)

    # ─── 正確方向加成 ─────────────────────────────────────
    if trade_result is not None and trade_result.pnl > 0:
        reward += 1.0  # 盈利交易額外加分

    return float(reward)
```

**注意事項：**
- 獎勵縮放非常重要，PPO 對數值範圍敏感
- 建議使用 `stable-baselines3` 的 `VecNormalize` 自動正規化獎勵
- 波動懲罰係數需要調整，過高會讓 Agent 完全不交易

### 2.4 PPO 訓練配置

```python
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

# 環境包裝
env = DummyVecEnv([lambda: StrategyFusionEnv()])
env = VecNormalize(env, norm_obs=True, norm_reward=True)

# PPO 超參數
model = PPO(
    policy="MlpPolicy",
    env=env,
    learning_rate=3e-4,
    n_steps=2048,           # 每次更新使用的時間步數
    batch_size=64,
    n_epochs=10,            # 每次更新的訓練輪數
    gamma=0.99,             # 折扣因子（0.99 = 非常長期）
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,          # 熵係數（鼓勵探索）
    vf_coef=0.5,
    max_grad_norm=0.5,
    verbose=1,
    tensorboard_log="./logs/rl_training/",
    device="cpu",           # BioNeuronAI 是 CPU 推論
)

# 訓練
model.learn(
    total_timesteps=1_000_000,  # 100萬步（約等於 1hr K線 1年資料跑 30 個 episode）
    callback=[
        EvalCallback(eval_env, best_model_save_path="rl_models/ppo_best/"),
        StopTrainingOnRewardThreshold(reward_threshold=50.0),
    ],
)
```

---

## 三、訓練流程設計

### 3.1 資料準備

```
現有資料：
  840+ 每日 zip → BTCUSDT 1h K線 2024-01-01 ~ 2026-04-21

訓練/驗證切分（Walk-Forward 風格）：
  訓練集：2024-01-01 ~ 2025-06-30（18 個月）
  驗證集：2025-07-01 ~ 2025-12-31（6 個月）
  最終測試：2026-01-01 ~ 2026-04-21（未見過）

每個 Episode 設計：
  從訓練集中隨機抽取一段連續時間（例如 30 天 = 720 根 1h K線）
  Agent 在這 720 根K線上做完整的交易決策
  Episode 結束時計算總 Sharpe 作為最終評估
```

### 3.2 策略信號預計算

為了加速訓練，建議預先計算所有策略的信號，而不是訓練時即時計算：

```python
# tools/precompute_strategy_signals.py

def precompute_signals(ohlcv_data: np.ndarray) -> List[Dict]:
    """
    預計算所有策略在每根K線的信號
    儲存為 .npy 或 .pkl 供 RL 訓練使用
    """
    strategies = {
        "trend_following": TrendFollowingStrategy("1h"),
        "mean_reversion": MeanReversionStrategy("1h"),
        "swing_trading": SwingTradingStrategy("1h"),
        "breakout": BreakoutTradingStrategy("1h"),
    }

    all_signals = []
    window_size = 100  # 每個策略需要的歷史K線數

    for i in range(window_size, len(ohlcv_data)):
        window = ohlcv_data[i - window_size:i]
        step_signals = {}
        for name, strategy in strategies.items():
            try:
                setup = strategy.generate_signal(window)
                step_signals[name] = {
                    "direction": setup.direction if setup else 0,
                    "confidence": setup.confidence if setup else 0.0,
                    "strength": float(setup.signal_strength.value) / 3 if setup else 0.0,
                }
            except Exception:
                step_signals[name] = {"direction": 0, "confidence": 0.0, "strength": 0.0}

        all_signals.append(step_signals)

    return all_signals
```

### 3.3 訓練監控

```python
# 使用 TensorBoard 監控訓練過程
# 執行：tensorboard --logdir ./logs/rl_training

# 關鍵指標：
# - mean_reward（平均獎勵）：應該逐漸上升
# - ep_len_mean（平均 episode 長度）：穩定在設定值附近
# - loss（策略損失）：應該收斂
# - entropy_loss（熵損失）：應該緩慢下降（Agent 逐漸確定化）

# 警告信號（訓練出問題的跡象）：
# - mean_reward 始終為 0 → 獎勵函數有問題
# - Agent 從不交易（只選 hold）→ 懲罰設計讓觀望最優
# - Agent 瘋狂交易（每步都開倉）→ 交易成本懲罰不夠
```

---

## 四、Shadow Mode（影子模式）

**強烈建議在生產環境部署前使用 Shadow Mode 驗證：**

```
Shadow Mode 設計：

現有系統（生產）       RL Agent（影子）
      │                       │
      ▼                       ▼
  AIStrategyFusion         RLFusionAgent
  MARKET_ADAPTIVE            PPO 推論
      │                       │
      ▼                       ▼
  實際執行交易            記錄決策但不執行
      │                       │
      └──────────┬────────────┘
                 ▼
         每日比較兩系統的決策差異
         記錄：若 RL Agent 的決策被執行，結果會是什麼？
         評估 N 天後，若 RL Agent 表現更好→ 考慮切換
```

實作方式：
```python
# api/app.py 或 backtest/service.py 中
if config.enable_rl_shadow_mode:
    rl_decision = rl_agent.predict(current_state)
    rl_shadow_log.append({
        "timestamp": now,
        "actual_decision": fusion_signal.consensus_direction,
        "rl_decision": rl_decision.action_type,
        "actual_result": None,  # 等待未來填入
    })
```

---

## 五、與 BioNeuronAI 現有 rl_fusion_agent.py 的對應

### 5.1 現有骨架已完成的部分

```python
# rl_fusion_agent.py 現有狀態

✅ StrategyFusionEnv（gymnasium.Env 子類）
   ✅ __init__：observation_space、action_space 定義
   ✅ reset()
   ✅ step()（基礎版本）
   ✅ _get_observation()
   ✅ _calculate_reward()（基礎版本，需強化）
   ✅ _update_position()
   ⚠️ market_data 需要接入真實資料

✅ RLFusionAgent（PPO 訓練封裝）
   ✅ __init__（PPO 配置）
   ✅ train()（訓練迴圈）
   ✅ predict()（推論）
   ✅ save/load

✅ SB3_AVAILABLE 安全檢查（stable-baselines3 選裝）
```

### 5.2 需要補完的部分

| 項目 | 目前狀態 | 需要做什麼 |
|------|---------|-----------|
| 真實 OHLCV 資料接入 | 假資料 | 接入 840+ zip 的資料載入邏輯 |
| 策略信號傳入 | 假信號 | 接入預計算的信號陣列 |
| 獎勵函數 | 基礎版本 | 補充 Sharpe、回撤、持倉時間懲罰 |
| 市場特徵正規化 | 未正規化 | 所有特徵正規化至 [-1, 1] |
| 訓練資料生成腳本 | 不存在 | `tools/precompute_strategy_signals.py` |
| VecNormalize 包裝 | 無 | 加入訓練流程 |
| TensorBoard 記錄 | 有配置但未完整 | 補充關鍵指標記錄 |
| EvalCallback | 無 | 定期驗證防止過擬合 |

---

## 六、完整整合流程圖

```
第一步（一次性）：訓練資料準備
  840+ zip → 解壓 → OHLCV 陣列
      ↓
  precompute_strategy_signals()
  → 儲存 signals_precomputed.pkl
  → 儲存 market_features.pkl

第二步（週期性訓練）：
  載入 signals_precomputed.pkl
      ↓
  StrategyFusionEnv(market_data, strategy_signals)
      ↓
  PPO.learn(total_timesteps=1_000_000)
      ↓
  儲存 rl_models/ppo_fusion_v1.zip
  + VecNormalize stats

第三步（生產推論）：
  每根新K線到來
      ↓
  計算四個策略的即時信號
      ↓
  RLFusionAgent.predict(current_state)
      ↓
  action = [方向, 倉位大小]
      ↓
  轉換為 TradeSetup → 交易引擎
```

---

## 七、已知挑戰與對策

### 7.1 樣本效率問題

**問題：** PPO 需要大量訓練步驟（通常 100 萬~1000 萬），而 840 天的 1h K線只有約 20,000 根。

**對策：**
- 每個 episode 隨機抽 30 天窗口，重複抽樣，製造大量 episodes
- 使用資料增強：微幅隨機縮放 OHLCV（Gaussian noise）增加資料多樣性
- 考慮使用 GAN 生成合成時序資料（ML4T Ch.21 的做法）

### 7.2 非平穩性問題

**問題：** 2024 年的 BTC 市場規律不一定在 2025-2026 年還有效。

**對策：**
- Walk-Forward 週期性重訓練（每季重訓一次）
- 保留多個版本的模型（v_Q1, v_Q2...），根據最近績效切換

### 7.3 獎勵稀疏問題

**問題：** 每步的即時獎勵很小（微小的 PnL），Agent 難以學習。

**對策：**
- 使用形狀獎勵（Reward Shaping）：加入中間獎勵（如：市場方向預測正確時給小獎勵）
- 考慮使用 LSTM Policy（記憶機制），讓 Agent 能看到更長的歷史

### 7.4 過擬合風險

**問題：** 1年的 BTC 資料對 RL 而言仍嫌不足，容易過擬合 2024 年的特定規律。

**對策：**
- EvalCallback：定期在驗證集上評估，若驗證集下滑則早停
- Dropout 正則化（在 MlpPolicy 中可配置）
- 多幣種訓練（未來）：加入 ETHUSDT、SOLUSDT 等，增加泛化能力

---

## 八、預估工時

| 任務 | 工時 |
|------|------|
| 補完 `rl_fusion_agent.py`（真實資料接入） | 3-5 天 |
| 實作 `tools/precompute_strategy_signals.py` | 2-3 天 |
| 強化獎勵函數設計與調試 | 3-5 天 |
| 初步訓練 + 調參（hyperparameter tuning） | 1-2 週 |
| Shadow Mode 驗證（至少 2-4 週觀察） | 2-4 週 |
| 評估並決定是否切換至生產 | 1 週 |
| **合計** | **約 6-10 週** |

---

## 九、依賴清單

```toml
# pyproject.toml 需要新增（部分可能已存在）
stable-baselines3>=2.0.0        # PPO 算法
gymnasium>=0.29.0               # RL 環境框架（已在骨架中使用）
tensorboard>=2.13.0             # 訓練監控
torch>=2.0.0                    # 已有（用於 111M 推論模型）
```

---

## 十、優先順序建議

方案 D 是本系列文件中**最複雜、最高風險、最長期**的方案，建議按以下順序推進：

```
1. 先完成方案 C（1週）→ 有穩定的硬性路由基線
   ↓
2. 同時推進方案 B（2-3週）→ 有 ML Meta-Learner 的中期改進
   ↓
3. 方案 D 以研究性質並行進行（不影響生產）
   ↓
4. 方案 D 用 Shadow Mode 驗證至少 1 個月
   ↓
5. 確認 Shadow Mode 結果優於方案 C/B 後，才考慮切換至生產
```

**建議心態：**
> 方案 D 的目標不是「替換」方案 C 或 B，而是在完全獨立的並行軌道上探索「AI 是否能學到人類想不到的融合規律」。即使 RL Agent 最後表現不如方案 C，這個過程本身也會讓你對策略融合有更深的理解。

---

*本文件為策略融合路線圖系列的最後一份。*  
*完整系列文件索引請見 `STRATEGY_FUSION_ROADMAP_OVERVIEW.md`。*
