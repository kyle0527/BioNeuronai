"""
 - 

"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

import numpy as np

from bioneuronai.analysis.news import CryptoNewsAnalyzer
from bioneuronai.analysis.feature_engineering import MarketMicrostructure
from bioneuronai.analysis.market_regime import RegimeAnalysis

# AI 引擎相關導入 - 使用別名避免衝突
from bioneuronai.core.inference_engine import TradingSignal as AITradingSignal
from bioneuronai.core.inference_engine import SignalType
from bioneuronai.data.binance_futures import OrderResult
from bioneuronai.analysis.news import NewsAnalysisResult
from schemas.enums import SignalType as TradeSignalType  # 交易信號的 BUY/SELL/HOLD 枚舉
from schemas.market import MarketData
from schemas.trading import TradingSignal

from ..data import BinanceFuturesConnector
from ..data.database_manager import get_database_manager, DatabaseManager
from ..trading.risk_manager import RiskManager

try:
    from ..strategies.selector import StrategySelector
    STRATEGY_SELECTOR_AVAILABLE = True
except ImportError:
    StrategySelector = None  # type: ignore[assignment,misc]
    STRATEGY_SELECTOR_AVAILABLE = False

# 位置數據模型（創建缺失的 Position 類別）
@dataclass
class Position:
    """交易位置數據模型"""
    symbol: str
    side: str  # LONG/SHORT
    size: float
    entry_price: float
    mark_price: float
    pnl: float
    timestamp: datetime

logger: logging.Logger = logging.getLogger(__name__)

# trading_engine 不直接配置 root logger 或建立 FileHandler
# 日誌配置由 CLI 入口 (cli/main.py) 統一管理

# 
try:
    from ..analysis import get_news_analyzer  # noqa: F401
    NEWS_ANALYZER_AVAILABLE = True
except ImportError:
    NEWS_ANALYZER_AVAILABLE = False
    logger.warning(" ")

#  RAG 模組 - 使用 PreTradeCheckSystem 替代
try:
    from ..trading.pretrade_automation import PreTradeCheckSystem
    RAG_NEWS_CHECKER_AVAILABLE = True
    PreTradeNewsChecker = PreTradeCheckSystem  # 別名兼容
except ImportError:
    RAG_NEWS_CHECKER_AVAILABLE = False
    PreTradeNewsChecker = None  # type: ignore
    PreTradeCheckSystem = None  # type: ignore
    logger.warning("RAG 新聞檢查模組不可用")

#  AI 
try:
    from .inference_engine import (
        InferenceEngine, 
        TradingSignal as AITradingSignal,
        SignalType  # noqa: F401
    )
    INFERENCE_ENGINE_AVAILABLE = True
except ImportError:
    INFERENCE_ENGINE_AVAILABLE = False
    logger.warning("[AI] AI Inference Engine not loaded")

# 
try:
    from ..analysis import (
        MarketDataProcessor,  # noqa: F401
        MarketRegimeDetector,  # noqa: F401
        VolumeProfileCalculator,  # noqa: F401
        LiquidationHeatmapCalculator  # noqa: F401
    )
    FEATURE_MODULES_AVAILABLE = True
except ImportError:
    FEATURE_MODULES_AVAILABLE = False
    logger.warning(" ")


class TradingEngine:
    """
     - 
    
    
    - API 
    - 
    - 
    - 
    - AI 
    - 
    """
    
    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
        strategy_type: str = "fusion",
        use_strategy_fusion: bool = True,  # 
        risk_config_path: Optional[str] = None,
        enable_ai_model: bool = True,       #  AI 
        ai_min_confidence: float = 0.5      # AI 
    ) -> None:
        # 
        self.connector = BinanceFuturesConnector(api_key, api_secret, testnet)
        self.risk_manager = RiskManager()  # RiskManager不需要參數
        
        # 正式策略主線：StrategySelector + AIStrategyFusion
        if not STRATEGY_SELECTOR_AVAILABLE or StrategySelector is None:
            raise ImportError("StrategySelector 不可用，無法初始化正式策略主線")

        self.strategy = StrategySelector(
            timeframe="1m",
            enable_ai_fusion=use_strategy_fusion or strategy_type == "fusion",
        )
        logger.info(
            "✅ 使用新策略主線: StrategySelector%s",
            " + AI Fusion" if getattr(self.strategy, "ai_fusion_available", False) else "",
        )
        
        # 
        self.auto_trade = False
        self.is_monitoring = False
        self.positions: List[Position] = []
        self.signals_history: List[TradingSignal] = []
        
        # 持倉數據與歷史
        self.max_position_size = 0.01  # 最大持倉大小
        
        # 數據存儲目錄與數據庫 — 以本檔案位置為錨點，確保 Docker 路徑正確
        # trading_engine.py 位於 src/bioneuronai/core/，4 層 parent = 專案根目錄
        _project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = _project_root / "data" / "bioneuronai" / "trading" / "engine"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化數據庫管理器
        self.db_manager: DatabaseManager = get_database_manager(
            db_path=str(self.data_dir / "trading.db")
        )
        logger.info("✅ 數據庫管理器已初始化")
        
        # ========== AI 模型引擎 ==========
        self.inference_engine: Optional["InferenceEngine"] = None
        self.enable_ai_model: bool = enable_ai_model
        self.ai_min_confidence: float = ai_min_confidence
        self.ai_model_loaded = False
        
        if enable_ai_model and INFERENCE_ENGINE_AVAILABLE:
            try:
                from .inference_engine import InferenceEngine
                self.inference_engine = InferenceEngine(
                    min_confidence=ai_min_confidence,
                    warmup=False  # 
                )
                logger.info("[AI] AI Inference Engine initialized (model pending load)")
            except Exception as e:
                logger.warning(f"[AI] AI Inference Engine initialization failed: {e}")
        
        # ==========  ==========
        self.market_data_processor = None
        self.regime_detector = None
        self.volume_profile_calculator = None
        self.liquidation_calculator = None
        
        if FEATURE_MODULES_AVAILABLE:
            try:
                from ..analysis import (
                    MarketDataProcessor,
                    MarketRegimeDetector,
                    VolumeProfileCalculator,
                    LiquidationHeatmapCalculator
                )
                self.market_data_processor = MarketDataProcessor()
                self.regime_detector = MarketRegimeDetector()
                self.volume_profile_calculator = VolumeProfileCalculator()
                self.liquidation_calculator = LiquidationHeatmapCalculator()
                logger.info(" ")
            except Exception as e:
                logger.warning(f" : {e}")
        
        # K
        self._klines_cache: Dict[str, List[Dict]] = {}
        self._klines_last_update: Dict[str, float] = {}
        
        # 
        self.news_analyzer: Optional[CryptoNewsAnalyzer] = None
        self.enable_news_analysis = True
        if NEWS_ANALYZER_AVAILABLE:
            try:
                from ..analysis import get_news_analyzer
                self.news_analyzer = get_news_analyzer()
                logger.info(" ")
            except Exception as e:
                logger.warning(f" : {e}")
        
        # RAG 交易前檢查系統
        self.news_checker = None
        self.enable_rag_news_check = True  # 
        if RAG_NEWS_CHECKER_AVAILABLE and PreTradeCheckSystem is not None:
            try:
                self.news_checker = PreTradeCheckSystem()
                logger.info("✅ 交易前檢查系統已初始化")
            except Exception as e:
                logger.warning(f"交易前檢查系統初始化失敗: {e}")
        
        logger.info(" ")
    
    # ========== AI  ==========
    
    def load_ai_model(self, model_name: str = "my_100m_model", warmup: bool = True) -> bool:
        """ AI 
        
        Args:
            model_name: 
            warmup: 
        """
        if not self.inference_engine:
            logger.error(" AI ")
            return False
        
        try:
            logger.info(f"[AI] Loading AI model: {model_name}...")
            self.inference_engine.load_model(model_name)
            
            if warmup:
                logger.info(" ...")
                self.inference_engine.model_loader.warmup()
            
            self.ai_model_loaded = True
            logger.info(" AI ")
            return True
            
        except FileNotFoundError:
            logger.error(f" : model/{model_name}.pth")
            return False
        except Exception as e:
            logger.error(f" AI : {e}")
            return False
    
    def get_ai_prediction(self, symbol: str) -> Optional["AITradingSignal"]:
        """ AI 獲取交易信號 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離數據收集和處理
        
        Args:
            symbol: 交易對符號，必填參數以支持任意幣種
            
        Returns:
            AI 交易信號或 None
        """
        if not self.ai_model_loaded or not self.inference_engine:
            return None
        
        try:
            # 獲取 K 線數據
            klines = self._get_klines(symbol)
            if not klines or len(klines) < 50:
                logger.warning(f"K: {len(klines) if klines else 0} ")
                return None
            
            current_price = float(klines[-1].get('close', klines[-1].get('c', 0)))
            
            # 收集輔助數據 (Extract Method)
            microstructure: Optional[MarketMicrostructure] = self._collect_market_microstructure(symbol, current_price)
            regime_analysis: Optional[RegimeAnalysis] = self._collect_regime_analysis(symbol, klines)
            
            # 調用 AI 引擎預測
            ai_signal: AITradingSignal = self.inference_engine.predict(
                symbol=symbol,
                current_price=current_price,
                klines=klines,
                microstructure=microstructure,
                volume_profile=None,
                liquidation_heatmap=None,
                regime_analysis=regime_analysis
            )
            
            return ai_signal
            
        except Exception as e:
            logger.error(f"AI : {e}")
            return None
    
    def _collect_market_microstructure(
        self, 
        symbol: str, 
        current_price: float
    ) -> Optional[MarketMicrostructure]:
        """收集市場微觀結構數據"""
        if not self.market_data_processor:
            return None
        
        try:
            order_book = self.connector.get_order_book(symbol, limit=20)
            funding_data = self.connector.get_funding_rate(symbol)
            oi_data = self.connector.get_open_interest(symbol)
            
            return self.market_data_processor.build_market_microstructure(
                symbol=symbol,
                current_price=current_price,
                order_book=order_book,
                funding_data=funding_data,
                oi_data=oi_data
            )
        except Exception as e:
            logger.debug(f": {e}")
            return None
    
    def _collect_regime_analysis(self, symbol: str, klines: List) -> Optional[RegimeAnalysis]:
        """收集市場環境分析"""
        if not self.regime_detector:
            return None
        
        try:
            # 提取 OHLCV 數據
            closes: List[float] = [float(k.get('close', k.get('c', 0))) for k in klines]
            highs: List[float] = [float(k.get('high', k.get('h', 0))) for k in klines]
            lows: List[float] = [float(k.get('low', k.get('l', 0))) for k in klines]
            volumes: List[float] = [float(k.get('volume', k.get('v', 0))) for k in klines]
            
            # 批量更新歷史數據（避免逐筆迴圈）
            self.regime_detector.bulk_update_data(
                symbol=symbol,
                prices=closes,
                highs=highs,
                lows=lows,
                volumes=volumes
            )
            
            return self.regime_detector.detect_regime(symbol=symbol)
        except Exception as e:
            logger.debug(f": {e}")
            return None
    
    def _get_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List:
        """獲取 K 線數據（Binance 返回 List[List] 格式）"""
        cache_key: str = f"{symbol}_{interval}"
        current_time: float = time.time()
        
        #  (30)
        if (cache_key in self._klines_cache and 
            current_time - self._klines_last_update.get(cache_key, 0) < 30):
            return self._klines_cache[cache_key]
        
        try:
            klines = self.connector.get_klines(symbol, interval, limit)
            if klines:
                # 將 Binance 返回的 List[List] 轉換為 List[Dict] 以便使用
                klines_dict = self._convert_klines_to_dict(klines)
                self._klines_cache[cache_key] = klines_dict
                self._klines_last_update[cache_key] = current_time
                return klines_dict
            return []
        except Exception as e:
            logger.error(f" K : {e}")
            return self._klines_cache.get(cache_key, [])
    
    def _convert_klines_to_dict(self, klines: List[List]) -> List[Dict]:
        """將 Binance K 線數據從 List[List] 轉換為 List[Dict]"""
        result = []
        for k in klines:
            if len(k) >= 6:
                result.append({
                    'open_time': k[0],
                    'open': k[1],
                    'high': k[2],
                    'low': k[3],
                    'close': k[4],
                    'volume': k[5],
                    'close_time': k[6] if len(k) > 6 else None,
                    'o': k[1],  # 別名
                    'h': k[2],
                    'l': k[3],
                    'c': k[4],
                    'v': k[5]
                })
        return result
    
    def toggle_ai_model(self) -> None:
        """ AI """
        self.enable_ai_model = not self.enable_ai_model
        status: str = "[GREEN] " if self.enable_ai_model else " "
        logger.info(f"[AI] AI : {status}")
    
    def get_ai_status(self) -> Dict:
        """ AI """
        status = {
            "enabled": self.enable_ai_model,
            "engine_initialized": self.inference_engine is not None,
            "model_loaded": self.ai_model_loaded,
            "min_confidence": self.ai_min_confidence,
        }
        
        if self.inference_engine and self.ai_model_loaded:
            status.update(self.inference_engine.get_stats())
        
        return status
    
    def get_real_time_price(self, symbol: str) -> Optional[MarketData]:
        """獲取實時價格數據
        
        Args:
            symbol: 交易對符號 (例: BTCUSDT, ETHUSDT)
        
        Returns:
            市場數據或 None
        """
        return self.connector.get_ticker_price(symbol)
    
    def start_monitoring(self, symbol: str) -> None:
        """開始監控指定交易對
        
        Args:
            symbol: 交易對符號 (例: BTCUSDT, ETHUSDT, SOLUSDT)
        """
        if self.is_monitoring:
            logger.warning("已在監控中，請先停止現有監控")
            return
        
        self.is_monitoring = True
        
        # RAG 
        if self.enable_rag_news_check and self.news_checker:
            self._check_breaking_news_before_start(symbol)
        
        # 
        if self.enable_news_analysis and self.news_analyzer:
            self._show_news_analysis(symbol)
        
        # 
        account_info = self.connector.get_account_info()
        if account_info:
            initial_balance = float(account_info.get('totalWalletBalance', 0))
            self.risk_manager.update_balance(initial_balance)
            logger.info(f" : ${initial_balance:,.2f}")
        
        def on_ticker_update(data) -> None:
            """"""
            try:
                if not self.is_monitoring:
                    return
                
                signal: Optional[TradingSignal] = self._process_market_data(data, symbol)
                
                if signal:
                    self._handle_trading_signal(signal)
                    
            except Exception as e:
                logger.error(f": {e}", exc_info=True)
        
        #  WebSocket 
        logger.info(f"   {symbol} ...")
        self.connector.subscribe_ticker_stream(symbol.lower(), on_ticker_update, auto_reconnect=True)
    
    def _process_market_data(self, data: Dict, symbol: str) -> Optional[TradingSignal]:
        """"""
        try:
            current_price = float(data['c'])
            klines = self._get_klines(symbol, interval="1m", limit=200)
            if not klines or len(klines) < 20:
                return None

            final_signal = self.generate_trading_signal(
                symbol=symbol,
                current_price=current_price,
                klines=klines,
                display_ai=True,
            )
            
            if final_signal:
                self.signals_history.append(final_signal)
                self._display_signal_info(final_signal, current_price)
                return final_signal
            
            return None
            
        except Exception as e:
            logger.error(f": {e}")
            return None

    def generate_trading_signal(
        self,
        symbol: str,
        current_price: float,
        klines: List[Dict[str, Any]],
        event_score: float = 0.0,
        event_context: Optional[Any] = None,
        display_ai: bool = False,
    ) -> Optional[TradingSignal]:
        """
        產生正式交易信號。

        統一 live / replay 使用同一條策略主線：
        1. StrategySelector / AI Fusion 產生策略信號
        2. 可用時再融合 AI inference signal
        """
        strategy_signal = self._generate_strategy_signal(
            symbol=symbol,
            current_price=current_price,
            klines=klines,
            event_score=event_score,
            event_context=event_context,
        )

        ai_signal: Optional[AITradingSignal] = None
        if self.enable_ai_model and self.ai_model_loaded and self.inference_engine:
            try:
                ai_signal = self.inference_engine.predict(
                    symbol=symbol,
                    current_price=current_price,
                    klines=klines,
                )
                if ai_signal and display_ai:
                    self._display_ai_signal(ai_signal, current_price)
            except Exception as e:
                logger.warning(f"AI 信號生成失敗: {e}")

        return self._fuse_signals(strategy_signal, ai_signal, symbol, current_price)

    def _generate_strategy_signal(
        self,
        symbol: str,
        current_price: float,
        klines: List[Dict[str, Any]],
        event_score: float = 0.0,
        event_context: Optional[Any] = None,
    ) -> Optional[TradingSignal]:
        """使用新策略主線生成可執行的 TradingSignal。"""
        ohlcv_data = self._convert_klines_to_ohlcv(klines)
        if ohlcv_data.size == 0 or len(ohlcv_data) < 20:
            return None

        payload = self.strategy.get_actionable_signal(  # type: ignore[union-attr]
            ohlcv_data=ohlcv_data,
            symbol=symbol,
            event_score=event_score,
            event_context=event_context,
        )
        if not payload or not payload.get("should_trade"):
            return None

        direction = str(payload.get("direction", "")).lower()
        signal_type = self._direction_to_signal_type(direction)
        if signal_type is None:
            return None

        entry_price = payload.get("entry_price") or current_price
        take_profit = payload.get("take_profit")
        stop_loss = payload.get("stop_loss")

        target_price = None
        if take_profit and self._is_valid_target_price(signal_type, float(entry_price), float(take_profit)):
            target_price = float(take_profit)

        stop_loss_value = None
        if stop_loss and self._is_valid_stop_loss(signal_type, float(entry_price), float(stop_loss)):
            stop_loss_value = float(stop_loss)

        confidence = float(payload.get("confidence") or payload.get("setup_confidence") or 0.5)

        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=max(0.0, min(1.0, confidence)),
            entry_price=float(entry_price),
            target_price=target_price,
            stop_loss=stop_loss_value,
            take_profit=float(take_profit) if take_profit else None,
            position_size=None,
            strategy_name=str(payload.get("strategy_name", "strategy_selector")),
            reason=(
                f"新策略主線: {payload.get('strategy_name', 'strategy_selector')} | "
                f"{payload.get('fusion_method', 'selector')}"
            ),
            metadata={
                "source": "strategy_selector",
                "direction": direction,
                "contributing_strategies": payload.get("contributing_strategies", []),
                "consensus_strength": payload.get("consensus_strength"),
            },
            timestamp=datetime.now(),
        )

    def _convert_klines_to_ohlcv(self, klines: List[Dict[str, Any]]) -> np.ndarray:
        """將 K 線 dict 列表轉為 selector 需要的 OHLCV numpy array。"""
        rows = []
        for kline in klines:
            try:
                rows.append([
                    float(kline.get("open_time", 0)),
                    float(kline.get("open", kline.get("o", 0))),
                    float(kline.get("high", kline.get("h", 0))),
                    float(kline.get("low", kline.get("l", 0))),
                    float(kline.get("close", kline.get("c", 0))),
                    float(kline.get("volume", kline.get("v", 0))),
                ])
            except (TypeError, ValueError):
                continue

        if not rows:
            return np.empty((0, 6))
        return np.array(rows, dtype=float)

    def _direction_to_signal_type(self, direction: str) -> Optional[TradeSignalType]:
        """將策略方向轉為統一 SignalType。"""
        mapping = {
            "long": TradeSignalType.BUY,
            "short": TradeSignalType.SELL,
            "buy": TradeSignalType.BUY,
            "sell": TradeSignalType.SELL,
        }
        return mapping.get(direction)

    def _is_valid_stop_loss(
        self,
        signal_type: TradeSignalType,
        entry_price: float,
        stop_loss: float,
    ) -> bool:
        """驗證止損與方向一致。"""
        if signal_type == TradeSignalType.BUY:
            return stop_loss < entry_price
        if signal_type == TradeSignalType.SELL:
            return stop_loss > entry_price
        return False

    def _is_valid_target_price(
        self,
        signal_type: TradeSignalType,
        entry_price: float,
        target_price: float,
    ) -> bool:
        """驗證目標價與方向一致。"""
        if signal_type == TradeSignalType.BUY:
            return target_price > entry_price
        if signal_type == TradeSignalType.SELL:
            return target_price < entry_price
        return False
    
    def _fuse_signals(
        self, 
        strategy_signal, 
        ai_signal: Optional["AITradingSignal"],
        symbol: str,
        current_price: float
    ) -> Optional[TradingSignal]:
        """ AI  - 重構降低複雜度
        
        複雜度降低策略：Early Return + Extract Method
        
        :
        1. 
        2. 
        3. 
        """
        # Early Return: 僅有 AI 信號
        if ai_signal and not strategy_signal:
            return self._convert_ai_signal_to_trading_signal(ai_signal, symbol, current_price)
        
        # Early Return: 僅有策略信號
        if strategy_signal and not ai_signal:
            return self._create_strategy_only_signal(strategy_signal, symbol)
        
        # 雙信號融合
        if ai_signal and strategy_signal and hasattr(strategy_signal, 'action'):
            return self._fuse_both_signals(ai_signal, strategy_signal, symbol, current_price)
        
        return None
    
    def _create_strategy_only_signal(
        self, 
        strategy_signal, 
        symbol: str
    ) -> Optional[TradingSignal]:
        """創建僅含策略信號的交易信號"""
        if isinstance(strategy_signal, TradingSignal):
            return strategy_signal

        if not hasattr(strategy_signal, 'signal_type'):
            return None
        
        return TradingSignal(
            signal_type=strategy_signal.signal_type,
            symbol=getattr(strategy_signal, 'symbol', symbol),
            confidence=getattr(strategy_signal, 'confidence', 0.5),
            entry_price=getattr(strategy_signal, 'entry_price', getattr(strategy_signal, 'target_price', None)),
            strategy_name=getattr(strategy_signal, 'strategy_name', 'strategy_fusion'),
            reason=getattr(strategy_signal, 'reason', ""),
            target_price=getattr(strategy_signal, 'target_price', None),
            stop_loss=getattr(strategy_signal, 'stop_loss', None),
            take_profit=getattr(strategy_signal, 'take_profit', None),
            position_size=getattr(strategy_signal, 'position_size', None),
            indicators=getattr(strategy_signal, 'indicators', None),
            metadata=getattr(strategy_signal, 'metadata', None),
            timestamp=datetime.now()
        )
    
    def _fuse_both_signals(
        self,
        ai_signal: "AITradingSignal",
        strategy_signal,
        symbol: str,
        current_price: float
    ) -> Optional[TradingSignal]:
        """融合 AI 和策略信號"""
        ai_action: str = self._get_ai_action(ai_signal)
        strategy_action = strategy_signal.action
        
        # 一致性信號 → 增強置信度
        if ai_action == strategy_action and ai_action != "HOLD":
            return self._create_enhanced_signal(
                ai_signal, strategy_signal, symbol, current_price, ai_action
            )
        
        # 不一致 → 選擇置信度較高者
        return self._resolve_conflicting_signals(
            ai_signal, strategy_signal, symbol, current_price, ai_action, strategy_action
        )
    
    def _create_enhanced_signal(
        self,
        ai_signal: "AITradingSignal",
        strategy_signal,
        symbol: str,
        current_price: float,
        action: str
    ) -> TradingSignal:
        """創建增強的融合信號"""
        enhanced_confidence: float = min(
            0.95,
            (ai_signal.confidence + getattr(strategy_signal, 'confidence', 0.5)) / 2 + 0.1
        )
        
        return TradingSignal(
            symbol=symbol,
            signal_type=TradeSignalType(action.lower()),
            confidence=enhanced_confidence,
            entry_price=current_price,
            strategy_name='ai_strategy_fusion',
            reason=f"AI+ | AI: {ai_signal.reasoning}",
            target_price=(
                ai_signal.suggested_take_profit
                if ai_signal.suggested_take_profit > 0 and
                self._is_valid_target_price(TradeSignalType(action.lower()), current_price, ai_signal.suggested_take_profit)
                else getattr(strategy_signal, 'target_price', None)
            ),
            stop_loss=ai_signal.suggested_stop_loss if ai_signal.suggested_stop_loss > 0 
                      else getattr(strategy_signal, 'stop_loss', None),
            take_profit=ai_signal.suggested_take_profit if ai_signal.suggested_take_profit > 0 
                        else getattr(strategy_signal, 'take_profit', None),
            position_size=ai_signal.suggested_position_size or getattr(strategy_signal, 'position_size', None),
            indicators=getattr(strategy_signal, 'indicators', None),
            metadata={"source": "ai_strategy_fusion"},
            timestamp=datetime.now()
        )
    
    def _resolve_conflicting_signals(
        self,
        ai_signal: "AITradingSignal",
        strategy_signal,
        symbol: str,
        current_price: float,
        ai_action: str,
        strategy_action: str
    ) -> Optional[TradingSignal]:
        """解決衝突信號 (選擇置信度較高者)"""
        ai_conf: float = ai_signal.confidence
        strat_conf: Any = getattr(strategy_signal, 'confidence', 0.5)
        
        # AI 置信度更高
        if ai_conf > strat_conf and ai_action != "HOLD":
            return self._convert_ai_signal_to_trading_signal(ai_signal, symbol, current_price)
        
        # 策略置信度更高
        if strategy_action != "HOLD":
            return TradingSignal(
                signal_type=strategy_signal.signal_type,
                symbol=symbol,
                confidence=strat_conf,
                entry_price=getattr(strategy_signal, 'entry_price', getattr(strategy_signal, 'target_price', current_price)),
                strategy_name=getattr(strategy_signal, 'strategy_name', 'strategy_override'),
                reason=f"策略信號 (AI: {ai_action} {ai_conf:.1%})",
                target_price=getattr(strategy_signal, 'target_price', None),
                stop_loss=getattr(strategy_signal, 'stop_loss', None),
                take_profit=getattr(strategy_signal, 'take_profit', None),
                position_size=getattr(strategy_signal, 'position_size', None),
                indicators=getattr(strategy_signal, 'indicators', None),
                metadata={"source": "strategy_override"},
                timestamp=datetime.now()
            )
        
        return None
    
    def _get_ai_action(self, ai_signal: "AITradingSignal") -> str:
        """ AI """
        if not INFERENCE_ENGINE_AVAILABLE:
            return "HOLD"
        
        from .inference_engine import SignalType
        
        long_signals: List[SignalType] = [SignalType.STRONG_LONG, SignalType.LONG, SignalType.WEAK_LONG]
        short_signals: List[SignalType] = [SignalType.STRONG_SHORT, SignalType.SHORT, SignalType.WEAK_SHORT]
        
        if ai_signal.signal_type in long_signals:
            return "BUY"
        elif ai_signal.signal_type in short_signals:
            return "SELL"
        else:
            return "HOLD"
    
    def _convert_ai_signal_to_trading_signal(
        self, 
        ai_signal: "AITradingSignal",
        symbol: str,
        current_price: float
    ) -> TradingSignal:
        """ AI 信號轉換為 TradingSignal """
        action: str = self._get_ai_action(ai_signal)
        
        return TradingSignal(
            symbol=symbol,
            signal_type=TradeSignalType(action.lower()),
            confidence=ai_signal.confidence,
            entry_price=current_price,
            strategy_name='ai_inference',
            reason=f"AI推理: {ai_signal.reasoning}",
            target_price=(
                ai_signal.suggested_take_profit
                if ai_signal.suggested_take_profit > 0 and
                self._is_valid_target_price(TradeSignalType(action.lower()), current_price, ai_signal.suggested_take_profit)
                else None
            ),
            stop_loss=ai_signal.suggested_stop_loss if ai_signal.suggested_stop_loss > 0 else None,
            take_profit=ai_signal.suggested_take_profit if ai_signal.suggested_take_profit > 0 else None,
            position_size=ai_signal.suggested_position_size or None,
            indicators=None,
            metadata={"source": "ai_inference"},
            timestamp=datetime.now()
        )
    
    def _display_ai_signal(self, ai_signal: "AITradingSignal", current_price: float) -> None:
        """ AI """
        logger.info(f"🤖 AI : {ai_signal}")
        if ai_signal.suggested_leverage > 1:
            logger.info(f"   : {ai_signal.suggested_leverage}x | "
                       f": {ai_signal.suggested_position_size:.1%}")
        if ai_signal.suggested_stop_loss > 0:
            sl_pct: float = abs(ai_signal.suggested_stop_loss - current_price) / current_price * 100
            tp_pct: float = abs(ai_signal.suggested_take_profit - current_price) / current_price * 100
            logger.info(f"   : {sl_pct:.1f}% | : {tp_pct:.1f}% | "
                       f"RR: {ai_signal.risk_reward_ratio:.2f}")
    
    def _display_signal_info(self, signal: TradingSignal, current_price: float) -> None:
        """"""
        action_emoji: Dict[str, str] = {"BUY": "[GREEN]", "SELL": "", "HOLD": ""}
        emoji: str = action_emoji.get(signal.action, "")
        
        logger.info(f"{emoji} {signal.symbol}: ${current_price:,.2f} | "
                   f": {signal.action} (: {signal.confidence:.2%})")
        
        # 
        if hasattr(self.strategy, 'weights'):
            weights_str: str = " | ".join([f"{k.split('_')[0][:3]}:{v:.2f}" 
                                     for k, v in getattr(self.strategy, 'weights', {}).items()])
            logger.info(f"     : {weights_str}")
        
        reason = signal.reason or ""
        logger.info(f"    {reason[:100]}...")
    
    def _handle_trading_signal(self, signal: TradingSignal) -> None:
        """"""
        if signal.action == "HOLD":
            return
        
        if not self.auto_trade:
            return
        
        # 
        account_info = self.connector.get_account_info()
        if not account_info:
            logger.error(" ")
            return
        
        account_balance = float(account_info.get('totalWalletBalance', 0))
        
        can_trade, reason = self.risk_manager.check_can_trade(
            signal.confidence, 
            account_balance
        )
        
        if can_trade:
            logger.info(" ")
            self.execute_trade(signal)
        else:
            logger.warning(f" : {reason}")
    
    def execute_trade(self, signal: TradingSignal) -> None:
        """執行交易 - 主流程
        
        根據修復指南降低認知複雜度：將複雜邏輯拆分為多個輔助函數
        """
        try:
            # 1. 新聞風險檢查
            if not self._check_news_risk(signal.symbol):
                return
            
            # 2. 獲取賬戶信息
            account_balance: Optional[float] = self._get_account_balance()
            if account_balance is None:
                return
            
            # 3. 獲取當前價格
            current_price: Optional[float] = self._get_current_price(signal)
            if current_price is None or current_price <= 0:
                return
            
            # 4. 計算倉位大小
            position_size: Optional[float] = self._calculate_position_size(
                account_balance, current_price, signal.stop_loss
            )
            if position_size is None:
                return
            
            # 5. 顯示交易信息
            self._display_trade_info(signal, position_size, current_price)
            
            # 
            order_result: Optional[OrderResult] = self.connector.place_order(
                symbol=signal.symbol,
                side="BUY" if signal.action == "BUY" else "SELL",
                order_type="MARKET",
                quantity=position_size,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )
            
            if order_result and order_result.status != "ERROR":
                # 
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
                if hasattr(self.strategy, "record_trade_result"):
                    self.strategy.record_trade_result(  # type: ignore[union-attr]
                        str(getattr(signal, "strategy_name", "strategy_selector")),
                        {
                            "r_multiple": 0.0,
                            "confidence": signal.confidence,
                            "pnl": 0.0,
                            "symbol": signal.symbol,
                        },
                    )
                self._save_trade_to_file(trade_info)
                
                logger.info(f"  ID: {order_result.order_id}")
                
            else:
                logger.error(f" : {order_result.error if order_result else ''}")
                
        except Exception as e:
            logger.error(f" : {e}", exc_info=True)
    
    def _check_news_risk(self, symbol: str) -> bool:
        """檢查新聞風險
        
        Returns:
            True 如果可以交易，False 如果有新聞風險
        """
        if not (self.enable_rag_news_check or self.enable_news_analysis):
            return True

        assessment = self._assess_major_news(symbol)
        status = str(assessment.get("status", "ERROR"))
        summary = str(assessment.get("summary", ""))
        has_major_negative = bool(assessment.get("has_major_negative", False))

        if status == "ERROR":
            logger.error(f"新聞檢查失敗（阻擋交易）: {summary}")
            return False

        if status == "NO_DATA":
            logger.warning(f"新聞檢查無資料（不中斷交易）: {summary}")
            return True

        if has_major_negative:
            logger.warning(f"新聞風險警告（阻擋交易）: {summary}")
            return False

        logger.info(f"新聞檢查通過: {summary}")
        return True

    def _assess_major_news(self, symbol: str) -> Dict[str, Any]:
        """統一新聞評估入口（使用 PreTradeCheckSystem / RAG 單一路徑）"""
        if not self.news_checker:
            return {
                "status": "ERROR",
                "has_major_negative": False,
                "summary": "PreTradeCheckSystem 不可用，無法評估新聞風險",
            }

        try:
            if hasattr(self.news_checker, "_check_major_news"):
                result = self.news_checker._check_major_news(symbol)  # type: ignore[attr-defined]
                if isinstance(result, dict):
                    return result
            return {
                "status": "ERROR",
                "has_major_negative": False,
                "summary": "PreTradeCheckSystem 新聞介面不可用",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "has_major_negative": False,
                "summary": f"新聞評估例外: {e}",
            }
    
    def _get_account_balance(self) -> Optional[float]:
        """獲取賬戶餘額
        
        Returns:
            賬戶餘額，獲取失敗返回 None
        """
        account_info = self.connector.get_account_info()
        if not account_info:
            logger.error(" ")
            return None
        
        return float(account_info.get('totalWalletBalance', 0))
    
    def _get_current_price(self, signal: TradingSignal) -> Optional[float]:
        """獲取當前價格
        
        Args:
            signal: 交易信號
            
        Returns:
            當前價格，獲取失敗返回 None
        """
        if signal.target_price:
            return float(signal.target_price)
        
        price_data: Optional[MarketData] = self.get_real_time_price(signal.symbol)
        if not price_data:
            logger.error(" ")
            return None
        
        current_price: float = price_data.price
        if current_price <= 0:
            logger.error(" ")
            return None
        
        return current_price
    
    def _calculate_position_size(
        self, 
        account_balance: float, 
        current_price: float, 
        stop_loss: Optional[float]
    ) -> Optional[float]:
        """計算倉位大小
        
        Args:
            account_balance: 賬戶餘額
            current_price: 當前價格
            stop_loss: 止損價格
            
        Returns:
            倉位大小，計算失敗返回 None
        """
        # 使用 1% 風險規則
        risk_amount: float = account_balance * 0.01
        
        # 計算止損距離
        stop_price: float = stop_loss or current_price * 0.98
        stop_distance: float = abs(current_price - stop_price) / current_price
        
        # 計算倉位大小
        if stop_distance > 0:
            position_size = risk_amount / (current_price * stop_distance)
        else:
            position_size = risk_amount / current_price * 0.1  # 默認 10% 倉位
        
        # 限制最大倉位
        position_size = min(position_size, self.max_position_size)
        
        # 確保最小倉位
        if position_size < 0.001:
            logger.warning(f"   ({position_size:.6f}) 0.001")
            position_size = 0.001
        
        return position_size
    
    def _display_trade_info(self, signal: TradingSignal, quantity: float, current_price: float) -> None:
        """"""
        logger.info(" :")
        logger.info(f"   : {signal.action}")
        logger.info(f"   : {quantity:.6f} {signal.symbol.replace('USDT', '')}")
        logger.info(f"   : ${quantity * current_price:,.2f} USDT")
        logger.info(f"   : ${signal.stop_loss:,.2f}" if signal.stop_loss else "   : ")
        logger.info(f"   : ${signal.take_profit:,.2f}" if signal.take_profit else "   : ")
    
    def _save_trade_to_file(self, trade_info: Dict) -> None:
        """保存交易記錄到數據庫（並備份到 JSONL）"""
        try:
            # 保存到數據庫
            trade_id: Optional[int] = self.db_manager.save_trade(trade_info)
            logger.info(f"💾 交易記錄已保存到數據庫: ID={trade_id}")
            
            # 兼容性：同時保存到 JSONL（可選）
            trades_file: Path = self.data_dir / "trades_history.jsonl"
            with open(trades_file, 'a', encoding='utf-8') as f:
                json.dump({
                    **trade_info,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False)
                f.write('\\n')
                
        except Exception as e:
            logger.error(f"保存交易記錄失敗: {e}")
    
    def _show_news_analysis(self, symbol: str) -> None:
        """"""
        if not self.news_checker:
            return
        
        print("\\n" + "=" * 60)
        print(" ")
        print("=" * 60)
        
        try:
            assessment = self._assess_major_news(symbol)
            status = str(assessment.get("status", "ERROR"))
            has_major_negative = bool(assessment.get("has_major_negative", False))
            summary = str(assessment.get("summary", ""))
            print(f"📰 {symbol} 新聞檢查 [{status}]")
            print(f"摘要: {summary}")

            print()
            if status == "ERROR":
                print("❌ 新聞檢查失敗，建議暫停交易")
            elif status == "NO_DATA":
                print("⚪ 無相關新聞資料，維持中性判定")
            elif has_major_negative:
                print("⚠️ 偵測重大利空，建議暫停或降低倉位")
            else:
                print("✅ 未偵測重大利空")
            
            print("=" * 60 + "\\n")
            
        except Exception as e:
            logger.warning(f": {e}")
    
    def stop_monitoring(self) -> None:
        """"""
        self.is_monitoring = False
        self.connector.close_all_connections()
        logger.info(" ")
    
    def get_news_summary(self, symbol: str) -> str:
        """
        獲取新聞摘要（支持任意幣種）
        
        Args:
            symbol: 交易對符號 (例: BTCUSDT, ETHUSDT)
        
        Returns:
            str: 新聞摘要文本
        """
        try:
            assessment = self._assess_major_news(symbol)
            status = str(assessment.get("status", "ERROR"))
            summary = str(assessment.get("summary", ""))
            return f"[{status}] {summary}"
        except (AttributeError, ValueError) as e:
            return f"[ERROR] {e}"
    
    def set_news_analysis(self, enabled: bool) -> None:
        """"""
        self.enable_news_analysis = enabled
        logger.info(f"新聞分析 {'已啟用' if enabled else '已停用'}")
    
    def save_signals_history(self, _filepath: str = "signals_history.json") -> None:
        """保存信號歷史（目前使用統一的 save_all_data）
        
        Args:
            _filepath: 保留參數以保持 API 兼容性，實際使用 save_all_data()
        """
        self.save_all_data()
    
    def enable_auto_trading(self) -> None:
        """"""
        self.auto_trade = True
        logger.info("🤖 ")
    
    def disable_auto_trading(self) -> None:
        """"""
        self.auto_trade = False
        logger.info("⏸  ")
    
    def _check_breaking_news_before_start(self, symbol: str) -> None:
        """開盤前突發新聞檢查（使用 PreTradeCheckSystem / RAG）"""
        try:
            logger.info(f"\n{'='*70}")
            logger.info("📰 檢查突發新聞中...")
            logger.info(f"{'='*70}")
            
            assessment = self._assess_major_news(symbol)
            status = str(assessment.get("status", "ERROR"))
            summary = str(assessment.get("summary", ""))
            has_major_negative = bool(assessment.get("has_major_negative", False))

            if status == "OK" and not has_major_negative:
                logger.info(f"✅ 新聞檢查通過: {summary}")
            elif status == "NO_DATA":
                logger.warning(f"⚪ 新聞檢查無資料: {summary}")
            else:
                logger.error(f"\n{'='*70}")
                logger.error("⚠️ 新聞風險/系統警告")
                logger.error(f"{'='*70}")
                logger.error(f"原因: {summary}")
                if status == "ERROR":
                    logger.error("\n建議: 先排除新聞系統異常，再進行交易")
                else:
                    logger.error("\n建議: 等待新聞風險降低後再交易")
                logger.error(f"{'='*70}\n")
                
                # 詢問是否繼續
                response: str = input("\n是否繼續監控? (yes/no): ")
                if response.lower() not in ['yes', 'y', '是']:
                    logger.info("已停止監控")
                    self.is_monitoring = False
                    return
            
            logger.info(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"RAG 新聞檢查失敗: {e}")
    
    def toggle_rag_news_check(self) -> None:
        """ RAG """
        if not self.news_checker:
            logger.warning("RAG ")
            return
        
        self.enable_rag_news_check = not self.enable_rag_news_check
        status: str = "[GREEN] " if self.enable_rag_news_check else " "
        logger.info(f"RAG : {status}")
    
    def get_latest_news(self, hours: int = 6, max_articles: int = 10):
        """獲取最新加密貨幣新聞（使用 news_analyzer）"""
        if not self.news_analyzer:
            logger.warning("新聞分析器不可用")
            logger.info("提示: 確保 CryptoNewsAnalyzer 正確初始化")
            return []
        
        try:
            # 使用 news_analyzer 的 analyze_news 方法
            result: NewsAnalysisResult = self.news_analyzer.analyze_news(symbol="BTCUSDT", hours=hours)
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📰 最近 {hours} 小時內的新聞分析")
            logger.info(f"{'='*70}\n")
            
            if hasattr(result, 'articles') and result.articles:
                for i, article in enumerate(result.articles[:max_articles], 1):
                    title: Any = getattr(article, 'title', 'Unknown')
                    source: Any = getattr(article, 'source', 'Unknown')
                    url: Any = getattr(article, 'url', '')
                    logger.info(f"[{i}] {title}")
                    logger.info(f"    來源: {source}")
                    if url:
                        logger.info(f"    連結: {url}\n")
                return result.articles[:max_articles]
            else:
                logger.info("未找到相關新聞")
                return []
            
        except Exception as e:
            logger.error(f"獲取新聞失敗: {e}")
            return []
    
    def get_account_summary(self) -> Dict:
        """"""
        account_info = self.connector.get_account_info()
        
        if not account_info:
            return {
                "status": " ",
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
            "status": " ",
            "balance": total_balance,
            "available_balance": available_balance,
            "unrealized_pnl": total_unrealized_profit,
            "positions_count": len(active_positions),
            "positions": active_positions,
            "risk_stats": self.risk_manager.get_risk_statistics(),
            "strategy_weights": getattr(self.strategy, 'weights', {})
        }
    
    def get_strategy_report(self) -> Dict:
        """"""
        if hasattr(self.strategy, 'get_performance_summary'):
            return self.strategy.get_performance_summary()
        if hasattr(self.strategy, 'get_strategy_report'):
            return self.strategy.get_strategy_report()
        return {"message": ""}
    
    def save_all_data(self) -> None:
        """"""
        try:
            # 
            history_data = []
            for signal in self.signals_history[-1000:]:
                signal_dict = signal.model_dump()
                if hasattr(signal.timestamp, 'isoformat'):
                    signal_dict['timestamp'] = signal.timestamp.isoformat()
                history_data.append(signal_dict)
            
            signals_path: Path = self.data_dir / "signals_history.json"
            with open(signals_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f" : {signals_path} ({len(history_data)} )")
            
            # 
            if hasattr(self.strategy, 'weights'):
                weights_path: Path = self.data_dir / "strategy_weights.json"
                with open(weights_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'weights': getattr(self.strategy, 'weights', {}),
                        'performance_history': {
                            k: v[-100:] for k, v in getattr(self.strategy, 'performance_history', {}).items()
                        },
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=2, ensure_ascii=False)
                logger.info(f"  : {weights_path}")
            
            # 保存風險統計
            risk_stats_path: Path = self.data_dir / "risk_statistics.json"
            with open(risk_stats_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'statistics': self.risk_manager.get_risk_statistics(),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"風險統計已儲存: {risk_stats_path}")
            
            # 保存風險配置 (使用風險參數)
            risk_config_path: Path = self.data_dir / "risk_config.json"
            with open(risk_config_path, 'w', encoding='utf-8') as f:
                risk_params = getattr(self.risk_manager, 'risk_parameters', {})
                config_data = {}
                for level, params in risk_params.items() if isinstance(risk_params, dict) else {}:
                    config_data[level] = {
                        'max_risk_per_trade': getattr(params, 'max_risk_per_trade', 0.02),
                        'max_daily_risk': getattr(params, 'max_daily_risk', 0.05),
                        'max_leverage': getattr(params, 'max_leverage', 3.0)
                    }
                json.dump({
                    'risk_config': config_data,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"風險配置已儲存: {risk_config_path}")
            
        except Exception as e:
            logger.error(f": {e}", exc_info=True)


# 
CryptoFuturesTrader = TradingEngine
