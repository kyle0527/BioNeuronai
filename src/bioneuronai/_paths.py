"""Shared project path helpers."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_project_path(path: str | Path) -> Path:
    """Resolve relative repo paths from the project root."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate
