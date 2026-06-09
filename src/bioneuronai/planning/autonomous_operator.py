"""Autonomous planning operator.

The operator is an orchestrator.  It calls the existing planning and pretrade
modules, applies adaptation rules, records a decision ledger entry, and only
executes local paper orders when explicitly allowed.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .adaptation_controller import (
    AdaptationController,
    AutonomousAction,
    AutonomousMode,
)
from .decision_ledger import DecisionLedger
from .plan_controller import TradingPlanController
from .pretrade_automation import PreTradeCheckSystem


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if hasattr(value, "model_dump"):
        return _serialize(value.model_dump())
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return {
            key: _serialize(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return value


@dataclass
class AutonomousOperatorConfig:
    """Configuration for one autonomous operator run."""

    mode: str = AutonomousMode.ADVISOR.value
    symbol: str = "BTCUSDT"
    intended_action: str = "BUY"
    interval: str = "1h"
    account_balance: float = 10000.0
    klines_limit: int = 300
    max_pairs: int = 3
    data_dir: Optional[str] = None
    ledger_path: Optional[str] = None
    execute_paper: bool = False
    paper_initial_balance: float = 10000.0
    paper_notional_fraction: float = 0.01

    def normalized_action(self) -> str:
        action = self.intended_action.strip().upper()
        if action == "LONG":
            return "BUY"
        if action == "SHORT":
            return "SELL"
        return action


class AutonomousOperator:
    """Run one safe autonomous observe-plan-check-adapt cycle."""

    def __init__(
        self,
        config: Optional[AutonomousOperatorConfig] = None,
        *,
        plan_controller: Optional[Any] = None,
        pretrade_checker: Optional[Any] = None,
        adaptation_controller: Optional[AdaptationController] = None,
        ledger: Optional[DecisionLedger] = None,
    ) -> None:
        self.config = config or AutonomousOperatorConfig()
        self.plan_controller = plan_controller or TradingPlanController()
        self.pretrade_checker = pretrade_checker or PreTradeCheckSystem()
        self.adaptation_controller = adaptation_controller or AdaptationController()
        self.ledger = ledger or DecisionLedger(self.config.ledger_path)

    async def run_once(self) -> Dict[str, Any]:
        started_at = datetime.now()
        klines = self._load_klines()

        plan = await self.plan_controller.create_comprehensive_plan(
            klines=klines,
            account_balance=self.config.account_balance,
            symbol=self.config.symbol,
        )
        plan_serialized = _serialize(plan)

        candidates = self._extract_candidates(plan_serialized)
        pretrade_results = self._run_pretrade(candidates)
        ledger_summary = self.ledger.summarize(limit=100)

        adaptation = self.adaptation_controller.evaluate(
            mode=self.config.mode,
            plan=plan_serialized,
            pretrade_results=pretrade_results,
            ledger_summary=ledger_summary,
            intended_action=self.config.normalized_action(),
        )

        paper_execution: Optional[Dict[str, Any]] = None
        if (
            self.config.execute_paper
            and adaptation.action == AutonomousAction.PAPER_TRADE
            and adaptation.can_execute
        ):
            paper_execution = self._execute_paper_order(adaptation.to_dict(), pretrade_results)

        record: Dict[str, Any] = {
            "type": "autonomous_cycle",
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "mode": self.config.mode,
            "symbol": self.config.symbol,
            "intended_action": self.config.normalized_action(),
            "candidates": candidates,
            "plan_status": plan_serialized.get("status"),
            "plan_execution_ready": plan_serialized.get("execution_ready"),
            "plan_blocking_steps": plan_serialized.get("blocking_steps", []),
            "pretrade_summary": self._pretrade_summary(pretrade_results),
            "ledger_summary": ledger_summary,
            "adaptation": adaptation.to_dict(),
            "final_action": adaptation.action.value,
            "paper_execution": paper_execution,
        }
        self.ledger.append(record)
        return record

    def run_once_sync(self) -> Dict[str, Any]:
        return asyncio.run(self.run_once())

    def _load_klines(self) -> List[Dict[str, Any]]:
        try:
            from backtest import HistoricalDataStream

            stream = HistoricalDataStream(
                symbol=self.config.symbol,
                interval=self.config.interval,
                data_dir=self.config.data_dir,
                speed_multiplier=0,
            )
            target_open_time = int(datetime.now().timestamp() * 1000)
            klines = stream.get_klines_until_time(
                target_open_time,
                limit=self.config.klines_limit,
            )
            return list(klines or [])
        except Exception:
            return []

    def _extract_candidates(self, plan: Dict[str, Any]) -> List[str]:
        symbols: List[str] = []
        steps = plan.get("steps_results", {})
        step9 = steps.get(9) or steps.get("9") or {}

        recommended = step9.get("recommended_pair")
        if recommended:
            symbols.append(str(recommended))

        for item in step9.get("pairs", []) or []:
            if isinstance(item, dict) and item.get("symbol"):
                symbols.append(str(item["symbol"]))

        for item in step9.get("backup_pairs", []) or []:
            if isinstance(item, str):
                symbols.append(item)
            elif isinstance(item, dict) and item.get("symbol"):
                symbols.append(str(item["symbol"]))

        symbols.append(self.config.symbol)

        deduped: List[str] = []
        for symbol in symbols:
            normalized = symbol.upper()
            if normalized not in deduped:
                deduped.append(normalized)
        return deduped[: max(1, self.config.max_pairs)]

    def _run_pretrade(self, candidates: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for symbol in candidates:
            try:
                result = self.pretrade_checker.execute_pretrade_check(
                    symbol=symbol,
                    intended_action=self.config.normalized_action(),
                    signal_source="AUTONOMOUS_OPERATOR",
                )
                results.append(_serialize(result))
            except Exception as exc:
                results.append({
                    "symbol": symbol,
                    "overall_assessment": {"status": "ERROR", "error": str(exc)},
                })
        return results

    def _pretrade_summary(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        summary: List[Dict[str, Any]] = []
        for result in results:
            assessment = result.get("overall_assessment", {})
            summary.append({
                "symbol": result.get("symbol"),
                "status": assessment.get("status"),
                "score_percentage": assessment.get("score_percentage"),
                "technical_status": assessment.get("technical_status"),
                "fundamental_status": assessment.get("fundamental_status"),
                "risk_status": assessment.get("risk_status"),
                "recommendation": assessment.get("recommendation"),
            })
        return summary

    def _execute_paper_order(
        self,
        adaptation: Dict[str, Any],
        pretrade_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        selected_symbol = adaptation.get("selected_symbol") or self.config.symbol
        selected = next(
            (item for item in pretrade_results if item.get("symbol") == selected_symbol),
            pretrade_results[0] if pretrade_results else {},
        )

        from bioneuronai.data.paper_binance import PaperBinanceFuturesConnector

        connector = PaperBinanceFuturesConnector(
            testnet=False,
            initial_balance=self.config.paper_initial_balance,
        )
        market = connector.get_ticker_price(str(selected_symbol))
        price = float(getattr(market, "close", 0.0) or 0.0)
        if price <= 0:
            raise RuntimeError(f"paper execution failed: price unavailable for {selected_symbol}")

        notional = (
            self.config.paper_initial_balance
            * self.config.paper_notional_fraction
            * float(adaptation.get("risk_multiplier", 1.0) or 1.0)
        )
        quantity = max(notional / price, 0.0)

        order_params = selected.get("order_parameters", {})
        stop_loss = order_params.get("stop_loss_price") if isinstance(order_params, dict) else None
        take_profit_targets = (
            order_params.get("take_profit_targets")
            if isinstance(order_params, dict)
            else None
        )
        take_profit = None
        if isinstance(take_profit_targets, list) and take_profit_targets:
            first_target = take_profit_targets[0]
            if isinstance(first_target, dict):
                take_profit = first_target.get("price")

        side = "BUY" if self.config.normalized_action() == "BUY" else "SELL"
        order = connector.place_order(
            symbol=str(selected_symbol),
            side=side,
            order_type="MARKET",
            quantity=quantity,
            stop_loss=float(stop_loss) if stop_loss else None,
            take_profit=float(take_profit) if take_profit else None,
        )
        return {
            "symbol": selected_symbol,
            "side": side,
            "quantity": quantity,
            "notional": notional,
            "price": price,
            "order": order.to_dict() if order else None,
            "paper_state": connector.get_paper_state(),
        }


__all__ = ["AutonomousOperator", "AutonomousOperatorConfig"]
