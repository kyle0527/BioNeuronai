# -*- coding: utf-8 -*-
"""System and credential validation routes."""

import os

from fastapi import APIRouter

from bioneuronai.api.models import (
    ApiResponse,
    BinanceValidateRequest,
    ModuleStatus,
    StatusResponse,
)

router = APIRouter()


@router.get("/", tags=["root"])
async def root():
    return {"service": "BioNeuronai API", "version": "2.1", "docs": "/docs", "backtest_ui": "/backtest/ui"}


@router.get("/api/v1/status", response_model=StatusResponse, tags=["system"])
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
