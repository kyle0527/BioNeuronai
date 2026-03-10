"""
市場評估器 - Market Evaluator

職責:
1. 市場體制識別 (來自 v1 + v2)
2. 策略評分與篩選
3. ADX 等技術指標計算

Created: 2026-01-25
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

from .types import (
    StrategyType,
    MarketRegime,
    StrategyConfigTemplate,
    InternalPerformanceMetrics,
    STRATEGY_MARKET_FIT,
)
from .configs import get_default_strategy_configs

logger = logging.getLogger(__name__)


class MarketEvaluator:
    """
    市場評估器 - 識別市場狀態並評估策略適配度
    
    整合:
    - v1 的詳細評分邏輯
    - v2 的 ADX 計算和體制識別
    """
    
    def __init__(self):
        self.strategy_configs = get_default_strategy_configs()
        self._performance_history: Dict[str, List[Dict]] = {}
    
    def identify_market_regime(self, ohlcv_data: np.ndarray) -> MarketRegime:
        """
        識別市場體制 (來自 v2)
        
        Args:
            ohlcv_data: OHLCV 數據 (timestamp, open, high, low, close, volume)
            
        Returns:
            MarketRegime 枚舉值
        """
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        n = len(close)
        if n < 50:
            return MarketRegime.SIDEWAYS_LOW_VOL
        
        # 計算移動平均
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:])
        
        # 趨勢強度
        trend_strength = (close[-1] - sma_50) / sma_50 * 100
        
        # 波動率
        returns = np.diff(close[-21:]) / close[-21:-1]
        volatility = np.std(returns)
        avg_vol = np.std(np.diff(close[-50:-20]) / close[-50:-21])
        vol_ratio = volatility / avg_vol if avg_vol > 0 else 1
        
        # 價格範圍
        range_20 = (max(high[-20:]) - min(low[-20:])) / np.mean(close[-20:])
        
        # ADX (趨勢強度)
        adx = self._calculate_adx(high, low, close)
        
        # 判斷市場體制
        if adx > 25:
            if close[-1] > sma_20 > sma_50 and trend_strength > 3:
                return MarketRegime.TRENDING_BULL
            elif close[-1] < sma_20 < sma_50 and trend_strength < -3:
                return MarketRegime.TRENDING_BEAR
        
        if vol_ratio > 1.5:
            return MarketRegime.VOLATILE_UNCERTAIN
        
        if range_20 < 0.04 and vol_ratio < 0.8:
            return MarketRegime.BREAKOUT_POTENTIAL
        
        if range_20 < 0.06:
            if vol_ratio < 1:
                return MarketRegime.SIDEWAYS_LOW_VOL
            else:
                return MarketRegime.SIDEWAYS_HIGH_VOL
        
        return MarketRegime.SIDEWAYS_HIGH_VOL
    
    def _calculate_adx(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> float:
        """計算 ADX (平均趨向指標)"""
        n = len(close)
        if n < period * 2:
            return 20.0
        
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        tr = np.zeros(n)
        
        for i in range(1, n):
            h_diff = high[i] - high[i-1]
            l_diff = low[i-1] - low[i]
            
            if h_diff > l_diff and h_diff > 0:
                plus_dm[i] = h_diff
            if l_diff > h_diff and l_diff > 0:
                minus_dm[i] = l_diff
            
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
        
        atr = np.mean(tr[-period:])
        if atr == 0:
            return 20.0
            
        plus_di = 100 * np.mean(plus_dm[-period:]) / atr
        minus_di = 100 * np.mean(minus_dm[-period:]) / atr
        
        if plus_di + minus_di == 0:
            return 20.0
            
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        return float(dx)
    
    def calculate_volatility(self, ohlcv_data: np.ndarray) -> Tuple[float, str]:
        """
        計算波動率並分級
        
        Returns:
            (volatility_value, risk_level)
        """
        close = ohlcv_data[:, 4]
        returns = np.diff(close[-20:]) / close[-20:-1]
        volatility = float(np.std(returns))
        
        risk_level = self._classify_risk_level(volatility)
        
        return volatility, risk_level
    
    def _classify_risk_level(self, volatility: float) -> str:
        """根據波動率分類風險等級"""
        if volatility > 0.03:
            return "high"
        elif volatility < 0.01:
            return "low"
        return "medium"
    
    def score_strategies(
        self,
        market_regime: MarketRegime,
        account_balance: float = 10000.0,
        preferences: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        對所有策略進行評分 (整合 v1 + v2)
        
        Args:
            market_regime: 當前市場體制
            account_balance: 帳戶餘額
            preferences: 用戶偏好 (可選)
            
        Returns:
            策略名稱 -> 評分 的字典
        """
        scores = {}
        
        for name, config in self.strategy_configs.items():
            scores[name] = self._calculate_single_strategy_score(
                config, market_regime, account_balance, preferences
            )
        
        return scores
    
    def _calculate_single_strategy_score(
        self,
        config: StrategyConfigTemplate,
        market_regime: MarketRegime,
        account_balance: float,
        preferences: Optional[Dict]
    ) -> float:
        """計算單一策略的評分"""
        score = 0.0
        
        # 1. 市場適配度 (40%)
        score += self._score_market_fit(config.strategy_type, market_regime)
        
        # 2. 資金要求 (20%)
        score += self._score_capital_fit(config, account_balance)
        
        # 3. 歷史績效 (20%)
        score += 0.2 * self._get_historical_performance_score(config.name)
        
        # 4. 策略本身指標 (20%)
        score += self._score_strategy_quality(config)
        
        # 5. 偏好調整
        score += self._apply_preference_adjustments(config, preferences)
        
        return max(0.0, min(1.0, score))
    
    def _score_market_fit(
        self,
        strategy_type: StrategyType,
        market_regime: MarketRegime
    ) -> float:
        """計算市場適配度分數 (40%)"""
        fit = STRATEGY_MARKET_FIT.get(strategy_type, {})
        if market_regime in fit.get('best', []):
            return 0.4
        if market_regime in fit.get('good', []):
            return 0.2
        if market_regime in fit.get('avoid', []):
            return -0.2
        return 0.1  # 中性
    
    def _score_capital_fit(
        self,
        config: StrategyConfigTemplate,
        account_balance: float
    ) -> float:
        """計算資金適配度分數 (20%)"""
        if config.min_capital <= account_balance:
            capital_ratio = min(1.0, account_balance / (config.min_capital * 5))
            return 0.2 * capital_ratio
        else:
            return -0.1  # 資金不足扣分
    
    def _score_strategy_quality(self, config: StrategyConfigTemplate) -> float:
        """計算策略品質分數 (20%)"""
        # 基於 sharpe_ratio 和 win_rate
        quality_score = (config.sharpe_ratio / 3.0 + config.win_rate) / 2
        return 0.2 * min(1.0, quality_score)
    
    def _apply_preference_adjustments(
        self,
        config: StrategyConfigTemplate,
        preferences: Optional[Dict]
    ) -> float:
        """應用偏好調整"""
        score = 0.0
        if preferences:
            if 'prefer_simple' in preferences and config.complexity.value == 'simple':
                score += 0.05
            if 'max_drawdown' in preferences:
                if config.max_drawdown > preferences['max_drawdown']:
                    score -= 0.1
        return score
    
    def _get_historical_performance_score(self, strategy_name: str) -> float:
        """獲取歷史績效評分"""
        history = self._performance_history.get(strategy_name, [])
        if not history:
            return 0.5  # 無歷史數據，給中性分
        
        # 計算近期績效
        recent = history[-20:]  # 最近 20 筆
        wins = sum(1 for t in recent if t.get('r_multiple', 0) > 0)
        win_rate = wins / len(recent) if recent else 0.5
        
        return win_rate
    
    def filter_viable_strategies(
        self,
        scores: Dict[str, float],
        account_balance: float,
        min_score: float = 0.3,
        preferences: Optional[Dict] = None
    ) -> List[StrategyConfigTemplate]:
        """
        篩選可行策略 (來自 v1)
        
        Args:
            scores: 策略評分
            account_balance: 帳戶餘額
            min_score: 最低分數門檻
            preferences: 用戶偏好
            
        Returns:
            可行策略列表
        """
        viable = []
        
        for name, score in scores.items():
            if score < min_score:
                continue
            
            config = self.strategy_configs.get(name)
            if not config:
                continue
            
            # 資金檢查
            if config.min_capital > account_balance:
                continue
            
            # 複雜度檢查
            if preferences and 'max_complexity' in preferences:
                complexity_levels = {"simple": 1, "medium": 2, "complex": 3}
                max_level = preferences['max_complexity']
                if complexity_levels.get(config.complexity.value, 2) > max_level:
                    continue
            
            viable.append(config)
        
        return viable
    
    def record_performance(self, strategy_name: str, trade_result: Dict[str, Any]):
        """記錄策略績效"""
        if strategy_name not in self._performance_history:
            self._performance_history[strategy_name] = []
        
        self._performance_history[strategy_name].append(trade_result)
        
        # 保留最近 100 筆
        if len(self._performance_history[strategy_name]) > 100:
            self._performance_history[strategy_name] = \
                self._performance_history[strategy_name][-100:]
    
    def get_performance_metrics(self, strategy_name: str) -> InternalPerformanceMetrics:
        """獲取策略績效指標"""
        history = self._performance_history.get(strategy_name, [])
        
        if not history:
            return InternalPerformanceMetrics(strategy_name=strategy_name)
        
        total_trades = len(history)
        wins = sum(1 for t in history if t.get('r_multiple', 0) > 0)
        total_r = sum(t.get('r_multiple', 0) for t in history)
        
        return InternalPerformanceMetrics(
            strategy_name=strategy_name,
            total_trades=total_trades,
            win_rate=wins / total_trades if total_trades > 0 else 0,
            profit_factor=1.0 + (total_r / total_trades) if total_trades > 0 else 1.0,
            total_return=total_r * 0.01,  # 假設每 R = 1%
        )
