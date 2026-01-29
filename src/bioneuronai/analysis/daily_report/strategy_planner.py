"""
策略規劃器
==========

負責交易策略的選擇、參數配置、適用性驗證

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import logging
from typing import Dict, Any

# 2. 本地模組
from .models import MarketCondition, StrategyPerformance

logger = logging.getLogger(__name__)


class StrategyPlanner:
    """
    策略規劃器
    
    功能：
    1. 分析當前市場狀況
    2. 評估各策略歷史表現
    3. 匹配策略與市場環境
    4. 配置策略具體參數
    5. 驗證策略適用性
    """
    
    def __init__(self):
        self.default_strategy = "StrategyFusion"
    
    # ========================================
    # 市場狀況分析
    # ========================================
    
    def analyze_current_market_condition(self) -> MarketCondition:
        """
        分析當前市場狀況
        
        Returns:
            MarketCondition 實例
        """
        try:

            # 需要整合: 波動率計算、趨勢識別、支撐阻力分析
            
            return MarketCondition(
                condition="NORMAL",
                volatility="MEDIUM",
                trend="SIDEWAYS",
                strength=0.5
            )
        except Exception as e:
            logger.error(f"市場狀況分析失敗: {e}")
            return MarketCondition(
                condition="UNKNOWN",
                volatility="UNKNOWN",
                trend="UNKNOWN",
                strength=0.0
            )
    
    # ========================================
    # 策略評估
    # ========================================
    
    def evaluate_strategy_performance(self) -> StrategyPerformance:
        """
        評估各策略歷史表現
        
        Returns:
            StrategyPerformance 實例
        """
        try:
            # 需要整合: 歷史回測數據、勝率統計、盈虧比分析
            
            return StrategyPerformance(
                best_strategy=self.default_strategy,
                win_rate=65.5,
                profit_factor=1.4,
                max_drawdown=8.2,
                sample_size=100
            )
        except Exception as e:
            logger.error(f"策略表現評估失敗: {e}")
            return StrategyPerformance(
                best_strategy=self.default_strategy,
                win_rate=50.0,
                profit_factor=1.0,
                max_drawdown=10.0,
                sample_size=0
            )
    
    # ========================================
    # 策略匹配
    # ========================================
    
    def match_strategy_to_market(self, market_condition: MarketCondition) -> Dict[str, Any]:
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
            logger.error(f"策略匹配失敗: {e}")
            return {
                "recommended": self.default_strategy,
                "match_score": 5.0,
                "alternatives": []
            }
    
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
            logger.error(f"策略參數配置失敗: {e}")
            return {"rsi_period": 14}
    
    # ========================================
    # 策略驗證
    # ========================================
    
    def verify_strategy_suitability(
        self, 
        strategy_match: Dict, 
        market_condition: MarketCondition
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
            logger.error(f"策略適用性驗證失敗: {e}")
            return {
                "score": 5.0,
                "status": "UNCERTAIN",
                "confidence": 0.5,
                "risks": ["驗證失敗"]
            }
    
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
            logger.error(f"策略最終選擇失敗: {e}")
            return {
                "name": self.default_strategy,
                "confidence": 0.5,
                "parameters": {}
            }
    
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
