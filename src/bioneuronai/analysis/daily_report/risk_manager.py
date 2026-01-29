"""
風險管理器
==========

負責風險參數計算、交易對篩選、倉位管理

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import logging
from typing import Dict, List, Any

# 2. 本地模組
from .models import RiskParameters, TradingPairsPriority, MarketCondition

logger = logging.getLogger(__name__)


class RiskManager:
    """
    風險管理器
    
    功能：
    1. 帳戶資金分析
    2. 計算基礎風險參數
    3. 根據波動率調整風險
    4. 配置持倉管理規則
    5. 計算交易頻率限制
    6. 交易對篩選與優先級排序
    """
    
    def __init__(self):
        self.default_risk = {
            "single_trade": 1.0,  # 1%
            "daily_limit": 3.0,   # 3%
            "max_positions": 1
        }
    
    # ========================================
    # 帳戶分析
    # ========================================
    
    def analyze_account_funds(self) -> Dict[str, Any]:
        """
        分析帳戶資金狀況
        
        Returns:
            帳戶分析結果
        """
        try:
            # 需要整合真實的帳戶查詢 API
            # 從交易所獲取真實帳戶餘額、可用資金、凍結資金
            
            return {
                "available": 5000.0,
                "total": 5500.0,
                "in_use": 500.0,
                "risk_tolerance": "MEDIUM",
                "max_position_size": 500.0,
                "leverage": 1.0
            }
        except Exception as e:
            logger.error(f"帳戶資金分析失敗: {e}")
            return {
                "available": 0.0,
                "risk_tolerance": "LOW",
                "max_position_size": 0.0
            }
    
    # ========================================
    # 風險參數計算
    # ========================================
    
    def calculate_base_risk_parameters(self, account_analysis: Dict) -> Dict[str, Any]:
        """
        計算基礎風險參數
        
        Args:
            account_analysis: 帳戶分析結果
        
        Returns:
            基礎風險參數
        """
        try:
            risk_tolerance = account_analysis.get("risk_tolerance", "LOW")
            
            # 根據風險承受度調整參數
            risk_profiles = {
                "LOW": {
                    "single_trade": 1.0,
                    "daily_limit": 3.0,
                    "max_positions": 1
                },
                "MEDIUM": {
                    "single_trade": 2.0,
                    "daily_limit": 6.0,
                    "max_positions": 3
                },
                "HIGH": {
                    "single_trade": 3.0,
                    "daily_limit": 10.0,
                    "max_positions": 5
                }
            }
            
            return risk_profiles.get(risk_tolerance, self.default_risk)
            
        except Exception as e:
            logger.error(f"基礎風險參數計算失敗: {e}")
            return self.default_risk
    
    def adjust_risk_for_volatility(
        self, 
        base_risk: Dict, 
        market_condition: MarketCondition
    ) -> Dict[str, Any]:
        """
        根據市場波動調整風險
        
        Args:
            base_risk: 基礎風險參數
            market_condition: 市場狀況
        
        Returns:
            調整後的風險參數
        """
        try:
            volatility = market_condition.volatility
            
            # 波動率調整係數
            adjustment_factors = {
                "LOW": 1.2,      # 低波動可以增加風險
                "MEDIUM": 1.0,   # 正常波動
                "HIGH": 0.8,     # 高波動降低風險
                "EXTREME": 0.5   # 極端波動大幅降低
            }
            
            adjustment_factor = adjustment_factors.get(volatility, 1.0)
            
            return {
                "single_trade": base_risk["single_trade"] * adjustment_factor,
                "daily_limit": base_risk["daily_limit"] * adjustment_factor,
                "max_positions": base_risk.get("max_positions", 1),
                "adjustment_factor": adjustment_factor,
                "reason": f"市場波動率: {volatility}"
            }
        except Exception as e:
            logger.error(f"風險波動調整失敗: {e}")
            return {**base_risk, "adjustment_factor": 1.0}
    
    # ========================================
    # 持倉管理
    # ========================================
    
    def configure_position_management(self, max_positions: int = 3) -> Dict[str, Any]:
        """
        配置持倉管理規則
        
        Args:
            max_positions: 最大持倉數
        
        Returns:
            持倉管理配置
        """
        try:
            return {
                "max_positions": max_positions,
                "correlation_limit": 0.7,  # 相關性上限
                "position_sizing": "EQUAL_WEIGHT",  # 等權重
                "rebalance_threshold": 0.1,  # 重平衡閾值 10%
                "stop_loss_multiplier": 1.0,
                "take_profit_multiplier": 2.0
            }
        except Exception as e:
            logger.error(f"持倉管理配置失敗: {e}")
            return {"max_positions": 1}
    
    def calculate_trading_frequency(
        self, 
        market_condition: MarketCondition
    ) -> Dict[str, Any]:
        """
        計算交易頻率限制
        
        Args:
            market_condition: 市場狀況
        
        Returns:
            交易頻率限制
        """
        try:
            # 根據市場狀況調整頻率
            if market_condition.volatility in ["HIGH", "EXTREME"]:
                daily_max = 3
                interval_minutes = 60
            elif market_condition.volatility == "MEDIUM":
                daily_max = 5
                interval_minutes = 30
            else:
                daily_max = 8
                interval_minutes = 15
            
            return {
                "daily_max": daily_max,
                "interval_minutes": interval_minutes,
                "cooling_period": 60,  # 冷卻期（分鐘）
                "max_consecutive_losses": 3  # 連續虧損上限
            }
        except Exception as e:
            logger.error(f"交易頻率計算失敗: {e}")
            return {
                "daily_max": 3,
                "interval_minutes": 60
            }
    
    def integrate_risk_parameters(
        self, 
        volatility_adjusted_risk: Dict, 
        position_rules: Dict, 
        frequency_limits: Dict
    ) -> RiskParameters:
        """
        整合風險參數
        
        Args:
            volatility_adjusted_risk: 波動率調整後的風險
            position_rules: 持倉規則
            frequency_limits: 頻率限制
        
        Returns:
            RiskParameters 實例
        """
        try:
            return RiskParameters(
                single_trade_risk=volatility_adjusted_risk.get("single_trade", 1.0),
                daily_max_loss=volatility_adjusted_risk.get("daily_limit", 3.0),
                max_positions=position_rules.get("max_positions", 1),
                max_daily_trades=frequency_limits.get("daily_max", 3),
                adjustment_factor=volatility_adjusted_risk.get("adjustment_factor", 1.0)
            )
        except Exception as e:
            logger.error(f"風險參數整合失敗: {e}")
            return RiskParameters(
                single_trade_risk=1.0,
                daily_max_loss=3.0,
                max_positions=1,
                max_daily_trades=3
            )
    
    # ========================================
    # 交易對篩選
    # ========================================
    
    def scan_available_trading_pairs(self) -> Dict[str, Any]:
        """
        掃描所有可用交易對
        
        Returns:
            分類的交易對列表
        """
        try:
            # 需要整合真實的交易所 API
            # 從 Binance 獲取所有可用交易對及其狀態
            
            return {
                "all": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"],
                "major": ["BTCUSDT", "ETHUSDT"],
                "altcoins": ["ADAUSDT", "DOTUSDT", "LINKUSDT"],
                "total_count": 5
            }
        except Exception as e:
            logger.error(f"交易對掃描失敗: {e}")
            return {
                "all": ["BTCUSDT"],
                "major": ["BTCUSDT"],
                "altcoins": []
            }
    
    def analyze_liquidity_metrics(self, available_pairs: Dict) -> Dict[str, Any]:
        """
        分析流動性指標
        
        Args:
            available_pairs: 可用交易對
        
        Returns:
            流動性分析結果
        """
        try:
            # 需要整合真實的流動性分析
            # 計算: 24h交易量、買賣價差、訂單簿深度
            
            all_pairs = available_pairs.get("all", [])
            
            # 簡化版：假設主流幣流動性高
            high_liquidity = [p for p in all_pairs if p in ["BTCUSDT", "ETHUSDT", "BNBUSDT"]]
            
            return {
                "high_liquidity": high_liquidity,
                "medium_liquidity": [p for p in all_pairs if p not in high_liquidity],
                "low_liquidity": [],
                "avg_spread": 0.01,  # 0.01%
                "volume_24h": dict.fromkeys(high_liquidity, 1000000)
            }
        except Exception as e:
            logger.error(f"流動性分析失敗: {e}")
            return {
                "high_liquidity": ["BTCUSDT"],
                "avg_spread": 0.02
            }
    
    def check_volatility_compatibility(
        self, 
        liquidity_analysis: Dict
    ) -> Dict[str, Any]:
        """
        檢查波動率適配性
        
        Args:
            liquidity_analysis: 流動性分析
        
        Returns:
            波動率適配結果
        """
        try:
            high_liquidity_pairs = liquidity_analysis.get("high_liquidity", [])
            
            return {
                "compatible": high_liquidity_pairs,
                "incompatible": [],
                "best_match": high_liquidity_pairs[0] if high_liquidity_pairs else "BTCUSDT",
                "volatility_range": "MEDIUM_TO_HIGH"
            }
        except Exception as e:
            logger.error(f"波動率適配性檢查失敗: {e}")
            return {
                "compatible": ["BTCUSDT"],
                "best_match": "BTCUSDT"
            }
    
    def apply_risk_filters(
        self, 
        volatility_match: Dict, 
        integrated_risk: RiskParameters
    ) -> Dict[str, Any]:
        """
        應用風險過濾器
        
        Args:
            volatility_match: 波動率匹配結果
            integrated_risk: 整合風險參數
        
        Returns:
            過濾後的交易對
        """
        try:
            compatible_pairs = volatility_match.get("compatible", [])
            
            # 根據風險參數過濾
            if integrated_risk.single_trade_risk < 1.5:
                approved = [p for p in compatible_pairs if p in ["BTCUSDT", "ETHUSDT"]]
            else:
                approved = compatible_pairs
            
            excluded = [p for p in compatible_pairs if p not in approved]
            
            return {
                "approved": approved,
                "excluded": excluded,
                "reason": f"風險級別: {integrated_risk.single_trade_risk:.1f}%"
            }
        except Exception as e:
            logger.error(f"風險過濾失敗: {e}")
            return {
                "approved": ["BTCUSDT"],
                "excluded": []
            }
    
    def prioritize_trading_pairs(self, risk_filtered: Dict) -> TradingPairsPriority:
        """
        生成交易對優先級清單
        
        Args:
            risk_filtered: 風險過濾結果
        
        Returns:
            TradingPairsPriority 實例
        """
        try:
            approved = risk_filtered.get("approved", [])
            excluded = risk_filtered.get("excluded", [])
            
            # 優先級排序：BTC > ETH > 其他
            priority_order = ["BTCUSDT", "ETHUSDT"]
            
            primary = []
            backup = []
            
            for pair in approved:
                if pair in priority_order:
                    primary.append(pair)
                else:
                    backup.append(pair)
            
            # 確保順序
            primary.sort(key=lambda x: priority_order.index(x) if x in priority_order else 999)
            
            return TradingPairsPriority(
                primary=primary[:3],  # 最多3個主要交易對
                backup=backup[:2],    # 最多2個備用交易對
                excluded=excluded
            )
        except Exception as e:
            logger.error(f"交易對優先級排序失敗: {e}")
            return TradingPairsPriority(
                primary=["BTCUSDT"],
                backup=[],
                excluded=[]
            )
    
    # ========================================
    # 每日限制計算
    # ========================================
    
    def calculate_comprehensive_daily_limits(
        self, 
        account_analysis: Dict, 
        integrated_risk: RiskParameters
    ) -> Dict[str, Any]:
        """
        計算每日交易限制
        
        Args:
            account_analysis: 帳戶分析
            integrated_risk: 整合風險參數
        
        Returns:
            每日限制配置
        """
        try:
            account_balance = account_analysis.get("available", 1000.0)
            max_daily_loss_pct = integrated_risk.daily_max_loss / 100
            single_trade_risk_pct = integrated_risk.single_trade_risk / 100
            
            return {
                "max_loss_usd": round(account_balance * max_daily_loss_pct, 2),
                "max_single_trade_usd": round(account_balance * single_trade_risk_pct, 2),
                "max_trades": integrated_risk.max_daily_trades,
                "max_positions": integrated_risk.max_positions,
                "daily_reset_time": "00:00 UTC"
            }
        except Exception as e:
            logger.error(f"每日限制計算失敗: {e}")
            return {
                "max_loss_usd": 50.0,
                "max_single_trade_usd": 20.0,
                "max_trades": 3
            }
