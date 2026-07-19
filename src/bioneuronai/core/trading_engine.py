"""
 -

"""

import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

from bioneuronai.analysis.feature_engineering import MarketMicrostructure
from bioneuronai.analysis.market_regime import RegimeAnalysis
from bioneuronai.analysis.news import CryptoNewsAnalyzer, NewsAnalysisResult
from bioneuronai.data.binance_futures import OrderResult
from config.trading_costs import TradingCostCalculator
from schemas.enums import SignalType as TradeSignalType  # 交易信號的 BUY/SELL/HOLD 枚舉
from schemas.market import MarketData
from schemas.trading import TradingSignal

from ..data import BinanceFuturesConnector, PaperBinanceFuturesConnector
from ..data.database_manager import DatabaseManager, get_database_manager
from ..risk_management import RiskManager

try:
    from ..strategies.selector import StrategySelector
    STRATEGY_SELECTOR_AVAILABLE = True
except ImportError:
    StrategySelector = None  # type: ignore[assignment,misc]
    STRATEGY_SELECTOR_AVAILABLE = False

try:
    from ..strategies.phase_router import TradingPhaseRouter
    PHASE_ROUTER_AVAILABLE = True
except ImportError:
    TradingPhaseRouter = None  # type: ignore[assignment,misc]
    PHASE_ROUTER_AVAILABLE = False

try:
    from ..strategies.rl_fusion_agent import (
        SB3_AVAILABLE as RL_SB3_AVAILABLE,
    )
    from ..strategies.rl_fusion_agent import (
        MarketState as RLMarketState,
    )
    from ..strategies.rl_fusion_agent import (
        RLMetaAgent,
    )
    from ..strategies.rl_fusion_agent import (
        StrategySignal as RLStrategySignal,
    )
    RL_META_AGENT_AVAILABLE = True
except ImportError:
    RLMetaAgent = None  # type: ignore[assignment,misc]
    RLStrategySignal = None  # type: ignore[assignment,misc]
    RLMarketState = None  # type: ignore[assignment,misc]
    RL_SB3_AVAILABLE = False
    RL_META_AGENT_AVAILABLE = False

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


@dataclass
class _OrderBookSnapshotAdapter:
    """將 Binance order book dict 轉為特徵模組可讀的快照介面。"""

    bids: List[List[Any]]
    asks: List[List[Any]]
    best_bid: float = 0.0
    best_ask: float = 0.0

    @property
    def spread_percentage(self) -> float:
        if self.best_bid <= 0 or self.best_ask <= 0:
            return 0.0
        mid_price = (self.best_bid + self.best_ask) / 2
        if mid_price <= 0:
            return 0.0
        return ((self.best_ask - self.best_bid) / mid_price) * 100

    def get_bid_depth(self, levels: int = 20) -> float:
        return sum(float(level[1]) for level in self.bids[:levels] if len(level) >= 2)

    def get_ask_depth(self, levels: int = 20) -> float:
        return sum(float(level[1]) for level in self.asks[:levels] if len(level) >= 2)

    def get_imbalance(self, levels: int = 20) -> float:
        bid_depth = self.get_bid_depth(levels)
        ask_depth = self.get_ask_depth(levels)
        total_depth = bid_depth + ask_depth
        if total_depth <= 0:
            return 0.0
        return (bid_depth - ask_depth) / total_depth


@dataclass
class _FundingRateAdapter:
    """資金費率特徵轉接層。"""

    funding_rate: float = 0.0
    predicted_funding_rate: float = 0.0
    hours_until_funding: float = 0.0


@dataclass
class _OpenInterestAdapter:
    """未平倉量特徵轉接層。"""

    open_interest: float = 0.0

logger: logging.Logger = logging.getLogger(__name__)

# trading_engine 不直接配置 root logger 或建立 FileHandler
# 日誌配置由 CLI 入口 (cli/main.py) 統一管理

# 新聞分析器（延遲初始化）
try:
    from ..analysis import get_news_analyzer as _get_news_analyzer
    NEWS_ANALYZER_AVAILABLE = True
except ImportError:
    _get_news_analyzer = None  # type: ignore[assignment]
    NEWS_ANALYZER_AVAILABLE = False
    logger.warning(" ")

#  RAG 模組 - 使用 PreTradeCheckSystem 替代
try:
    from ..planning.pretrade_automation import PreTradeCheckSystem
    RAG_NEWS_CHECKER_AVAILABLE = True
    PreTradeNewsChecker = PreTradeCheckSystem  # 別名兼容
except ImportError:
    RAG_NEWS_CHECKER_AVAILABLE = False
    PreTradeNewsChecker = None  # type: ignore
    PreTradeCheckSystem = None  # type: ignore
    logger.warning("RAG 新聞檢查模組不可用")

# NewsAdapter (RAG 事件上下文)
try:
    from rag.services.news_adapter import get_news_adapter as _get_news_adapter
    NEWS_ADAPTER_AVAILABLE = True
except ImportError:
    _get_news_adapter = None  # type: ignore
    NEWS_ADAPTER_AVAILABLE = False

#  AI
try:
    from .inference_engine import (
        UNIFIED_MODEL_NAME,
        InferenceEngine,
        get_shared_inference_engine,
    )
    from .inference_engine import (
        TradingSignal as AITradingSignal,
    )
    INFERENCE_ENGINE_AVAILABLE = True
except ImportError:
    InferenceEngine = None  # type: ignore[assignment,misc]
    UNIFIED_MODEL_NAME = "unified_v2_100m"
    get_shared_inference_engine = None  # type: ignore[assignment]
    AITradingSignal = None  # type: ignore[assignment,misc]
    INFERENCE_ENGINE_AVAILABLE = False
    logger.warning("[AI] AI Inference Engine not loaded")

# 特徵模組（延遲實例化）
try:
    from ..analysis import (
        LiquidationHeatmapCalculator,
        MarketDataProcessor,
        MarketRegimeDetector,
        VolumeProfileCalculator,
    )
    FEATURE_MODULES_AVAILABLE = True
except ImportError:
    MarketDataProcessor = None  # type: ignore[assignment,misc]
    MarketRegimeDetector = None  # type: ignore[assignment,misc]
    VolumeProfileCalculator = None  # type: ignore[assignment,misc]
    LiquidationHeatmapCalculator = None  # type: ignore[assignment,misc]
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
        ai_min_confidence: float = 0.5,     # AI
        paper_trading: bool = False,
        paper_initial_balance: float = 10000.0,
    ) -> None:
        #
        self.paper_trading = paper_trading
        self.connector: Union[BinanceFuturesConnector, PaperBinanceFuturesConnector]
        if paper_trading:
            self.connector = PaperBinanceFuturesConnector(
                api_key=api_key,
                api_secret=api_secret,
                testnet=False,
                initial_balance=paper_initial_balance,
            )
            logger.info("🧾 Live-paper execution enabled: orders are virtual and logged locally")
        else:
            self.connector = BinanceFuturesConnector(api_key, api_secret, testnet)
        self.risk_manager = RiskManager()  # RiskManager不需要參數
        self.strategy_type = str(strategy_type or "fusion").strip().lower()
        self.enable_phase_router = self.strategy_type == "phase_router"
        self.enable_rl_meta_agent = self.strategy_type == "rl_fusion"

        # 正式策略主線：StrategySelector + AIStrategyFusion
        if not STRATEGY_SELECTOR_AVAILABLE or StrategySelector is None:
            raise ImportError("StrategySelector 不可用，無法初始化正式策略主線")

        self.strategy = StrategySelector(
            timeframe="1m",
            enable_ai_fusion=use_strategy_fusion or strategy_type == "fusion",
        )

        # 載入固化後的黃金策略配置 (整合後的策略)
        if self.strategy.load_golden_profile():
            logger.info("✨ TradingEngine 已成功載入整合後的黃金策略配置")
        else:
            logger.info("ℹ️ 未找到黃金策略配置，將使用預設權重運行")

        logger.info(
            "✅ 使用新策略主線: StrategySelector%s",
            " + AI Fusion" if getattr(self.strategy, "ai_fusion_available", False) else "",
        )
        self.phase_router: Optional[Any] = None
        if self.enable_phase_router and (not PHASE_ROUTER_AVAILABLE or TradingPhaseRouter is None):
            raise ImportError("PhaseRouter 策略模式需要 TradingPhaseRouter，但目前模組不可用")
        if self.enable_phase_router and TradingPhaseRouter is not None:
            try:
                self.phase_router = TradingPhaseRouter(timeframe="1m", enable_ai_selection=True)
                logger.info("✅ PhaseRouter 已接入 TradingEngine 主線")
            except Exception as e:
                raise RuntimeError(f"PhaseRouter 初始化失敗: {e}") from e

        self.rl_meta_agent: Optional[Any] = None

        self.cost_calculator = TradingCostCalculator(
            vip_level=0,
            use_bnb=False,
            default_leverage=10,
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
        if self.enable_rl_meta_agent:
            self.rl_meta_agent = self._initialize_rl_meta_agent()

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

        if enable_ai_model and (
            not INFERENCE_ENGINE_AVAILABLE or get_shared_inference_engine is None
        ):
            raise ImportError("AI Inference Engine 不可用，無法啟用 AI 模型交易")

        if enable_ai_model:
            try:
                self.inference_engine = get_shared_inference_engine(
                    model_name=UNIFIED_MODEL_NAME,
                    min_confidence=ai_min_confidence,
                )
                self.ai_model_loaded = self.inference_engine.is_ready
                logger.info("[AI] Shared unified v2 inference engine initialized")
            except Exception as e:
                raise RuntimeError(f"AI Inference Engine initialization failed: {e}") from e

        # ==========  ==========
        self.market_data_processor = None
        self.regime_detector = None
        self.volume_profile_calculator = None
        self.liquidation_calculator = None

        if FEATURE_MODULES_AVAILABLE:
            try:
                assert MarketDataProcessor is not None
                assert MarketRegimeDetector is not None
                assert VolumeProfileCalculator is not None
                assert LiquidationHeatmapCalculator is not None
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
        if NEWS_ANALYZER_AVAILABLE and _get_news_analyzer is not None:
            try:
                self.news_analyzer = _get_news_analyzer()
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

        # NewsAdapter — 提供 EventContext 供策略層使用
        self.news_adapter: Optional[Any] = None
        if NEWS_ADAPTER_AVAILABLE and _get_news_adapter is not None:
            try:
                self.news_adapter = _get_news_adapter()
                logger.info("✅ NewsAdapter 已初始化")
            except Exception as e:
                logger.warning(f"NewsAdapter 初始化失敗: {e}")

        # ── 記憶層 + LoRA 在線學習器 ────────────────────────────────────────────
        try:
            from bioneuronai.core.online_learner import OnlineLearner
            from bioneuronai.memory.episodic_memory import EpisodicMemory
            _memory_dir = _project_root / "data" / "bioneuronai" / "memory"
            self.episodic_memory: Optional[Any] = EpisodicMemory(data_dir=_memory_dir)
            self.online_learner: Optional[Any] = None
            if enable_ai_model and self.ai_model_loaded:
                # 模型在 load_model() 後才能初始化 learner；此處設 None，load_model 後補
                pass
            logger.info("✅ 記憶層已初始化 | path=%s", _memory_dir)
        except Exception as _mem_err:
            self.episodic_memory = None
            self.online_learner = None
            logger.warning("記憶層初始化失敗（非致命）: %s", _mem_err)

        # ── 自適應學習中樞：交易結果 → 策略權重閉環（跨重啟持久化）─────────
        self.adaptive_hub: Optional[Any] = None
        try:
            from bioneuronai.core.adaptive_hub import AdaptiveLearningHub
            self.adaptive_hub = AdaptiveLearningHub(
                state_path=_project_root / "data" / "bioneuronai" / "learning" / "adaptive_hub.json"
            )
            # 重啟後立即恢復上次學到的策略權重，自適應狀態不歸零
            _learned_weights = self.adaptive_hub.get_strategy_weights()
            if _learned_weights and hasattr(self.strategy, "load_performance_weights"):
                self.strategy.load_performance_weights(_learned_weights, blend_alpha=0.3)
                logger.info("✅ 自適應中樞已恢復策略權重: %s", _learned_weights)
        except Exception as _hub_err:
            self.adaptive_hub = None
            logger.warning("自適應中樞初始化失敗（非致命）: %s", _hub_err)

        # 待決策的 ActionRecord（key = symbol，交易出場前保持 PENDING）
        self._pending_action_records: Dict[str, Any] = {}
        # 同步追蹤各 symbol 對應的策略名稱（用於 notify_trade_closed）
        self._pending_strategy_names: Dict[str, str] = {}

        # Paper trading 平倉回調接通（VirtualAccount → TradingEngine）
        if self.paper_trading and hasattr(self.connector, "virtual_account"):
            self.connector.virtual_account.set_close_callback(self._on_paper_close)
            logger.info("✅ Paper trading 平倉回調已接通 → notify_trade_closed")

        logger.info(" ")

    def _initialize_rl_meta_agent(self) -> Optional[Any]:
        """初始化 RL Meta-Agent；僅在模型與依賴齊備時啟用。"""
        if not RL_META_AGENT_AVAILABLE or RLMetaAgent is None or not RL_SB3_AVAILABLE:
            raise ImportError("rl_fusion 策略模式需要 RLMetaAgent / stable-baselines3 / gymnasium")

        model_path = self.data_dir / "rl_models"
        model_file = model_path / "ppo_strategy_fusion.zip"
        if not model_file.exists():
            raise FileNotFoundError(f"RL 模型不存在，無法啟用 rl_fusion: {model_file}")

        try:
            num_strategies = len(getattr(self.strategy, "_strategies", {})) or 5
            agent = RLMetaAgent(
                num_strategies=num_strategies,
                model_path=model_path,
                training_mode=False,
            )
            logger.info("✅ RL Meta-Agent 已接入 TradingEngine 主線")
            return agent
        except Exception as e:
            raise RuntimeError(f"RL Meta-Agent 初始化失敗: {e}") from e

    # ========== AI  ==========

    def load_ai_model(
        self, model_name: str = UNIFIED_MODEL_NAME, warmup: bool = False
    ) -> bool:
        """ AI

        Args:
            model_name:
            warmup:
        """
        if not self.inference_engine:
            logger.error(" AI ")
            return False
        if model_name != UNIFIED_MODEL_NAME:
            logger.error("Only unified_v2_100m is allowed in the active trading runtime")
            return False

        try:
            logger.info(f"[AI] Loading AI model: {model_name}...")
            self.inference_engine.load_model(model_name)

            if warmup:
                logger.info(" ...")
                self.inference_engine.model_loader.warmup()

            self.ai_model_loaded = True
            logger.info(" AI ")

            # 模型載入後初始化 LoRA 在線學習器
            if self.episodic_memory is not None and self.online_learner is None:
                try:
                    from bioneuronai.core.online_learner import OnlineLearner
                    self.online_learner = OnlineLearner(
                        model=self.inference_engine.model_loader.get_model(),
                        memory=self.episodic_memory,
                        device="cpu",
                    )
                    self.online_learner.load_latest_lora()
                    logger.info("✅ LoRA 在線學習器已初始化")
                except Exception as _le:
                    logger.warning("LoRA 在線學習器初始化失敗（非致命）: %s", _le)

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
            order_book_raw = self.connector.get_order_book(symbol, limit=20)
            book_ticker = self.connector.get_book_ticker(symbol)
            premium_index = self.connector.get_premium_index(symbol)
            funding_info = self.connector.get_funding_info(symbol)
            funding_history = self.connector.get_funding_rate(symbol)
            oi_raw = self.connector.get_open_interest(symbol)
            leverage_brackets = self.connector.get_leverage_brackets(symbol)

            return self.market_data_processor.build_market_microstructure(
                symbol=symbol,
                current_price=current_price,
                order_book=self._adapt_order_book(order_book_raw, book_ticker),
                funding_data=self._adapt_funding_data(premium_index, funding_info, funding_history),
                oi_data=self._adapt_open_interest(oi_raw),
                leverage_brackets=leverage_brackets
            )
        except Exception as e:
            logger.debug(f": {e}")
            return None

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """安全轉 float，避免原始 API 格式不穩定時中斷主流程。"""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _adapt_order_book(
        self,
        order_book: Optional[Dict[str, Any]],
        book_ticker: Optional[Dict[str, Any]] = None,
    ) -> Optional[_OrderBookSnapshotAdapter]:
        """將 Binance order book / bookTicker 轉為市場微結構需要的介面。"""
        bids = order_book.get("bids", []) if order_book else []
        asks = order_book.get("asks", []) if order_book else []

        best_bid = self._safe_float(book_ticker.get("bidPrice")) if book_ticker else 0.0
        best_ask = self._safe_float(book_ticker.get("askPrice")) if book_ticker else 0.0
        if best_bid <= 0 and bids:
            best_bid = self._safe_float(bids[0][0])
        if best_ask <= 0 and asks:
            best_ask = self._safe_float(asks[0][0])

        if not bids and not asks and best_bid <= 0 and best_ask <= 0:
            return None
        return _OrderBookSnapshotAdapter(
            bids=bids,
            asks=asks,
            best_bid=best_bid,
            best_ask=best_ask,
        )

    def _adapt_funding_data(
        self,
        premium_index: Optional[Dict[str, Any]],
        funding_info: Optional[Any],
        funding_history: Optional[List[Dict[str, Any]]],
    ) -> Optional[_FundingRateAdapter]:
        """整合 premiumIndex / fundingInfo / fundingRate 歷史為單一 funding 特徵。"""
        funding_rate = 0.0
        if premium_index:
            funding_rate = self._safe_float(premium_index.get("lastFundingRate"))
        elif funding_history:
            funding_rate = self._safe_float(funding_history[0].get("fundingRate"))

        hours_until_funding = 0.0
        if premium_index and premium_index.get("nextFundingTime"):
            next_funding_ts = self._safe_float(premium_index.get("nextFundingTime"))
            if next_funding_ts > 0:
                hours_until_funding = max(0.0, (next_funding_ts / 1000 - time.time()) / 3600)

        info_payload: Optional[Dict[str, Any]] = None
        if isinstance(funding_info, list):
            info_payload = funding_info[0] if funding_info else None
        elif isinstance(funding_info, dict):
            info_payload = funding_info

        if hours_until_funding <= 0 and info_payload:
            hours_until_funding = self._safe_float(info_payload.get("fundingIntervalHours"))

        if funding_rate == 0.0 and hours_until_funding <= 0 and not info_payload:
            return None
        return _FundingRateAdapter(
            funding_rate=funding_rate,
            predicted_funding_rate=funding_rate,
            hours_until_funding=hours_until_funding,
        )

    def _adapt_open_interest(
        self,
        oi_data: Optional[Dict[str, Any]],
    ) -> Optional[_OpenInterestAdapter]:
        """將 openInterest API 回傳轉為市場微結構需要的欄位。"""
        if not oi_data:
            return None
        open_interest = self._safe_float(oi_data.get("openInterest"))
        if open_interest <= 0:
            return None
        return _OpenInterestAdapter(open_interest=open_interest)

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

    def get_recent_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 300,
    ) -> List[Dict[str, Any]]:
        """提供自主流程讀取已轉換的 K 線，不建立另一個市場資料適配器。"""
        return self._get_klines(symbol=symbol, interval=interval, limit=limit)

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
        """相容入口：現在只啟動唯讀觀測，不再產生 ticker 直連交易。"""
        logger.warning(
            "start_monitoring 已收斂為行情觀測；自動決策請使用 AutonomousOperator"
        )
        self.start_market_observer(symbol)

    def start_market_observer(
        self,
        symbol: str,
        on_ticker: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        """啟動唯讀行情觀測，供 AutonomousOperator 更新紙上帳戶價格。

        這個入口刻意不產生訊號、不呼叫策略、也不送單；交易決策只能由
        ``AutonomousOperator`` 的 plan → pretrade → adaptation 流程完成。
        """
        if self.is_monitoring:
            logger.warning("已在監控中，請先停止現有監控")
            return

        self.is_monitoring = True

        def on_ticker_update(data: Dict[str, Any]) -> None:
            try:
                if not self.is_monitoring:
                    return
                self._update_paper_price_from_ticker(data, symbol)
                if on_ticker is not None:
                    on_ticker(data)
            except Exception as exc:
                logger.error("行情觀測 callback 失敗: %s", exc, exc_info=True)

        logger.info("啟動唯讀行情觀測 | %s", symbol)
        self.connector.subscribe_ticker_stream(
            symbol.lower(), on_ticker_update, auto_reconnect=True
        )

    def _update_paper_price_from_ticker(self, data: Dict[str, Any], symbol: str) -> None:
        """同步 tick 價格至既有 VirtualAccount，讓既有 SL/TP 照常生效。"""
        if not self.paper_trading or not hasattr(self.connector, "virtual_account"):
            return
        try:
            current_price = float(data["c"])
            high = float(data.get("h", current_price))
            low = float(data.get("l", current_price))
            self.connector.virtual_account.update_price(
                symbol, current_price, high=high, low=low
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.debug("VirtualAccount price update 失敗: %s", exc)

    def _process_market_data(self, data: Dict, symbol: str) -> Optional[TradingSignal]:
        """"""
        try:
            current_price = float(data['c'])

            # 舊監控入口保留相容性；紙上帳戶價格更新與唯讀觀測共用同一實作。
            self._update_paper_price_from_ticker(data, symbol)

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

        統一 live / replay 使用同一條責任鏈：
        1. StrategySelector 只產生戰術候選
        2. AI 讀取市場、濃縮新聞記憶與策略候選後作最終決策

        ``event_score`` 與 ``event_context`` 僅保留舊呼叫端相容性；新聞規則
        不再把固定方向傳入策略或覆寫 AI。
        """
        strategy_signal = self._generate_strategy_signal(
            symbol=symbol,
            current_price=current_price,
            klines=klines,
            event_score=0.0,
            event_context=None,
        )

        ai_signal: Optional[AITradingSignal] = None
        if self.enable_ai_model and self.ai_model_loaded and self.inference_engine:
            try:
                ai_signal = self.inference_engine.predict(
                    symbol=symbol,
                    current_price=current_price,
                    klines=klines,
                    context_text=self._build_ai_context(symbol, strategy_signal),
                )
                if ai_signal and display_ai:
                    self._display_ai_signal(ai_signal, current_price)
            except Exception as e:
                logger.warning(f"AI 信號生成失敗: {e}")

        final_signal = self._fuse_signals(strategy_signal, ai_signal, symbol, current_price)

        # ── T0：決策快照 ─────────────────────────────────────────────────────
        self._record_decision(
            symbol=symbol,
            current_price=current_price,
            ai_signal=ai_signal,
            final_signal=final_signal,
            strategy_signal=strategy_signal,
        )

        return final_signal

    @staticmethod
    def _build_ai_context(symbol: str, strategy_signal: Optional[Any]) -> str:
        """建立 AI 使用的濃縮事件記憶與獨立策略候選，不讀新聞全文。"""
        event_parts: List[str] = []
        try:
            from ..analysis.news.event_contract import get_contract_manager

            memory = get_contract_manager().get_memory_snapshot(symbol=symbol)
            for event in memory.get("active_events", [])[:3]:
                event_parts.append(
                    f"{event.get('event_type', 'UNKNOWN')} "
                    f"importance={float(event.get('current_importance', 0.0)):.3f} "
                    f"remaining_hours={float(event.get('remaining_hours', 0.0)):.1f}"
                )
        except Exception as exc:
            logger.debug("濃縮新聞事件記憶讀取失敗: %s", exc)

        news_context = (
            "; ".join(event_parts)
            if event_parts
            else "no active strategic event"
        )
        strategy_action = str(
            getattr(strategy_signal, "action", None)
            or getattr(strategy_signal, "signal_type", "HOLD")
        )
        strategy_confidence = float(
            getattr(strategy_signal, "confidence", 0.0) or 0.0
        )
        return (
            f"新聞事件記憶：{news_context}。"
            f"策略戰術候選：action={strategy_action}, confidence={strategy_confidence:.3f}；"
            "最終方向由 AI 判斷。 "
            f"News event memory: {news_context}. "
            f"Strategy candidate: action={strategy_action}, "
            f"confidence={strategy_confidence:.3f}; AI makes the final decision."
        )

    def _record_decision(
        self,
        symbol: str,
        current_price: float,
        ai_signal: Optional[Any],
        final_signal: Optional[Any],
        strategy_signal: Optional[Any],
    ) -> None:
        """T0：在每次決策時建立 ActionRecord 並存入待決區。"""
        if self.episodic_memory is None:
            return
        if final_signal is None:
            return
        try:
            from bioneuronai.core.action_record import ActionRecord
            record = ActionRecord(symbol=symbol)

            # 從 inference_engine 取得最近一次的 feature 向量（1024 維 → reshape 16×64）
            raw_feats: Optional[Any] = None
            raw_logits: Optional[Any] = None
            decoded: Dict[str, Any] = {}

            if self.inference_engine is not None:
                feats = getattr(self.inference_engine, "last_features_", None)
                if feats is not None:
                    raw_feats = np.asarray(feats, dtype=np.float32).reshape(16, 64)
                raw_logits = getattr(final_signal, "raw_output", None)

            if raw_feats is None or raw_logits is None:
                logger.warning("[ActionRecord] missing real inference snapshot; skip T0 | %s", symbol)
                return
            raw_logits = np.asarray(raw_logits, dtype=np.float32)
            if raw_feats.shape != (16, 64) or raw_logits.shape != (65,):
                logger.warning(
                    "[ActionRecord] incompatible inference snapshot; skip T0 | %s features=%s raw=%s",
                    symbol,
                    raw_feats.shape,
                    raw_logits.shape,
                )
                return

            # 依 unified-v2 的 65 維輸出頭解碼；不以固定機率或固定風控值補造資料。
            sigmoid = lambda value: 1.0 / (1.0 + np.exp(-float(value)))
            decoded = {
                "direction_probs": self._softmax(raw_logits[0:3]),
                "confidence_probs": self._softmax(raw_logits[3:6]),
                "leverage_probs": self._softmax(raw_logits[6:16]),
                "position_size": sigmoid(raw_logits[16]),
                "stop_loss_pct": sigmoid(raw_logits[17]) * 0.10,
                "take_profit_pct": sigmoid(raw_logits[18]) * 0.20,
                "hold_period_probs": self._softmax(raw_logits[19:29]),
                "multi_tf_align": np.tanh(raw_logits[29:34]),
                "pattern_probs": 1.0 / (1.0 + np.exp(-raw_logits[34:54])),
                "uncertainty": sigmoid(raw_logits[54]),
                "regime_probs": self._softmax(raw_logits[55:65]),
            }

            market_snapshot = {
                "price": current_price,
                "funding_rate": 0.0,
                "liquidation_volume_5min": 0.0,
                "price_change_5min_pct": 0.0,
                "volatility_1h": 0.0,
                "bid_ask_spread": 0.0,
                "orderbook_imbalance": 0.0,
            }

            record.fill_decision(
                symbol=symbol,
                numeric_patches=raw_feats,
                raw_signal=raw_logits,
                decoded=decoded,
                market_snapshot=market_snapshot,
            )
            record.strategy_signal_score = float(getattr(strategy_signal, "confidence", 0.0) or 0.0)
            record.ai_signal_score = float(getattr(ai_signal, "confidence", 0.0) or 0.0)
            record.fusion_score = float(getattr(final_signal, "confidence", 0.0) or 0.0)

            self._pending_action_records[symbol] = record
            self._pending_strategy_names[symbol] = str(
                getattr(strategy_signal, "strategy_name", "strategy_selector")
            )
            logger.debug("[ActionRecord] T0 recorded | symbol=%s direction=%s conf=%.2f",
                         symbol, record.direction, record.confidence)
        except Exception as _e:
            logger.debug("[ActionRecord] T0 記錄失敗（非致命）: %s", _e)

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

        phase_router_signal = self._generate_phase_router_signal(
            symbol=symbol,
            current_price=current_price,
            ohlcv_data=ohlcv_data,
            event_context=event_context,
        )
        if phase_router_signal is not None:
            return phase_router_signal

        payload = self.strategy.get_actionable_signal(  # type: ignore[union-attr]
            ohlcv_data=ohlcv_data,
            symbol=symbol,
            event_score=event_score,
            event_context=event_context,
        )
        payload = self._apply_rl_meta_agent(
            payload=payload,
            symbol=symbol,
            ohlcv_data=ohlcv_data,
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

        # ── 風險報酬比前置強制 ──────────────────────────────────────────
        # TradingSignal schema 要求：
        #   中等置信度 (0.5~0.8) 至少 RR=1.0，高置信度 (>0.8) 至少 RR=1.5。
        # 若策略提供的 take_profit 不足，自動延伸止盈至符合最低 RR，
        # 確保信號能通過 Pydantic 驗證，而非拋出 ValueError 中斷 backtest。
        if target_price is not None and stop_loss_value is not None and confidence >= 0.5:
            ep = float(entry_price)
            sl = stop_loss_value
            min_rr = 1.5 if confidence > 0.8 else 1.0
            if signal_type == TradeSignalType.BUY:
                risk = ep - sl
                reward = target_price - ep
                if risk > 0 and reward / risk < min_rr:
                    target_price = ep + risk * min_rr
            elif signal_type == TradeSignalType.SELL:
                risk = sl - ep
                reward = ep - target_price
                if risk > 0 and reward / risk < min_rr:
                    target_price = ep - risk * min_rr
        # ────────────────────────────────────────────────────────────────

        payload_metadata = dict(payload.get("metadata") or {})
        payload_metadata.setdefault("source", "strategy_selector")
        payload_metadata.update(
            {
                "direction": direction,
                "contributing_strategies": payload.get("contributing_strategies", []),
                "consensus_strength": payload.get("consensus_strength"),
            }
        )

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
            metadata=payload_metadata,
            timestamp=datetime.now(),
        )


    def _generate_phase_router_signal(
        self,
        symbol: str,
        current_price: float,
        ohlcv_data: np.ndarray,
        event_context: Optional[Any] = None,
    ) -> Optional[TradingSignal]:
        """在 TradingEngine 主流程中可選地使用 PhaseRouter。"""
        if not getattr(self, "enable_phase_router", False) or getattr(self, "phase_router", None) is None:
            return None

        try:
            market_data = self._build_phase_router_market_data(
                symbol=symbol,
                ohlcv_data=ohlcv_data,
                event_context=event_context,
            )
            first_position = self.positions[0] if getattr(self, "positions", None) else None
            decision = self.phase_router.route_trading_decision(  # type: ignore[union-attr]
                current_time=datetime.now(),
                market_data=market_data,
                has_position=first_position is not None,
                position_direction=first_position.side.lower() if first_position else None,
            )
            return self._convert_phase_router_decision_to_signal(
                decision=decision,
                symbol=symbol,
                current_price=current_price,
            )
        except Exception as e:
            raise RuntimeError(f"PhaseRouter 主線執行失敗: {e}") from e

    def _build_phase_router_market_data(
        self,
        symbol: str,
        ohlcv_data: np.ndarray,
        event_context: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """為 PhaseRouter 建立最小市場資料上下文。"""
        volatility = self._estimate_ohlcv_volatility(ohlcv_data)
        news_timestamp = getattr(event_context, "timestamp", None) if event_context is not None else None
        return {
            "symbol": symbol,
            "ohlcv": ohlcv_data,
            "volatility": volatility,
            "has_news_event": event_context is not None,
            "news_event_time": news_timestamp,
        }

    def _convert_phase_router_decision_to_signal(
        self,
        decision: Optional[Dict[str, Any]],
        symbol: str,
        current_price: float,
    ) -> Optional[TradingSignal]:
        """將 PhaseRouter 的決策轉為正式 TradingSignal。"""
        if not decision:
            return None

        setup = decision.get("signal")
        if setup is None:
            return None

        signal_type = self._direction_to_signal_type(str(getattr(setup, "direction", "")).lower())
        if signal_type is None:
            return None

        strength = getattr(getattr(setup, "signal_strength", None), "value", 3)
        confirmations = float(getattr(setup, "entry_confirmations", 0) or 0)
        required_confirmations = float(getattr(setup, "required_confirmations", 1) or 1)
        confidence = max(
            min(float(strength) / 5.0, 1.0),
            min(confirmations / max(required_confirmations, 1.0), 1.0),
        )
        entry_price = float(getattr(setup, "entry_price", current_price) or current_price)
        take_profit = getattr(setup, "take_profit_1", None)
        stop_loss = getattr(setup, "stop_loss", None)

        target_price = None
        if take_profit and self._is_valid_target_price(signal_type, entry_price, float(take_profit)):
            target_price = float(take_profit)

        stop_loss_value = None
        if stop_loss and self._is_valid_stop_loss(signal_type, entry_price, float(stop_loss)):
            stop_loss_value = float(stop_loss)

        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=max(0.0, min(1.0, confidence)),
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss_value,
            take_profit=float(take_profit) if take_profit else None,
            position_size=getattr(setup, "total_position_size", None),
            strategy_name="phase_router",
            reason=(
                f"PhaseRouter: {decision.get('phase', 'unknown')} / "
                f"{decision.get('action_phase', 'entry')} / "
                f"{decision.get('strategy_used', 'router')}"
            ),
            metadata={
                "source": "phase_router",
                "phase": decision.get("phase"),
                "action_phase": decision.get("action_phase"),
                "strategy_used": decision.get("strategy_used"),
            },
            timestamp=datetime.now(),
        )

    def _apply_rl_meta_agent(
        self,
        payload: Optional[Dict[str, Any]],
        symbol: str,
        ohlcv_data: np.ndarray,
    ) -> Optional[Dict[str, Any]]:
        """讓 RL Meta-Agent 以可選方式後處理 selector / fusion 輸出。"""
        if (
            payload is None
            or not payload.get("should_trade")
            or getattr(self, "rl_meta_agent", None) is None
            or RLStrategySignal is None
            or RLMarketState is None
        ):
            return payload

        try:
            strategy_signals = self.strategy.get_strategy_signals(  # type: ignore[union-attr]
                ohlcv_data,
                symbol=symbol,
            )
            rl_action = self.rl_meta_agent.predict(  # type: ignore[union-attr]
                strategy_signals=self._build_rl_strategy_signals(strategy_signals),
                market_state=self._build_rl_market_state(symbol, ohlcv_data),
                current_position=self._build_rl_current_position(symbol),
            )
        except Exception as e:
            logger.warning(f"RL Meta-Agent 推論失敗，回退既有主線: {e}")
            return payload

        rl_direction = str(getattr(rl_action, "action_type", "hold")).lower()
        rl_confidence = float(getattr(rl_action, "confidence", 0.0) or 0.0)
        if rl_direction == "hold" and rl_confidence >= 0.5:
            return None

        if rl_direction not in {"long", "short"}:
            return payload

        merged_payload = dict(payload)
        merged_payload.setdefault("metadata", {})
        merged_payload["metadata"] = {
            **(payload.get("metadata") or {}),
            "source": "rl_meta_agent",
            "rl_action": rl_direction,
            "rl_confidence": rl_confidence,
        }

        base_direction = str(payload.get("direction", "")).lower()
        base_confidence = float(payload.get("confidence") or 0.5)
        if rl_direction != base_direction and rl_confidence >= max(base_confidence, 0.75):
            merged_payload["direction"] = rl_direction
            merged_payload["confidence"] = rl_confidence
            merged_payload["strategy_name"] = "rl_meta_agent"
            merged_payload["fusion_method"] = "rl_meta_agent_override"
            return merged_payload

        if rl_direction == base_direction:
            merged_payload["confidence"] = max(base_confidence, min(0.95, rl_confidence))
            merged_payload["strategy_name"] = payload.get("strategy_name", "rl_meta_agent")
            return merged_payload

        return payload

    def _build_rl_strategy_signals(self, strategy_signals: Dict[str, Any]) -> List[Any]:
        """將 selector 的策略 setup 轉成 RL Agent 可接受的信號。"""
        converted: List[Any] = []
        if RLStrategySignal is None:
            return converted

        for name, setup in strategy_signals.items():
            if setup is None:
                converted.append(
                    RLStrategySignal(
                        strategy_name=name,
                        direction="neutral",
                        strength=0.0,
                        confidence=0.0,
                    )
                )
                continue

            strength = float(getattr(getattr(setup, "signal_strength", None), "value", 3)) / 5.0
            confirmations = float(getattr(setup, "entry_confirmations", 0) or 0)
            required_confirmations = float(getattr(setup, "required_confirmations", 1) or 1)
            confidence = min(1.0, max(strength, confirmations / max(required_confirmations, 1.0)))
            converted.append(
                RLStrategySignal(
                    strategy_name=name,
                    direction=str(getattr(setup, "direction", "neutral") or "neutral").lower(),
                    strength=max(0.0, min(1.0, strength)),
                    confidence=max(0.0, min(1.0, confidence)),
                    entry_price=float(getattr(setup, "entry_price", 0.0) or 0.0),
                    stop_loss=float(getattr(setup, "stop_loss", 0.0) or 0.0),
                    take_profit=float(getattr(setup, "take_profit_1", 0.0) or 0.0),
                )
            )

        return converted

    def _build_rl_market_state(self, symbol: str, ohlcv_data: np.ndarray) -> Any:
        """為 RL Agent 建立市場狀態摘要。"""
        if RLMarketState is None:
            return None

        closes = ohlcv_data[:, 4] if len(ohlcv_data) else np.array([], dtype=float)
        volumes = ohlcv_data[:, 5] if len(ohlcv_data) else np.array([], dtype=float)
        price = float(closes[-1]) if closes.size else 0.0
        trend_strength = 0.0
        if closes.size >= 2 and closes[0] != 0:
            trend_strength = max(-1.0, min(1.0, (float(closes[-1]) - float(closes[0])) / float(closes[0])))

        volume_ratio = 0.0
        if volumes.size >= 2:
            baseline_volume = float(np.mean(volumes[:-1])) or 1.0
            volume_ratio = max(0.0, min(1.0, float(volumes[-1]) / max(baseline_volume, 1.0)))

        # 新聞記憶不保存固定多空，舊 RL 欄位維持中性；只提供事件強度相關
        # 的有效時間與數量，避免 RL 策略在每次判斷時重新抓新聞全文。
        news_sentiment = 0.0
        news_duration_hours = 0.0
        related_news_count = 0
        try:
            from ..analysis.news.event_contract import get_contract_manager

            memory = get_contract_manager().get_memory_snapshot(symbol=symbol)
            active_events = memory.get("active_events", [])
            related_news_count = len(active_events)
            news_duration_hours = max(
                (
                    float(event.get("remaining_hours", 0.0))
                    for event in active_events
                ),
                default=0.0,
            )
        except Exception as exc:
            logger.debug("RL 市場狀態事件記憶讀取失敗: %s", exc)

        return RLMarketState(
            price=price,
            volatility=self._estimate_ohlcv_volatility(ohlcv_data),
            trend_strength=trend_strength,
            volume_ratio=volume_ratio,
            news_sentiment=max(-1.0, min(1.0, news_sentiment)),
            time_of_day=datetime.now().hour / 23.0,
            news_duration_hours=news_duration_hours,
            related_news_count=related_news_count,
        )

    def _build_rl_current_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """將當前持倉轉成 RL Agent 可讀格式。"""
        for position in getattr(self, "positions", []):
            if position.symbol != symbol:
                continue
            side = str(position.side).upper()
            return {
                "type": 1 if side == "LONG" else -1 if side == "SHORT" else 0,
                "size": float(getattr(position, "size", 0.0) or 0.0),
            }
        return None

    @staticmethod
    def _estimate_ohlcv_volatility(ohlcv_data: np.ndarray) -> float:
        """由 OHLCV 粗估 0-1 區間的波動率。"""
        if ohlcv_data.size == 0 or len(ohlcv_data) < 2:
            return 0.0
        closes = ohlcv_data[:, 4]
        previous = closes[:-1]
        current = closes[1:]
        valid = previous != 0
        if not np.any(valid):
            return 0.0
        returns = (current[valid] - previous[valid]) / previous[valid]
        return float(max(0.0, min(1.0, np.std(returns) * 10.0)))

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

    # ------------------------------------------------------------------
    # 多模態動態融合權重 (strategy, ai_inference, news)
    # 三者加總 = 1.0，依市場 regime 自動切換
    # 設計原則：
    #   - 技術策略為主力（可解釋、regime 特化）
    #   - AI 推論為輔助（已內建 1024 維多模態特徵）
    #   - 新聞情緒為過濾層（調整信心，非獨立方向信號）
    # ------------------------------------------------------------------
    _MODAL_WEIGHTS: Dict[str, Dict[str, float]] = {
        "strong_trend":    {"strategy": 0.70, "ai": 0.25, "news": 0.05},
        "ranging":         {"strategy": 0.50, "ai": 0.40, "news": 0.10},
        "high_volatility": {"strategy": 0.45, "ai": 0.40, "news": 0.15},
        "news_event":      {"strategy": 0.35, "ai": 0.35, "news": 0.30},
        "default":         {"strategy": 0.60, "ai": 0.30, "news": 0.10},
    }

    def _get_modal_weights(self, market_regime: str) -> Dict[str, float]:
        """依 AI 模型回報的 market_regime 字串選擇對應權重組。"""
        regime = (market_regime or "").lower()
        if any(k in regime for k in ("strong", "trend", "bull", "bear")):
            return self._MODAL_WEIGHTS["strong_trend"]
        if any(k in regime for k in ("rang", "chop", "sideways", "consolidat")):
            return self._MODAL_WEIGHTS["ranging"]
        if any(k in regime for k in ("volat", "spike", "extreme")):
            return self._MODAL_WEIGHTS["high_volatility"]
        if any(k in regime for k in ("news", "event", "announcement")):
            return self._MODAL_WEIGHTS["news_event"]
        return self._MODAL_WEIGHTS["default"]

    def _get_news_modal_score(self, symbol: str) -> float:
        """將新聞情緒分數（-1~1）正規化為模態信心值（0~1）。
        無新聞分析器或分析失敗時返回 0.5（中性，不影響加權）。
        """
        if not self.news_analyzer:
            return 0.5
        try:
            result = self.news_analyzer.analyze_news(symbol, hours=4)
            return max(0.0, min(1.0, (result.sentiment_score + 1.0) / 2.0))
        except Exception:
            return 0.5

    def _fuse_signals(
        self,
        strategy_signal,
        ai_signal: Optional["AITradingSignal"],
        symbol: str,
        current_price: float
    ) -> Optional[TradingSignal]:
        """將 AI 最終決策轉為交易信號；策略僅是 AI 的戰術候選輸入。

        方法名稱保留以維持既有呼叫架構。未取得 AI 決策時不得讓策略或新聞
        規則自行下單；AI 回傳 HOLD 時也不建立交易信號。
        """
        if ai_signal is None:
            if strategy_signal is not None:
                logger.info("策略已產生候選，但沒有 AI 最終決策；本輪不建立交易信號")
            return None
        if self._get_ai_action(ai_signal) == "HOLD":
            return None
        return self._convert_ai_signal_to_trading_signal(
            ai_signal,
            symbol,
            current_price,
        )

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
        current_price: float,
        weights: Dict[str, float],
        news_score: float,
    ) -> Optional[TradingSignal]:
        """三模態加權融合：一致時增強信心，衝突時以加權信心裁決。"""
        ai_action: str = self._get_ai_action(ai_signal)
        strategy_action = strategy_signal.action

        # 一致信號 → 三模態加權增強信心
        if ai_action == strategy_action and ai_action != "HOLD":
            return self._create_enhanced_signal(
                ai_signal, strategy_signal, symbol, current_price,
                ai_action, weights, news_score
            )

        # 衝突信號 → 加權信心裁決
        return self._resolve_conflicting_signals(
            ai_signal, strategy_signal, symbol, current_price,
            ai_action, strategy_action, weights, news_score
        )

    def _create_enhanced_signal(
        self,
        ai_signal: "AITradingSignal",
        strategy_signal,
        symbol: str,
        current_price: float,
        action: str,
        weights: Dict[str, float],
        news_score: float,
    ) -> TradingSignal:
        """三模態一致時，以加權信心公式增強融合信號。
        加權信心 = strategy_conf * w_strategy + ai_conf * w_ai + news_score * w_news
        """
        strat_conf: float = getattr(strategy_signal, 'confidence', 0.5)
        ai_conf: float = ai_signal.confidence
        weighted_confidence: float = (
            strat_conf  * weights["strategy"]
            + ai_conf   * weights["ai"]
            + news_score * weights["news"]
        )
        # 一致信號給予小幅加成，上限 0.95
        enhanced_confidence: float = min(0.95, weighted_confidence + 0.05)

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
        strategy_action: str,
        weights: Dict[str, float],
        news_score: float,
    ) -> Optional[TradingSignal]:
        """衝突信號裁決：計算各模態加權信心，選擇較高者。
        加權信心 = signal_conf * 該模態權重 + news_score * news 權重
        """
        ai_conf: float = ai_signal.confidence
        strat_conf: float = getattr(strategy_signal, 'confidence', 0.5)

        weighted_ai: float   = ai_conf    * weights["ai"]   + news_score * weights["news"]
        weighted_strat: float = strat_conf * weights["strategy"] + news_score * weights["news"]

        # AI 加權信心較高
        if weighted_ai > weighted_strat and ai_action != "HOLD":
            return self._convert_ai_signal_to_trading_signal(ai_signal, symbol, current_price)

        # 策略加權信心較高
        if strategy_action != "HOLD":
            return TradingSignal(
                signal_type=strategy_signal.signal_type,
                symbol=symbol,
                confidence=min(0.95, weighted_strat),
                entry_price=getattr(strategy_signal, 'entry_price', getattr(strategy_signal, 'target_price', current_price)),
                strategy_name=getattr(strategy_signal, 'strategy_name', 'strategy_override'),
                reason=f"策略信號勝出 (加權: {weighted_strat:.2f} vs AI: {weighted_ai:.2f})",
                target_price=getattr(strategy_signal, 'target_price', None),
                stop_loss=getattr(strategy_signal, 'stop_loss', None),
                take_profit=getattr(strategy_signal, 'take_profit', None),
                position_size=getattr(strategy_signal, 'position_size', None),
                indicators=getattr(strategy_signal, 'indicators', None),
                metadata={"source": "strategy_override", "modal_weights": weights},
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

            # 4.5 成本效益驗證：預期獲利必須超過總交易成本
            microstructure: Optional[MarketMicrostructure] = self._collect_market_microstructure(
                signal.symbol, current_price
            )
            if not self._is_cost_effective(signal, current_price, position_size * current_price, microstructure):
                logger.info(
                    "[成本過濾] %s 預期獲利不足以覆蓋手續費+資金費率+滑點，跳過下單",
                    signal.symbol,
                )
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
                self._save_trade_to_file(trade_info)

                # ── T1：進場快照 ──────────────────────────────────────────
                pending = self._pending_action_records.get(signal.symbol)
                if pending is not None:
                    try:
                        pending.fill_entry(
                            order_id=str(order_result.order_id),
                            entry_price=current_price,
                            leverage=getattr(signal, "suggested_leverage", 1) or 1,
                            position_size=position_size,
                            stop_loss=float(signal.stop_loss or 0),
                            take_profit=float(signal.take_profit or 0),
                        )
                        logger.debug("[ActionRecord] T1 recorded | symbol=%s order=%s",
                                     signal.symbol, order_result.order_id)

                    except Exception as _e:
                        logger.debug("[ActionRecord] T1 記錄失敗（非致命）: %s", _e)

                logger.info(f"  ID: {order_result.order_id}")

            else:
                logger.error(f" : {order_result.error if order_result else ''}")

        except Exception as e:
            logger.error(f" : {e}", exc_info=True)

    def execute_prepared_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        learning_context: Optional[Dict[str, Any]] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[OrderResult]:
        """執行已通過 planning/pretrade/adaptation 的訂單，作為統一執行入口。

        ``learning_context`` 僅接受當輪統一模型實際產生的輸入與輸出快照。
        在訂單確認成交後，才會將它寫成 ActionRecord 的 T0/T1；缺少快照時
        不會用預設值補造訓練資料。
        """
        normalized_side = side.strip().upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError(f"unsupported order side: {side}")
        if quantity <= 0:
            raise ValueError(f"quantity must be positive: {quantity}")
        result = self.connector.place_order(
            symbol=symbol,
            side=normalized_side,
            order_type="MARKET",
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            client_order_id=client_order_id,
        )
        if result is not None and result.status == "ERROR":
            raise RuntimeError(f"prepared order failed: {result.error}")
        if result is not None and str(result.status).upper() == "FILLED":
            self._record_prepared_order_action(
                symbol=symbol,
                side=normalized_side,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                result=result,
                learning_context=learning_context,
            )
        return result

    def _record_prepared_order_action(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        result: OrderResult,
        learning_context: Optional[Dict[str, Any]],
    ) -> None:
        """以已成交訂單與真實模型快照建立 ActionRecord 的 T0/T1。"""
        if self.episodic_memory is None:
            return
        if symbol in self._pending_action_records:
            logger.warning("[ActionRecord] pending record exists; skip prepared order | %s", symbol)
            return
        if not isinstance(learning_context, dict):
            logger.warning("[ActionRecord] no verified AI snapshot; skip prepared order | %s", symbol)
            return

        try:
            patches = np.asarray(learning_context.get("numeric_patches"), dtype=np.float32)
            raw_signal = np.asarray(learning_context.get("raw_signal"), dtype=np.float32)
        except (TypeError, ValueError):
            logger.warning("[ActionRecord] invalid AI snapshot values; skip prepared order | %s", symbol)
            return
        if patches.shape != (16, 64) or raw_signal.shape != (65,):
            logger.warning(
                "[ActionRecord] incomplete AI snapshot; skip prepared order | %s patches=%s raw=%s",
                symbol,
                patches.shape,
                raw_signal.shape,
            )
            return

        try:
            from bioneuronai.core.action_record import ActionRecord

            signal = learning_context.get("signal")
            signal = signal if isinstance(signal, dict) else {}
            entry_price = float(getattr(result, "price", 0.0) or 0.0)
            if entry_price <= 0:
                entry_price = float(learning_context.get("price_at_decision", 0.0) or 0.0)
            if entry_price <= 0:
                logger.warning("[ActionRecord] filled order has no verifiable price; skip | %s", symbol)
                return

            record = ActionRecord(symbol=symbol)
            record.numeric_patches = patches.tolist()
            record.raw_signal = raw_signal.tolist()
            record.direction = "LONG" if side == "BUY" else "SHORT"
            record.confidence = float(signal.get("confidence", 0.0) or 0.0)
            record.uncertainty = float(1.0 / (1.0 + np.exp(-float(raw_signal[54]))))
            record.suggested_leverage = int(signal.get("suggested_leverage", 1) or 1)
            record.suggested_position_size = float(
                signal.get("suggested_position_size", 0.0) or 0.0
            )
            record.market_regime = str(signal.get("market_regime", "UNKNOWN") or "UNKNOWN")
            record.price_at_decision = float(
                learning_context.get("price_at_decision", entry_price) or entry_price
            )
            record.text_context = str(learning_context.get("text_context", "") or "")
            record.multi_tf_align = np.tanh(raw_signal[29:34]).tolist()
            record.detected_patterns = (1.0 / (1.0 + np.exp(-raw_signal[34:54]))).tolist()
            record.regime_probs = self._softmax(raw_signal[55:65]).tolist()
            record.embedding = raw_signal[55:65].tolist()
            record.fill_entry(
                order_id=str(result.order_id),
                entry_price=entry_price,
                leverage=record.suggested_leverage,
                position_size=quantity * entry_price,
                stop_loss=float(stop_loss or 0.0),
                take_profit=float(take_profit or 0.0),
            )
            self._pending_action_records[symbol] = record
            self._pending_strategy_names[symbol] = "autonomous_paper"
            logger.info("[ActionRecord] prepared order T0/T1 recorded | %s order=%s", symbol, result.order_id)
        except Exception as exc:  # pragma: no cover - audit trail must not block a filled order
            logger.warning("[ActionRecord] prepared order record failed | %s: %s", symbol, exc)

    @staticmethod
    def _softmax(values: np.ndarray) -> np.ndarray:
        shifted = values - np.max(values)
        exp_values = np.exp(shifted)
        return exp_values / np.sum(exp_values)

    def notify_trade_closed(
        self,
        strategy_name: str,
        realized_pnl: float,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        symbol: str = "",
        exit_price: float = 0.0,
        exit_reason: str = "MANUAL",
    ) -> None:
        """平倉後呼叫，以實際損益更新策略權重，並推入記憶層觸發 LoRA 更新。

        Args:
            strategy_name: 產生信號的策略名稱
            realized_pnl: 實際損益（USDT）
            entry_price: 進場價格
            stop_loss_price: 止損價格（用於計算 R multiple）
            symbol: 交易對符號
            exit_price: 出場價格（用於 ActionRecord T2）
            exit_reason: 出場原因 SL_HIT / TP_HIT / MANUAL / TIMEOUT
        """
        if stop_loss_price and entry_price and abs(entry_price - stop_loss_price) > 0:
            risk = abs(entry_price - stop_loss_price)
            r_multiple = realized_pnl / risk
        else:
            r_multiple = 1.0 if realized_pnl > 0 else -1.0

        trade_result = {
            "r_multiple": r_multiple,
            "pnl": realized_pnl,
            "symbol": symbol,
        }
        if hasattr(self.strategy, "record_trade_result"):
            self.strategy.record_trade_result(strategy_name, trade_result)  # type: ignore[union-attr]
            logger.info(
                "策略權重已更新: %s | R=%.2f | PnL=%.2f",
                strategy_name, r_multiple, realized_pnl,
            )

        # ── T2：出場快照 + 記憶層推入 + LoRA 更新觸發 ───────────────────────
        self._pending_strategy_names.pop(symbol, None)
        realized_pnl_pct: Optional[float] = None
        realized_regime: Optional[str] = None
        if symbol and self.episodic_memory is not None:
            pending = self._pending_action_records.pop(symbol, None)
            if pending is not None:
                try:
                    _exit_price = exit_price if exit_price > 0 else entry_price
                    pending.fill_exit(
                        exit_price=_exit_price,
                        exit_reason=exit_reason,
                    )
                    experience = pending.to_experience_record()

                    is_extreme = self.episodic_memory.push(experience)
                    realized_pnl_pct = experience.pnl_pct
                    realized_regime = experience.market_regime
                    logger.info(
                        "[ActionRecord] T2 complete | symbol=%s outcome=%s pnl=%.3f%% extreme=%s",
                        symbol, experience.outcome, experience.pnl_pct * 100, is_extreme,
                    )

                    # 觸發 LoRA 在線更新（如果 learner 已初始化）
                    if self.online_learner is not None:
                        update_metrics = self.online_learner.record_outcome(
                            experience,
                            memory_already_recorded=True,
                        )
                        if update_metrics:
                            logger.info(
                                "[LoRA] 在線更新完成 | step=%d loss=%.5f",
                                update_metrics.get("update_step", 0),
                                update_metrics.get("loss", 0),
                            )
                except Exception as _e:
                    logger.debug("[ActionRecord] T2 記錄失敗（非致命）: %s", _e)

        # ── 自適應閉環：結果 → 中樞 → 重算策略權重 → 注入 selector ──────────
        if self.adaptive_hub is not None and symbol:
            try:
                if realized_pnl_pct is None:
                    # 無 ActionRecord 時以價格估算（方向以實際損益正負判定）
                    if entry_price > 0 and exit_price > 0:
                        magnitude = abs(exit_price - entry_price) / entry_price
                        realized_pnl_pct = magnitude if realized_pnl > 0 else -magnitude
                    else:
                        realized_pnl_pct = 0.001 if realized_pnl > 0 else -0.001
                self.adaptive_hub.record_trade(
                    strategy_name=strategy_name,
                    symbol=symbol,
                    pnl_pct=realized_pnl_pct,
                    market_regime=realized_regime,
                )
                if hasattr(self.strategy, "load_performance_weights"):
                    self.strategy.load_performance_weights(
                        self.adaptive_hub.get_strategy_weights(), blend_alpha=0.3
                    )
            except Exception as _hub_e:
                logger.debug("自適應中樞更新失敗（非致命）: %s", _hub_e)

    def _on_paper_close(
        self,
        symbol: str,
        realized_pnl: float,
        entry_price: float,
        exit_price: float,
        exit_reason: str,
    ) -> None:
        """VirtualAccount 平倉回調 → 自動觸發 T2 + LoRA 更新。

        這是連接 VirtualAccount（知道倉位實際出場）與
        notify_trade_closed（知道 ActionRecord / 記憶層）的橋樑。
        """
        strategy_nm = self._pending_strategy_names.get(symbol, "paper_auto")
        logger.info(
            "[Paper] 平倉事件觸發 | symbol=%s reason=%s pnl=%.4f",
            symbol, exit_reason, realized_pnl,
        )
        try:
            self.notify_trade_closed(
                strategy_name=strategy_nm,
                realized_pnl=realized_pnl,
                entry_price=entry_price,
                symbol=symbol,
                exit_price=exit_price,
                exit_reason=exit_reason,
            )
        except Exception as _e:
            logger.debug("_on_paper_close 回調失敗（非致命）: %s", _e)

    def _is_cost_effective(
        self,
        signal: TradingSignal,
        current_price: float,
        position_size_usd: float,
        microstructure: Optional[MarketMicrostructure] = None,
    ) -> bool:
        """驗證預期獲利是否足以覆蓋交易總成本。

        funding_rate 直接從已收集的 MarketMicrostructure 讀取（無需另發 API）。
        spread_bps 從 order_book 的最佳買賣報價計算（order_book 已在微結構收集時取得）。
        取得失敗或無 take_profit 時放行，不阻擋交易。
        """
        try:
            take_profit = getattr(signal, "take_profit", None)
            if not take_profit or current_price <= 0:
                return True

            # 從已收集的微結構讀取資金費率（可正可負）
            funding_rate: Optional[float] = None
            spread_bps: Optional[float] = None
            if microstructure is not None:
                funding_rate = microstructure.funding_rate

            # 從 order_book 計算即時價差（order_book 已在微結構收集時取得）
            try:
                ob = self.connector.get_order_book(signal.symbol, limit=5)
                if ob and ob.get("bids") and ob.get("asks"):
                    best_bid = float(ob["bids"][0][0])
                    best_ask = float(ob["asks"][0][0])
                    mid = (best_bid + best_ask) / 2
                    if mid > 0:
                        spread_bps = ((best_ask - best_bid) / mid) * 10000
            except Exception:
                pass

            expected_move_pct = abs(take_profit - current_price) / current_price * 100
            min_profit_pct = self.cost_calculator.get_minimum_profit_target(
                position_size_usd=position_size_usd,
                symbol=signal.symbol,
                desired_profit_margin=0.0,
                leverage=self.cost_calculator.default_leverage,
                based_on="notional",
                funding_rate=funding_rate,
                spread_bps=spread_bps,
            )
            return bool(expected_move_pct >= float(min_profit_pct))
        except Exception:
            return True

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
        """獲取賬戶可用餘額

        使用 availableBalance（可用餘額）而非 totalWalletBalance（總餘額），
        確保倉位計算不超出實際可下單的資金（已扣除已用保證金）。

        Returns:
            可用餘額，獲取失敗返回 None
        """
        account_info = self.connector.get_account_info()
        if not account_info:
            logger.error(" ")
            return None

        # 優先取 availableBalance；回退到 totalWalletBalance
        available = account_info.get('availableBalance') or account_info.get('totalWalletBalance', 0)
        return float(available)

    def _get_current_price(self, signal: TradingSignal) -> Optional[float]:
        """獲取當前進場參考價格

        優先使用信號的 entry_price（策略指定的進場價），
        其次向交易所查詢即時 ticker。
        注意：不使用 target_price（止盈價）作為進場參考，以免倉位計算錯誤。

        Args:
            signal: 交易信號

        Returns:
            當前進場參考價格，獲取失敗返回 None
        """
        # 優先使用 entry_price（策略明確指定的進場價）
        if signal.entry_price and signal.entry_price > 0:
            return float(signal.entry_price)

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

        # ── 可用餘額上限守衛 ────────────────────────────────────────────
        # 確保所需保證金不超過帳戶可用餘額的 90%。
        # 保留 10% 緩衝涵蓋：手續費 (taker 0.055%) + 滑點 (0.01%~0.05%) + 舍入誤差。
        # 使用傳入的 account_balance（已是 availableBalance）避免因帳戶狀態時差導致超額。
        available = account_balance
        # 嘗試再次從 connector 取得最新可用餘額
        try:
            connector = getattr(self, "connector", None)
            if connector is not None:
                va = getattr(connector, "virtual_account", None)
                if va is not None:
                    fresh = va.get_available_balance()
                    available = min(available, fresh)  # 保守取較小值
        except Exception:
            pass
        leverage = getattr(self, "leverage", 1) or 1
        max_qty_by_balance = (available * 0.90 * leverage) / current_price
        position_size = min(position_size, max_qty_by_balance)
        # ────────────────────────────────────────────────────────────────

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

                if sys.stdin is not None and sys.stdin.isatty():
                    response: str = input("\n是否繼續監控? (yes/no): ")
                    if response.lower() in ['yes', 'y', '是']:
                        logger.warning("操作員已確認忽略新聞風險並繼續監控")
                    else:
                        logger.info("已停止監控")
                        self.is_monitoring = False
                        return
                else:
                    if self.paper_trading:
                        logger.warning(
                            "非互動環境偵測到新聞風險；保留 Paper 行情監控，"
                            "並停用自動開新倉"
                        )
                        self.auto_trade = False
                        return
                    logger.error("非互動環境偵測到新聞風險/系統警告，保守停止監控")
                    logger.info("已停止監控")
                    self.is_monitoring = False
                    return

            logger.info(f"{'='*70}\n")

        except Exception as e:
            logger.error(f"RAG 新聞檢查失敗: {e}")
            if self.paper_trading:
                logger.warning("Paper 行情監控保留，並停用自動開新倉")
                self.auto_trade = False
                return
            if sys.stdin is None or not sys.stdin.isatty():
                logger.error("非互動環境無法確認新聞檢查異常，保守停止監控")
                self.is_monitoring = False

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
            summary = self.strategy.get_performance_summary()
            return dict(summary) if isinstance(summary, dict) else {"summary": summary}
        if hasattr(self.strategy, 'get_strategy_report'):
            report = self.strategy.get_strategy_report()
            return dict(report) if isinstance(report, dict) else {"report": report}
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

    def get_learning_status(self) -> Dict[str, Any]:
        """回傳記憶層和 LoRA 學習器的當前狀態，供 API 或 Dashboard 查詢。"""
        result: Dict[str, Any] = {
            "memory_enabled": self.episodic_memory is not None,
            "learner_enabled": self.online_learner is not None,
            "pending_records": list(self._pending_action_records.keys()),
        }
        if self.episodic_memory is not None:
            result["memory"] = self.episodic_memory.get_stats()
        if self.online_learner is not None:
            result["learner"] = self.online_learner.get_stats()
        return result


#
CryptoFuturesTrader = TradingEngine


# ════════════════════════════════════════════════════════════════════
# 🚀 程式可運行與直接驗證原則 (CODE_FIX_GUIDE.md)
# ════════════════════════════════════════════════════════════════════
