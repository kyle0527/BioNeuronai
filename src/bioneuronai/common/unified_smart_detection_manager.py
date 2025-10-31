"""Smart detection manager that blends rule signals with novelty analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Sequence

import numpy as np

from .response_novelty_analyzer import ResponseNoveltyAnalyzer


@dataclass(slots=True)
class DetectionRuleResult:
    """Container describing the outcome of a rule-based detector."""

    confidence: Any  # Typically a ``Confidence`` enum from ``aiva_common``
    severity: Any  # Typically a ``Severity`` enum
    metadata: MutableMapping[str, Any] | None = None


@dataclass(slots=True)
class DetectionDecision:
    """Final blended decision returned by the smart manager."""

    confidence: Any
    severity: Any
    novelty_score: float
    confidence_score: float
    risk_score: float
    risk_label: str


class UnifiedSmartDetectionManager:
    """Fuse handcrafted rules with BioNeuron driven novelty scoring."""

    _CONFIDENCE_TO_SCORE = {
        "LOW": 0.3,
        "MEDIUM": 0.6,
        "HIGH": 0.85,
        "CRITICAL": 0.95,
    }

    _SEVERITY_TO_SCORE = {
        "INFO": 0.1,
        "LOW": 0.3,
        "MEDIUM": 0.6,
        "HIGH": 0.8,
        "CRITICAL": 0.95,
    }

    _RISK_BUCKETS = (
        (0.25, "low"),
        (0.55, "medium"),
        (0.75, "high"),
        (1.01, "critical"),
    )

    def __init__(
        self,
        *,
        input_dim: int = 5,
        novelty_threshold: float = 0.55,
        novelty_weight: float = 0.35,
    ) -> None:
        self.novelty_threshold = float(novelty_threshold)
        self.novelty_weight = float(np.clip(novelty_weight, 0.1, 0.8))
        self.novelty_analyzer = ResponseNoveltyAnalyzer(input_dim)

    # ------------------------------------------------------------------
    # Baseline handling
    # ------------------------------------------------------------------
    def record_normal_profile(
        self, feature_vector: Sequence[float], *, context: Mapping[str, Any] | None = None
    ) -> None:
        """Add a known-good response feature vector to the novelty baseline."""

        self.novelty_analyzer.observe_baseline(feature_vector)

    def feedback(
        self,
        feature_vector: Sequence[float],
        *,
        confirmed_anomaly: bool,
    ) -> None:
        """Incorporate analyst feedback to refine the novelty model."""

        self.novelty_analyzer.learn_from_feedback(feature_vector, confirmed_anomaly)

    # ------------------------------------------------------------------
    # Scoring / fusion
    # ------------------------------------------------------------------
    def combine_rule_and_novelty(
        self,
        rule_result: DetectionRuleResult,
        feature_vector: Sequence[float],
        *,
        context: Mapping[str, Any] | None = None,
    ) -> DetectionDecision:
        """Blend rule and novelty evidence to obtain a unified decision."""

        novelty = self.novelty_analyzer.score(feature_vector)
        base_conf_score = self._confidence_to_score(rule_result.confidence)
        base_sev_score = self._severity_to_score(rule_result.severity)

        weight = self.novelty_weight
        if novelty >= self.novelty_threshold * 1.5:
            weight = min(0.75, weight + 0.25)
        elif novelty >= self.novelty_threshold:
            weight = min(0.6, weight + 0.15)
        elif novelty < self.novelty_threshold * 0.5:
            weight = max(0.2, weight - 0.1)

        combined_conf_score = (1 - weight) * base_conf_score + weight * max(
            base_conf_score, novelty
        )
        combined_conf_score = float(np.clip(combined_conf_score, 0.0, 1.0))

        severity_bonus = 0.0
        if novelty > self.novelty_threshold:
            severity_bonus = 0.2 * (novelty - self.novelty_threshold)
        combined_sev_score = float(
            np.clip(base_sev_score + severity_bonus, 0.0, 1.0)
        )

        final_conf = self._score_to_confidence(rule_result.confidence, combined_conf_score)
        final_sev = self._score_to_severity(rule_result.severity, combined_sev_score)

        risk_score = float(np.clip((combined_conf_score + combined_sev_score) / 2.0, 0.0, 1.0))
        risk_label = self._score_to_risk_label(risk_score)

        return DetectionDecision(
            confidence=final_conf,
            severity=final_sev,
            novelty_score=float(novelty),
            confidence_score=combined_conf_score,
            risk_score=risk_score,
            risk_label=risk_label,
        )

    # ------------------------------------------------------------------
    # Helpers for mapping enum values to floats and back
    # ------------------------------------------------------------------
    def _confidence_to_score(self, confidence: Any) -> float:
        key = getattr(confidence, "name", str(confidence)).upper()
        return float(self._CONFIDENCE_TO_SCORE.get(key, 0.5))

    def _severity_to_score(self, severity: Any) -> float:
        key = getattr(severity, "name", str(severity)).upper()
        return float(self._SEVERITY_TO_SCORE.get(key, 0.4))

    def _score_to_confidence(self, original: Any, score: float) -> Any:
        key = self._closest_key(self._CONFIDENCE_TO_SCORE, score)
        return self._cast_like(original, key)

    def _score_to_severity(self, original: Any, score: float) -> Any:
        key = self._closest_key(self._SEVERITY_TO_SCORE, score)
        return self._cast_like(original, key)

    @staticmethod
    def _closest_key(mapping: Mapping[str, float], score: float) -> str:
        score = float(np.clip(score, 0.0, 1.0))
        return min(mapping.items(), key=lambda item: abs(item[1] - score))[0]

    @staticmethod
    def _cast_like(original: Any, name: str) -> Any:
        if hasattr(original, "__class__") and hasattr(original.__class__, "__getitem__"):
            try:
                return original.__class__[name]
            except Exception:
                pass
        return name

    def _score_to_risk_label(self, score: float) -> str:
        for threshold, label in self._RISK_BUCKETS:
            if score <= threshold:
                return label
        return "critical"


__all__ = [
    "DetectionDecision",
    "DetectionRuleResult",
    "UnifiedSmartDetectionManager",
]
