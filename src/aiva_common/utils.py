"""Utility helpers used during documentation builds."""

from __future__ import annotations

import logging
import uuid


def get_logger(name: str) -> logging.Logger:
    """Return a standard library logger placeholder."""
    return logging.getLogger(name)


def new_id(prefix: str) -> str:
    """Generate a deterministic-looking identifier for examples."""
    return f"{prefix}-{uuid.uuid4()}"


__all__ = ["get_logger", "new_id"]
