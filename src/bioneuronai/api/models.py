# -*- coding: utf-8 -*-
"""
API Request / Response Models

此檔案為向後相容的轉發層。
所有模型的主定義位於 src/schemas/api.py（單一事實來源）。
本模組僅負責從 schemas 重新導出，供 api/app.py 使用，維持現有 import 路徑不變。
"""

from schemas.api import (  # noqa: F401
    # Request models
    NewsRequest,
    PreTradeRequest,
    TradeStartRequest,
    BinanceValidateRequest,
    # Response / status models
    RestApiResponse as ApiResponse,
    ModuleStatus,
    StatusResponse,
)

__all__ = [
    "NewsRequest",
    "PreTradeRequest",
    "TradeStartRequest",
    "BinanceValidateRequest",
    "ApiResponse",
    "ModuleStatus",
    "StatusResponse",
]
