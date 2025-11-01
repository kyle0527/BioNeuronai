"""Utility for scoring response novelty using bio-inspired neurons."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Union

import numpy as np

from ..core import BioNeuron
from ..improved_core import ImprovedBioNeuron

try:  # pragma: no cover - optional import for typing clarity
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore


ResponseLike = Union[str, "httpx.Response", object]


@dataclass
class NoveltyAnalysis:
    """Container for novelty results."""

    score: float
    threshold: float

    @property
    def is_novel(self) -> bool:
        return self.score >= self.threshold


class NoveltyAnalyzer:
    """Wrapper around BioNeuron/ImprovedBioNeuron to model normal responses."""

    ERROR_KEYWORDS = (
        "error", "exception", "stack trace", "sql", "syntax", "warning", "fail"
    )
    ANOMALY_KEYWORDS = (
        "unauthorized", "forbidden", "denied", "invalid", "alert", "hacked"
    )
    STRUCTURE_KEYWORDS = (
        "select", "union", "admin", "drop", "insert", "update", "delete"
    )
    FEATURE_NAMES = (
        "length",
        "digit_ratio",
        "upper_ratio",
        "symbol_ratio",
        "error_flag",
        "anomaly_flag",
        "structure_score",
        "status_feature",
        "status_bucket",
    )

    def __init__(
        self,
        *,
        use_improved: bool = True,
        novelty_threshold: float = 0.65,
        memory_len: int = 6,
        auto_adapt: bool = False,
    ) -> None:
        self.use_improved = use_improved
        self.novelty_threshold = float(novelty_threshold)
        self.memory_len = memory_len
        self.auto_adapt = auto_adapt and not use_improved  # avoid double-forward issues
        self._feature_count = len(self.FEATURE_NAMES)
        self._neuron = self._create_neuron()
        self._baseline_observed = False
        self._last_output = 0.0

    def _create_neuron(self):
        if self.use_improved:
            return ImprovedBioNeuron(
                num_inputs=self._feature_count,
                memory_len=self.memory_len,
                adaptive_threshold=True,
            )
        return BioNeuron(num_inputs=self._feature_count, memory_len=self.memory_len)

    def reset(self) -> None:
        """Reset the underlying neuron state."""
        self._neuron = self._create_neuron()
        self._baseline_observed = False
        self._last_output = 0.0

    def learn_normal(self, response: ResponseLike, status_code: int | None = None) -> NoveltyAnalysis:
        """Feed a known-good response to establish baseline patterns."""
        vector, derived_status = self._vectorize_response(response, status_code)
        if self.use_improved:
            # improved_hebbian_learn internally calls forward
            self._neuron.improved_hebbian_learn(vector, target=0.3)
        else:
            output = self._neuron.forward(vector)
            self._neuron.hebbian_learn(vector, output)
            self._last_output = output
        self._baseline_observed = True
        return NoveltyAnalysis(self._current_novelty(), self.novelty_threshold)

    def score_response(
        self,
        response: ResponseLike,
        status_code: int | None = None,
    ) -> NoveltyAnalysis:
        """Compute novelty score for an observed response."""
        vector, _ = self._vectorize_response(response, status_code)
        output = self._neuron.forward(vector)
        self._last_output = output
        score = self._current_novelty()
        if self.auto_adapt and self._baseline_observed and score < self.novelty_threshold * 0.6:
            # gently reinforce familiar responses without double-forwarding
            self._neuron.hebbian_learn(vector, output)
        return NoveltyAnalysis(score, self.novelty_threshold)

    # ------------------------------------------------------------------
    def _current_novelty(self) -> float:
        if self.use_improved:
            return float(self._neuron.enhanced_novelty_score())
        return float(self._neuron.novelty_score())

    def _vectorize_response(
        self, response: ResponseLike, status_code: int | None
    ) -> Tuple[np.ndarray, int | None]:
        text, derived_status = self._extract_text_and_status(response, status_code)
        length = min(len(text) / 4000.0, 1.0)
        digit_ratio = self._safe_ratio(sum(ch.isdigit() for ch in text), len(text))
        upper_ratio = self._safe_ratio(sum(ch.isupper() for ch in text), len(text))
        symbol_ratio = self._safe_ratio(
            sum(not ch.isalnum() and not ch.isspace() for ch in text), len(text)
        )
        lower_text = text.lower()
        error_flag = float(any(keyword in lower_text for keyword in self.ERROR_KEYWORDS))
        anomaly_flag = float(any(keyword in lower_text for keyword in self.ANOMALY_KEYWORDS))
        structure_score = self._safe_ratio(
            sum(keyword in lower_text for keyword in self.STRUCTURE_KEYWORDS),
            len(self.STRUCTURE_KEYWORDS),
        )
        status_feature = 0.0
        status_bucket = 0.0
        if derived_status is not None:
            status_feature = min(max((derived_status - 100.0) / 500.0, 0.0), 1.0)
            if derived_status >= 500:
                status_bucket = 1.0
            elif derived_status >= 400:
                status_bucket = 0.7
            elif derived_status >= 300:
                status_bucket = 0.4
            else:
                status_bucket = 0.1

        vector = np.array(
            [
                length,
                digit_ratio,
                upper_ratio,
                symbol_ratio,
                error_flag,
                anomaly_flag,
                structure_score,
                status_feature,
                status_bucket,
            ],
            dtype=np.float32,
        )
        return vector, derived_status

    def _extract_text_and_status(
        self, response: ResponseLike, status_code: int | None
    ) -> tuple[str, int | None]:
        if isinstance(response, str):
            return response, status_code
        text = getattr(response, "text", "")
        derived_status = status_code
        if derived_status is None:
            derived_status = getattr(response, "status_code", None)
        return str(text or ""), derived_status

    @staticmethod
    def _safe_ratio(numerator: int, denominator: int) -> float:
        return float(numerator) / float(denominator) if denominator else 0.0
