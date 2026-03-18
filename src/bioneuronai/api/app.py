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
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    JobStatus,
    ModuleStatus,
    NewsRequest,
    PreTradeRequest,
    SimulateRequest,
    StatusResponse,
    TradeStartRequest,
)

logger = logging.getLogger(__name__)

# ── 背景任務儲存 ──────────────────────────────────────────────────────────────
_jobs: Dict[str, JobStatus] = {}


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("BioNeuronai API 啟動中 ...")
    yield
    logger.info("BioNeuronai API 關閉")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BioNeuronai API",
    description="AI-driven cryptocurrency futures trading system REST API",
    version="4.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/", tags=["root"])
async def root():
    return {"service": "BioNeuronai API", "version": "4.3.0", "docs": "/docs"}


# ── Status ────────────────────────────────────────────────────────────────────


@app.get("/api/v1/status", response_model=StatusResponse, tags=["system"])
async def get_status():
    """系統健康狀態檢查"""
    checks = [
        ("bioneuronai.core.trading_engine", "TradingEngine", "TradingEngine"),
        ("bioneuronai.data.binance_futures", "BinanceFuturesConnector", "BinanceFutures"),
        ("bioneuronai.analysis", "CryptoNewsAnalyzer", "NewsAnalyzer"),
        ("bioneuronai.trading.sop_automation", "SOPAutomationSystem", "SOPSystem"),
        ("bioneuronai.trading.plan_controller", "TradingPlanController", "PlanController"),
        ("bioneuronai.trading.pretrade_automation", "PreTradeCheckSystem", "PreTradeCheck"),
        ("backtest", "BacktestEngine", "BacktestEngine"),
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


# ── Plan ──────────────────────────────────────────────────────────────────────


@app.post("/api/v1/plan", response_model=ApiResponse, tags=["trading"])
async def create_plan():
    """生成每日 SOP 交易計劃"""
    report = None

    # 優先：TradingPlanController（10 步驟，async）
    try:
        from bioneuronai.trading.plan_controller import TradingPlanController

        controller = TradingPlanController()
        report = await controller.create_comprehensive_plan()
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("TradingPlanController 執行失敗: %s", exc)

    # Fallback：SOPAutomationSystem（同步）
    if report is None:
        try:
            from bioneuronai.trading.sop_automation import SOPAutomationSystem

            sop = SOPAutomationSystem()
            report = await asyncio.to_thread(sop.execute_daily_premarket_check)
        except Exception as exc:
            return ApiResponse(success=False, message=f"計劃生成失敗: {exc}")

    return ApiResponse(success=True, message="交易計劃已生成", data=_safe_serialize(report))


# ── News ──────────────────────────────────────────────────────────────────────


@app.post("/api/v1/news", response_model=ApiResponse, tags=["analysis"])
async def analyze_news(req: NewsRequest):
    """新聞情緒分析"""
    try:
        from bioneuronai.analysis import CryptoNewsAnalyzer

        analyzer = CryptoNewsAnalyzer()
        result = await asyncio.to_thread(analyzer.analyze_news, req.symbol)

        if isinstance(result, dict):
            data = result
        elif hasattr(result, "model_dump"):
            data = result.model_dump()
        elif hasattr(result, "__dict__"):
            data = result.__dict__
        else:
            data = {"raw": str(result)}

        return ApiResponse(success=True, message="新聞分析完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"新聞分析失敗: {exc}")


# ── PreTrade ──────────────────────────────────────────────────────────────────


@app.post("/api/v1/pretrade", response_model=ApiResponse, tags=["trading"])
async def pretrade_check(req: PreTradeRequest):
    """進場前檢查"""
    try:
        from bioneuronai.trading.pretrade_automation import PreTradeCheckSystem

        checker = PreTradeCheckSystem()
        result = await asyncio.to_thread(
            checker.execute_pretrade_check,
            symbol=req.symbol,
            action=req.action,
        )

        if isinstance(result, dict):
            data = result
        elif hasattr(result, "model_dump"):
            data = result.model_dump()
        elif hasattr(result, "__dict__"):
            data = result.__dict__
        else:
            data = {"raw": str(result)}

        return ApiResponse(success=True, message="進場前檢查完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"進場前檢查失敗: {exc}")


# ── Backtest (background job) ─────────────────────────────────────────────────


@app.post("/api/v1/backtest", response_model=JobStatus, tags=["backtest"])
async def start_backtest(req: BacktestRequest):
    """啟動回測（背景任務）"""
    job_id = str(uuid.uuid4())[:8]
    job = JobStatus(job_id=job_id, status="pending")
    _jobs[job_id] = job

    asyncio.create_task(_run_backtest(job_id, req))
    return job


async def _run_backtest(job_id: str, req: BacktestRequest):
    job = _jobs[job_id]
    job.status = "running"
    try:
        from backtest import BacktestEngine
        from bioneuronai.core.trading_engine import TradingEngine

        def _execute():
            te = None
            try:
                te = TradingEngine(testnet=True)
            except Exception:
                pass

            engine = BacktestEngine(
                symbol=req.symbol,
                interval=req.interval,
                start_date=req.start_date,
                end_date=req.end_date,
                initial_balance=req.balance,
            )

            def ai_strategy(bar, connector):
                if te is None or not (te.inference_engine and te.ai_model_loaded):
                    return
                klines = connector.data_stream.get_klines_until_now(100)
                if not klines or len(klines) < 20:
                    return
                try:
                    signal = te.inference_engine.predict(
                        symbol=bar.symbol, current_price=bar.close, klines=klines,
                    )
                    pos = next(
                        (p for p in connector.get_account_info()["positions"]
                         if p["symbol"] == bar.symbol and abs(p["positionAmt"]) > 0),
                        None,
                    )
                    sig_str = signal.signal_type.value
                    if "long" in sig_str and (not pos or float(pos["positionAmt"]) <= 0):
                        if pos and float(pos["positionAmt"]) < 0:
                            connector.place_order(bar.symbol, "BUY", "MARKET", abs(float(pos["positionAmt"])))
                        connector.place_order(bar.symbol, "BUY", "MARKET", 0.05)
                    elif "short" in sig_str and (not pos or float(pos["positionAmt"]) >= 0):
                        if pos and float(pos["positionAmt"]) > 0:
                            connector.place_order(bar.symbol, "SELL", "MARKET", float(pos["positionAmt"]))
                        connector.place_order(bar.symbol, "SELL", "MARKET", 0.05)
                except Exception:
                    pass

            result = engine.run(ai_strategy)
            return {
                attr: getattr(result, attr, None)
                for attr in ("total_return", "sharpe_ratio", "max_drawdown", "win_rate", "total_trades")
                if getattr(result, attr, None) is not None
            }

        data = await asyncio.to_thread(_execute)
        job.status = "completed"
        job.result = data
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


# ── Simulate (background job) ────────────────────────────────────────────────


@app.post("/api/v1/simulate", response_model=JobStatus, tags=["backtest"])
async def start_simulate(req: SimulateRequest):
    """啟動模擬交易（背景任務）"""
    job_id = str(uuid.uuid4())[:8]
    job = JobStatus(job_id=job_id, status="pending")
    _jobs[job_id] = job

    asyncio.create_task(_run_simulate(job_id, req))
    return job


async def _run_simulate(job_id: str, req: SimulateRequest):
    job = _jobs[job_id]
    job.status = "running"
    try:
        from backtest import MockBinanceConnector

        def _execute():
            te = None
            try:
                from bioneuronai.core.trading_engine import TradingEngine
                te = TradingEngine(testnet=True)
            except Exception:
                pass

            mock = MockBinanceConnector(
                symbol=req.symbol,
                interval=req.interval,
                initial_balance=req.balance,
                start_date=req.start_date,
                end_date=req.end_date,
            )

            bar_count = 0
            while mock.next_tick() and bar_count < req.bars:
                bar = mock._current_bar
                if bar is None:
                    continue
                bar_count += 1

                if te and te.inference_engine and te.ai_model_loaded:
                    try:
                        klines = mock.data_stream.get_klines_until_now(50)
                        te.inference_engine.predict(
                            symbol=bar.symbol, current_price=bar.close, klines=klines,
                        )
                    except Exception:
                        pass

            acct = mock.get_account_info()
            final_balance = float(acct.get("totalWalletBalance", req.balance))
            pnl = final_balance - req.balance
            stats = mock.virtual_account.get_stats() if hasattr(mock, "virtual_account") else {}

            return {
                "final_balance": final_balance,
                "pnl": pnl,
                "total_return_pct": stats.get("total_return", 0),
                "total_trades": stats.get("total_trades", 0),
                "win_rate": stats.get("win_rate", 0),
                "bars_processed": bar_count,
            }

        data = await asyncio.to_thread(_execute)
        job.status = "completed"
        job.result = data
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


# ── Job Status ────────────────────────────────────────────────────────────────


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatus, tags=["system"])
async def get_job_status(job_id: str):
    """查詢背景任務狀態"""
    if job_id not in _jobs:
        return JobStatus(job_id=job_id, status="not_found", error="Job not found")
    return _jobs[job_id]


# ── Trade Control ─────────────────────────────────────────────────────────────

_trade_task = None
_trade_engine = None


@app.post("/api/v1/trade/start", response_model=ApiResponse, tags=["trading"])
async def start_trade(req: TradeStartRequest):
    """啟動交易監控"""
    global _trade_task, _trade_engine

    if _trade_task and not _trade_task.done():
        return ApiResponse(success=False, message="交易已在運行中")

    try:
        from bioneuronai.core.trading_engine import TradingEngine

        _trade_engine = TradingEngine(testnet=req.testnet)

        async def _monitor():
            await asyncio.to_thread(_trade_engine.start_monitoring, req.symbol)

        _trade_task = asyncio.create_task(_monitor())
        mode = "測試網" if req.testnet else "正式網"
        return ApiResponse(success=True, message=f"交易監控已啟動 [{mode}] {req.symbol}")
    except Exception as exc:
        return ApiResponse(success=False, message=f"交易啟動失敗: {exc}")


@app.post("/api/v1/trade/stop", response_model=ApiResponse, tags=["trading"])
async def stop_trade():
    """停止交易監控"""
    global _trade_task, _trade_engine

    if _trade_task and not _trade_task.done():
        _trade_task.cancel()
        _trade_task = None

    if _trade_engine and hasattr(_trade_engine, "stop_monitoring"):
        try:
            _trade_engine.stop_monitoring()
        except Exception:
            pass

    _trade_engine = None
    return ApiResponse(success=True, message="交易監控已停止")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _safe_serialize(obj) -> dict:
    """將任意對象安全轉為 dict"""
    if isinstance(obj, dict):
        return {k: _safe_value(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
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
