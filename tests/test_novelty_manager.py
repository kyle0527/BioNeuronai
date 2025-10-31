from enum import Enum

import pytest

from bioneuronai.common import DetectionRuleResult, UnifiedSmartDetectionManager


class DummyConfidence(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class DummySeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@pytest.fixture()
def novelty_manager() -> UnifiedSmartDetectionManager:
    manager = UnifiedSmartDetectionManager(input_dim=5, novelty_threshold=0.5)
    baseline_vector = [0.1, 0.2, 0.05, 0.0, 0.1]
    for _ in range(6):
        manager.record_normal_profile(baseline_vector)
    return manager


def test_high_novelty_increases_risk(novelty_manager: UnifiedSmartDetectionManager) -> None:
    rule = DetectionRuleResult(
        confidence=DummyConfidence.MEDIUM,
        severity=DummySeverity.LOW,
        metadata={"engine": "unit-test"},
    )

    baseline_vector = [0.1, 0.2, 0.05, 0.0, 0.1]
    normal_decision = novelty_manager.combine_rule_and_novelty(rule, baseline_vector)

    novel_vector = [0.9, 0.85, 0.7, 1.0, 0.95]
    high_decision = novelty_manager.combine_rule_and_novelty(rule, novel_vector)

    assert high_decision.novelty_score > normal_decision.novelty_score
    assert high_decision.risk_label in {"high", "critical"}

    # Decision confidence should escalate beyond the baseline score
    high_conf_name = getattr(high_decision.confidence, "name", str(high_decision.confidence))
    assert high_conf_name in {"HIGH", "CRITICAL"}


def test_feedback_reinforces_baseline(novelty_manager: UnifiedSmartDetectionManager) -> None:
    rule = DetectionRuleResult(
        confidence=DummyConfidence.MEDIUM,
        severity=DummySeverity.LOW,
        metadata={"engine": "unit-test"},
    )

    novel_vector = [0.8, 0.75, 0.6, 0.9, 0.88]
    decision_before = novelty_manager.combine_rule_and_novelty(rule, novel_vector)
    assert decision_before.risk_label in {"high", "critical"}

    novelty_manager.feedback(novel_vector, confirmed_anomaly=False)
    decision_after = novelty_manager.combine_rule_and_novelty(rule, novel_vector)

    assert decision_after.novelty_score < decision_before.novelty_score
    assert decision_after.risk_score <= decision_before.risk_score
