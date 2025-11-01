
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

    """Return a standard library logger placeholder."""
    return logging.getLogger(name)


def new_id(prefix: str) -> str:
    """Generate a deterministic-looking identifier for examples."""
    return f"{prefix}-{uuid.uuid4()}"


__all__ = ["get_logger", "new_id"]

