# -*- coding: utf-8 -*-
"""Analysis routes."""

import asyncio
from typing import Any, Dict

from fastapi import APIRouter

from bioneuronai.api.models import ApiResponse, NewsRequest
from bioneuronai.api.serialization import safe_serialize

router = APIRouter()


@router.post("/api/v1/news", response_model=ApiResponse, tags=["analysis"])
async def analyze_news(req: NewsRequest):
    """新聞情緒分析"""
    try:
        from bioneuronai.analysis import CryptoNewsAnalyzer

        analyzer = CryptoNewsAnalyzer()
        result = await asyncio.to_thread(analyzer.analyze_news, req.symbol)

        if isinstance(result, dict):
            data: Dict[str, Any] = result
        elif hasattr(result, "model_dump"):
            data = safe_serialize(result)
        elif hasattr(result, "__dict__"):
            data = safe_serialize(result)
        else:
            data = {"raw": str(result)}

        return ApiResponse(success=True, message="新聞分析完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"新聞分析失敗: {exc}")
