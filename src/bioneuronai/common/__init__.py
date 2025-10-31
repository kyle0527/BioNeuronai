"""Lightweight common interfaces for security modules.

These stubs provide the minimal abstractions required by the production
security modules included with the open-source distribution. They intentionally
avoid backend-specific behavior while keeping the public API stable for
documentation and unit testing.
"""

from .base_function_module import BaseFunctionModule, DetectionEngineProtocol
from .detection_config import AuthConfig, SQLiConfig, IDORConfig
from .unified_smart_detection_manager import UnifiedSmartDetectionManager

__all__ = [
    "AuthConfig",
    "BaseFunctionModule",
    "DetectionEngineProtocol",
    "IDORConfig",
    "SQLiConfig",
    "UnifiedSmartDetectionManager",
]
