"""
風險管理器 - Risk Manager

⚠️ 注意：此模組保留用於向後兼容
所有風險管理類別統一從 risk_management.position_manager 導入
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Any
import numpy as np
import math
from pathlib import Path

# 從統一的 risk_management 模組導入所有類別
from ..risk_management.position_manager import (
    RiskLevel,
    PositionType,
    RiskParameters,
    PositionSizing,
    PortfolioRisk,
    RiskAlert,
    get_risk_params
)

logger = logging.getLogger(__name__)

# 導入數據庫管理器（可選）
if TYPE_CHECKING:
    from ..data.database_manager import DatabaseManager

DB_AVAILABLE = False
DatabaseManager: Any = None
get_database_manager: Any = None

try:
    from ..data.database_manager import get_database_manager, DatabaseManager
    DB_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ 數據庫管理器不可用，風險統計將僅保存到內存")

class RiskManager:
    """風險管理器 - 管理交易風險
    
    ⚠️ 注意：此類使用 risk_management.position_manager 中定義的 RiskParameters
    """
    
    def __init__(self, use_database: bool = True):
        # 使用統一的風險參數定義
        self.risk_parameters = self._initialize_risk_parameters()
        self.portfolio_positions = {}
        self.risk_alerts = []
        self.historical_drawdowns = []
        self.correlation_cache = {}
        
        # 交易記錄與統計
        self.trade_history: List[Dict] = []
        self.current_balance: float = 0.0
        self.peak_balance: float = 0.0
        self.daily_trade_count: int = 0
        self.last_trade_date: Optional[datetime] = None
        
        # 數據庫管理器（可選）
        self.db_manager: Any = None
        if use_database and DB_AVAILABLE:
            try:
                self.db_manager = get_database_manager()
                logger.info("✅ RiskManager 已連接數據庫")
            except Exception as e:
                logger.warning(f"⚠️ RiskManager 無法連接數據庫: {e}")
        
        # 統計數據文件路徑
        self.stats_dir = Path("data/bioneuronai/trading/runtime")
        self.stats_dir.mkdir(exist_ok=True, parents=True)
        
    def _initialize_risk_parameters(self) -> Dict[str, RiskParameters]:
        """初始化風險參數 - 使用 risk_management 模組的 RiskParameters 類別"""
        return {
            "CONSERVATIVE": RiskParameters(
                max_risk_per_trade=0.01,
                max_daily_risk=0.03,
                max_portfolio_risk=0.15,
                max_drawdown_limit=0.10,
                max_correlation=0.60,
                max_leverage=2.0,
                position_concentration=0.20,
                sector_concentration=0.40
            ),
            "MODERATE": RiskParameters(
                max_risk_per_trade=0.02,
                max_daily_risk=0.05,
                max_portfolio_risk=0.25,
                max_drawdown_limit=0.15,
                max_correlation=0.70,
                max_leverage=3.0,
                position_concentration=0.25,
                sector_concentration=0.50
            ),
            "AGGRESSIVE": RiskParameters(
                max_risk_per_trade=0.03,
                max_daily_risk=0.08,
                max_portfolio_risk=0.40,
                max_drawdown_limit=0.25,
                max_correlation=0.80,
                max_leverage=5.0,
                position_concentration=0.30,
                sector_concentration=0.60
            ),
            "HIGH_RISK": RiskParameters(
                max_risk_per_trade=0.05,
                max_daily_risk=0.15,
                max_portfolio_risk=0.60,
                max_drawdown_limit=0.40,
                max_correlation=0.90,
                max_leverage=10.0,
                position_concentration=0.40,
                sector_concentration=0.80
            )
        }
    
    async def calculate_position_size(self, symbol: str, entry_price: float, 
                                    stop_loss_price: float, account_balance: float,
                                    risk_level: str = "MODERATE", 
                                    additional_factors: Optional[Dict] = None) -> PositionSizing:
        """計算建議倉位大小"""
        await asyncio.sleep(0)  # Async yield point for task scheduling
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
            
            # 3. Kelly 公式計算
            kelly_size = self._calculate_kelly_size(
                symbol, entry_price, stop_loss_price, additional_factors
            )
            
            # 4. 波動率調整
            volatility_adjusted_size = self._calculate_volatility_adjusted_size(
                symbol, risk_based_size, additional_factors
            )
            
            # 5. 流動性約束
            liquidity_adjusted_size = self._apply_liquidity_constraints(
                symbol, volatility_adjusted_size, additional_factors
            )
            
            # 6. 相關性約束
            correlation_adjusted_size = self._apply_correlation_constraints(
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
        """評估投資組合風險"""
        await asyncio.sleep(0)  # Async yield point for task scheduling
        logger.info("評估投資組合風險...")
        
        try:
            # 1. 計算總曝險
            total_exposure = self._calculate_total_exposure(current_positions, market_data)
            
            # 2. 計算VaR
            var_results = self._calculate_var(current_positions, market_data)
            
            # 3. 計算相關矩陣
            correlation_matrix = self._calculate_correlation_matrix(current_positions)
            
            # 4. 分析集中度風險
            concentration_risk = self._analyze_concentration_risk(current_positions, account_info)
            
            # 5. 評估流動性風險
            liquidity_risk = self._assess_liquidity_risk(current_positions, market_data)
            
            # 6. 計算槓桿比率
            leverage_ratio = self._calculate_leverage_ratio(current_positions, account_info)
            
            # 7. 分析最大回撤
            max_drawdown = self._analyze_maximum_drawdown(current_positions)
            
            # 8. 計算預期虧損
            expected_shortfall = self._calculate_expected_shortfall(current_positions, market_data)
            
            # 9. 計算風險調整收益
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
            
            # 生成風險警報
            self._generate_risk_alerts(portfolio_risk, account_info)
            
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
            total_risk = 0
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
    
    def _calculate_kelly_size(self, _symbol: str, entry_price: float, 
                                  stop_loss_price: float, _additional_factors: Optional[Dict] = None) -> float:
        """使用Kelly公式計算倉位大小"""
        # _symbol 和 _additional_factors 保留用於未來整合真實數據
        try:
            # 從 _additional_factors 取得實際勝率/平均盈利；無資料時用保守預設
            factors = _additional_factors or {}
            win_rate = factors.get("win_rate", 0.5)    # 保守預設 50%
            avg_win = factors.get("avg_win", 0.03)     # 保守預設 3%
            avg_loss = abs(entry_price - stop_loss_price) / entry_price  # 實際止損距離
            
            if avg_loss == 0:
                return 0
            
            # Kelly公式: f* = (bp - q) / b
            # 其中 b = 購率, p = 勝率, q = 1-p
            odds_ratio = avg_win / avg_loss
            kelly_fraction = (odds_ratio * win_rate - (1 - win_rate)) / odds_ratio
            
            # 限制最大6Kelly分數25%
            kelly_fraction = max(0, min(0.25, kelly_fraction))
            
            return kelly_fraction
            
        except Exception as e:
            logger.error(f"Kelly計算失敗: {e}")
            return 0.05  # 預設5%
    
    def _calculate_volatility_adjusted_size(self, symbol: str, base_size: float, 
                                                additional_factors: Optional[Dict] = None) -> float:
        """根據波動率調整倉位大小"""
        # symbol 和 additional_factors 保留用於未來整合真實波動率數據
        _ = symbol
        try:
            # 從 additional_factors 取得真實 ATR 百分比波動率；無資料時用保守預設
            factors = additional_factors or {}
            volatility = factors.get("volatility", factors.get("atr_pct", 0.30))  # 預設 30%
            
            # 基準波動率設為25%
            base_volatility = 0.25
            volatility_adjustment = base_volatility / volatility
            
            # 限制調整係數在0.5-2.0之間
            volatility_adjustment = max(0.5, min(2.0, volatility_adjustment))
            
            return base_size * volatility_adjustment
            
        except Exception as e:
            logger.error(f"波動率調整失敗: {e}")
            return base_size
    
    def _apply_liquidity_constraints(self, symbol: str, base_size: float, 
                                         additional_factors: Optional[Dict] = None) -> float:
        """應用流動性約束"""
        # symbol 和 additional_factors 保留用於未來整合真實市場深度數據
        _ = symbol
        try:
            # 從 additional_factors 取得真實市場深度與日成交量；無資料時用保守預設
            factors = additional_factors or {}
            market_depth = factors.get("market_depth", 1.0)      # 預設正常深度
            daily_volume = factors.get("daily_volume", 50000.0)  # 預設 50k USDT
            
            # 最大倉位不超過日交易量的2%
            max_size_by_volume = daily_volume * 0.02
            
            # 應用流動性約束
            liquidity_adjusted_size = min(base_size, max_size_by_volume) * market_depth
            
            return max(0, liquidity_adjusted_size)
            
        except Exception as e:
            logger.error(f"流動性約束失敗: {e}")
            return base_size * 0.8  # 預設提降20%
    
    def _apply_correlation_constraints(self, symbol: str, base_size: float, 
                                           risk_params: RiskParameters) -> float:
        """應用相關性約束"""
        # symbol 保留用於未來真實相關性計算
        _ = symbol
        try:
            # 檢查現有持倉
            existing_symbols = list(self.portfolio_positions.keys())
            
            if not existing_symbols:
                return base_size
            
            # 加密貨幣之間長期相關性較高，無即時資料時用保守正相關預設 (0.6)
            correlations = dict.fromkeys(existing_symbols, 0.6)
            
            # 檢查最高相關性
            max_correlation = max(correlations.values()) if correlations else 0
            
            if max_correlation > risk_params.max_correlation:
                correlation_adjustment = risk_params.max_correlation / max_correlation
                return base_size * correlation_adjustment
            
            return base_size
            
        except Exception as e:
            logger.error(f"相關性約束失敗: {e}")
            return base_size
    
    def _apply_concentration_constraints(self, symbol: str, base_size: float, 
                                       risk_params: RiskParameters, account_balance: float) -> float:
        """應用集中度約束"""
        # symbol 保留用於未來依符號設定不同集中度限制
        _ = symbol
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
        """計算總曝险"""
        # market_data 保留用於未來整合即時價格數據
        _ = market_data
        total_exposure = 0
        
        for symbol, position in positions.items():
            position_value = position.get('size', 0) * position.get('price', 0)
            leverage = position.get('leverage', 1)
            total_exposure += position_value * leverage
        
        return total_exposure
    
    def _calculate_var(self, positions: Dict, market_data: Dict) -> Dict:
        """計算風險價值(VaR)"""
        _ = market_data
        try:
            # 從實際持倉盈虧建立歷史報酬序列
            history_returns = []
            for pos in positions.values():
                pnl_pct = pos.get("unrealized_pnl_pct", 0.0)
                if abs(pnl_pct) > 1e-9:
                    history_returns.append(pnl_pct)

            if len(history_returns) >= 30:
                portfolio_returns = np.array(history_returns)
            else:
                # 持倉數量不足，回傳保守固定值
                return {"var_95": 0.025, "var_99": 0.035}
            
            # 計算VaR
            var_95 = np.percentile(portfolio_returns, 5) * -1  # 95% VaR
            var_99 = np.percentile(portfolio_returns, 1) * -1  # 99% VaR
            
            return {
                "var_95": var_95,
                "var_99": var_99
            }
            
        except Exception as e:
            logger.error(f"VaR計算失敗: {e}")
            return {"var_95": 0.02, "var_99": 0.03}
    
    def _calculate_correlation_matrix(self, positions: Dict) -> Dict:
        """計算相關矩陣"""
        try:
            symbols = list(positions.keys())
            correlation_matrix = {}
            
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
            logger.error(f"相關矩陣計算失敗: {e}")
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
    
    def _assess_liquidity_risk(self, positions: Dict, market_data: Dict) -> float:
        """評估流動性風險"""
        try:
            liquidity_scores = []
            
            for symbol, position in positions.items():
                _ = position
                # 從 market_data 取得該幣對的實際市場資料
                symbol_data = market_data.get(symbol, {})
                bid_ask_spread = symbol_data.get("bid_ask_spread", 0.002)
                market_depth = symbol_data.get("market_depth", 1.0)
                trading_volume = symbol_data.get("volume_ratio", 1.0)
                
                # 計算流動性分數 (0-1)
                spread_score = max(0, 1 - bid_ask_spread * 100)
                depth_score = min(1, market_depth / 2.0)
                volume_score = min(1, trading_volume / 5.0)
                
                position_liquidity = (spread_score + depth_score + volume_score) / 3
                liquidity_scores.append(position_liquidity)
            
            # 計算流動性風險: 流動性越高，風險越低
            avg_liquidity = np.mean(liquidity_scores) if liquidity_scores else 0.5
            liquidity_risk = float(1 - avg_liquidity)
            
            return liquidity_risk
            
        except Exception as e:
            logger.error(f"流動性風險評估失敗: {e}")
            return 0.3  # 預設中等風險
    
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
        """分析最大回撤"""
        try:
            # 從實際持倉盈虧資料建立歷史轉機序列
            portfolio_values: List[float] = []
            cumulative = self.current_balance if self.current_balance > 0 else 100000.0
            portfolio_values.append(cumulative)

            for pos in positions.values():
                daily_pnl = pos.get('unrealized_pnl', 0.0)
                cumulative = float(cumulative + daily_pnl)
                portfolio_values.append(cumulative)

            if len(portfolio_values) < 2:
                return 0.0
            peak = portfolio_values[0]
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"回撤分析失敗: {e}")
            return 0.1  # 預設10%
    
    def _calculate_expected_shortfall(self, positions: Dict, market_data: Dict) -> float:
        """計算預期虐損(ES)"""
        _ = market_data
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
        """計算風險調整後收益 (Sharpe Ratio)"""
        _ = account_info
        try:
            # 從實際持倉數據計算年化報酬與波動率
            pnl_list = [pos.get('unrealized_pnl_pct', 0.0) for pos in positions.values()]
            if len(pnl_list) >= 2:
                annual_return = float(np.mean(pnl_list) * 252)
                volatility = float(np.std(pnl_list) * (252 ** 0.5))
            else:
                return 1.0
            
            # 計算 Sharpe Ratio (無風險利率 3%)
            risk_free_rate = 0.03
            if volatility < 1e-9:
                return 1.0
            sharpe_ratio = (annual_return - risk_free_rate) / volatility
            
            return sharpe_ratio
            
        except Exception as e:
            logger.error(f"風險調整收益計算失敗: {e}")
            return 1.0  # 預設值
    
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
        """檢查相關性限制"""
        await asyncio.sleep(0)  # Async yield point
        alerts = []
        
        try:
            correlation_matrix = self._calculate_correlation_matrix(positions)
            
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
        """優化相關性配置"""
        await asyncio.sleep(0)  # Async yield point
        try:
            correlation_matrix = self._calculate_correlation_matrix(positions)
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
    
    def _generate_risk_alerts(self, portfolio_risk: PortfolioRisk, 
                                   account_info: Dict) -> None:
        """生成風險警報"""
        # account_info 保留用於未來根據帳戶狀態生成警報
        _ = account_info
        try:
            # 檢查VaR風險
            if portfolio_risk.var_1day_95 > 0.03:  # 超過3%
                self.risk_alerts.append(RiskAlert(
                    alert_type="HIGH_VAR_DETECTED",
                    severity="MEDIUM",
                    message=f"95% VaR過高: {portfolio_risk.var_1day_95:.2%}",
                    suggested_action="考慮減少倉位",
                    timestamp=datetime.now()
                ))
            
            # 檢查流動性風險
            if portfolio_risk.liquidity_risk > 0.5:
                self.risk_alerts.append(RiskAlert(
                    alert_type="HIGH_LIQUIDITY_RISK",
                    severity="MEDIUM",
                    message=f"流動性風險高: {portfolio_risk.liquidity_risk:.2%}",
                    suggested_action="考慮切換至高流動性交易對",
                    timestamp=datetime.now()
                ))
        
        except Exception as e:
            logger.error(f"風險警報生成失敗: {e}")
    
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
    
    # ========== 交易檢查與記錄方法 ==========
    
    def _check_drawdown_limit(self, risk_params: RiskParameters) -> Optional[str]:
        """檢查回撤限制，返回錯誤原因或 None"""
        if self.peak_balance > 0 and self.current_balance > 0:
            current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
            if current_drawdown > risk_params.max_drawdown_limit:
                return f"超過最大回撤限制: {current_drawdown:.1%} > {risk_params.max_drawdown_limit:.1%}"
        return None
    
    def _check_daily_trade_limit(self) -> Optional[str]:
        """檢查每日交易次數限制，返回錯誤原因或 None"""
        today = datetime.now().date()
        if self.last_trade_date and self.last_trade_date.date() == today:
            if self.daily_trade_count >= 10:
                return f"超過每日交易次數限制: {self.daily_trade_count} >= 10"
        return None
    
    def _check_critical_alerts(self) -> Optional[str]:
        """檢查高優先級風險警報，返回錯誤原因或 None"""
        critical_alerts = [a for a in self.risk_alerts 
                         if a.severity in ["CRITICAL", "HIGH"] 
                         and (datetime.now() - a.timestamp).seconds < 3600]
        if critical_alerts:
            return f"存在 {len(critical_alerts)} 個高優先級風險警報"
        return None
    
    def check_can_trade(self, signal_confidence: float, account_balance: float, 
                       risk_level: str = "MODERATE") -> Tuple[bool, str]:
        """
        綜合交易檢查 - 檢查是否可以進行交易
        
        Args:
            signal_confidence: 信號置信度 (0-1)
            account_balance: 帳戶餘額
            risk_level: 風險等級
            
        Returns:
            (can_trade, reason): 是否可以交易及原因
        """
        try:
            risk_params = self.risk_parameters.get(risk_level, self.risk_parameters["MODERATE"])
            
            # 1. 檢查置信度門檻 (最低 50%)
            if signal_confidence < 0.5:
                return False, f"信號置信度過低: {signal_confidence:.1%} < 50%"
            
            # 2. 檢查回撤限制
            if reason := self._check_drawdown_limit(risk_params):
                return False, reason
            
            # 3. 檢查每日交易次數
            if reason := self._check_daily_trade_limit():
                return False, reason
            
            # 4. 檢查餘額充足性 (最低 100 USD)
            if account_balance < 100:
                return False, f"帳戶餘額不足: ${account_balance:.2f} < $100"
            
            # 5. 檢查高優先級風險警報
            if reason := self._check_critical_alerts():
                return False, reason
            
            # 6. 檢查槓桿限制
            if self.portfolio_positions:
                current_leverage = self._calculate_leverage_ratio(
                    self.portfolio_positions, 
                    {'balance': account_balance}
                )
                if current_leverage > risk_params.max_leverage * 0.9:
                    return False, f"接近槓桿上限: {current_leverage:.1f}x / {risk_params.max_leverage:.1f}x"
            
            # 所有檢查通過
            return True, "交易檢查通過"
            
        except Exception as e:
            logger.error(f"交易檢查失敗: {e}")
            return False, f"檢查過程發生錯誤: {str(e)}"
    
    def record_trade(self, trade_info: Dict):
        """
        記錄交易信息用於統計分析
        
        Args:
            trade_info: 交易信息字典，應包含:
                - symbol: 交易對
                - side: BUY/SELL
                - size: 交易大小
                - entry_price: 進場價格
                - exit_price: 出場價格 (平倉時)
                - pnl: 盈虧 (平倉時)
                - timestamp: 時間戳
        """
        try:
            # 添加時間戳
            trade_record = {
                **trade_info,
                'recorded_at': datetime.now()
            }
            
            self.trade_history.append(trade_record)
            
            # 更新每日交易計數
            today = datetime.now().date()
            if self.last_trade_date is None or self.last_trade_date.date() != today:
                self.daily_trade_count = 1
                self.last_trade_date = datetime.now()
            else:
                self.daily_trade_count += 1
            
            # 如果有 PnL，更新歷史回撤記錄
            if 'pnl' in trade_info and self.current_balance > 0:
                balance_after_trade = self.current_balance + trade_info['pnl']
                drawdown_pct = (self.peak_balance - balance_after_trade) / self.peak_balance if self.peak_balance > 0 else 0
                
                if drawdown_pct > 0:
                    self.historical_drawdowns.append({
                        'timestamp': datetime.now(),
                        'drawdown': drawdown_pct,
                        'balance': balance_after_trade
                    })
            
            logger.info(f"✅ 交易記錄已保存: {trade_info.get('symbol', 'N/A')} {trade_info.get('side', 'N/A')}")
            
        except Exception as e:
            logger.error(f"記錄交易失敗: {e}")
    
    def get_risk_statistics(self) -> Dict:
        """獲取風險統計數據 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離統計計算模塊
        
        Returns:
            包含勝率、平均盈虧、profit factor 等統計數據的字典
        """
        try:
            # Early Return for empty data
            if not self.trade_history:
                return self._get_empty_statistics()
            
            # 過濾已平倉交易
            closed_trades = [t for t in self.trade_history if 'pnl' in t]
            if not closed_trades:
                return self._get_no_closed_trades_statistics()
            
            # 分離各統計模塊計算 (Extract Method)
            win_loss_stats = self._calculate_win_loss_statistics(closed_trades)
            profit_stats = self._calculate_profit_statistics(closed_trades)
            risk_stats = self._calculate_risk_statistics(closed_trades)
            
            # 組合完整統計報告
            return self._build_complete_statistics(win_loss_stats, profit_stats, risk_stats, closed_trades)
            
        except Exception as e:
            logger.error(f"獲取風險統計失敗: {e}")
            return {'error': str(e)}
    
    def _get_empty_statistics(self) -> Dict:
        """獲取空統計數據"""
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'avg_risk_reward': 0.0
        }
    
    def _get_no_closed_trades_statistics(self) -> Dict:
        """獲取無已平倉交易統計"""
        return {
            'total_trades': len(self.trade_history),
            'closed_trades': 0,
            'open_positions': len(self.trade_history),
            'message': '無已平倉交易數據'
        }
    
    def _calculate_win_loss_statistics(self, closed_trades: List[Dict]) -> Dict:
        """計算勝負統計"""
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] < 0]
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
        
        return {
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate
        }
    
    def _calculate_profit_statistics(self, closed_trades: List[Dict]) -> Dict:
        """計算盈利統計"""
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] < 0]
        
        # 平均盈虧
        avg_profit = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 0
        
        # Profit Factor
        total_profit = sum([t['pnl'] for t in winning_trades]) if winning_trades else 0
        total_loss = abs(sum([t['pnl'] for t in losing_trades])) if losing_trades else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return {
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'profit_factor': profit_factor
        }
    
    def _calculate_risk_statistics(self, closed_trades: List[Dict]) -> Dict:
        """計算風險統計"""
        # 最大回撤
        max_drawdown = max([d['drawdown'] for d in self.historical_drawdowns]) if self.historical_drawdowns else 0
        
        # Sharpe Ratio
        sharpe_ratio = self._calculate_sharpe_ratio(closed_trades)
        
        # 風險回報比
        avg_risk_reward = self._calculate_average_risk_reward(closed_trades)
        
        return {
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_risk_reward': avg_risk_reward
        }
    
    def _calculate_sharpe_ratio(self, closed_trades: List[Dict]) -> float:
        """計算 Sharpe Ratio"""
        if len(closed_trades) < 2:
            return 0
        
        returns = [t['pnl'] / t.get('entry_price', 1) for t in closed_trades if 'entry_price' in t]
        if not returns:
            return 0
        
        avg_return = float(np.mean(returns))
        std_return = float(np.std(returns))
        return (avg_return - 0.0001) / std_return if std_return > 0 else 0  # 假設無風險利率 0.01%
    
    def _calculate_average_risk_reward(self, closed_trades: List[Dict]) -> float:
        """計算平均風險回報比"""
        risk_rewards = []
        for t in closed_trades:
            if 'stop_loss_distance' in t and t['stop_loss_distance'] > 0:
                rr = abs(t['pnl']) / (t.get('entry_price', 1) * t['stop_loss_distance'])
                risk_rewards.append(rr)
        return float(np.mean(risk_rewards)) if risk_rewards else 0
    
    def _build_complete_statistics(
        self, 
        win_loss_stats: Dict, 
        profit_stats: Dict, 
        risk_stats: Dict, 
        closed_trades: List[Dict]
    ) -> Dict:
        """構建完整統計報告"""
        return {
            'total_trades': len(self.trade_history),
            'closed_trades': len(closed_trades),
            'open_positions': len(self.trade_history) - len(closed_trades),
            'win_rate': round(win_loss_stats['win_rate'], 4),
            'winning_trades': len(win_loss_stats['winning_trades']),
            'losing_trades': len(win_loss_stats['losing_trades']),
            'avg_profit': round(float(profit_stats['avg_profit']), 2),
            'avg_loss': round(float(profit_stats['avg_loss']), 2),
            'profit_factor': round(float(profit_stats['profit_factor']), 2) if profit_stats['profit_factor'] != float('inf') else 'inf',
            'max_drawdown': round(float(risk_stats['max_drawdown']), 4),
            'sharpe_ratio': round(float(risk_stats['sharpe_ratio']), 2),
            'avg_risk_reward': round(float(risk_stats['avg_risk_reward']), 2),
            'total_profit': round(float(profit_stats['total_profit']), 2),
            'total_loss': round(float(profit_stats['total_loss']), 2),
            'net_profit': round(float(profit_stats['total_profit'] - profit_stats['total_loss']), 2),
            'daily_trade_count': self.daily_trade_count,
            'current_balance': round(self.current_balance, 2),
            'peak_balance': round(self.peak_balance, 2)
        }
    
    def update_balance(self, balance: float):
        """
        更新餘額並重新計算回撤
        
        Args:
            balance: 最新帳戶餘額
        """
        try:
            self.current_balance = balance
            
            # 更新峰值餘額
            if balance > self.peak_balance:
                self.peak_balance = balance
                logger.info(f"📈 新峰值餘額: ${balance:,.2f}")
            
            # 計算當前回撤
            if self.peak_balance > 0:
                current_drawdown = (self.peak_balance - balance) / self.peak_balance
                
                if current_drawdown > 0:
                    logger.info(f"⚠️ 當前回撤: {current_drawdown:.2%} (${self.peak_balance - balance:,.2f})")
                    
                    # 記錄到歷史回撤
                    self.historical_drawdowns.append({
                        'timestamp': datetime.now(),
                        'drawdown': current_drawdown,
                        'balance': balance
                    })
                    
                    # 檢查是否超過任何風險等級的限制
                    for level, params in self.risk_parameters.items():
                        if current_drawdown > params.max_drawdown_limit:
                            self.risk_alerts.append(RiskAlert(
                                alert_type="DRAWDOWN_THRESHOLD_REACHED",
                                severity="CRITICAL",
                                message=f"回撤達到 {level} 等級限制: {current_drawdown:.2%} > {params.max_drawdown_limit:.2%}",
                                suggested_action="考慮停止交易或降低倉位",
                                timestamp=datetime.now()
                            ))
                            break
            
            logger.info(f"💰 餘額已更新: ${balance:,.2f}")
            
            # 保存風險統計到數據庫
            if self.db_manager:
                try:
                    stats = self.get_risk_statistics()
                    self.db_manager.save_risk_stats(stats)
                    logger.debug("💾 風險統計已保存到數據庫")
                except Exception as e:
                    logger.error(f"保存風險統計失敗: {e}")
            
        except Exception as e:
            logger.error(f"更新餘額失敗: {e}")
    
    def save_statistics_to_file(self):
        """
        保存風險統計到 JSON 文件（兼容舊版）
        
        同時會保存到數據庫（如果可用）
        """
        try:
            stats = self.get_risk_statistics()
            
            # 保存到數據庫
            if self.db_manager:
                self.db_manager.save_risk_stats(stats)
                logger.info("💾 風險統計已保存到數據庫")
            
            # 兼容：同時保存到 JSON
            stats_file = self.stats_dir / "risk_statistics.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 風險統計已保存到文件: {stats_file}")
            
        except Exception as e:
            logger.error(f"保存風險統計失敗: {e}")
    
    def load_statistics_from_database(self, days: int = 30) -> Optional[Dict]:
        """
        從數據庫加載風險統計歷史
        
        Args:
            days: 加載最近 N 天的統計
            
        Returns:
            統計數據字典或 None
        """
        if not self.db_manager:
            logger.warning("數據庫管理器不可用")
            return None
        
        try:
            stats_history = self.db_manager.get_risk_stats_history(days=days)
            
            if stats_history:
                logger.info(f"📊 從數據庫加載 {len(stats_history)} 條風險統計記錄")
                # 當前實現返回最新記錄，如需返回完整列表可擴展API
                return stats_history[0] if stats_history else None
            else:
                logger.info("📭 數據庫中無風險統計記錄")
                return None
                
        except Exception as e:
            logger.error(f"從數據庫加載風險統計失敗: {e}")
            return None