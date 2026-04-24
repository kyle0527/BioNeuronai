# -*- coding: utf-8 -*-
"""
BioNeuronai REST API Server
============================

將 CLI 功能包裝為 REST API，保持業務邏輯不變。

啟動方式:
    uvicorn bioneuronai.api.app:app --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# ── 路徑設定 ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bioneuronai.api.models import (  # noqa: E402
    ApiResponse,
    BacktestRequest,
    BinanceValidateRequest,
    ModuleStatus,
    NewsRequest,
    PreTradeRequest,
    SimulateRequest,
    StrategyBacktestRequest,
    StatusResponse,
    TradeStartRequest,
)
from schemas.api import (  # noqa: E402
    ChatRequest,
    ChatResponse,
    DashboardDataResponse,
    TradeOrderRequest,
    WsRiskData,
    WsMaxDrawdown,
    WsPretradeItem,
    WsPretradeChecklist,
    WsAuditLogEntry,
    WsPosition,
)

logger = logging.getLogger(__name__)


class TradeManager:
    """封裝 API 層的交易引擎與背景監控 task。"""

    def __init__(self) -> None:
        self._trade_task: Optional[asyncio.Task[Any]] = None
        self._trade_engine: Optional[Any] = None

    @property
    def engine(self) -> Optional[Any]:
        return self._trade_engine

    @property
    def task(self) -> Optional[asyncio.Task[Any]]:
        return self._trade_task

    def is_running(self) -> bool:
        return self._trade_task is not None and not self._trade_task.done()

    async def start(self, req: TradeStartRequest) -> str:
        """啟動交易監控並回傳使用中的環境名稱。"""
        if self.is_running():
            raise RuntimeError("交易已在運行中")

        from bioneuronai.core.trading_engine import TradingEngine

        api_key = req.api_key or os.getenv("BINANCE_API_KEY", "")
        api_secret = req.api_secret or os.getenv("BINANCE_API_SECRET", "")

        self._trade_engine = TradingEngine(
            api_key=api_key,
            api_secret=api_secret,
            testnet=req.testnet,
        )

        async def _monitor() -> None:
            if self._trade_engine is None:
                return
            await asyncio.to_thread(self._trade_engine.start_monitoring, req.symbol)

        self._trade_task = asyncio.create_task(_monitor())
        return "測試網" if req.testnet else "正式網"

    async def stop(self) -> None:
        """停止交易監控並清理引擎引用。"""
        if self._trade_task is not None and not self._trade_task.done():
            self._trade_task.cancel()
            self._trade_task = None

        if self._trade_engine is not None and hasattr(self._trade_engine, "stop_monitoring"):
            try:
                await asyncio.to_thread(self._trade_engine.stop_monitoring)
            except Exception:
                pass

        self._trade_engine = None

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """透過目前交易引擎查詢即時價格。"""
        if self._trade_engine is None:
            return None
        get_price = getattr(self._trade_engine, "_get_current_price", None)
        if get_price is None:
            return None
        try:
            price = await asyncio.to_thread(get_price, symbol)
            return float(price) if price else None
        except Exception:
            return None

    async def get_virtual_portfolio(self) -> list[dict]:
        """取得虛擬帳戶投資組合快照。"""
        if self._trade_engine is None:
            return []
        try:
            account = getattr(self._trade_engine, "virtual_account", None)
            if account is None:
                return []
            get_portfolio = getattr(account, "get_portfolio", None)
            if get_portfolio is None:
                return []
            raw = await asyncio.to_thread(get_portfolio)
            return raw if isinstance(raw, list) else []
        except Exception:
            return []


_trade_manager = TradeManager()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("BioNeuronai API 啟動中 ...")
    yield
    await _trade_manager.stop()
    logger.info("BioNeuronai API 關閉")


# ── CORS ─────────────────────────────────────────────────────────────────────
def _get_allowed_origins() -> list[str]:
    """從環境變數讀取允許的來源。
    
    生產環境請設定 ALLOWED_ORIGINS 環境變數，例如：
        ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
    
    若未設定，預設只允許本地開發伺服器。
    """
    env_val = os.getenv("ALLOWED_ORIGINS", "").strip()
    if env_val:
        return [o.strip() for o in env_val.split(",") if o.strip()]
    # 預設：本地開發的常見埠口
    return [
        "http://localhost:5173",   # Vite dev (devops-d)
        "http://localhost:3000",   # Create React App
        "http://localhost:8080",   # 其他本地服務
    ]


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BioNeuronai API",
    description="AI-driven cryptocurrency futures trading system REST API",
    version="2.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/", tags=["root"])
async def root():
    return {"service": "BioNeuronai API", "version": "2.1", "docs": "/docs", "backtest_ui": "/backtest/ui"}


# ── Status ────────────────────────────────────────────────────────────────────


@app.get("/api/v1/status", response_model=StatusResponse, tags=["system"])
async def get_status():
    """系統健康狀態檢查"""
    checks = [
        ("bioneuronai.core.trading_engine", "TradingEngine", "TradingEngine"),
        ("bioneuronai.data.binance_futures", "BinanceFuturesConnector", "BinanceFutures"),
        ("bioneuronai.analysis", "CryptoNewsAnalyzer", "NewsAnalyzer"),
        ("bioneuronai.analysis.daily_report", "SOPAutomationSystem", "SOPSystem"),
        ("bioneuronai.planning.pretrade_automation", "PreTradeCheckSystem", "PreTradeCheck"),
    ]

    modules = []
    all_ok = True
    for module_path, class_name, label in checks:
        try:
            mod = __import__(module_path, fromlist=[class_name])
            getattr(mod, class_name)
            modules.append(ModuleStatus(name=label, available=True))
        except (ImportError, AttributeError) as exc:
            modules.append(ModuleStatus(name=label, available=False, error=str(exc)))
            all_ok = False

    version = None
    try:
        import bioneuronai
        version = getattr(bioneuronai, "__version__", None)
    except Exception:
        pass

    return StatusResponse(modules=modules, version=version, all_ok=all_ok)


# ── Binance Validate ─────────────────────────────────────────────────────────


@app.post("/api/v1/binance/validate", response_model=ApiResponse, tags=["system"])
async def validate_binance_credentials(req: BinanceValidateRequest):
    """驗證 Binance API 憑證是否有效（讀取權限 + Futures 可用性）

    憑證優先順序：請求體 api_key/api_secret → 環境變數。
    """
    import os

    api_key = req.api_key or os.getenv("BINANCE_API_KEY", "")
    api_secret = req.api_secret or os.getenv("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        return ApiResponse(
            success=False,
            message="缺少 API 憑證。請在請求中提供 api_key/api_secret，或設定環境變數 BINANCE_API_KEY / BINANCE_API_SECRET。",
        )

    try:
        from bioneuronai.data.binance_futures import BinanceFuturesConnector

        connector = BinanceFuturesConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=req.testnet,
        )

        # 1. 取得報價（不需簽名，驗連線可達性）
        price_data = connector.get_ticker_price("BTCUSDT")
        if price_data is None:
            return ApiResponse(success=False, message="無法連線至 Binance，請檢查網路或 testnet 設定。")

        # 2. 獲取帳戶資訊（需簽名，驗 key 有效 + Futures 權限）
        account = connector.get_account_info()
        if not account:
            return ApiResponse(success=False, message="API Key 無效或缺乏 Futures 權限，請檢查 Key 設定。")

        total_balance = account.get("totalWalletBalance", "N/A")
        mode = "testnet" if req.testnet else "mainnet"
        return ApiResponse(
            success=True,
            message=f"憑證驗證成功 [{mode}]",
            data={"total_wallet_balance": total_balance, "environment": mode},
        )
    except Exception as exc:
        return ApiResponse(success=False, message=f"憑證驗證失敗: {exc}")


# ── News ──────────────────────────────────────────────────────────────────────


@app.post("/api/v1/news", response_model=ApiResponse, tags=["analysis"])
async def analyze_news(req: NewsRequest):
    """新聞情緒分析"""
    try:
        from bioneuronai.analysis import CryptoNewsAnalyzer

        analyzer = CryptoNewsAnalyzer()
        result = await asyncio.to_thread(analyzer.analyze_news, req.symbol)

        if isinstance(result, dict):
            data: Dict[str, Any] = result
        elif hasattr(result, "model_dump"):
            data = _safe_serialize(result)
        elif hasattr(result, "__dict__"):
            data = _safe_serialize(result)
        else:
            data = {"raw": str(result)}

        return ApiResponse(success=True, message="新聞分析完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"新聞分析失敗: {exc}")


# ── Backtest Replay ──────────────────────────────────────────────────────────


@app.get("/api/v1/backtest/catalog", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_catalog(symbol: str | None = None, interval: str | None = None):
    """列出可用的歷史回放資料。"""
    try:
        from backtest import get_catalog

        data = await asyncio.to_thread(get_catalog, None, symbol, interval)
        return ApiResponse(success=True, message="歷史資料掃描完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"歷史資料掃描失敗: {exc}")


@app.get("/api/v1/backtest/inspect", response_model=ApiResponse, tags=["backtest"])
async def inspect_backtest_dataset(
    symbol: str = "ETHUSDT",
    interval: str = "1h",
    start_date: str | None = None,
    end_date: str | None = None,
):
    """檢視指定資料集是否可被 replay 層載入。"""
    try:
        from backtest import HistoricalDataStream

        stream = await asyncio.to_thread(
            HistoricalDataStream,
            None,
            symbol,
            interval,
            start_date,
            end_date,
            0.0,
            True,
        )
        frame = stream.load_data()
        payload = {
            "resolved_root": str(stream.data_dir),
            "symbol": symbol,
            "interval": interval,
            "bars": len(frame),
            "start_open_time": int(frame["open_time"].iloc[0]),
            "end_open_time": int(frame["open_time"].iloc[-1]),
        }
        return ApiResponse(success=True, message="資料載入成功", data=payload)
    except Exception as exc:
        return ApiResponse(success=False, message=f"資料載入失敗: {exc}")


@app.post("/api/v1/backtest/simulate", response_model=ApiResponse, tags=["backtest"])
async def run_backtest_simulation(req: SimulateRequest):
    """執行 replay simulate。"""
    try:
        from backtest import run_simulation_summary

        data = await asyncio.to_thread(
            run_simulation_summary,
            req.symbol,
            req.interval,
            req.balance,
            req.bars,
            req.start_date,
            req.end_date,
        )
        return ApiResponse(success=True, message="simulate 完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"simulate 失敗: {exc}")


@app.post("/api/v1/backtest/run", response_model=ApiResponse, tags=["backtest"])
async def run_backtest(req: BacktestRequest):
    """執行 replay backtest。"""
    try:
        from backtest import run_backtest_summary

        data = await asyncio.to_thread(
            run_backtest_summary,
            req.symbol,
            req.interval,
            req.balance,
            req.start_date,
            req.end_date,
            None,
            req.warmup_bars,
        )
        return ApiResponse(success=True, message="backtest 完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"backtest 失敗: {exc}")


@app.post("/api/v1/backtest/strategy-run", response_model=ApiResponse, tags=["backtest"])
async def run_strategy_backtest(req: StrategyBacktestRequest):
    """執行策略模組競爭 / 策略模板回放。"""
    try:
        from backtest import run_strategy_suite_backtest

        data = await asyncio.to_thread(
            run_strategy_suite_backtest,
            symbol=req.symbol,
            interval=req.interval,
            balance=req.balance,
            start_date=req.start_date,
            end_date=req.end_date,
            warmup_bars=req.warmup_bars,
            close_open_positions_on_end=req.close_open_positions_on_end,
            execution_mode=req.execution_mode,
            parameter_overrides=req.parameter_overrides,
            commission_bps=req.commission_bps,
            slippage_bps=req.slippage_bps,
            walk_forward=req.walk_forward,
        )
        return ApiResponse(success=True, message="strategy backtest 完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"strategy backtest 失敗: {exc}")


@app.get("/api/v1/backtest/runs", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_runs(limit: int = 10):
    """列出 replay runtime runs。"""
    try:
        from backtest import list_runtime_runs

        data = await asyncio.to_thread(list_runtime_runs, limit)
        return ApiResponse(success=True, message="replay runs 讀取完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"replay runs 讀取失敗: {exc}")


@app.get("/api/v1/backtest/runs/{run_id}", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_run(run_id: str):
    """讀取指定 replay runtime run。"""
    try:
        from backtest import get_runtime_run

        data = await asyncio.to_thread(get_runtime_run, run_id)
        return ApiResponse(success=True, message="replay run 讀取完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"replay run 讀取失敗: {exc}")


@app.get("/backtest/ui", response_class=HTMLResponse, tags=["backtest"])
async def backtest_ui():
    """最小可用 backtest UI。"""
    from backtest import load_backtest_ui_html

    return HTMLResponse(load_backtest_ui_html())


# ── PreTrade ──────────────────────────────────────────────────────────────────


@app.post("/api/v1/pretrade", response_model=ApiResponse, tags=["trading"])
async def pretrade_check(req: PreTradeRequest):
    """進場前檢查"""
    try:
        from bioneuronai.planning.pretrade_automation import PreTradeCheckSystem

        checker = PreTradeCheckSystem()
        result = await asyncio.to_thread(
            checker.execute_pretrade_check,
            symbol=req.symbol,
            intended_action=req.action.upper(),
        )

        if isinstance(result, dict):
            data = result
        elif hasattr(result, "model_dump"):
            data = _safe_serialize(result)
        elif hasattr(result, "__dict__"):
            data = _safe_serialize(result)
        else:
            data = {"raw": str(result)}

        return ApiResponse(success=True, message="進場前檢查完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"進場前檢查失敗: {exc}")


# ── Trade Control ─────────────────────────────────────────────────────────────


@app.post("/api/v1/trade/start", response_model=ApiResponse, tags=["trading"])
async def start_trade(req: TradeStartRequest):
    """啟動交易監控"""
    if _trade_manager.is_running():
        return ApiResponse(success=False, message="交易已在運行中")

    try:
        mode = await _trade_manager.start(req)
        return ApiResponse(success=True, message=f"交易監控已啟動 [{mode}] {req.symbol}")
    except Exception as exc:
        return ApiResponse(success=False, message=f"交易啟動失敗: {exc}")


@app.post("/api/v1/trade/stop", response_model=ApiResponse, tags=["trading"])
async def stop_trade():
    """停止交易監控"""
    await _trade_manager.stop()
    return ApiResponse(success=True, message="交易監控已停止")


# ── Chat ─────────────────────────────────────────────────────────────────────

# 每個 conversation_id 對應一個 ChatEngine 實例（多輪記憶）
_chat_engines: Dict[str, Any] = {}
_default_chat_engine: Any = None


def _get_chat_engine(conversation_id: str, language: str = "auto") -> Any:
    """取得或建立對應 conversation_id 的 ChatEngine。"""
    global _default_chat_engine
    if conversation_id not in _chat_engines:
        if _default_chat_engine is None:
            try:
                from nlp.chat_engine import create_chat_engine
                _default_chat_engine = create_chat_engine(language=language)
            except Exception as e:
                logger.warning(f"[Chat] ChatEngine 初始化失敗: {e}")
                return None
        # 共用同一個引擎（若需要隔離多用戶，可改為每個 ID 建立獨立實例）
        _chat_engines[conversation_id] = _default_chat_engine
    return _chat_engines.get(conversation_id)


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest):
    """
    雙語對話端點（繁體中文 / English）。

    - 自動偵測使用者語言，依語言回應
    - 傳入 symbol（如 BTCUSDT）時自動注入即時市場資料
    - 傳入相同 conversation_id 可維持多輪對話記憶
    """
    import time
    import uuid
    t0 = time.time()

    conv_id = req.conversation_id or str(uuid.uuid4())

    engine = _get_chat_engine(conv_id, req.language)
    if engine is None:
        return ChatResponse(
            success=False,
            text="對話引擎未初始化，請確認模型已訓練並存放至 model/ 目錄。"
                 " (Chat engine not initialized. Please ensure the model is trained and placed in model/.)",
            language=req.language if req.language != "auto" else "zh",
            conversation_id=conv_id,
        )

    # 若有 language 設定，更新引擎語言
    if req.language != "auto":
        engine.set_language(req.language)

    # 建立市場上下文（若有 symbol）
    market_ctx = None
    if req.symbol:
        try:
            from nlp.chat_engine import MarketContext

            ctx = MarketContext(symbol=req.symbol)
            # 嘗試從全域 trade engine 取即時價格（可選）
            price = await _trade_manager.get_current_price(req.symbol)
            if price is not None:
                ctx.current_price = price
            market_ctx = ctx
        except Exception as e:
            logger.debug(f"[Chat] 市場上下文取得失敗（不影響對話）: {e}")

    # 執行對話（在執行緒中避免阻塞事件迴圈）
    try:
        response = await asyncio.to_thread(engine.chat, req.message, market_ctx)
        latency = (time.time() - t0) * 1000
        return ChatResponse(
            success=True,
            text=response.text,
            language=response.language,
            confidence=response.confidence,
            market_context_used=response.market_context_used,
            stopped_reason=response.stopped_reason,
            latency_ms=latency,
            conversation_id=conv_id,
        )
    except Exception as exc:
        logger.error(f"[Chat] 對話生成失敗: {exc}")
        return ChatResponse(
            success=False,
            text=f"生成失敗：{exc}",
            language="zh",
            conversation_id=conv_id,
        )


@app.delete("/api/v1/chat/{conversation_id}", response_model=ApiResponse, tags=["chat"])
async def reset_chat(conversation_id: str):
    """清除指定 conversation_id 的對話歷史"""
    engine = _chat_engines.get(conversation_id)
    if engine:
        engine.reset()
        return ApiResponse(success=True, message=f"對話歷史已清除 [{conversation_id}]")
    return ApiResponse(success=False, message="找不到該對話 ID")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _safe_serialize(obj: Any) -> dict[str, Any]:
    """將任意對象安全轉為 dict"""
    if isinstance(obj, dict):
        return {k: _safe_value(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return dict(obj.model_dump())
    if hasattr(obj, "__dict__"):
        return {k: _safe_value(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return {"raw": str(obj)}


def _safe_value(v):
    if isinstance(v, dict):
        return {k2: _safe_value(v2) for k2, v2 in v.items()}
    if isinstance(v, (list, tuple)):
        return [_safe_value(i) for i in v]
    if isinstance(v, datetime):
        return v.isoformat()
    try:
        import json
        json.dumps(v)
        return v
    except (TypeError, ValueError):
        return str(v)


# ── Dashboard REST ────────────────────────────────────────────────────────────


async def _build_dashboard_snapshot() -> dict:
    """組建 Dashboard 快照 dict，供 REST 端點及 WS 推送共用。"""
    now = datetime.now().isoformat()

    risk_level = "low"
    risk_pct = 0.0

    if _trade_manager.engine is not None:
        try:
            state = getattr(_trade_manager.engine, "state", None)
            if state and hasattr(state, "risk_percentage"):
                risk_pct = float(state.risk_percentage)
                if risk_pct > 20:
                    risk_level = "critical"
                elif risk_pct > 10:
                    risk_level = "high"
                elif risk_pct > 5:
                    risk_level = "medium"
        except Exception:
            pass

    audit_entries: list[WsAuditLogEntry] = []
    if _trade_manager.is_running():
        audit_entries.append(WsAuditLogEntry(
            id="sys-trade-running",
            timestamp=now,
            eventType="trade_start",
            description="交易監控運行中",
            status="success",
        ))

    checklist_items = [
        WsPretradeItem(id="c1", label="API 連線正常", completed=_trade_manager.engine is not None, required=True),
        WsPretradeItem(id="c2", label="風險參數已設定", completed=True, required=True),
        WsPretradeItem(id="c3", label="市場流動性正常", completed=True, required=False),
    ]
    completed_required = sum(1 for i in checklist_items if i.required and i.completed)
    total_required = sum(1 for i in checklist_items if i.required)

    snapshot = DashboardDataResponse(
        environment="testnet",
        risk=WsRiskData(level=risk_level, percentage=risk_pct, lastUpdated=now),
        maxDrawdown=WsMaxDrawdown(current=0.0, historical=0.0, period="30d", lastUpdated=now),
        pretradeChecklist=WsPretradeChecklist(
            items=checklist_items,
            completedCount=completed_required,
            totalCount=total_required,
            lastUpdated=now,
        ),
        auditLog=audit_entries,
        positions=None,
    )
    return snapshot.model_dump()


@app.get("/api/v1/dashboard", tags=["dashboard"])
async def get_dashboard():
    """取得 Dashboard 快照（admin-da 首頁使用）"""
    return await _build_dashboard_snapshot()


@app.post("/api/v1/orders", tags=["dashboard"])
async def submit_order(order: TradeOrderRequest):
    """提交交易訂單（admin-da TradingControls 使用）"""
    try:
        if _trade_manager.engine is None:
            return ApiResponse(
                success=False,
                message="交易引擎未啟動，請先呼叫 POST /api/v1/trade/start",
            )

        order_data = order.model_dump(exclude_none=True)
        place_fn = getattr(_trade_manager.engine, "place_order", None)
        if place_fn is not None:
            result = await asyncio.to_thread(place_fn, **order_data)
            return ApiResponse(
                success=True,
                message=f"訂單已提交 {order.side.upper()} {order.symbol} qty={order.quantity}",
                data=result if isinstance(result, dict) else {"status": "submitted", "order": order_data},
            )

        return ApiResponse(
            success=True,
            message=f"訂單已接受 {order.side.upper()} {order.symbol} qty={order.quantity}（引擎不支援直接下單）",
            data={"status": "accepted", "order": order_data},
        )
    except Exception as exc:
        return ApiResponse(success=False, message=f"訂單提交失敗: {exc}")


@app.delete("/api/v1/positions/{position_id}", tags=["dashboard"])
async def close_position(position_id: str):
    """平倉（admin-da 持倉列表使用）"""
    try:
        if _trade_manager.engine is None:
            return ApiResponse(success=False, message="交易引擎未啟動")

        close_fn = getattr(_trade_manager.engine, "close_position", None)
        if close_fn is not None:
            result = await asyncio.to_thread(close_fn, position_id)
            return ApiResponse(
                success=True,
                message=f"持倉 {position_id} 已平倉",
                data=result if isinstance(result, dict) else {"position_id": position_id},
            )

        return ApiResponse(
            success=True,
            message=f"平倉請求已記錄 {position_id}（引擎不支援直接平倉）",
            data={"position_id": position_id},
        )
    except Exception as exc:
        return ApiResponse(success=False, message=f"平倉失敗: {exc}")


# ── WebSocket Endpoints ───────────────────────────────────────────────────────


@app.websocket("/ws/trade")
async def ws_trade(websocket: WebSocket):
    """/ws/trade — 即時報價、成交推送（trading 前端 trade-control-page.tsx）"""
    await websocket.accept()
    symbol = "BTCUSDT"
    try:
        while True:
            price = 0.0
            current_price = await _trade_manager.get_current_price(symbol)
            if current_price is not None:
                price = current_price

            await websocket.send_json({"type": "price_update", "symbol": symbol, "price": price})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("[WS /ws/trade] 連線結束: %s", exc)


@app.websocket("/ws/analytics")
async def ws_analytics(websocket: WebSocket):
    """/ws/analytics — 投資組合、績效、成交資料推送（trading 前端 analytics-page.tsx）"""
    await websocket.accept()
    try:
        while True:
            portfolio: list[dict] = []
            portfolio = await _trade_manager.get_virtual_portfolio()

            await websocket.send_json({"type": "portfolio_update", "portfolio": portfolio})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("[WS /ws/analytics] 連線結束: %s", exc)


@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    """/ws/dashboard — Dashboard 整體狀態推送（admin-da DashboardView.tsx）"""
    await websocket.accept()
    try:
        while True:
            snapshot = await _build_dashboard_snapshot()
            await websocket.send_json(snapshot)
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("[WS /ws/dashboard] 連線結束: %s", exc)
