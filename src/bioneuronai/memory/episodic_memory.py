"""記憶層：熱回放緩衝 + 冷極端事件金庫

設計哲學：
- 有發生過的就有可能再發生 → 罕見但重大的事件永遠不刪
- 普通經驗走優先回放（PER）→ 損失越大被採樣越頻繁
- 極端事件判斷標準：5 分鐘價格變動 > 3σ 或發生爆倉潮
- 冷庫存 JSONL（人可讀、可審計），熱庫存 in-memory deque
"""

from __future__ import annotations

import json
import logging
import math
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# 極端事件的閾值（以 z-score 計）
EXTREME_ZSCORE_THRESHOLD = 3.0
# 爆倉潮觸發：爆倉規模超過過去 24h 平均的倍數
LIQUIDATION_CASCADE_MULTIPLIER = 5.0
# 冷庫預設保留最近 N 條（按 symbol 分別統計）
COLD_VAULT_MAX_PER_SYMBOL = 10_000


@dataclass
class ExperienceRecord:
    """單次決策的完整快照。這是 LoRA 在線學習的訓練樣本。"""

    # 識別
    record_id: str
    symbol: str
    timestamp: float                        # Unix timestamp

    # 模型輸入
    numeric_patches: List[List[float]]      # shape [16][64]
    text_context: Optional[str] = None      # 進場前讀到的新聞/提問

    # 模型輸出（原始 65 維）
    raw_signal: List[float] = field(default_factory=list)
    decoded_direction: str = "NEUTRAL"
    decoded_confidence: float = 0.0
    decoded_uncertainty: float = 0.5

    # 交易決策
    action_taken: str = "HOLD"              # BUY / SELL / HOLD
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    position_size: float = 0.0

    # 交易結果（事後填入）
    exit_price: float = 0.0
    pnl_pct: float = 0.0
    hold_duration_sec: float = 0.0
    outcome: str = "PENDING"                # WIN / LOSS / BREAKEVEN / PENDING

    # RL 獎勵
    reward: float = 0.0

    # 市場上下文
    market_regime: str = "UNKNOWN"
    volatility_1h: float = 0.0
    liquidation_volume_usd: float = 0.0     # 這 5 分鐘的爆倉量
    funding_rate: float = 0.0
    price_change_5min_pct: float = 0.0      # 觸發極端事件判斷

    # 潛在嵌入（用於相似度搜索，從輸出頭 [55:65] 取，或自行定義）
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExperienceRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def is_extreme(
        self,
        price_change_zscore: float = 0.0,
        liquidation_cascade: bool = False,
    ) -> bool:
        """判斷是否為需要永久記住的極端事件。"""
        if abs(price_change_zscore) >= EXTREME_ZSCORE_THRESHOLD:
            return True
        if liquidation_cascade:
            return True
        # 模型高置信度但結果完全相反 → 也是值得永遠記住的失敗案例
        if self.decoded_confidence > 0.8 and self.outcome == "LOSS" and abs(self.pnl_pct) > 0.05:
            return True
        return False


class _PriorityQueue:
    """簡單的基於 numpy 的優先採樣緩衝（無需 C++ 擴展）。"""

    def __init__(self, maxlen: int) -> None:
        self.maxlen = maxlen
        self._buffer: deque[ExperienceRecord] = deque(maxlen=maxlen)
        self._priorities: deque[float] = deque(maxlen=maxlen)

    def push(self, record: ExperienceRecord, priority: Optional[float] = None) -> None:
        p = priority if priority is not None else max(abs(record.pnl_pct), 1e-6)
        self._buffer.append(record)
        self._priorities.append(p)

    def sample(self, k: int) -> List[ExperienceRecord]:
        if not self._buffer:
            return []
        k = min(k, len(self._buffer))
        probs = np.array(list(self._priorities), dtype=np.float64)
        probs = probs / probs.sum()
        indices = np.random.choice(len(self._buffer), size=k, replace=False, p=probs)
        buf_list = list(self._buffer)
        return [buf_list[i] for i in indices]

    def __len__(self) -> int:
        return len(self._buffer)

    def update_priority(self, idx: int, priority: float) -> None:
        priorities = list(self._priorities)
        if 0 <= idx < len(priorities):
            priorities[idx] = priority
            self._priorities = deque(priorities, maxlen=self.maxlen)


class ExtremeEventVault:
    """冷永久金庫：只存極端事件，永不主動刪除。

    儲存格式：JSONL，一行一筆，附帶 embedding 向量供相似度搜索。
    """

    def __init__(self, vault_dir: str | Path) -> None:
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, List[Dict[str, Any]]] = {}  # symbol → list of header rows
        self._load_index()
        logger.info("ExtremeEventVault ready | path=%s | events=%d", self.vault_dir, self.total_count)

    def _vault_path(self, symbol: str) -> Path:
        return self.vault_dir / f"{symbol}_extreme.jsonl"

    def _load_index(self) -> None:
        for f in self.vault_dir.glob("*_extreme.jsonl"):
            symbol = f.stem.replace("_extreme", "")
            self._index[symbol] = []
            with f.open("r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                        # 只保留 header 欄位在 index（不含 patches 節省記憶體）
                        self._index[symbol].append({
                            "record_id": row.get("record_id", ""),
                            "timestamp": row.get("timestamp", 0),
                            "pnl_pct": row.get("pnl_pct", 0),
                            "price_change_5min_pct": row.get("price_change_5min_pct", 0),
                            "embedding": row.get("embedding"),
                        })
                    except json.JSONDecodeError:
                        continue

    @property
    def total_count(self) -> int:
        return sum(len(v) for v in self._index.values())

    def store(self, record: ExperienceRecord) -> None:
        symbol = record.symbol
        path = self._vault_path(symbol)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), ensure_ascii=False, default=str))
            fh.write("\n")
        if symbol not in self._index:
            self._index[symbol] = []
        self._index[symbol].append({
            "record_id": record.record_id,
            "timestamp": record.timestamp,
            "pnl_pct": record.pnl_pct,
            "price_change_5min_pct": record.price_change_5min_pct,
            "embedding": record.embedding,
        })
        logger.info("EXTREME event stored | symbol=%s | id=%s | pnl=%.3f%%",
                    symbol, record.record_id, record.pnl_pct * 100)

    def retrieve_similar(
        self,
        query_embedding: List[float],
        symbol: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """用 cosine 相似度找出最相似的歷史極端事件（從 index 取頭欄位）。"""
        candidates = self._index.get(symbol, [])
        if not candidates:
            return []
        q = np.array(query_embedding, dtype=np.float64)
        q_norm = q / (np.linalg.norm(q) + 1e-9)
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for row in candidates:
            if row.get("embedding") is None:
                continue
            e = np.array(row["embedding"], dtype=np.float64)
            e_norm = e / (np.linalg.norm(e) + 1e-9)
            sim = float(np.dot(q_norm, e_norm))
            scored.append((sim, row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_events": self.total_count,
            "by_symbol": {s: len(v) for s, v in self._index.items()},
        }


class EpisodicMemory:
    """統一記憶介面：熱緩衝 + 冷金庫 + 統計追蹤。

    使用方式：
        memory = EpisodicMemory(data_dir="data/memory")
        memory.push(record)                        # 自動分類熱/冷
        batch = memory.sample_hot(32)              # 採樣用於 LoRA 更新
        similar = memory.retrieve_extreme(...)     # 找相似極端事件
    """

    def __init__(
        self,
        data_dir: str | Path = "data/bioneuronai/memory",
        hot_buffer_size: int = 50_000,
        price_change_window: int = 100,             # 計算 z-score 用的滾動窗口
    ) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.hot_buffer = _PriorityQueue(maxlen=hot_buffer_size)
        self.cold_vault = ExtremeEventVault(self.data_dir / "extreme_vault")

        # 滾動統計（用於極端事件判斷）
        self._price_changes: deque[float] = deque(maxlen=price_change_window)
        self._liquidation_volumes: deque[float] = deque(maxlen=price_change_window)

        # 全域計數
        self._total_pushed = 0
        self._total_extreme = 0

        logger.info(
            "EpisodicMemory ready | hot_size=%d | cold=%d",
            hot_buffer_size,
            self.cold_vault.total_count,
        )

    def _compute_zscore(self, value: float, history: deque) -> float:
        if len(history) < 10:
            return 0.0
        arr = np.array(history, dtype=np.float64)
        mean, std = arr.mean(), arr.std()
        return (value - mean) / (std + 1e-9)

    def push(
        self,
        record: ExperienceRecord,
        liquidation_cascade: bool = False,
    ) -> bool:
        """推入一條經驗記錄。回傳 True 表示被判定為極端事件並存入冷庫。"""
        self._price_changes.append(record.price_change_5min_pct)
        self._liquidation_volumes.append(record.liquidation_volume_usd)

        price_zscore = self._compute_zscore(
            record.price_change_5min_pct, self._price_changes
        )

        # 判斷是否爆倉潮
        if len(self._liquidation_volumes) >= 10:
            liq_arr = np.array(self._liquidation_volumes, dtype=np.float64)
            liq_mean = liq_arr[:-1].mean()
            if liq_mean > 0 and record.liquidation_volume_usd > liq_mean * LIQUIDATION_CASCADE_MULTIPLIER:
                liquidation_cascade = True

        is_extreme = record.is_extreme(
            price_change_zscore=price_zscore,
            liquidation_cascade=liquidation_cascade,
        )

        priority = max(abs(record.pnl_pct), abs(price_zscore) * 0.01, 1e-6)
        self.hot_buffer.push(record, priority=priority)
        self._total_pushed += 1

        if is_extreme:
            self.cold_vault.store(record)
            self._total_extreme += 1

        return is_extreme

    def sample_hot(self, k: int) -> List[ExperienceRecord]:
        """從熱緩衝優先採樣（損失越大越容易被選到）。"""
        return self.hot_buffer.sample(k)

    def retrieve_extreme(
        self,
        query_embedding: List[float],
        symbol: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """在冷庫裡找最相似的極端歷史事件。"""
        return self.cold_vault.retrieve_similar(query_embedding, symbol, top_k)

    def update_outcome(
        self,
        record: ExperienceRecord,
        exit_price: float,
        pnl_pct: float,
        hold_duration_sec: float,
    ) -> ExperienceRecord:
        """交易平倉後補填結果，更新 reward。"""
        record.exit_price = exit_price
        record.pnl_pct = pnl_pct
        record.hold_duration_sec = hold_duration_sec
        record.outcome = "WIN" if pnl_pct > 0.001 else ("LOSS" if pnl_pct < -0.001 else "BREAKEVEN")

        # 多目標 Reward shaping（與 ActionRecord.fill_exit 一致）
        from bioneuronai.core.reward import compute_reward
        record.reward = compute_reward(
            pnl_pct=pnl_pct,
            hold_duration_sec=hold_duration_sec,
            uncertainty=record.decoded_uncertainty,
            confidence=record.decoded_confidence,
        )

        # 把更新後的記錄再塞回熱緩衝，更新優先級
        self.hot_buffer.push(record, priority=max(abs(pnl_pct), 1e-6))

        # 重新判斷是否需要存入冷庫（可能進場時不極端，但虧損極大）
        if record.is_extreme():
            self.cold_vault.store(record)

        return record

    def get_stats(self) -> Dict[str, Any]:
        hot = len(self.hot_buffer)
        recent_rewards = [r.reward for r in list(self.hot_buffer._buffer)[-100:] if r.reward != 0]
        win_rate = 0.0
        if recent_rewards:
            wins = sum(1 for r in list(self.hot_buffer._buffer)[-100:] if r.outcome == "WIN")
            win_rate = wins / len([r for r in list(self.hot_buffer._buffer)[-100:] if r.outcome != "PENDING"])
        return {
            "hot_buffer_size": hot,
            "total_pushed": self._total_pushed,
            "total_extreme": self._total_extreme,
            "extreme_rate_pct": round(self._total_extreme / max(self._total_pushed, 1) * 100, 2),
            "cold_vault": self.cold_vault.get_stats(),
            "recent_100_win_rate": round(win_rate, 4),
            "recent_100_avg_reward": round(float(np.mean(recent_rewards)) if recent_rewards else 0, 5),
        }
