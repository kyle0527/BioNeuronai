"""Utility helpers used by the production modules during testing."""
from __future__ import annotations

import logging
import uuid


def get_logger(name: str) -> logging.Logger:
    """Return a basic logger configured for console output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def new_id(prefix: str) -> str:
    """Generate a pseudo unique identifier with the given prefix."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"
