# -*- coding: utf-8 -*-
"""Backtest and replay routes."""

import asyncio

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from bioneuronai.api.models import (
    ApiResponse,
    BacktestRequest,
    SimulateRequest,
    StrategyBacktestRequest,
)

router = APIRouter()


@router.get("/api/v1/backtest/catalog", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_catalog(symbol: str | None = None, interval: str | None = None):
    """列出可用的歷史回放資料。"""
    try:
        from backtest import get_catalog

        data = await asyncio.to_thread(get_catalog, None, symbol, interval)
        return ApiResponse(success=True, message="歷史資料掃描完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"歷史資料掃描失敗: {exc}")


@router.get("/api/v1/backtest/inspect", response_model=ApiResponse, tags=["backtest"])
async def inspect_backtest_dataset(
    symbol: str = "ETHUSDT",
    interval: str = "1h",
    start_date: str | None = None,
    end_date: str | None = None,
):
    """檢視指定資料集是否可被 replay 層載入。"""
    try:
        from backtest import DEFAULT_DATA_DIR, HistoricalDataStream

        stream = await asyncio.to_thread(
            HistoricalDataStream,
            DEFAULT_DATA_DIR,
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


@router.post("/api/v1/backtest/simulate", response_model=ApiResponse, tags=["backtest"])
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


@router.post("/api/v1/backtest/run", response_model=ApiResponse, tags=["backtest"])
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


@router.post("/api/v1/backtest/strategy-run", response_model=ApiResponse, tags=["backtest"])
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


@router.get("/api/v1/backtest/runs", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_runs(limit: int = 10):
    """列出 replay runtime runs。"""
    try:
        from backtest import list_runtime_runs

        data = await asyncio.to_thread(list_runtime_runs, limit)
        return ApiResponse(success=True, message="replay runs 讀取完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"replay runs 讀取失敗: {exc}")


@router.get("/api/v1/backtest/runs/{run_id}", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_run(run_id: str):
    """讀取指定 replay runtime run。"""
    try:
        from backtest import get_runtime_run

        data = await asyncio.to_thread(get_runtime_run, run_id)
        return ApiResponse(success=True, message="replay run 讀取完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"replay run 讀取失敗: {exc}")


@router.get("/backtest/ui", response_class=HTMLResponse, tags=["backtest"])
async def backtest_ui():
    """最小可用 backtest UI。"""
    from backtest import load_backtest_ui_html

    return HTMLResponse(load_backtest_ui_html())
