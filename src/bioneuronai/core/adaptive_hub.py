"""自適應學習中樞 — 把交易結果轉成下一輪決策的調整量

這是「學習」和「決策」之間缺失的閉環：
- LoRA 更新改的是模型權重（慢、隱性）
- AdaptiveLearningHub 改的是策略權重與風險參數（快、顯性、可審計）

職責：
1. 記錄每筆平倉結果（策略 × 幣對 × 市場體制）
2. 維護 EWMA 期望值 / 勝率 / 連敗數（指數加權，近期表現權重高）
3. 產出 StrategySelector.load_performance_weights() 可直接使用的權重
4. 標記「該迴避的策略×幣對組合」（連續虧損 → 自動降權）
5. JSON 持久化 → 重啟後自適應狀態不歸零

設計原則：純標準庫 + 無模型依賴，任何執行路徑（引擎/自主迴圈/回測）都能掛。
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerfStats:
    """單一維度（策略 / 策略×幣對 / 全域）的滾動績效。"""

    trades: int = 0
    wins: int = 0
    ewma_pnl_pct: float = 0.0
    ewma_win_rate: float = 0.5
    consecutive_losses: int = 0
    last_pnl_pct: float = 0.0
    last_updated: float = 0.0

    def update(self, pnl_pct: float, alpha: float) -> None:
        self.trades += 1
        win = pnl_pct > 0
        if win:
            self.wins += 1
            self.consecutive_losses = 0
        elif pnl_pct < 0:
            self.consecutive_losses += 1
        self.ewma_pnl_pct = (1 - alpha) * self.ewma_pnl_pct + alpha * pnl_pct
        self.ewma_win_rate = (1 - alpha) * self.ewma_win_rate + alpha * (1.0 if win else 0.0)
        self.last_pnl_pct = pnl_pct
        self.last_updated = time.time()


class AdaptiveLearningHub:
    """交易結果 → 策略權重 / 風險調整的自適應閉環。

    使用方式：
        hub = AdaptiveLearningHub(state_path="data/.../adaptive_hub.json")
        hub.record_trade("trend_following", "BTCUSDT", pnl_pct=-0.012)
        selector.load_performance_weights(hub.get_strategy_weights())
        state = hub.get_learning_state()   # 給 AdaptationController / 自主迴圈
    """

    def __init__(
        self,
        state_path: str | Path = "data/bioneuronai/learning/adaptive_hub.json",
        ewma_alpha: float = 0.15,
        weight_sharpness: float = 30.0,
        min_weight: float = 0.05,
        min_samples: int = 5,
        avoid_expectancy_threshold: float = -0.003,
        avoid_consecutive_losses: int = 5,
    ) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.ewma_alpha = ewma_alpha
        self.weight_sharpness = weight_sharpness
        self.min_weight = min_weight
        self.min_samples = min_samples
        self.avoid_expectancy_threshold = avoid_expectancy_threshold
        self.avoid_consecutive_losses = avoid_consecutive_losses

        self._lock = threading.Lock()
        self.global_stats = PerfStats()
        self.strategy_stats: Dict[str, PerfStats] = {}
        self.pair_stats: Dict[str, Dict[str, PerfStats]] = {}  # strategy → symbol → stats
        self.regime_stats: Dict[str, PerfStats] = {}

        self._load()
        logger.info(
            "AdaptiveLearningHub ready | path=%s | strategies=%d | total_trades=%d",
            self.state_path, len(self.strategy_stats), self.global_stats.trades,
        )

    # ── 寫入端 ───────────────────────────────────────────────────────────

    def record_trade(
        self,
        strategy_name: str,
        symbol: str,
        pnl_pct: float,
        market_regime: Optional[str] = None,
    ) -> None:
        """平倉後記錄結果，更新所有維度的滾動績效並持久化。"""
        strategy_name = (strategy_name or "unknown").strip().lower()
        symbol = (symbol or "UNKNOWN").strip().upper()

        with self._lock:
            self.global_stats.update(pnl_pct, self.ewma_alpha)
            self.strategy_stats.setdefault(strategy_name, PerfStats()).update(
                pnl_pct, self.ewma_alpha
            )
            self.pair_stats.setdefault(strategy_name, {}).setdefault(
                symbol, PerfStats()
            ).update(pnl_pct, self.ewma_alpha)
            if market_regime:
                self.regime_stats.setdefault(str(market_regime), PerfStats()).update(
                    pnl_pct, self.ewma_alpha
                )
            self._save_locked()

        logger.info(
            "AdaptiveHub recorded | %s/%s pnl=%.3f%% | strategy_ewma=%.4f%% consec_loss=%d",
            strategy_name, symbol, pnl_pct * 100,
            self.strategy_stats[strategy_name].ewma_pnl_pct * 100,
            self.strategy_stats[strategy_name].consecutive_losses,
        )

    # ── 讀取端：決策層的調整量 ───────────────────────────────────────────

    def get_strategy_weights(self) -> Dict[str, float]:
        """以 EWMA 期望值產生策略權重（softmax with floor）。

        樣本不足的策略給中性權重（exp(0)=1），保留探索空間；
        所有權重有 min_weight 下限，避免任何策略被永久封殺。
        """
        import math

        with self._lock:
            if not self.strategy_stats:
                return {}
            raw: Dict[str, float] = {}
            for name, stats in self.strategy_stats.items():
                score = stats.ewma_pnl_pct if stats.trades >= self.min_samples else 0.0
                raw[name] = math.exp(self.weight_sharpness * score)

        total = sum(raw.values())
        weights = {k: v / total for k, v in raw.items()}
        # floor + 重新正規化
        weights = {k: max(self.min_weight, v) for k, v in weights.items()}
        total = sum(weights.values())
        return {k: round(v / total, 6) for k, v in weights.items()}

    def should_avoid(self, strategy_name: str, symbol: str) -> bool:
        """該策略在該幣對上是否表現差到應暫時迴避。"""
        stats = self.pair_stats.get((strategy_name or "").lower(), {}).get(
            (symbol or "").upper()
        )
        if stats is None or stats.trades < self.min_samples:
            return False
        if stats.consecutive_losses >= self.avoid_consecutive_losses:
            return True
        return stats.ewma_pnl_pct <= self.avoid_expectancy_threshold

    def get_avoid_list(self) -> List[Dict[str, str]]:
        """所有目前應迴避的（策略, 幣對）組合。"""
        out: List[Dict[str, str]] = []
        for strategy, symbols in self.pair_stats.items():
            for symbol in symbols:
                if self.should_avoid(strategy, symbol):
                    out.append({"strategy": strategy, "symbol": symbol})
        return out

    def get_risk_multiplier(self) -> float:
        """全域風險倍率：近期期望值為負或連敗時收縮倉位。"""
        g = self.global_stats
        if g.trades < self.min_samples:
            return 1.0
        if g.consecutive_losses >= 3 or g.ewma_pnl_pct < self.avoid_expectancy_threshold:
            return 0.5
        if g.ewma_pnl_pct < 0:
            return 0.75
        return 1.0

    def get_learning_state(self) -> Dict[str, Any]:
        """彙總給 AdaptationController / 自主迴圈 / 狀態 API 的學習狀態。"""
        avoid = self.get_avoid_list()
        return {
            "trades": self.global_stats.trades,
            "ewma_pnl_pct": round(self.global_stats.ewma_pnl_pct, 6),
            "ewma_win_rate": round(self.global_stats.ewma_win_rate, 4),
            "consecutive_losses": self.global_stats.consecutive_losses,
            "risk_multiplier": self.get_risk_multiplier(),
            "strategy_weights": self.get_strategy_weights(),
            "avoid_pairs": avoid,
            "avoid_symbols": sorted({row["symbol"] for row in avoid}),
            "by_strategy": {
                name: {
                    "trades": s.trades,
                    "ewma_pnl_pct": round(s.ewma_pnl_pct, 6),
                    "ewma_win_rate": round(s.ewma_win_rate, 4),
                    "consecutive_losses": s.consecutive_losses,
                }
                for name, s in self.strategy_stats.items()
            },
        }

    # ── 持久化 ───────────────────────────────────────────────────────────

    def _save_locked(self) -> None:
        payload = {
            "version": 1,
            "saved_at": time.time(),
            "global": asdict(self.global_stats),
            "strategies": {k: asdict(v) for k, v in self.strategy_stats.items()},
            "pairs": {
                strategy: {symbol: asdict(stats) for symbol, stats in symbols.items()}
                for strategy, symbols in self.pair_stats.items()
            },
            "regimes": {k: asdict(v) for k, v in self.regime_stats.items()},
        }
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.state_path)

    def save(self) -> None:
        with self._lock:
            self._save_locked()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.global_stats = PerfStats(**payload.get("global", {}))
            self.strategy_stats = {
                k: PerfStats(**v) for k, v in payload.get("strategies", {}).items()
            }
            self.pair_stats = {
                strategy: {symbol: PerfStats(**stats) for symbol, stats in symbols.items()}
                for strategy, symbols in payload.get("pairs", {}).items()
            }
            self.regime_stats = {
                k: PerfStats(**v) for k, v in payload.get("regimes", {}).items()
            }
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("AdaptiveLearningHub 狀態檔損毀，從空白開始: %s", exc)


__all__ = ["AdaptiveLearningHub", "PerfStats"]
