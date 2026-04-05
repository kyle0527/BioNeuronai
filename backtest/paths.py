"""Shared paths for the replay/backtest domain."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKTEST_ROOT = Path(__file__).resolve().parent

DOCS_ROOT = BACKTEST_ROOT / "docs"
UI_ROOT = BACKTEST_ROOT / "ui"
RUNTIME_ROOT = BACKTEST_ROOT / "runtime"
VENDOR_ROOT = BACKTEST_ROOT / "vendor"
DATA_ROOT = BACKTEST_ROOT / "data"

# Preferred long-term location: keep replay-related assets under backtest/.
BACKTEST_DATA_DIR = DATA_ROOT / "binance_historical"

# Current project data locations still supported as fallbacks.
PROJECT_DATA_DIR = PROJECT_ROOT / "data" / "bioneuronai" / "historical" / "data_downloads" / "binance_historical"
LEGACY_DATA_DIR = PROJECT_ROOT / "data_downloads" / "binance_historical"
TRAINING_DATA_DIR = PROJECT_ROOT / "training_data" / "data_downloads" / "binance_historical"


def candidate_data_roots(extra: Optional[Union[str, Path]] = None) -> List[Path]:
    """Return candidate replay data roots in priority order."""
    candidates: List[Path] = []

    if extra is not None:
        requested = Path(extra)
        if requested.is_absolute():
            candidates.append(requested)
        else:
            candidates.extend(
                [
                    requested,
                    BACKTEST_ROOT / requested,
                    PROJECT_ROOT / requested,
                ]
            )

    candidates.extend(
        [
            BACKTEST_DATA_DIR,
            PROJECT_DATA_DIR,
            LEGACY_DATA_DIR,
            TRAINING_DATA_DIR,
        ]
    )

    unique: List[Path] = []
    seen = set()
    for path in candidates:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def ensure_backtest_dirs(paths: Optional[Iterable[Path]] = None) -> None:
    """Create backtest-owned directories if they do not exist."""
    targets = list(paths or [DOCS_ROOT, UI_ROOT, RUNTIME_ROOT, VENDOR_ROOT, DATA_ROOT])
    for path in targets:
        path.mkdir(parents=True, exist_ok=True)
