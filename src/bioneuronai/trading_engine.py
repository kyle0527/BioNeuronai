"""
主要交易系統 - 重構版
整合所有模塊，提供統一的交易接口
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import asdict

# 導入重構後的模塊
from .data_models import MarketData, TradingSignal, Position
from .connectors import BinanceFuturesConnector
from .risk_management import RiskManager
from .trading_strategies import StrategyFusion

logger = logging.getLogger(__name__)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 嘗試導入新聞分析服務
try:
    from .news_analyzer import get_news_analyzer
    NEWS_ANALYZER_AVAILABLE = True
except ImportError:
    NEWS_ANALYZER_AVAILABLE = False
    logger.warning("📰 新聞分析服務未載入")


class TradingEngine:
    """
    交易引擎 - 主要控制器
    
    整合：
    - API 連接器
    - 策略系統
    - 風險管理
    - 新聞分析
    - 數據持久化
    """
    
    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
        strategy_type: str = "fusion",
        use_strategy_fusion: bool = True,  # 向後兼容參數
        risk_config_path: Optional[str] = None
    ):
        # 初始化核心組件
        self.connector = BinanceFuturesConnector(api_key, api_secret, testnet)
        self.risk_manager = RiskManager(risk_config_path)
        
        # 選擇策略（支持舊參數 use_strategy_fusion）
        if use_strategy_fusion or strategy_type == "fusion":
            self.strategy = StrategyFusion()
            logger.info("🧠 使用 AI 策略融合系統")
        else:
            # 可以在這裡添加其他策略
            self.strategy = StrategyFusion()
            logger.warning("使用默認策略融合系統")
        
        # 交易狀態
        self.auto_trade = False
        self.is_monitoring = False
        self.positions: List[Position] = []
        self.signals_history: List[TradingSignal] = []
        
        # 配置參數
        self.max_position_size = 0.01  # 最大倉位
        
        # 數據持久化
        self.data_dir = Path("trading_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 新聞分析服務
        self.news_analyzer = None
        self.enable_news_analysis = True
        if NEWS_ANALYZER_AVAILABLE:
            try:
                from .news_analyzer import get_news_analyzer
                self.news_analyzer = get_news_analyzer()
                logger.info("📰 新聞分析服務已啟用")
            except Exception as e:
                logger.warning(f"📰 新聞分析服務啟動失敗: {e}")
        
        logger.info("✅ 交易引擎初始化完成")
    
    def get_real_time_price(self, symbol: str = "BTCUSDT") -> Optional[MarketData]:
        """獲取實時價格"""
        return self.connector.get_ticker_price(symbol)
    
    def start_monitoring(self, symbol: str = "BTCUSDT"):
        """開始監控市場"""
        if self.is_monitoring:
            logger.warning("已經在監控中")
            return
        
        self.is_monitoring = True
        
        # 顯示交易前新聞分析
        if self.enable_news_analysis and self.news_analyzer:
            self._show_news_analysis(symbol)
        
        # 獲取初始賬戶餘額
        account_info = self.connector.get_account_info()
        if account_info:
            initial_balance = float(account_info.get('totalWalletBalance', 0))
            self.risk_manager.update_balance(initial_balance)
            logger.info(f"💼 初始餘額: ${initial_balance:,.2f}")
        
        def on_ticker_update(data):
            """處理實時價格更新"""
            try:
                if not self.is_monitoring:
                    return
                
                signal = self._process_market_data(data, symbol)
                
                if signal:
                    self._handle_trading_signal(signal)
                    
            except Exception as e:
                logger.error(f"處理市場數據失敗: {e}", exc_info=True)
        
        # 訂閱 WebSocket 流
        logger.info(f"👁️  開始監控 {symbol} 實時價格...")
        self.connector.subscribe_ticker_stream(symbol.lower(), on_ticker_update, auto_reconnect=True)
    
    def _process_market_data(self, data: Dict, symbol: str) -> Optional[TradingSignal]:
        """處理市場數據並生成信號"""
        try:
            # 構建市場數據
            from .trading_strategies import MarketData as StrategyMarketData
            
            current_price = float(data['c'])
            
            # 轉換為策略所需的格式
            market_data = StrategyMarketData(
                symbol=data['s'],
                price=current_price,
                volume=float(data['v']),
                timestamp=datetime.now(),
                high=float(data['h']),
                low=float(data['l']),
                open=float(data['o']),
                close=current_price,
                bid=float(data['b']),
                ask=float(data['a']),
                funding_rate=0.0,
                open_interest=0.0
            )
            
            # 使用策略分析
            signal = None
            if hasattr(self.strategy, 'analyze'):
                signal = self.strategy.analyze(market_data)
            elif hasattr(self.strategy, 'analyze_market'):
                signal = self.strategy.analyze_market(market_data)
            
            if signal and hasattr(signal, 'action'):
                # 轉換為本地信號格式
                local_signal = TradingSignal(
                    action=signal.action,
                    symbol=getattr(signal, 'symbol', symbol),
                    confidence=getattr(signal, 'confidence', 0.5),
                    reason=getattr(signal, 'reason', "策略信號"),
                    target_price=getattr(signal, 'target_price', None),
                    stop_loss=getattr(signal, 'stop_loss', None),
                    take_profit=getattr(signal, 'take_profit', None),
                    timestamp=datetime.now()
                )
                
                self.signals_history.append(local_signal)
                
                # 顯示信號信息
                self._display_signal_info(local_signal, current_price)
                
                return local_signal
            
            return None
            
        except Exception as e:
            logger.error(f"處理市場數據失敗: {e}")
            return None
    
    def _display_signal_info(self, signal: TradingSignal, current_price: float):
        """顯示信號信息"""
        action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}
        emoji = action_emoji.get(signal.action, "⚪")
        
        logger.info(f"{emoji} {signal.symbol}: ${current_price:,.2f} | "
                   f"信號: {signal.action} (置信度: {signal.confidence:.2%})")
        
        # 顯示策略權重信息
        if hasattr(self.strategy, 'weights'):
            weights_str = " | ".join([f"{k.split('_')[0][:3]}:{v:.2f}" 
                                     for k, v in getattr(self.strategy, 'weights', {}).items()])
            logger.info(f"   ⚖️  策略權重: {weights_str}")
        
        logger.info(f"   📝 {signal.reason[:100]}...")
    
    def _handle_trading_signal(self, signal: TradingSignal):
        """處理交易信號"""
        if signal.action == "HOLD":
            return
        
        if not self.auto_trade:
            return
        
        # 風險檢查
        account_info = self.connector.get_account_info()
        if not account_info:
            logger.error("❌ 無法獲取賬戶信息")
            return
        
        account_balance = float(account_info.get('totalWalletBalance', 0))
        
        can_trade, reason = self.risk_manager.check_can_trade(
            signal.confidence, 
            account_balance
        )
        
        if can_trade:
            logger.info("🚀 觸發自動交易信號！")
            self.execute_trade(signal)
        else:
            logger.warning(f"⛔ 風險管理阻止交易: {reason}")
    
    def execute_trade(self, signal: TradingSignal):
        """執行交易"""
        try:
            # 新聞風險檢查
            if self.enable_news_analysis and self.news_analyzer:
                can_trade, reason = self.news_analyzer.should_trade(signal.symbol)
                if not can_trade:
                    logger.warning(f"📰 新聞分析阻止交易: {reason}")
                    return
                logger.info(f"📰 新聞檢查通過: {reason}")
            
            # 獲取賬戶信息
            account_info = self.connector.get_account_info()
            if not account_info:
                logger.error("❌ 無法獲取賬戶信息，取消交易")
                return
            
            account_balance = float(account_info.get('totalWalletBalance', 0))
            
            # 獲取當前價格
            if signal.target_price:
                current_price = signal.target_price
            else:
                price_data = self.get_real_time_price(signal.symbol)
                current_price = price_data.price if price_data else 0.0
            
            if current_price <= 0:
                logger.error("❌ 無法獲取當前價格，取消交易")
                return
            
            # 計算倉位大小
            position_size = self.risk_manager.calculate_position_size(
                account_balance,
                current_price,
                signal.stop_loss
            )
            
            # 限制最大倉位
            position_size = min(position_size, self.max_position_size)
            
            if position_size < 0.001:
                logger.warning(f"⚠️  計算倉位太小 ({position_size:.6f})，調整為最小值 0.001")
                position_size = 0.001
            
            # 顯示交易詳情
            self._display_trade_info(signal, position_size, current_price)
            
            # 執行訂單
            order_result = self.connector.place_order(
                symbol=signal.symbol,
                side="BUY" if signal.action == "BUY" else "SELL",
                order_type="MARKET",
                quantity=position_size,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )
            
            if order_result and order_result.status != "ERROR":
                # 記錄交易
                trade_info = {
                    'symbol': signal.symbol,
                    'side': signal.action,
                    'quantity': position_size,
                    'price': current_price,
                    'confidence': signal.confidence,
                    'strategy': getattr(signal, 'strategy_name', 'Unknown'),
                    'order_id': order_result.order_id
                }
                
                self.risk_manager.record_trade(trade_info)
                self._save_trade_to_file(trade_info)
                
                logger.info(f"✅ 交易成功執行！訂單 ID: {order_result.order_id}")
                
                # 更新策略表現
                if hasattr(self.strategy, 'update_strategy_performance'):
                    logger.info("記錄交易信息供策略評估")
            else:
                logger.error(f"❌ 交易執行失敗: {order_result.error if order_result else '未知錯誤'}")
                
        except Exception as e:
            logger.error(f"❌ 執行交易時發生錯誤: {e}", exc_info=True)
    
    def _display_trade_info(self, signal: TradingSignal, quantity: float, current_price: float):
        """顯示交易詳情"""
        logger.info(f"📊 交易詳情:")
        logger.info(f"   方向: {signal.action}")
        logger.info(f"   數量: {quantity:.6f} {signal.symbol.replace('USDT', '')}")
        logger.info(f"   價值: ${quantity * current_price:,.2f} USDT")
        logger.info(f"   止損: ${signal.stop_loss:,.2f}" if signal.stop_loss else "   止損: 未設置")
        logger.info(f"   止盈: ${signal.take_profit:,.2f}" if signal.take_profit else "   止盈: 未設置")
    
    def _save_trade_to_file(self, trade_info: Dict):
        """保存交易記錄"""
        try:
            trades_file = self.data_dir / "trades_history.jsonl"
            with open(trades_file, 'a', encoding='utf-8') as f:
                json.dump({
                    **trade_info,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False)
                f.write('\\n')
        except Exception as e:
            logger.error(f"保存交易記錄失敗: {e}")
    
    def _show_news_analysis(self, symbol: str):
        """顯示交易前新聞分析"""
        if not self.news_analyzer:
            return
        
        print("\\n" + "=" * 60)
        print("📰 交易前新聞分析（重要！請先閱讀）")
        print("=" * 60)
        
        try:
            summary = self.news_analyzer.get_quick_summary(symbol)
            print(summary)
            
            can_trade, reason = self.news_analyzer.should_trade(symbol)
            
            print()
            if can_trade:
                print(f"✅ 新聞風險評估: 適合交易")
                print(f"   {reason}")
            else:
                print(f"⚠️  新聞風險評估: 建議暫緩")
                print(f"   {reason}")
            
            print("=" * 60 + "\\n")
            
        except Exception as e:
            logger.warning(f"新聞分析顯示失敗: {e}")
    
    def stop_monitoring(self):
        """停止監控"""
        self.is_monitoring = False
        self.connector.close_all_connections()
        logger.info("🛑 停止市場監控")
    
    def get_news_summary(self, symbol: str = "BTCUSDT") -> str:
        """
        獲取新聞分析摘要（可單獨調用）
        
        Args:
            symbol: 交易對
        
        Returns:
            str: 新聞摘要文字
        """
        if not self.news_analyzer:
            return "📰 新聞分析服務未啟用"
        
        try:
            return self.news_analyzer.get_quick_summary(symbol)
        except (AttributeError, ValueError) as e:
            return f"📰 新聞分析失敗: {e}"
    
    def set_news_analysis(self, enabled: bool):
        """啟用或禁用新聞分析"""
        self.enable_news_analysis = enabled
        status = "啟用" if enabled else "禁用"
        logger.info(f"📰 新聞分析已{status}")
    
    def save_signals_history(self, filepath: str = "signals_history.json"):
        """保存信號歷史（向後兼容方法）"""
        self.save_all_data()
    
    def enable_auto_trading(self):
        """啟用自動交易"""
        self.auto_trade = True
        logger.info("🤖 自動交易已啟用")
    
    def disable_auto_trading(self):
        """禁用自動交易"""
        self.auto_trade = False
        logger.info("⏸️  自動交易已禁用")
    
    def get_account_summary(self) -> Dict:
        """獲取賬戶摘要"""
        account_info = self.connector.get_account_info()
        
        if not account_info:
            return {
                "status": "❌ 未連接",
                "balance": 0.0,
                "positions": [],
                "risk_stats": self.risk_manager.get_risk_statistics()
            }
        
        total_balance = float(account_info.get('totalWalletBalance', 0))
        available_balance = float(account_info.get('availableBalance', 0))
        total_unrealized_profit = float(account_info.get('totalUnrealizedProfit', 0))
        
        positions = account_info.get('positions', [])
        active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
        
        return {
            "status": "✅ 已連接",
            "balance": total_balance,
            "available_balance": available_balance,
            "unrealized_pnl": total_unrealized_profit,
            "positions_count": len(active_positions),
            "positions": active_positions,
            "risk_stats": self.risk_manager.get_risk_statistics(),
            "strategy_weights": getattr(self.strategy, 'weights', {})
        }
    
    def get_strategy_report(self) -> Dict:
        """獲取策略報告"""
        if hasattr(self.strategy, 'get_strategy_report'):
            return self.strategy.get_strategy_report()
        return {"message": "當前策略不支持表現報告"}
    
    def save_all_data(self):
        """保存所有數據"""
        try:
            # 保存信號歷史
            history_data = []
            for signal in self.signals_history[-1000:]:
                signal_dict = asdict(signal)
                if 'timestamp' in signal_dict and signal_dict['timestamp']:
                    if isinstance(signal_dict['timestamp'], datetime):
                        signal_dict['timestamp'] = signal_dict['timestamp'].isoformat()
                history_data.append(signal_dict)
            
            signals_path = self.data_dir / "signals_history.json"
            with open(signals_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 信號歷史已保存: {signals_path} ({len(history_data)} 條記錄)")
            
            # 保存策略權重
            if hasattr(self.strategy, 'weights'):
                weights_path = self.data_dir / "strategy_weights.json"
                with open(weights_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'weights': getattr(self.strategy, 'weights', {}),
                        'performance_history': {
                            k: v[-100:] for k, v in getattr(self.strategy, 'performance_history', {}).items()
                        },
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=2, ensure_ascii=False)
                logger.info(f"⚖️  策略權重已保存: {weights_path}")
            
            # 保存風險統計
            risk_stats_path = self.data_dir / "risk_statistics.json"
            with open(risk_stats_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'statistics': self.risk_manager.get_risk_statistics(),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"📈 風險統計已保存: {risk_stats_path}")
            
            # 保存風險配置
            risk_config_path = self.data_dir / "risk_config.json"
            self.risk_manager.save_config(str(risk_config_path))
            
        except Exception as e:
            logger.error(f"保存數據失敗: {e}", exc_info=True)


# 保持向後兼容的別名
CryptoFuturesTrader = TradingEngine