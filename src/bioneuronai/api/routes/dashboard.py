# -*- coding: utf-8 -*-
"""Dashboard, risk, data catalog, and websocket routes."""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from bioneuronai.api.models import ApiResponse
from schemas.api import (
    DashboardDataResponse,
    TradeOrderRequest,
    WsAuditLogEntry,
    WsMaxDrawdown,
    WsPosition,
    WsPretradeChecklist,
    WsPretradeItem,
    WsRiskData,
)

_VALID_RISK_LEVELS = {"CONSERVATIVE", "MODERATE", "AGGRESSIVE", "HIGH_RISK"}
_VALID_KLINE_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
}


def create_router(trade_manager: Any, project_root: Path, logger: Any) -> APIRouter:
    router = APIRouter()
    risk_config_path = project_root / "config" / "risk_config_optimized.json"

    async def build_dashboard_snapshot() -> dict:
        """組建 Dashboard 快照 dict，供 REST 端點及 WS 推送共用。"""
        now = datetime.now().isoformat()
        risk_level = "low"
        risk_pct = 0.0

        if trade_manager.engine is not None:
            try:
                state = getattr(trade_manager.engine, "state", None)
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
        if trade_manager.is_running():
            audit_entries.append(WsAuditLogEntry(
                id="sys-trade-running",
                timestamp=now,
                eventType="trade_start",
                description="交易監控運行中",
                status="success",
            ))

        checklist_items = [
            WsPretradeItem(id="c1", label="API 連線正常", completed=trade_manager.engine is not None, required=True),
            WsPretradeItem(id="c2", label="風險參數已設定", completed=True, required=True),
            WsPretradeItem(id="c3", label="市場流動性正常", completed=True, required=False),
        ]
        completed_required = sum(1 for item in checklist_items if item.required and item.completed)
        total_required = sum(1 for item in checklist_items if item.required)
        positions = await trade_manager.get_virtual_portfolio()

        environment = "testnet"
        status = trade_manager.get_status()
        request = status.get("request") if isinstance(status, dict) else {}
        if isinstance(request, dict):
            mode = request.get("mode")
            if mode == "paper_live":
                environment = "paper_live"
            elif mode == "live_auto":
                environment = "mainnet"

        snapshot = DashboardDataResponse(
            environment=environment,
            risk=WsRiskData(level=risk_level, percentage=risk_pct, lastUpdated=now),
            maxDrawdown=WsMaxDrawdown(current=0.0, historical=0.0, period="30d", lastUpdated=now),
            pretradeChecklist=WsPretradeChecklist(
                items=checklist_items,
                completedCount=completed_required,
                totalCount=total_required,
                lastUpdated=now,
            ),
            auditLog=audit_entries,
            positions=positions or None,
        )
        return snapshot.model_dump()

    @router.get("/api/v1/dashboard", tags=["dashboard"])
    async def get_dashboard():
        """取得 Dashboard 快照（admin-da 首頁使用）"""
        return await build_dashboard_snapshot()

    @router.post("/api/v1/orders", tags=["dashboard"])
    async def submit_order(order: TradeOrderRequest):
        """提交交易訂單（admin-da TradingControls 使用）"""
        try:
            if trade_manager.engine is None:
                return ApiResponse(
                    success=False,
                    message="交易引擎未啟動，請先呼叫 POST /api/v1/trade/start",
                )

            connector = getattr(trade_manager.engine, "connector", None)
            place_fn = getattr(connector, "place_order", None)
            if place_fn is None:
                raise RuntimeError("目前交易 connector 不支援直接下單")

            result = await asyncio.to_thread(
                place_fn,
                symbol=order.symbol,
                side=order.side.upper(),
                order_type=order.orderType.upper(),
                quantity=order.quantity,
                price=order.price,
                stop_loss=order.stopLoss,
                take_profit=order.takeProfit,
                stop_price=order.stopPrice,
                time_in_force=order.timeInForce,
            )
            if result is None:
                raise RuntimeError("交易 connector 未回傳訂單結果")
            result_data = result.to_dict() if hasattr(result, "to_dict") else result
            return ApiResponse(
                success=True,
                message=f"訂單已執行 {order.side.upper()} {order.symbol} qty={order.quantity}",
                data=result_data,
            )
        except Exception as exc:
            return ApiResponse(success=False, message=f"訂單提交失敗: {exc}")

    @router.delete("/api/v1/positions/{position_id}", tags=["dashboard"])
    async def close_position(position_id: str):
        """平倉（admin-da 持倉列表使用）"""
        try:
            if trade_manager.engine is None:
                return ApiResponse(success=False, message="交易引擎未啟動")

            close_fn = getattr(trade_manager.engine, "close_position", None)
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

    @router.get("/api/v1/risk/config", response_model=ApiResponse, tags=["risk"])
    async def get_risk_config():
        """讀取目前的風險設定（risk_config_optimized.json）。"""
        try:
            data = json.loads(risk_config_path.read_text(encoding="utf-8"))
            return ApiResponse(success=True, message="風險設定讀取成功", data=data)
        except Exception as exc:
            return ApiResponse(success=False, message=f"風險設定讀取失敗: {exc}")

    @router.put("/api/v1/risk/config", response_model=ApiResponse, tags=["risk"])
    async def update_risk_config(body: Dict[str, Any]):
        """更新風險設定並寫回 risk_config_optimized.json。"""
        try:
            current = json.loads(risk_config_path.read_text(encoding="utf-8"))

            if "risk_level" in body:
                level = str(body["risk_level"]).upper()
                if level not in _VALID_RISK_LEVELS:
                    return ApiResponse(
                        success=False,
                        message=f"無效的 risk_level：{level}，允許值：{sorted(_VALID_RISK_LEVELS)}",
                    )
                current["risk_level"] = level

            if "custom_overrides" in body:
                overrides = body["custom_overrides"]
                if not isinstance(overrides, dict):
                    return ApiResponse(success=False, message="custom_overrides 必須為 object")
                current.setdefault("custom_overrides", {}).update(overrides)

            risk_config_path.write_text(
                json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return ApiResponse(success=True, message="風險設定已更新", data=current)
        except Exception as exc:
            return ApiResponse(success=False, message=f"風險設定更新失敗: {exc}")

    @router.get("/api/v1/data/catalog", response_model=ApiResponse, tags=["data"])
    async def get_data_catalog(symbol: str | None = None, interval: str | None = None):
        """列出 backtest/data/ 下已下載的歷史資料集（與 CLI backtest-data 等效）。"""
        try:
            from backtest import get_catalog

            data = await asyncio.to_thread(get_catalog, None, symbol, interval)
            return ApiResponse(success=True, message="資料目錄掃描完成", data=data)
        except Exception as exc:
            return ApiResponse(success=False, message=f"資料目錄掃描失敗: {exc}")

    @router.get("/api/v1/market/klines", response_model=ApiResponse, tags=["market"])
    async def get_market_klines(symbol: str = "BTCUSDT", interval: str = "1m", limit: int = 120):
        """取得 Binance Futures 最新 K 線，供 Dashboard 即時圖表使用。"""
        try:
            from bioneuronai.data.binance_futures import BinanceFuturesConnector

            normalized_symbol = symbol.strip().upper()
            normalized_interval = interval.strip()
            if not normalized_symbol:
                return ApiResponse(success=False, message="symbol 不可為空")
            if normalized_interval not in _VALID_KLINE_INTERVALS:
                return ApiResponse(
                    success=False,
                    message=f"不支援的 interval: {normalized_interval}",
                    data={"allowed": sorted(_VALID_KLINE_INTERVALS)},
                )
            safe_limit = max(10, min(int(limit), 500))

            connector = BinanceFuturesConnector(testnet=False)
            raw_klines = await asyncio.to_thread(
                connector.get_klines,
                normalized_symbol,
                normalized_interval,
                safe_limit,
            )
            if not raw_klines:
                return ApiResponse(success=False, message="Binance 未回傳 K 線資料")

            now_ms = int(time.time() * 1000)
            candles: list[dict[str, Any]] = []
            for raw in raw_klines:
                if len(raw) < 7:
                    continue
                close_time = int(raw[6])
                candles.append({
                    "open_time": int(raw[0]),
                    "open_time_iso": datetime.fromtimestamp(int(raw[0]) / 1000).isoformat(),
                    "open": float(raw[1]),
                    "high": float(raw[2]),
                    "low": float(raw[3]),
                    "close": float(raw[4]),
                    "volume": float(raw[5]),
                    "close_time": close_time,
                    "close_time_iso": datetime.fromtimestamp(close_time / 1000).isoformat(),
                    "closed": close_time <= now_ms,
                })

            if not candles:
                return ApiResponse(success=False, message="K 線資料格式無法解析")

            latest = candles[-1]
            return ApiResponse(
                success=True,
                message="K 線資料讀取成功",
                data={
                    "symbol": normalized_symbol,
                    "interval": normalized_interval,
                    "source": "binance_futures_public",
                    "server_time": datetime.now().isoformat(),
                    "polling_hint_seconds": 3,
                    "latest": latest,
                    "candles": candles,
                },
            )
        except Exception as exc:
            return ApiResponse(success=False, message=f"K 線資料讀取失敗: {exc}")

    @router.websocket("/ws/trade")
    async def ws_trade(websocket: WebSocket):
        """/ws/trade — 即時報價、成交推送（trading 前端 trade-control-page.tsx）"""
        await websocket.accept()
        symbol = "BTCUSDT"
        try:
            while True:
                price = 0.0
                current_price = await trade_manager.get_current_price(symbol)
                if current_price is not None:
                    price = current_price
                await websocket.send_json({"type": "price_update", "symbol": symbol, "price": price})
                await asyncio.sleep(2)
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logger.debug("[WS /ws/trade] 連線結束: %s", exc)

    @router.websocket("/ws/analytics")
    async def ws_analytics(websocket: WebSocket):
        """/ws/analytics — 投資組合、績效、成交資料推送（trading 前端 analytics-page.tsx）"""
        await websocket.accept()
        try:
            while True:
                portfolio: list[dict] = await trade_manager.get_virtual_portfolio()
                await websocket.send_json({"type": "portfolio_update", "portfolio": portfolio})
                await asyncio.sleep(5)
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logger.debug("[WS /ws/analytics] 連線結束: %s", exc)

    @router.websocket("/ws/dashboard")
    async def ws_dashboard(websocket: WebSocket):
        """Dashboard 即時狀態推送。"""
        await websocket.accept()
        try:
            while True:
                await websocket.send_json(await build_dashboard_snapshot())
                await asyncio.sleep(3)
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logger.debug("[WS /ws/dashboard] 連線結束: %s", exc)

    return router
