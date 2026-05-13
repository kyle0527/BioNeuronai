# -*- coding: utf-8 -*-
"""Small JSON-safe serialization helpers for API responses."""

import json
from datetime import datetime
from typing import Any


def safe_serialize(obj: Any) -> dict[str, Any]:
    """Convert common Python/Pydantic objects into a JSON-friendly dict."""
    if isinstance(obj, dict):
        return {k: safe_value(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return dict(obj.model_dump())
    if hasattr(obj, "__dict__"):
        return {k: safe_value(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return {"raw": str(obj)}


def safe_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: safe_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)
