"""Rule-based adaptation controller for autonomous operation.

This module does not analyze news or technical signals directly.  It consumes
the outputs of existing planning, pretrade, and ledger components and decides
how conservative the next autonomous step should be.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AutonomousMode(str, Enum):
    """Allowed autonomous operating modes."""

    ADVISOR = "advisor"
    PAPER_AUTO = "paper_auto"
    TESTNET_AUTO = "testnet_auto"
    LIVE_GUARDED = "live_guarded"


class AutonomousAction(str, Enum):
    """Final action selected by the autonomous operator."""

    ADVISE_ONLY = "advise_only"
    OBSERVE = "observe"
    WAIT = "wait"
    PAPER_TRADE = "paper_trade"
    TESTNET_CANDIDATE = "testnet_candidate"
    REQUIRES_HUMAN_CONFIRMATION = "requires_human_confirmation"
    STOP = "stop"


@dataclass
class AdaptationPolicy:
    """Conservative default thresholds for autonomous adaptation."""

    max_consecutive_losses: int = 3
    reduce_risk_drawdown_pct: float = 3.0
    stop_drawdown_pct: float = 5.0
    min_recent_win_rate: float = 0.45
    min_realized_for_win_rate: int = 20
    base_risk_multiplier: float = 1.0
    reduced_risk_multiplier: float = 0.5
    base_confidence_floor: float = 0.50
    raised_confidence_floor: float = 0.65
    base_interval_minutes: int = 60
    fast_interval_minutes: int = 15
    slow_interval_minutes: int = 120
    executable_statuses: tuple[str, ...] = ("EXECUTE", "CAUTIOUS_EXECUTE")
    # 學習狀態（AdaptiveLearningHub）相關閾值
    min_learning_samples: int = 10
    negative_expectancy_threshold: float = 0.0


@dataclass
class AdaptationDecision:
    """Decision returned by :class:`AdaptationController`."""

    action: AutonomousAction
    mode: AutonomousMode
    can_execute: bool
    risk_multiplier: float
    confidence_floor: float
    next_interval_minutes: int
    reasons: List[str] = field(default_factory=list)
    selected_symbol: Optional[str] = None
    selected_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "mode": self.mode.value,
            "can_execute": self.can_execute,
            "risk_multiplier": self.risk_multiplier,
            "confidence_floor": self.confidence_floor,
            "next_interval_minutes": self.next_interval_minutes,
            "reasons": list(self.reasons),
            "selected_symbol": self.selected_symbol,
            "selected_action": self.selected_action,
        }


class AdaptationController:
    """Select the next autonomous action from existing module outputs."""

    def __init__(self, policy: Optional[AdaptationPolicy] = None) -> None:
        self.policy = policy or AdaptationPolicy()

    def evaluate(
        self,
        *,
        mode: str | AutonomousMode,
        plan: Dict[str, Any],
        pretrade_results: List[Dict[str, Any]],
        ledger_summary: Dict[str, Any],
        intended_action: str,
        learning_state: Optional[Dict[str, Any]] = None,
    ) -> AdaptationDecision:
        mode_enum = mode if isinstance(mode, AutonomousMode) else AutonomousMode(str(mode))
        reasons: List[str] = []
        risk_multiplier = self.policy.base_risk_multiplier
        confidence_floor = self.policy.base_confidence_floor
        next_interval = self.policy.base_interval_minutes

        if not plan.get("execution_ready", plan.get("is_executable", False)):
            reasons.append("plan_not_executable")

        selected = self._select_executable_pretrade(pretrade_results)
        if selected is None:
            reasons.append("no_pretrade_candidate_passed")
        else:
            reasons.append("pretrade_candidate_available")

        if self._has_news_block(pretrade_results):
            reasons.append("news_or_fundamental_block")
            confidence_floor = max(confidence_floor, self.policy.raised_confidence_floor)
            next_interval = self.policy.fast_interval_minutes

        consecutive_losses = int(ledger_summary.get("consecutive_losses", 0) or 0)
        if consecutive_losses >= self.policy.max_consecutive_losses:
            reasons.append(f"consecutive_losses_{consecutive_losses}")
            risk_multiplier = min(risk_multiplier, self.policy.reduced_risk_multiplier)
            confidence_floor = max(confidence_floor, self.policy.raised_confidence_floor)
            next_interval = self.policy.slow_interval_minutes

        drawdown = float(ledger_summary.get("max_drawdown_pct", 0.0) or 0.0)
        if drawdown >= self.policy.stop_drawdown_pct:
            reasons.append(f"drawdown_stop_{drawdown:.2f}")
            return AdaptationDecision(
                action=AutonomousAction.STOP,
                mode=mode_enum,
                can_execute=False,
                risk_multiplier=0.0,
                confidence_floor=confidence_floor,
                next_interval_minutes=self.policy.slow_interval_minutes,
                reasons=reasons,
                selected_symbol=self._result_symbol(selected),
                selected_action=intended_action.upper(),
            )
        if drawdown >= self.policy.reduce_risk_drawdown_pct:
            reasons.append(f"drawdown_reduce_risk_{drawdown:.2f}")
            risk_multiplier = min(risk_multiplier, self.policy.reduced_risk_multiplier)
            confidence_floor = max(confidence_floor, self.policy.raised_confidence_floor)

        realized_count = int(ledger_summary.get("realized_count", 0) or 0)
        win_rate = ledger_summary.get("win_rate")
        if (
            realized_count >= self.policy.min_realized_for_win_rate
            and win_rate is not None
            and float(win_rate) < self.policy.min_recent_win_rate
        ):
            reasons.append(f"recent_win_rate_low_{float(win_rate):.2f}")
            risk_multiplier = min(risk_multiplier, self.policy.reduced_risk_multiplier)
            confidence_floor = max(confidence_floor, self.policy.raised_confidence_floor)

        # ── 學習狀態（來自 AdaptiveLearningHub）的自我修正規則 ────────────
        if learning_state:
            learn_trades = int(learning_state.get("trades", 0) or 0)
            if learn_trades >= self.policy.min_learning_samples:
                expectancy = float(learning_state.get("ewma_pnl_pct", 0.0) or 0.0)
                if expectancy < self.policy.negative_expectancy_threshold:
                    reasons.append(f"learning_expectancy_negative_{expectancy:.4f}")
                    risk_multiplier = min(risk_multiplier, self.policy.reduced_risk_multiplier)
                    confidence_floor = max(confidence_floor, self.policy.raised_confidence_floor)

                learn_consecutive = int(learning_state.get("consecutive_losses", 0) or 0)
                if learn_consecutive >= self.policy.max_consecutive_losses:
                    reasons.append(f"learning_consecutive_losses_{learn_consecutive}")
                    risk_multiplier = min(risk_multiplier, self.policy.reduced_risk_multiplier)
                    confidence_floor = max(confidence_floor, self.policy.raised_confidence_floor)
                    next_interval = self.policy.slow_interval_minutes

            # 中樞建議的全域風險倍率（取更保守者）
            hub_multiplier = learning_state.get("risk_multiplier")
            if hub_multiplier is not None:
                risk_multiplier = min(risk_multiplier, float(hub_multiplier))

            # 該幣對近期被學習層標記為應迴避 → 本輪不執行
            avoid_symbols = {
                str(s).upper() for s in learning_state.get("avoid_symbols", []) or []
            }
            selected_symbol_value = self._result_symbol(selected)
            if selected_symbol_value and selected_symbol_value.upper() in avoid_symbols:
                reasons.append("symbol_deprioritized_by_learning")

        plan_ok = not any(reason == "plan_not_executable" for reason in reasons)
        pretrade_ok = selected is not None
        can_execute = (
            plan_ok
            and pretrade_ok
            and "news_or_fundamental_block" not in reasons
            and "symbol_deprioritized_by_learning" not in reasons
        )

        if mode_enum == AutonomousMode.ADVISOR:
            action = AutonomousAction.ADVISE_ONLY
            can_execute = False
        elif not can_execute:
            action = AutonomousAction.WAIT if selected is not None else AutonomousAction.OBSERVE
        elif mode_enum == AutonomousMode.PAPER_AUTO:
            action = AutonomousAction.PAPER_TRADE
        elif mode_enum == AutonomousMode.TESTNET_AUTO:
            action = AutonomousAction.TESTNET_CANDIDATE
            can_execute = False
            reasons.append("testnet_execution_not_enabled_in_v1")
        else:
            action = AutonomousAction.REQUIRES_HUMAN_CONFIRMATION
            can_execute = False
            reasons.append("live_guarded_requires_human_confirmation")

        return AdaptationDecision(
            action=action,
            mode=mode_enum,
            can_execute=can_execute,
            risk_multiplier=risk_multiplier,
            confidence_floor=confidence_floor,
            next_interval_minutes=next_interval,
            reasons=reasons,
            selected_symbol=self._result_symbol(selected),
            selected_action=intended_action.upper(),
        )

    def _select_executable_pretrade(
        self, results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        for result in results:
            assessment = result.get("overall_assessment", {})
            status = str(assessment.get("status", "")).upper()
            if status in self.policy.executable_statuses:
                return result
        return None

    def _has_news_block(self, results: List[Dict[str, Any]]) -> bool:
        for result in results:
            fundamentals = result.get("fundamentals", {})
            if hasattr(fundamentals, "__dict__"):
                fundamentals = vars(fundamentals)
            no_major_negative = fundamentals.get("no_major_negative", True)
            fundamental_status = str(fundamentals.get("overall_status", "")).upper()
            if no_major_negative is False or fundamental_status in {"POOR", "REJECT", "REJECTED"}:
                return True
        return False

    @staticmethod
    def _result_symbol(result: Optional[Dict[str, Any]]) -> Optional[str]:
        if result is None:
            return None
        symbol = result.get("symbol")
        return str(symbol) if symbol else None


__all__ = [
    "AdaptationController",
    "AdaptationDecision",
    "AdaptationPolicy",
    "AutonomousAction",
    "AutonomousMode",
]
