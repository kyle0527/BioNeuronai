"""Action Record — P0 核心：每次決策的完整快照

這是連接「交易決策」和「在線學習」的橋樑。
沒有完整的 Action Record，LoRA 就沒有訓練材料，成績單也無從生成。

每個 ActionRecord 在三個時間點被填寫：
  T0 - 決策前：features + model logits + market context
  T1 - 進場：entry_price + 實際執行細節
  T2 - 出場：exit + pnl + outcome → 轉為 ExperienceRecord 進記憶層
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class ActionRecord:
    """一次完整的決策-執行-結果循環快照。"""

    record_id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])
    symbol: str = ""
    created_at: float = field(default_factory=time.time)

    # ── T0：決策時刻 ────────────────────────────────────────────────────
    # 模型輸入（16 根 K 線 × 64 特徵）
    numeric_patches: Optional[List[List[float]]] = None

    # 模型原始輸出（65 維）
    raw_signal: Optional[List[float]] = None

    # 解碼後的核心決策
    direction: str = "NEUTRAL"          # LONG / SHORT / NEUTRAL
    confidence: float = 0.0
    uncertainty: float = 0.5
    suggested_leverage: int = 1
    suggested_position_size: float = 0.0
    suggested_stop_loss_pct: float = 0.02
    suggested_take_profit_pct: float = 0.04
    suggested_hold_period: str = "1h"

    # 多時框一致性（5 個時框）
    multi_tf_align: Optional[List[float]] = None

    # K 線形態（20 種）
    detected_patterns: Optional[List[float]] = None

    # 市場狀態
    market_regime: str = "UNKNOWN"
    regime_probs: Optional[List[float]] = None

    # 進場時的市場快照
    price_at_decision: float = 0.0
    bid_ask_spread: float = 0.0
    orderbook_imbalance: float = 0.0
    funding_rate: float = 0.0
    liquidation_volume_5min: float = 0.0
    price_change_5min_pct: float = 0.0
    volatility_1h: float = 0.0

    # 進場時讀到的文字（新聞/社群）
    text_context: Optional[str] = None

    # 決策來源（strategy 分數和 ai 分數）
    strategy_signal_score: float = 0.0
    ai_signal_score: float = 0.0
    fusion_score: float = 0.0

    # 潛在嵌入（來自 raw_signal[55:65]，供相似度搜索）
    embedding: Optional[List[float]] = None

    # ── T1：進場執行 ─────────────────────────────────────────────────────
    order_id: Optional[str] = None
    entry_price: float = 0.0
    entry_time: float = 0.0
    actual_leverage: int = 1
    actual_position_size: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    slippage_pct: float = 0.0
    entry_fee_pct: float = 0.0

    # ── T2：出場結果 ─────────────────────────────────────────────────────
    exit_price: float = 0.0
    exit_time: float = 0.0
    exit_fee_pct: float = 0.0
    hold_duration_sec: float = 0.0
    pnl_pct: float = 0.0
    pnl_usd: float = 0.0
    exit_reason: str = "PENDING"        # SL_HIT / TP_HIT / MANUAL / TIMEOUT / PENDING
    outcome: str = "PENDING"            # WIN / LOSS / BREAKEVEN / PENDING

    # RL 獎勵（出場後計算）
    reward: float = 0.0

    def fill_decision(
        self,
        symbol: str,
        numeric_patches: np.ndarray,
        raw_signal: np.ndarray,
        decoded: Dict[str, Any],
        market_snapshot: Dict[str, Any],
        text_context: Optional[str] = None,
    ) -> "ActionRecord":
        """T0：填入決策時刻的資料。"""
        self.symbol = symbol
        self.numeric_patches = numeric_patches.tolist()
        self.raw_signal = raw_signal.tolist()

        def _item(v: Any) -> float:
            if hasattr(v, "item"):
                return float(v.item())
            return float(v)

        def _tolist(v: Any) -> List[float]:
            values = v.tolist() if hasattr(v, "tolist") else list(v)
            return [float(item) for item in values]

        dir_probs = decoded.get("direction_probs")
        if dir_probs is not None:
            idx = int(np.argmax(_tolist(dir_probs)))
            self.direction = ["LONG", "NEUTRAL", "SHORT"][idx]

        conf_probs = decoded.get("confidence_probs")
        if conf_probs is not None:
            conf_list = _tolist(conf_probs)
            self.confidence = float(np.sum(np.array(conf_list) * [0.3, 0.6, 0.9]))

        self.uncertainty = _item(decoded.get("uncertainty", 0.5))
        lev_probs = decoded.get("leverage_probs")
        if lev_probs is not None:
            self.suggested_leverage = int(np.argmax(_tolist(lev_probs))) + 1
        self.suggested_position_size = _item(decoded.get("position_size", 0.0))
        self.suggested_stop_loss_pct = _item(decoded.get("stop_loss_pct", 0.02))
        self.suggested_take_profit_pct = _item(decoded.get("take_profit_pct", 0.04))

        hold_probs = decoded.get("hold_period_probs")
        if hold_probs is not None:
            from bioneuronai.memory.episodic_memory import ExperienceRecord
            from nlp.tiny_llm_v2 import HOLD_PERIOD_LABELS
            idx = int(np.argmax(_tolist(hold_probs)))
            self.suggested_hold_period = HOLD_PERIOD_LABELS[idx]

        self.multi_tf_align = _tolist(decoded.get("multi_tf_align", [0.0] * 5))
        self.detected_patterns = _tolist(decoded.get("pattern_probs", [0.0] * 20))

        regime_probs = decoded.get("regime_probs")
        if regime_probs is not None:
            from nlp.tiny_llm_v2 import REGIME_LABELS
            self.regime_probs = _tolist(regime_probs)
            self.market_regime = REGIME_LABELS[int(np.argmax(self.regime_probs))]

        # 從 raw_signal 取後 10 維作為 embedding（供相似度搜索）
        if len(raw_signal) >= 65:
            self.embedding = raw_signal[55:65].tolist()

        self.text_context = text_context
        self.price_at_decision = float(market_snapshot.get("price", 0))
        self.bid_ask_spread = float(market_snapshot.get("bid_ask_spread", 0))
        self.orderbook_imbalance = float(market_snapshot.get("orderbook_imbalance", 0))
        self.funding_rate = float(market_snapshot.get("funding_rate", 0))
        self.liquidation_volume_5min = float(market_snapshot.get("liquidation_volume_5min", 0))
        self.price_change_5min_pct = float(market_snapshot.get("price_change_5min_pct", 0))
        self.volatility_1h = float(market_snapshot.get("volatility_1h", 0))

        return self

    def fill_entry(
        self,
        order_id: str,
        entry_price: float,
        leverage: int,
        position_size: float,
        stop_loss: float,
        take_profit: float,
        slippage_pct: float = 0.0,
        fee_pct: float = 0.00055,
    ) -> "ActionRecord":
        """T1：進場執行後填入。"""
        self.order_id = order_id
        self.entry_price = entry_price
        self.entry_time = time.time()
        self.actual_leverage = leverage
        self.actual_position_size = position_size
        self.stop_loss_price = stop_loss
        self.take_profit_price = take_profit
        self.slippage_pct = slippage_pct
        self.entry_fee_pct = fee_pct
        return self

    def fill_exit(
        self,
        exit_price: float,
        exit_reason: str,
        fee_pct: float = 0.00055,
    ) -> "ActionRecord":
        """T2：出場後填入，計算損益與 reward。"""
        self.exit_price = exit_price
        self.exit_time = time.time()
        self.exit_fee_pct = fee_pct
        self.hold_duration_sec = self.exit_time - self.entry_time
        self.exit_reason = exit_reason

        if self.entry_price > 0:
            direction_mult = 1.0 if self.direction == "LONG" else -1.0
            raw_pnl = (exit_price - self.entry_price) / self.entry_price * direction_mult
            total_fee = self.entry_fee_pct + fee_pct + self.slippage_pct
            self.pnl_pct = raw_pnl - total_fee
            self.pnl_usd = self.pnl_pct * self.actual_position_size

        self.outcome = (
            "WIN" if self.pnl_pct > 0.001
            else "LOSS" if self.pnl_pct < -0.001
            else "BREAKEVEN"
        )

        # 多目標 Reward shaping：盈虧 × 時間效率 × 校準 × 風控紀律
        from bioneuronai.core.reward import compute_reward
        self.reward = compute_reward(
            pnl_pct=self.pnl_pct,
            hold_duration_sec=self.hold_duration_sec,
            uncertainty=self.uncertainty,
            confidence=self.confidence,
            exit_reason=exit_reason,
        )

        return self

    def to_experience_record(self):
        """轉換為 ExperienceRecord，推入 EpisodicMemory。"""
        from bioneuronai.memory.episodic_memory import ExperienceRecord
        return ExperienceRecord(
            record_id=self.record_id,
            symbol=self.symbol,
            timestamp=self.created_at,
            numeric_patches=self.numeric_patches or [],
            text_context=self.text_context,
            raw_signal=self.raw_signal or [],
            decoded_direction=self.direction,
            decoded_confidence=self.confidence,
            decoded_uncertainty=self.uncertainty,
            action_taken=("BUY" if self.direction == "LONG" else
                          "SELL" if self.direction == "SHORT" else "HOLD"),
            entry_price=self.entry_price,
            stop_loss=self.stop_loss_price,
            take_profit=self.take_profit_price,
            position_size=self.actual_position_size,
            exit_price=self.exit_price,
            pnl_pct=self.pnl_pct,
            hold_duration_sec=self.hold_duration_sec,
            outcome=self.outcome,
            reward=self.reward,
            market_regime=self.market_regime,
            volatility_1h=self.volatility_1h,
            liquidation_volume_usd=self.liquidation_volume_5min,
            funding_rate=self.funding_rate,
            price_change_5min_pct=self.price_change_5min_pct,
            embedding=self.embedding,
        )

    def to_dict(self) -> Dict[str, Any]:
        d = self.__dict__.copy()
        return d

    def is_complete(self) -> bool:
        return self.outcome != "PENDING"

    def __repr__(self) -> str:
        return (
            f"ActionRecord({self.symbol} {self.direction} "
            f"conf={self.confidence:.2f} unc={self.uncertainty:.2f} "
            f"pnl={self.pnl_pct*100:.2f}% [{self.outcome}])"
        )
