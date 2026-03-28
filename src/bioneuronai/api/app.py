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
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

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
    ModuleStatus,
    NewsRequest,
    PreTradeRequest,
    StatusResponse,
    TradeStartRequest,
)

logger = logging.getLogger(__name__)


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
    version="4.1.0",
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
    return {"service": "BioNeuronai API", "version": "4.1.0", "docs": "/docs"}


# ── Status ────────────────────────────────────────────────────────────────────


@app.get("/api/v1/status", response_model=StatusResponse, tags=["system"])
async def get_status():
    """系統健康狀態檢查"""
    checks = [
        ("bioneuronai.core.trading_engine", "TradingEngine", "TradingEngine"),
        ("bioneuronai.data.binance_futures", "BinanceFuturesConnector", "BinanceFutures"),
        ("bioneuronai.analysis", "CryptoNewsAnalyzer", "NewsAnalyzer"),
        ("bioneuronai.trading.sop_automation", "SOPAutomationSystem", "SOPSystem"),
        ("bioneuronai.trading.pretrade_automation", "PreTradeCheckSystem", "PreTradeCheck"),
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
async def validate_binance_credentials(req: TradeStartRequest):
    """驗證 Binance API 憑證是否有效（讀取權限 + Futures 可用性）

    憑證優先順序：請求體 api_key/api_secret → 環境變數 → config fallback。
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
        price_data = connector.get_ticker_price(req.symbol)
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

_trade_task = None
_trade_engine = None


@app.post("/api/v1/trade/start", response_model=ApiResponse, tags=["trading"])
async def start_trade(req: TradeStartRequest):
    """啟動交易監控"""
    global _trade_task, _trade_engine

    if _trade_task and not _trade_task.done():
        return ApiResponse(success=False, message="交易已在運行中")

    try:
        import os
        from bioneuronai.core.trading_engine import TradingEngine

        # 憑證優先順序：請求注入 → 環境變數
        api_key = req.api_key or os.getenv("BINANCE_API_KEY", "")
        api_secret = req.api_secret or os.getenv("BINANCE_API_SECRET", "")

        _trade_engine = TradingEngine(
            api_key=api_key,
            api_secret=api_secret,
            testnet=req.testnet,
        )

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
