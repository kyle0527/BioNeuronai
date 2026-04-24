"""
Smoke tests — 驗證核心模組可正常匯入與基本功能。

執行方式:
    python -m pytest tests/ -v
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

# 確保 src/ 在路徑中
_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ── 匯入 smoke tests ──────────────────────────────────────────────────────────

def test_bioneuronai_package_importable():
    """bioneuronai 主套件可匯入。"""
    import bioneuronai  # noqa: F401


def test_backtest_collect_signal_export_smoke():
    """backtest 套件應匯出 signal 訓練資料收集入口。"""
    from backtest import collect_signal_training_data

    assert callable(collect_signal_training_data)


def test_fastapi_app_importable():
    """FastAPI app 可匯入（不啟動伺服器）。"""
    from bioneuronai.api.app import app
    assert app is not None


def test_schemas_rag_importable():
    """schemas.rag 中的 EventContext 可匯入。"""
    from schemas.rag import EventContext
    ctx = EventContext(event_score=1.0, event_type="MACRO", intensity="HIGH")
    assert ctx.event_type == "MACRO"
    assert ctx.intensity == "HIGH"


def test_plan_controller_importable():
    """TradingPlanController 可匯入。"""
    from bioneuronai.planning.plan_controller import TradingPlanController  # noqa: F401


def test_legacy_model_importable():
    """HundredMillionModel 可從正式路徑匯入（不依賴 archived/）。"""
    from bioneuronai.models.legacy import HundredMillionModel
    model = HundredMillionModel(input_dim=64, hidden_dims=[128], output_dim=32)
    assert model.count_parameters() > 0


def test_cors_config_no_wildcard():
    """CORS 設定在無環境變數時不應包含萬用字元 '*'。"""
    from bioneuronai.api.app import _get_allowed_origins
    origins = _get_allowed_origins()
    assert "*" not in origins, (
        "allow_origins 不應設為 ['*']；"
        "請透過 ALLOWED_ORIGINS 環境變數設定允許的來源"
    )


def test_api_trade_state_is_managed_by_trade_manager():
    """API 交易狀態應由 TradeManager 封裝，不再暴露模組級全域引擎/task。"""
    import importlib

    api_app = importlib.import_module("bioneuronai.api.app")

    assert hasattr(api_app, "_trade_manager")
    assert type(api_app._trade_manager).__name__ == "TradeManager"
    assert not hasattr(api_app, "_trade_engine")
    assert not hasattr(api_app, "_trade_task")


def test_nlp_rag_system_is_not_default_export():
    """舊版 nlp.rag_system 應保留相容但不再是 NLP 模組的預設導出。"""
    import nlp

    assert "get_rag_system" not in nlp.__all__
    assert callable(nlp.get_rag_system)


class _FakeNewsAdapter:
    def search(self, symbol: str, max_results: int = 10, hours: int = 24):  # noqa: ARG002
        return [
            SimpleNamespace(
                title=f"{symbol} bullish catalyst",
                sentiment_score=0.35,
            )
        ]

    def get_event_context(self, symbol: str):
        from schemas.rag import EventContext

        return EventContext(
            event_score=0.2,
            event_type="MACRO",
            intensity="LOW",
            affected_symbols=[symbol],
        )


class _FakeConnector:
    def get_open_interest(self, symbol: str):  # noqa: ARG002
        return {"openInterest": "20000"}

    def get_ticker_24hr(self, symbol: str):  # noqa: ARG002
        return {
            "volume": "1200",
            "quoteVolume": "2500000",
            "priceChangePercent": "4.2",
        }

    def get_order_book(self, symbol: str, limit: int = 20):  # noqa: ARG002
        return {
            "bids": [["49995", "80"], ["49990", "60"]],
            "asks": [["50005", "90"], ["50010", "70"]],
        }

    def get_account_info(self):
        return {
            "totalWalletBalance": "10000",
            "availableBalance": "8000",
            "totalMarginBalance": "10000",
        }

    def get_ticker_price(self, symbol: str):  # noqa: ARG002
        return SimpleNamespace(price=50000.0)

    def get_premium_index(self, symbol: str):  # noqa: ARG002
        return {"lastFundingRate": "0.0001"}

    def get_book_ticker(self, symbol: str):  # noqa: ARG002
        return {"bidPrice": "49995", "askPrice": "50005"}


class _FakeRetriever:
    def retrieve_for_trading(
        self,
        symbol: str,
        context: str = "",
        include_news: bool = True,
        include_web: bool = True,
        time_hours: int = 24,
    ):  # noqa: ARG002
        return {
            "market_news": [
                SimpleNamespace(
                    title=f"{symbol} market structure improving",
                    source="news_api",
                    relevance_score=0.82,
                )
            ],
            "events": [
                SimpleNamespace(
                    title=f"{symbol} macro tailwind",
                    source="internal_knowledge",
                    relevance_score=0.76,
                )
            ],
        }


class _FakeKnowledgeBase:
    def __init__(self):
        self.add_calls = []
        self.saved = False

    def add_document(
        self,
        doc_id,
        title,
        content,
        doc_type,
        tags=None,
        metadata=None,
        update_index=True,
    ):
        self.add_calls.append(
            {
                "doc_id": doc_id,
                "title": title,
                "content": content,
                "doc_type": doc_type,
                "tags": tags or [],
                "metadata": metadata or {},
                "update_index": update_index,
            }
        )
        return SimpleNamespace(id=doc_id, title=title)

    def save_to_storage(self):
        self.saved = True


class _PendingOnlyConnector:
    def __init__(self):
        self.orders = []

    def has_pending_entry_order(self, symbol: str, side: str | None = None):  # noqa: ARG002
        return bool(self.orders)

    def has_open_position(self, symbol: str):  # noqa: ARG002
        return False


class _FakeNewsFetcher:
    def __init__(self, items):
        self._items = items
        self.rss_feeds = []

    def fetch_cryptopanic(self, coin: str):  # noqa: ARG002
        return list(self._items)

    def fetch_rss_feed(self, feed_url: str, coin: str):  # noqa: ARG002
        return []


def test_pretrade_execution_smoke_with_stubbed_dependencies():
    """pretrade 主鏈應可完整執行，不因 EventContext 或 os 問題中斷。"""
    from bioneuronai.planning.pretrade_automation import PreTradeCheckSystem

    checker = PreTradeCheckSystem()
    checker._get_connector = lambda: _FakeConnector()
    checker._get_news_adapter = lambda: _FakeNewsAdapter()
    checker._get_trading_retriever = lambda: _FakeRetriever()

    result = checker.execute_pretrade_check(symbol="BTCUSDT", intended_action="long")

    assert result["intended_action"] == "BUY"
    assert result["fundamentals"].news_check_status == "OK"
    assert result["fundamentals"].rag_context["status"] == "OK"
    assert result["fundamentals"].rag_context["total_hits"] == 2
    assert result["risk_calculation"].overall_status != "ERROR"


def test_base_strategy_pending_entry_state_sync_smoke():
    """待成交進場單應將策略維持在 ENTRY_READY，而不是被分析流程重置成 IDLE。"""
    import numpy as np

    from bioneuronai.strategies.base_strategy import (
        BaseStrategy,
        MarketCondition,
        PositionManagement,
        RiskParameters,
        SignalStrength,
        StrategyState,
        TradeSetup,
    )

    class PendingAwareStrategy(BaseStrategy):
        def __init__(self):
            super().__init__(
                name="Pending Aware",
                timeframe="1h",
                risk_params=RiskParameters(max_risk_per_trade_pct=1.0),
            )
            self.entry_attempts = 0

        def analyze_market(self, ohlcv_data, additional_data=None):  # noqa: ARG002
            self.state = StrategyState.ANALYZING
            self._finalize_analysis_state()
            return {
                "symbol": (additional_data or {}).get("symbol", "BTCUSDT"),
                "current_price": 100.0,
            }

        def evaluate_entry_conditions(self, market_analysis, ohlcv_data):  # noqa: ARG002
            return TradeSetup(
                symbol=market_analysis["symbol"],
                direction="long",
                entry_price=100.0,
                entry_confirmations=3,
                required_confirmations=3,
                stop_loss=95.0,
                take_profit_1=110.0,
                take_profit_2=115.0,
                take_profit_3=120.0,
                risk_reward_ratio=2.5,
                valid_until=datetime.now() + timedelta(minutes=30),
                signal_strength=SignalStrength.STRONG,
                market_condition=MarketCondition.UPTREND,
            )

        def execute_entry(self, setup, connector):
            self.entry_attempts += 1
            connector.orders.append(
                {
                    "symbol": setup.symbol,
                    "side": "BUY",
                    "status": "NEW",
                }
            )
            self._mark_pending_entry(setup)
            return None

        def manage_position(self, trade, current_price, ohlcv_data):  # noqa: ARG002
            return PositionManagement()

        def evaluate_exit_conditions(self, trade, current_price, ohlcv_data):  # noqa: ARG002
            return False, ""

        def execute_exit(self, trade, reason, connector, partial_exit=False, exit_portion=1.0):  # noqa: ARG002
            return True

    strategy = PendingAwareStrategy()
    connector = _PendingOnlyConnector()
    ohlcv = np.array(
        [
            [0, 100.0, 101.0, 99.0, 100.0, 10.0],
            [1, 100.0, 102.0, 99.0, 101.0, 11.0],
        ],
        dtype=float,
    )

    first = strategy.run_iteration(
        ohlcv_data=ohlcv,
        current_price=101.0,
        account_balance=10000.0,
        connector=connector,
        additional_data={"symbol": "BTCUSDT"},
    )
    second = strategy.run_iteration(
        ohlcv_data=ohlcv,
        current_price=101.0,
        account_balance=10000.0,
        connector=connector,
        additional_data={"symbol": "BTCUSDT"},
    )

    assert strategy.entry_attempts == 1
    assert strategy.state == StrategyState.ENTRY_READY
    assert strategy.current_setup is not None
    assert "pending" in " ".join(first["actions_taken"]).lower()
    assert any("待成交進場單" in msg for msg in second["signals"])


def test_strategy_planner_backtest_smoke():
    """daily_report 的回測驗證應接上正式 replay，而非 NOT_IMPLEMENTED。"""
    from bioneuronai.analysis.daily_report.strategy_planner import StrategyPlanner

    result = StrategyPlanner().perform_plan_backtest()

    assert result["status"] == "COMPLETED"
    assert result["status"] != "NOT_IMPLEMENTED"
    assert result["trade_count"] > 0
    assert result["run_id"]


def test_daily_report_writeback_to_knowledge_base_smoke(tmp_path):
    """daily_report 結果應保存 JSON，並寫回 MARKET_ANALYSIS 知識庫。"""
    from bioneuronai.analysis.daily_report.report_generator import ReportGenerator
    from rag.internal.knowledge_base import DocumentType

    fake_kb = _FakeKnowledgeBase()
    generator = ReportGenerator(
        data_dir=str(tmp_path),
        knowledge_base=fake_kb,
    )

    result = {
        "report_time": datetime(2026, 4, 21, 9, 0, 0),
        "report_version": "2.0",
        "report_type": "每日開盤前分析報告",
        "market_environment": {
            "overall_status": "BULLISH",
            "crypto_sentiment": 0.45,
            "us_futures": "UP",
            "european_markets": "MIXED",
            "asian_markets": "UP",
            "economic_events": ["CPI"],
            "news_analysis": {
                "sentiment": "positive",
                "sentiment_score": 0.45,
                "news_count": 3,
                "positive_count": 2,
                "negative_count": 0,
            },
        },
        "trading_plan": {
            "overall_status": "READY",
            "selected_strategy": "trend_following",
            "risk_parameters": {
                "single_trade_risk": 1.0,
                "daily_max_loss": 3.0,
                "max_positions": 2,
                "max_daily_trades": 4,
            },
            "trading_pairs": ["BTCUSDT", "ETHUSDT"],
            "daily_limits": {
                "max_loss_usd": 300.0,
                "max_single_trade_usd": 1500.0,
                "max_trades": 4,
            },
        },
        "overall_assessment": {
            "market_condition": "看漲 (BULLISH)",
            "plan_status": "READY",
            "recommendation": "可謹慎執行既定計劃",
        },
    }

    status = generator.save_check_results(result)

    assert status["knowledge_base"]["status"] == "OK"
    assert fake_kb.saved is True
    assert len(fake_kb.add_calls) == 1
    assert fake_kb.add_calls[0]["doc_type"] == DocumentType.MARKET_ANALYSIS
    assert "Daily Market Report" in fake_kb.add_calls[0]["title"]
    assert list(tmp_path.glob("sop_check_*.json"))


def test_event_context_trading_chain_smoke():
    """正式事件鏈應可從 trading_engine 傳到 strategy_fusion。"""
    from bioneuronai.core.trading_engine import TradingEngine
    from bioneuronai.strategies.selector.core import StrategySelector
    from schemas.rag import EventContext
    from schemas.enums import SignalType as TradeSignalType

    captured = {}

    class _FakeFusion:
        def generate_fusion_signal(self, ohlcv_data, additional_data=None, event_score=0.0, event_context=None):  # noqa: ARG002
            captured["event_context"] = event_context
            captured["event_score"] = event_score
            return SimpleNamespace(
                should_trade=True,
                consensus_direction="long",
                confidence_score=0.78,
                consensus_strength=0.7,
                contributing_strategies=["trend_following"],
                has_conflict=False,
                fusion_method_used=SimpleNamespace(value="market_adaptive"),
                selected_setup=None,
            )

    selector = StrategySelector.__new__(StrategySelector)
    selector._ai_fusion = _FakeFusion()

    engine = TradingEngine.__new__(TradingEngine)
    engine.strategy = selector
    engine._convert_klines_to_ohlcv = TradingEngine._convert_klines_to_ohlcv.__get__(engine, TradingEngine)
    engine._direction_to_signal_type = TradingEngine._direction_to_signal_type.__get__(engine, TradingEngine)
    engine._is_valid_target_price = TradingEngine._is_valid_target_price.__get__(engine, TradingEngine)
    engine._is_valid_stop_loss = TradingEngine._is_valid_stop_loss.__get__(engine, TradingEngine)

    event_context = EventContext(
        event_score=1.5,
        event_type="MACRO",
        intensity="HIGH",
        affected_symbols=["BTCUSDT"],
    )
    klines = [
        {
            "open_time": index,
            "open": 100 + index,
            "high": 101 + index,
            "low": 99 + index,
            "close": 100.5 + index,
            "volume": 1000 + index,
        }
        for index in range(25)
    ]

    signal = TradingEngine._generate_strategy_signal(
        engine,
        symbol="BTCUSDT",
        current_price=125.0,
        klines=klines,
        event_score=event_context.event_score,
        event_context=event_context,
    )

    assert signal is not None
    assert signal.signal_type == TradeSignalType.BUY
    assert captured["event_context"] is event_context
    assert captured["event_score"] == event_context.event_score


def test_live_event_context_consumer_chain_smoke():
    """正式 live 路徑應可從 news_adapter 經 trading_engine 傳到 strategy_fusion。"""
    from bioneuronai.core.trading_engine import TradingEngine
    from bioneuronai.strategies.selector.core import StrategySelector
    from schemas.rag import EventContext
    from schemas.enums import SignalType as TradeSignalType

    captured = {}

    class _FakeFusion:
        def generate_fusion_signal(self, ohlcv_data, additional_data=None, event_score=0.0, event_context=None):  # noqa: ARG002
            captured["event_context"] = event_context
            captured["event_score"] = event_score
            return SimpleNamespace(
                should_trade=True,
                consensus_direction="long",
                confidence_score=0.81,
                consensus_strength=0.75,
                contributing_strategies=["trend_following"],
                has_conflict=False,
                fusion_method_used=SimpleNamespace(value="market_adaptive"),
                selected_setup=None,
            )

    class _FakeNewsAdapter:
        def get_event_context(self, symbol: str):
            captured["symbol"] = symbol
            return EventContext(
                event_score=1.8,
                event_type="MACRO",
                intensity="HIGH",
                affected_symbols=[symbol],
            )

    selector = StrategySelector.__new__(StrategySelector)
    selector._ai_fusion = _FakeFusion()

    engine = TradingEngine.__new__(TradingEngine)
    engine.strategy = selector
    engine.news_adapter = _FakeNewsAdapter()
    engine.enable_phase_router = False
    engine.enable_ai_model = False
    engine.ai_model_loaded = False
    engine.inference_engine = None
    engine.signals_history = []
    engine._get_klines = lambda symbol, interval="1m", limit=200: [  # noqa: ARG005
        {
            "open_time": index,
            "open": 100 + index,
            "high": 101 + index,
            "low": 99 + index,
            "close": 100.5 + index,
            "volume": 1000 + index,
        }
        for index in range(25)
    ]
    engine._display_signal_info = lambda *args, **kwargs: None
    engine._generate_phase_router_signal = lambda **kwargs: None
    engine._apply_rl_meta_agent = lambda payload, symbol, ohlcv_data: payload  # noqa: ARG005
    engine._fuse_signals = lambda strategy_signal, ai_signal, symbol, current_price: strategy_signal  # noqa: ARG005
    engine._convert_klines_to_ohlcv = TradingEngine._convert_klines_to_ohlcv.__get__(engine, TradingEngine)
    engine._direction_to_signal_type = TradingEngine._direction_to_signal_type.__get__(engine, TradingEngine)
    engine._is_valid_target_price = TradingEngine._is_valid_target_price.__get__(engine, TradingEngine)
    engine._is_valid_stop_loss = TradingEngine._is_valid_stop_loss.__get__(engine, TradingEngine)
    engine._generate_strategy_signal = TradingEngine._generate_strategy_signal.__get__(engine, TradingEngine)
    engine.generate_trading_signal = TradingEngine.generate_trading_signal.__get__(engine, TradingEngine)
    engine._process_market_data = TradingEngine._process_market_data.__get__(engine, TradingEngine)

    signal = engine._process_market_data({"c": "125.0"}, "BTCUSDT")

    assert signal is not None
    assert signal.signal_type == TradeSignalType.BUY
    assert captured["symbol"] == "BTCUSDT"
    assert captured["event_context"] is not None
    assert captured["event_context"].event_type == "MACRO"
    assert captured["event_score"] == captured["event_context"].event_score


def test_phase_router_trading_engine_integration_smoke():
    """TradingEngine 應可在主流程中接入 PhaseRouter。"""
    from bioneuronai.core.trading_engine import TradingEngine
    from schemas.enums import SignalType as TradeSignalType

    class _FakePhaseRouter:
        def route_trading_decision(self, current_time, market_data, has_position=False, position_direction=None):  # noqa: ARG002
            assert market_data["symbol"] == "BTCUSDT"
            return {
                "phase": "mid_session",
                "action_phase": "entry",
                "strategy_used": "TrendFollowingStrategy",
                "signal": SimpleNamespace(
                    direction="long",
                    entry_price=125.0,
                    stop_loss=120.0,
                    take_profit_1=135.0,
                    total_position_size=0.2,
                    signal_strength=SimpleNamespace(value=4),
                    entry_confirmations=4,
                    required_confirmations=4,
                ),
            }

    engine = TradingEngine.__new__(TradingEngine)
    engine.enable_phase_router = True
    engine.phase_router = _FakePhaseRouter()
    engine.enable_rl_meta_agent = False
    engine.rl_meta_agent = None
    engine.positions = []

    signal = TradingEngine._generate_strategy_signal(
        engine,
        symbol="BTCUSDT",
        current_price=125.0,
        klines=[
            {
                "open_time": index,
                "open": 100 + index,
                "high": 101 + index,
                "low": 99 + index,
                "close": 100.5 + index,
                "volume": 1000 + index,
            }
            for index in range(25)
        ],
        event_score=0.0,
        event_context=None,
    )

    assert signal is not None
    assert signal.signal_type == TradeSignalType.BUY
    assert signal.strategy_name == "phase_router"
    assert signal.metadata["source"] == "phase_router"


def test_rl_meta_agent_integration_smoke():
    """TradingEngine 應可讓 RL Meta-Agent 後處理 selector 輸出。"""
    import bioneuronai.core.trading_engine as trading_engine_module
    from bioneuronai.core.trading_engine import TradingEngine
    from schemas.enums import SignalType as TradeSignalType

    class _FakeStrategy:
        def get_actionable_signal(self, ohlcv_data, symbol=None, event_score=0.0, event_context=None):  # noqa: ARG002
            return {
                "should_trade": True,
                "direction": "long",
                "confidence": 0.55,
                "entry_price": 125.0,
                "take_profit": 135.0,
                "stop_loss": 120.0,
                "strategy_name": "strategy_selector",
                "fusion_method": "selector",
            }

        def get_strategy_signals(self, ohlcv_data, symbol=None):  # noqa: ARG002
            return {
                "trend_following": SimpleNamespace(
                    direction="long",
                    entry_price=125.0,
                    stop_loss=120.0,
                    take_profit_1=135.0,
                    signal_strength=SimpleNamespace(value=4),
                    entry_confirmations=4,
                    required_confirmations=4,
                )
            }

    class _FakeRLAgent:
        def predict(self, strategy_signals, market_state, current_position=None):  # noqa: ARG002
            assert strategy_signals
            assert market_state.price > 0
            return SimpleNamespace(action_type="short", position_size=0.3, confidence=0.9)

    trading_engine_module.RLStrategySignal = lambda **kwargs: SimpleNamespace(**kwargs)
    trading_engine_module.RLMarketState = lambda **kwargs: SimpleNamespace(**kwargs)

    engine = TradingEngine.__new__(TradingEngine)
    engine.strategy = _FakeStrategy()
    engine.enable_phase_router = False
    engine.phase_router = None
    engine.enable_rl_meta_agent = True
    engine.rl_meta_agent = _FakeRLAgent()
    engine.positions = []
    engine.news_analyzer = None

    signal = TradingEngine._generate_strategy_signal(
        engine,
        symbol="BTCUSDT",
        current_price=125.0,
        klines=[
            {
                "open_time": index,
                "open": 100 + index,
                "high": 101 + index,
                "low": 99 + index,
                "close": 100.5 + index,
                "volume": 1000 + index,
            }
            for index in range(25)
        ],
        event_score=0.0,
        event_context=None,
    )

    assert signal is not None
    assert signal.signal_type == TradeSignalType.SELL
    assert signal.strategy_name == "rl_meta_agent"
    assert signal.metadata["source"] == "rl_meta_agent"


def test_news_analyzer_adaptive_window_smoke(tmp_path):
    """news analyzer 未指定 hours 時應依上次抓取時間自適應，不固定 24 小時。"""
    from bioneuronai.analysis.news.analyzer import CryptoNewsAnalyzer

    now = datetime.now()
    fetcher = _FakeNewsFetcher(
        [
            {
                "title": "BTC older article",
                "source": "CryptoPanic",
                "url": "https://example.com/old",
                "published_at": now - timedelta(hours=10),
                "summary": "older summary",
            },
            {
                "title": "BTC fresh article",
                "source": "CryptoPanic",
                "url": "https://example.com/new",
                "published_at": now - timedelta(minutes=30),
                "summary": "fresh summary",
            },
        ]
    )
    analyzer = CryptoNewsAnalyzer(enable_rag_ingest=False, news_fetcher=fetcher)
    analyzer._news_records_dir = tmp_path
    analyzer._news_records_file = tmp_path / "news_records.json"
    analyzer._news_fetch_state_file = tmp_path / "news_fetch_state.json"
    analyzer._save_last_fetch_time("BTCUSDT", now - timedelta(hours=2))

    result = analyzer.analyze_news("BTCUSDT", hours=None)

    assert result.total_articles == 1
    assert result.recent_headlines == ["BTC fresh article"]


def test_trading_engine_modal_weights_smoke():
    """三模態權重融合應實際影響最終信心。"""
    from bioneuronai.core.inference_engine import TradingSignal as AITradingSignal
    from bioneuronai.core.inference_engine import SignalType as AISignalType
    from bioneuronai.core.trading_engine import TradingEngine
    from schemas.enums import SignalType as TradeSignalType

    engine = TradingEngine.__new__(TradingEngine)
    engine._is_valid_target_price = TradingEngine._is_valid_target_price.__get__(engine, TradingEngine)

    ai_signal = AITradingSignal(
        symbol="BTCUSDT",
        timestamp=datetime.now(),
        signal_type=AISignalType.LONG,
        confidence=0.8,
        suggested_stop_loss=120.0,
        suggested_take_profit=135.0,
        suggested_position_size=0.2,
        market_regime="news_event",
        reasoning="news regime alignment",
    )
    strategy_signal = SimpleNamespace(
        action="BUY",
        confidence=0.6,
        signal_type=TradeSignalType.BUY,
        target_price=134.0,
        stop_loss=121.0,
        take_profit=134.0,
        position_size=0.15,
        indicators={"regime": "news_event"},
    )

    weights = TradingEngine._get_modal_weights(engine, "news_event")
    fused = TradingEngine._fuse_both_signals(
        engine,
        ai_signal=ai_signal,
        strategy_signal=strategy_signal,
        symbol="BTCUSDT",
        current_price=125.0,
        weights=weights,
        news_score=0.9,
    )

    expected_confidence = min(
        0.95,
        (0.6 * weights["strategy"]) + (0.8 * weights["ai"]) + (0.9 * weights["news"]) + 0.05,
    )

    assert fused is not None
    assert fused.signal_type == TradeSignalType.BUY
    assert fused.metadata["source"] == "ai_strategy_fusion"
    assert abs(fused.confidence - expected_confidence) < 1e-9


def test_strategy_fusion_event_weight_adjustment_smoke():
    """事件權重調整後應維持正規化，且宏觀事件提高趨勢策略權重。"""
    from bioneuronai.strategies.strategy_fusion import AIStrategyFusion
    from schemas.rag import EventContext

    fusion = AIStrategyFusion(enable_learning=False)
    baseline_trend_weight = fusion.strategy_weights["trend_following"].final_weight

    fusion._adjust_weights_by_event(
        EventContext(
            event_score=1.2,
            event_type="MACRO",
            intensity="HIGH",
            affected_symbols=["BTCUSDT"],
        )
    )

    adjusted_weights = {
        name: weight.final_weight for name, weight in fusion.strategy_weights.items()
    }

    assert abs(sum(adjusted_weights.values()) - 1.0) < 1e-9
    assert adjusted_weights["trend_following"] > baseline_trend_weight


def test_phase_router_phase_weight_adjustment_smoke():
    """PhaseRouter 的倉位與風險倍數應真正改動 TradeSetup。"""
    from bioneuronai.strategies.base_strategy import TradeSetup
    from bioneuronai.strategies.phase_router import PhaseConfig, TradingPhase, TradingPhaseRouter

    router = TradingPhaseRouter.__new__(TradingPhaseRouter)
    signal = TradeSetup(
        symbol="BTCUSDT",
        direction="long",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit_1=110.0,
        take_profit_2=120.0,
        take_profit_3=130.0,
        total_position_size=0.5,
    )
    config = PhaseConfig(
        phase=TradingPhase.MID_SESSION,
        position_size_multiplier=1.2,
        risk_multiplier=0.5,
    )

    adjusted = TradingPhaseRouter._adjust_signal_for_phase(router, signal, config)

    assert adjusted is not None
    assert abs(adjusted.total_position_size - 0.6) < 1e-9
    assert abs(adjusted.stop_loss - 97.5) < 1e-9
    assert abs(adjusted.take_profit_1 - 105.0) < 1e-9
    assert abs(adjusted.take_profit_2 - 110.0) < 1e-9
    assert abs(adjusted.take_profit_3 - 115.0) < 1e-9


def test_chat_cli_fallback_smoke(monkeypatch, capsys):
    """chat 指令在無模型時應可走完整 fallback 鏈並正常退出。"""
    import nlp.chat_engine as chat_engine
    from bioneuronai.cli.main import cmd_chat

    monkeypatch.setattr(chat_engine, "create_chat_engine", lambda *args, **kwargs: None)
    inputs = iter(["exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    cmd_chat(
        argparse.Namespace(
            symbol="BTCUSDT",
            language="zh",
            allow_rule_based_fallback=True,
        )
    )

    output = capsys.readouterr().out
    assert "規則模式" in output


def test_collect_signal_data_cli_parser_smoke():
    """訓練資料收集命令應存在於正式 CLI。"""
    from bioneuronai.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "collect-signal-data",
            "--symbol", "BTCUSDT",
            "--interval", "1h",
            "--seq-len", "16",
            "--max-samples", "25",
        ]
    )

    assert args.command == "collect-signal-data"
    assert args.symbol == "BTCUSDT"
    assert args.interval == "1h"
    assert args.seq_len == 16
    assert args.max_samples == 25
    assert callable(args.func)


def test_bilingual_tokenizer_legacy_load_smoke(tmp_path):
    """舊版僅含 vocab 的 tokenizer JSON 仍應可載入。"""
    import json

    from nlp.bilingual_tokenizer import BilingualTokenizer

    path = tmp_path / "legacy_vocab.json"
    path.write_text(
        json.dumps(
            {
                "vocab": {
                    "[PAD]": 0,
                    "[UNK]": 1,
                    "[BOS]": 2,
                    "[EOS]": 3,
                    "a": 4,
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    tokenizer = BilingualTokenizer.load(str(path))

    assert tokenizer.vocab["a"] == 4
    assert tokenizer.pad_token_id == 0
    assert tokenizer.bos_token_id == 2
    assert tokenizer.vocab_size >= len(tokenizer.vocab)


def test_virtual_account_pending_entry_reserves_margin_smoke():
    """未成交開倉單應預留保證金，避免可用餘額被錯算成還能繼續掛單。"""
    from bioneuronai.trading.virtual_account import VirtualAccount

    account = VirtualAccount(initial_balance=100.0, leverage=1)

    first = account.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=0.5,
        price=100.0,
    )
    second = account.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=0.6,
        price=100.0,
    )

    assert first.status.value == "NEW"
    assert second.status.value == "REJECTED"
    assert account.get_available_balance() < 50.0


def test_chat_engine_honest_generator_path_smoke():
    """ChatEngine 應支援 HonestGenerator.generate_with_honesty 介面。"""
    import torch

    from nlp.chat_engine import ChatEngine

    class _DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self._p = torch.nn.Parameter(torch.zeros(1))

        def forward(self, input_ids):  # pragma: no cover
            return input_ids

    class _DummyTokenizer:
        special_token_ids = {"eos_token": 0}

        def encode(self, text, max_length=1024, truncation=True):  # noqa: ARG002
            return torch.tensor([[1, 2, 3]], dtype=torch.long)

        def decode(self, ids):  # noqa: ARG002
            return "decoded"

    class _FakeHonestGenerator:
        def generate_with_honesty(self, input_ids, max_length=100, **kwargs):  # noqa: ARG002
            return {
                "generated_text": "市場結構偏多，但需嚴格控風險。",
                "overall_confidence": 0.73,
                "stop_reason": "",
            }

    engine = ChatEngine(
        model=_DummyModel(),
        tokenizer=_DummyTokenizer(),
        language="zh",
        max_new_tokens=32,
    )
    engine._honest_gen = _FakeHonestGenerator()

    text, confidence, stopped_reason = engine._generate("test prompt")

    assert text == "市場結構偏多，但需嚴格控風險。"
    assert abs(confidence - 0.73) < 1e-9
    assert stopped_reason == ""
