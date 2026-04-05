"""Replay UI helpers."""

from __future__ import annotations

from pathlib import Path

from .paths import UI_ROOT, ensure_backtest_dirs


def load_backtest_ui_html() -> str:
    """Load the replay UI from backtest-owned assets."""
    ensure_backtest_dirs([UI_ROOT])
    html_path = UI_ROOT / "index.html"
    return html_path.read_text(encoding="utf-8")
