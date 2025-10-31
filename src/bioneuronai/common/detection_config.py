"""Minimal detection configuration stubs."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SQLiConfig:
    enabled: bool = True


@dataclass
class IDORConfig:
    enabled: bool = True


@dataclass
class AuthConfig:
    enabled: bool = True
