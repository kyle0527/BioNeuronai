# -*- coding: utf-8 -*-
"""System and credential validation routes."""

import importlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter

from bioneuronai.api.models import (
    ApiResponse,
    BinanceValidateRequest,
    ModuleStatus,
    StatusResponse,
)

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]


@router.get("/", tags=["root"])
async def root():
    return {"service": "BioNeuronai API", "version": "2.1", "docs": "/docs", "backtest_ui": "/backtest/ui"}


@router.get("/api/v1/status", response_model=StatusResponse, tags=["system"])
async def get_status():
    """系統健康狀態檢查與本機 runtime readiness。"""
    checks = [
        ("bioneuronai.core.trading_engine", "TradingEngine", "TradingEngine"),
        ("bioneuronai.data.binance_futures", "BinanceFuturesConnector", "BinanceFutures"),
        ("bioneuronai.analysis", "CryptoNewsAnalyzer", "NewsAnalyzer"),
        ("bioneuronai.analysis.daily_report", "SOPAutomationSystem", "SOPSystem"),
        ("bioneuronai.planning.pretrade_automation", "PreTradeCheckSystem", "PreTradeCheck"),
    ]

    modules = []
    for module_path, class_name, label in checks:
        modules.append(_import_status(module_path, class_name, label, "module", required=True))

    readiness = _build_readiness()
    all_items = modules + readiness
    blocking = [item.name for item in all_items if item.required and not item.available]
    all_ok = not blocking

    import bioneuronai

    return StatusResponse(
        modules=modules,
        version=getattr(bioneuronai, "__version__", None),
        all_ok=all_ok,
        ready=all_ok,
        blocking=blocking,
        readiness=readiness,
    )


def _import_status(
    module_path: str,
    class_name: str,
    label: str,
    category: str,
    *,
    required: bool,
) -> ModuleStatus:
    try:
        mod = importlib.import_module(module_path)
        getattr(mod, class_name)
        return ModuleStatus(name=label, available=True, category=category, required=required)
    except Exception as exc:
        return ModuleStatus(
            name=label,
            available=False,
            error=str(exc),
            category=category,
            required=required,
        )


def _check_item(
    name: str,
    category: str,
    required: bool,
    fn: Callable[[], dict[str, Any] | None],
) -> ModuleStatus:
    try:
        details = fn() or {}
        return ModuleStatus(
            name=name,
            available=True,
            category=category,
            required=required,
            details=details,
        )
    except Exception as exc:
        return ModuleStatus(
            name=name,
            available=False,
            error=str(exc),
            category=category,
            required=required,
        )


def _build_readiness() -> list[ModuleStatus]:
    return [
        _check_item("Python 3.13 runtime", "runtime", True, _check_python_runtime),
        _check_item("PyTorch import", "runtime", True, _check_torch_runtime),
        _check_item("Active trading model", "model", True, _check_active_model),
        _check_item("TinyLLM chat model", "model", True, _check_chat_model),
        _check_item("Event rules config", "config", True, lambda: _check_file("config/event_rules.json")),
        _check_item("Risk config", "config", True, lambda: _check_file("config/risk_config_optimized.json")),
        _check_item("Readiness gate config", "config", True, lambda: _check_file("config/trading_readiness_gate.json")),
        _check_item("Binance public market data", "external", False, _check_binance_public_data),
    ]


def _check_python_runtime() -> dict[str, Any]:
    major, minor = sys.version_info[:2]
    if (major, minor) != (3, 13):
        raise RuntimeError(f"expected Python 3.13, got {major}.{minor}")
    return {
        "version": sys.version.split()[0],
        "executable": sys.executable,
        "platform": platform.platform(),
    }


def _check_torch_runtime() -> dict[str, Any]:
    import torch

    return {
        "version": getattr(torch, "__version__", "unknown"),
        "cuda_available": bool(torch.cuda.is_available()),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
    }


def _check_active_model() -> dict[str, Any]:
    config_path = PROJECT_ROOT / "config" / "active_model.json"
    if not config_path.exists():
        raise FileNotFoundError(str(config_path))
    data = json.loads(config_path.read_text(encoding="utf-8"))
    model_path = data.get("materialized_path") or data.get("model_path")
    if not model_path:
        raise RuntimeError("active_model.json missing materialized_path/model_path")
    resolved = Path(model_path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    if not resolved.exists():
        raise FileNotFoundError(str(resolved))
    return {
        "model_name": data.get("model_name"),
        "path": str(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def _check_chat_model() -> dict[str, Any]:
    model_path = PROJECT_ROOT / "model" / "tiny_llm_100m.pth"
    if not model_path.exists():
        raise FileNotFoundError(str(model_path))
    return {"path": str(model_path), "size_bytes": model_path.stat().st_size}


def _check_file(relative_path: str) -> dict[str, Any]:
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(str(path))
    return {"path": str(path), "size_bytes": path.stat().st_size}


def _check_binance_public_data() -> dict[str, Any]:
    from bioneuronai.data.binance_futures import BinanceFuturesConnector

    connector = BinanceFuturesConnector(testnet=False)
    ticker = connector.get_ticker_price("BTCUSDT")
    if ticker is None:
        raise RuntimeError("BTCUSDT ticker unavailable")
    return {"symbol": "BTCUSDT", "source": "binance_futures_public"}


@router.post("/api/v1/binance/validate", response_model=ApiResponse, tags=["system"])
async def validate_binance_credentials(req: BinanceValidateRequest):
    """驗證 Binance API 憑證是否有效（讀取權限 + Futures 可用性）"""
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

        price_data = connector.get_ticker_price("BTCUSDT")
        if price_data is None:
            return ApiResponse(success=False, message="無法連線至 Binance，請檢查網路或 testnet 設定。")

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
