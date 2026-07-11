"""
 (Inference Engine)
================================

-  AI

:
     ->  ->  ->  ->

:
    - ModelLoader:  PyTorch
    - FeaturePipeline:
    - Predictor:
    - SignalInterpreter:
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

from ..data.cloud_storage import materialize_uri

UNIFIED_MODEL_NAME = "unified_v2_100m"


# ============================================================================
#
# ============================================================================

class SignalType(Enum):
    """"""
    STRONG_LONG = "strong_long"      #
    LONG = "long"                     #
    WEAK_LONG = "weak_long"           #
    NEUTRAL = "neutral"               # /
    WEAK_SHORT = "weak_short"         #
    SHORT = "short"                   #
    STRONG_SHORT = "strong_short"     #


class RiskLevel(Enum):
    """"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class TradingSignal:
    """"""
    symbol: str
    timestamp: datetime
    signal_type: SignalType
    confidence: float                 # 0-1

    #
    suggested_leverage: int = 1
    suggested_position_size: float = 0.0  #
    suggested_entry: float = 0.0
    suggested_stop_loss: float = 0.0
    suggested_take_profit: float = 0.0

    #
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_reward_ratio: float = 0.0

    #
    raw_output: Optional[np.ndarray] = None
    model_latency_ms: float = 0.0

    #
    market_regime: str = ""
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "signal_type": self.signal_type.value,
            "confidence": round(self.confidence, 4),
            "suggested_leverage": self.suggested_leverage,
            "suggested_position_size": round(self.suggested_position_size, 4),
            "suggested_entry": round(self.suggested_entry, 2),
            "suggested_stop_loss": round(self.suggested_stop_loss, 2),
            "suggested_take_profit": round(self.suggested_take_profit, 2),
            "risk_level": self.risk_level.value,
            "risk_reward_ratio": round(self.risk_reward_ratio, 2),
            "model_latency_ms": round(self.model_latency_ms, 2),
            "market_regime": self.market_regime,
            "reasoning": self.reasoning
        }

    def __str__(self) -> str:
        signal_emoji = {
            SignalType.STRONG_LONG: "[++]",
            SignalType.LONG: "[+]",
            SignalType.WEAK_LONG: "[+?]",
            SignalType.NEUTRAL: "[=]",
            SignalType.WEAK_SHORT: "[-?]",
            SignalType.SHORT: "[-]",
            SignalType.STRONG_SHORT: "[--]"
        }
        emoji = signal_emoji.get(self.signal_type, "")
        return (
            f"{emoji} {self.symbol} | {self.signal_type.value.upper()} "
            f"(: {self.confidence:.1%}) | "
            f": {self.risk_level.value} | "
            f": {self.model_latency_ms:.1f}ms"
        )


# ============================================================================
#  (Model Loader)
# ============================================================================

class ModelLoader:
    """

     PyTorch
    """

    def __init__(self, model_dir: Optional[Path] = None):
        """

        Args:
            model_dir:  model/
        """
        if model_dir is None:
            # : BioNeuronai/model/
            model_dir = Path(__file__).parent.parent.parent.parent / "model"

        self.project_root = Path(__file__).parent.parent.parent.parent
        self.model_dir = Path(model_dir)
        self.models: Dict[str, nn.Module] = {}
        self.active_model_name: Optional[str] = None
        self.device = self._get_device()

        logger.info(f"ModelLoader  | : {self.device} | : {self.model_dir}")

    def _get_device(self) -> torch.device:
        """"""
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f" GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            logger.info(" CPU ")
        return device

    @staticmethod
    def _extract_state_dict(checkpoint: Any) -> Dict[str, torch.Tensor]:
        """從多種 checkpoint 版型中提取 state_dict。"""
        if isinstance(checkpoint, dict) and isinstance(checkpoint.get("state_dict"), dict):
            return cast(Dict[str, torch.Tensor], checkpoint["state_dict"])
        if isinstance(checkpoint, dict):
            return cast(Dict[str, torch.Tensor], checkpoint)
        raise TypeError(f"不支援的 checkpoint 格式: {type(checkpoint).__name__}")

    @staticmethod
    def _is_v2_checkpoint(state_dict: Dict[str, torch.Tensor]) -> bool:
        """判斷是否為統一 TinyLLM v2 checkpoint。"""
        return any(key.startswith("numeric_encoder.") for key in state_dict) and any(
            key.startswith("signal_head.proj.") for key in state_dict
        )

    @staticmethod
    def _supports_signal_inference(model: nn.Module) -> bool:
        """判斷模型是否可直接用於交易訊號推論。"""
        return (
            hasattr(model, "forward_signal")
            and (
                getattr(model, "numeric_proj", None) is not None
                or getattr(model, "numeric_encoder", None) is not None
            )
            and getattr(model, "signal_head", None) is not None
        )

    def _build_unified_model(self, config_dict: Optional[Dict[str, Any]] = None) -> nn.Module:
        """依 active_model 設定建立唯一的 v2 模型；無權重時為明確未訓練狀態。"""
        import sys

        src_path = str(self.project_root / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from nlp.tiny_llm_v2 import TinyLLMv2, TinyLLMv2Config

        config = (
            TinyLLMv2Config.from_dict(config_dict)
            if config_dict
            else TinyLLMv2Config.compact_100m()
        )
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(0)
            model = TinyLLMv2(config)
        setattr(model, "is_trained", False)
        setattr(model, "model_name", UNIFIED_MODEL_NAME)
        return model

    def _build_default_model(
        self,
        checkpoint: Any,
        state_dict: Dict[str, torch.Tensor],
    ) -> Tuple[type, Dict[str, Any]]:
        """依 checkpoint 自動選擇相容的模型類別與初始化參數。"""
        import sys

        project_root = self.project_root
        src_path = str(project_root / "src")
        root_path = str(project_root)
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        # 確保根目錄在路徑中，支援專案層級模組與相對資源解析。
        if root_path not in sys.path:
            sys.path.insert(0, root_path)

        if self._is_v2_checkpoint(state_dict):
            from nlp.tiny_llm_v2 import TinyLLMv2, TinyLLMv2Config

            config_dict = checkpoint.get("config") if isinstance(checkpoint, dict) else None
            config = TinyLLMv2Config.from_dict(config_dict or {})
            return TinyLLMv2, {"config": config}
        raise RuntimeError(
            "只允許 TinyLLMv2 統一 checkpoint；v1/legacy 權重僅可供離線遷移，"
            "不可再載入現役推論流程"
        )

    def load_model(
        self,
        model_name: str = UNIFIED_MODEL_NAME,
    ) -> nn.Module:
        """

        Args:
            model_name:  .pth
            model_name: 唯一現役模型名稱
        """
        if model_name in self.models:
            self.active_model_name = model_name
            return self.models[model_name]

        model_path = self._resolve_model_path(model_name)

        if not model_path.exists() and model_name == UNIFIED_MODEL_NAME:
            active = self._read_active_model_config()
            model = self._build_unified_model(active.get("config"))
            model.to(self.device).eval()
            self.models[model_name] = model
            self.active_model_name = model_name
            logger.warning(
                "統一模型權重尚未建立；已載入固定 seed 的未訓練 v2，僅供端到端運作驗證"
            )
            return model

        if not model_path.exists():
            raise FileNotFoundError(f"模型不存在: {model_path}")

        logger.info(f": {model_path}")

        #
        start_time = time.time()
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
        load_time = time.time() - start_time

        state_dict = self._extract_state_dict(checkpoint)

        model_class, model_kwargs = self._build_default_model(checkpoint, state_dict)
        model = model_class(**model_kwargs)
        missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
        if missing_keys or unexpected_keys:
            details: List[str] = []
            if missing_keys:
                details.append(f"missing={missing_keys[:8]}")
            if unexpected_keys:
                details.append(f"unexpected={unexpected_keys[:8]}")
            raise RuntimeError(
                f"模型權重與架構不相容 ({'; '.join(details)})。"
            )
        if hasattr(model, "forward_signal") and not self._supports_signal_inference(model):
            raise RuntimeError("載入的是文字生成 TinyLLM 權重，缺少 numeric signal head，無法用於交易推論")
        model.to(self.device)
        model.eval()  #
        setattr(model, "is_trained", True)
        setattr(model, "model_name", model_name)

        #
        param_count = sum(p.numel() for p in model.parameters())
        logger.info(
            f" | : {param_count/1e6:.1f}M | "
            f": {load_time:.2f}s | : {self.device}"
        )

        self.models[model_name] = model
        self.active_model_name = model_name

        return cast(nn.Module, model)

    def _resolve_model_path(self, model_name: str) -> Path:
        """Resolve model path from env, active model metadata, or the local model directory."""
        env_model_path = os.getenv("MODEL_PATH") or os.getenv("BIONEURONAI_MODEL_PATH")
        if env_model_path:
            if env_model_path.endswith("/") or not Path(env_model_path).suffix:
                return self._materialize_model_path(f"{env_model_path.rstrip('/')}/{model_name}.pth")
            return self._materialize_model_path(env_model_path)

        env_model_dir = os.getenv("MODEL_DIR") or os.getenv("BIONEURONAI_MODEL_DIR")
        if env_model_dir:
            return self._materialize_model_path(f"{env_model_dir.rstrip('/')}/{model_name}.pth")

        active_model_path = self._resolve_active_model_path(model_name)
        if active_model_path is not None:
            return active_model_path

        return self.model_dir / f"{model_name}.pth"

    def _materialize_model_path(self, value: str) -> Path:
        """Resolve local relative paths from the repo root while keeping cloud URIs supported."""
        resolved = materialize_uri(value)
        if not resolved.is_absolute():
            return self.project_root / resolved
        return resolved

    def _resolve_active_model_path(self, model_name: str) -> Optional[Path]:
        """Resolve persisted promoted model metadata shared by API, CLI, and engines."""
        active = self._read_active_model_config()
        promoted_model = str(active.get("model_name") or "").strip()
        if promoted_model and promoted_model != model_name:
            return None

        model_path = str(active.get("model_path") or "").strip()
        if not model_path:
            return None
        if model_path.endswith("/") or not Path(model_path).suffix:
            return self._materialize_model_path(f"{model_path.rstrip('/')}/{model_name}.pth")
        return self._materialize_model_path(model_path)

    def _read_active_model_config(self) -> Dict[str, Any]:
        """讀取唯一 active model 設定；格式錯誤時回傳空設定。"""
        active_config = self.project_root / "config" / "active_model.json"
        if not active_config.exists():
            return {}
        try:
            return cast(
                Dict[str, Any], json.loads(active_config.read_text(encoding="utf-8"))
            )
        except Exception as exc:
            logger.warning("active model metadata read failed: %s", exc)
            return {}

    def get_model(self, model_name: Optional[str] = None) -> nn.Module:
        """"""
        if model_name is None:
            model_name = self.active_model_name

        if model_name is None or model_name not in self.models:
            raise ValueError(f" '{model_name}' ")

        return self.models[model_name]

    def warmup(self, model_name: Optional[str] = None, iterations: int = 10):
        """ ()"""
        model = self.get_model(model_name)

        logger.info(f"... ({iterations} )")
        with torch.no_grad():
            for _ in range(iterations):
                if self._supports_signal_inference(model):
                    config = getattr(model, "config", None)
                    seq_len = int(
                        getattr(config, "num_patches", None)
                        or getattr(config, "numeric_seq_len", 16)
                        or 16
                    )
                    input_dim = int(
                        getattr(config, "num_patch_features", None)
                        or getattr(config, "numeric_input_dim", 1024)
                        or 1024
                    )
                    dummy_input = torch.zeros(1, seq_len, input_dim, dtype=torch.float32, device=self.device)
                else:
                    dummy_input = torch.zeros(1, 1024, dtype=torch.float32, device=self.device)
                _ = self._run_warmup_forward(model, dummy_input)

        #
        start = time.perf_counter()
        with torch.no_grad():
            for _ in range(100):
                _ = self._run_warmup_forward(model, dummy_input)
        avg_latency = (time.perf_counter() - start) / 100 * 1000

        logger.info(f" | : {avg_latency:.2f}ms")
        return avg_latency

    def _run_warmup_forward(self, model: nn.Module, dummy_input: torch.Tensor) -> torch.Tensor:
        """Run the correct inference path for warmup across TinyLLM signal and legacy models."""
        if self._supports_signal_inference(model):
            output = self._run_signal_forward(model, dummy_input)
            return cast(torch.Tensor, output[0] if isinstance(output, tuple) else output)
        return cast(torch.Tensor, model(dummy_input))

    @staticmethod
    def _run_signal_forward(
        model: nn.Module,
        numeric_input: torch.Tensor,
        **kwargs: Any,
    ) -> Any:
        """呼叫已通過能力檢查的模型 signal 入口。"""
        forward_signal = cast(Callable[..., Any], getattr(model, "forward_signal"))
        return forward_signal(numeric_input, **kwargs)


# ============================================================================
#  (Feature Pipeline)
# ============================================================================

class FeaturePipeline:
    """

     1024
    """

    #
    FEATURE_CONFIG = {
        "price_features": 128,        #
        "volume_features": 128,       #
        "orderbook_features": 128,    #
        "technical_features": 256,    #
        "microstructure_features": 128,  #
        "regime_features": 64,        #
        "time_features": 32,          #
        "sentiment_features": 64,     #
        "liquidation_features": 64,   #
        "funding_features": 32,       #
    }

    TOTAL_FEATURES = 1024

    # 從既有 1024 維 SSOT 特徵中挑出 58 個有效欄位；其餘 6 維由 regime/time/funding
    # 以固定規則整理。這是 v2 唯一的 64 維 patch 映射，避免各模組自行切片。
    V2_BASE_INDICES = np.array(
        [
            0, 1, 2, 3, 4, 10, 15, 20, 21, 22, 23, 30, 40, 41,
            128, 129, 130, 131, 138, 143, 178, 179, 180, 181, 182,
            256, 266, 267, 268, 269, 276, 277, 278, 279, 286, 287, 288,
            384, 385, 386, 394, 395, 396, 404, 405, 414, 424, 425, 426, 434, 435,
            640, 641, 642, 643, 660, 661, 680,
        ],
        dtype=np.int64,
    )

    def __init__(self):
        """"""
        #  ()
        self.feature_means: Optional[np.ndarray] = None
        self.feature_stds: Optional[np.ndarray] = None

        #
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[float]] = {}

        logger.info(f"FeaturePipeline  | : {self.TOTAL_FEATURES}")

    def build_features(
        self,
        current_price: float,
        klines: List[Dict],  # K
        order_book: Optional[Any] = None,
        microstructure: Optional[Any] = None,  # MarketMicrostructure
        volume_profile: Optional[Any] = None,  # VolumeProfile
        liquidation_heatmap: Optional[Any] = None,  # LiquidationHeatmap
        regime_analysis: Optional[Any] = None,  # RegimeAnalysis
    ) -> np.ndarray:
        """

        Args:
            symbol:
            current_price:
            klines: K
            order_book:
            microstructure:
            volume_profile:
            liquidation_heatmap:
            regime_analysis:

        Returns:
            1024
        """
        features = np.zeros(self.TOTAL_FEATURES, dtype=np.float32)
        offset = 0

        # 1.  (128 )
        price_features = self._extract_price_features(klines, current_price)
        features[offset:offset + 128] = price_features[:128]
        offset += 128

        # 2.  (128 )
        volume_features = self._extract_volume_features(klines, volume_profile)
        features[offset:offset + 128] = volume_features[:128]
        offset += 128

        # 3.  (128 )
        orderbook_features = self._extract_orderbook_features(order_book)
        features[offset:offset + 128] = orderbook_features[:128]
        offset += 128

        # 4.  (256 )
        technical_features = self._extract_technical_features(klines)
        features[offset:offset + 256] = technical_features[:256]
        offset += 256

        # 5.  (128 )
        micro_features = self._extract_microstructure_features(microstructure)
        features[offset:offset + 128] = micro_features[:128]
        offset += 128

        # 6.  (64 )
        regime_features = self._extract_regime_features(regime_analysis)
        features[offset:offset + 64] = regime_features[:64]
        offset += 64

        # 7.  (32 )
        time_features = self._extract_time_features()
        features[offset:offset + 32] = time_features[:32]
        offset += 32

        # 8.  (64 )
        sentiment_features = self._extract_sentiment_features(microstructure)
        features[offset:offset + 64] = sentiment_features[:64]
        offset += 64

        # 9.  (64 )
        liquidation_features = self._extract_liquidation_features(liquidation_heatmap, microstructure)
        features[offset:offset + 64] = liquidation_features[:64]
        offset += 64

        # 10.  (32 )
        funding_features = self._extract_funding_features(microstructure)
        features[offset:offset + 32] = funding_features[:32]
        offset += 32

        #
        if self.feature_means is not None and self.feature_stds is not None:
            features = (features - self.feature_means) / (self.feature_stds + 1e-8)

        return cast(np.ndarray, features)

    @classmethod
    def to_v2_patch(cls, features: np.ndarray) -> np.ndarray:
        """把既有 1024 維特徵確定性轉成 v2 唯一的 64 維語意 patch。"""
        values = np.asarray(features, dtype=np.float32)
        if values.shape[-1] != cls.TOTAL_FEATURES:
            raise ValueError(
                f"v2 feature conversion expects {cls.TOTAL_FEATURES} values, "
                f"got {values.shape[-1]}"
            )

        compact = np.zeros((*values.shape[:-1], 64), dtype=np.float32)
        compact[..., :58] = values[..., cls.V2_BASE_INDICES]

        regime_one_hot = values[..., 768:778]
        regime_present = np.max(regime_one_hot, axis=-1) > 0
        regime_index = np.argmax(regime_one_hot, axis=-1).astype(np.float32) / 9.0
        compact[..., 58] = np.where(regime_present, regime_index, 0.0)
        compact[..., 59] = values[..., 788]  # volatility regime
        compact[..., 60] = values[..., 798]  # trend strength
        compact[..., 61] = values[..., 832]  # UTC hour sin
        compact[..., 62] = values[..., 833]  # UTC hour cos
        compact[..., 63] = values[..., 992]  # funding rate
        return compact

    def _extract_price_features(self, klines: List[Dict], current_price: float) -> np.ndarray:
        """"""
        features = np.zeros(128, dtype=np.float32)

        if not klines:
            return cast(np.ndarray, features)

        #
        closes = np.array([float(k.get('close', k.get('c', 0))) for k in klines[-100:]])

        if len(closes) < 2:
            return cast(np.ndarray, features)

        #  ()
        for i, period in enumerate([1, 5, 15, 30, 60]):
            if len(closes) > period:
                change = (closes[-1] - closes[-1-period]) / closes[-1-period]
                features[i] = change

        #  (0-1 )
        price_min: float = float(np.min(closes))
        price_max: float = float(np.max(closes))
        if price_max > price_min:
            features[10] = (current_price - price_min) / (price_max - price_min)

        #
        if len(closes) >= 20:
            momentum = (closes[-1] - closes[-20]) / closes[-20]
            features[15] = momentum

        #  ()
        for i, period in enumerate([5, 10, 20, 50]):
            if len(closes) > period:
                returns = np.diff(closes[-period:]) / closes[-period:-1]
                volatility = np.std(returns) * np.sqrt(period)
                features[20 + i] = volatility

        #  ()
        if len(closes) >= 20:
            x = np.arange(20)
            slope, _ = np.polyfit(x, closes[-20:], 1)
            features[30] = slope / current_price  #

        #
        if len(closes) >= 50:
            features[40] = (current_price - np.min(closes[-50:])) / current_price
            features[41] = (np.max(closes[-50:]) - current_price) / current_price

        return cast(np.ndarray, features)

    def _extract_volume_features(self, klines: List[Dict], volume_profile: Optional[Any]) -> np.ndarray:
        """"""
        features = np.zeros(128, dtype=np.float32)

        if not klines:
            return cast(np.ndarray, features)

        #
        volumes = np.array([float(k.get('volume', k.get('v', 0))) for k in klines[-100:]])

        if len(volumes) < 2:
            return cast(np.ndarray, features)

        #
        for i, period in enumerate([1, 5, 15, 30]):
            if len(volumes) > period:
                avg_recent = np.mean(volumes[-period:])
                avg_before = np.mean(volumes[-period*2:-period]) if len(volumes) > period*2 else avg_recent
                if avg_before > 0:
                    features[i] = (avg_recent - avg_before) / avg_before

        #
        if len(volumes) >= 20:
            avg_20 = np.mean(volumes[-20:])
            features[10] = volumes[-1] / avg_20 if avg_20 > 0 else 1.0

        #
        if len(volumes) >= 10:
            x = np.arange(10)
            slope, _ = np.polyfit(x, volumes[-10:], 1)
            features[15] = slope / np.mean(volumes[-10:]) if np.mean(volumes[-10:]) > 0 else 0

        # Volume Profile
        if volume_profile:
            features[50] = volume_profile.poc_price
            features[51] = volume_profile.value_area_high
            features[52] = volume_profile.value_area_low
            features[53] = len(volume_profile.high_volume_nodes)
            features[54] = len(volume_profile.low_volume_nodes)

        return cast(np.ndarray, features)

    def _extract_orderbook_features(self, order_book: Optional[Any]) -> np.ndarray:
        """"""
        features = np.zeros(128, dtype=np.float32)

        if order_book is None:
            return cast(np.ndarray, features)

        #
        features[0] = order_book.spread_percentage if hasattr(order_book, 'spread_percentage') else 0

        #
        if hasattr(order_book, 'get_bid_depth'):
            for i, depth in enumerate([5, 10, 20, 50]):
                features[10 + i] = order_book.get_bid_depth(depth)
                features[20 + i] = order_book.get_ask_depth(depth)

        #
        if hasattr(order_book, 'get_imbalance'):
            for i, depth in enumerate([5, 10, 20]):
                features[30 + i] = order_book.get_imbalance(depth)

        return cast(np.ndarray, features)

    def _extract_technical_features(self, klines: List[Dict]) -> np.ndarray:
        """"""
        features = np.zeros(256, dtype=np.float32)

        if not klines or len(klines) < 30:
            return cast(np.ndarray, features)

        closes = np.array([float(k.get('close', k.get('c', 0))) for k in klines])
        highs = np.array([float(k.get('high', k.get('h', 0))) for k in klines])
        lows = np.array([float(k.get('low', k.get('l', 0))) for k in klines])

        # RSI ()
        for i, period in enumerate([7, 14, 21]):
            rsi = self._calculate_rsi(closes, period)
            features[i] = (rsi - 50) / 50  #  -1  1

        # MACD
        macd, signal, histogram = self._calculate_macd(closes)
        features[10] = macd / closes[-1] if closes[-1] > 0 else 0
        features[11] = signal / closes[-1] if closes[-1] > 0 else 0
        features[12] = histogram / closes[-1] if closes[-1] > 0 else 0

        #
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes)
        current = closes[-1]
        bb_width = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
        bb_position = (current - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
        features[20] = bb_width
        features[21] = bb_position

        # ATR (Average True Range)
        atr = self._calculate_atr(highs, lows, closes)
        features[30] = atr / current if current > 0 else 0

        #
        for i, period in enumerate([5, 10, 20, 50, 100]):
            if len(closes) >= period:
                ma = np.mean(closes[-period:])
                features[40 + i] = (current - ma) / ma if ma > 0 else 0

        # EMA
        for i, period in enumerate([12, 26, 50]):
            if len(closes) >= period:
                ema = self._calculate_ema(closes, period)
                features[50 + i] = (current - ema) / ema if ema > 0 else 0

        return cast(np.ndarray, features)

    def _extract_microstructure_features(self, microstructure: Optional[Any]) -> np.ndarray:
        """"""
        features = np.zeros(128, dtype=np.float32)

        if microstructure is None:
            return cast(np.ndarray, features)

        #
        features[0] = microstructure.price_change_1m / 100 if hasattr(microstructure, 'price_change_1m') else 0
        features[1] = microstructure.price_change_5m / 100 if hasattr(microstructure, 'price_change_5m') else 0
        features[2] = microstructure.price_change_15m / 100 if hasattr(microstructure, 'price_change_15m') else 0
        features[3] = microstructure.price_change_1h / 100 if hasattr(microstructure, 'price_change_1h') else 0

        #
        features[10] = microstructure.volume_ratio if hasattr(microstructure, 'volume_ratio') else 1.0

        #
        features[20] = microstructure.bid_ask_spread if hasattr(microstructure, 'bid_ask_spread') else 0
        features[21] = microstructure.order_book_imbalance if hasattr(microstructure, 'order_book_imbalance') else 0

        #
        features[30] = microstructure.oi_change_1h / 100 if hasattr(microstructure, 'oi_change_1h') else 0
        features[31] = microstructure.oi_change_24h / 100 if hasattr(microstructure, 'oi_change_24h') else 0

        #
        features[40] = microstructure.long_short_ratio if hasattr(microstructure, 'long_short_ratio') else 1.0
        features[41] = microstructure.taker_buy_sell_ratio if hasattr(microstructure, 'taker_buy_sell_ratio') else 1.0

        return cast(np.ndarray, features)

    def _extract_regime_features(self, regime_analysis: Optional[Any]) -> np.ndarray:
        """"""
        features = np.zeros(64, dtype=np.float32)

        if regime_analysis is None:
            return cast(np.ndarray, features)

        # One-hot
        regime_map = {
            "trending_up": 0, "trending_down": 1,
            "ranging": 2, "breakout_up": 3, "breakout_down": 4,
            "high_volatility": 5, "low_volatility": 6,
            "accumulation": 7, "distribution": 8, "choppy": 9
        }

        if hasattr(regime_analysis, 'regime'):
            regime_idx = regime_map.get(regime_analysis.regime.value, 2)
            features[regime_idx] = 1.0

        #
        if hasattr(regime_analysis, 'volatility_regime'):
            vol_map = {"very_low": 0.1, "low": 0.3, "normal": 0.5, "high": 0.7, "extreme": 0.9}
            features[20] = vol_map.get(regime_analysis.volatility_regime.value, 0.5)

        #
        if hasattr(regime_analysis, 'trend_strength'):
            strength_map = {"none": 0, "weak": 0.25, "moderate": 0.5, "strong": 0.75, "very_strong": 1.0}
            features[30] = strength_map.get(regime_analysis.trend_strength.value, 0)

        return cast(np.ndarray, features)

    def _extract_time_features(self) -> np.ndarray:
        """"""
        features = np.zeros(32, dtype=np.float32)

        now = datetime.now(timezone.utc)

        #  ()
        hour_sin = np.sin(2 * np.pi * now.hour / 24)
        hour_cos = np.cos(2 * np.pi * now.hour / 24)
        features[0] = hour_sin
        features[1] = hour_cos

        #  ()
        day_sin = np.sin(2 * np.pi * now.weekday() / 7)
        day_cos = np.cos(2 * np.pi * now.weekday() / 7)
        features[2] = day_sin
        features[3] = day_cos

        #
        day_of_month_sin = np.sin(2 * np.pi * now.day / 31)
        day_of_month_cos = np.cos(2 * np.pi * now.day / 31)
        features[4] = day_of_month_sin
        features[5] = day_of_month_cos

        #
        features[10] = 1.0 if now.weekday() >= 5 else 0.0

        #  (//)
        features[15] = 1.0 if 0 <= now.hour < 8 else 0.0   #
        features[16] = 1.0 if 7 <= now.hour < 15 else 0.0  #
        features[17] = 1.0 if 13 <= now.hour < 22 else 0.0 #

        return cast(np.ndarray, features)

    def _extract_sentiment_features(self, microstructure: Optional[Any]) -> np.ndarray:
        """"""
        features = np.zeros(64, dtype=np.float32)

        if microstructure is None:
            return cast(np.ndarray, features)

        #
        if hasattr(microstructure, 'long_short_ratio'):
            ratio = microstructure.long_short_ratio
            #  -1 ()  1 ()
            sentiment = (ratio - 1) / max(abs(ratio - 1), 0.01)
            features[0] = np.clip(sentiment, -1, 1)

        #
        if hasattr(microstructure, 'order_book_imbalance'):
            features[10] = microstructure.order_book_imbalance

        return cast(np.ndarray, features)

    def _extract_liquidation_features(
        self,
        liquidation_heatmap: Optional[Any],
        microstructure: Optional[Any]
    ) -> np.ndarray:
        """"""
        features = np.zeros(64, dtype=np.float32)

        #
        if microstructure:
            if hasattr(microstructure, 'long_liquidation_1h'):
                features[0] = np.log1p(microstructure.long_liquidation_1h) / 20  #
            if hasattr(microstructure, 'short_liquidation_1h'):
                features[1] = np.log1p(microstructure.short_liquidation_1h) / 20
            if hasattr(microstructure, 'net_liquidation'):
                features[2] = np.sign(microstructure.net_liquidation) * np.log1p(abs(microstructure.net_liquidation)) / 20

        #
        if liquidation_heatmap:
            features[10] = liquidation_heatmap.nearest_long_cluster_distance / 10
            features[11] = liquidation_heatmap.nearest_short_cluster_distance / 10
            features[12] = np.log1p(liquidation_heatmap.total_long_liquidation_risk) / 25
            features[13] = np.log1p(liquidation_heatmap.total_short_liquidation_risk) / 25

        return cast(np.ndarray, features)

    def _extract_funding_features(self, microstructure: Optional[Any]) -> np.ndarray:
        """"""
        features = np.zeros(32, dtype=np.float32)

        if microstructure is None:
            return cast(np.ndarray, features)

        if hasattr(microstructure, 'funding_rate'):
            features[0] = microstructure.funding_rate * 100  #

        if hasattr(microstructure, 'predicted_funding_rate'):
            features[1] = microstructure.predicted_funding_rate * 100

        if hasattr(microstructure, 'hours_to_funding'):
            #  ()
            features[2] = microstructure.hours_to_funding / 8

        return cast(np.ndarray, features)

    # ==========  ==========

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """ RSI"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    def _calculate_macd(
        self,
        prices: np.ndarray,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[float, float, float]:
        """ MACD"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0

        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)

        macd_line = ema_fast - ema_slow
        # MACD 信號線應為 MACD 值的 9 週期 EMA（O(n) 增量計算）
        signal_line = self._calculate_macd_signal_ema(prices, fast, slow, signal)
        if signal_line is None:
            signal_line = macd_line  # 資料不足時退化為 MACD 值本身
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def _calculate_macd_signal_ema(
        self,
        prices: np.ndarray,
        fast: int,
        slow: int,
        signal: int,
    ):
        """O(n) 增量計算 MACD 信號線（MACD 值的 signal 週期 EMA）。"""
        if len(prices) < slow + signal:
            return None
        k_fast = 2 / (fast + 1)
        k_slow = 2 / (slow + 1)
        k_sig = 2 / (signal + 1)
        ema_f = float(prices[0])
        ema_s = float(prices[0])
        for p in prices[1:slow]:
            ema_f = p * k_fast + ema_f * (1 - k_fast)
            ema_s = p * k_slow + ema_s * (1 - k_slow)
        macd_vals = []
        for p in prices[slow:]:
            ema_f = p * k_fast + ema_f * (1 - k_fast)
            ema_s = p * k_slow + ema_s * (1 - k_slow)
            macd_vals.append(ema_f - ema_s)
        if len(macd_vals) < signal:
            return None
        sig_ema = macd_vals[0]
        for v in macd_vals[1:]:
            sig_ema = v * k_sig + sig_ema * (1 - k_sig)
        return sig_ema

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """ EMA"""
        if len(prices) < period:
            return float(prices[-1]) if len(prices) > 0 else 0.0

        multiplier = 2 / (period + 1)
        ema = prices[-period]

        for price in prices[-period+1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return float(ema)

    def _calculate_bollinger_bands(
        self,
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[float, float, float]:
        """"""
        if len(prices) < period:
            return 0.0, 0.0, 0.0

        middle = np.mean(prices[-period:])
        std = np.std(prices[-period:])

        upper = middle + std_dev * std
        lower = middle - std_dev * std

        return float(upper), float(middle), float(lower)

    def _calculate_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int = 14
    ) -> float:
        """ ATR"""
        if len(highs) < period + 1:
            return 0.0

        tr_list = []
        for i in range(-period, 0):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_list.append(tr)

        return float(np.mean(tr_list))


# ============================================================================
#  (Predictor)
# ============================================================================

class Predictor:
    """


    """

    def __init__(self, model_loader: ModelLoader):
        """"""
        self.model_loader = model_loader
        self.device = model_loader.device

        #
        self.inference_count = 0
        self.total_latency_ms = 0.0

        logger.info("Predictor ")

    @torch.no_grad()
    def predict(
        self,
        features: np.ndarray,
        model_name: Optional[str] = None,
        text_ids: Optional[torch.Tensor] = None,
    ) -> Tuple[np.ndarray, float]:
        """

        Args:
            features: 1024
            model_name:

        Returns:
            (512 ,  ms)
        """
        model = self.model_loader.get_model(model_name)

        # 轉換為 Tensor
        # features 形狀可能是 (1024,) 或 (T, 1024)；統一加 batch 維度
        feat_tensor = torch.from_numpy(features).float()
        if feat_tensor.dim() == 1:
            # 單步 (1024,) → (1, 1, 1024)
            input_tensor = feat_tensor.unsqueeze(0).unsqueeze(0).to(self.device)
        else:
            # 多步 (T, 1024) → (1, T, 1024)
            input_tensor = feat_tensor.unsqueeze(0).to(self.device)

        # 執行推論：優先使用 TinyLLM 的 forward_signal 路徑
        start_time = time.perf_counter()
        if self.model_loader._supports_signal_inference(model):
            if getattr(model, "numeric_encoder", None) is not None:
                output = self.model_loader._run_signal_forward(
                    model,
                    input_tensor,
                    text_ids=text_ids,
                )
            else:
                output = self.model_loader._run_signal_forward(model, input_tensor)
            if isinstance(output, tuple):
                output = output[0]
        else:
            # 舊版 MLP 模型向下相容：降為單步 (1, 1024)
            input_tensor = input_tensor[:, -1, :] if input_tensor.dim() == 3 else input_tensor
            output = model(input_tensor)
        latency_ms = (time.perf_counter() - start_time) * 1000

        #
        self.inference_count += 1
        self.total_latency_ms += latency_ms

        return output.cpu().numpy()[0], latency_ms

    def get_stats(self) -> Dict[str, float]:
        """"""
        avg_latency = self.total_latency_ms / self.inference_count if self.inference_count > 0 else 0
        return {
            "total_inferences": self.inference_count,
            "avg_latency_ms": avg_latency,
            "total_latency_ms": self.total_latency_ms
        }


# ============================================================================
#  (Signal Interpreter)
# ============================================================================

class SignalInterpreter:
    """

     512
    """

    #
    OUTPUT_CONFIG = {
        "direction_logits": (0, 3),      #  (Long/Neutral/Short)
        "confidence_logits": (3, 6),     #  (Low/Medium/High)
        "risk_logits": (6, 10),          #
        "leverage_logits": (10, 20),     #  (1-10  1x-10x)
        "position_size": (20, 21),       #  (sigmoid)
        "stop_loss_pct": (21, 22),       #
        "take_profit_pct": (22, 23),     #
        "regime_logits": (23, 33),       #
        "embedding": (33, 512),          #  ()
    }

    def __init__(self, min_confidence: float = 0.5):
        """

        Args:
            min_confidence:
        """
        self.min_confidence = min_confidence
        logger.info(f"SignalInterpreter  | : {min_confidence}")

    def interpret(
        self,
        symbol: str,
        current_price: float,
        model_output: np.ndarray,
        latency_ms: float,
        regime_analysis: Optional[Any] = None
    ) -> TradingSignal:
        """

        Args:
            symbol:
            current_price:
            model_output:  512
            latency_ms:
            regime_analysis:  ()

        Returns:
            TradingSignal
        """
        if model_output.shape[-1] == 65:
            return self._interpret_v2(
                symbol, current_price, model_output, latency_ms, regime_analysis
            )

        #
        direction_logits = model_output[self.OUTPUT_CONFIG["direction_logits"][0]:
                                        self.OUTPUT_CONFIG["direction_logits"][1]]
        direction_probs = self._softmax(direction_logits)
        direction_idx = np.argmax(direction_probs)
        direction_confidence = direction_probs[direction_idx]

        #
        confidence_logits = model_output[self.OUTPUT_CONFIG["confidence_logits"][0]:
                                         self.OUTPUT_CONFIG["confidence_logits"][1]]
        confidence_probs = self._softmax(confidence_logits)
        raw_confidence: float = float(np.sum(confidence_probs * np.array([0.3, 0.6, 0.9])))

        #
        final_confidence = direction_confidence * raw_confidence

        #
        signal_type = self._determine_signal_type(int(direction_idx), float(final_confidence))

        #
        risk_logits = model_output[self.OUTPUT_CONFIG["risk_logits"][0]:
                                   self.OUTPUT_CONFIG["risk_logits"][1]]
        risk_probs = self._softmax(risk_logits)
        risk_idx = np.argmax(risk_probs)
        risk_level = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.EXTREME][risk_idx]

        #
        leverage_logits = model_output[self.OUTPUT_CONFIG["leverage_logits"][0]:
                                       self.OUTPUT_CONFIG["leverage_logits"][1]]
        leverage_probs = self._softmax(leverage_logits)
        suggested_leverage = int(np.argmax(leverage_probs)) + 1

        #
        position_raw = model_output[self.OUTPUT_CONFIG["position_size"][0]]
        suggested_position = self._sigmoid(float(position_raw)) * 0.1  #  10%

        #
        sl_raw = model_output[self.OUTPUT_CONFIG["stop_loss_pct"][0]]
        tp_raw = model_output[self.OUTPUT_CONFIG["take_profit_pct"][0]]
        stop_loss_pct = self._sigmoid(float(sl_raw)) * 0.05  #  5%
        take_profit_pct = self._sigmoid(float(tp_raw)) * 0.10  #  10%

        #
        if signal_type in [SignalType.STRONG_LONG, SignalType.LONG, SignalType.WEAK_LONG]:
            stop_loss = current_price * (1 - stop_loss_pct)
            take_profit = current_price * (1 + take_profit_pct)
        elif signal_type in [SignalType.STRONG_SHORT, SignalType.SHORT, SignalType.WEAK_SHORT]:
            stop_loss = current_price * (1 + stop_loss_pct)
            take_profit = current_price * (1 - take_profit_pct)
        else:
            stop_loss = 0.0
            take_profit = 0.0

        #
        if stop_loss_pct > 0:
            risk_reward = take_profit_pct / stop_loss_pct
        else:
            risk_reward = 0.0

        #
        market_regime = ""
        if regime_analysis and hasattr(regime_analysis, 'regime'):
            market_regime = regime_analysis.regime.value

        #
        reasoning = self._generate_reasoning(signal_type, final_confidence, risk_level, market_regime)

        return TradingSignal(
            symbol=symbol,
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=final_confidence,
            suggested_leverage=suggested_leverage,
            suggested_position_size=suggested_position,
            suggested_entry=current_price,
            suggested_stop_loss=stop_loss,
            suggested_take_profit=take_profit,
            risk_level=risk_level,
            risk_reward_ratio=risk_reward,
            raw_output=model_output,
            model_latency_ms=latency_ms,
            market_regime=market_regime,
            reasoning=reasoning
        )

    def _interpret_v2(
        self,
        symbol: str,
        current_price: float,
        model_output: np.ndarray,
        latency_ms: float,
        regime_analysis: Optional[Any],
    ) -> TradingSignal:
        """解析統一模型唯一的 65 維交易輸出。"""
        from nlp.tiny_llm_v2 import HOLD_PERIOD_LABELS, REGIME_LABELS

        direction_probs = self._softmax(model_output[0:3])
        confidence_probs = self._softmax(model_output[3:6])
        direction_index = int(np.argmax(direction_probs))
        confidence_level = float(
            np.sum(confidence_probs * np.array([0.3, 0.6, 0.9]))
        )
        uncertainty = self._sigmoid(float(model_output[54]))
        confidence = float(direction_probs[direction_index] * confidence_level * (1.0 - uncertainty))
        signal_type = self._determine_signal_type(direction_index, confidence)

        leverage = int(np.argmax(self._softmax(model_output[6:16]))) + 1
        position_size = self._sigmoid(float(model_output[16]))
        stop_loss_pct = self._sigmoid(float(model_output[17])) * 0.10
        take_profit_pct = self._sigmoid(float(model_output[18])) * 0.20
        hold_period = HOLD_PERIOD_LABELS[int(np.argmax(self._softmax(model_output[19:29])))]
        regime = REGIME_LABELS[int(np.argmax(self._softmax(model_output[55:65])))]

        if signal_type in {SignalType.STRONG_LONG, SignalType.LONG, SignalType.WEAK_LONG}:
            stop_loss = current_price * (1.0 - stop_loss_pct)
            take_profit = current_price * (1.0 + take_profit_pct)
        elif signal_type in {SignalType.STRONG_SHORT, SignalType.SHORT, SignalType.WEAK_SHORT}:
            stop_loss = current_price * (1.0 + stop_loss_pct)
            take_profit = current_price * (1.0 - take_profit_pct)
        else:
            stop_loss = 0.0
            take_profit = 0.0

        if uncertainty < 0.33:
            risk_level = RiskLevel.LOW
        elif uncertainty < 0.66:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH

        external_regime = ""
        if regime_analysis is not None and hasattr(regime_analysis, "regime"):
            external_regime = str(regime_analysis.regime.value)
        market_regime = external_regime or regime
        reasoning = (
            f"unified-v2 | {signal_type.value} | confidence={confidence:.1%} | "
            f"uncertainty={uncertainty:.1%} | hold={hold_period} | regime={market_regime}"
        )
        risk_reward = take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 0.0

        return TradingSignal(
            symbol=symbol,
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=confidence,
            suggested_leverage=leverage,
            suggested_position_size=position_size,
            suggested_entry=current_price,
            suggested_stop_loss=stop_loss,
            suggested_take_profit=take_profit,
            risk_level=risk_level,
            risk_reward_ratio=risk_reward,
            raw_output=model_output,
            model_latency_ms=latency_ms,
            market_regime=market_regime,
            reasoning=reasoning,
        )

    def _determine_signal_type(self, direction_idx: int, confidence: float) -> SignalType:
        """"""
        if direction_idx == 0:  # Long
            if confidence >= 0.8:
                return SignalType.STRONG_LONG
            elif confidence >= 0.6:
                return SignalType.LONG
            elif confidence >= self.min_confidence:
                return SignalType.WEAK_LONG
            else:
                return SignalType.NEUTRAL
        elif direction_idx == 2:  # Short
            if confidence >= 0.8:
                return SignalType.STRONG_SHORT
            elif confidence >= 0.6:
                return SignalType.SHORT
            elif confidence >= self.min_confidence:
                return SignalType.WEAK_SHORT
            else:
                return SignalType.NEUTRAL
        else:  # Neutral
            return SignalType.NEUTRAL

    def _generate_reasoning(
        self,
        signal_type: SignalType,
        confidence: float,
        risk_level: RiskLevel,
        market_regime: str
    ) -> str:
        """"""
        parts = []

        #
        signal_desc = {
            SignalType.STRONG_LONG: "",
            SignalType.LONG: "",
            SignalType.WEAK_LONG: "",
            SignalType.NEUTRAL: "",
            SignalType.WEAK_SHORT: "",
            SignalType.SHORT: "",
            SignalType.STRONG_SHORT: ""
        }
        parts.append(signal_desc.get(signal_type, ""))

        #
        parts.append(f" {confidence:.1%}")

        #
        risk_desc = {
            RiskLevel.LOW: "",
            RiskLevel.MEDIUM: "",
            RiskLevel.HIGH: "",
            RiskLevel.EXTREME: ""
        }
        parts.append(risk_desc.get(risk_level, ""))

        #
        if market_regime:
            regime_desc = {
                "trending_up": "",
                "trending_down": "",
                "ranging": "",
                "breakout_up": "",
                "breakout_down": "",
                "high_volatility": "",
                "low_volatility": ""
            }
            parts.append(regime_desc.get(market_regime, market_regime))

        return " | ".join(parts)

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """Softmax """
        exp_x = np.exp(x - np.max(x))
        return cast(np.ndarray, exp_x / exp_x.sum())

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Sigmoid """
        return float(1 / (1 + np.exp(-np.clip(x, -500, 500))))


# ============================================================================
#  (Inference Engine) -
# ============================================================================

class InferenceEngine:
    """



    :
        engine = InferenceEngine()
        engine.load_model()
        signal = engine.predict(symbol, price, klines, ...)
    """

    # 滾動視窗長度：與 TinyLLMConfig.numeric_seq_len 保持一致
    _SEQ_LEN: int = 16

    def __init__(
        self,
        model_dir: Optional[Path] = None,
        min_confidence: float = 0.5,
        warmup: bool = True
    ):
        """

        Args:
            model_dir:
            min_confidence:
            warmup:
        """
        self.model_loader = ModelLoader(model_dir)
        self.feature_pipeline = FeaturePipeline()
        self.predictor: Optional[Predictor] = None
        self.signal_interpreter = SignalInterpreter(min_confidence)

        # 滾動特徵視窗：保存最近 _SEQ_LEN 步的 1024 維特徵
        # 使用 deque 以 O(1) 效率維護視窗
        from collections import deque
        self._feature_buffer: Any = deque(maxlen=self._SEQ_LEN)

        self._warmup_on_load = warmup
        self._is_ready = False
        self.use_v2_mode: bool = True
        self._tokenizer: Optional[Any] = None
        self.last_numeric_patches_: Optional[np.ndarray] = None

        logger.info("InferenceEngine ")

    def load_model(
        self,
        model_name: str = UNIFIED_MODEL_NAME,
    ) -> "InferenceEngine":
        """

        Returns:
            self ()
        """
        self.model_loader.load_model(model_name)
        self.predictor = Predictor(self.model_loader)

        if self._warmup_on_load:
            self.model_loader.warmup(model_name)

        self._is_ready = True
        logger.info(f" | : {model_name}")

        return self

    def predict(
        self,
        symbol: str,
        current_price: float,
        klines: List[Dict],
        order_book: Optional[Any] = None,
        microstructure: Optional[Any] = None,
        volume_profile: Optional[Any] = None,
        liquidation_heatmap: Optional[Any] = None,
        regime_analysis: Optional[Any] = None,
        context_text: Optional[str] = None,
    ) -> TradingSignal:
        """

        Args:
            symbol:  ( "BTCUSDT")
            current_price:
            klines: K
            order_book:  ()
            microstructure:  ()
            volume_profile:  ()
            liquidation_heatmap:  ()
            regime_analysis:  ()

        Returns:
            TradingSignal
        """
        if not self._is_ready:
            raise RuntimeError(" load_model()")

        # 1. 提取當前時間步的 1024 維特徵
        features = self.feature_pipeline.build_features(
            current_price=current_price,
            klines=klines,
            order_book=order_book,
            microstructure=microstructure,
            volume_profile=volume_profile,
            liquidation_heatmap=liquidation_heatmap,
            regime_analysis=regime_analysis
        )

        # 暴露給 ActionRecord 使用（(16, 64) 視圖，保持與 v2 patch 格式相容）
        self.last_features_: np.ndarray = features
        self.last_feature_seq_: Optional[np.ndarray] = None  # 下方填充

        # 2. 更新滾動視窗，構建 (T, 1024) 序列
        self._feature_buffer.append(features)
        seq = list(self._feature_buffer)          # T 個 ndarray，T ≤ _SEQ_LEN
        # 若視窗未滿，用第一幀補齊（pad-left with first frame）
        while len(seq) < self._SEQ_LEN:
            seq.insert(0, seq[0])
        feature_seq = np.stack(seq, axis=0)       # (T, 1024)
        self.last_feature_seq_ = feature_seq      # expose (T, 1024) for ActionRecord

        # 3. 統一模型使用固定的 (16, 64) patch；舊格式只允許明確指定時相容。
        if self.predictor is None:
            raise RuntimeError("Predictor ")
        model = self.model_loader.get_model()
        text_ids: Optional[torch.Tensor] = None
        inference_features = feature_seq
        if getattr(model, "numeric_encoder", None) is not None:
            inference_features = self.feature_pipeline.to_v2_patch(feature_seq)
            self.last_numeric_patches_ = inference_features
            text_ids = self._encode_context(
                context_text or self._default_context(symbol, current_price, regime_analysis)
            )
        output, latency_ms = self.predictor.predict(
            inference_features, text_ids=text_ids
        )

        # 4. 解析訊號
        signal = self.signal_interpreter.interpret(
            symbol=symbol,
            current_price=current_price,
            model_output=output,
            latency_ms=latency_ms,
            regime_analysis=regime_analysis
        )

        return signal

    def _get_tokenizer(self) -> Any:
        """載入全專案共用的中英 tokenizer。"""
        if self._tokenizer is not None:
            return self._tokenizer
        from nlp.bilingual_tokenizer import BilingualTokenizer

        tokenizer_path = self.model_loader.project_root / "model" / "tokenizer" / "vocab.json"
        self._tokenizer = (
            BilingualTokenizer.load(str(tokenizer_path))
            if tokenizer_path.exists()
            else BilingualTokenizer(vocab_size=16000)
        )
        return self._tokenizer

    def _encode_context(self, text: str) -> torch.Tensor:
        tokenizer = self._get_tokenizer()
        token_ids = tokenizer.encode(
            text, max_length=128, truncation=True, add_special_tokens=True
        )
        return torch.tensor(
            [token_ids], dtype=torch.long, device=self.model_loader.device
        )

    @staticmethod
    def _default_context(
        symbol: str, current_price: float, regime_analysis: Optional[Any]
    ) -> str:
        regime = "unknown"
        if regime_analysis is not None and hasattr(regime_analysis, "regime"):
            regime = str(regime_analysis.regime.value)
        return f"{symbol} current price {current_price:.8f}; market regime {regime}."

    def predict_with_explanation(
        self,
        symbol: str,
        current_price: float,
        klines: List[Dict],
        *,
        context_text: str = "",
        language: str = "zh",
        max_new_tokens: int = 24,
        **market_inputs: Any,
    ) -> Dict[str, Any]:
        """使用同一模型、同一次市場狀態產生交易決策與中英文說明。"""
        signal = self.predict(
            symbol=symbol,
            current_price=current_price,
            klines=klines,
            context_text=context_text,
            **market_inputs,
        )
        model = self.model_loader.get_model()
        if self.last_numeric_patches_ is None or not hasattr(model, "generate"):
            return {"signal": signal, "explanation": signal.reasoning, "language": language}

        prompt = (
            f"請用中文說明此交易決策：{signal.reasoning}"
            if language != "en"
            else f"Explain this trading decision in English: {signal.reasoning}"
        )
        tokenizer = self._get_tokenizer()
        input_ids = self._encode_context(prompt)
        numeric = torch.from_numpy(self.last_numeric_patches_).unsqueeze(0).to(
            self.model_loader.device
        )
        trained = bool(getattr(model, "is_trained", False))
        generation_budget = max_new_tokens if trained else 0
        generate = cast(Callable[..., torch.Tensor], getattr(model, "generate"))
        with torch.no_grad():
            output_ids = generate(
                input_ids,
                max_new_tokens=generation_budget,
                temperature=0.8,
                top_k=50,
                top_p=0.92,
                repetition_penalty=1.1,
                eos_token_id=getattr(tokenizer, "eos_token_id", None),
                numeric_patches=numeric,
            )
        generated = output_ids[0, input_ids.shape[1]:].tolist()
        explanation = tokenizer.decode(generated).strip() or signal.reasoning
        if not trained:
            explanation = f"[UNTRAINED/未訓練] {explanation}"
        signal.reasoning = explanation
        return {
            "signal": signal,
            "explanation": explanation,
            "language": language,
            "model_name": getattr(model, "model_name", UNIFIED_MODEL_NAME),
            "trained": trained,
        }

    def enable_v2_mode(self) -> None:
        """啟用已接通的 TinyLLM v2 16x64 → 65 維統一路徑。"""
        self.use_v2_mode = True
        logger.info("[InferenceEngine] unified v2 mode enabled")

    def reset_buffer(self) -> None:
        """清空滾動特徵視窗（回測切換 episode 或重新開始時呼叫）"""
        self._feature_buffer.clear()
        logger.debug("[InferenceEngine] feature buffer reset")

    def predict_batch(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[TradingSignal]:
        """

        Args:
            requests:  predict()

        Returns:
            TradingSignal
        """
        return [self.predict(**req) for req in requests]

    @property
    def is_ready(self) -> bool:
        """"""
        return self._is_ready

    def get_stats(self) -> Dict[str, Any]:
        """"""
        stats = {
            "is_ready": self._is_ready,
            "device": str(self.model_loader.device),
            "active_model": self.model_loader.active_model_name,
            "architecture": "TinyLLMv2",
            "v2_mode": self.use_v2_mode,
        }
        if self._is_ready:
            model = self.model_loader.get_model()
            stats["trained"] = bool(getattr(model, "is_trained", False))
            stats["parameters"] = sum(p.numel() for p in model.parameters())

        if self.predictor:
            stats.update(self.predictor.get_stats())

        return stats


# ============================================================================
#
# ============================================================================

def create_inference_engine(
    model_name: str = UNIFIED_MODEL_NAME,
    min_confidence: float = 0.5
) -> InferenceEngine:
    """

    :
        engine = create_inference_engine()
        signal = engine.predict("BTCUSDT", 50000, klines)
    """
    engine = InferenceEngine(min_confidence=min_confidence, warmup=False)
    engine.load_model(model_name)
    return engine


_SHARED_INFERENCE_ENGINE: Optional[InferenceEngine] = None


def get_shared_inference_engine(
    model_name: str = UNIFIED_MODEL_NAME,
    min_confidence: float = 0.5,
) -> InferenceEngine:
    """取得程序內唯一的模型與推論服務，供交易、聊天及自主循環共用。"""
    global _SHARED_INFERENCE_ENGINE
    if _SHARED_INFERENCE_ENGINE is None:
        _SHARED_INFERENCE_ENGINE = create_inference_engine(model_name, min_confidence)
    return _SHARED_INFERENCE_ENGINE


# ============================================================================
#
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        from backtest import HistoricalDataStream

        stream = HistoricalDataStream(symbol="BTCUSDT", interval="1h", speed_multiplier=0)
        klines = list(
            stream.get_klines_until_time(int(time.time() * 1000), limit=300) or []
        )
        if not klines:
            raise RuntimeError("本機沒有 BTCUSDT 1h 歷史資料，無法執行正式入口驗證")
        current_price = float(klines[-1].get("close", klines[-1].get("c", 0.0)))
        result = get_shared_inference_engine().predict_with_explanation(
            "BTCUSDT", current_price, klines, language="zh"
        )
        payload = dict(result)
        payload["signal"] = result["signal"].to_dict()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"[ERROR] {exc}")
        import traceback
        traceback.print_exc()
