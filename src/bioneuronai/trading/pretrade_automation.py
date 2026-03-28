"""
🎯 SOP 第二步：單筆交易前檢查自動化系統
Per-Trade Pre-Execution Checklist Automation

根據 CRYPTO_TRADING_SOP.md 自動執行 1.2 單筆交易前檢查
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from bioneuronai.trading_strategies import MarketData

# 錯誤常量定義
ERROR_MODULE_UNAVAILABLE = "MODULE_UNAVAILABLE"
ERROR_API_EMPTY_DATA = "API_EMPTY_DATA"

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

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

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: Optional[bool] = None,
    ) -> None:
        # pretrade_automation.py 位於 src/bioneuronai/trading/，4 層 parent = 專案根目錄
        _project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = _project_root / "data" / "bioneuronai" / "trading" / "pretrade"
        self.data_dir.mkdir(exist_ok=True, parents=True)

        # 儲存注入的憑證（None 表示由 _get_connector 自行解析）
        self._api_key = api_key
        self._api_secret = api_secret
        self._testnet = testnet

        # 嘗試導入交易模組
        self._import_modules()

        # 從配置文件載入風險參數
        try:
            from config.trading_config import (
                MAX_RISK_PER_TRADE,
                MIN_RISK_REWARD_RATIO,
                LEVERAGE,
                MIN_EXPECTED_RETURN
            )
            self.default_risk_params = {
                "risk_percentage": MAX_RISK_PER_TRADE,
                "min_risk_reward_ratio": MIN_RISK_REWARD_RATIO,
                "max_leverage": LEVERAGE,
                "min_expected_return": MIN_EXPECTED_RETURN
            }
            logger.info(f"✅ 風險參數已從配置載入: {MAX_RISK_PER_TRADE*100}%")
        except ImportError:
            # Fallback 默認值
            self.default_risk_params = {
                "risk_percentage": 0.02,
                "min_risk_reward_ratio": 1.5,
                "max_leverage": 10,
                "min_expected_return": 0.005
            }
            logger.warning("⚠️ 配置文件不可用，使用默認風險參數")

    def _get_connector(self):
        """取得 BinanceFuturesConnector，憑證優先順序：
        1. 注入值（__init__ 傳入）
        2. 環境變數 BINANCE_API_KEY / BINANCE_API_SECRET / BINANCE_TESTNET
        3. config.trading_config（fallback，僅含 testnet demo key）
        """
        import os
        from ..data.binance_futures import BinanceFuturesConnector

        api_key = self._api_key or os.getenv("BINANCE_API_KEY", "")
        api_secret = self._api_secret or os.getenv("BINANCE_API_SECRET", "")
        if self._testnet is not None:
            testnet = self._testnet
        else:
            env_testnet = os.getenv("BINANCE_TESTNET", "")
            if env_testnet:
                testnet = env_testnet.lower() != "false"
            else:
                testnet = True  # 安全預設：testnet

        # 若注入與環境變數均無設定，嘗試 config fallback（僅 demo key）
        if not api_key or not api_secret:
            try:
                from config.trading_config import (
                    BINANCE_API_KEY as _cfg_key,
                    BINANCE_API_SECRET as _cfg_secret,
                    USE_TESTNET as _cfg_testnet,
                )
                api_key = api_key or _cfg_key
                api_secret = api_secret or _cfg_secret
                if self._testnet is None and not env_testnet:
                    testnet = _cfg_testnet
            except ImportError:
                pass

        return BinanceFuturesConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
        )
    
    def _import_modules(self) -> None:
        """導入所需模組"""
        try:
            from .. import CryptoFuturesTrader, TradingSignal  # noqa: F401
            from ..analysis import CryptoNewsAnalyzer  # noqa: F401
            from ..trading_strategies import StrategyFusion  # noqa: F401
            self.modules_available = True
            logger.info("[OK] 交易模組導入成功")
        except ImportError as e:
            logger.warning(f"[WARN] 部分模組不可用: {e}")
            self.modules_available = False
    
    def execute_pretrade_check(self, symbol: str = "BTCUSDT", 
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
        
        start_time: datetime = datetime.now()
        results = {
            "check_time": start_time,
            "sop_version": "1.0", 
            "sop_step": "1.2 單筆交易前檢查",
            "symbol": symbol,
            "intended_action": intended_action,
            "signal_source": signal_source
        }
        
        # Step 1: 技術信號確認
        logger.info("[INFO] Step 1/5: 技術信號確認")
        technical_check: TechnicalSignalCheck = self._check_technical_signals(symbol, intended_action)
        results["technical_signals"] = technical_check
        
        # Step 2: 基本面檢查
        logger.info("📰 Step 2/5: 基本面檢查")
        fundamental_check: FundamentalCheck = self._check_fundamentals(symbol)
        results["fundamentals"] = fundamental_check
        
        # Step 3: 風險計算
        logger.info("⚖️ Step 3/5: 風險計算")
        risk_calculation: RiskCalculation = self._calculate_risk(symbol, intended_action, technical_check)
        results["risk_calculation"] = risk_calculation
        
        # Step 4: 訂單參數設定
        logger.info("📋 Step 4/5: 訂單參數設定")
        order_params: OrderParameters = self._configure_order_parameters(symbol, intended_action, risk_calculation)
        results["order_parameters"] = order_params
        
        # Step 5: 最終確認
        logger.info("[OK] Step 5/5: 最終確認檢查")
        final_confirmation: FinalConfirmation = self._final_confirmation_check(
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
        
        completion_time: datetime = datetime.now()
        duration: float = (completion_time - start_time).total_seconds()
        
        logger.info(f"[OK] 單筆交易檢查完成 | 耗時: {duration:.1f}秒")
        logger.info(f"🎯 交易建議: {overall_assessment['recommendation']}")
        
        return results
    
    def _check_technical_signals(self, symbol: str, action: str) -> TechnicalSignalCheck:
        """檢查技術信號 (SOP 1.2 第一部分)"""
        check = TechnicalSignalCheck(timestamp=datetime.now())
        
        try:
            logger.info("   📈 分析主要趨勢方向...")
            
            # 模擬獲取市場數據進行技術分析
            market_data = self._get_market_data(symbol)
            
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
                logger.warning("   [WARN] 無法獲取市場數據，使用預設值")
                check.overall_status = "DATA_UNAVAILABLE"
                
        except Exception as e:
            logger.error(f"   [ERROR] 技術信號檢查失敗: {e}")
            check.overall_status = "ERROR"
        
        return check
    
    def _check_fundamentals(self, symbol: str) -> FundamentalCheck:
        """檢查基本面 (SOP 1.2 第二部分)"""
        check = FundamentalCheck(timestamp=datetime.now())
        
        try:
            logger.info("   📰 檢查基本面狀況...")
            
            # 1. 重大消息檢查
            major_news = self._check_major_news(symbol)
            check.no_major_negative = not major_news.get('has_major_negative', False)
            logger.info(f"     ✓ 無重大利空: {'是' if check.no_major_negative else '否'}")
            
            # 2. 資金流動檢查
            fund_flow = self._check_fund_flow(symbol)
            check.normal_fund_flow = fund_flow.get('is_normal', True)
            logger.info(f"     ✓ 資金流動正常: {'是' if check.normal_fund_flow else '否'}")
            
            # 3. 交易量檢查
            volume_data = self._check_volume(symbol)
            check.normal_volume = volume_data.get('is_normal', True)
            logger.info(f"     ✓ 交易量正常: {'是' if check.normal_volume else '否'}")
            
            # 4. 市場深度檢查
            depth_data = self._check_market_depth(symbol)
            check.sufficient_depth = depth_data.get('sufficient', True)
            logger.info(f"     ✓ 市場深度充足: {'是' if check.sufficient_depth else '否'}")
            
            # 綜合評估
            check.overall_status = self._assess_fundamental_status(check)
            
        except Exception as e:
            logger.error(f"   [ERROR] 基本面檢查失敗: {e}")
            check.overall_status = "ERROR"
        
        return check
    
    def _get_default_stop_loss(self, entry_price: float, is_buy: bool) -> float:
        """計算預設止損價格（2%）"""
        if is_buy:
            return entry_price * 0.98
        return entry_price * 1.02
    
    def _get_technical_stop_loss(
        self, technical_check: TechnicalSignalCheck, entry_price: float, is_buy: bool
    ) -> float:
        """從技術位獲取止損價格"""
        if not technical_check.support_resistance:
            return self._get_default_stop_loss(entry_price, is_buy)
        
        key = 'support' if is_buy else 'resistance'
        stop_price = technical_check.support_resistance.get(key, 0)
        
        if stop_price == 0:
            return self._get_default_stop_loss(entry_price, is_buy)
        return float(stop_price)
    
    def _calculate_take_profit(
        self, entry_price: float, price_diff: float, is_buy: bool
    ) -> float:
        """計算止盈價格（2:1 盈虧比）"""
        profit_distance = price_diff * 2
        if is_buy:
            return entry_price + profit_distance
        return entry_price - profit_distance
    
    def _calculate_risk(self, symbol: str, action: str, 
                            technical_check: TechnicalSignalCheck) -> RiskCalculation:
        """風險計算 (SOP 1.2 第三部分 - 1% 規則)"""
        calc = RiskCalculation(timestamp=datetime.now())
        
        try:
            logger.info("   💰 執行風險計算...")
            
            # 1. 獲取帳戶資訊
            account_info = self._get_account_info()
            calc.account_balance = account_info.get('total_balance', 10000.0)  # 預設$10,000
            calc.risk_percentage = self.default_risk_params['risk_percentage']
            calc.max_loss_amount = calc.account_balance * calc.risk_percentage
            
            logger.info(f"     ✓ 帳戶總資金: ${calc.account_balance:.2f}")
            logger.info(f"     ✓ 風險比例: {calc.risk_percentage*100:.1f}%")
            logger.info(f"     ✓ 最大虧損: ${calc.max_loss_amount:.2f}")
            
            # 2. 獲取當前價格
            current_price: float = self._get_current_price(symbol)
            calc.entry_price = current_price or 50000.0  # 預設BTC價格
            
            # 3. 計算止損價格 (基於技術位或固定百分比)
            is_buy = action == "BUY"
            calc.stop_loss_price = self._get_technical_stop_loss(
                technical_check, calc.entry_price, is_buy
            )
            
            # 4. 計算倉位大小 (1% 規則)
            price_diff: float = abs(calc.entry_price - calc.stop_loss_price)
            if price_diff > 0:
                calc.position_size = calc.max_loss_amount / price_diff
            else:
                calc.position_size = 0.001  # 最小倉位
            
            logger.info(f"     ✓ 入場價格: ${calc.entry_price:.2f}")
            logger.info(f"     ✓ 止損價格: ${calc.stop_loss_price:.2f}")
            logger.info(f"     ✓ 倉位大小: {calc.position_size:.6f}")
            
            # 5. 計算止盈目標
            calc.take_profit_price = self._calculate_take_profit(
                calc.entry_price, price_diff, is_buy
            )
            
            # 6. 計算期望回報
            profit_distance = price_diff * 2  # 2:1 盈虧比
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
            logger.error(f"   [ERROR] 風險計算失敗: {e}")
            calc.overall_status = "ERROR"
        
        return calc
    
    def _configure_order_parameters(self, _symbol: str, _action: str,
                                        risk_calc: RiskCalculation) -> OrderParameters:
        """配置訂單參數 (SOP 1.2 第四部分)
        
        Args:
            _symbol: 保留參數，未來可能用於特定交易對的訂單配置
            _action: 保留參數，未來可能用於不同動作的訂單配置
            risk_calc: 風險計算結果
        """
        params = OrderParameters(timestamp=datetime.now())
        
        try:
            logger.info("   📋 設定訂單參數...")
            
            # 1. 入場訂單設定
            params.order_type = "LIMIT"  # 預設限價單
            params.entry_price = risk_calc.entry_price
            params.quantity = risk_calc.position_size
            params.leverage = int(min(5, self.default_risk_params['max_leverage']))  # 保守槓桿
            
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
            logger.error(f"   [ERROR] 訂單參數設定失敗: {e}")
            params.overall_status = "ERROR"
        
        return params
    
    def _final_confirmation_check(self, technical: TechnicalSignalCheck,
                                      fundamental: FundamentalCheck,
                                      risk: RiskCalculation,
                                      order: OrderParameters) -> FinalConfirmation:
        """最終確認檢查 (SOP 1.2 第五部分)"""
        check = FinalConfirmation(timestamp=datetime.now())
        
        try:
            logger.info("   [OK] 執行最終確認...")
            
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
            logger.error(f"   [ERROR] 最終確認檢查失敗: {e}")
            check.overall_status = "ERROR"
        
        return check
    
    # ========== 輔助方法 ==========
    
    def _get_market_data(self, symbol: str) -> Optional[Dict]:
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
        bullish_count: int = sum(1 for trend in timeframes.values() if trend == "BULLISH")
        bearish_count: int = sum(1 for trend in timeframes.values() if trend == "BEARISH")
        
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
        return str(macd_data.get("signal", "NEUTRAL"))
    
    def _analyze_bollinger(self, data: Dict) -> str:
        """分析布林帶位置"""
        bollinger = data.get("bollinger", {})
        return str(bollinger.get("position", "MIDDLE"))
    
    def _calculate_signal_strength(self, check: TechnicalSignalCheck, action: str) -> Tuple[float, int]:
        """計算信號強度"""
        strength = 0.0
        count = 0
        
        # 趨勢確認
        trend_match: bool = (
            (action == "BUY" and "上升" in check.main_trend) or
            (action == "SELL" and "下降" in check.main_trend)
        )
        if trend_match:
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
    
    def _check_major_news(self, symbol: str) -> Dict:
        """檢查重大新聞"""
        try:
            if self.modules_available:
                from ..analysis import CryptoNewsAnalyzer
                analyzer = CryptoNewsAnalyzer()
                news_summary: str = analyzer.get_quick_summary(symbol)
                
                # 簡單的負面新聞檢測
                negative_keywords: List[str] = ["crash", "ban", "hack", "scam", "regulation"]
                has_negative: bool = any(keyword in news_summary.lower() for keyword in negative_keywords)
                
                return {"has_major_negative": has_negative, "summary": news_summary}
            else:
                return {"has_major_negative": False, "summary": "新聞分析不可用"}
        except Exception:
            return {"has_major_negative": False, "summary": "無法獲取新聞"}
    
    def _check_fund_flow(self, symbol: str) -> Dict:
        """檢查資金流動 - 使用 Open Interest 作為市場資金流動指標"""
        if not self.modules_available:
            logger.warning("交易模組不可用，無法檢查資金流動")
            return {"is_normal": False, "error": ERROR_MODULE_UNAVAILABLE, "net_flow": 0}
        
        try:
            connector = self._get_connector()

            # 獲取 Open Interest（未平倉合約量）
            oi_data = connector.get_open_interest(symbol)
            if oi_data:
                open_interest = float(oi_data.get('openInterest', 0))
                logger.info(f"📊 {symbol} Open Interest: {open_interest:,.2f}")
                # Open Interest > 10000 視為正常流動性
                is_normal: bool = open_interest > 10000
                return {"is_normal": is_normal, "net_flow": open_interest}
            else:
                logger.warning(f"無法獲取 {symbol} Open Interest 數據")
                return {"is_normal": False, "error": ERROR_API_EMPTY_DATA, "net_flow": 0}
                
        except Exception as e:
            logger.error(f"檢查資金流動失敗: {e}")
            return {"is_normal": False, "error": str(e), "net_flow": 0}
    
    def _check_volume(self, symbol: str) -> Dict:
        """檢查交易量 - 從真實 API 獲取 24h 交易量數據"""
        if not self.modules_available:
            logger.warning("交易模組不可用，無法檢查交易量")
            return {"is_normal": False, "error": "模組不可用", "volume_ratio": 0}
        
        try:
            connector = self._get_connector()

            # 獲取 24h 行情統計
            ticker_24h = connector.get_ticker_24hr(symbol)
            if ticker_24h:
                volume = float(ticker_24h.get('volume', 0))
                quote_volume = float(ticker_24h.get('quoteVolume', 0))
                price_change_pct = float(ticker_24h.get('priceChangePercent', 0))
                
                logger.info(f"📊 {symbol} 24h 交易量: {volume:,.2f} | 成交額: ${quote_volume:,.0f}")
                
                # 交易量超過 1000 BTC 等值視為正常
                # 價格波動在 -20% ~ +20% 視為正常
                is_normal: bool = quote_volume > 1_000_000 and -20 < price_change_pct < 20
                volume_ratio: float | int = quote_volume / 1_000_000 if quote_volume > 0 else 0
                
                return {
                    "is_normal": is_normal,
                    "volume_ratio": round(volume_ratio, 2),
                    "volume": volume,
                    "quote_volume": quote_volume,
                    "price_change_pct": price_change_pct
                }
            else:
                logger.warning(f"無法獲取 {symbol} 24h 數據")
                return {"is_normal": False, "error": "API 回傳空數據", "volume_ratio": 0}
                
        except Exception as e:
            logger.error(f"檢查交易量失敗: {e}")
            return {"is_normal": False, "error": str(e), "volume_ratio": 0}
    
    def _check_market_depth(self, symbol: str) -> Dict:
        """檢查市場深度 - 從真實 API 獲取訂單簿數據"""
        if not self.modules_available:
            logger.warning("交易模組不可用，無法檢查市場深度")
            return {"sufficient": False, "error": "模組不可用", "bid_ask_spread": 999}
        
        try:
            connector = self._get_connector()

            # 獲取訂單簿深度（前 20 檔）
            depth_data = connector.get_order_book(symbol, limit=20)
            if depth_data and 'bids' in depth_data and 'asks' in depth_data:
                bids = depth_data['bids']
                asks = depth_data['asks']
                
                if bids and asks:
                    # 計算買賣價差
                    best_bid = float(bids[0][0])
                    best_ask = float(asks[0][0])
                    mid_price: float = (best_bid + best_ask) / 2
                    spread: float = (best_ask - best_bid) / mid_price * 100  # 百分比
                    
                    # 計算深度（前 10 檔總量）
                    bid_depth: float | int = sum(float(b[1]) for b in bids[:10])
                    ask_depth: float | int = sum(float(a[1]) for a in asks[:10])
                    total_depth: float | int = bid_depth + ask_depth
                    
                    logger.info(f"📊 {symbol} 價差: {spread:.4f}% | 深度: {total_depth:,.2f}")
                    
                    # 價差 < 0.1% 且深度 > 100 視為足夠
                    sufficient: bool = spread < 0.1 and total_depth > 100
                    
                    return {
                        "sufficient": sufficient,
                        "bid_ask_spread": round(spread, 4),
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "bid_depth": bid_depth,
                        "ask_depth": ask_depth,
                        "total_depth": total_depth
                    }
                else:
                    logger.warning(f"{symbol} 訂單簿為空")
                    return {"sufficient": False, "error": "訂單簿為空", "bid_ask_spread": 999}
            else:
                logger.warning(f"無法獲取 {symbol} 訂單簿數據")
                return {"sufficient": False, "error": "API 回傳空數據", "bid_ask_spread": 999}
                
        except Exception as e:
            logger.error(f"檢查市場深度失敗: {e}")
            return {"sufficient": False, "error": str(e), "bid_ask_spread": 999}
    
    def _assess_fundamental_status(self, check: FundamentalCheck) -> str:
        """評估基本面狀態"""
        good_count: int = sum([
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
    
    def _get_account_info(self) -> Dict:
        """獲取帳戶信息 - 從真實 API 獲取，需要有效的 API Key"""
        if not self.modules_available:
            raise RuntimeError("交易模組不可用，無法獲取帳戶信息")
        
        try:
            connector = self._get_connector()

            # 嘗試獲取帳戶信息（需要有效 API Key）
            account_data = connector.get_account_info()
            
            if account_data:
                total_balance = float(account_data.get('totalWalletBalance', 0))
                available_balance = float(account_data.get('availableBalance', 0))
                margin_ratio = float(account_data.get('totalMarginBalance', 0))
                
                logger.info(f"💰 帳戶餘額: ${total_balance:,.2f} | 可用: ${available_balance:,.2f}")
                
                return {
                    "total_balance": total_balance,
                    "available_balance": available_balance,
                    "margin_ratio": margin_ratio
                }
            else:
                # API 返回空 = 認證失敗或網路問題
                raise RuntimeError(
                    "無法獲取帳戶資訊。請檢查:\n"
                    "1. API Key 是否有效（可能已過期）\n"
                    "2. API Key 是否有 Futures 權限\n"
                    "3. 是否使用正確的 Testnet/Mainnet 配置"
                )
                
        except ImportError as e:
            raise RuntimeError(f"無法導入配置: {e}")
        except Exception as e:
            raise RuntimeError(f"獲取帳戶信息失敗: {e}")
    
    def _get_current_price(self, symbol: str) -> float:
        """獲取當前價格 - 從真實 API 獲取"""
        if not self.modules_available:
            raise RuntimeError("交易模組不可用，無法獲取市場價格")
        
        try:
            connector = self._get_connector()

            # 獲取真實價格 (返回 MarketData 物件)
            market_data: MarketData | None = connector.get_ticker_price(symbol)
            if market_data is None or market_data.price <= 0:
                raise ValueError(f"無效的價格數據: {market_data}")
            
            logger.info(f"📊 {symbol} 當前價格: ${market_data.price:,.2f}")
            return float(market_data.price)
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 價格失敗: {e}")
            raise RuntimeError(f"無法獲取市場價格: {e}")
    
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
    
    def _validate_order_parameters(self, params: OrderParameters, _risk: RiskCalculation) -> str:
        """驗證訂單參數
        
        Args:
            params: 訂單參數
            _risk: 風險計算結果（保留以保持接口一致性）
        """
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
        score = 0.0
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
        score_percentage: float = (score / max_score) * 100
        
        if score_percentage >= 80:
            status = "EXECUTE"
            recommendation = "[OK] 建議執行交易，所有檢查通過"
        elif score_percentage >= 60:
            status = "CAUTIOUS_EXECUTE"
            recommendation = "[WARN] 可謹慎執行，但需密切監控"
        elif score_percentage >= 40:
            status = "WAIT"
            recommendation = "🟡 建議等待更好時機"
        else:
            status = "REJECT"
            recommendation = "[STOP] 建議暫停交易，風險過高"
        
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
    
    def _save_pretrade_results(self, results: Dict) -> None:
        """保存交易前檢查結果"""
        try:
            timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename: Path = self.data_dir / f"pretrade_check_{timestamp}.json"
            
            # 轉換dataclass為字典
            serializable_results = self._convert_to_serializable(results)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"[OK] 交易前檢查結果已保存: {filename}")
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
