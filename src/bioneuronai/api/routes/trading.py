# -*- coding: utf-8 -*-
"""Pretrade and trade-control routes."""

import asyncio
from typing import Any

from fastapi import APIRouter

from bioneuronai.api.models import ApiResponse, PreTradeRequest, TradeStartRequest
from bioneuronai.api.serialization import safe_serialize


def create_router(trade_manager: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/pretrade", response_model=ApiResponse, tags=["trading"])
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
                data = safe_serialize(result)
            elif hasattr(result, "__dict__"):
                data = safe_serialize(result)
            else:
                data = {"raw": str(result)}

            return ApiResponse(success=True, message="進場前檢查完成", data=data)
        except Exception as exc:
            return ApiResponse(success=False, message=f"進場前檢查失敗: {exc}")

    @router.post("/api/v1/trade/start", response_model=ApiResponse, tags=["trading"])
    async def start_trade(req: TradeStartRequest):
        """啟動交易監控"""
        if trade_manager.is_running():
            return ApiResponse(success=False, message="交易已在運行中")

        try:
            data = await trade_manager.start(req)
            environment = data.get("environment", "未知環境")
            return ApiResponse(
                success=True,
                message=f"交易監控已啟動 [{environment}] {req.symbol}",
                data=data,
            )
        except Exception as exc:
            return ApiResponse(success=False, message=f"交易啟動失敗: {exc}")

    @router.get("/api/v1/trade/status", response_model=ApiResponse, tags=["trading"])
    async def trade_status():
        """取得交易監控與自動交易狀態。"""
        return ApiResponse(success=True, message="交易狀態查詢完成", data=trade_manager.get_status())

    @router.post("/api/v1/trade/stop", response_model=ApiResponse, tags=["trading"])
    async def stop_trade():
        """停止交易監控"""
        await trade_manager.stop()
        return ApiResponse(success=True, message="交易監控已停止", data=trade_manager.get_status())

    return router
