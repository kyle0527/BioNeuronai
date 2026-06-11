"""Autonomous planning operator.

The operator is an orchestrator.  It calls the existing planning and pretrade
modules, applies adaptation rules, records a decision ledger entry, and only
executes local paper orders when explicitly allowed.

v2 closed loop: the operator now keeps a persistent paper connector across
cycles, settles trade outcomes back into the decision ledger and the
AdaptiveLearningHub, and feeds the resulting learning state into the next
adaptation decision.  ``run_forever`` drives the continuous
observe → plan → check → adapt → execute → settle cycle.
"""

from __future__ import annotations

import asyncio
import logging
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

logger = logging.getLogger(__name__)


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
    learning_state_path: Optional[str] = None

    def normalized_action(self) -> str:
        action = self.intended_action.strip().upper()
        if action == "LONG":
            return "BUY"
        if action == "SHORT":
            return "SELL"
        return action


class AutonomousOperator:
    """Continuous autonomous observe-plan-check-adapt-execute-settle loop."""

    def __init__(
        self,
        config: Optional[AutonomousOperatorConfig] = None,
        *,
        plan_controller: Optional[Any] = None,
        pretrade_checker: Optional[Any] = None,
        adaptation_controller: Optional[AdaptationController] = None,
        ledger: Optional[DecisionLedger] = None,
        learning_hub: Optional[Any] = None,
    ) -> None:
        self.config = config or AutonomousOperatorConfig()
        # 預設元件延遲載入：注入 stub 時不需要任何重依賴
        if plan_controller is None:
            from .plan_controller import TradingPlanController
            plan_controller = TradingPlanController()
        if pretrade_checker is None:
            from .pretrade_automation import PreTradeCheckSystem
            pretrade_checker = PreTradeCheckSystem()
        self.plan_controller = plan_controller
        self.pretrade_checker = pretrade_checker
        self.adaptation_controller = adaptation_controller or AdaptationController()
        self.ledger = ledger or DecisionLedger(self.config.ledger_path)

        if learning_hub is None:
            try:
                from bioneuronai.core.adaptive_hub import AdaptiveLearningHub
                state_path = self.config.learning_state_path or (
                    _project_root() / "data" / "bioneuronai" / "learning" / "adaptive_hub.json"
                )
                learning_hub = AdaptiveLearningHub(state_path=state_path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("AdaptiveLearningHub unavailable: %s", exc)
                learning_hub = None
        self.learning_hub = learning_hub

        # 跨循環持續的 paper 連接器與未平倉追蹤
        self._paper_connector: Optional[Any] = None
        self._open_executions: Dict[str, Dict[str, Any]] = {}
        self._settled_this_cycle: List[Dict[str, Any]] = []
        self._cycle_count = 0

    # ── 主循環 ───────────────────────────────────────────────────────────

    async def run_once(self) -> Dict[str, Any]:
        started_at = datetime.now()
        self._cycle_count += 1

        # 1. 結算上一輪留下的倉位（觸發 SL/TP → outcome 回寫）
        settled = self._settle_open_positions()

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
        learning_state = self._build_learning_state()

        adaptation = self._evaluate_adaptation(
            plan_serialized, pretrade_results, ledger_summary, learning_state
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
            "cycle": self._cycle_count,
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
            "learning_state": learning_state,
            "settled_outcomes": settled,
            "adaptation": adaptation.to_dict(),
            "final_action": adaptation.action.value,
            "paper_execution": paper_execution,
        }
        self.ledger.append(record)
        return record

    def run_once_sync(self) -> Dict[str, Any]:
        return asyncio.run(self.run_once())

    async def run_forever(
        self,
        max_cycles: Optional[int] = None,
        interval_scale: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """持續自主迴圈：執行 → 等待 adaptation 建議的間隔 → 下一輪。

        Args:
            max_cycles: 最多執行幾輪（None = 無上限，直到 STOP）。
            interval_scale: 等待時間縮放（測試/回放時可設為 0）。

        Returns:
            所有循環的 ledger 紀錄。
        """
        records: List[Dict[str, Any]] = []
        while max_cycles is None or len(records) < max_cycles:
            record = await self.run_once()
            records.append(record)

            if record["final_action"] == AutonomousAction.STOP.value:
                logger.warning("Autonomous loop STOP triggered | cycle=%d", self._cycle_count)
                break

            minutes = float(
                record.get("adaptation", {}).get("next_interval_minutes", 60) or 60
            )
            sleep_sec = minutes * 60.0 * max(0.0, interval_scale)
            if sleep_sec > 0:
                await asyncio.sleep(sleep_sec)
        return records

    # ── 閉環：結果結算與學習狀態 ─────────────────────────────────────────

    def _build_learning_state(self) -> Optional[Dict[str, Any]]:
        if self.learning_hub is None:
            return None
        try:
            return self.learning_hub.get_learning_state()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("learning state unavailable: %s", exc)
            return None

    def _evaluate_adaptation(
        self,
        plan_serialized: Dict[str, Any],
        pretrade_results: List[Dict[str, Any]],
        ledger_summary: Dict[str, Any],
        learning_state: Optional[Dict[str, Any]],
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "mode": self.config.mode,
            "plan": plan_serialized,
            "pretrade_results": pretrade_results,
            "ledger_summary": ledger_summary,
            "intended_action": self.config.normalized_action(),
        }
        try:
            return self.adaptation_controller.evaluate(
                **kwargs, learning_state=learning_state
            )
        except TypeError:
            # 注入的舊版 controller 不認得 learning_state → 退回舊簽名
            return self.adaptation_controller.evaluate(**kwargs)

    def _settle_open_positions(self) -> List[Dict[str, Any]]:
        """用最新市價更新持倉，觸發 SL/TP 結算；回傳本輪已實現的結果。"""
        self._settled_this_cycle = []
        if not self._open_executions or self._paper_connector is None:
            return []
        connector = self._paper_connector
        for symbol in list(self._open_executions.keys()):
            try:
                market = connector.get_ticker_price(symbol)
                price = float(getattr(market, "close", 0.0) or 0.0)
                if price > 0:
                    connector.virtual_account.update_price(symbol, price)
            except Exception as exc:
                logger.warning("settle failed for %s: %s", symbol, exc)
        return list(self._settled_this_cycle)

    def _on_paper_close(
        self,
        symbol: str,
        realized_pnl: float,
        entry_price: float,
        exit_price: float,
        exit_reason: str,
    ) -> None:
        """VirtualAccount 平倉回調 → outcome 回寫 ledger + 學習中樞。"""
        execution = self._open_executions.pop(symbol, None)
        side = (execution or {}).get("side", "BUY")
        strategy = (execution or {}).get("strategy", "autonomous_paper")

        if entry_price > 0 and exit_price > 0:
            direction_mult = 1.0 if side == "BUY" else -1.0
            pnl_pct = (exit_price - entry_price) / entry_price * direction_mult
        else:
            pnl_pct = 0.001 if realized_pnl > 0 else -0.001

        outcome_record = {
            "type": "trade_outcome",
            "symbol": symbol,
            "strategy": strategy,
            "outcome": {
                "pnl": realized_pnl,
                "pnl_pct": pnl_pct,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "exit_reason": exit_reason,
            },
        }
        try:
            self.ledger.append(outcome_record)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("ledger outcome append failed: %s", exc)

        if self.learning_hub is not None:
            try:
                self.learning_hub.record_trade(
                    strategy_name=strategy, symbol=symbol, pnl_pct=pnl_pct
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("learning hub record failed: %s", exc)

        if hasattr(self, "_settled_this_cycle"):
            self._settled_this_cycle.append(outcome_record["outcome"] | {"symbol": symbol})

        logger.info(
            "Autonomous outcome settled | %s pnl=%.4f (%.3f%%) reason=%s",
            symbol, realized_pnl, pnl_pct * 100, exit_reason,
        )

    # ── 既有步驟 ─────────────────────────────────────────────────────────

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

    def _get_paper_connector(self) -> Any:
        """持久化 paper 連接器：跨循環保留倉位，平倉回調接 outcome 閉環。"""
        if self._paper_connector is None:
            from bioneuronai.data.paper_binance import PaperBinanceFuturesConnector

            self._paper_connector = PaperBinanceFuturesConnector(
                testnet=False,
                initial_balance=self.config.paper_initial_balance,
            )
            self._paper_connector.virtual_account.set_close_callback(self._on_paper_close)
        return self._paper_connector

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

        connector = self._get_paper_connector()
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

        self._open_executions[str(selected_symbol)] = {
            "side": side,
            "quantity": quantity,
            "entry_price": price,
            "strategy": "autonomous_paper",
            "opened_at": datetime.now().isoformat(),
        }

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
