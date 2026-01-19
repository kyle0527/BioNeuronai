"""
🎯 SOP 第二步：單筆交易前檢查自動化系統
Per-Trade Pre-Execution Checklist Automation

根據 CRYPTO_TRADING_SOP.md 自動執行 1.2 單筆交易前檢查
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import math
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TechnicalSignalCheck:
    """技術信號檢查結果"""
    timestamp: datetime
    main_trend: str = "UNKNOWN"  # 上升/下降/震盪
    support_resistance: Optional[Dict] = None
    timeframes_aligned: bool = False
    rsi_status: str = "UNKNOWN"
    macd_signal: str = "UNKNOWN"
    bollinger_position: str = "UNKNOWN"
    signal_strength: float = 0.0
    signal_count: int = 0
    overall_status: str = "UNKNOWN"

@dataclass
class FundamentalCheck:
    """基本面檢查結果"""
    timestamp: datetime
    no_major_negative: bool = True
    normal_fund_flow: bool = True
    normal_volume: bool = True
    sufficient_depth: bool = True
    overall_status: str = "UNKNOWN"

@dataclass
class RiskCalculation:
    """風險計算結果"""
    timestamp: datetime
    account_balance: float = 0.0
    risk_percentage: float = 0.02  # 2%
    max_loss_amount: float = 0.0
    position_size: float = 0.0
    entry_price: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    win_rate: float = 0.6
    profit_target: float = 0.04  # 4%
    max_loss: float = 0.02  # 2%
    expected_return: float = 0.0
    risk_reward_ratio: float = 0.0
    overall_status: str = "UNKNOWN"

@dataclass
class OrderParameters:
    """訂單參數設定"""
    timestamp: datetime
    order_type: str = "LIMIT"  # LIMIT/MARKET
    entry_price: float = 0.0
    quantity: float = 0.0
    leverage: int = 1
    stop_loss_type: str = "STOP_MARKET"
    stop_loss_price: float = 0.0
    take_profit_enabled: bool = True
    take_profit_targets: Optional[List[Dict]] = None
    overall_status: str = "UNKNOWN"

@dataclass
class FinalConfirmation:
    """最終確認檢查"""
    timestamp: datetime
    psychological_state: bool = True
    trading_log_ready: bool = True
    signal_reconfirmed: bool = False
    risk_acceptable: bool = False
    plan_compliant: bool = False
    triple_check_passed: bool = False
    overall_status: str = "UNKNOWN"

class PreTradeCheckSystem:
    """單筆交易前檢查系統"""
    
    def __init__(self):
        self.data_dir = Path("pretrade_check_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 嘗試導入交易模組
        self._import_modules()
        
        # 預設風險參數
        self.default_risk_params = {
            "risk_percentage": 0.02,  # 2%
            "min_risk_reward_ratio": 1.5,
            "max_leverage": 10,
            "min_expected_return": 0.005  # 0.5%
        }
    
    def _import_modules(self):
        """導入所需模組"""
        try:
            from . import CryptoFuturesTrader, TradingSignal
            from .news_analyzer import CryptoNewsAnalyzer
            from .trading_strategies import StrategyFusion
            self.modules_available = True
            logger.info("✅ 交易模組導入成功")
        except ImportError as e:
            logger.warning(f"⚠️ 部分模組不可用: {e}")
            self.modules_available = False
    
    async def execute_pretrade_check(self, symbol: str = "BTCUSDT", 
                                   signal_source: str = "AI_FUSION",
                                   intended_action: str = "BUY") -> Dict[str, Any]:
        """
        執行單筆交易前檢查 (SOP 步驟 1.2)
        
        Args:
            symbol: 交易對
            signal_source: 信號來源
            intended_action: 預期動作 (BUY/SELL)
        
        Returns:
            Dict: 完整的檢查結果
        """
        logger.info(f"🎯 開始執行單筆交易前檢查 - {symbol} {intended_action}")
        
        start_time = datetime.now()
        results = {
            "check_time": start_time,
            "sop_version": "1.0", 
            "sop_step": "1.2 單筆交易前檢查",
            "symbol": symbol,
            "intended_action": intended_action,
            "signal_source": signal_source
        }
        
        # Step 1: 技術信號確認
        logger.info("📊 Step 1/5: 技術信號確認")
        technical_check = await self._check_technical_signals(symbol, intended_action)
        results["technical_signals"] = technical_check
        
        # Step 2: 基本面檢查
        logger.info("📰 Step 2/5: 基本面檢查")
        fundamental_check = await self._check_fundamentals(symbol)
        results["fundamentals"] = fundamental_check
        
        # Step 3: 風險計算
        logger.info("⚖️ Step 3/5: 風險計算")
        risk_calculation = await self._calculate_risk(symbol, intended_action, technical_check)
        results["risk_calculation"] = risk_calculation
        
        # Step 4: 訂單參數設定
        logger.info("📋 Step 4/5: 訂單參數設定")
        order_params = await self._configure_order_parameters(symbol, intended_action, risk_calculation)
        results["order_parameters"] = order_params
        
        # Step 5: 最終確認
        logger.info("✅ Step 5/5: 最終確認檢查")
        final_confirmation = await self._final_confirmation_check(
            technical_check, fundamental_check, risk_calculation, order_params
        )
        results["final_confirmation"] = final_confirmation
        
        # 綜合評估
        overall_assessment = self._assess_trade_readiness(
            technical_check, fundamental_check, risk_calculation, 
            order_params, final_confirmation
        )
        results["overall_assessment"] = overall_assessment
        
        # 保存結果
        self._save_pretrade_results(results)
        
        completion_time = datetime.now()
        duration = (completion_time - start_time).total_seconds()
        
        logger.info(f"✅ 單筆交易檢查完成 | 耗時: {duration:.1f}秒")
        logger.info(f"🎯 交易建議: {overall_assessment['recommendation']}")
        
        return results
    
    async def _check_technical_signals(self, symbol: str, action: str) -> TechnicalSignalCheck:
        """檢查技術信號 (SOP 1.2 第一部分)"""
        check = TechnicalSignalCheck(timestamp=datetime.now())
        
        try:
            logger.info("   📈 分析主要趨勢方向...")
            
            # 模擬獲取市場數據進行技術分析
            market_data = await self._get_market_data(symbol)
            
            if market_data:
                # 1. 主要趨勢分析
                check.main_trend = self._analyze_main_trend(market_data)
                logger.info(f"     ✓ 主要趨勢: {check.main_trend}")
                
                # 2. 支撐阻力位分析
                check.support_resistance = self._find_support_resistance(market_data)
                logger.info(f"     ✓ 關鍵位: 支撐 ${check.support_resistance.get('support', 0):.0f}, 阻力 ${check.support_resistance.get('resistance', 0):.0f}")
                
                # 3. 多時間框架對齊檢查
                check.timeframes_aligned = self._check_timeframe_alignment(market_data, action)
                logger.info(f"     ✓ 時間框架對齊: {'是' if check.timeframes_aligned else '否'}")
                
                # 4. 技術指標分析
                check.rsi_status = self._analyze_rsi(market_data)
                check.macd_signal = self._analyze_macd(market_data)
                check.bollinger_position = self._analyze_bollinger(market_data)
                
                logger.info(f"     ✓ RSI 狀態: {check.rsi_status}")
                logger.info(f"     ✓ MACD 信號: {check.macd_signal}")
                logger.info(f"     ✓ 布林帶位置: {check.bollinger_position}")
                
                # 5. 信號強度評估
                check.signal_strength, check.signal_count = self._calculate_signal_strength(
                    check, action
                )
                logger.info(f"     ✓ 信號強度: {check.signal_strength:.1f}/10 ({check.signal_count}個確認信號)")
                
                # 6. 綜合評估
                check.overall_status = self._assess_technical_status(check)
            else:
                logger.warning("   ⚠️ 無法獲取市場數據，使用預設值")
                check.overall_status = "DATA_UNAVAILABLE"
                
        except Exception as e:
            logger.error(f"   ❌ 技術信號檢查失敗: {e}")
            check.overall_status = "ERROR"
        
        return check
    
    async def _check_fundamentals(self, symbol: str) -> FundamentalCheck:
        """檢查基本面 (SOP 1.2 第二部分)"""
        check = FundamentalCheck(timestamp=datetime.now())
        
        try:
            logger.info("   📰 檢查基本面狀況...")
            
            # 1. 重大消息檢查
            major_news = await self._check_major_news(symbol)
            check.no_major_negative = not major_news.get('has_major_negative', False)
            logger.info(f"     ✓ 無重大利空: {'是' if check.no_major_negative else '否'}")
            
            # 2. 資金流動檢查
            fund_flow = await self._check_fund_flow(symbol)
            check.normal_fund_flow = fund_flow.get('is_normal', True)
            logger.info(f"     ✓ 資金流動正常: {'是' if check.normal_fund_flow else '否'}")
            
            # 3. 交易量檢查
            volume_data = await self._check_volume(symbol)
            check.normal_volume = volume_data.get('is_normal', True)
            logger.info(f"     ✓ 交易量正常: {'是' if check.normal_volume else '否'}")
            
            # 4. 市場深度檢查
            depth_data = await self._check_market_depth(symbol)
            check.sufficient_depth = depth_data.get('sufficient', True)
            logger.info(f"     ✓ 市場深度充足: {'是' if check.sufficient_depth else '否'}")
            
            # 綜合評估
            check.overall_status = self._assess_fundamental_status(check)
            
        except Exception as e:
            logger.error(f"   ❌ 基本面檢查失敗: {e}")
            check.overall_status = "ERROR"
        
        return check
    
    async def _calculate_risk(self, symbol: str, action: str, 
                            technical_check: TechnicalSignalCheck) -> RiskCalculation:
        """風險計算 (SOP 1.2 第三部分 - 1% 規則)"""
        calc = RiskCalculation(timestamp=datetime.now())
        
        try:
            logger.info("   💰 執行風險計算...")
            
            # 1. 獲取帳戶資訊
            account_info = await self._get_account_info()
            calc.account_balance = account_info.get('total_balance', 10000.0)  # 預設$10,000
            calc.risk_percentage = self.default_risk_params['risk_percentage']
            calc.max_loss_amount = calc.account_balance * calc.risk_percentage
            
            logger.info(f"     ✓ 帳戶總資金: ${calc.account_balance:.2f}")
            logger.info(f"     ✓ 風險比例: {calc.risk_percentage*100:.1f}%")
            logger.info(f"     ✓ 最大虧損: ${calc.max_loss_amount:.2f}")
            
            # 2. 獲取當前價格
            current_price = await self._get_current_price(symbol)
            calc.entry_price = current_price or 50000.0  # 預設BTC價格
            
            # 3. 計算止損價格 (基於技術位或固定百分比)
            if technical_check.support_resistance:
                # 基於技術位
                if action == "BUY":
                    calc.stop_loss_price = technical_check.support_resistance.get('support', 0)
                    if calc.stop_loss_price == 0:
                        calc.stop_loss_price = calc.entry_price * 0.98  # 2% 止損
                else:  # SELL
                    calc.stop_loss_price = technical_check.support_resistance.get('resistance', 0)
                    if calc.stop_loss_price == 0:
                        calc.stop_loss_price = calc.entry_price * 1.02  # 2% 止損
            else:
                # 固定百分比止損
                if action == "BUY":
                    calc.stop_loss_price = calc.entry_price * 0.98  # 2% 止損
                else:
                    calc.stop_loss_price = calc.entry_price * 1.02  # 2% 止損
            
            # 4. 計算倉位大小 (1% 規則)
            price_diff = abs(calc.entry_price - calc.stop_loss_price)
            if price_diff > 0:
                calc.position_size = calc.max_loss_amount / price_diff
            else:
                calc.position_size = 0.001  # 最小倉位
            
            logger.info(f"     ✓ 入場價格: ${calc.entry_price:.2f}")
            logger.info(f"     ✓ 止損價格: ${calc.stop_loss_price:.2f}")
            logger.info(f"     ✓ 倉位大小: {calc.position_size:.6f}")
            
            # 5. 計算止盈目標
            profit_distance = price_diff * 2  # 2:1 盈虧比
            if action == "BUY":
                calc.take_profit_price = calc.entry_price + profit_distance
            else:
                calc.take_profit_price = calc.entry_price - profit_distance
            
            # 6. 計算期望回報
            calc.win_rate = 0.6  # 60% 勝率 (可從歷史數據獲取)
            calc.profit_target = profit_distance / calc.entry_price
            calc.max_loss = price_diff / calc.entry_price
            
            calc.expected_return = (calc.win_rate * calc.profit_target) + ((1 - calc.win_rate) * (-calc.max_loss))
            
            # 7. 計算盈虧比
            calc.risk_reward_ratio = calc.profit_target / calc.max_loss if calc.max_loss > 0 else 0
            
            logger.info(f"     ✓ 止盈價格: ${calc.take_profit_price:.2f}")
            logger.info(f"     ✓ 期望回報: {calc.expected_return*100:.2f}%")
            logger.info(f"     ✓ 盈虧比: {calc.risk_reward_ratio:.2f}:1")
            
            # 8. 風險評估
            calc.overall_status = self._assess_risk_status(calc)
            
        except Exception as e:
            logger.error(f"   ❌ 風險計算失敗: {e}")
            calc.overall_status = "ERROR"
        
        return calc
    
    async def _configure_order_parameters(self, symbol: str, action: str,
                                        risk_calc: RiskCalculation) -> OrderParameters:
        """配置訂單參數 (SOP 1.2 第四部分)"""
        params = OrderParameters(timestamp=datetime.now())
        
        try:
            logger.info("   📋 設定訂單參數...")
            
            # 1. 入場訂單設定
            params.order_type = "LIMIT"  # 預設限價單
            params.entry_price = risk_calc.entry_price
            params.quantity = risk_calc.position_size
            params.leverage = min(5, self.default_risk_params['max_leverage'])  # 保守槓桿
            
            logger.info(f"     ✓ 訂單類型: {params.order_type}")
            logger.info(f"     ✓ 入場價格: ${params.entry_price:.2f}")
            logger.info(f"     ✓ 訂單數量: {params.quantity:.6f}")
            logger.info(f"     ✓ 槓桿倍數: {params.leverage}x")
            
            # 2. 止損訂單設定
            params.stop_loss_type = "STOP_MARKET"  # 止損市價單，確保執行
            params.stop_loss_price = risk_calc.stop_loss_price
            
            logger.info(f"     ✓ 止損類型: {params.stop_loss_type}")
            logger.info(f"     ✓ 止損價格: ${params.stop_loss_price:.2f}")
            
            # 3. 止盈訂單設定 (分批止盈)
            params.take_profit_enabled = True
            params.take_profit_targets = [
                {"percentage": 30, "price": risk_calc.take_profit_price * 0.7 + risk_calc.entry_price * 0.3},
                {"percentage": 40, "price": risk_calc.take_profit_price * 0.85 + risk_calc.entry_price * 0.15},
                {"percentage": 30, "price": risk_calc.take_profit_price}
            ]
            
            logger.info("     ✓ 分批止盈目標:")
            for i, target in enumerate(params.take_profit_targets, 1):
                logger.info(f"       {target['percentage']}% @ ${target['price']:.2f}")
            
            # 4. 參數驗證
            params.overall_status = self._validate_order_parameters(params, risk_calc)
            
        except Exception as e:
            logger.error(f"   ❌ 訂單參數設定失敗: {e}")
            params.overall_status = "ERROR"
        
        return params
    
    async def _final_confirmation_check(self, technical: TechnicalSignalCheck,
                                      fundamental: FundamentalCheck,
                                      risk: RiskCalculation,
                                      order: OrderParameters) -> FinalConfirmation:
        """最終確認檢查 (SOP 1.2 第五部分)"""
        check = FinalConfirmation(timestamp=datetime.now())
        
        try:
            logger.info("   ✅ 執行最終確認...")
            
            # 1. 心理狀態檢查 (模擬)
            check.psychological_state = True  # 假設狀態良好
            logger.info(f"     ✓ 心理狀態: {'良好' if check.psychological_state else '需調整'}")
            
            # 2. 交易記錄準備
            check.trading_log_ready = True  # 系統自動準備
            logger.info(f"     ✓ 交易日誌: {'已準備' if check.trading_log_ready else '未準備'}")
            
            # 3. 三次確認原則
            # 第一次：再次確認信號有效性
            check.signal_reconfirmed = (
                technical.overall_status in ["STRONG", "MODERATE"] and
                technical.signal_strength >= 6.0
            )
            logger.info(f"     ✓ 信號重確認: {'通過' if check.signal_reconfirmed else '不通過'}")
            
            # 第二次：再次確認風險可控性
            check.risk_acceptable = (
                risk.overall_status == "ACCEPTABLE" and
                risk.risk_reward_ratio >= self.default_risk_params['min_risk_reward_ratio'] and
                risk.expected_return >= self.default_risk_params['min_expected_return']
            )
            logger.info(f"     ✓ 風險可控性: {'通過' if check.risk_acceptable else '不通過'}")
            
            # 第三次：再次確認符合交易計劃
            check.plan_compliant = (
                fundamental.overall_status in ["GOOD", "ACCEPTABLE"] and
                order.overall_status == "VALID"
            )
            logger.info(f"     ✓ 計劃符合性: {'通過' if check.plan_compliant else '不通過'}")
            
            # 三次確認結果
            check.triple_check_passed = (
                check.signal_reconfirmed and 
                check.risk_acceptable and 
                check.plan_compliant
            )
            
            logger.info(f"     🎯 三次確認: {'全部通過' if check.triple_check_passed else '存在問題'}")
            
            # 綜合評估
            check.overall_status = self._assess_final_confirmation(check)
            
        except Exception as e:
            logger.error(f"   ❌ 最終確認檢查失敗: {e}")
            check.overall_status = "ERROR"
        
        return check
    
    # ========== 輔助方法 ==========
    
    async def _get_market_data(self, symbol: str) -> Optional[Dict]:
        """獲取市場數據"""
        try:
            # 根據不同交易對返回相應數據
            if "BTC" in symbol:
                return {
                    "symbol": symbol,
                    "price": 50000.0,
                    "volume_24h": 1000000,
                    "high_24h": 51000.0,
                    "low_24h": 49000.0,
                    "rsi": 55.0,
                    "macd": {"signal": "BULLISH", "histogram": 0.5},
                    "bollinger": {"position": "MIDDLE", "width": 0.04},
                    "support": 49500.0,
                    "resistance": 50500.0,
                    "timeframes": {
                        "15m": "BULLISH",
                        "1h": "BULLISH", 
                        "4h": "NEUTRAL"
                    }
                }
            elif "ETH" in symbol:
                return {
                    "symbol": symbol,
                    "price": 3000.0,
                    "volume_24h": 500000,
                    "high_24h": 3100.0,
                    "low_24h": 2900.0,
                    "rsi": 52.0,
                    "macd": {"signal": "BULLISH", "histogram": 0.3},
                    "bollinger": {"position": "MIDDLE", "width": 0.03},
                    "support": 2950.0,
                    "resistance": 3050.0,
                    "timeframes": {
                        "15m": "BULLISH",
                        "1h": "NEUTRAL", 
                        "4h": "NEUTRAL"
                    }
                }
            else:
                # 默認數據
                return {
                    "symbol": symbol,
                    "price": 1.0,
                    "volume_24h": 100000,
                    "high_24h": 1.1,
                    "low_24h": 0.9,
                    "rsi": 50.0,
                    "macd": {"signal": "NEUTRAL", "histogram": 0.0},
                    "bollinger": {"position": "MIDDLE", "width": 0.02},
                    "support": 0.95,
                    "resistance": 1.05,
                    "timeframes": {
                        "15m": "NEUTRAL",
                        "1h": "NEUTRAL", 
                        "4h": "NEUTRAL"
                    }
                }
        except Exception as e:
            logger.error(f"獲取市場數據失敗: {e}")
            return None
    
    def _analyze_main_trend(self, data: Dict) -> str:
        """分析主要趨勢"""
        # 簡單的趨勢分析邏輯
        timeframes = data.get("timeframes", {})
        bullish_count = sum(1 for trend in timeframes.values() if trend == "BULLISH")
        bearish_count = sum(1 for trend in timeframes.values() if trend == "BEARISH")
        
        if bullish_count > bearish_count:
            return "上升趨勢"
        elif bearish_count > bullish_count:
            return "下降趨勢"
        else:
            return "震盪整理"
    
    def _find_support_resistance(self, data: Dict) -> Dict:
        """找出支撐阻力位"""
        return {
            "support": data.get("support", data.get("low_24h", 0)),
            "resistance": data.get("resistance", data.get("high_24h", 0))
        }
    
    def _check_timeframe_alignment(self, data: Dict, action: str) -> bool:
        """檢查多時間框架對齊"""
        timeframes = data.get("timeframes", {})
        if action == "BUY":
            return sum(1 for trend in timeframes.values() if trend in ["BULLISH", "NEUTRAL"]) >= 2
        else:
            return sum(1 for trend in timeframes.values() if trend in ["BEARISH", "NEUTRAL"]) >= 2
    
    def _analyze_rsi(self, data: Dict) -> str:
        """分析RSI狀態"""
        rsi = data.get("rsi", 50)
        if rsi > 70:
            return "超買"
        elif rsi < 30:
            return "超賣"
        elif 40 <= rsi <= 60:
            return "中性區間"
        else:
            return "正常"
    
    def _analyze_macd(self, data: Dict) -> str:
        """分析MACD信號"""
        macd_data = data.get("macd", {})
        return macd_data.get("signal", "NEUTRAL")
    
    def _analyze_bollinger(self, data: Dict) -> str:
        """分析布林帶位置"""
        bollinger = data.get("bollinger", {})
        return bollinger.get("position", "MIDDLE")
    
    def _calculate_signal_strength(self, check: TechnicalSignalCheck, action: str) -> Tuple[float, int]:
        """計算信號強度"""
        strength = 0.0
        count = 0
        
        # 趨勢確認
        if action == "BUY" and "上升" in check.main_trend:
            strength += 2.0
            count += 1
        elif action == "SELL" and "下降" in check.main_trend:
            strength += 2.0
            count += 1
        
        # 時間框架對齊
        if check.timeframes_aligned:
            strength += 1.5
            count += 1
        
        # RSI確認
        if (action == "BUY" and check.rsi_status in ["超賣", "正常"]) or \
           (action == "SELL" and check.rsi_status in ["超買", "正常"]):
            strength += 1.0
            count += 1
        
        # MACD確認
        if (action == "BUY" and check.macd_signal == "BULLISH") or \
           (action == "SELL" and check.macd_signal == "BEARISH"):
            strength += 1.5
            count += 1
        
        # 其他指標可以繼續添加...
        
        return min(strength, 10.0), count
    
    def _assess_technical_status(self, check: TechnicalSignalCheck) -> str:
        """評估技術狀態"""
        if check.signal_strength >= 7.0 and check.signal_count >= 3:
            return "STRONG"
        elif check.signal_strength >= 5.0 and check.signal_count >= 2:
            return "MODERATE"
        elif check.signal_strength >= 3.0:
            return "WEAK"
        else:
            return "INSUFFICIENT"
    
    async def _check_major_news(self, symbol: str) -> Dict:
        """檢查重大新聞"""
        try:
            if self.modules_available:
                from .news_analyzer import CryptoNewsAnalyzer
                analyzer = CryptoNewsAnalyzer()
                news_summary = analyzer.get_quick_summary(symbol)
                
                # 簡單的負面新聞檢測
                negative_keywords = ["crash", "ban", "hack", "scam", "regulation"]
                has_negative = any(keyword in news_summary.lower() for keyword in negative_keywords)
                
                return {"has_major_negative": has_negative, "summary": news_summary}
            else:
                return {"has_major_negative": False, "summary": "新聞分析不可用"}
        except Exception:
            return {"has_major_negative": False, "summary": "無法獲取新聞"}
    
    async def _check_fund_flow(self, symbol: str) -> Dict:
        """檢查資金流動"""
        # 模擬資金流動檢查
        return {"is_normal": True, "net_flow": 1000000}
    
    async def _check_volume(self, symbol: str) -> Dict:
        """檢查交易量"""
        # 模擬交易量檢查
        return {"is_normal": True, "volume_ratio": 1.2}
    
    async def _check_market_depth(self, symbol: str) -> Dict:
        """檢查市場深度"""
        # 模擬市場深度檢查
        return {"sufficient": True, "bid_ask_spread": 0.01}
    
    def _assess_fundamental_status(self, check: FundamentalCheck) -> str:
        """評估基本面狀態"""
        good_count = sum([
            check.no_major_negative,
            check.normal_fund_flow,
            check.normal_volume,
            check.sufficient_depth
        ])
        
        if good_count == 4:
            return "GOOD"
        elif good_count >= 3:
            return "ACCEPTABLE"
        elif good_count >= 2:
            return "CAUTIOUS"
        else:
            return "POOR"
    
    async def _get_account_info(self) -> Dict:
        """獲取帳戶信息"""
        # 模擬帳戶信息
        return {
            "total_balance": 10000.0,
            "available_balance": 9500.0,
            "margin_ratio": 0.0
        }
    
    async def _get_current_price(self, symbol: str) -> float:
        """獲取當前價格"""
        # 模擬當前價格
        if "BTC" in symbol:
            return 50000.0
        elif "ETH" in symbol:
            return 3000.0
        else:
            return 1.0
    
    def _assess_risk_status(self, calc: RiskCalculation) -> str:
        """評估風險狀態"""
        if (calc.risk_reward_ratio >= 2.0 and 
            calc.expected_return >= 0.01 and
            calc.position_size > 0):
            return "ACCEPTABLE"
        elif (calc.risk_reward_ratio >= 1.5 and 
              calc.expected_return >= 0.005):
            return "MODERATE"
        else:
            return "HIGH_RISK"
    
    def _validate_order_parameters(self, params: OrderParameters, risk: RiskCalculation) -> str:
        """驗證訂單參數"""
        if (params.quantity > 0 and
            params.entry_price > 0 and
            params.stop_loss_price > 0 and
            params.leverage <= self.default_risk_params['max_leverage']):
            return "VALID"
        else:
            return "INVALID"
    
    def _assess_final_confirmation(self, check: FinalConfirmation) -> str:
        """評估最終確認狀態"""
        if check.triple_check_passed and check.psychological_state:
            return "APPROVED"
        elif check.signal_reconfirmed and check.risk_acceptable:
            return "CONDITIONAL"
        else:
            return "REJECTED"
    
    def _assess_trade_readiness(self, technical: TechnicalSignalCheck,
                               fundamental: FundamentalCheck,
                               risk: RiskCalculation,
                               order: OrderParameters,
                               final: FinalConfirmation) -> Dict:
        """評估整體交易準備度"""
        
        # 評分系統
        score = 0
        max_score = 5
        
        # 技術分析評分
        if technical.overall_status == "STRONG":
            score += 1
        elif technical.overall_status == "MODERATE":
            score += 0.7
        
        # 基本面評分
        if fundamental.overall_status == "GOOD":
            score += 1
        elif fundamental.overall_status == "ACCEPTABLE":
            score += 0.8
        
        # 風險評分
        if risk.overall_status == "ACCEPTABLE":
            score += 1
        elif risk.overall_status == "MODERATE":
            score += 0.6
        
        # 訂單參數評分
        if order.overall_status == "VALID":
            score += 1
        
        # 最終確認評分
        if final.overall_status == "APPROVED":
            score += 1
        elif final.overall_status == "CONDITIONAL":
            score += 0.5
        
        # 決定最終建議
        score_percentage = (score / max_score) * 100
        
        if score_percentage >= 80:
            status = "EXECUTE"
            recommendation = "✅ 建議執行交易，所有檢查通過"
        elif score_percentage >= 60:
            status = "CAUTIOUS_EXECUTE"
            recommendation = "⚠️ 可謹慎執行，但需密切監控"
        elif score_percentage >= 40:
            status = "WAIT"
            recommendation = "🟡 建議等待更好時機"
        else:
            status = "REJECT"
            recommendation = "❌ 建議暫停交易，風險過高"
        
        return {
            "status": status,
            "recommendation": recommendation,
            "score": score,
            "score_percentage": score_percentage,
            "technical_status": technical.overall_status,
            "fundamental_status": fundamental.overall_status,
            "risk_status": risk.overall_status,
            "order_status": order.overall_status,
            "final_status": final.overall_status,
            "timestamp": datetime.now().isoformat()
        }
    
    def _save_pretrade_results(self, results: Dict):
        """保存交易前檢查結果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_dir / f"pretrade_check_{timestamp}.json"
            
            # 轉換dataclass為字典
            serializable_results = self._convert_to_serializable(results)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"✅ 交易前檢查結果已保存: {filename}")
        except Exception as e:
            logger.error(f"保存結果失敗: {e}")
    
    def _convert_to_serializable(self, obj) -> Any:
        """轉換對象為可序列化格式"""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                result[key] = self._convert_to_serializable(value)
            return result
        elif isinstance(obj, dict):
            return {key: self._convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

# ========== 測試函數 ==========

async def test_pretrade_automation():
    """測試單筆交易前檢查系統"""
    logger.info("🧪 開始測試單筆交易前檢查系統...")
    
    pretrade_system = PreTradeCheckSystem()
    
    # 測試BTC買入信號檢查
    results = await pretrade_system.execute_pretrade_check(
        symbol="BTCUSDT",
        signal_source="AI_FUSION",
        intended_action="BUY"
    )
    
    # 顯示結果摘要
    print("\n" + "="*60)
    print("🎯 單筆交易前檢查結果摘要")
    print("="*60)
    
    assessment = results['overall_assessment']
    print(f"交易對: {results['symbol']}")
    print(f"預期動作: {results['intended_action']}")
    print(f"信號來源: {results['signal_source']}")
    print()
    print(f"技術分析: {assessment['technical_status']}")
    print(f"基本面: {assessment['fundamental_status']}")
    print(f"風險評估: {assessment['risk_status']}")
    print(f"訂單參數: {assessment['order_status']}")
    print(f"最終確認: {assessment['final_status']}")
    print()
    print(f"綜合評分: {assessment['score_percentage']:.1f}%")
    print(f"最終決策: {assessment['status']}")
    print(f"建議: {assessment['recommendation']}")
    print("="*60)
    
    return results

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pretrade_automation())