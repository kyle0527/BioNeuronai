from __future__ import annotations

from aiva_common.enums import Confidence

from bioneuronai.production_idor_module import ProductionHorizontalIDOREngine
from bioneuronai.production_sqli_module import ProductionUnionSQLiEngine
from bioneuronai.enhanced_auth_module import WeakCredentialEngine
from bioneuronai.security.novelty_analyzer import NoveltyAnalyzer


class FakeElapsed:
    def __init__(self, seconds: float = 0.1) -> None:
        self._seconds = seconds

    def total_seconds(self) -> float:
        return self._seconds


class FakeResponse:
    def __init__(
        self,
        text: str,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        elapsed: float = 0.1,
    ) -> None:
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.elapsed = FakeElapsed(elapsed)


def test_union_sql_novelty_adjusts_confidence() -> None:
    engine = ProductionUnionSQLiEngine()
    engine.novelty_analyzer.reset()
    baseline = FakeResponse("Welcome to the dashboard, user.")
    engine.novelty_analyzer.learn_normal(baseline)

    suspicious = FakeResponse(
        "SQL syntax error near 'UNION SELECT password FROM users' -- stack trace",
        status_code=500,
    )

    analysis = engine._analyze_union_response(
        suspicious,
        baseline,
        "' UNION SELECT",
        engine.novelty_analyzer,
    )

    assert analysis["novelty_score"] >= engine.novelty_analyzer.novelty_threshold
    assert analysis["confidence"] >= Confidence.MEDIUM
    assert any("新穎度分數" in ev for ev in analysis["evidence"])


def test_horizontal_idor_flags_manual_review_on_high_novelty() -> None:
    engine = ProductionHorizontalIDOREngine()
    engine.novelty_analyzer.reset()
    baseline = FakeResponse("Profile for user id=1 with limited data", status_code=200)
    engine.novelty_analyzer.learn_normal(baseline)

    anomalous = FakeResponse(
        "403 Forbidden: administrator action required -- unexpected audit message",
        status_code=403,
    )

    analysis = engine._analyze_horizontal_response(
        baseline,
        anomalous,
        original_id="1",
        test_id="2",
        novelty_analyzer=engine.novelty_analyzer,
    )

    assert not analysis["is_vulnerable"]
    assert analysis["manual_review"]
    assert analysis["novelty_score"] >= engine.novelty_analyzer.novelty_threshold


def test_weak_credential_novelty_boosts_confidence() -> None:
    engine = WeakCredentialEngine()
    engine.novelty_analyzer.reset()
    baseline = FakeResponse("Login page - please enter your credentials", status_code=200)
    engine.novelty_analyzer.learn_normal(baseline)

    success_response = FakeResponse(
        "Welcome Admin! Dashboard loading... unexpected debug output error",
        status_code=200,
        cookies={"session": "abc123"},
    )

    analysis = engine._analyze_login_response(success_response, "admin")

    assert analysis["success"]
    assert analysis["confidence"] == Confidence.HIGH
    assert analysis["novelty_score"] >= engine.novelty_analyzer.novelty_threshold


def test_novelty_analyzer_considers_status_and_content() -> None:
    analyzer = NoveltyAnalyzer(use_improved=True, novelty_threshold=0.35)

    baseline = FakeResponse("OK", status_code=200)
    analyzer.learn_normal(baseline)

    similar = FakeResponse("OK", status_code=200)
    assert analyzer.score_response(similar).score < analyzer.novelty_threshold

    status_shift = FakeResponse("OK", status_code=503)
    assert analyzer.score_response(status_shift).score >= analyzer.novelty_threshold

    content_shift = FakeResponse(
        "Warning: SQL exception stack trace UNION SELECT password FROM users", status_code=200
    )
    assert analyzer.score_response(content_shift).score >= analyzer.novelty_threshold
