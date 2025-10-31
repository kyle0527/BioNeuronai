"""Configuration placeholders used by the production modules in tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SQLiConfig:
    baseline_window: int = 50
    novelty_threshold: float = 0.55
    novelty_weight: float = 0.35


@dataclass(slots=True)
class IDORConfig:
    baseline_window: int = 40
    novelty_threshold: float = 0.5
    novelty_weight: float = 0.3


@dataclass(slots=True)
class AuthConfig:
    baseline_window: int = 60
    novelty_threshold: float = 0.6
    novelty_weight: float = 0.4


__all__ = ["SQLiConfig", "IDORConfig", "AuthConfig"]
