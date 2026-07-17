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
import json
import logging
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta
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
    if is_dataclass(value) and not isinstance(value, type):
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
    # 卡單偵測與自動平倉：持倉超過 N 輪未平倉即標記（0 = 停用）。
    # 實作：已實作自動強制出場，會下達反向 reduce-only 市價單平倉。
    max_position_hold_cycles: int = 0
    # 每 N 輪執行一次 AIReflectionLoop（0 = 停用；僅在 run_forever 時生效）
    reflect_every_cycles: int = 0
    reflection_sample_size: int = 50
    ai_context: str = ""
    ai_language: str = "zh"
    news_hours: int = 24
    news_refresh_minute: int = 5

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
        goal_tracker: Optional[Any] = None,
        inference_engine: Optional[Any] = None,
        trading_engine: Optional[Any] = None,
    ) -> None:
        self.config = config or AutonomousOperatorConfig()
        # 預設元件延遲載入：注入 stub 時不需要任何重依賴
        if plan_controller is None:
            from .plan_controller import TradingPlanController
            plan_controller = TradingPlanController()
        if pretrade_checker is None:
            from .pretrade_automation import PreTradeCheckSystem
            pretrade_checker = PreTradeCheckSystem(
                account_balance=self.config.account_balance,
            )
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

        # 目標層級追蹤（最小版：監測並記錄，尚未自動回饋風險參數）
        self.goal_tracker = goal_tracker
        self.inference_engine = inference_engine
        self.trading_engine = trading_engine

        # 學習狀態 provider 擴充點：讓 OnlineLearner / EpisodicMemory 等
        # 模組的統計接入自主迴圈（merge 進 learning_state，記入 ledger）
        self._state_providers: Dict[str, Any] = {}

        # 跨循環持續的 paper 連接器與未平倉追蹤
        self._paper_connector: Optional[Any] = None
        self._open_executions: Dict[str, Dict[str, Any]] = {}
        self._settled_this_cycle: List[Dict[str, Any]] = []
        self._cycle_count = 0
        self._news_analyzer: Optional[Any] = None
        self._last_news_refresh_slot: Optional[str] = None
        self._last_news_refresh_summary: Optional[Dict[str, Any]] = None

    def register_state_provider(self, name: str, provider: Any) -> None:
        """註冊額外的學習狀態來源（如 LoRA learner 的 get_stats）。

        provider 為無參數 callable，回傳 dict；其輸出會以 ``name`` 為 key
        併入每輪的 learning_state，寫進 decision ledger 供審計與後續規則使用。
        例：operator.register_state_provider("lora", online_learner.get_stats)
        """
        self._state_providers[str(name)] = provider

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
        news_refresh = self._refresh_news_memory_if_due(klines)
        news_memory = self._collect_news_memory_snapshot()
        strategy_snapshot = self._collect_strategy_snapshot(klines)
        ai_input_snapshot = self._build_ai_input_snapshot(
            klines=klines,
            plan=plan_serialized,
            candidates=candidates,
            news_memory=news_memory,
            strategy_snapshot=strategy_snapshot,
        )
        ai_decision = self._run_unified_ai(klines, ai_input_snapshot)
        cycle_action = self._resolve_cycle_action(ai_decision)
        pretrade_results = (
            self._run_pretrade(candidates, cycle_action)
            if cycle_action in {"BUY", "SELL"}
            else []
        )
        ledger_summary = self.ledger.summarize(limit=100)
        learning_state = self._build_learning_state()
        stale_positions = self._check_stale_positions()

        goal_report: Optional[Dict[str, Any]] = None
        if self.goal_tracker is not None:
            try:
                goal_report = self.goal_tracker.evaluate(
                    learning_state=learning_state, ledger_summary=ledger_summary
                ).to_dict()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("goal tracker failed: %s", exc)

        adaptation = self._evaluate_adaptation(
            plan_serialized,
            pretrade_results,
            ledger_summary,
            learning_state,
            cycle_action,
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
            "intended_action": cycle_action,
            "news_refresh": news_refresh,
            "ai_input_snapshot": ai_input_snapshot,
            "ai_decision": ai_decision,
            "candidates": candidates,
            "plan_status": plan_serialized.get("status"),
            "plan_execution_ready": plan_serialized.get("execution_ready"),
            "plan_blocking_steps": plan_serialized.get("blocking_steps", []),
            "pretrade_summary": self._pretrade_summary(pretrade_results),
            "ledger_summary": ledger_summary,
            "learning_state": learning_state,
            "goal_report": goal_report,
            "stale_positions": stale_positions,
            "settled_outcomes": settled,
            "adaptation": adaptation.to_dict(),
            "final_action": adaptation.action.value,
            "paper_execution": paper_execution,
        }
        self.ledger.append(record)
        self._maybe_run_reflection()
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
            base_sleep = minutes * 60.0
            until_news_refresh = self._seconds_until_next_news_refresh(datetime.now())
            sleep_sec = min(base_sleep, until_news_refresh) * max(0.0, interval_scale)
            if sleep_sec > 0:
                await asyncio.sleep(sleep_sec)
        return records

    # ── 閉環：結果結算與學習狀態 ─────────────────────────────────────────

    def _build_learning_state(self) -> Optional[Dict[str, Any]]:
        state: Optional[Dict[str, Any]] = None
        if self.learning_hub is not None:
            try:
                state = self.learning_hub.get_learning_state()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("learning state unavailable: %s", exc)

        # 註冊的額外狀態來源（LoRA learner、記憶層統計等）
        if self._state_providers:
            state = state or {}
            for name, provider in self._state_providers.items():
                try:
                    state[name] = provider()
                except Exception as exc:  # pragma: no cover - defensive
                    state[name] = {"error": str(exc)}
        return state

    def _check_stale_positions(self) -> List[Dict[str, Any]]:
        """卡單偵測與自動平倉：持倉超過 max_position_hold_cycles 輪即自動下反向 reduce-only 單平倉。

        這會透過 connector 下達反向 reduce-only 市價單，並走 _on_paper_close 既有的 outcome 回寫路徑。
        """
        limit = int(self.config.max_position_hold_cycles or 0)
        if limit <= 0:
            return []
        stale: List[Dict[str, Any]] = []
        connector = self._get_paper_connector()
        from bioneuronai.trading.virtual_account import PositionSide

        for symbol in list(self._open_executions.keys()):
            execution = self._open_executions[symbol]
            held = self._cycle_count - int(execution.get("opened_cycle", self._cycle_count))
            if held >= limit:
                va = getattr(connector, "virtual_account", None)
                positions = getattr(va, "positions", None) if va is not None else None
                position = positions.get(symbol) if positions else None
                if position and position.quantity > 0:
                    qty = position.quantity
                    side = "SELL" if position.side == PositionSide.LONG else "BUY"
                    logger.warning(
                        "STALE position detected | %s held %d cycles (limit=%d). "
                        "自動平倉強制出場中... 下單方向: %s, 數量: %.4f",
                        symbol, held, limit, side, qty
                    )
                    try:
                        order = connector.place_order(
                            symbol=symbol,
                            side=side,
                            order_type="MARKET",
                            quantity=qty,
                            reduce_only=True,
                        )
                        stale.append({
                            "symbol": symbol,
                            "held_cycles": held,
                            "limit": limit,
                            "action": "FLATTED",
                            "order_id": order.order_id if order else None,
                        })
                    except Exception as exc:
                        logger.error("放置卡單平倉委託失敗 (%s): %s", symbol, exc)
                        stale.append({
                            "symbol": symbol,
                            "held_cycles": held,
                            "limit": limit,
                            "action": "FLAT_ERROR",
                            "error": str(exc),
                        })
                else:
                    logger.warning(
                        "STALE position ghost cleanup | %s 帳戶中已無實質持倉但存在於 open_executions 中。自動清除紀錄。",
                        symbol
                    )
                    self._open_executions.pop(symbol, None)
                    stale.append({
                        "symbol": symbol,
                        "held_cycles": held,
                        "limit": limit,
                        "action": "GHOST_CLEANUP",
                    })
        return stale

    def _evaluate_adaptation(
        self,
        plan_serialized: Dict[str, Any],
        pretrade_results: List[Dict[str, Any]],
        ledger_summary: Dict[str, Any],
        learning_state: Optional[Dict[str, Any]],
        intended_action: str,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "mode": self.config.mode,
            "plan": plan_serialized,
            "pretrade_results": pretrade_results,
            "ledger_summary": ledger_summary,
            "intended_action": intended_action,
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

        cal_idx = (execution or {}).get("calibration_record_index")
        if cal_idx is not None:
            try:
                from bioneuronai.risk_management.confidence_calibrator import (
                    get_confidence_calibrator,
                )

                if get_confidence_calibrator().record_outcome_by_index(int(cal_idx), pnl_pct):
                    logger.info(
                        "Calibration outcome recorded | %s index=%s pnl_pct=%.4f",
                        symbol,
                        cal_idx,
                        pnl_pct,
                    )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("calibration record_outcome failed: %s", exc)

        logger.info(
            "Autonomous outcome settled | %s pnl=%.4f (%.3f%%) reason=%s",
            symbol, realized_pnl, pnl_pct * 100, exit_reason,
        )

    def _maybe_run_reflection(self) -> None:
        """P5：可選反思迴圈，依 reflect_every_cycles 在 run_forever 中觸發。"""
        every = int(self.config.reflect_every_cycles or 0)
        if every <= 0 or self._cycle_count <= 0 or self._cycle_count % every != 0:
            return
        try:
            from bioneuronai.planning.reflection_loop import AIReflectionLoop

            result = AIReflectionLoop().run_reflection_cycle(
                k=int(self.config.reflection_sample_size or 50)
            )
            self.ledger.append({
                "type": "reflection_cycle",
                "cycle": self._cycle_count,
                "status": result.status,
                "total_trades_analyzed": result.total_trades_analyzed,
                "losing_trades_count": result.losing_trades_count,
                "recommended_temperature": result.recommended_temperature,
                "learning_report_path": result.learning_report_path,
            })
            logger.info(
                "Reflection cycle completed | cycle=%d status=%s analyzed=%d",
                self._cycle_count,
                result.status,
                result.total_trades_analyzed,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("reflection cycle failed: %s", exc)

    def _has_open_position(self, connector: Any, symbol: str) -> bool:
        if symbol in self._open_executions:
            return True
        va = getattr(connector, "virtual_account", None)
        positions = getattr(va, "positions", None) if va is not None else None
        if not positions:
            return False
        position = positions.get(symbol)
        if position is None:
            return False
        return float(getattr(position, "quantity", 0.0) or 0.0) > 0.0

    def _resolve_paper_quantity(
        self,
        adaptation: Dict[str, Any],
        order_params: Dict[str, Any],
        price: float,
    ) -> tuple[float, str]:
        """優先採 pretrade quantity；無效時退回 legacy notional 公式。"""
        risk_multiplier = float(adaptation.get("risk_multiplier", 1.0) or 1.0)
        raw_qty = float(order_params.get("quantity", 0.0) or 0.0)
        if raw_qty > 0 and price > 0:
            return max(raw_qty * risk_multiplier, 0.0), "pretrade_quantity"

        notional = (
            self.config.paper_initial_balance
            * self.config.paper_notional_fraction
            * risk_multiplier
        )
        return max(notional / price, 0.0), "paper_notional_fraction"

    def _calibration_index_from_pretrade(self, selected: Dict[str, Any]) -> Optional[int]:
        risk_calc = selected.get("risk_calculation")
        if isinstance(risk_calc, dict):
            idx = risk_calc.get("calibration_record_index")
            return int(idx) if idx is not None else None
        if risk_calc is not None:
            idx = getattr(risk_calc, "calibration_record_index", None)
            return int(idx) if idx is not None else None
        return None

    # ── 既有步驟 ─────────────────────────────────────────────────────────

    def _load_klines(self) -> List[Dict[str, Any]]:
        try:
            from backtest import DEFAULT_DATA_DIR, HistoricalDataStream

            stream = HistoricalDataStream(
                symbol=self.config.symbol,
                interval=self.config.interval,
                data_dir=self.config.data_dir or DEFAULT_DATA_DIR,
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

    def _run_pretrade(
        self, candidates: List[str], intended_action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        action = intended_action or self.config.normalized_action()
        for symbol in candidates:
            try:
                result = self.pretrade_checker.execute_pretrade_check(
                    symbol=symbol,
                    intended_action=action,
                    signal_source="AUTONOMOUS_OPERATOR",
                )
                results.append(_serialize(result))
            except Exception as exc:
                results.append({
                    "symbol": symbol,
                    "overall_assessment": {"status": "ERROR", "error": str(exc)},
                })
        return results

    def _get_inference_engine(self) -> Any:
        """延遲取得全程序唯一的統一模型服務。"""
        if self.inference_engine is None:
            from bioneuronai.core.inference_engine import get_shared_inference_engine

            self.inference_engine = get_shared_inference_engine()
        return self.inference_engine

    def _get_news_analyzer(self) -> Any:
        """延遲建立新聞模組唯一實例；自主迴圈不另建第二套新聞狀態。"""
        if self._news_analyzer is None:
            from bioneuronai.analysis.news.analyzer import CryptoNewsAnalyzer

            self._news_analyzer = CryptoNewsAnalyzer(enable_rag_ingest=False)
        return self._news_analyzer

    def _refresh_news_memory_if_due(
        self,
        klines: List[Dict[str, Any]],
        at_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """啟動時與每小時第 5 分鐘後更新一次完整新聞及事件記憶。"""
        now = at_time or datetime.now()
        slot = now.strftime("%Y-%m-%dT%H")
        due = self._last_news_refresh_slot is None or (
            now.minute >= self.config.news_refresh_minute
            and self._last_news_refresh_slot != slot
        )
        if not due:
            return {
                "refreshed": False,
                "last_refresh_slot": self._last_news_refresh_slot,
                "last_refresh_summary": self._last_news_refresh_summary,
            }

        analyzer = self._get_news_analyzer()
        result = analyzer.analyze_news(
            self.config.symbol,
            hours=self.config.news_hours,
        )

        from bioneuronai.analysis.news.event_contract import get_contract_manager

        latest = klines[-1] if klines else {}
        price = float(latest.get("close", latest.get("c", 0.0)) or 0.0)
        get_contract_manager().validate_expired_contracts(
            {self.config.symbol: price, "CRYPTO": price}
        )
        article_ids = [
            f"{article.source_id}:{article.url}"
            for article in result.articles
            if article.language in {"zh", "en"}
        ]
        summary = {
            "refreshed_at": now.isoformat(),
            "refresh_slot": slot,
            "article_count": len(article_ids),
            "article_ids": article_ids,
            "languages": sorted(
                {
                    article.language
                    for article in result.articles
                    if article.language in {"zh", "en"}
                }
            ),
            "event_updates": len(analyzer.last_event_updates),
        }
        self._last_news_refresh_slot = slot
        self._last_news_refresh_summary = summary
        return {"refreshed": True, **summary}

    def _collect_news_memory_snapshot(self) -> Dict[str, Any]:
        """平常決策只讀濃縮事件記憶與程式化經濟日曆，不讀新聞全文。"""
        from bioneuronai.analysis.news.event_contract import get_contract_manager

        memory = get_contract_manager().get_memory_snapshot(symbol=self.config.symbol)
        memory["economic_calendar"] = self._collect_economic_snapshot()
        return memory

    def _seconds_until_next_news_refresh(self, now: datetime) -> float:
        """計算到下一個本地時間 HH:05 的秒數。"""
        target = now.replace(
            minute=self.config.news_refresh_minute,
            second=0,
            microsecond=0,
        )
        if target <= now:
            target += timedelta(hours=1)
        return max(1.0, (target - now).total_seconds())

    def _collect_strategy_snapshot(self, klines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """取得既有策略模組的戰術候選；AI 讀取它們，但不由策略取代 AI 決策。"""
        if not klines:
            raise RuntimeError("缺少真實 K 線，無法建立策略模組輸入")
        engine = self._get_trading_engine()
        ohlcv = engine._convert_klines_to_ohlcv(klines)
        if len(ohlcv) < 20:
            raise RuntimeError("真實 K 線不足 20 根，無法建立策略模組輸入")
        strategy = engine.strategy
        signals = strategy.get_strategy_signals(ohlcv, symbol=self.config.symbol)
        actionable = strategy.get_actionable_signal(ohlcv, symbol=self.config.symbol)
        return {
            "candidate_signals": _serialize(signals),
            "actionable_candidate": _serialize(actionable) if actionable else None,
        }

    def _collect_economic_snapshot(self) -> Dict[str, Any]:
        """取得既有經濟日曆模組的已排程事件，不將其偽裝成新聞。"""
        from bioneuronai.analysis.daily_report.market_data import MarketDataCollector

        collector = MarketDataCollector(connector=self._get_trading_engine().connector)
        return {"events": collector.check_economic_calendar()}

    def _build_ai_input_snapshot(
        self,
        *,
        klines: List[Dict[str, Any]],
        plan: Dict[str, Any],
        candidates: List[str],
        news_memory: Dict[str, Any],
        strategy_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        """建立每次自主決策唯一、可重播的多模態輸入快照。"""
        latest = klines[-1] if klines else {}
        current_price = float(latest.get("close", latest.get("c", 0.0)) or 0.0)
        context_text = self._build_compact_decision_context(
            news_memory,
            strategy_snapshot,
        )
        return {
            "snapshot_version": "ai_input_v2",
            "created_at": datetime.now().isoformat(),
            "symbol": self.config.symbol,
            "market": {
                "interval": self.config.interval,
                "klines_count": len(klines),
                "latest_kline": _serialize(latest),
                "current_price": current_price,
            },
            "news_memory": news_memory,
            "strategy": strategy_snapshot,
            "planning": {
                "status": plan.get("status"),
                "execution_ready": plan.get("execution_ready"),
                "blocking_steps": plan.get("blocking_steps", []),
                "candidate_symbols": candidates,
            },
            "natural_language_context": context_text,
        }

    @staticmethod
    def _build_compact_decision_context(
        news_memory: Dict[str, Any],
        strategy_snapshot: Dict[str, Any],
    ) -> str:
        """把各模組獨立輸出壓成決策摘要；不包含任何原始新聞全文。"""
        from nlp.bilingual_tokenizer import BilingualTokenizer

        tokenizer_path = _project_root() / "model" / "tokenizer" / "vocab.json"
        tokenizer = BilingualTokenizer.load(str(tokenizer_path))
        active_events = news_memory.get("active_events") or []
        if active_events:
            event_parts = [
                (
                    f"{event.get('event_type')} importance="
                    f"{float(event.get('current_importance', 0.0)):.2f} remaining="
                    f"{float(event.get('remaining_hours', 0.0)):.1f}h"
                )
                for event in active_events[:3]
            ]
            lines = ["News memory: " + " | ".join(event_parts)]
        else:
            lines = ["News memory: no active strategic event."]

        actionable = strategy_snapshot.get("actionable_candidate") or {}
        if isinstance(actionable, dict):
            strategy_name = actionable.get("strategy_name") or "strategy_selector"
            direction = actionable.get("direction") or "no entry"
            confidence = actionable.get("confidence")
            lines.append(
                f"Strategy: {strategy_name}; {direction}; confidence={confidence}. AI decides."
            )

        economic_snapshot = news_memory.get("economic_calendar") or {}
        events = economic_snapshot.get("events") or []
        if events:
            lines.append("Calendar: " + str(events[0])[:50])

        accepted: List[str] = []
        for line in lines:
            for limit in (None, 80, 60, 40, 20):
                truncated = line if limit is None else line[:limit]
                candidate = "\n".join([*accepted, truncated])
                if len(tokenizer.encode(candidate, add_special_tokens=True)) <= 128:
                    accepted.append(truncated)
                    break
        if not accepted:
            raise RuntimeError("無法在 128 token 限制內建立 AI 自然語言輸入")
        return "\n".join(accepted)

    def _run_unified_ai(
        self,
        klines: List[Dict[str, Any]],
        ai_input_snapshot: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """以單一模型處理本輪多模態輸入，保存原始 65 維輸出而非自動生成人類報告。"""
        if not klines:
            return None
        latest = klines[-1]
        current_price = float(latest.get("close", latest.get("c", 0.0)) or 0.0)
        if current_price <= 0:
            return None
        try:
            engine = self._get_inference_engine()
            signal = engine.predict(
                symbol=self.config.symbol,
                current_price=current_price,
                klines=klines,
                context_text=str(ai_input_snapshot["natural_language_context"]),
            )
            inference_snapshot = engine.get_last_inference_snapshot()
            ai_input_snapshot["model_input"] = {
                "tokenizer_version": inference_snapshot["tokenizer_version"],
                "text_token_ids": inference_snapshot["text_token_ids"],
                "numeric_patches": inference_snapshot["numeric_patches"],
            }
            hold_period, valid_until = self._decision_validity(
                inference_snapshot["raw_signal"]
            )
            return {
                "signal": signal.to_dict(),
                "raw_signal": inference_snapshot["raw_signal"],
                "model_name": inference_snapshot["model_name"],
                "tokenizer_version": inference_snapshot["tokenizer_version"],
                "trained": inference_snapshot["model_trained"],
                "decision_hold_period": hold_period,
                "decision_valid_until": valid_until,
            }
        except Exception as exc:
            raise RuntimeError(f"統一 AI 決策失敗：{exc}") from exc

    @staticmethod
    def _decision_validity(raw_signal: List[float]) -> tuple[str, str]:
        """依模型 65 維 hold-period 輸出建立本輪決策有效期限。"""
        from nlp.tiny_llm_v2 import HOLD_PERIOD_LABELS

        if len(raw_signal) != 65:
            raise ValueError(f"統一模型輸出必須為 65 維，實際為 {len(raw_signal)}")
        hold_period = HOLD_PERIOD_LABELS[max(range(10), key=lambda index: raw_signal[19 + index])]
        duration_by_label = {
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
            "2d": timedelta(days=2),
            "3d": timedelta(days=3),
            "1w": timedelta(days=7),
            "2w": timedelta(days=14),
            "exit": timedelta(minutes=0),
        }
        return hold_period, (datetime.now() + duration_by_label[hold_period]).isoformat()

    def _resolve_cycle_action(self, ai_decision: Optional[Dict[str, Any]]) -> str:
        """只採用本輪 AI 的明確方向；中性或失敗不以預設 BUY/SELL 覆蓋。"""
        if not ai_decision:
            return "HOLD"
        signal = ai_decision.get("signal")
        if not isinstance(signal, dict):
            return "HOLD"
        signal_type = str(signal.get("signal_type") or "").lower()
        if "long" in signal_type:
            return "BUY"
        if "short" in signal_type:
            return "SELL"
        return "HOLD"

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
        """取得 TradingEngine 所持有的唯一 paper 連接器。"""
        if self._paper_connector is None:
            trading_engine = self._get_trading_engine()
            self._paper_connector = trading_engine.connector
            self._paper_connector.virtual_account.set_close_callback(
                self._on_shared_paper_close
            )
        return self._paper_connector

    def _get_trading_engine(self) -> Any:
        """延遲建立唯一 TradingEngine；planning 不再持有第二套執行器。"""
        if self.trading_engine is None:
            from bioneuronai.core.trading_engine import TradingEngine

            self.trading_engine = TradingEngine(
                enable_ai_model=True,
                paper_trading=True,
                paper_initial_balance=self.config.paper_initial_balance,
            )
        return self.trading_engine

    def _on_shared_paper_close(
        self,
        symbol: str,
        realized_pnl: float,
        entry_price: float,
        exit_price: float,
        exit_reason: str,
    ) -> None:
        """一次平倉同時回寫 TradingEngine 與 autonomous ledger。"""
        if self.trading_engine is not None:
            self.trading_engine._on_paper_close(
                symbol, realized_pnl, entry_price, exit_price, exit_reason
            )
        self._on_paper_close(
            symbol, realized_pnl, entry_price, exit_price, exit_reason
        )

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
        symbol_key = str(selected_symbol)

        if self._has_open_position(connector, symbol_key):
            logger.warning(
                "paper execution skipped | %s already has open position or pending execution",
                symbol_key,
            )
            return {
                "symbol": symbol_key,
                "skipped": True,
                "reason": "existing_position",
                "paper_state": connector.get_paper_state(),
            }

        market = connector.get_ticker_price(symbol_key)
        price = float(getattr(market, "close", 0.0) or 0.0)
        if price <= 0:
            raise RuntimeError(f"paper execution failed: price unavailable for {selected_symbol}")

        order_params = selected.get("order_parameters", {})
        if not isinstance(order_params, dict):
            order_params = _serialize(order_params) if order_params else {}

        quantity, qty_source = self._resolve_paper_quantity(adaptation, order_params, price)
        if quantity <= 0:
            raise RuntimeError(
                f"paper execution failed: invalid quantity for {selected_symbol} (source={qty_source})"
            )

        stop_loss = order_params.get("stop_loss_price")
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

        selected_action = str(adaptation.get("selected_action") or "").upper()
        side = "BUY" if selected_action == "BUY" else "SELL"
        if self.trading_engine is not None or self._paper_connector is None:
            order = self._get_trading_engine().execute_prepared_order(
                symbol=str(selected_symbol),
                side=side,
                quantity=quantity,
                stop_loss=float(stop_loss) if stop_loss else None,
                take_profit=float(take_profit) if take_profit else None,
            )
        else:
            order = connector.place_order(
                symbol=str(selected_symbol),
                side=side,
                order_type="MARKET",
                quantity=quantity,
                stop_loss=float(stop_loss) if stop_loss else None,
                take_profit=float(take_profit) if take_profit else None,
            )

        self._open_executions[symbol_key] = {
            "side": side,
            "quantity": quantity,
            "entry_price": price,
            "strategy": "autonomous_paper",
            "opened_at": datetime.now().isoformat(),
            "opened_cycle": self._cycle_count,
            "calibration_record_index": self._calibration_index_from_pretrade(selected),
            "quantity_source": qty_source,
        }

        return {
            "symbol": selected_symbol,
            "side": side,
            "quantity": quantity,
            "quantity_source": qty_source,
            "notional": quantity * price,
            "price": price,
            "order": order.to_dict() if order else None,
            "paper_state": connector.get_paper_state(),
        }


__all__ = ["AutonomousOperator", "AutonomousOperatorConfig"]
