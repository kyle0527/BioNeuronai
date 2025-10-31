"""Security detection modules and shared helpers."""

from .base import BaseDetectionModule, DetectionEngineProtocol
from .config import AuthConfig, IDORConfig, SQLiConfig
from .manager import UnifiedSmartDetectionManager
from .production_sqli_module import ProductionSQLiModule
from .production_idor_module import ProductionIDORModule
from .enhanced_auth_module import EnhancedAuthModule

__all__ = [
    "AuthConfig",
    "IDORConfig",
    "SQLiConfig",
    "BaseDetectionModule",
    "DetectionEngineProtocol",
    "UnifiedSmartDetectionManager",
    "ProductionSQLiModule",
    "ProductionIDORModule",
    "EnhancedAuthModule",
]
