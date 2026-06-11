"""目標層級追蹤 — 自主運作的「在不在軌道上」判斷（最小可用版）

真正自主的系統需要知道自己離目標多遠，而不只是逐筆反應。
這個模組是該能力的第一階段：

✅ 已實作（最小版）：
- 以可配置的目標（期望值 / 勝率 / 連敗容忍 / 回撤上限）對照
  AdaptiveLearningHub 的學習狀態與 ledger 摘要
- 輸出 ON_TRACK / AT_RISK / OFF_TRACK 與違反項清單、建議風險縮放
- AutonomousOperator 每輪呼叫並寫入 decision ledger（僅監測記錄）

❌ 尚未實作（擴充點，介面已預留）：
- 多時間尺度目標（1h/1d/1w 分層追蹤）→ GoalConfig.horizon 欄位已留
- recommended_risk_scale 自動回饋到 AdaptationController
  （目前只記錄，不自動執行；接點在 AutonomousOperator._evaluate_adaptation）
- Sharpe / Sortino 等風險調整後指標（需要逐筆報酬序列持久化）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GoalConfig:
    """目標定義。horizon 欄位為多時間尺度擴充點（目前未分層使用）。"""

    name: str = "default"
    horizon: str = "session"            # 擴充點：1h / 1d / 1w / session
    min_ewma_pnl_pct: float = 0.0       # 期望值至少打平
    min_ewma_win_rate: float = 0.40
    max_consecutive_losses: int = 5
    max_drawdown_pct: float = 5.0
    min_trades_to_judge: int = 10       # 樣本不足前不下判斷


@dataclass
class GoalReport:
    status: str                          # ON_TRACK / AT_RISK / OFF_TRACK / INSUFFICIENT_DATA
    violations: List[str] = field(default_factory=list)
    recommended_risk_scale: float = 1.0  # 目前僅記錄，尚未自動回饋（見模組 docstring）
    goal_name: str = "default"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "violations": list(self.violations),
            "recommended_risk_scale": self.recommended_risk_scale,
            "goal_name": self.goal_name,
        }


class GoalTracker:
    """對照目標評估目前學習狀態。

    使用方式：
        tracker = GoalTracker(GoalConfig(min_ewma_win_rate=0.45))
        report = tracker.evaluate(learning_state, ledger_summary)
    """

    def __init__(self, config: Optional[GoalConfig] = None) -> None:
        self.config = config or GoalConfig()

    def evaluate(
        self,
        learning_state: Optional[Dict[str, Any]] = None,
        ledger_summary: Optional[Dict[str, Any]] = None,
    ) -> GoalReport:
        cfg = self.config
        state = learning_state or {}
        ledger = ledger_summary or {}

        trades = int(state.get("trades", 0) or 0)
        if trades < cfg.min_trades_to_judge:
            return GoalReport(status="INSUFFICIENT_DATA", goal_name=cfg.name)

        violations: List[str] = []

        ewma_pnl = float(state.get("ewma_pnl_pct", 0.0) or 0.0)
        if ewma_pnl < cfg.min_ewma_pnl_pct:
            violations.append(f"ewma_pnl_pct_{ewma_pnl:.4f}_below_{cfg.min_ewma_pnl_pct}")

        win_rate = float(state.get("ewma_win_rate", 0.5) or 0.5)
        if win_rate < cfg.min_ewma_win_rate:
            violations.append(f"ewma_win_rate_{win_rate:.2f}_below_{cfg.min_ewma_win_rate}")

        consecutive = int(state.get("consecutive_losses", 0) or 0)
        if consecutive >= cfg.max_consecutive_losses:
            violations.append(f"consecutive_losses_{consecutive}")

        drawdown = float(ledger.get("max_drawdown_pct", 0.0) or 0.0)
        if drawdown >= cfg.max_drawdown_pct:
            violations.append(f"drawdown_{drawdown:.2f}_exceeds_{cfg.max_drawdown_pct}")

        if not violations:
            return GoalReport(status="ON_TRACK", goal_name=cfg.name)

        # 違反越多越偏離軌道；風險縮放建議只記錄，尚未自動執行
        if len(violations) == 1:
            return GoalReport(
                status="AT_RISK",
                violations=violations,
                recommended_risk_scale=0.75,
                goal_name=cfg.name,
            )
        return GoalReport(
            status="OFF_TRACK",
            violations=violations,
            recommended_risk_scale=0.5,
            goal_name=cfg.name,
        )


__all__ = ["GoalConfig", "GoalReport", "GoalTracker"]
