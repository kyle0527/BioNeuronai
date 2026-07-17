# 策略競爭系統整修計畫
> 更新日期: 2026-04-05
> 目的: 提供其他 AI / 開發者接手時的單一事實來源，說明目前真實狀況、後續實作順序、驗收標準。
> 範圍: 只處理策略模組、策略競爭 / 優化 / 編排層，以及它們和正式 replay 的整合。
> 不含: 新聞分析、daily report、RAG、其他分析模組。
>
> 註：本文件屬於策略 / replay 子系統專項整修計畫。此次文件整理未重新跑全量 replay，因此本文件保留為專項工作計畫，不視為全系統最新完成狀態。

## 目錄

1. 目前真實狀況
2. 已做過的實際驗證
3. 接下來預計怎麼做
4. 通過標準
5. 其他 AI 協作限制
6. 建議驗證命令
7. 一句話結論

---

## 1. 目前真實狀況

### 1.1 已完成的部分

- 正式主策略主線已收斂為：
  - `src/bioneuronai/core/trading_engine.py`
  - `src/bioneuronai/strategies/selector/core.py`
  - `src/bioneuronai/strategies/strategy_fusion.py`
- 舊主策略檔 `src/bioneuronai/trading_strategies.py` 已移除，不再是正式主路徑。
- `selector/` 目前只保留 `evaluator.py` 作為正式市場評估器；`evaluator_new.py` 已移除。
- 正式 replay / backtest 主系統已收斂到 `backtest/`。
- `StrategyArena` 已改為使用正式 replay，不再使用隨機假績效。
- `StrategyPortfolioOptimizer` 已改為使用正式 replay 聚合各 phase gene，不再使用隨機假績效。
- `BTCUSDT` 正式歷史資料已搬入 `backtest/data/binance_historical/`，`PairTradingStrategy` 的次資產資料依賴已補齊。
- `_load_secondary_ohlcv(...)` 已可在 `ETHUSDT` 主資產回放時載入 `BTCUSDT` 次資產資料。
- `VirtualAccount` 已補上 `LIMIT` 單成交模型，不再只成交市價單與條件單。
- `PairTradingStrategy` / `DirectionChangeStrategy` 已改成經由正式 connector 下單。
- `BreakoutTradingStrategy` 已修正突破基準，改為使用「當前 bar 之前」的區間。
- `DirectionChangeStrategy` 已修正 confirmation 計數，與 `required_confirmations` 對齊。

### 1.2 固定策略目前的正式 replay 狀態

驗證條件：

- symbol: `ETHUSDT`
- interval: `1h`
- date range: `2025-12-22 ~ 2026-01-21`
- warmup bars: `10`

目前實測結果：

- `PairTradingStrategy`
  - 已可正式交易
  - 次資產資料可正常載入
- `MeanReversionStrategy`
  - 已可正式交易
- `BreakoutTradingStrategy`
  - 已可正式交易
  - 目前交易數偏少，但不再是 0 trade
- `DirectionChangeStrategy`
  - 已可正式交易
  - 目前交易數偏少，但不再是 0 trade
- `SwingTradingStrategy`
  - 已可正式交易
  - 目前仍存在過度加碼 / pending order 管理問題
- `TrendFollowingStrategy`
  - 已可正式交易
  - 目前仍存在過度加碼 / pending order 管理問題

### 1.3 已確認的核心問題

#### 問題 A: pending order 與策略狀態契約已補主缺口，仍需觀察交易品質

影響檔案：

- `src/bioneuronai/strategies/base_strategy.py`
- `src/bioneuronai/strategies/swing_trading.py`
- `src/bioneuronai/strategies/trend_following.py`
- `backtest/mock_connector.py`
- `src/bioneuronai/trading/virtual_account.py`

目前狀況：

- 多個策略現在會在正式 replay 下產生真交易。
- `SwingTradingStrategy` / `TrendFollowingStrategy` 原本的重複掛單主因已定位並修補：
  - `BaseStrategy._finalize_analysis_state()` 現在會保留 `ENTRY_READY`
  - `LIMIT` entry 未成交時會留下 `current_setup`
  - connector 的 pending/open-position 狀態會在 `run_iteration()` 內同步回策略 state
  - `VirtualAccount` 會對未成交開倉單預留保證金，避免可用餘額被錯算
- 對應 smoke 已覆蓋：
  - pending entry 不再被下一輪分析重置成 `IDLE`
  - 第二筆超額 pending entry 會因保證金不足被拒絕

剩餘工作：

- 持續觀察 `SwingTradingStrategy` / `TrendFollowingStrategy` 在長區間 replay 下的交易數與加碼行為是否已回到合理範圍。
- 若仍有異常高交易數，下一步會轉向個別策略的 entry 條件與 partial fill/exit 管理。

#### 問題 B: 高階競爭已是真 replay，但仍受到固定策略品質拖累

影響檔案：

- `src/bioneuronai/strategies/strategy_arena.py`
- `src/bioneuronai/strategies/portfolio_optimizer.py`

已實際驗證到的狀況：

- `StrategyArena` / `StrategyPortfolioOptimizer` 現在都已吃正式 replay 結果，不再是假分數。
- 但因為固定策略層的交易品質不均衡，競爭結果會被：
  - 過度加碼策略
  - 交易數異常高策略
  - pending order 狀態未同步策略
  污染。

因此目前高階競爭層的主要問題，不是評估來源假，而是上游固定策略品質還未穩定。

### 1.4 目前不要誤判的地方

- `backtest/` 不是目前的問題根源。
  它已能讓正式主交易主線產生真交易，也已能評估高階競爭層。
- 現在高階競爭層不是假系統了。
  `StrategyArena` / `StrategyPortfolioOptimizer` 已改用真 replay。
- `PairTradingStrategy` 目前不再是「缺資料無法驗證」。
- `BreakoutTradingStrategy` / `DirectionChangeStrategy` 目前不再是「0 trade」。
- 目前真正的問題中心是：
  - pending order 與策略狀態契約
  - 過度加碼與單月交易數異常高
  - 固定策略品質尚未穩定

---

## 2. 已做過的實際驗證

### 2.1 已通過的驗證

- `python main.py status`
- `python main.py backtest --symbol ETHUSDT --interval 1h --start-date 2025-12-22 --end-date 2025-12-23 --balance 10000 --warmup-bars 10`
- `python main.py evolve --symbol ETHUSDT --interval 1h --population 2 --generations 1 --warmup-bars 10`
- `python -m compileall src\\bioneuronai\\strategies backtest`

### 2.2 已確認的結果

- 正式主交易主線 replay 可產生交易。
- `StrategyArena` 現在走正式 replay。
- `StrategyPortfolioOptimizer` 現在走正式 replay。
- `PairTradingStrategy` / `MeanReversionStrategy` / `BreakoutTradingStrategy` / `DirectionChangeStrategy` 現在都能在正式 replay 下產生交易。
- `SwingTradingStrategy` / `TrendFollowingStrategy` 現在雖能交易，但仍會出現異常高交易數與過度加碼。

### 2.3 目前已知的策略狀態分類

- 可交易，且基本路徑已打通：
  - `PairTradingStrategy`
  - `MeanReversionStrategy`
  - `BreakoutTradingStrategy`
  - `DirectionChangeStrategy`
- 可交易，但仍有重大品質問題：
  - `SwingTradingStrategy`
  - `TrendFollowingStrategy`

---

## 3. 接下來預計怎麼做

## Phase 1: 補齊 pending order 與策略狀態契約

目標：

- 先讓 `LIMIT` / pending order 不再造成重複進場與過度加碼。

優先檔案：

- `backtest/mock_connector.py`
- `src/bioneuronai/trading/virtual_account.py`
- `src/bioneuronai/strategies/base_strategy.py`
- `src/bioneuronai/strategies/swing_trading.py`
- `src/bioneuronai/strategies/trend_following.py`

處理方向：

1. 定義 pending entry order 存在時的防重複下單保護。
2. 讓策略能分辨：
   - 尚未成交的 entry order
   - 已成交但仍持倉的 trade
3. 避免單月交易數異常膨脹與餘額被吃成負值。

## Phase 2: 重新做固定策略普查

目標：

- 確認在真 replay + pending order 修正後，各策略的交易數與行為是否合理。

優先檔案：

- `backtest/service.py`
- `src/bioneuronai/strategies/strategy_arena.py`
- 各固定策略檔案

處理方向：

1. 逐策略跑正式 replay。
2. 列出每個策略：
   - trade count
   - setup count
   - validation reject count
   - pending order count
3. 分出：
   - 已可交易且行為合理
   - 已可交易但過度加碼
   - 有 setup 但成交率不足

## Phase 3: 修過度加碼與策略品質

目標：

- 找出為什麼部分策略會出現異常高交易數、重複掛單、餘額負值。

優先檔案：

- `src/bioneuronai/strategies/swing_trading.py`
- `src/bioneuronai/strategies/trend_following.py`
- `src/bioneuronai/trading/virtual_account.py`
- `backtest/mock_connector.py`

處理方向：

1. 追蹤 pending entry order 的生命週期。
2. 確認重複掛單是來自：
   - 策略不知道自己已有 pending order
   - replay fill 後未反映回策略狀態
   - 保護條件不足
3. 只做契約與狀態同步修正，不用粗暴放寬門檻。

## Phase 4: 最後才回到高階競爭層微調

目標：

- 在固定策略層交易行為合理之後，再看競爭結果是否有辨識度。

優先檔案：

- `src/bioneuronai/strategies/strategy_arena.py`
- `src/bioneuronai/strategies/portfolio_optimizer.py`
- `src/bioneuronai/strategies/phase_router.py`

處理方向：

1. 重新檢查 scoring / fitness。
2. 檢查 phase-gene 聚合是否合理。
3. 視需要再處理 `PhaseRouter`。

---

## 4. 通過標準

## 4.1 Phase 1 通過標準

- 策略在存在 pending entry order 時，不會無限制重複送新單。
- replay 不再出現因重複掛單導致的可用餘額長時間為負。
- `SwingTradingStrategy` / `TrendFollowingStrategy` 的單月交易數明顯下降到可解釋範圍。

## 4.2 Phase 2 通過標準

- 有一份逐策略正式 replay 普查結果。
- 每個策略都能被清楚歸類到：
  - 可交易且合理
  - 可交易但仍需品質調整
  - 有 setup 但成交率不足

## 4.3 Phase 3 通過標準

- `SwingTradingStrategy` / `TrendFollowingStrategy` 的 pending order 行為已被定性。
- 在合理資料區間內，不應該再出現：
  - 同一方向無上限重複加碼
  - 大量 pending order 堆積
  - 可用餘額被打成負值卻持續送單

## 4.4 整體完成標準

以下條件同時成立，才算這條線完成：

1. `StrategyArena` 與 `StrategyPortfolioOptimizer` 持續使用正式 replay。
2. 固定策略層在正式 replay 下具備可解釋的 setup / 成交結果。
3. 主要固定策略在合理資料區間內應有可解釋的交易數與持倉行為。
4. 文件已同步更新，不再宣稱假績效或舊主路徑。

---

## 5. 其他 AI 協作限制

其他 AI 在這條線上工作時，請遵守：

1. 以修改既有檔案為主，除非真的沒有合適位置才新增。
2. 不要把假績效或隨機回測重新加回去。
3. 不要為了讓策略「看起來會交易」而粗暴降低門檻。
4. 不要把 replay 層和 evaluator 層責任重新混在一起。
5. 不要恢復 `trading_strategies.py` 類似舊主路徑。
6. 每次修完都要用正式 replay 再驗證，不接受只靠靜態推論。

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

### 單策略 replay 普查

```powershell
python - <<'PY'
from backtest.service import run_strategy_instance_backtest
from bioneuronai.strategies.swing_trading import SwingTradingStrategy
from bioneuronai.strategies.trend_following import TrendFollowingStrategy

for cls in [SwingTradingStrategy, TrendFollowingStrategy]:
    result = run_strategy_instance_backtest(
        cls(),
        symbol="ETHUSDT",
        interval="1h",
        balance=10000.0,
        start_date="2025-12-22",
        end_date="2026-01-21",
        warmup_bars=10,
    )
    print(cls.__name__, result["total_trades"], result["total_return"])
PY
```

### 編譯檢查

```powershell
python -m compileall src\\bioneuronai\\strategies backtest
```

---

## 7. 一句話結論

目前正式 replay 與高階競爭框架已經接上真資料；真正還沒完成的，不是競爭框架本身，而是固定策略的 pending order / 倉位狀態契約，以及由此造成的過度加碼問題。
