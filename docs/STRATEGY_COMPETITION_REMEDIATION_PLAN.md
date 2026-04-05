# 策略競爭系統整修計畫
> 更新日期: 2026-04-05  
> 目的: 提供其他 AI / 開發者接手時的單一事實來源，說明目前真實狀況、後續實作順序、驗收標準。  
> 範圍: 只處理策略模組、策略競爭 / 優化 / 編排層，以及它們和正式 replay 的整合。  
> 不含: 新聞分析、daily report、RAG、其他分析模組。

---

## 1. 目前真實狀況

### 1.1 已完成的部分

- 正式主策略主線已收斂為：
  - `src/bioneuronai/core/trading_engine.py`
  - `src/bioneuronai/strategies/selector/core.py`
  - `src/bioneuronai/strategies/strategy_fusion.py`
- 舊主策略檔 `src/bioneuronai/trading_strategies.py` 已移除，不再是正式主路徑。
- 正式 replay / backtest 主系統已收斂到 `backtest/`。
- `StrategyArena` 已改為使用正式 replay，不再使用隨機假績效。
- `StrategyPortfolioOptimizer` 已改為使用正式 replay 聚合各 phase gene，不再使用隨機假績效。
- `python main.py backtest ...` 可實際產生交易，代表 replay 主底座與正式主交易主線可用。

### 1.2 已確認的核心問題

#### 問題 A: 固定策略共同流程的 setup 驗證順序錯誤

影響檔案：

- `src/bioneuronai/strategies/base_strategy.py`

已實際驗證到的狀況：

- `TrendFollowingStrategy`
- `SwingTradingStrategy`
- `MeanReversionStrategy`

都能先產生 `TradeSetup`，但在 `BaseStrategy.run_iteration()` 裡會先呼叫 `validate_setup(setup)`，而 `validate_setup()` 又會檢查：

- `setup.total_position_size <= 0`

問題是 `setup.total_position_size` 目前是在 **驗證之後** 才計算。

因此目前實際流程變成：

1. `evaluate_entry_conditions()` 產生 setup
2. `validate_setup()` 因 `total_position_size == 0` 失敗
3. 後面的 `calculate_position_size()` 根本來不及執行
4. 策略整月 0 trade

這是目前最確定、最優先的 bug。

#### 問題 B: PairTrading 正式 replay 缺次資產資料

影響檔案：

- `src/bioneuronai/strategies/pair_trading_strategy.py`
- `backtest/service.py`
- `backtest/data/binance_historical/`

已實際驗證到的狀況：

- `PairTradingStrategy` 需要 `additional_data['secondary_ohlcv']`
- 現有正式 replay 資料根目錄下只有 `ETHUSDT`
- `_load_secondary_ohlcv(...)` 目前無法為 `ETHUSDT` 載入 `BTCUSDT`

因此 `PairTradingStrategy` 目前不是「條件太嚴」，而是「資料依賴不足」。

#### 問題 C: Breakout / DirectionChange 目前在正式資料窗口上完全未觸發

影響檔案：

- `src/bioneuronai/strategies/breakout_trading.py`
- `src/bioneuronai/strategies/direction_change_strategy.py`

已實際驗證到的狀況：

- 在 `ETHUSDT / 1h / 2025-12-22 ~ 2026-01-21` 這段上
- `BreakoutTradingStrategy` 沒有產生任何 setup
- `DirectionChangeStrategy` 沒有產生任何 setup

目前還不能直接判定是 bug 或策略本來就不適合這段市場，但就「策略可交易性」來說，現在不合格。

### 1.3 目前不要誤判的地方

- `backtest/` 本身不是問題根源。  
  它已能讓 `TradingEngine` 主線實際產生交易。
- 現在高階競爭層也不是假系統了。  
  `StrategyArena` / `StrategyPortfolioOptimizer` 已改用真 replay。
- 目前的問題中心是：
  - 固定策略本體的可交易性
  - 固定策略共同流程的驗證順序
  - PairTrading 的資料依賴

---

## 2. 已做過的實際驗證

### 2.1 已通過的驗證

- `python main.py status`
- `python main.py backtest --symbol ETHUSDT --interval 1h --start-date 2025-12-22 --end-date 2025-12-23 --balance 10000 --warmup-bars 10`
- `python main.py evolve --symbol ETHUSDT --interval 1h --population 2 --generations 1 --warmup-bars 10`

### 2.2 已確認的結果

- 正式主交易主線 replay 可產生交易
- `StrategyArena` 現在走正式 replay
- `StrategyPortfolioOptimizer` 現在走正式 replay
- 固定策略層在正式 replay 下仍普遍 0 trade

### 2.3 已做過的策略普查結論

在目前正式資料窗口下：

- `TrendFollowingStrategy`
  - 會產生 setup
  - 但被共同驗證流程擋掉
- `SwingTradingStrategy`
  - 會產生 setup
  - 但被共同驗證流程擋掉
- `MeanReversionStrategy`
  - 會產生 setup
  - 但被共同驗證流程擋掉
- `BreakoutTradingStrategy`
  - 目前未產生 setup
- `DirectionChangeStrategy`
  - 目前未產生 setup
- `PairTradingStrategy`
  - 缺次資產資料，無法正式驗證

---

## 3. 接下來預計怎麼做

## Phase 1: 修固定策略共同流程

目標：

- 先讓已經會產生 setup 的策略真正能送到下單階段

優先檔案：

- `src/bioneuronai/strategies/base_strategy.py`

處理方向：

1. 調整 `run_iteration()` 流程
2. 先計算 `setup.total_position_size`
3. 再跑 `validate_setup()`
4. 或重構 `validate_setup()`，讓它不在前置驗證階段檢查尚未填入的欄位

原則：

- 不要用繞過驗證的方式硬放行
- 要讓 setup 驗證職責清楚：
  - 前置驗證
  - 風險計算後驗證

## Phase 2: 重新做固定策略普查

目標：

- 確認修完共同流程後，哪些策略真的恢復可交易性

優先檔案：

- `backtest/service.py`
- `src/bioneuronai/strategies/strategy_arena.py`
- 各固定策略檔案

處理方向：

1. 逐策略跑正式 replay
2. 列出每個策略：
   - trade count
   - setup count
   - validation reject count
3. 分出：
   - 已可交易
   - 邏輯仍待修
   - 資料依賴不足

## Phase 3: 補 PairTrading 所需正式資料

目標：

- 讓 `PairTradingStrategy` 能被公平評估

優先檔案：

- `backtest/data/binance_historical/`
- `backtest/service.py`
- `src/bioneuronai/strategies/pair_trading_strategy.py`

處理方向：

1. 補正式 `BTCUSDT` 歷史資料
2. 確認 `_load_secondary_ohlcv(...)` 能載到資料
3. 再做單獨 replay 驗證

## Phase 4: 修 Breakout / DirectionChange 的可交易性

目標：

- 找出為什麼整段資料都沒有 setup

優先檔案：

- `src/bioneuronai/strategies/breakout_trading.py`
- `src/bioneuronai/strategies/direction_change_strategy.py`

處理方向：

1. 逐步統計各條件的命中次數
2. 確認是：
   - 條件過嚴
   - 欄位計算錯誤
   - 市場資料本身不適合
3. 只做有根據的調整，不隨便降低門檻到亂出手

## Phase 5: 最後才回到高階競爭層微調

目標：

- 在固定策略層真正可交易之後，再看競爭結果是否有辨識度

優先檔案：

- `src/bioneuronai/strategies/strategy_arena.py`
- `src/bioneuronai/strategies/portfolio_optimizer.py`
- `src/bioneuronai/strategies/phase_router.py`

處理方向：

1. 重新檢查 scoring / fitness
2. 檢查 phase-gene 聚合是否合理
3. 視需要再處理 `PhaseRouter`

---

## 4. 通過標準

## 4.1 Phase 1 通過標準

- `TrendFollowingStrategy`、`SwingTradingStrategy`、`MeanReversionStrategy`
  在正式 replay 下，不再因 `total_position_size == 0` 被提前擋掉
- `validate_setup()` 的失敗訊息不再只出現空字串 `''`
- 同一段資料下，至少其中一部分 setup 能走到 `execute_entry()` 之前

## 4.2 Phase 2 通過標準

- 有一份逐策略正式 replay 普查結果
- 每個策略都能被清楚歸類到：
  - 可交易
  - 有 setup 但仍被阻擋
  - 缺資料
  - 整段無 setup

## 4.3 Phase 3 通過標準

- `backtest/data/binance_historical/` 有至少兩個可用 symbol
- `_load_secondary_ohlcv(...)` 能實際載到配對資料
- `PairTradingStrategy` 可完成正式 replay 評估

## 4.4 Phase 4 通過標準

- `BreakoutTradingStrategy` 和 `DirectionChangeStrategy` 至少能清楚回答：
  - 是邏輯問題
  - 還是市場條件未觸發
- 在合理資料區間內，不應該再出現「整月完全沒有任何 setup，且原因不明」

## 4.5 整體完成標準

以下條件同時成立，才算這條線完成：

1. `StrategyArena` 與 `StrategyPortfolioOptimizer` 持續使用正式 replay
2. 固定策略層不再因共同流程 bug 而整體失效
3. 除配對資料依賴外，其餘主要固定策略在合理資料區間內應有可解釋的觸發結果
4. 文件已同步更新，不再宣稱假績效或舊主路徑

---

## 5. 其他 AI 協作限制

其他 AI 在這條線上工作時，請遵守：

1. 以修改既有檔案為主，除非真的沒有合適位置才新增
2. 不要把假績效或隨機回測重新加回去
3. 不要為了讓策略「看起來會交易」而粗暴降低門檻
4. 不要把 replay 層和 evaluator 層責任重新混在一起
5. 不要恢復 `trading_strategies.py` 類似舊主路徑
6. 每次修完都要用正式 replay 再驗證，不接受只靠靜態推論

---

## 6. 建議驗證命令

### 正式主線 smoke

```powershell
python main.py status
python main.py backtest --symbol ETHUSDT --interval 1h --start-date 2025-12-22 --end-date 2025-12-23 --balance 10000 --warmup-bars 10
```

### 競爭層 smoke

```powershell
python main.py evolve --symbol ETHUSDT --interval 1h --population 2 --generations 1 --warmup-bars 10
```

### 編譯檢查

```powershell
python -m compileall src\\bioneuronai\\strategies src\\bioneuronai\\cli backtest
```

---

## 7. 一句話結論

目前正式 replay 與高階競爭框架已經接上真資料；真正還沒完成的，不是競爭框架本身，而是固定策略層的可交易性與共同流程 bug。
