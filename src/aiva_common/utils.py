"""Utility helpers shared across security detection modules."""

from __future__ import annotations

import logging
import uuid


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance."""

    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)


def new_id(prefix: str) -> str:
    """Generate a deterministic-looking identifier for findings."""

    return f"{prefix}_{uuid.uuid4().hex}"


__all__ = ["get_logger", "new_id"]
