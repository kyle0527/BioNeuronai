"""Lightweight documentation stubs for :mod:`aiva_common`.

These modules provide the minimal interfaces required to import security
modules during documentation builds without pulling the proprietary
implementation. They are **not** feature complete and should only be used for
static analysis and API reference generation.
"""

from . import enums, schemas, utils  # noqa: F401

__all__ = [
    "enums",
    "schemas",
    "utils",
]
