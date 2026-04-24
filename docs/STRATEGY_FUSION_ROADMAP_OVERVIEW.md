# 策略融合系統：未來發展路線圖總覽

> 建立日期：2026-04-24  
> 版本：v1.0  
> 作者：研究整理  
> 適用版本：BioNeuronAI v4.1.0+

---

## 文件索引

本系列文件共 4 份，請依需求閱讀：

| 文件 | 說明 |
|------|------|
| **本文件**：`STRATEGY_FUSION_ROADMAP_OVERVIEW.md` | 架構總覽、方案對比、選擇建議 |
| `STRATEGY_FUSION_PLAN_B_ML_METALEARNER.md` | 方案 B：ML Meta-Learner 詳細實作 |
| `STRATEGY_FUSION_PLAN_C_REGIME_ROUTING.md` | 方案 C：硬性體制路由詳細實作 |
| `STRATEGY_FUSION_PLAN_D_RL_AGENT.md` | 方案 D：深度強化學習 Agent 詳細實作 |

---

## 一、背景：為什麼需要重新規劃融合策略

### 1.1 現有系統架構（已完成部分）

目前 BioNeuronAI 策略層已完成以下工作：

```
─────────────────────────────────────────────────────────
L1 路由層（已完成）
  StrategySelector  ←  MarketEvaluator（市場體制辨識）
      │
      │  依體制輸出各策略類型比重
      │  並加入回測績效 blend（build_selector_performance_weights）
      ▼
─────────────────────────────────────────────────────────
L2 融合層（已完成）
  AIStrategyFusion  ←  FusionMethod.MARKET_ADAPTIVE
      │
      │  多策略各自跑 generate_signal()
      │  加權投票後輸出一筆 FusionSignal
      ▼
─────────────────────────────────────────────────────────
L3 輸出層
  TradeSetup（進場價、SL、TP）→ 交易引擎
─────────────────────────────────────────────────────────
```

已實作的 FusionMethod 枚舉：
- `WEIGHTED_VOTE`：加權票數
- `BEST_PERFORMER`：最佳績效者優先
- `MARKET_ADAPTIVE`：體制自適應（目前預設）
- `CONFIDENCE_BASED`：信心加權
- `ENSEMBLE`：集成（骨架存在，未完整實作）

### 1.2 核心問題確認

經過業界對比研究與使用者反饋，確認了當前架構的根本問題：

> **StrategySelector 本質上只是一個路由器（Router），AIStrategyFusion 雖有加權投票，但各策略仍然獨立思考，只是在最後一步把票數加起來而已。**

這等同於 5 個人各自看同一份資料、各自做決定，然後舉手投票。但問題是：
- 策略 A 看到趨勢上升→多
- 策略 B 看到 RSI 超買→空
- 策略 C 看到支撐位→多
- **沒有任何機制去理解：「當 A 和 B 同時出現信號時，歷史上哪個更可靠？」**

這就是要改進的核心。

---

## 二、業界主流方案總覽

### 方案 A：加權投票聚合（已實作，現狀）

**代表系統：** QuantConnect Algorithm Framework Multi-Alpha

```
Alpha 模型 1 → Insight(LONG, confidence=0.7, weight=0.3)  ┐
Alpha 模型 2 → Insight(LONG, confidence=0.5, weight=0.4)  ├──→ Portfolio
Alpha 模型 3 → Insight(SHORT, confidence=0.3, weight=0.3) ┘    Construction
                                                                 Model
                                                                 ↓
                                                            PortfolioTarget
```

**QuantConnect 的做法：**
- 每個 Alpha 模型輸出 `Insight` 物件（方向 + 信心 + 建議倉位比重）
- Portfolio Construction Model 消費所有 Insight，決定最終倉位
- `EqualWeightingPortfolioConstructionModel`：每個 Insight 等權
- 自訂 Portfolio Construction：可寫複雜合併邏輯

**BioNeuronAI 現狀對應：**
- Alpha 模型 = `BaseStrategy` 子類（TrendFollowing、MeanReversion 等）
- Insight = `TradeSetup`（進場+SL+TP）
- Portfolio Construction = `AIStrategyFusion._fuse_by_weighted_vote()`

**優點：**
- 架構清晰、模組化
- 單一策略可插拔替換
- 容易 debug（知道哪個策略出了什麼信號）

**缺點（使用者發現的問題）：**
- 融合邏輯是人工規則，無法「學習」
- 策略間的相關性沒有被考慮
- 市場體制判斷如果錯誤，整個比重全錯

---

### 方案 B：ML Meta-Learner 堆疊（進階改進）

**代表系統：** ML for Trading (Stefan Jansen) XGBoost Stacking、Citadel 內部風格

```
策略 1 → {direction: 1, confidence: 0.7, rsi: 68, ma_diff: 0.02}  ┐
策略 2 → {direction: 0, confidence: 0.5, bb_pos: 0.8, vol: 1.2}   ├──→ XGBoost
策略 3 → {direction: 1, confidence: 0.6, atr_ratio: 1.1, ...}     ┘    Meta-Learner
市場特徵 → {regime: trending, vix: 0.3, volume_surge: 1.5}             ↓
                                                                   預測:
                                                                   LONG  prob=0.71
                                                                   SHORT prob=0.18
                                                                   FLAT  prob=0.11
```

**核心差異：**
- 不是人工定義「如何投票」，而是**用歷史資料訓練模型去學習「哪些信號組合在哪些市場下有效」**
- Meta-Learner 的輸入是各策略的「特徵值」（不只是方向），輸出是最終決策的概率分佈
- XGBoost 可以學到：「當 RSI > 65 且趨勢策略信心 > 0.7 且是趨勢市，歷史上做多勝率 0.73」

**詳見：** `STRATEGY_FUSION_PLAN_B_ML_METALEARNER.md`

---

### 方案 C：硬性體制路由（實務最有效）

**代表系統：** Bridgewater All Weather、Two Sigma 市場體制識別

```
體制識別器
    │
    ├── 趨勢體制（ADX > 25, EMA 排列整齊）
    │       └──→ 只啟動 TrendFollowing + Breakout
    │           100% 倉位在這兩個策略中分配
    │           MeanReversion、SwingTrading 完全靜默
    │
    ├── 震盪體制（ADX < 20, 在支撐壓力間震盪）
    │       └──→ 只啟動 MeanReversion + SwingTrading
    │           TrendFollowing 完全靜默（避免假突破）
    │
    ├── 高波動體制（ATR 超過均值 2 倍以上）
    │       └──→ 倉位減半，只啟動 Breakout 策略
    │           其他策略暫停（波動太大，止損容易被掃）
    │
    └── 過渡體制（體制切換中）
            └──→ 觀望，不進新倉，等待體制確認
```

**核心差異：**
- 現有 `StrategySelector` 是**軟性路由**（調整比重，所有策略仍在跑）
- 方案 C 是**硬性路由**（只跑最適合的，其他完全關閉）
- 消除策略衝突的根本：你不可能同時既用趨勢策略又用均值回歸

**詳見：** `STRATEGY_FUSION_PLAN_C_REGIME_ROUTING.md`

---

### 方案 D：深度強化學習 Agent（長期研究）

**代表系統：** OpenAI Gym Trading、JP Morgan Deep RL Papers、ML4T Ch.22

```
觀察空間（State）:
    市場 OHLCV 特徵
    + 各策略信號 (direction, strength, confidence) × 4 策略
    + 新聞情緒 (event_score)
    + 當前持倉狀態
    + 市場體制特徵
           ↓
    PPO Agent（神經網路）
           ↓
動作空間（Action）:
    0 = 觀望
    1 = 做多（倉位 1%）
    2 = 做多（倉位 2%）
    3 = 做多（倉位 3%）
    4 = 做空（倉位 1%）
    5 = 做空（倉位 2%）
    6 = 做空（倉位 3%）
    7 = 平倉
           ↓
獎勵函數（Reward）:
    已實現 PnL × (1 - 交易成本懲罰) × (1 + Sharpe 加成)
    - 持倉過久的時間懲罰
    - 連續虧損的額外懲罰
```

**核心差異：**
- 不需要人工定義融合規則
- Agent 自己學習「什麼時候用哪個策略、進多少倉」
- 可能學到人類無法想到的規律（如：策略全部看多時反而做空）
- `rl_fusion_agent.py` 已有骨架實作（PPO + gymnasium）

**詳見：** `STRATEGY_FUSION_PLAN_D_RL_AGENT.md`

---

## 三、方案全面對比

### 3.1 技術複雜度 vs 預期效果

```
高   ┤
     │                              ● D (RL Agent)
預   │
期   │               ● B (ML Meta-Learner)
效   │
果   │   ● C (體制路由)
     │
     │ ● A (現狀)
低   ┤
     └──────────────────────────────────────
         低         技術複雜度         高
```

### 3.2 詳細對比表

| 維度 | A（現狀） | B（ML Meta-Learner） | C（體制路由） | D（RL Agent） |
|------|-----------|---------------------|--------------|--------------|
| **融合本質** | 人工加權投票 | ML學習融合規則 | 體制切換路由 | AI端對端學習 |
| **需要訓練** | 否 | 是（有標籤監督學習） | 否 | 是（強化學習） |
| **可解釋性** | 高 | 中（SHAP值可解釋） | 最高 | 低 |
| **對歷史資料需求** | 低 | 中（需要足夠樣本） | 低 | 高（需大量episode）|
| **過擬合風險** | 低 | 中 | 低 | 高 |
| **策略衝突問題** | 存在 | 緩解（Meta-Learner學習忽略衝突信號） | 消除 | 自動學習 |
| **體制判斷錯誤影響** | 高 | 中 | 高（錯誤體制→完全錯策略） | 低（RL自己判斷）|
| **BioNeuronAI 現有程式可用** | ✅ 全部 | ✅ 策略信號 + 擴充 | ✅ MarketEvaluator 擴充 | ✅ rl_fusion_agent.py 骨架 |
| **預計實作工時** | — | 2-3週 | 3-5天 | 4-8週 |
| **生產穩定性** | 高 | 高 | 高 | 中低 |

### 3.3 按階段的推薦組合

**第一階段（1-2週）：建立基線**
→ 強化方案 C（硬性體制路由）+ 方案 A 繼續作為補充

**第二階段（1-2個月）：ML 強化**
→ 在方案 C 基礎上加入方案 B 的 Meta-Learner 進行信心校準

**第三階段（3個月+）：長期研究**
→ 方案 D 的 RL Agent 並行研究，用 shadow mode 先驗證

---

## 四、與 BioNeuronAI 現有架構的對應關係

### 4.1 現有程式碼資產清單

以下是與策略融合直接相關的現有程式碼：

```
src/bioneuronai/strategies/
├── base_strategy.py          ← 策略基底（TradeSetup、SignalStrength、MarketCondition）
├── trend_following.py        ← 趨勢策略
├── swing_trading.py          ← 波段策略
├── mean_reversion.py         ← 均值回歸
├── breakout_trading.py       ← 突破策略
├── direction_change_strategy.py ← 方向轉換策略
├── pair_trading_strategy.py  ← 配對交易
├── strategy_fusion.py        ← AIStrategyFusion（核心融合邏輯）
│   └── FusionMethod: WEIGHTED_VOTE / BEST_PERFORMER /
│                     MARKET_ADAPTIVE / CONFIDENCE_BASED / ENSEMBLE
├── phase_router.py           ← 交易階段路由（開盤/盤中/收盤）
├── portfolio_optimizer.py    ← 組合優化
├── strategy_arena.py         ← 策略競技場（回測競爭）
├── rl_fusion_agent.py        ← RL 融合骨架（PPO + gymnasium）
└── selector/
    ├── core.py               ← StrategySelector（路由器 + blend）
    ├── evaluator.py          ← MarketEvaluator（體制識別）
    ├── types.py              ← StrategyType、MarketRegime 等
    └── configs.py            ← 10 個策略配置模板
```

### 4.2 各方案需要新增 / 修改的檔案

| 方案 | 需修改的現有檔案 | 需新增的檔案 |
|------|----------------|-------------|
| C（體制路由） | `selector/core.py`（hardcode route邏輯）、`selector/evaluator.py`（強化體制識別） | `selector/hard_router.py` |
| B（Meta-Learner） | `strategy_fusion.py`（新增ENSEMBLE_ML模式）、`selector/core.py`（信心校準呼叫） | `ml_meta_learner.py`、訓練腳本 |
| D（RL Agent） | `rl_fusion_agent.py`（從骨架補完）、`strategy_fusion.py`（接入RL動作） | 訓練環境、模型儲存路徑 |

---

## 五、當前系統問題診斷

### 5.1 StrategySelector 層（L1）

**已有的體制識別：**
`MarketEvaluator` 已可識別以下體制：
- `trending_bull`（上升趨勢）
- `trending_bear`（下降趨勢）
- `ranging`（震盪）
- `high_volatility`（高波動）
- `low_volatility`（低波動）

**問題：** 識別後只是調整比重（`_calculate_strategy_weights()`），沒有硬性切換機制。

**影響：** 即使在明確的趨勢市，`MeanReversionStrategy` 仍有 10-15% 的比重在跑，可能輸出衝突信號。

### 5.2 AIStrategyFusion 層（L2）

**已有的融合方式：**
`MARKET_ADAPTIVE` 模式：
```python
# 來自 strategy_fusion.py
# 體制推薦策略 ×1.5，避免策略 ×0.5，加入信號強度乘數
```

**問題：** 乘數是人工定義的固定值（1.5、0.5），沒有根據歷史表現動態調整。

### 5.3 回測反饋循環（已完成，但未完整利用）

上一輪 session 已完成：
```python
# backtest/service.py
weights = build_selector_performance_weights(results)
selector.load_performance_weights(weights, blend_alpha=0.3)
```

這個回測反饋循環（Feedback Loop）是方案 B 的雛型，可以在此基礎上擴充。

---

## 六、術語對照表

在閱讀本系列文件時，以下術語需要釐清：

| 術語 | BioNeuronAI 中的對應 | 說明 |
|------|---------------------|------|
| Alpha 信號 | `TradeSetup`（策略輸出） | 方向 + 信心 + SL/TP 的組合信號 |
| 融合 / 聚合 | `AIStrategyFusion` | 把多個策略信號合成一個最終決策 |
| 體制 | `MarketRegime`（in types.py） | 趨勢/震盪/高波動等市場狀態 |
| Meta-Learner | 尚未實作 | 學習「哪些策略信號在哪種體制下有效」的第二層模型 |
| RL Agent | `rl_fusion_agent.py`（骨架） | 透過強化學習自主學習融合策略 |
| IS / OOS | 樣本內 / 樣本外 | Walk-Forward 驗證的兩個期間 |
| Blend Alpha | `_performance_blend_alpha` | 回測績效權重佔比（0=純市場體制，1=純回測績效） |

---

## 七、後續決策指引

回答以下問題，對應到你應該優先選擇的方案：

**Q1: 你現在最想解決什麼問題？**
- 「策略互相衝突、反向」→ 方案 C
- 「不知道在哪種市場下哪個策略更好」→ 方案 B
- 「想讓 AI 完全自主決定」→ 方案 D

**Q2: 你現在有多少時間？**
- 1 週以內 → 方案 C（最快落地）
- 1 個月 → 方案 B（中期可見效果）
- 3 個月以上 → 方案 D（長期研究）

**Q3: 你更在乎穩定性還是效能上限？**
- 穩定性優先 → 方案 C > B > D
- 效能上限優先 → 方案 D > B > C

**Q4: 你有足夠的歷史回測資料嗎？**
- 有（840+ 每日K線，已完整本地化）→ 全部方案都可行
- 沒有 → 方案 C 不需要額外訓練資料

---

*詳細實作規劃見各子文件。本文件為策略融合改進系列的統一入口。*
