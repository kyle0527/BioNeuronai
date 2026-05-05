"""
新聞事件合約 (NewsEventContract)
=================================

v2.2 Phase 1.2 核心功能：讓新聞影響力具備「時間維度」。

設計目標：
- 每個重大新聞生成一個 Contract，包含衰減參數與到期時間
- 影響力隨時間呈指數或線性衰減，避免利多無限期延長
- 到期後自動記錄真實 PnL，標記為高品質 Meta-Learner 訓練資料

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import hashlib
import json
import logging
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── 衰減模式常量 ──────────────────────────────────────────────────────────────
DECAY_EXPONENTIAL = "exponential"  # 指數衰減：半衰期 = decay_rate 小時
DECAY_LINEAR = "linear"            # 線性衰減：在 expires_at 時歸零

# ── 緊急程度常量 ──────────────────────────────────────────────────────────────
URGENCY_CRITICAL = "critical"  # |impact| >= 0.7
URGENCY_HIGH = "high"          # |impact| >= 0.4
URGENCY_MEDIUM = "medium"      # |impact| >= 0.2
URGENCY_LOW = "low"            # |impact| < 0.2

# ── 訓練標籤常量 ──────────────────────────────────────────────────────────────
LABEL_CONFIRMED_BULLISH = "confirmed_bullish"
LABEL_CONFIRMED_BEARISH = "confirmed_bearish"
LABEL_FALSE_SIGNAL = "false_signal"
LABEL_NEGLIGIBLE = "negligible"  # 價格變化幅度太小


def _urgency_from_impact(impact: float) -> str:
    """根據初始影響力決定緊急程度"""
    abs_impact = abs(impact)
    if abs_impact >= 0.7:
        return URGENCY_CRITICAL
    if abs_impact >= 0.4:
        return URGENCY_HIGH
    if abs_impact >= 0.2:
        return URGENCY_MEDIUM
    return URGENCY_LOW


@dataclass
class NewsEventContract:
    """
    新聞事件合約

    每個重大新聞事件對應一份合約，記錄影響力隨時間的衰減，
    並在到期後自動計算真實 PnL 作為 Meta-Learner 訓練資料。

    欄位說明：
        contract_id       : 唯一識別碼（md5 of event_type + headline + created_at）
        event_type        : 事件類型，與 EventRule.event_type 一致（如 HACK, ETF_APPROVAL）
        symbol            : 影響的主要交易對（如 BTCUSDT）
        headline          : 觸發合約的新聞標題
        initial_impact    : 初始影響力，範圍 [-1.0, +1.0]，正值看漲、負值看跌
        urgency           : 緊急程度（critical / high / medium / low）
        decay_mode        : 衰減模式（exponential / linear）
        decay_rate        : 指數模式：半衰期（小時）；線性模式：無意義（使用 expires_at 計算）
        created_at        : 合約建立時間
        expires_at        : 影響力歸零的時間
        price_at_creation : 合約建立時的標的資產價格（用於計算 PnL）
        resolved          : 是否已完成驗證
        resolved_at       : 驗證完成時間
        resolution_price  : 驗證時的市場價格
        realized_pnl_pct  : 實際價格變化百分比 (resolution_price - price_at_creation) / price_at_creation * 100
        training_label    : 訓練標籤（confirmed_bullish / confirmed_bearish / false_signal / negligible）
    """

    contract_id: str
    event_type: str
    symbol: str
    headline: str
    initial_impact: float
    urgency: str
    decay_mode: str
    decay_rate: float
    created_at: datetime
    expires_at: datetime
    price_at_creation: float = 0.0
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_price: float = 0.0
    realized_pnl_pct: float = 0.0
    training_label: Optional[str] = None

    # ── 核心方法 ──────────────────────────────────────────────────────────────

    def get_current_impact(self, at_time: Optional[datetime] = None) -> float:
        """
        計算當前衰減後的影響力。

        Args:
            at_time: 計算時間點；None 使用 datetime.now()

        Returns:
            衰減後的影響力，已解析或已到期時返回 0.0
        """
        if self.resolved:
            return 0.0

        now = at_time or datetime.now()
        if now >= self.expires_at:
            return 0.0

        elapsed_hours = (now - self.created_at).total_seconds() / 3600.0

        if self.decay_mode == DECAY_EXPONENTIAL:
            # 指數衰減：每 decay_rate 小時強度減半
            half_life = max(self.decay_rate, 1e-6)
            decay_factor = math.pow(0.5, elapsed_hours / half_life)
        else:
            # 線性衰減：從建立時間到 expires_at 均勻歸零
            total_hours = (self.expires_at - self.created_at).total_seconds() / 3600.0
            if total_hours <= 0:
                return 0.0
            decay_factor = max(0.0, 1.0 - elapsed_hours / total_hours)

        return self.initial_impact * decay_factor

    def is_expired(self, at_time: Optional[datetime] = None) -> bool:
        """判斷合約是否已到期（未必已驗證）"""
        now = at_time or datetime.now()
        return now >= self.expires_at

    def validate(self, current_price: float) -> None:
        """
        到期後驗證：記錄真實 PnL 並生成 Meta-Learner 訓練標籤。

        僅在 price_at_creation > 0 且尚未 resolved 時執行。

        Args:
            current_price: 合約到期時的市場價格
        """
        if self.resolved:
            logger.debug("合約 %s 已驗證，跳過", self.contract_id)
            return
        if self.price_at_creation <= 0:
            logger.warning(
                "合約 %s 無有效建立時價格，跳過驗證 (price_at_creation=%.4f)",
                self.contract_id,
                self.price_at_creation,
            )
            return

        self.resolved = True
        self.resolved_at = datetime.now()
        self.resolution_price = current_price
        self.realized_pnl_pct = (
            (current_price - self.price_at_creation) / self.price_at_creation * 100
        )

        # 生成訓練標籤
        # 若價格幾乎沒動（< 0.5%），視為不顯著
        if abs(self.realized_pnl_pct) < 0.5:
            self.training_label = LABEL_NEGLIGIBLE
        else:
            # 判斷預測方向與實際方向是否一致
            predicted_up = self.initial_impact > 0
            actual_up = self.realized_pnl_pct > 0
            if predicted_up == actual_up:
                self.training_label = (
                    LABEL_CONFIRMED_BULLISH if actual_up else LABEL_CONFIRMED_BEARISH
                )
            else:
                self.training_label = LABEL_FALSE_SIGNAL

        logger.info(
            "✅ 合約驗證完成 [%s] %s | PnL=%.2f%% | label=%s",
            self.event_type,
            self.headline[:40],
            self.realized_pnl_pct,
            self.training_label,
        )

    # ── 序列化 ────────────────────────────────────────────────────────────────

    def to_dict(self) -> Dict:
        """序列化為可 JSON 儲存的字典"""
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        d["expires_at"] = self.expires_at.isoformat()
        d["resolved_at"] = self.resolved_at.isoformat() if self.resolved_at else None
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "NewsEventContract":
        """從字典還原合約物件"""
        d = dict(data)
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d["expires_at"] = datetime.fromisoformat(d["expires_at"])
        d["resolved_at"] = (
            datetime.fromisoformat(d["resolved_at"]) if d.get("resolved_at") else None
        )
        return cls(**d)


# ─────────────────────────────────────────────────────────────────────────────
# NewsEventContractManager
# ─────────────────────────────────────────────────────────────────────────────


class NewsEventContractManager:
    """
    新聞事件合約管理員

    負責：
    1. 根據 RuleBasedEvaluator 偵測到的事件建立合約
    2. 持久化合約至 JSON 檔案
    3. 提供衰減後影響力彙總（供 Meta-Learner feature_extractor 使用）
    4. 對到期合約執行驗證閉環（需傳入當前市場價格）

    單例透過 get_contract_manager() 取得。
    """

    DEFAULT_CONTRACTS_FILE = (
        Path(__file__).parent.parent.parent.parent  # src/bioneuronai
        / ".."  # src
        / ".."  # project root
        / "data"
        / "bioneuronai"
        / "trading"
        / "sop"
        / "news_event_contracts.json"
    )

    def __init__(self, contracts_file: Optional[Path] = None) -> None:
        self._contracts_file: Path = (
            contracts_file or self.DEFAULT_CONTRACTS_FILE
        ).resolve()
        self._contracts_file.parent.mkdir(parents=True, exist_ok=True)
        self._contracts: Dict[str, NewsEventContract] = {}
        self._load()
        logger.info(
            "✅ NewsEventContractManager 初始化完成，載入 %d 份合約",
            len(self._contracts),
        )

    # ── 公開 API ──────────────────────────────────────────────────────────────

    def create_contract(
        self,
        event_type: str,
        symbol: str,
        headline: str,
        initial_impact: float,
        decay_hours: float,
        price_at_creation: float = 0.0,
        decay_mode: str = DECAY_EXPONENTIAL,
    ) -> NewsEventContract:
        """
        建立並持久化一份新的事件合約。

        Args:
            event_type        : 事件類型（HACK / REGULATION / ETF_APPROVAL 等）
            symbol            : 影響的交易對
            headline          : 觸發新聞標題
            initial_impact    : 初始影響力 [-1.0, +1.0]
            decay_hours       : 影響力半衰期（指數模式）或有效總時長（線性模式）
            price_at_creation : 建立時的市場價格（0 表示未知）
            decay_mode        : DECAY_EXPONENTIAL 或 DECAY_LINEAR

        Returns:
            新建的 NewsEventContract
        """
        now = datetime.now()
        raw_id = f"{event_type}_{symbol}_{headline}_{now.isoformat()}"
        contract_id = hashlib.md5(raw_id.encode()).hexdigest()[:16]

        # 到期時間：指數衰減取 3 倍半衰期；線性衰減直接用 decay_hours
        expires_at = now + timedelta(
            hours=decay_hours * 3 if decay_mode == DECAY_EXPONENTIAL else decay_hours
        )

        contract = NewsEventContract(
            contract_id=contract_id,
            event_type=event_type,
            symbol=symbol,
            headline=headline,
            initial_impact=float(initial_impact),
            urgency=_urgency_from_impact(initial_impact),
            decay_mode=decay_mode,
            decay_rate=float(decay_hours),
            created_at=now,
            expires_at=expires_at,
            price_at_creation=float(price_at_creation),
        )

        self._contracts[contract_id] = contract
        self._save()

        logger.info(
            "📋 新合約建立 [%s/%s] impact=%.2f urgency=%s expires=%s",
            event_type,
            symbol,
            initial_impact,
            contract.urgency,
            expires_at.strftime("%Y-%m-%d %H:%M"),
        )
        return contract

    def get_active_contracts(
        self,
        symbol: Optional[str] = None,
        at_time: Optional[datetime] = None,
    ) -> List[NewsEventContract]:
        """
        取得目前仍有效（未到期且未 resolved）的合約。

        Args:
            symbol  : 若指定，只返回該交易對相關合約
            at_time : 計算時間點，None 使用 now()

        Returns:
            有效合約列表，按建立時間由新到舊排序
        """
        now = at_time or datetime.now()
        active = [
            c
            for c in self._contracts.values()
            if not c.resolved and not c.is_expired(now)
        ]
        if symbol:
            active = [c for c in active if c.symbol == symbol]
        return sorted(active, key=lambda c: c.created_at, reverse=True)

    def get_aggregated_intensity(
        self,
        symbol: Optional[str] = None,
        at_time: Optional[datetime] = None,
    ) -> float:
        """
        彙總所有有效合約的衰減後影響力，正規化至 [-1.0, +1.0]。

        用於 Meta-Learner feature_extractor 的 event_intensity 欄位（[6] 維）。

        Args:
            symbol  : 若指定，只計算該交易對相關合約
            at_time : 計算時間點

        Returns:
            彙總影響力 [-1.0, +1.0]，0.0 表示無有效合約
        """
        active = self.get_active_contracts(symbol=symbol, at_time=at_time)
        if not active:
            return 0.0

        total = sum(c.get_current_impact(at_time) for c in active)
        # 使用 tanh 壓縮至 [-1, +1]，多個同向事件會累加
        return float(math.tanh(total))

    def validate_expired_contracts(
        self,
        current_prices: Optional[Dict[str, float]] = None,
    ) -> int:
        """
        對所有已到期但尚未 resolved 的合約執行驗證閉環。

        Args:
            current_prices: {symbol: price} 字典；若缺少某交易對，跳過其合約。

        Returns:
            成功驗證的合約數量
        """
        if current_prices is None:
            current_prices = {}

        validated = 0
        now = datetime.now()

        for contract in list(self._contracts.values()):
            if contract.resolved:
                continue
            if not contract.is_expired(now):
                continue

            price = current_prices.get(contract.symbol, 0.0)
            if price <= 0:
                logger.debug(
                    "合約 %s 已到期但無 %s 價格，跳過驗證",
                    contract.contract_id,
                    contract.symbol,
                )
                continue

            contract.validate(price)
            validated += 1

        if validated > 0:
            self._save()
            logger.info("🔄 驗證閉環：共驗證 %d 份到期合約", validated)

        return validated

    def get_training_data(self) -> List[Dict]:
        """
        取得所有已驗證合約作為 Meta-Learner 訓練資料。

        只返回 label 不為 None 且有效價格的合約。

        Returns:
            訓練資料字典列表，各包含 initial_impact, realized_pnl_pct, training_label 等欄位
        """
        training_records = []
        for contract in self._contracts.values():
            if not contract.resolved or contract.training_label is None:
                continue
            if contract.training_label == LABEL_NEGLIGIBLE:
                continue
            training_records.append(contract.to_dict())
        return training_records

    def purge_old_contracts(self, keep_days: int = 90) -> int:
        """
        清除已解析且建立時間超過 keep_days 天的舊合約，節省儲存空間。

        Args:
            keep_days: 保留天數，預設 90 天

        Returns:
            清除的合約數量
        """
        cutoff = datetime.now() - timedelta(days=keep_days)
        to_remove = [
            cid
            for cid, c in self._contracts.items()
            if c.resolved and c.created_at < cutoff
        ]
        for cid in to_remove:
            del self._contracts[cid]

        if to_remove:
            self._save()
            logger.info("🗑️  清除 %d 份舊合約（超過 %d 天）", len(to_remove), keep_days)

        return len(to_remove)

    # ── 持久化 ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """從 JSON 檔案載入合約"""
        if not self._contracts_file.exists():
            return
        try:
            with open(self._contracts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                try:
                    c = NewsEventContract.from_dict(item)
                    self._contracts[c.contract_id] = c
                except Exception as exc:
                    logger.warning("解析合約記錄失敗，跳過: %s", exc)
        except Exception as exc:
            logger.warning("載入合約檔案失敗: %s", exc)

    def _save(self) -> None:
        """將目前所有合約序列化至 JSON 檔案"""
        try:
            records = [c.to_dict() for c in self._contracts.values()]
            tmp = self._contracts_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            tmp.replace(self._contracts_file)
        except Exception as exc:
            logger.error("儲存合約檔案失敗: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# 單例
# ─────────────────────────────────────────────────────────────────────────────

_contract_manager: Optional[NewsEventContractManager] = None


def get_contract_manager() -> NewsEventContractManager:
    """取得 NewsEventContractManager 單例"""
    global _contract_manager
    if _contract_manager is None:
        _contract_manager = NewsEventContractManager()
    return _contract_manager
