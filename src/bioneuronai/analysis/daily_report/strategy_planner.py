"""
策略規劃器
==========

負責交易策略的選擇、參數配置、適用性驗證

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import logging
import requests
from typing import Any, Dict

# 2. 本地模組
from .models import DailyMarketCondition, StrategyPerformance

logger = logging.getLogger(__name__)

# Binance Futures 公開 REST API（K 線不需要 API Key）
_BINANCE_FUTURES_API = "https://fapi.binance.com"


class StrategyPlanner:
    """
    策略規劃器

    功能：
    1. 分析當前市場狀況（Binance 即時 K 線 + MarketRegimeDetector）
    2. 評估各策略歷史表現（StrategySelector 配置，無回測時回傳零值）
    3. 匹配策略與市場環境
    4. 配置策略具體參數
    5. 驗證策略適用性
    """

    def __init__(self, connector: Any = None) -> None:
        self.connector = connector  # 保留供未來擴充使用
        self.default_strategy = "StrategyFusion"
        self.request_timeout: int = 10
        self.user_agent: str = "Mozilla/5.0"
    
    # ========================================
    # 市場狀況分析
    # ========================================
    
    def analyze_current_market_condition(self) -> DailyMarketCondition:
        """
        分析當前市場狀況。

        流程：
        1. 從 Binance /fapi/v1/klines 取得 BTCUSDT 1h 最近 200 根 K 線（公開，無需 Key）
        2. 將每根 K 線餵入 MarketRegimeDetector
        3. 呼叫 detect_regime() 取得 RegimeAnalysis
        4. 將 MarketRegime / VolatilityRegime 映射為 DailyMarketCondition

        Returns:
            DailyMarketCondition 實例（無法取得資料時各欄位為 UNKNOWN）
        """
        try:
            from ..market_regime import MarketRegimeDetector

            url = (
                f"{_BINANCE_FUTURES_API}/fapi/v1/klines"
                "?symbol=BTCUSDT&interval=1h&limit=200"
            )
            response = requests.get(
                url,
                timeout=self.request_timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            klines_raw = response.json()

            if len(klines_raw) < 100:
                raise ValueError(f"K 線資料不足（{len(klines_raw)} 根），需至少 100 根")

            detector = MarketRegimeDetector()
            for k in klines_raw:
                detector.update_data(
                    symbol="BTCUSDT",
                    price=float(k[4]),   # close
                    high=float(k[2]),    # high
                    low=float(k[3]),     # low
                    volume=float(k[5]),  # volume
                )

            analysis = detector.detect_regime("BTCUSDT")
            if analysis is None:
                raise ValueError("MarketRegimeDetector.detect_regime() 回傳 None")

            condition = self._map_regime_to_condition(analysis.current_regime)
            volatility = self._map_volatility_regime(analysis.volatility_regime)
            trend = self._map_trend_direction(analysis.trend_direction)
            strength = min(max(float(analysis.trend_score) / 100.0, 0.0), 1.0)

            logger.info(
                f"市場狀況分析完成: condition={condition}, "
                f"volatility={volatility}, trend={trend}, strength={strength:.2f}"
            )
            return DailyMarketCondition(
                condition=condition,
                volatility=volatility,
                trend=trend,
                strength=strength,
            )

        except Exception as e:
            raise RuntimeError(f"市場狀況分析失敗: {e}") from e

    # ----------------------------------------
    # 市場狀況輔助映射
    # ----------------------------------------

    def _map_regime_to_condition(self, regime: Any) -> str:
        """將 MarketRegime 枚舉映射為 DailyMarketCondition.condition 字串"""
        regime_map: Dict[str, str] = {
            "strong_uptrend":   "BULLISH",
            "uptrend":          "BULLISH",
            "weak_uptrend":     "MILD_BULLISH",
            "sideways_range":   "NORMAL",
            "weak_downtrend":   "MILD_BEARISH",
            "downtrend":        "BEARISH",
            "strong_downtrend": "BEARISH",
            "high_volatility":  "HIGH_VOLATILITY",
            "breakout":         "BREAKOUT",
            "reversal":         "REVERSAL",
        }
        key = getattr(regime, "value", str(regime))
        return regime_map.get(key, "NORMAL")

    def _map_volatility_regime(self, vol_regime: Any) -> str:
        """將 VolatilityRegime 枚舉映射為 DailyMarketCondition.volatility 字串"""
        vol_map: Dict[str, str] = {
            "very_low": "LOW",
            "low":      "LOW",
            "normal":   "MEDIUM",
            "high":     "HIGH",
            "extreme":  "EXTREME",
        }
        key = getattr(vol_regime, "value", str(vol_regime))
        return vol_map.get(key, "MEDIUM")

    def _map_trend_direction(self, direction: int) -> str:
        """將 trend_direction 整數（1 / 0 / -1）映射為趨勢字串"""
        if direction > 0:
            return "UP"
        if direction < 0:
            return "DOWN"
        return "SIDEWAYS"
    
    # ========================================
    # 策略評估
    # ========================================
    
    def evaluate_strategy_performance(self) -> StrategyPerformance:
        """
        評估各策略歷史表現。

        優先嘗試從 StrategySelector 取得基於策略配置的績效資料。
        若 StrategySelector 不可用或無回測資料，回傳 sample_size=0 的誠實空值，
        不使用任何假數據。

        Returns:
            StrategyPerformance 實例
        """
        try:
            from ...strategies.selector.core import StrategySelector

            selector = StrategySelector()
            configs = selector.get_default_configs() if hasattr(selector, "get_default_configs") else {}

            if configs:
                # 選取 win_rate 最高的配置作為代表
                best_name = self.default_strategy
                best_wr = 0.0
                best_pf = 0.0
                best_dd = 0.0

                for name, cfg in configs.items():
                    wr = float(getattr(cfg, "expected_win_rate", 0.0) or 0.0)
                    if wr > best_wr:
                        best_wr = wr
                        best_name = name
                        best_pf = float(getattr(cfg, "expected_profit_factor", 0.0) or 0.0)
                        best_dd = float(getattr(cfg, "max_drawdown_limit", 0.0) or 0.0)

                if best_wr > 0.0:
                    logger.info(
                        f"策略績效來自 StrategySelector 配置: "
                        f"{best_name} win_rate={best_wr:.1f}%"
                    )
                    return StrategyPerformance(
                        best_strategy=best_name,
                        win_rate=best_wr,
                        profit_factor=best_pf,
                        max_drawdown=best_dd,
                        sample_size=0,   # 來自配置定義，非實測數據
                    )

        except Exception as e:
            logger.warning(f"StrategySelector 不可用: {e}")

        # 無任何績效資料：回傳誠實的零值（sample_size=0 表示無實測數據）
        logger.info("無回測資料，以 StrategyFusion 為預設策略，績效指標尚無實測數據")
        return StrategyPerformance(
            best_strategy=self.default_strategy,
            win_rate=0.0,
            profit_factor=0.0,
            max_drawdown=0.0,
            sample_size=0,
        )
    
    # ========================================
    # 策略匹配
    # ========================================
    
    def match_strategy_to_market(self, market_condition: DailyMarketCondition) -> Dict[str, Any]:
        """
        匹配策略與市場環境
        
        Args:
            market_condition: 市場狀況
        
        Returns:
            策略匹配結果
        """
        try:

            # 根據市場波動性、趨勢強度選擇最適合的策略
            
            strategy_map = {
                "HIGH": ["BreakoutStrategy", "TrendFollowing"],
                "MEDIUM": [self.default_strategy, "RSI_Divergence"],
                "LOW": ["MeanReversion", "RangeTrading"]
            }
            
            candidates = strategy_map.get(market_condition.volatility, [self.default_strategy])
            
            return {
                "recommended": candidates[0],
                "match_score": 8.5,
                "alternatives": candidates[1:] if len(candidates) > 1 else [],
                "reason": f"市場波動率 {market_condition.volatility}"
            }
        except Exception as e:
            raise RuntimeError(f"策略匹配失敗: {e}") from e
    
    # ========================================
    # 策略配置
    # ========================================
    
    def configure_strategy_parameters(self, strategy_name: str) -> Dict[str, Any]:
        """
        配置策略具體參數
        
        Args:
            strategy_name: 策略名稱
        
        Returns:
            策略參數配置
        """
        try:
            # 預設參數配置
            default_config = {
                "rsi_period": 14,
                "macd_config": {"fast": 12, "slow": 26, "signal": 9},
                "bollinger_periods": 20,
                "risk_multiplier": 1.0,
                "stop_loss_pct": 2.0,
                "take_profit_pct": 4.0
            }
            
            # 根據策略名稱定制參數
            strategy_configs = {
                "StrategyFusion": {
                    **default_config,
                    "fusion_weight": {"rsi": 0.3, "macd": 0.3, "bollinger": 0.4}
                },
                "RSI_Divergence": {
                    **default_config,
                    "rsi_oversold": 30,
                    "rsi_overbought": 70
                },
                "BreakoutStrategy": {
                    **default_config,
                    "breakout_threshold": 1.5,
                    "volume_multiplier": 2.0
                }
            }
            
            return strategy_configs.get(strategy_name, default_config)
            
        except Exception as e:
            raise RuntimeError(f"策略參數配置失敗: {e}") from e
    
    # ========================================
    # 策略驗證
    # ========================================
    
    def verify_strategy_suitability(
        self, 
        strategy_match: Dict, 
        market_condition: DailyMarketCondition
    ) -> Dict[str, Any]:
        """
        驗證策略適用性
        
        Args:
            strategy_match: 策略匹配結果
            market_condition: 市場狀況
        
        Returns:
            適用性驗證結果
        """
        try:
            match_score = strategy_match.get("match_score", 5.0)
            
            # 計算適用性評分
            score = match_score
            
            # 檢查市場趨勢與策略適配
            if market_condition.condition == "UNKNOWN":
                score -= 2.0
            
            # 檢查波動率適配
            if market_condition.volatility == "EXTREME":
                score -= 1.5
            
            # 判斷狀態
            if score >= 8.0:
                status = "EXCELLENT"
                confidence = 0.9
            elif score >= 6.5:
                status = "SUITABLE"
                confidence = 0.75
            elif score >= 5.0:
                status = "ACCEPTABLE"
                confidence = 0.6
            else:
                status = "UNSUITABLE"
                confidence = 0.3
            
            risks = []
            if market_condition.volatility in ["HIGH", "EXTREME"]:
                risks.append("市場波動風險")
            if market_condition.condition == "UNKNOWN":
                risks.append("市場狀況不明")
            
            return {
                "score": round(score, 1),
                "status": status,
                "confidence": confidence,
                "risks": risks,
                "recommendation": self._get_suitability_recommendation(status)
            }
            
        except Exception as e:
            raise RuntimeError(f"策略適用性驗證失敗: {e}") from e
    
    def _get_suitability_recommendation(self, status: str) -> str:
        """獲取適用性建議"""
        recommendations = {
            "EXCELLENT": "強烈推薦執行",
            "SUITABLE": "可以執行，注意風險管理",
            "ACCEPTABLE": "謹慎執行，密切監控",
            "UNSUITABLE": "不建議執行，等待更好時機"
        }
        return recommendations.get(status, "需要進一步評估")
    
    # ========================================
    # 最終選擇
    # ========================================
    
    def finalize_strategy_selection(
        self, 
        strategy_match: Dict, 
        suitability: Dict
    ) -> Dict[str, Any]:
        """
        最終確定交易策略
        
        Args:
            strategy_match: 策略匹配結果
            suitability: 適用性驗證結果
        
        Returns:
            最終策略選擇結果
        """
        try:
            strategy_name = strategy_match.get("recommended", self.default_strategy)
            
            return {
                "name": strategy_name,
                "confidence": suitability.get("confidence", 0.5),
                "parameters": self.configure_strategy_parameters(strategy_name),
                "status": suitability.get("status", "UNCERTAIN"),
                "score": suitability.get("score", 5.0),
                "risks": suitability.get("risks", [])
            }
        except Exception as e:
            raise RuntimeError(f"策略最終選擇失敗: {e}") from e
    
    # ========================================
    # 回測驗證
    # ========================================
    
    def perform_plan_backtest(self) -> Dict[str, Any]:
        """
        執行計劃回測驗證
        
        Returns:
            回測結果
        """
        # 未實現：需要整合真實的回測系統
        logger.warning("⚠️ 回測功能未實現，跳過此步驟")
        
        return {
            "status": "NOT_IMPLEMENTED",
            "annual_return": None,
            "max_drawdown": None,
            "sharpe_ratio": None,
            "win_rate": None,
            "note": "回測系統需要實現 - 建議使用 data_downloads/run_backtest.py"
        }
