# -*- coding: utf-8 -*-
"""Chat routes."""

import asyncio
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter

from bioneuronai.api.models import ApiResponse
from schemas.api import ChatRequest, ChatResponse

_chat_engines: dict[str, Any] = {}
_default_chat_engine: Any = None


def _get_chat_engine(conversation_id: str, language: str = "auto", logger: Any = None) -> Any:
    """取得或建立對應 conversation_id 的 ChatEngine。"""
    global _default_chat_engine
    if conversation_id not in _chat_engines:
        if _default_chat_engine is None:
            try:
                from nlp.chat_engine import create_chat_engine

                _default_chat_engine = create_chat_engine(language=language)
            except Exception as exc:
                if logger is not None:
                    logger.warning("[Chat] ChatEngine 初始化失敗: %s", exc)
                return None
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

        engine = _get_chat_engine(conv_id, req.language, logger)
        if engine is None:
            return ChatResponse(
                success=False,
                text="對話引擎未初始化，請確認模型已訓練並存放至 model/ 目錄。"
                     " (Chat engine not initialized. Please ensure the model is trained and placed in model/.)",
                language=req.language if req.language != "auto" else "zh",
                conversation_id=conv_id,
            )

        if req.language != "auto":
            engine.set_language(req.language)

        market_ctx = None
        if req.symbol:
            try:
                from nlp.chat_engine import MarketContext

                ctx = MarketContext(symbol=req.symbol)
                price = await trade_manager.get_current_price(req.symbol)
                if price is not None:
                    ctx.current_price = price
                market_ctx = ctx
            except Exception as exc:
                logger.debug("[Chat] 市場上下文取得失敗（不影響對話）: %s", exc)

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
