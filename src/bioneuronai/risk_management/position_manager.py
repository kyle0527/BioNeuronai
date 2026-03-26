"""
風險管理器 - Risk Manager

提供統一的風險參數管理和倉位計算

風險參數定義：
--------------
所有風險參數統一在此模組定義，透過 RiskParameters 類別管理
其他模組應透過導入此模組來獲取風險參數，而非自行定義

使用方式：
---------
    from bioneuronai.risk_management import RiskManager, get_risk_params
    
    # 獲取 MODERATE 等級的風險參數
    params = get_risk_params("MODERATE")
    max_risk = params.max_risk_per_trade  # 0.02 (2%)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, cast
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

def get_risk_params(level: str = "MODERATE") -> 'RiskParameters':
    """
    獲取指定風險等級的參數配置
    
    Args:
        level: 風險等級 (CONSERVATIVE, MODERATE, AGGRESSIVE, HIGH_RISK)
    
    Returns:
        RiskParameters 物件
        
    Example:
        >>> params = get_risk_params("MODERATE")
        >>> print(params.max_risk_per_trade)  # 0.02
    """
    manager = RiskManager()
    return cast(
        RiskParameters,
        manager.risk_parameters.get(level.upper(), manager.risk_parameters["MODERATE"]),
    )

class RiskLevel(Enum):
    """"""
    CONSERVATIVE = ""
    MODERATE = ""
    AGGRESSIVE = ""
    HIGH_RISK = ""

class PositionType(Enum):
    """"""
    LONG = ""
    SHORT = ""
    NEUTRAL = ""

@dataclass
class RiskParameters:
    """"""
    max_risk_per_trade: float  # 
    max_daily_risk: float      # 
    max_portfolio_risk: float  # 
    max_drawdown_limit: float  # 
    max_correlation: float     # 
    max_leverage: float        # 
    position_concentration: float  # 
    sector_concentration: float    # 
    
@dataclass
class PositionSizing:
    """"""
    symbol: str
    recommended_size: float    # 
    max_size: float           # 
    risk_amount: float        # 
    stop_loss_distance: float # 
    entry_price: float        # 
    stop_loss_price: float    # 
    take_profit_price: float  # 
    risk_reward_ratio: float  # 
    kelly_fraction: float     # 
    confidence_score: float   # 

@dataclass
class PortfolioRisk:
    """"""
    timestamp: datetime
    total_exposure: float      # 
    var_1day_95: float        # 195%VaR
    var_1day_99: float        # 199%VaR
    expected_shortfall: float  # 
    maximum_drawdown: float    # 
    correlation_matrix: Dict   # 
    concentration_risk: Dict   # 
    liquidity_risk: float     # 
    leverage_ratio: float     # 
    risk_adjusted_return: float # 

@dataclass
class RiskAlert:
    """"""
    alert_type: str    # 
    severity: str      # : LOW, MEDIUM, HIGH, CRITICAL
    message: str       # 
    suggested_action: str  # 
    timestamp: datetime

class RiskManager:
    """ - """
    
    def __init__(self):
        self.risk_parameters = self._initialize_risk_parameters()
        self.portfolio_positions = {}
        self.risk_alerts = []
        self.historical_drawdowns = []
        self.correlation_cache = {}
        
    def _initialize_risk_parameters(self) -> Dict[str, RiskParameters]:
        """"""
        return {
            "CONSERVATIVE": RiskParameters(
                max_risk_per_trade=0.01,    # 1%
                max_daily_risk=0.03,        # 3%
                max_portfolio_risk=0.15,    # 15%
                max_drawdown_limit=0.10,    # 10%
                max_correlation=0.60,       # 60%
                max_leverage=2.0,           # 2x
                position_concentration=0.20, # 20%
                sector_concentration=0.40   # 40%
            ),
            "MODERATE": RiskParameters(
                max_risk_per_trade=0.02,    # 2%
                max_daily_risk=0.05,        # 5%
                max_portfolio_risk=0.25,    # 25%
                max_drawdown_limit=0.15,    # 15%
                max_correlation=0.70,       # 70%
                max_leverage=3.0,           # 3x
                position_concentration=0.25, # 25%
                sector_concentration=0.50   # 50%
            ),
            "AGGRESSIVE": RiskParameters(
                max_risk_per_trade=0.03,    # 3%
                max_daily_risk=0.08,        # 8%
                max_portfolio_risk=0.40,    # 40%
                max_drawdown_limit=0.25,    # 25%
                max_correlation=0.80,       # 80%
                max_leverage=5.0,           # 5x
                position_concentration=0.30, # 30%
                sector_concentration=0.60   # 60%
            ),
            "HIGH_RISK": RiskParameters(
                max_risk_per_trade=0.05,    # 5%
                max_daily_risk=0.15,        # 15%
                max_portfolio_risk=0.60,    # 60%
                max_drawdown_limit=0.40,    # 40%
                max_correlation=0.90,       # 90%
                max_leverage=10.0,          # 10x
                position_concentration=0.40, # 40%
                sector_concentration=0.80   # 80%
            )
        }
    
    async def calculate_position_size(self, symbol: str, entry_price: float, 
                                    stop_loss_price: float, account_balance: float,
                                    risk_level: str = "MODERATE", 
                                    additional_factors: Optional[Dict] = None) -> PositionSizing:
        """"""
        logger.info(f" : {symbol}")
        logger.info(f"   : {entry_price:.2f}")
        logger.info(f"   : {stop_loss_price:.2f}")
        logger.info(f"   : ${account_balance:,.2f}")
        
        try:
            risk_params = self.risk_parameters[risk_level]
            
            # 1. 
            stop_distance = abs(entry_price - stop_loss_price) / entry_price
            logger.info(f"    : {stop_distance:.2%}")
            
            # 2. 
            risk_based_size = self._calculate_risk_based_size(
                account_balance, stop_distance, risk_params
            )
            
            # 3. 
            kelly_size = await self._calculate_kelly_size(
                symbol, entry_price, stop_loss_price, additional_factors
            )
            
            # 4. 
            volatility_adjusted_size = await self._calculate_volatility_adjusted_size(
                symbol, risk_based_size, additional_factors
            )
            
            # 5. 
            liquidity_adjusted_size = await self._apply_liquidity_constraints(
                symbol, volatility_adjusted_size, additional_factors
            )
            
            # 6. 
            correlation_adjusted_size = await self._apply_correlation_constraints(
                symbol, liquidity_adjusted_size, risk_params
            )
            
            # 7. 
            concentration_adjusted_size = self._apply_concentration_constraints(
                symbol, correlation_adjusted_size, risk_params, account_balance
            )
            
            # 8. 
            final_size = min(
                risk_based_size,
                kelly_size * 0.5,  # 
                volatility_adjusted_size,
                liquidity_adjusted_size,
                correlation_adjusted_size,
                concentration_adjusted_size
            )
            
            # 9. 
            max_size = account_balance * risk_params.position_concentration / entry_price
            risk_amount = final_size * entry_price * stop_distance
            
            #  ( 1:2)
            take_profit_distance = stop_distance * 2
            if entry_price > stop_loss_price:  # 
                take_profit_price = entry_price * (1 + take_profit_distance)
            else:  # 
                take_profit_price = entry_price * (1 - take_profit_distance)
            
            risk_reward_ratio = take_profit_distance / stop_distance
            
            # 
            confidence_factors = [
                1.0 if stop_distance < 0.05 else 0.5,  # 
                1.0 if final_size == risk_based_size else final_size / risk_based_size,  # 
                kelly_size / risk_based_size if kelly_size > 0 else 0.5  # 
            ]
            confidence_score = sum(confidence_factors) / len(confidence_factors)
            
            result = PositionSizing(
                symbol=symbol,
                recommended_size=final_size,
                max_size=max_size,
                risk_amount=risk_amount,
                stop_loss_distance=stop_distance,
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                risk_reward_ratio=risk_reward_ratio,
                kelly_fraction=kelly_size / account_balance * entry_price if kelly_size > 0 else 0,
                confidence_score=confidence_score
            )
            
            logger.info(f"    : {final_size:.4f} {symbol}")
            logger.info(f"    : ${risk_amount:.2f} ({risk_amount/account_balance:.2%})")
            logger.info(f"    : 1:{risk_reward_ratio:.1f}")
            logger.info(f"    : {confidence_score:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f": {e}")
            return self._get_default_position_sizing(symbol, entry_price, stop_loss_price)
    
    async def assess_portfolio_risk(self, current_positions: Dict, 
                                  market_data: Dict, account_info: Dict) -> PortfolioRisk:
        """"""
        logger.info(" ...")
        
        try:
            # 1. 
            total_exposure = self._calculate_total_exposure(current_positions, market_data)
            
            # 2. VaR
            var_results = await self._calculate_var(current_positions, market_data)
            
            # 3. 
            correlation_matrix = await self._calculate_correlation_matrix(current_positions)
            
            # 4. 
            concentration_risk = self._analyze_concentration_risk(current_positions, account_info)
            
            # 5. 
            liquidity_risk = await self._assess_liquidity_risk(current_positions, market_data)
            
            # 6. 
            leverage_ratio = self._calculate_leverage_ratio(current_positions, account_info)
            
            # 7. 
            max_drawdown = self._analyze_maximum_drawdown(current_positions)
            
            # 8. 
            expected_shortfall = await self._calculate_expected_shortfall(current_positions, market_data)
            
            # 9. 
            risk_adjusted_return = self._calculate_risk_adjusted_return(current_positions, account_info)
            
            portfolio_risk = PortfolioRisk(
                timestamp=datetime.now(),
                total_exposure=total_exposure,
                var_1day_95=var_results['var_95'],
                var_1day_99=var_results['var_99'],
                expected_shortfall=expected_shortfall,
                maximum_drawdown=max_drawdown,
                correlation_matrix=correlation_matrix,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk,
                leverage_ratio=leverage_ratio,
                risk_adjusted_return=risk_adjusted_return
            )
            
            # 
            await self._generate_risk_alerts(portfolio_risk, account_info)
            
            return portfolio_risk
            
        except Exception as e:
            logger.error(f": {e}")
            return self._get_default_portfolio_risk()
    
    async def monitor_risk_limits(self, current_positions: Dict, 
                                account_info: Dict, risk_level: str = "MODERATE") -> List[RiskAlert]:
        """"""
        logger.info(" ...")
        
        alerts = []
        risk_params = self.risk_parameters[risk_level]
        
        try:
            # 1. 
            for symbol, position in current_positions.items():
                trade_risk = self._calculate_position_risk(position, account_info['balance'])
                
                if trade_risk > risk_params.max_risk_per_trade:
                    alerts.append(RiskAlert(
                        alert_type="TRADE_RISK_EXCEEDED",
                        severity="HIGH",
                        message=f"{symbol}{trade_risk:.2%}{risk_params.max_risk_per_trade:.2%}",
                        suggested_action="",
                        timestamp=datetime.now()
                    ))
            
            # 2. 
            portfolio_risk = sum(self._calculate_position_risk(pos, account_info['balance']) 
                               for pos in current_positions.values())
            
            if portfolio_risk > risk_params.max_portfolio_risk:
                alerts.append(RiskAlert(
                    alert_type="PORTFOLIO_RISK_EXCEEDED", 
                    severity="CRITICAL",
                    message=f"{portfolio_risk:.2%}{risk_params.max_portfolio_risk:.2%}",
                    suggested_action="",
                    timestamp=datetime.now()
                ))
            
            # 3. 
            leverage = self._calculate_leverage_ratio(current_positions, account_info)
            
            if leverage > risk_params.max_leverage:
                alerts.append(RiskAlert(
                    alert_type="LEVERAGE_EXCEEDED",
                    severity="HIGH",
                    message=f"{leverage:.1f}x{risk_params.max_leverage:.1f}x",
                    suggested_action="",
                    timestamp=datetime.now()
                ))
            
            # 4. 
            concentration = self._check_concentration_limits(current_positions, account_info, risk_params)
            alerts.extend(concentration)
            
            # 5. 
            correlation_alerts = await self._check_correlation_limits(current_positions, risk_params)
            alerts.extend(correlation_alerts)
            
            # 6. 
            drawdown_alert = self._check_drawdown_limits(account_info, risk_params)
            if drawdown_alert:
                alerts.append(drawdown_alert)
            
            # 
            self.risk_alerts.extend(alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f": {e}")
            return []
    
    async def optimize_risk_exposure(self, target_positions: Dict, 
                                   account_info: Dict, 
                                   risk_level: str = "MODERATE") -> Dict:
        """"""
        logger.info(" ...")
        
        try:
            risk_params = self.risk_parameters[risk_level]
            optimized_positions = {}
            
            # 1. 
            total_risk = 0.0
            for symbol, position in target_positions.items():
                risk = self._calculate_position_risk(position, account_info['balance'])
                total_risk += risk
            
            # 2. 
            if total_risk > risk_params.max_portfolio_risk:
                scale_factor = risk_params.max_portfolio_risk / total_risk
                logger.info(f"   : {scale_factor:.2%}")
                
                for symbol, position in target_positions.items():
                    optimized_positions[symbol] = {
                        **position,
                        'size': position['size'] * scale_factor
                    }
            else:
                optimized_positions = target_positions.copy()
            
            # 3. 
            optimized_positions = await self._optimize_correlations(
                optimized_positions, risk_params
            )
            
            # 4. 
            optimized_positions = self._optimize_concentration(
                optimized_positions, account_info, risk_params
            )
            
            # 5. 
            optimization_metrics = {
                "original_risk": total_risk,
                "optimized_risk": sum(
                    self._calculate_position_risk(pos, account_info['balance'])
                    for pos in optimized_positions.values()
                ),
                "risk_reduction": total_risk - sum(
                    self._calculate_position_risk(pos, account_info['balance'])
                    for pos in optimized_positions.values()
                ),
                "position_adjustments": len([
                    s for s in target_positions
                    if target_positions[s]['size'] != optimized_positions.get(s, {}).get('size', 0)
                ])
            }
            
            return {
                "optimized_positions": optimized_positions,
                "optimization_metrics": optimization_metrics,
                "risk_assessment": await self.assess_portfolio_risk(
                    optimized_positions, {}, account_info
                )
            }
            
        except Exception as e:
            logger.error(f": {e}")
            return {"optimized_positions": target_positions}
    
    # ==========  ==========
    
    def _calculate_risk_based_size(self, account_balance: float, 
                                 stop_distance: float, risk_params: RiskParameters) -> float:
        """"""
        risk_amount = account_balance * risk_params.max_risk_per_trade
        return risk_amount / stop_distance if stop_distance > 0 else 0
    
    async def _calculate_kelly_size(self, symbol: str, entry_price: float, 
                                  stop_loss_price: float, additional_factors: Optional[Dict] = None) -> float:
        """"""
        try:
            # 使用傳入的 additional_factors 或帳戶資料；無歷史資料時採用保守預設值
            factors = additional_factors or {}
            win_rate = factors.get("win_rate", 0.5)    # 保守預設 50%
            avg_win = factors.get("avg_win", 0.03)     # 保守預設 3%
            avg_loss = abs(entry_price - stop_loss_price) / entry_price  # 
            
            if avg_loss == 0:
                return 0
            
            # : f* = (bp - q) / b
            #  b = , p = , q = 1-p
            odds_ratio = avg_win / avg_loss
            kelly_fraction = (odds_ratio * win_rate - (1 - win_rate)) / odds_ratio
            
            # 25%
            kelly_fraction = max(0, min(0.25, kelly_fraction))
            
            return float(kelly_fraction)
            
        except Exception as e:
            logger.error(f": {e}")
            return 0.05  # 5%
    
    async def _calculate_volatility_adjusted_size(self, symbol: str, base_size: float, 
                                                additional_factors: Optional[Dict] = None) -> float:
        """"""
        try:
            # 從 additional_factors 或 market_data 取得真實波動率；無資料時用保守預設
            factors = additional_factors or {}
            volatility = float(factors.get("volatility", factors.get("atr_pct", 0.30)))  # 預設 30%
            
            # 25%
            base_volatility = 0.25
            volatility_adjustment = base_volatility / volatility
            
            # 0.5-2.0
            volatility_adjustment = max(0.5, min(2.0, volatility_adjustment))
            
            return base_size * volatility_adjustment
            
        except Exception as e:
            logger.error(f": {e}")
            return base_size
    
    async def _apply_liquidity_constraints(self, symbol: str, base_size: float, 
                                         additional_factors: Optional[Dict] = None) -> float:
        """"""
        try:
            # 從 additional_factors 取得真實市場深度與成交量；無資料時採保守預設
            factors = additional_factors or {}
            market_depth = float(factors.get("market_depth", 1.0))      # 預設正常深度
            daily_volume = float(factors.get("daily_volume", 50000.0))  # 預設 50k USDT
            
            # 2%
            max_size_by_volume = daily_volume * 0.02
            
            # 
            liquidity_adjusted_size = min(base_size, max_size_by_volume) * market_depth
            
            return max(0, liquidity_adjusted_size)
            
        except Exception as e:
            logger.error(f": {e}")
            return base_size * 0.8  # 
    
    async def _apply_correlation_constraints(self, symbol: str, base_size: float, 
                                           risk_params: RiskParameters) -> float:
        """"""
        try:
            # 
            existing_symbols = list(self.portfolio_positions.keys())
            
            if not existing_symbols:
                return base_size
            
            # 無即時相關性資料時，加密貨幣對之間採用保守正相關預設 (0.6)
            correlations = dict.fromkeys(existing_symbols, 0.6)
            
            # 
            max_correlation = max(correlations.values()) if correlations else 0
            
            if max_correlation > risk_params.max_correlation:
                correlation_adjustment = risk_params.max_correlation / max_correlation
                return base_size * correlation_adjustment
            
            return base_size
            
        except Exception as e:
            logger.error(f": {e}")
            return base_size
    
    def _apply_concentration_constraints(self, symbol: str, base_size: float, 
                                       risk_params: RiskParameters, account_balance: float) -> float:
        """"""
        try:
            # 
            max_position_value = account_balance * risk_params.position_concentration
            
            # 
            if base_size > max_position_value:
                return max_position_value
            
            return base_size
            
        except Exception as e:
            logger.error(f": {e}")
            return base_size * 0.8
    
    # ==========  ==========
    
    def _calculate_total_exposure(self, positions: Dict, market_data: Dict) -> float:
        """"""
        total_exposure = 0
        
        for symbol, position in positions.items():
            position_value = position.get('size', 0) * position.get('price', 0)
            leverage = position.get('leverage', 1)
            total_exposure += position_value * leverage
        
        return total_exposure
    
    async def _calculate_var(self, positions: Dict, market_data: Dict) -> Dict:
        """(VaR)"""
        try:
            # 從實際持倉盈虧建立歷史報酬序列，無資料時用保守固定值
            history_returns = []
            for pos in positions.values():
                pnl_pct = pos.get("unrealized_pnl_pct", 0.0)
                if abs(pnl_pct) > 1e-9:
                    history_returns.append(pnl_pct)

            if len(history_returns) >= 30:
                portfolio_returns = np.array(history_returns)
            else:
                # 持倉數量不足，兩儀回傳保守固定值
                return {"var_95": 0.025, "var_99": 0.035}
            
            # VaR
            var_95 = np.percentile(portfolio_returns, 5) * -1  # 95% VaR
            var_99 = np.percentile(portfolio_returns, 1) * -1  # 99% VaR
            
            return {
                "var_95": var_95,
                "var_99": var_99
            }
            
        except Exception as e:
            logger.error(f"VaR: {e}")
            return {"var_95": 0.02, "var_99": 0.03}
    
    async def _calculate_correlation_matrix(self, positions: Dict) -> Dict:
        """"""
        try:
            symbols = list(positions.keys())
            correlation_matrix: Dict[str, Dict[str, float]] = {}
            
            for i, symbol1 in enumerate(symbols):
                correlation_matrix[symbol1] = {}
                for j, symbol2 in enumerate(symbols):
                    if i == j:
                        correlation_matrix[symbol1][symbol2] = 1.0
                    else:
                        # 加密貨幣之間長期相關性較高，無即時資料時用保守預設 0.65
                        correlation = 0.65 if i != j else 1.0
                        correlation_matrix[symbol1][symbol2] = correlation
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f": {e}")
            return {}
    
    def _analyze_concentration_risk(self, positions: Dict, account_info: Dict) -> Dict:
        """"""
        try:
            account_balance = account_info.get('balance', 0)
            
            if account_balance == 0:
                return {}
            
            concentration_risk = {}
            
            # 
            for symbol, position in positions.items():
                position_value = position.get('size', 0) * position.get('price', 0)
                concentration = position_value / account_balance
                concentration_risk[symbol] = concentration
            
            # 
            total_concentration = sum(concentration_risk.values())
            herfindahl_index = sum(c**2 for c in concentration_risk.values())
            
            return {
                "individual_concentrations": concentration_risk,
                "total_concentration": total_concentration,
                "herfindahl_index": herfindahl_index,
                "max_individual_concentration": max(concentration_risk.values()) if concentration_risk else 0
            }
            
        except Exception as e:
            logger.error(f": {e}")
            return {}
    
    async def _assess_liquidity_risk(self, positions: Dict, market_data: Dict) -> float:
        """"""
        try:
            liquidity_scores = []
            
            for symbol, position in positions.items():
                # 從 market_data 取得該幣對的實際市場資料
                symbol_data = market_data.get(symbol, {})
                bid_ask_spread = symbol_data.get("bid_ask_spread", 0.002)   # 實際買賣價差
                market_depth = symbol_data.get("market_depth", 1.0)         # 市場深度倍數
                trading_volume = symbol_data.get("volume_ratio", 1.0)       # 本期成交量 / 均值
                
                #  (0-1)
                spread_score = max(0, 1 - bid_ask_spread * 100)
                depth_score = min(1, market_depth / 2.0)
                volume_score = min(1, trading_volume / 5.0)
                
                position_liquidity = (spread_score + depth_score + volume_score) / 3
                liquidity_scores.append(position_liquidity)
            
            #  (1 - )
            avg_liquidity = np.mean(liquidity_scores) if liquidity_scores else 0.5
            liquidity_risk = float(1 - avg_liquidity)
            
            return liquidity_risk
            
        except Exception as e:
            logger.error(f": {e}")
            return 0.3  # 
    
    def _calculate_leverage_ratio(self, positions: Dict, account_info: Dict) -> float:
        """"""
        try:
            total_notional = 0
            account_balance = account_info.get('balance', 0)
            
            for position in positions.values():
                position_value = position.get('size', 0) * position.get('price', 0)
                leverage = position.get('leverage', 1)
                total_notional += position_value * leverage
            
            return total_notional / account_balance if account_balance > 0 else 0
            
        except Exception as e:
            logger.error(f": {e}")
            return 1.0
    
    def _analyze_maximum_drawdown(self, positions: Dict) -> float:
        """"""
        try:
            # 從實際持倉盈虧建立歷史轉機序列
            portfolio_values: List[float] = []
            cumulative = 100000.0
            portfolio_values.append(cumulative)

            for pos in positions.values():
                daily_pnl = pos.get('unrealized_pnl', 0.0)
                cumulative = float(cumulative + daily_pnl)
                portfolio_values.append(cumulative)

            if len(portfolio_values) < 2:
                return 0.0
            peak = portfolio_values[0]
            max_drawdown = 0.0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f": {e}")
            return 0.1  # 10%
    
    async def _calculate_expected_shortfall(self, positions: Dict, market_data: Dict) -> float:
        """(ES)"""
        try:
            # 從實際持倉數據建立分布
            history_returns = []
            for pos in positions.values():
                pnl_pct = pos.get("unrealized_pnl_pct", 0.0)
                if abs(pnl_pct) > 1e-9:
                    history_returns.append(pnl_pct)

            if len(history_returns) < 30:
                return 0.035  # 持倉資料不足時回傳保守估算值

            returns = np.array(history_returns)
            
            # 95% VaR
            var_95 = np.percentile(returns, 5)
            
            #  (VaR)
            tail_losses = returns[returns <= var_95]
            expected_shortfall = float(np.mean(tail_losses) * -1)
            
            return expected_shortfall
            
        except Exception as e:
            logger.error(f": {e}")
            return 0.035  # 3.5%
    
    def _calculate_risk_adjusted_return(self, positions: Dict, account_info: Dict) -> float:
        """"""
        try:
            # 從實際持倉數據計算年化報酬與波動率
            pnl_list = [pos.get('unrealized_pnl_pct', 0.0) for pos in positions.values()]
            if len(pnl_list) >= 2:
                annual_return = float(np.mean(pnl_list) * 252)         # 年化
                volatility = float(np.std(pnl_list) * (252 ** 0.5))    # 年化波動率
            else:
                # 持倉為空或單一持倉，無法計算 Sharpe，回傳預設中立值
                return 1.0
            
            #  (3%)
            risk_free_rate = 0.03
            sharpe_ratio = (annual_return - risk_free_rate) / volatility
            
            return sharpe_ratio
            
        except Exception as e:
            logger.error(f": {e}")
            return 1.0  # 
    
    # ==========  ==========
    
    def _calculate_position_risk(self, position: Dict, account_balance: float) -> float:
        """"""
        try:
            position_value = position.get('size', 0) * position.get('price', 0)
            stop_loss_distance = position.get('stop_loss_distance', 0.02)
            leverage = position.get('leverage', 1)
            
            risk_amount = position_value * stop_loss_distance * leverage
            risk_percentage = risk_amount / account_balance if account_balance > 0 else 0
            
            return risk_percentage
            
        except Exception as e:
            logger.error(f": {e}")
            return 0.01  # 1%
    
    def _check_concentration_limits(self, positions: Dict, account_info: Dict, 
                                  risk_params: RiskParameters) -> List[RiskAlert]:
        """"""
        alerts = []
        concentration_analysis = self._analyze_concentration_risk(positions, account_info)
        
        # 
        for symbol, concentration in concentration_analysis.get('individual_concentrations', {}).items():
            if concentration > risk_params.position_concentration:
                alerts.append(RiskAlert(
                    alert_type="POSITION_CONCENTRATION_EXCEEDED",
                    severity="MEDIUM",
                    message=f"{symbol}{concentration:.2%}{risk_params.position_concentration:.2%}",
                    suggested_action="",
                    timestamp=datetime.now()
                ))
        
        return alerts
    
    async def _check_correlation_limits(self, positions: Dict, 
                                      risk_params: RiskParameters) -> List[RiskAlert]:
        """"""
        alerts = []
        
        try:
            correlation_matrix = await self._calculate_correlation_matrix(positions)
            
            for symbol1, correlations in correlation_matrix.items():
                for symbol2, correlation in correlations.items():
                    if (symbol1 != symbol2 and 
                        correlation > risk_params.max_correlation):
                        alerts.append(RiskAlert(
                            alert_type="HIGH_CORRELATION_DETECTED",
                            severity="LOW",
                            message=f"{symbol1}{symbol2}{correlation:.2%}",
                            suggested_action="",
                            timestamp=datetime.now()
                        ))
                        break  # 
        
        except Exception as e:
            logger.error(f": {e}")
        
        return alerts
    
    def _check_drawdown_limits(self, account_info: Dict, 
                              risk_params: RiskParameters) -> Optional[RiskAlert]:
        """"""
        try:
            current_balance = account_info.get('balance', 0)
            peak_balance = account_info.get('peak_balance', current_balance)
            
            if peak_balance > 0:
                current_drawdown = (peak_balance - current_balance) / peak_balance
                
                if current_drawdown > risk_params.max_drawdown_limit:
                    return RiskAlert(
                        alert_type="DRAWDOWN_LIMIT_EXCEEDED",
                        severity="CRITICAL",
                        message=f"{current_drawdown:.2%}{risk_params.max_drawdown_limit:.2%}",
                        suggested_action="",
                        timestamp=datetime.now()
                    )
        
        except Exception as e:
            logger.error(f": {e}")
        
        return None
    
    # ==========  ==========
    
    async def _optimize_correlations(self, positions: Dict, 
                                   risk_params: RiskParameters) -> Dict:
        """"""
        try:
            correlation_matrix = await self._calculate_correlation_matrix(positions)
            optimized_positions = positions.copy()
            
            # 
            high_correlation_pairs = []
            for symbol1, correlations in correlation_matrix.items():
                for symbol2, correlation in correlations.items():
                    if (symbol1 != symbol2 and 
                        correlation > risk_params.max_correlation and
                        (symbol2, symbol1) not in high_correlation_pairs):
                        high_correlation_pairs.append((symbol1, symbol2))
            
            # 
            for symbol1, symbol2 in high_correlation_pairs:
                # 
                size1 = optimized_positions[symbol1].get('size', 0)
                size2 = optimized_positions[symbol2].get('size', 0)
                
                if size1 > size2:
                    optimized_positions[symbol2]['size'] *= 0.7
                else:
                    optimized_positions[symbol1]['size'] *= 0.7
            
            return optimized_positions
            
        except Exception as e:
            logger.error(f": {e}")
            return positions
    
    def _optimize_concentration(self, positions: Dict, account_info: Dict, 
                               risk_params: RiskParameters) -> Dict:
        """"""
        try:
            account_balance = account_info.get('balance', 0)
            optimized_positions = positions.copy()
            
            # 
            for symbol, position in optimized_positions.items():
                position_value = position.get('size', 0) * position.get('price', 0)
                concentration = position_value / account_balance if account_balance > 0 else 0
                
                if concentration > risk_params.position_concentration:
                    # 
                    adjustment_factor = risk_params.position_concentration / concentration
                    optimized_positions[symbol]['size'] *= adjustment_factor
            
            return optimized_positions
            
        except Exception as e:
            logger.error(f": {e}")
            return positions
    
    async def _generate_risk_alerts(self, portfolio_risk: PortfolioRisk, 
                                   account_info: Dict):
        """"""
        try:
            # VaR
            if portfolio_risk.var_1day_95 > 0.03:  # 3%
                self.risk_alerts.append(RiskAlert(
                    alert_type="HIGH_VAR_DETECTED",
                    severity="MEDIUM",
                    message=f"95% VaR{portfolio_risk.var_1day_95:.2%}",
                    suggested_action="",
                    timestamp=datetime.now()
                ))
            
            # 
            if portfolio_risk.liquidity_risk > 0.5:
                self.risk_alerts.append(RiskAlert(
                    alert_type="HIGH_LIQUIDITY_RISK",
                    severity="MEDIUM",
                    message=f"{portfolio_risk.liquidity_risk:.2%}",
                    suggested_action="",
                    timestamp=datetime.now()
                ))
        
        except Exception as e:
            logger.error(f": {e}")
    
    # ==========  ==========
    
    def _get_default_position_sizing(self, symbol: str, entry_price: float, 
                                   stop_loss_price: float) -> PositionSizing:
        """"""
        stop_distance = abs(entry_price - stop_loss_price) / entry_price
        
        return PositionSizing(
            symbol=symbol,
            recommended_size=0.01,  # 1%
            max_size=0.05,          # 5%
            risk_amount=100.0,      # $100
            stop_loss_distance=stop_distance,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=entry_price * (1.04 if entry_price > stop_loss_price else 0.96),
            risk_reward_ratio=2.0,
            kelly_fraction=0.05,
            confidence_score=0.5
        )
    
    def _get_default_portfolio_risk(self) -> PortfolioRisk:
        """"""
        return PortfolioRisk(
            timestamp=datetime.now(),
            total_exposure=10000.0,
            var_1day_95=0.02,
            var_1day_99=0.03,
            expected_shortfall=0.035,
            maximum_drawdown=0.1,
            correlation_matrix={},
            concentration_risk={},
            liquidity_risk=0.3,
            leverage_ratio=1.0,
            risk_adjusted_return=1.0
        )
    
    def get_risk_summary(self) -> Dict:
        """"""
        return {
            "active_alerts": len([a for a in self.risk_alerts if 
                                (datetime.now() - a.timestamp).hours < 24]),
            "current_positions": len(self.portfolio_positions),
            "risk_parameters": {
                level: {
                    "max_risk_per_trade": params.max_risk_per_trade,
                    "max_portfolio_risk": params.max_portfolio_risk,
                    "max_leverage": params.max_leverage
                }
                for level, params in self.risk_parameters.items()
            }
        }
