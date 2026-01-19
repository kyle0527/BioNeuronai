"""
風險管理器 - Risk Manager
全面的風險管理和頭寸規模計算系統
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import math

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """風險等級枚舉"""
    CONSERVATIVE = "保守型"
    MODERATE = "穩健型"
    AGGRESSIVE = "積極型"
    HIGH_RISK = "高風險型"

class PositionType(Enum):
    """頭寸類型枚舉"""
    LONG = "多頭"
    SHORT = "空頭"
    NEUTRAL = "中性"

@dataclass
class RiskParameters:
    """風險參數配置"""
    max_risk_per_trade: float  # 單筆交易最大風險比例
    max_daily_risk: float      # 日最大風險比例
    max_portfolio_risk: float  # 組合最大風險比例
    max_drawdown_limit: float  # 最大回撤限制
    max_correlation: float     # 最大相關性
    max_leverage: float        # 最大槓桿倍數
    position_concentration: float  # 單一頭寸最大集中度
    sector_concentration: float    # 板塊最大集中度
    
@dataclass
class PositionSizing:
    """頭寸規模計算結果"""
    symbol: str
    recommended_size: float    # 推薦頭寸大小
    max_size: float           # 最大允許頭寸
    risk_amount: float        # 風險金額
    stop_loss_distance: float # 止損距離
    entry_price: float        # 進場價格
    stop_loss_price: float    # 止損價格
    take_profit_price: float  # 止盈價格
    risk_reward_ratio: float  # 風險收益比
    kelly_fraction: float     # 凱利公式建議比例
    confidence_score: float   # 計算信心度

@dataclass
class PortfolioRisk:
    """組合風險分析"""
    timestamp: datetime
    total_exposure: float      # 總風險敞口
    var_1day_95: float        # 1日95%VaR
    var_1day_99: float        # 1日99%VaR
    expected_shortfall: float  # 期望短缺
    maximum_drawdown: float    # 最大回撤
    correlation_matrix: Dict   # 相關性矩陣
    concentration_risk: Dict   # 集中度風險
    liquidity_risk: float     # 流動性風險
    leverage_ratio: float     # 槓桿比率
    risk_adjusted_return: float # 風險調整收益

@dataclass
class RiskAlert:
    """風險警報"""
    alert_type: str    # 警報類型
    severity: str      # 嚴重程度: LOW, MEDIUM, HIGH, CRITICAL
    message: str       # 警報訊息
    suggested_action: str  # 建議行動
    timestamp: datetime

class RiskManager:
    """風險管理器 - 全面風險控制與頭寸管理"""
    
    def __init__(self):
        self.risk_parameters = self._initialize_risk_parameters()
        self.portfolio_positions = {}
        self.risk_alerts = []
        self.historical_drawdowns = []
        self.correlation_cache = {}
        
    def _initialize_risk_parameters(self) -> Dict[str, RiskParameters]:
        """初始化不同風險等級的參數"""
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
        """計算最優頭寸規模"""
        logger.info(f"💰 計算頭寸規模: {symbol}")
        logger.info(f"   進場價格: {entry_price:.2f}")
        logger.info(f"   止損價格: {stop_loss_price:.2f}")
        logger.info(f"   帳戶餘額: ${account_balance:,.2f}")
        
        try:
            risk_params = self.risk_parameters[risk_level]
            
            # 1. 計算止損距離
            stop_distance = abs(entry_price - stop_loss_price) / entry_price
            logger.info(f"   ✓ 止損距離: {stop_distance:.2%}")
            
            # 2. 基於風險的頭寸計算
            risk_based_size = self._calculate_risk_based_size(
                account_balance, stop_distance, risk_params
            )
            
            # 3. 凱利公式計算
            kelly_size = await self._calculate_kelly_size(
                symbol, entry_price, stop_loss_price, additional_factors
            )
            
            # 4. 波動率調整
            volatility_adjusted_size = await self._calculate_volatility_adjusted_size(
                symbol, risk_based_size, additional_factors
            )
            
            # 5. 流動性約束
            liquidity_adjusted_size = await self._apply_liquidity_constraints(
                symbol, volatility_adjusted_size, additional_factors
            )
            
            # 6. 相關性約束
            correlation_adjusted_size = await self._apply_correlation_constraints(
                symbol, liquidity_adjusted_size, risk_params
            )
            
            # 7. 集中度約束
            concentration_adjusted_size = self._apply_concentration_constraints(
                symbol, correlation_adjusted_size, risk_params, account_balance
            )
            
            # 8. 最終頭寸確定
            final_size = min(
                risk_based_size,
                kelly_size * 0.5,  # 凱利公式保守應用
                volatility_adjusted_size,
                liquidity_adjusted_size,
                correlation_adjusted_size,
                concentration_adjusted_size
            )
            
            # 9. 計算相關價格和比率
            max_size = account_balance * risk_params.position_concentration / entry_price
            risk_amount = final_size * entry_price * stop_distance
            
            # 計算止盈價格 (風險收益比 1:2)
            take_profit_distance = stop_distance * 2
            if entry_price > stop_loss_price:  # 多頭
                take_profit_price = entry_price * (1 + take_profit_distance)
            else:  # 空頭
                take_profit_price = entry_price * (1 - take_profit_distance)
            
            risk_reward_ratio = take_profit_distance / stop_distance
            
            # 計算信心度
            confidence_factors = [
                1.0 if stop_distance < 0.05 else 0.5,  # 止損距離合理性
                1.0 if final_size == risk_based_size else final_size / risk_based_size,  # 約束影響
                kelly_size / risk_based_size if kelly_size > 0 else 0.5  # 凱利公式一致性
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
            
            logger.info(f"   ✓ 推薦頭寸: {final_size:.4f} {symbol}")
            logger.info(f"   ✓ 風險金額: ${risk_amount:.2f} ({risk_amount/account_balance:.2%})")
            logger.info(f"   ✓ 風險收益比: 1:{risk_reward_ratio:.1f}")
            logger.info(f"   ✓ 信心度: {confidence_score:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"頭寸規模計算失敗: {e}")
            return self._get_default_position_sizing(symbol, entry_price, stop_loss_price)
    
    async def assess_portfolio_risk(self, current_positions: Dict, 
                                  market_data: Dict, account_info: Dict) -> PortfolioRisk:
        """評估組合風險"""
        logger.info("📊 評估組合風險...")
        
        try:
            # 1. 計算總風險敞口
            total_exposure = self._calculate_total_exposure(current_positions, market_data)
            
            # 2. VaR計算
            var_results = await self._calculate_var(current_positions, market_data)
            
            # 3. 相關性分析
            correlation_matrix = await self._calculate_correlation_matrix(current_positions)
            
            # 4. 集中度風險
            concentration_risk = self._analyze_concentration_risk(current_positions, account_info)
            
            # 5. 流動性風險
            liquidity_risk = await self._assess_liquidity_risk(current_positions, market_data)
            
            # 6. 槓桿分析
            leverage_ratio = self._calculate_leverage_ratio(current_positions, account_info)
            
            # 7. 最大回撤分析
            max_drawdown = self._analyze_maximum_drawdown(current_positions)
            
            # 8. 期望短缺計算
            expected_shortfall = await self._calculate_expected_shortfall(current_positions, market_data)
            
            # 9. 風險調整收益
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
            await self._generate_risk_alerts(portfolio_risk, account_info)
            
            return portfolio_risk
            
        except Exception as e:
            logger.error(f"組合風險評估失敗: {e}")
            return self._get_default_portfolio_risk()
    
    async def monitor_risk_limits(self, current_positions: Dict, 
                                account_info: Dict, risk_level: str = "MODERATE") -> List[RiskAlert]:
        """監控風險限制"""
        logger.info("🚨 監控風險限制...")
        
        alerts = []
        risk_params = self.risk_parameters[risk_level]
        
        try:
            # 1. 檢查單筆交易風險
            for symbol, position in current_positions.items():
                trade_risk = self._calculate_position_risk(position, account_info['balance'])
                
                if trade_risk > risk_params.max_risk_per_trade:
                    alerts.append(RiskAlert(
                        alert_type="TRADE_RISK_EXCEEDED",
                        severity="HIGH",
                        message=f"{symbol}單筆風險{trade_risk:.2%}超過限制{risk_params.max_risk_per_trade:.2%}",
                        suggested_action="減少頭寸規模或調整止損",
                        timestamp=datetime.now()
                    ))
            
            # 2. 檢查組合風險
            portfolio_risk = sum(self._calculate_position_risk(pos, account_info['balance']) 
                               for pos in current_positions.values())
            
            if portfolio_risk > risk_params.max_portfolio_risk:
                alerts.append(RiskAlert(
                    alert_type="PORTFOLIO_RISK_EXCEEDED", 
                    severity="CRITICAL",
                    message=f"組合總風險{portfolio_risk:.2%}超過限制{risk_params.max_portfolio_risk:.2%}",
                    suggested_action="立即減倉或對沖",
                    timestamp=datetime.now()
                ))
            
            # 3. 檢查槓桿比率
            leverage = self._calculate_leverage_ratio(current_positions, account_info)
            
            if leverage > risk_params.max_leverage:
                alerts.append(RiskAlert(
                    alert_type="LEVERAGE_EXCEEDED",
                    severity="HIGH",
                    message=f"槓桿倍數{leverage:.1f}x超過限制{risk_params.max_leverage:.1f}x",
                    suggested_action="降低槓桿或增加保證金",
                    timestamp=datetime.now()
                ))
            
            # 4. 檢查集中度
            concentration = self._check_concentration_limits(current_positions, account_info, risk_params)
            alerts.extend(concentration)
            
            # 5. 檢查相關性
            correlation_alerts = await self._check_correlation_limits(current_positions, risk_params)
            alerts.extend(correlation_alerts)
            
            # 6. 檢查回撤
            drawdown_alert = self._check_drawdown_limits(account_info, risk_params)
            if drawdown_alert:
                alerts.append(drawdown_alert)
            
            # 更新風險警報歷史
            self.risk_alerts.extend(alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"風險監控失敗: {e}")
            return []
    
    async def optimize_risk_exposure(self, target_positions: Dict, 
                                   account_info: Dict, 
                                   risk_level: str = "MODERATE") -> Dict:
        """優化風險敞口"""
        logger.info("⚖️ 優化風險敞口...")
        
        try:
            risk_params = self.risk_parameters[risk_level]
            optimized_positions = {}
            
            # 1. 計算當前總風險
            total_risk = 0
            for symbol, position in target_positions.items():
                risk = self._calculate_position_risk(position, account_info['balance'])
                total_risk += risk
            
            # 2. 如果超過限制，按比例縮減
            if total_risk > risk_params.max_portfolio_risk:
                scale_factor = risk_params.max_portfolio_risk / total_risk
                logger.info(f"   風險超限，按比例縮減: {scale_factor:.2%}")
                
                for symbol, position in target_positions.items():
                    optimized_positions[symbol] = {
                        **position,
                        'size': position['size'] * scale_factor
                    }
            else:
                optimized_positions = target_positions.copy()
            
            # 3. 檢查並調整相關性
            optimized_positions = await self._optimize_correlations(
                optimized_positions, risk_params
            )
            
            # 4. 檢查並調整集中度
            optimized_positions = self._optimize_concentration(
                optimized_positions, account_info, risk_params
            )
            
            # 5. 計算優化效果
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
            logger.error(f"風險敞口優化失敗: {e}")
            return {"optimized_positions": target_positions}
    
    # ========== 私有計算方法 ==========
    
    def _calculate_risk_based_size(self, account_balance: float, 
                                 stop_distance: float, risk_params: RiskParameters) -> float:
        """基於風險的頭寸計算"""
        risk_amount = account_balance * risk_params.max_risk_per_trade
        return risk_amount / stop_distance if stop_distance > 0 else 0
    
    async def _calculate_kelly_size(self, symbol: str, entry_price: float, 
                                  stop_loss_price: float, additional_factors: Optional[Dict] = None) -> float:
        """凱利公式計算頭寸"""
        try:
            # 模擬歷史勝率和賠率數據
            win_rate = np.random.uniform(0.45, 0.65)  # 45%-65%勝率
            avg_win = np.random.uniform(0.02, 0.08)   # 平均獲利2%-8%
            avg_loss = abs(entry_price - stop_loss_price) / entry_price  # 平均虧損
            
            if avg_loss == 0:
                return 0
            
            # 凱利公式: f* = (bp - q) / b
            # 其中 b = 賠率, p = 勝率, q = 1-p
            odds_ratio = avg_win / avg_loss
            kelly_fraction = (odds_ratio * win_rate - (1 - win_rate)) / odds_ratio
            
            # 保守應用，限制最大25%
            kelly_fraction = max(0, min(0.25, kelly_fraction))
            
            return kelly_fraction
            
        except Exception as e:
            logger.error(f"凱利公式計算失敗: {e}")
            return 0.05  # 預設5%
    
    async def _calculate_volatility_adjusted_size(self, symbol: str, base_size: float, 
                                                additional_factors: Optional[Dict] = None) -> float:
        """波動率調整頭寸"""
        try:
            # 模擬波動率數據
            volatility = np.random.uniform(0.15, 0.60)  # 15%-60%年化波動率
            
            # 基準波動率25%
            base_volatility = 0.25
            volatility_adjustment = base_volatility / volatility
            
            # 限制調整範圍在0.5-2.0倍
            volatility_adjustment = max(0.5, min(2.0, volatility_adjustment))
            
            return base_size * volatility_adjustment
            
        except Exception as e:
            logger.error(f"波動率調整計算失敗: {e}")
            return base_size
    
    async def _apply_liquidity_constraints(self, symbol: str, base_size: float, 
                                         additional_factors: Optional[Dict] = None) -> float:
        """應用流動性約束"""
        try:
            # 模擬市場深度數據
            market_depth = np.random.uniform(0.5, 2.0)  # 相對市場深度
            daily_volume = np.random.uniform(10000, 100000)  # 日交易量
            
            # 限制頭寸不超過日交易量的2%
            max_size_by_volume = daily_volume * 0.02
            
            # 根據市場深度調整
            liquidity_adjusted_size = min(base_size, max_size_by_volume) * market_depth
            
            return max(0, liquidity_adjusted_size)
            
        except Exception as e:
            logger.error(f"流動性約束應用失敗: {e}")
            return base_size * 0.8  # 保守估計
    
    async def _apply_correlation_constraints(self, symbol: str, base_size: float, 
                                           risk_params: RiskParameters) -> float:
        """應用相關性約束"""
        try:
            # 檢查與現有持倉的相關性
            existing_symbols = list(self.portfolio_positions.keys())
            
            if not existing_symbols:
                return base_size
            
            # 模擬相關性數據
            correlations = {
                existing_symbol: np.random.uniform(-0.3, 0.9)
                for existing_symbol in existing_symbols
            }
            
            # 如果與任何現有持倉高度相關，減少頭寸
            max_correlation = max(correlations.values()) if correlations else 0
            
            if max_correlation > risk_params.max_correlation:
                correlation_adjustment = risk_params.max_correlation / max_correlation
                return base_size * correlation_adjustment
            
            return base_size
            
        except Exception as e:
            logger.error(f"相關性約束應用失敗: {e}")
            return base_size
    
    def _apply_concentration_constraints(self, symbol: str, base_size: float, 
                                       risk_params: RiskParameters, account_balance: float) -> float:
        """應用集中度約束"""
        try:
            # 單一頭寸集中度限制
            max_position_value = account_balance * risk_params.position_concentration
            
            # 如果基礎頭寸值超過限制，按比例縮減
            if base_size > max_position_value:
                return max_position_value
            
            return base_size
            
        except Exception as e:
            logger.error(f"集中度約束應用失敗: {e}")
            return base_size * 0.8
    
    # ========== 風險評估方法 ==========
    
    def _calculate_total_exposure(self, positions: Dict, market_data: Dict) -> float:
        """計算總風險敞口"""
        total_exposure = 0
        
        for symbol, position in positions.items():
            position_value = position.get('size', 0) * position.get('price', 0)
            leverage = position.get('leverage', 1)
            total_exposure += position_value * leverage
        
        return total_exposure
    
    async def _calculate_var(self, positions: Dict, market_data: Dict) -> Dict:
        """計算風險價值(VaR)"""
        try:
            # 模擬組合日收益率分布
            portfolio_returns = np.random.normal(0.001, 0.025, 1000)  # 0.1%均值，2.5%標準差
            
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
    
    async def _calculate_correlation_matrix(self, positions: Dict) -> Dict:
        """計算相關性矩陣"""
        try:
            symbols = list(positions.keys())
            correlation_matrix = {}
            
            for i, symbol1 in enumerate(symbols):
                correlation_matrix[symbol1] = {}
                for j, symbol2 in enumerate(symbols):
                    if i == j:
                        correlation_matrix[symbol1][symbol2] = 1.0
                    else:
                        # 模擬相關系數
                        correlation = np.random.uniform(0.3, 0.8)
                        correlation_matrix[symbol1][symbol2] = correlation
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"相關性矩陣計算失敗: {e}")
            return {}
    
    def _analyze_concentration_risk(self, positions: Dict, account_info: Dict) -> Dict:
        """分析集中度風險"""
        try:
            account_balance = account_info.get('balance', 0)
            
            if account_balance == 0:
                return {}
            
            concentration_risk = {}
            
            # 單一頭寸集中度
            for symbol, position in positions.items():
                position_value = position.get('size', 0) * position.get('price', 0)
                concentration = position_value / account_balance
                concentration_risk[symbol] = concentration
            
            # 總體集中度指標
            total_concentration = sum(concentration_risk.values())
            herfindahl_index = sum(c**2 for c in concentration_risk.values())
            
            return {
                "individual_concentrations": concentration_risk,
                "total_concentration": total_concentration,
                "herfindahl_index": herfindahl_index,
                "max_individual_concentration": max(concentration_risk.values()) if concentration_risk else 0
            }
            
        except Exception as e:
            logger.error(f"集中度風險分析失敗: {e}")
            return {}
    
    async def _assess_liquidity_risk(self, positions: Dict, market_data: Dict) -> float:
        """評估流動性風險"""
        try:
            liquidity_scores = []
            
            for symbol, position in positions.items():
                # 模擬流動性指標
                bid_ask_spread = np.random.uniform(0.001, 0.01)  # 0.1%-1%點差
                market_depth = np.random.uniform(0.5, 2.0)       # 市場深度
                trading_volume = np.random.uniform(0.1, 10.0)    # 相對交易量
                
                # 流動性評分 (0-1，越高越好)
                spread_score = max(0, 1 - bid_ask_spread * 100)
                depth_score = min(1, market_depth / 2.0)
                volume_score = min(1, trading_volume / 5.0)
                
                position_liquidity = (spread_score + depth_score + volume_score) / 3
                liquidity_scores.append(position_liquidity)
            
            # 組合流動性風險 (1 - 平均流動性評分)
            avg_liquidity = np.mean(liquidity_scores) if liquidity_scores else 0.5
            liquidity_risk = float(1 - avg_liquidity)
            
            return liquidity_risk
            
        except Exception as e:
            logger.error(f"流動性風險評估失敗: {e}")
            return 0.3  # 中等流動性風險
    
    def _calculate_leverage_ratio(self, positions: Dict, account_info: Dict) -> float:
        """計算槓桿比率"""
        try:
            total_notional = 0
            account_balance = account_info.get('balance', 0)
            
            for position in positions.values():
                position_value = position.get('size', 0) * position.get('price', 0)
                leverage = position.get('leverage', 1)
                total_notional += position_value * leverage
            
            return total_notional / account_balance if account_balance > 0 else 0
            
        except Exception as e:
            logger.error(f"槓桿比率計算失敗: {e}")
            return 1.0
    
    def _analyze_maximum_drawdown(self, positions: Dict) -> float:
        """分析最大回撤"""
        try:
            # 模擬組合歷史淨值數據
            portfolio_values = [100000]  # 起始100,000
            
            for i in range(100):  # 模擬100個交易日
                daily_return = np.random.normal(0.001, 0.02)  # 日收益率
                new_value = float(portfolio_values[-1] * (1 + daily_return))
                portfolio_values.append(new_value)
            
            # 計算最大回撤
            peak = portfolio_values[0]
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"最大回撤分析失敗: {e}")
            return 0.1  # 預設10%
    
    async def _calculate_expected_shortfall(self, positions: Dict, market_data: Dict) -> float:
        """計算期望短缺(ES)"""
        try:
            # 模擬組合收益率分布
            returns = np.random.normal(0.001, 0.025, 10000)
            
            # 計算95% VaR
            var_95 = np.percentile(returns, 5)
            
            # 計算期望短缺 (超過VaR的平均損失)
            tail_losses = returns[returns <= var_95]
            expected_shortfall = float(np.mean(tail_losses) * -1)
            
            return expected_shortfall
            
        except Exception as e:
            logger.error(f"期望短缺計算失敗: {e}")
            return 0.035  # 預設3.5%
    
    def _calculate_risk_adjusted_return(self, positions: Dict, account_info: Dict) -> float:
        """計算風險調整收益"""
        try:
            # 模擬組合表現數據
            annual_return = np.random.uniform(0.08, 0.25)  # 8%-25%年化收益
            volatility = np.random.uniform(0.15, 0.35)     # 15%-35%年化波動率
            
            # 夏普比率 (無風險利率假設為3%)
            risk_free_rate = 0.03
            sharpe_ratio = (annual_return - risk_free_rate) / volatility
            
            return sharpe_ratio
            
        except Exception as e:
            logger.error(f"風險調整收益計算失敗: {e}")
            return 1.0  # 預設夏普比率
    
    # ========== 風險監控方法 ==========
    
    def _calculate_position_risk(self, position: Dict, account_balance: float) -> float:
        """計算單一頭寸風險"""
        try:
            position_value = position.get('size', 0) * position.get('price', 0)
            stop_loss_distance = position.get('stop_loss_distance', 0.02)
            leverage = position.get('leverage', 1)
            
            risk_amount = position_value * stop_loss_distance * leverage
            risk_percentage = risk_amount / account_balance if account_balance > 0 else 0
            
            return risk_percentage
            
        except Exception as e:
            logger.error(f"頭寸風險計算失敗: {e}")
            return 0.01  # 預設1%風險
    
    def _check_concentration_limits(self, positions: Dict, account_info: Dict, 
                                  risk_params: RiskParameters) -> List[RiskAlert]:
        """檢查集中度限制"""
        alerts = []
        concentration_analysis = self._analyze_concentration_risk(positions, account_info)
        
        # 檢查單一頭寸集中度
        for symbol, concentration in concentration_analysis.get('individual_concentrations', {}).items():
            if concentration > risk_params.position_concentration:
                alerts.append(RiskAlert(
                    alert_type="POSITION_CONCENTRATION_EXCEEDED",
                    severity="MEDIUM",
                    message=f"{symbol}持倉集中度{concentration:.2%}超過限制{risk_params.position_concentration:.2%}",
                    suggested_action="分散投資或減少該頭寸",
                    timestamp=datetime.now()
                ))
        
        return alerts
    
    async def _check_correlation_limits(self, positions: Dict, 
                                      risk_params: RiskParameters) -> List[RiskAlert]:
        """檢查相關性限制"""
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
                            message=f"{symbol1}與{symbol2}相關性{correlation:.2%}過高",
                            suggested_action="考慮降低其中一個頭寸或增加對沖",
                            timestamp=datetime.now()
                        ))
                        break  # 避免重複警報
        
        except Exception as e:
            logger.error(f"相關性檢查失敗: {e}")
        
        return alerts
    
    def _check_drawdown_limits(self, account_info: Dict, 
                              risk_params: RiskParameters) -> Optional[RiskAlert]:
        """檢查回撤限制"""
        try:
            current_balance = account_info.get('balance', 0)
            peak_balance = account_info.get('peak_balance', current_balance)
            
            if peak_balance > 0:
                current_drawdown = (peak_balance - current_balance) / peak_balance
                
                if current_drawdown > risk_params.max_drawdown_limit:
                    return RiskAlert(
                        alert_type="DRAWDOWN_LIMIT_EXCEEDED",
                        severity="CRITICAL",
                        message=f"當前回撤{current_drawdown:.2%}超過限制{risk_params.max_drawdown_limit:.2%}",
                        suggested_action="立即停止交易並評估策略",
                        timestamp=datetime.now()
                    )
        
        except Exception as e:
            logger.error(f"回撤檢查失敗: {e}")
        
        return None
    
    # ========== 風險優化方法 ==========
    
    async def _optimize_correlations(self, positions: Dict, 
                                   risk_params: RiskParameters) -> Dict:
        """優化相關性"""
        try:
            correlation_matrix = await self._calculate_correlation_matrix(positions)
            optimized_positions = positions.copy()
            
            # 識別高相關的頭寸對
            high_correlation_pairs = []
            for symbol1, correlations in correlation_matrix.items():
                for symbol2, correlation in correlations.items():
                    if (symbol1 != symbol2 and 
                        correlation > risk_params.max_correlation and
                        (symbol2, symbol1) not in high_correlation_pairs):
                        high_correlation_pairs.append((symbol1, symbol2))
            
            # 對高相關的頭寸對進行調整
            for symbol1, symbol2 in high_correlation_pairs:
                # 保留較大的頭寸，縮減較小的
                size1 = optimized_positions[symbol1].get('size', 0)
                size2 = optimized_positions[symbol2].get('size', 0)
                
                if size1 > size2:
                    optimized_positions[symbol2]['size'] *= 0.7
                else:
                    optimized_positions[symbol1]['size'] *= 0.7
            
            return optimized_positions
            
        except Exception as e:
            logger.error(f"相關性優化失敗: {e}")
            return positions
    
    def _optimize_concentration(self, positions: Dict, account_info: Dict, 
                               risk_params: RiskParameters) -> Dict:
        """優化集中度"""
        try:
            account_balance = account_info.get('balance', 0)
            optimized_positions = positions.copy()
            
            # 檢查並調整單一頭寸集中度
            for symbol, position in optimized_positions.items():
                position_value = position.get('size', 0) * position.get('price', 0)
                concentration = position_value / account_balance if account_balance > 0 else 0
                
                if concentration > risk_params.position_concentration:
                    # 縮減頭寸至限制水平
                    adjustment_factor = risk_params.position_concentration / concentration
                    optimized_positions[symbol]['size'] *= adjustment_factor
            
            return optimized_positions
            
        except Exception as e:
            logger.error(f"集中度優化失敗: {e}")
            return positions
    
    async def _generate_risk_alerts(self, portfolio_risk: PortfolioRisk, 
                                   account_info: Dict):
        """生成風險警報"""
        try:
            # VaR警報
            if portfolio_risk.var_1day_95 > 0.03:  # 3%
                self.risk_alerts.append(RiskAlert(
                    alert_type="HIGH_VAR_DETECTED",
                    severity="MEDIUM",
                    message=f"95% VaR達到{portfolio_risk.var_1day_95:.2%}，風險較高",
                    suggested_action="考慮減倉或增加對沖",
                    timestamp=datetime.now()
                ))
            
            # 流動性風險警報
            if portfolio_risk.liquidity_risk > 0.5:
                self.risk_alerts.append(RiskAlert(
                    alert_type="HIGH_LIQUIDITY_RISK",
                    severity="MEDIUM",
                    message=f"流動性風險{portfolio_risk.liquidity_risk:.2%}偏高",
                    suggested_action="避免大額交易或選擇更具流動性的資產",
                    timestamp=datetime.now()
                ))
        
        except Exception as e:
            logger.error(f"風險警報生成失敗: {e}")
    
    # ========== 預設值方法 ==========
    
    def _get_default_position_sizing(self, symbol: str, entry_price: float, 
                                   stop_loss_price: float) -> PositionSizing:
        """預設頭寸規模"""
        stop_distance = abs(entry_price - stop_loss_price) / entry_price
        
        return PositionSizing(
            symbol=symbol,
            recommended_size=0.01,  # 預設1%
            max_size=0.05,          # 最大5%
            risk_amount=100.0,      # 預設$100風險
            stop_loss_distance=stop_distance,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=entry_price * (1.04 if entry_price > stop_loss_price else 0.96),
            risk_reward_ratio=2.0,
            kelly_fraction=0.05,
            confidence_score=0.5
        )
    
    def _get_default_portfolio_risk(self) -> PortfolioRisk:
        """預設組合風險"""
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
        """獲取風險管理摘要"""
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