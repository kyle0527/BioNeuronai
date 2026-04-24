# 方案 C：硬性體制路由（Hard Regime Routing）

> 建立日期：2026-04-24  
> 版本：v1.0  
> 系列文件：策略融合路線圖 [3/4]  
> 前置文件：`STRATEGY_FUSION_ROADMAP_OVERVIEW.md`

---

## 一、核心概念

### 1.1 軟性路由 vs 硬性路由

**現有系統（軟性路由）：**
```
體制識別 → 趨勢市
↓
_calculate_strategy_weights() 調整：
  trend_following: 0.40  （從 0.25 提升）
  breakout:        0.30  （從 0.25 提升）
  swing_trading:   0.15  （從 0.25 降低）
  mean_reversion:  0.15  （從 0.25 降低）

→ 四個策略都在跑，只是比重不同
→ mean_reversion 仍有 15% 機率發出反向信號
→ 衝突依然存在
```

**方案 C（硬性路由）：**
```
體制識別 → 趨勢市
↓
HardRouter 決定：
  trend_following: ✅ 啟動（50%倉位）
  breakout:        ✅ 啟動（50%倉位）
  swing_trading:   ❌ 完全靜默
  mean_reversion:  ❌ 完全靜默

→ 只有趨勢相關策略產生信號
→ 零衝突
```

### 1.2 業界依據

**Bridgewater All Weather（全天候策略）：**
> 不同的資產類別（股票、債券、黃金、商品）在不同的經濟體制（成長+通脹的4個象限）下表現不同，全天候的做法不是讓所有資產同時跑，而是讓適合當前體制的資產類別主導配置。

對應到策略：不同的市場體制（趨勢/震盪/高波動）適合不同的策略，硬性路由的精神是「把不適合的策略完全移開」。

**Two Sigma 市場體制識別：**
> 在明確識別體制後，使用完全不同的模型（有時甚至是完全不同的信號邏輯）。不是調整同一套邏輯的參數，而是切換到為該體制設計的專屬系統。

---

## 二、體制分類設計

### 2.1 五種核心體制

基於現有 `MarketEvaluator.identify_market_regime()` 的輸出，擴充為：

```
TRENDING_BULL  →  上升趨勢（ADX > 25, 價格 > MA20 > MA50）
TRENDING_BEAR  →  下降趨勢（ADX > 25, 價格 < MA20 < MA50）
SIDEWAYS       →  震盪（ADX < 20, 價格在支撐壓力間震盪）
HIGH_VOLATILE  →  高波動（ATR > 均值 2 倍）
TRANSITIONING  →  過渡期（體制剛切換，尚未確認）
```

### 2.2 體制 ↔ 策略對應表

| 體制 | 啟用策略 | 禁用策略 | 倉位倍數 | 原因說明 |
|------|---------|---------|---------|---------|
| TRENDING_BULL | TrendFollowing (60%) + Breakout (40%) | MeanReversion, Swing | 100% | 趨勢市均值回歸會一直逆勢 |
| TRENDING_BEAR | TrendFollowing (60%) + Breakout (40%) | MeanReversion, Swing | 100% | 同上，方向相反 |
| SIDEWAYS | MeanReversion (50%) + SwingTrading (50%) | TrendFollowing, Breakout | 80% | 震盪市趨勢策略假突破連連 |
| HIGH_VOLATILE | Breakout (70%) + TrendFollowing (30%) | MeanReversion, Swing | 50% | 高波動縮倉，Breakout 最能捕捉 |
| TRANSITIONING | 觀望（無進新倉） | 全部 | 0% | 體制不明確，等待確認 |

### 2.3 體制切換的緩衝設計

直接切換體制會導致：
- 前一體制的持倉突然被強制平倉
- 頻繁的體制抖動（震盪進入/退出趨勢體制）

**緩衝機制設計：**
```
體制確認機制：
  連續 N 根 K 線都滿足新體制條件 → 才正式切換
  N = 3（1h 資料建議值，可配置）

持倉保護機制：
  體制切換時，已有持倉繼續持有直到原有出場條件觸發
  不強制平倉（除非新體制明確禁止該方向）
  
  例外：從 TRENDING_BULL 切換到 TRENDING_BEAR
        → 多頭持倉強制平倉（方向完全相反）

冷靜期：
  體制切換後 2 根 K 線內，不開新倉（等待市場穩定）
```

---

## 三、實作規劃

### 3.1 新增檔案：`src/bioneuronai/strategies/selector/hard_router.py`

```python
"""
硬性體制路由器 (Hard Regime Router)
=====================================

核心理念：在明確的市場體制下，只啟動最適合的策略組合，
完全靜默不適合的策略，消除信號衝突。

v.s. 現有 StrategySelector（軟性路由）：
  軟性路由 → 調整比重（所有策略都有份）
  硬性路由 → 只啟動對的策略（其他完全關閉）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import numpy as np
import logging
from collections import deque

logger = logging.getLogger(__name__)


class RegimeState(Enum):
    """體制識別狀態"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILE = "high_volatile"
    TRANSITIONING = "transitioning"


@dataclass
class RegimeConfig:
    """各體制的策略配置"""
    regime: RegimeState
    active_strategies: Dict[str, float]    # 策略名 → 比重（合計=1.0）
    disabled_strategies: Set[str]
    position_size_multiplier: float        # 1.0=正常, 0.5=縮半
    allow_new_entry: bool = True           # 是否允許開新倉
    description: str = ""


@dataclass
class RegimeSignal:
    """路由器輸出的體制信號"""
    current_regime: RegimeState
    previous_regime: Optional[RegimeState]
    is_just_switched: bool          # 是否剛剛切換體制
    in_cooldown: bool               # 是否在冷靜期（切換後 N 根K線）
    active_strategies: Dict[str, float]    # 當前啟用的策略及比重
    disabled_strategies: Set[str]
    position_size_multiplier: float
    allow_new_entry: bool
    regime_confidence: float        # 0-1，體制確認信心
    bars_in_regime: int             # 在當前體制中待了幾根K線
    adx_value: float
    volatility_ratio: float


class HardRouter:
    """
    硬性體制路由器

    使用方式：
      router = HardRouter(timeframe="1h", confirm_bars=3)
      regime_signal = router.route(ohlcv_data)

      if not regime_signal.allow_new_entry:
          return  # 觀望

      for strategy_name, weight in regime_signal.active_strategies.items():
          if strategy_name not in regime_signal.disabled_strategies:
              # 只用這些策略
              signal = strategies[strategy_name].generate_signal(ohlcv_data)
    """

    # 各體制的預設配置
    REGIME_CONFIGS: Dict[RegimeState, RegimeConfig] = {
        RegimeState.TRENDING_BULL: RegimeConfig(
            regime=RegimeState.TRENDING_BULL,
            active_strategies={
                "trend_following": 0.60,
                "breakout": 0.40,
            },
            disabled_strategies={"mean_reversion", "swing_trading"},
            position_size_multiplier=1.0,
            allow_new_entry=True,
            description="上升趨勢：趨勢追蹤 + 突破，禁止均值回歸",
        ),
        RegimeState.TRENDING_BEAR: RegimeConfig(
            regime=RegimeState.TRENDING_BEAR,
            active_strategies={
                "trend_following": 0.60,
                "breakout": 0.40,
            },
            disabled_strategies={"mean_reversion", "swing_trading"},
            position_size_multiplier=1.0,
            allow_new_entry=True,
            description="下降趨勢：趨勢追蹤 + 突破，禁止均值回歸",
        ),
        RegimeState.SIDEWAYS: RegimeConfig(
            regime=RegimeState.SIDEWAYS,
            active_strategies={
                "mean_reversion": 0.50,
                "swing_trading": 0.50,
            },
            disabled_strategies={"trend_following", "breakout"},
            position_size_multiplier=0.8,
            allow_new_entry=True,
            description="震盪市：均值回歸 + 波段，禁止趨勢追蹤",
        ),
        RegimeState.HIGH_VOLATILE: RegimeConfig(
            regime=RegimeState.HIGH_VOLATILE,
            active_strategies={
                "breakout": 0.70,
                "trend_following": 0.30,
            },
            disabled_strategies={"mean_reversion", "swing_trading"},
            position_size_multiplier=0.5,
            allow_new_entry=True,
            description="高波動：縮倉 50%，主做突破",
        ),
        RegimeState.TRANSITIONING: RegimeConfig(
            regime=RegimeState.TRANSITIONING,
            active_strategies={},
            disabled_strategies={"trend_following", "mean_reversion", "swing_trading", "breakout"},
            position_size_multiplier=0.0,
            allow_new_entry=False,
            description="體制過渡期：觀望，不開新倉",
        ),
    }

    def __init__(
        self,
        timeframe: str = "1h",
        confirm_bars: int = 3,           # 體制確認所需K線數
        cooldown_bars: int = 2,          # 體制切換後冷靜期
        adx_trend_threshold: float = 25.0,
        adx_sideways_threshold: float = 20.0,
        volatility_threshold: float = 2.0,  # ATR 比值高於此值 → 高波動
    ):
        self.timeframe = timeframe
        self.confirm_bars = confirm_bars
        self.cooldown_bars = cooldown_bars
        self.adx_trend_threshold = adx_trend_threshold
        self.adx_sideways_threshold = adx_sideways_threshold
        self.volatility_threshold = volatility_threshold

        # 狀態
        self._current_regime = RegimeState.TRANSITIONING
        self._previous_regime: Optional[RegimeState] = None
        self._candidate_regime: Optional[RegimeState] = None
        self._candidate_count = 0
        self._bars_in_regime = 0
        self._cooldown_remaining = 0
        self._regime_history: deque = deque(maxlen=50)

    def route(self, ohlcv_data: np.ndarray) -> RegimeSignal:
        """
        核心路由函式

        Args:
            ohlcv_data: OHLCV 數據，shape (N, 6)：
                        [timestamp, open, high, low, close, volume]

        Returns:
            RegimeSignal：包含當前體制、啟用策略清單、倉位倍數等
        """
        # 識別當前 K 線的體制信號
        raw_regime, adx, vol_ratio = self._identify_raw_regime(ohlcv_data)

        # 更新體制確認緩衝
        confirmed_regime = self._update_regime_confirmation(raw_regime)

        # 計算信心
        confidence = self._calculate_regime_confidence(ohlcv_data, confirmed_regime, adx)

        # 更新冷靜期計數
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1

        config = self.REGIME_CONFIGS[confirmed_regime]
        return RegimeSignal(
            current_regime=confirmed_regime,
            previous_regime=self._previous_regime,
            is_just_switched=(confirmed_regime != self._previous_regime and self._bars_in_regime == 1),
            in_cooldown=(self._cooldown_remaining > 0),
            active_strategies=config.active_strategies.copy(),
            disabled_strategies=config.disabled_strategies.copy(),
            position_size_multiplier=config.position_size_multiplier,
            allow_new_entry=config.allow_new_entry and self._cooldown_remaining == 0,
            regime_confidence=confidence,
            bars_in_regime=self._bars_in_regime,
            adx_value=adx,
            volatility_ratio=vol_ratio,
        )

    def _identify_raw_regime(
        self, ohlcv_data: np.ndarray
    ) -> Tuple[RegimeState, float, float]:
        """識別當前K線的原始體制（尚未確認）"""
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]

        if len(close) < 50:
            return RegimeState.TRANSITIONING, 0.0, 1.0

        adx = self._calculate_adx(high, low, close)
        vol_ratio = self._calculate_vol_ratio(close)

        # 計算趨勢方向
        sma_20 = float(np.mean(close[-20:]))
        sma_50 = float(np.mean(close[-50:]))
        current_price = float(close[-1])

        # 高波動優先判斷（無論趨勢方向）
        if vol_ratio > self.volatility_threshold:
            return RegimeState.HIGH_VOLATILE, adx, vol_ratio

        # 趨勢判斷
        if adx > self.adx_trend_threshold:
            if current_price > sma_20 and sma_20 > sma_50:
                return RegimeState.TRENDING_BULL, adx, vol_ratio
            elif current_price < sma_20 and sma_20 < sma_50:
                return RegimeState.TRENDING_BEAR, adx, vol_ratio

        # 低 ADX → 震盪
        if adx < self.adx_sideways_threshold:
            return RegimeState.SIDEWAYS, adx, vol_ratio

        # ADX 中間值 → 過渡期
        return RegimeState.TRANSITIONING, adx, vol_ratio

    def _update_regime_confirmation(self, raw_regime: RegimeState) -> RegimeState:
        """
        體制確認緩衝：
        連續 confirm_bars 根K線都是同一體制 → 正式確認切換
        """
        if raw_regime == self._candidate_regime:
            self._candidate_count += 1
        else:
            self._candidate_regime = raw_regime
            self._candidate_count = 1

        if self._candidate_count >= self.confirm_bars:
            if self._candidate_regime != self._current_regime:
                # 正式切換體制
                self._previous_regime = self._current_regime
                self._current_regime = self._candidate_regime  # type: ignore
                self._bars_in_regime = 0
                self._cooldown_remaining = self.cooldown_bars
                logger.info(
                    f"體制切換: {self._previous_regime.value} → {self._current_regime.value}"
                )

        self._bars_in_regime += 1
        self._regime_history.append(self._current_regime)
        return self._current_regime

    def _calculate_adx(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14
    ) -> float:
        """計算 ADX"""
        n = len(close)
        if n < period * 2:
            return 20.0
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        tr = np.zeros(n)
        for i in range(1, n):
            h_diff = high[i] - high[i - 1]
            l_diff = low[i - 1] - low[i]
            if h_diff > l_diff and h_diff > 0:
                plus_dm[i] = h_diff
            if l_diff > h_diff and l_diff > 0:
                minus_dm[i] = l_diff
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
        atr = float(np.mean(tr[-period:]))
        if atr == 0:
            return 20.0
        plus_di = 100 * float(np.mean(plus_dm[-period:])) / atr
        minus_di = 100 * float(np.mean(minus_dm[-period:])) / atr
        if plus_di + minus_di == 0:
            return 20.0
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        return float(dx)

    def _calculate_vol_ratio(self, close: np.ndarray, short: int = 14, long: int = 50) -> float:
        """計算短期/長期 ATR 比值"""
        if len(close) < long + 1:
            return 1.0
        returns = np.diff(close) / close[:-1]
        short_vol = float(np.std(returns[-short:]))
        long_vol = float(np.std(returns[-long:]))
        return short_vol / long_vol if long_vol > 0 else 1.0

    def _calculate_regime_confidence(
        self,
        ohlcv_data: np.ndarray,
        regime: RegimeState,
        adx: float,
    ) -> float:
        """計算體制識別的信心分數"""
        base_confidence = min(self._candidate_count / self.confirm_bars, 1.0)

        if regime in (RegimeState.TRENDING_BULL, RegimeState.TRENDING_BEAR):
            # ADX 越高，趨勢體制越可信
            adx_bonus = min((adx - self.adx_trend_threshold) / 20, 0.3)
            return min(base_confidence + adx_bonus, 1.0)
        elif regime == RegimeState.SIDEWAYS:
            adx_bonus = min((self.adx_sideways_threshold - adx) / 20, 0.3)
            return min(base_confidence + adx_bonus, 1.0)
        else:
            return base_confidence

    def get_regime_history(self) -> List[str]:
        """返回最近的體制歷史"""
        return [r.value for r in self._regime_history]
```

### 3.2 修改 `selector/core.py`：整合 HardRouter

在 `StrategySelector.__init__()` 中新增：
```python
# 在現有軟性路由的基礎上，新增硬性路由模式
from .hard_router import HardRouter
self._hard_router: Optional[HardRouter] = None
self._use_hard_routing: bool = False  # 預設關閉，需手動啟用

def enable_hard_routing(self, confirm_bars: int = 3) -> None:
    """啟用硬性體制路由模式"""
    self._hard_router = HardRouter(timeframe=self.timeframe, confirm_bars=confirm_bars)
    self._use_hard_routing = True
    logger.info("✅ 硬性體制路由已啟用")
```

在 `recommend_strategy()` 中，如果啟用了硬性路由，則覆蓋策略比重：
```python
def recommend_strategy(self, ohlcv_data, ...) -> StrategyRecommendation:
    ...
    # 新增：硬性路由覆蓋
    if self._use_hard_routing and self._hard_router is not None:
        regime_signal = self._hard_router.route(ohlcv_data)

        # 如果不允許進新倉，直接返回觀望
        if not regime_signal.allow_new_entry:
            return StrategyRecommendation(
                primary_strategy="none",
                strategy_weights={},
                position_size_pct=0.0,
                notes=f"體制過渡期觀望 | 體制:{regime_signal.current_regime.value}",
            )

        # 覆蓋策略比重（只保留啟用的策略）
        weights = regime_signal.active_strategies.copy()
        # 調整倉位大小
        final_position_size = base_position_size * regime_signal.position_size_multiplier
        ...
```

---

## 四、完整流程圖

```
新的一根 K 線到達
        │
        ▼
HardRouter.route(ohlcv_data)
        │
        ├── 計算 ADX, 波動率比值
        ├── 判斷原始體制（raw_regime）
        ├── 緩衝確認（連續 3 根確認）
        └── 輸出 RegimeSignal
                │
                ├── allow_new_entry = False
                │       └──→ 觀望，不跑任何策略
                │
                └── allow_new_entry = True
                        │
                        ▼
              只對 active_strategies 中的策略呼叫
              strategy.generate_signal(ohlcv_data)
                        │
                        ▼
              AIStrategyFusion（只收到啟用策略的信號）
              FusionMethod.MARKET_ADAPTIVE（投票融合）
                        │
                        ▼
              FusionSignal（方向、信心、TradeSetup）
                        │
                        ▼
              倉位大小 × position_size_multiplier
                        │
                        ▼
              最終 TradeSetup → 交易引擎
```

---

## 五、配置說明

### 5.1 體制判斷閾值（可在 `config/` 中配置）

```python
# config/strategy_config.py（或 config/hard_router_config.yaml）
HARD_ROUTER_CONFIG = {
    "confirm_bars": 3,           # 體制確認需要幾根K線（建議 1h=3, 4h=2, 日K=1）
    "cooldown_bars": 2,          # 體制切換後冷靜期（建議 1h=2, 4h=1）
    "adx_trend_threshold": 25.0, # ADX > 25 → 趨勢體制
    "adx_sideways_threshold": 20.0,  # ADX < 20 → 震盪體制
    "volatility_threshold": 2.0, # ATR 短期/長期比 > 2 → 高波動
}
```

### 5.2 各體制策略比重（可客製化）

```python
# 若想修改某個體制的策略組合，可以在初始化後覆蓋
router = HardRouter()
router.REGIME_CONFIGS[RegimeState.SIDEWAYS].active_strategies = {
    "mean_reversion": 0.70,  # 震盪市更偏重均值回歸
    "swing_trading": 0.30,
}
```

---

## 六、與現有系統的相容性

方案 C 不需要破壞任何現有程式碼：

```
現有（繼續可用）：
  StrategySelector（軟性路由）
  AIStrategyFusion（MARKET_ADAPTIVE 模式）
  build_selector_performance_weights()
  load_performance_weights()

新增（可選啟用）：
  HardRouter（新檔案）
  selector.enable_hard_routing()（新方法）
```

使用者可以用 CLI 參數 `--hard-routing` 啟用，不影響預設行為：
```bash
# 現有用法（不變）
python main.py backtest --strategy-backtest

# 新增用法（啟用硬性路由）
python main.py backtest --strategy-backtest --hard-routing
```

---

## 七、效果驗證設計

### 7.1 體制識別準確度驗證

```
用 2024 年 BTC 1h 資料（840+ 每日K線）

已知的大趨勢：
  - 2024-01 ~ 2024-03：上升趨勢
  - 2024-04 ~ 2024-08：震盪
  - 2024-09 ~ 2024-11：急速上升趨勢

驗證：HardRouter 是否在正確的時間識別出正確的體制
指標：體制識別準確率（比對肉眼判斷的人工標籤）
```

### 7.2 回測對比

```
相同時段：2024-10-01 ~ 2024-12-31（趨勢市）

組 A：軟性路由（現有系統）
  - 所有策略都有比重，包含均值回歸
  - 測量 Sharpe、勝率、最大回撤

組 C：硬性路由（方案 C）
  - 趨勢市只跑 TrendFollowing + Breakout
  - 倉位 100%（非高波動期）
  - 測量 Sharpe、勝率、最大回撤

關注指標：
  - 衝突信號比率（軟性路由中有多少次是多空同時出現？）
  - 交易次數（硬性路由應該更少）
  - 勝率（硬性路由的勝率應該更高）
```

---

## 八、預估工時

| 任務 | 工時 |
|------|------|
| 實作 `hard_router.py` | 1-2 天 |
| 修改 `selector/core.py` 整合 | 0.5 天 |
| 補充 CLI `--hard-routing` 參數 | 0.5 天 |
| 體制識別回測驗證 | 1-2 天 |
| **合計** | **3-5 天** |

這是 4 個方案中**最快可以落地的**，且不破壞現有功能。

---

## 九、常見問題

**Q: 如果體制識別錯誤怎麼辦？**
> 這是硬性路由最大的風險。緩衝機制（confirm_bars=3）可以減少噪音，但不能完全避免。建議同時保留軟性路由作為備援：若硬性路由觀望時，軟性路由仍在運算，可以作為輔助參考。

**Q: 體制切換時的未平持倉怎麼處理？**
> 持倉保護：已有持倉繼續按原始 SL/TP 執行，不強制平倉。例外：TRENDING_BULL → TRENDING_BEAR 時，多頭持倉強制平倉（方向完全相反）。

**Q: 過渡期（TRANSITIONING）要觀望多久？**
> 直到連續 confirm_bars 根K線確認為非過渡期體制為止。以 1h 資料、confirm_bars=3 為例，最長等待 3 小時。

**Q: 加密貨幣 24/7 交易，沒有傳統的「開盤/收盤」，phase_router.py 的交易時段邏輯還有意義嗎？**
> 對 BTC 1h 的確意義不大，但 UTC 亞洲盤（00:00-08:00）、歐洲盤（08:00-16:00）、美洲盤（16:00-24:00）的流動性差異仍然存在。HardRouter 目前不考慮時段，這是有意為之的簡化。

---

*下一份文件：`STRATEGY_FUSION_PLAN_D_RL_AGENT.md`（深度強化學習 Agent，長期研究方向）*
