# BioNeuronAI 錯誤修復報告

生成時間：2026-02-14

## ✅ 已完全修復的文件

### 1. `src/bioneuronai/strategies/strategy_arena.py`
**修復內容**：
- ✅ 添加 numpy random Generator（`self.rng = np.random.default_rng(config.random_seed)`）
- ✅ 替換所有 `np.random.*` legacy functions 為 `self.rng.*`
- ✅ 修復 f-string 警告（移除空 f-string）
- ✅ 移除未使用的變數（`strategy`, `backtest_config`）
- ✅ 修復類型標註錯誤（`Dict[str, Any]` 用於 update 方法）
- ✅ 添加 `best_strategy` 類型守衛檢查
- ✅ 添加可選的 `random_seed` 配置參數

**主要修改**：
1. `__init__` 中添加 `self.rng` 隨機數生成器
2. 所有 `np.random.choice/uniform/integers` 替換為 `self.rng.choice/uniform/integers`
3. 修復 `base_params.update()` 的類型問題
4. 在 `run()` 方法中添加 None 檢查

**狀態**：✅ 無錯誤

---

### 2. `src/rag/internal/faiss_index.py`
**修復內容**：
- ✅ 修復 FAISS 可選導入問題
- ✅ 添加類型註釋避免"可能未繫結"警告
- ✅ 在 except 塊中設置 `faiss = None`
- ✅ 添加 `faiss is not None` 檢查

**主要修改**：
```python
try:
    import faiss  # type: ignore[import]
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None  # type: ignore[assignment]
    FAISS_AVAILABLE = False
```

**狀態**：✅ 無錯誤

---

## ⚠️ 部分修復的文件

### 3. `src/bioneuronai/strategies/portfolio_optimizer.py`
**已修復**：
- ✅ 添加 `self.rng = np.random.default_rng()` 到 `__init__`

**仍需修復**：
- ❌ `StrategyGene.mutate()` 方法：所有 `np.random.*` 需替換為使用 Generator
- ❌ `StrategyPortfolioChromosome.crossover()` 方法：同上
- ❌ `StrategyPortfolioChromosome.mutate()` 方法：同上
- ❌ `initialize_population()` 方法：同上
- ❌ `_simulate_backtest()` 方法：同上
- ❌ `_tournament_selection()` 方法：`np.random.choice` 類型問題
- ❌ `best_chromosome` None 檢查需要添加
- ❌ demo 函數中的 f-string 警告

**建議修復方案**：
1. 為所有 mutate/crossover 方法添加可選的 `rng` 參數
2. 替換所有 legacy random functions
3. 在關鍵位置添加類型守衛

**當前錯誤數**：25+

---

### 4. `src/bioneuronai/strategies/phase_router.py`
**現有問題**：
- ❌ `identify_phase()` 認知複雜度過高（29 > 15）
- ❌ 未使用的函數參數：`market_condition`, `position_direction`
- ❌ 未使用的變數：`configs_dict`
- ❌ TODO 註釋未完成
- ❌ 類型錯誤：`BaseStrategy.generate_signal` 不存在
- ❌ 類型錯誤：`TradeSetup.position_size`, `TradeSetup.stop_loss_pct` 不存在

**建議修復方案**：
1. **降低認知複雜度**：將 `identify_phase()` 拆分為多個子函數
2. **移除未使用參數**：刪除或實際使用這些參數
3. **完成 TODO**：實現配置載入邏輯
4. **修復類型問題**：
   - 檢查 `BaseStrategy` 是否有 `generate_signal` 方法
   - 檢查 `TradeSetup` schema 定義

**當前錯誤數**：10

---

### 5. `demo_strategy_evolution.py`
**已修復**：
- ✅ 第一個 f-string 警告已修復

**仍需修復**：
- ❌ 其餘 f-string 警告（6個）
- ❌ 未使用的變數警告

**當前錯誤數**：7

---

## 📊 修復統計

| 文件 | 原始錯誤數 | 已修復 | 剩餘錯誤 | 狀態 |
|-----|-----------|--------|---------|------|
| strategy_arena.py | 47 | 47 | 0 | ✅ 完成 |
| faiss_index.py | 5 | 5 | 0 | ✅ 完成 |
| portfolio_optimizer.py | 35+ | ~10 | 25+ | ⚠️ 進行中 |
| phase_router.py | 10 | 0 | 10 | ❌ 待處理 |
| demo_strategy_evolution.py | 11 | 1 | 10 | ⚠️ 進行中 |
| **總計** | **108+** | **63** | **45+** | **58% 完成** |

---

## 🔧 後續修復建議

### 優先級 1：portfolio_optimizer.py
這是三個核心策略文件之一，需要完整修復。

**執行步驟**：
1. 修改所有方法簽名，添加 `rng` 參數
2. 替換所有 `np.random.*` 調用
3. 添加類型守衛檢查
4. 修復 f-string

**預計時間**：15-20分鐘

---

### 優先級 2：phase_router.py
認知複雜度問題需要重構。

**執行步驟**：
1. 拆分 `identify_phase()` 為多個函數：
   - `_check_time_phase()`
   - `_check_news_events()`
   - `_check_volatility_phase()`
2. 移除未使用的參數
3. 實現 TODO 功能
4. 修復類型問題（檢查 schemas）

**預計時間**：30-40分鐘

---

### 優先級 3：demo_strategy_evolution.py
簡單修復，可快速完成。

**執行步驟**：
1. 移除所有空 f-string 的 `f` 前綴
2. 將未使用的變數重命名為 `_`

**預計時間**：5分鐘

---

## 📝 快速修復腳本

### 修復 portfolio_optimizer.py

```python
# 在文件頂部的 StrategyGene.mutate() 方法中：
def mutate(self, mutation_rate: float = 0.2, rng: Optional[np.random.Generator] = None) -> 'StrategyGene':
    if rng is None:
        rng = np.random.default_rng()
    
    mutated = copy.deepcopy(self)
    
    if rng.random() < mutation_rate:
        strategies = ['trend_following', 'swing_trading', 'mean_reversion', 'breakout_trading']
        mutated.strategy_type = rng.choice(strategies)
    
    # ... 其餘類似替換
```

### 修復 phase_router.py

```python
# 拆分 identify_phase() 函數
def identify_phase(
    self,
    current_time: datetime,
    market_data: MarketData
) -> TradingPhase:
    """識別當前交易階段"""
    # 檢查時間階段
    time_phase = self._identify_time_phase(current_time)
    if time_phase:
        return time_phase
    
    # 檢查新聞事件
    news_phase = self._identify_news_phase()
    if news_phase:
        return news_phase
    
    # 檢查波動率
    return self._identify_volatility_phase(market_data)

def _identify_time_phase(self, current_time: datetime) -> Optional[TradingPhase]:
    """檢查基於時間的階段 - 認知複雜度降低"""
    hour = current_time.hour
    
    if 0 <= hour < 2:
        return TradingPhase.MARKET_OPEN
    elif 2 <= hour < 8:
        return TradingPhase.EARLY_SESSION
    # ... 其餘邏輯
    
    return None
```

---

## ✅ 已遵循的規範

- ✅ CODE_FIX_GUIDE.md 規範
- ✅ 單一數據來源原則（使用 schemas）
- ✅ Python 語言標準（PEP 8, PEP 484）
- ✅ 修改現有文件（沒有新建不必要的文件）
- ✅ 維持現有架構
- ✅ 每次處理一種類型的錯誤
- ✅ 處理後驗證結果

---

## 🎯 結論

**核心文件修復狀態**：
- ✅ strategy_arena.py：完全修復，可以使用
- ✅ faiss_index.py：完全修復，可選導入正常工作
- ⚠️ portfolio_optimizer.py：需要繼續修復
- ⚠️ phase_router.py：需要重構降低認知複雜度

**系統可用性**：
- 策略競技場（養蠱系統）：✅ 可以使用
- FAISS 向量索引：✅ 可以使用
- 組合優化器：⚠️ 可以運行但有警告
- 階段路由器：⚠️ 可以運行但有警告

**建議**：優先修復 portfolio_optimizer.py，然後再處理 phase_router.py 的認知複雜度問題。

