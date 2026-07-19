# -*- coding: utf-8 -*-
"""Chat routes."""

import asyncio
import re
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter

from bioneuronai.api.models import ApiResponse
from schemas.api import ChatRequest, ChatResponse, TradeStartRequest

_chat_engines: dict[str, Any] = {}
_default_chat_engine: Any = None

_SYMBOL_RE = re.compile(r"\b([A-Z]{2,12}USDT)\b", re.IGNORECASE)
_ZH_RE = re.compile(r"[\u4e00-\u9fff]")

_ANALYZE_TERMS = (
    "分析", "判斷", "適合", "做多", "做空", "行情", "走勢", "風險",
    "analyze", "analysis", "market", "long", "short", "risk",
)
_STATUS_TERMS = ("交易狀態", "監控狀態", "系統狀態", "程式情況", "status", "running", "目前程式")
_STOP_TERMS = ("停止交易", "停止監控", "停止自動", "stop trading", "stop monitor", "停止")
_START_PAPER_TERMS = (
    "paper_live", "paper live", "虛擬實盤", "模擬實盤", "紙上交易",
    "啟動虛擬", "開始虛擬", "start paper", "start virtual",
)
_PORTFOLIO_TERMS = ("持倉", "部位", "帳戶", "portfolio", "position", "positions", "account")
_PRETRADE_TERMS = ("進場前", "交易前", "pretrade", "pre-trade", "風控檢查")
_LIVE_TERMS = ("live_auto", "正式網", "真實下單", "真倉", "real money", "live trading")
_TESTNET_TERMS = ("testnet_auto", "測試網自動", "testnet auto")


def _ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    alpha = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for value in values[period:]:
        ema = value * alpha + ema * (1 - alpha)
    return float(ema)


def _rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for prev, cur in zip(values[-period - 1:-1], values[-period:]):
        delta = cur - prev
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _resolve_language(req: ChatRequest) -> str:
    if req.language in {"zh", "en"}:
        return req.language
    return "zh" if _ZH_RE.search(req.message) else "en"


def _resolve_symbol(req: ChatRequest, default: str = "BTCUSDT") -> str:
    if req.symbol:
        return req.symbol.upper()
    match = _SYMBOL_RE.search(req.message.upper())
    return match.group(1).upper() if match else default


def _extract_balance(text: str, default: float = 10000.0) -> float:
    match = re.search(r"(?:balance|餘額|本金|資金)\D{0,12}(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not match:
        return default
    return max(1.0, float(match.group(1)))


def _detect_chat_action(message: str) -> str | None:
    if _contains_any(message, _LIVE_TERMS):
        return "refuse_live_auto"
    if _contains_any(message, _TESTNET_TERMS):
        return "refuse_testnet_auto"
    if _contains_any(message, _STOP_TERMS):
        return "stop_trading"
    if _contains_any(message, _START_PAPER_TERMS):
        return "start_paper_live"
    if _contains_any(message, _PRETRADE_TERMS):
        return "pretrade_check"
    if _contains_any(message, _STATUS_TERMS):
        return "trade_status"
    if _contains_any(message, _PORTFOLIO_TERMS):
        return "portfolio_status"
    if _contains_any(message, _ANALYZE_TERMS):
        return "analyze_market"
    return None


async def _load_public_market_snapshot(symbol: str, logger: Any) -> dict[str, Any]:
    """Load public Binance Futures data without requiring API keys."""
    from bioneuronai.data import BinanceFuturesConnector

    connector = BinanceFuturesConnector(testnet=False)
    ticker, stats, klines = await asyncio.gather(
        asyncio.to_thread(connector.get_ticker_price, symbol),
        asyncio.to_thread(connector.get_ticker_24hr, symbol),
        asyncio.to_thread(connector.get_klines, symbol, "1h", 120),
    )
    closes = [float(k[4]) for k in (klines or []) if len(k) > 4]
    if len(closes) < 50:
        raise RuntimeError(f"{symbol} 1h K 線不足，至少需要 50 根，實際 {len(closes)} 根")
    ema20 = _ema(closes, 20)
    ema50 = _ema(closes, 50)
    rsi14 = _rsi(closes, 14)
    price = float(getattr(ticker, "price", 0.0) or getattr(ticker, "close", 0.0) or 0.0)
    if not price and closes:
        price = closes[-1]
    if not price:
        raise RuntimeError(f"{symbol} 即時價格不可用")
    return {
        "price": price,
        "change_24h_pct": float((stats or {}).get("priceChangePercent", 0.0) or 0.0),
        "volume_24h": float((stats or {}).get("volume", 0.0) or 0.0),
        "rsi14": rsi14,
        "ema20": ema20,
        "ema50": ema50,
        "kline_count": len(closes),
    }


def _structured_market_reply(symbol: str, snapshot: dict[str, Any], language: str) -> str:
    price = float(snapshot.get("price") or 0.0)
    change = float(snapshot.get("change_24h_pct") or 0.0)
    rsi14 = snapshot.get("rsi14")
    ema20 = snapshot.get("ema20")
    ema50 = snapshot.get("ema50")
    kline_count = int(snapshot.get("kline_count") or 0)

    if not price:
        if language == "en":
            return "I cannot fetch enough live market data right now, so I will not provide a trade direction."
        return "目前無法取得足夠即時行情，因此不提供做多或做空方向。"

    trend = "neutral"
    if ema20 is not None and ema50 is not None:
        if ema20 > ema50:
            trend = "bullish"
        elif ema20 < ema50:
            trend = "bearish"

    if rsi14 is not None and rsi14 >= 70:
        stance = "不建議追多，偏向等待回落或更明確訊號"
        reason = "RSI 偏高，有追高風險"
    elif trend == "bullish" and change >= 0:
        stance = "可列入觀察，但不等於直接進場"
        reason = "短中期均線偏多，且 24h 漲跌幅未轉弱"
    elif trend == "bearish":
        stance = "暫不適合主動做多"
        reason = "1h EMA20 低於 EMA50，趨勢仍偏弱"
    else:
        stance = "偏觀望"
        reason = "目前方向訊號不夠明確"

    rsi_text = f"{rsi14:.1f}" if rsi14 is not None else "不足"
    ema_text = "不足"
    if ema20 is not None and ema50 is not None:
        ema_text = f"EMA20 {ema20:,.2f} / EMA50 {ema50:,.2f}"

    if language == "en":
        return (
            f"{symbol}: price {price:,.2f} USDT, 24h change {change:+.2f}%. "
            f"My structured view is: {stance}. Reason: {reason}. "
            f"1h data: RSI14 {rsi_text}, {ema_text}, candles {kline_count}. "
            "This is a market explanation, not an auto-trade signal; use paper_live or the trade engine signal before execution."
        )

    return (
        f"{symbol} 目前價格約 {price:,.2f} USDT，24h 漲跌幅 {change:+.2f}%。"
        f"結論：{stance}。主要原因：{reason}。"
        f"1h 資料：RSI14 {rsi_text}，{ema_text}，K 線數 {kline_count}。"
        "這是行情解釋，不是自動下單訊號；真正執行前仍要以 paper_live/交易引擎訊號與新聞風險閘門為準。"
    )


def _format_trade_status(status: dict[str, Any], language: str) -> str:
    engine = status.get("engine", {})
    request = status.get("request", {}) or {}
    if language == "en":
        return (
            f"Trading status: running={status.get('running')}, mode={status.get('mode')}, "
            f"symbol={request.get('symbol', 'N/A')}, auto_trade={engine.get('auto_trade')}, "
            f"AI loaded={engine.get('ai_model_loaded')}, paper={engine.get('paper_trading')}."
        )
    return (
        f"目前交易狀態：running={status.get('running')}，mode={status.get('mode')}，"
        f"symbol={request.get('symbol', 'N/A')}，auto_trade={engine.get('auto_trade')}，"
        f"AI loaded={engine.get('ai_model_loaded')}，paper={engine.get('paper_trading')}。"
    )


def _format_portfolio(positions: list[dict[str, Any]], language: str) -> str:
    if not positions:
        return "No open paper/live positions were found." if language == "en" else "目前沒有查到開放持倉。"
    if language == "en":
        lines = ["Current positions:"]
        for pos in positions:
            lines.append(
                f"- {pos.get('symbol')} {pos.get('side')} qty={pos.get('quantity')} "
                f"entry={pos.get('entryPrice')} pnl={pos.get('unrealizedPnl')}"
            )
        return "\n".join(lines)
    lines = ["目前持倉："]
    for pos in positions:
        lines.append(
            f"- {pos.get('symbol')} {pos.get('side')} 數量={pos.get('quantity')} "
            f"進場={pos.get('entryPrice')} 未實現損益={pos.get('unrealizedPnl')}"
        )
    return "\n".join(lines)


def _format_start_paper(status: dict[str, Any], language: str) -> str:
    symbol = (status.get("request") or {}).get("symbol", "N/A")
    if language == "en":
        return (
            f"Started paper_live for {symbol}. It uses Binance mainnet market data but keeps orders local "
            "in the virtual account. Live exchange orders are not sent."
        )
    return (
        f"已啟動 {symbol} 的 paper_live。這會使用 Binance 主網即時行情，但下單只寫入本機虛擬帳戶，"
        "不會送出真實 Binance 訂單。"
    )


def _format_refusal(action: str, language: str) -> str:
    if action == "refuse_live_auto":
        if language == "en":
            return "I will not start live_auto from chat. Use the dedicated trade control flow with the live confirmation guard."
        return "我不會從聊天直接啟動 live_auto。正式網交易必須走專用交易控制流程與二次確認。"
    if language == "en":
        return "I will not start testnet_auto from chat yet. Use the dedicated trade control flow so credentials and risk settings stay explicit."
    return "我目前不會從聊天直接啟動 testnet_auto。請走專用交易控制流程，讓憑證與風控設定保持明確。"


async def _run_pretrade_tool(symbol: str, message: str) -> dict[str, Any]:
    action = "short" if _contains_any(message, ("short", "sell", "做空", "空")) else "long"
    from bioneuronai.planning.pretrade_automation import PreTradeCheckSystem

    checker = PreTradeCheckSystem()
    result = await asyncio.to_thread(
        checker.execute_pretrade_check,
        symbol=symbol,
        intended_action=action,
    )
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "__dict__"):
        return dict(result.__dict__)
    return {"raw": str(result)}


def _tool_response(
    *,
    text: str,
    language: str,
    action: str,
    data: dict[str, Any] | None,
    latency_ms: float,
    conversation_id: str,
    confidence: float = 0.85,
    market_context_used: bool = False,
) -> ChatResponse:
    return ChatResponse(
        success=True,
        text=text,
        language=language,
        confidence=confidence,
        market_context_used=market_context_used,
        stopped_reason="tool_call",
        action=action,
        tool_calls=[{"name": action, "success": True}],
        structured_data=data,
        latency_ms=latency_ms,
        conversation_id=conversation_id,
    )


async def _handle_chat_tool(
    req: ChatRequest,
    trade_manager: Any,
    logger: Any,
    language: str,
    conversation_id: str,
    started_at: float,
    market_snapshot: dict[str, Any],
) -> ChatResponse | None:
    action = _detect_chat_action(req.message)
    if action is None:
        return None

    symbol = _resolve_symbol(req)
    def latency() -> float:
        return (time.time() - started_at) * 1000

    if action in {"refuse_live_auto", "refuse_testnet_auto"}:
        return _tool_response(
            text=_format_refusal(action, language),
            language=language,
            action=action,
            data={"symbol": symbol, "allowed": False},
            latency_ms=latency(),
            conversation_id=conversation_id,
            confidence=1.0,
        )

    if action == "trade_status":
        status = trade_manager.get_status()
        return _tool_response(
            text=_format_trade_status(status, language),
            language=language,
            action=action,
            data=status,
            latency_ms=latency(),
            conversation_id=conversation_id,
            confidence=1.0,
        )

    if action == "portfolio_status":
        positions = await trade_manager.get_virtual_portfolio()
        return _tool_response(
            text=_format_portfolio(positions, language),
            language=language,
            action=action,
            data={"positions": positions},
            latency_ms=latency(),
            conversation_id=conversation_id,
            confidence=0.9,
        )

    if action == "stop_trading":
        await trade_manager.stop()
        status = trade_manager.get_status()
        return _tool_response(
            text=_format_trade_status(status, language),
            language=language,
            action=action,
            data=status,
            latency_ms=latency(),
            conversation_id=conversation_id,
            confidence=1.0,
        )

    if action == "start_paper_live":
        if trade_manager.is_running():
            status = trade_manager.get_status()
            text = _format_trade_status(status, language)
            return _tool_response(
                text=text,
                language=language,
                action=action,
                data=status,
                latency_ms=latency(),
                conversation_id=conversation_id,
                confidence=0.95,
            )
        req_start = TradeStartRequest(
            symbol=symbol,
            testnet=False,
            mode="paper_live",
            paper_initial_balance=_extract_balance(req.message),
            auto_trade=False,
            load_ai_model=True,
            model_name="unified_v2_100m",
            warmup_model=False,
        )
        status = await trade_manager.start(req_start)
        return _tool_response(
            text=_format_start_paper(status, language),
            language=language,
            action=action,
            data=status,
            latency_ms=latency(),
            conversation_id=conversation_id,
            confidence=0.95,
        )

    if action == "pretrade_check":
        data = await _run_pretrade_tool(symbol, req.message)
        summary = str(data.get("summary") or data.get("recommendation") or data.get("status") or data)[:800]
        text = f"Pretrade check for {symbol}: {summary}" if language == "en" else f"{symbol} 交易前檢查：{summary}"
        return _tool_response(
            text=text,
            language=language,
            action=action,
            data=data,
            latency_ms=latency(),
            conversation_id=conversation_id,
            confidence=0.8,
        )

    if action == "analyze_market":
        snapshot = market_snapshot or await _load_public_market_snapshot(symbol, logger)
        text = _structured_market_reply(symbol, snapshot, language)
        return _tool_response(
            text=text,
            language=language,
            action=action,
            data={"symbol": symbol, "market": snapshot},
            latency_ms=latency(),
            conversation_id=conversation_id,
            confidence=0.55,
            market_context_used=True,
        )

    return None


def _get_chat_engine(conversation_id: str, language: str = "auto", logger: Any = None) -> Any:
    """取得或建立對應 conversation_id 的 ChatEngine。"""
    global _default_chat_engine
    if conversation_id not in _chat_engines:
        if _default_chat_engine is None:
            from nlp.chat_engine import create_chat_engine

            _default_chat_engine = create_chat_engine(language=language)
        _chat_engines[conversation_id] = _default_chat_engine
    return _chat_engines.get(conversation_id)


def create_router(trade_manager: Any, logger: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/chat", response_model=ChatResponse, tags=["chat"])
    async def chat(req: ChatRequest):
        """
        雙語對話端點（繁體中文 / English）。

        - 自動偵測使用者語言，依語言回應
        - 傳入 symbol（如 BTCUSDT）時自動注入即時市場資料
        - 傳入相同 conversation_id 可維持多輪對話記憶
        """
        t0 = time.time()
        conv_id = req.conversation_id or str(uuid4())
        response_language = _resolve_language(req)

        try:
            tool_response = await _handle_chat_tool(
                req=req,
                trade_manager=trade_manager,
                logger=logger,
                language=response_language,
                conversation_id=conv_id,
                started_at=t0,
                market_snapshot={},
            )
            if tool_response is not None:
                return tool_response
        except Exception as exc:
            logger.error("[Chat] 工具指令執行失敗: %s", exc)
            return ChatResponse(
                success=False,
                text=f"工具指令執行失敗：{exc}",
                language=response_language,
                action=_detect_chat_action(req.message),
                stopped_reason="tool_error",
                conversation_id=conv_id,
            )

        try:
            engine = _get_chat_engine(conv_id, req.language, logger)
        except Exception as exc:
            logger.error("[Chat] ChatEngine 初始化失敗: %s", exc)
            return ChatResponse(
                success=False,
                text=f"對話引擎初始化失敗：{exc}",
                language=response_language,
                stopped_reason="engine_unavailable",
                conversation_id=conv_id,
            )
        if engine is not None and req.language != "auto":
            engine.set_language(req.language)

        market_ctx = None
        market_snapshot: dict[str, Any] = {}
        if req.symbol:
            try:
                from nlp.chat_engine import MarketContext

                ctx = MarketContext(symbol=req.symbol)
                price = await trade_manager.get_current_price(req.symbol)
                if price is None:
                    market_snapshot = await _load_public_market_snapshot(req.symbol, logger)
                    price = market_snapshot.get("price")
                if price is not None:
                    ctx.current_price = float(price)
                if market_snapshot:
                    ctx.price_change_24h_pct = float(market_snapshot.get("change_24h_pct") or 0.0)
                    if market_snapshot.get("rsi14") is not None:
                        ctx.indicators["RSI14_1h"] = round(float(market_snapshot["rsi14"]), 2)
                    if market_snapshot.get("ema20") is not None:
                        ctx.indicators["EMA20_1h"] = round(float(market_snapshot["ema20"]), 2)
                    if market_snapshot.get("ema50") is not None:
                        ctx.indicators["EMA50_1h"] = round(float(market_snapshot["ema50"]), 2)
                market_ctx = ctx
            except Exception as exc:
                logger.error("[Chat] 市場上下文取得失敗: %s", exc)
                return ChatResponse(
                    success=False,
                    text=f"市場上下文取得失敗：{exc}",
                    language=response_language,
                    stopped_reason="market_data_unavailable",
                    conversation_id=conv_id,
                )

        try:
            if engine is None:
                return ChatResponse(
                    success=False,
                    text="對話引擎未初始化，請確認模型已訓練並存放至 model/ 目錄。"
                         " (Chat engine not initialized. Please ensure the model is trained and placed in model/.)",
                    language=response_language,
                    conversation_id=conv_id,
                )

            response = await asyncio.to_thread(engine.chat, req.message, market_ctx)
            latency = (time.time() - t0) * 1000
            text = response.text
            confidence = response.confidence
            stopped_reason = response.stopped_reason
            return ChatResponse(
                success=True,
                text=text,
                language=response.language,
                confidence=confidence,
                market_context_used=response.market_context_used,
                stopped_reason=stopped_reason,
                latency_ms=latency,
                conversation_id=conv_id,
            )
        except Exception as exc:
            logger.error("[Chat] 對話生成失敗: %s", exc)
            return ChatResponse(
                success=False,
                text=f"生成失敗：{exc}",
                language="zh",
                conversation_id=conv_id,
            )

    @router.delete("/api/v1/chat/{conversation_id}", response_model=ApiResponse, tags=["chat"])
    async def reset_chat(conversation_id: str):
        """清除指定 conversation_id 的對話歷史"""
        engine = _chat_engines.get(conversation_id)
        if engine:
            engine.reset()
            return ApiResponse(success=True, message=f"對話歷史已清除 [{conversation_id}]")
        return ApiResponse(success=False, message="找不到該對話 ID")

    return router
