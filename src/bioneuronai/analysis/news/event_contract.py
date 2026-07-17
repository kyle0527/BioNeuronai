"""
新聞事件合約 (NewsEventContract)
=================================

v2.2 Phase 1.2 核心功能：讓新聞影響力具備「時間維度」。

設計目標：
- 每個重大新聞生成一個 Contract，包含衰減參數與到期時間
- 事件重要性隨時間呈指數或線性衰減；方向由 AI 而非事件規則決定
- 到期後自動記錄真實 PnL，標記為高品質 Meta-Learner 訓練資料

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import hashlib
import json
import logging
import math
import uuid
from dataclasses import asdict, dataclass, field
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
LABEL_REALIZED_UP = "realized_up"
LABEL_REALIZED_DOWN = "realized_down"
LABEL_NEGLIGIBLE = "negligible"  # 價格變化幅度太小

# ── 驗證閾值 ─────────────────────────────────────────────────────────────────
# 若 |realized_pnl_pct| 小於此值，視為價格沒有顯著變動，不納入訓練資料
NEGLIGIBLE_PNL_THRESHOLD = 0.5  # 單位：百分比


def _urgency_from_importance(importance: float) -> str:
    """根據初始重要性決定緊急程度。"""
    if importance >= 0.7:
        return URGENCY_CRITICAL
    if importance >= 0.4:
        return URGENCY_HIGH
    if importance >= 0.2:
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
        initial_importance: 初始重要性，範圍 [0.0, 1.0]，不預先判斷多空
        minimum_importance: 有效期結束前保留的重要性下限
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
        training_label    : 真實市場結果標籤（realized_up / realized_down / negligible）
    """

    contract_id: str
    event_type: str
    symbol: str
    headline: str
    initial_importance: float
    minimum_importance: float
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

    def get_current_importance(self, at_time: Optional[datetime] = None) -> float:
        """
        計算當前衰減後的重要性。

        Args:
            at_time: 計算時間點；None 使用 datetime.now()

        Returns:
            衰減後的重要性，已解析或已到期時返回 0.0
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

        return self.minimum_importance + (
            self.initial_importance - self.minimum_importance
        ) * decay_factor

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
        # 若價格幾乎沒動，視為不顯著
        if abs(self.realized_pnl_pct) < NEGLIGIBLE_PNL_THRESHOLD:
            self.training_label = LABEL_NEGLIGIBLE
        else:
            self.training_label = (
                LABEL_REALIZED_UP if self.realized_pnl_pct > 0 else LABEL_REALIZED_DOWN
            )

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
        # 舊資料使用帶方向的 initial_impact；載入時只保留其絕對強度，
        # 避免既有殘值繼續把事件規則當成固定多空。
        if "initial_importance" not in d and "initial_impact" in d:
            d["initial_importance"] = abs(float(d.pop("initial_impact")))
        d.setdefault("minimum_importance", 0.0)
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

    # __file__ is src/bioneuronai/analysis/news/event_contract.py
    # parents[4] => project root (bioneuronai repo root)
    DEFAULT_CONTRACTS_FILE: Path = (
        Path(__file__).parents[4]
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
        initial_importance: float,
        minimum_importance: float,
        duration_hours: float,
        price_at_creation: float = 0.0,
        decay_mode: str = DECAY_LINEAR,
    ) -> NewsEventContract:
        """
        建立並持久化一份新的事件合約。

        Args:
            event_type        : 事件類型（HACK / REGULATION / ETF_APPROVAL 等）
            symbol            : 影響的交易對
            headline          : 觸發新聞標題
            initial_importance: 初始重要性 [0.0, 1.0]，不帶方向
            minimum_importance: 有效期結束前保留的重要性下限
            duration_hours    : 有效總時長；不代表預測方向
            price_at_creation : 建立時的市場價格（0 表示未知）
            decay_mode        : DECAY_EXPONENTIAL 或 DECAY_LINEAR

        Returns:
            新建的 NewsEventContract
        """
        now = datetime.now()
        normalized_symbol = symbol.strip().upper() or "CRYPTO"
        normalized_headline = " ".join(headline.casefold().split())

        # 同一輪新聞分析可能從不同來源或重試路徑重複命中同一事件。
        # 事件合約代表「事件」而不是「文章筆數」，因此尚未到期的同事件
        # 必須共用同一份合約，避免戰略重要性被重複報導人為放大。
        for existing in self._contracts.values():
            if existing.resolved or existing.is_expired(now):
                continue
            if existing.symbol.strip().upper() != normalized_symbol:
                continue
            if existing.event_type.casefold() != event_type.casefold():
                continue
            existing_headline = " ".join(existing.headline.casefold().split())
            if existing_headline == normalized_headline:
                logger.info(
                    "重用有效新聞事件合約 [%s/%s] contract_id=%s",
                    event_type,
                    normalized_symbol,
                    existing.contract_id,
                )
                return existing

            # 同一事件類型出現新的報導，視為事件進展而不是另一份獨立記憶。
            # 規則只更新重要性與有效時間；多空方向仍完全留給 AI 判斷。
            current_importance = existing.get_current_importance(now)
            existing.headline = headline
            existing.initial_importance = max(
                current_importance,
                float(initial_importance),
            )
            existing.minimum_importance = min(
                existing.initial_importance,
                max(existing.minimum_importance, float(minimum_importance)),
            )
            existing.urgency = _urgency_from_importance(
                existing.initial_importance
            )
            existing.decay_mode = decay_mode
            existing.decay_rate = float(duration_hours)
            existing.created_at = now
            existing.expires_at = max(
                existing.expires_at,
                now + timedelta(hours=duration_hours),
            )
            if price_at_creation > 0:
                existing.price_at_creation = float(price_at_creation)
            self._save()
            logger.info(
                "更新有效新聞事件合約 [%s/%s] importance=%.2f expires=%s",
                event_type,
                normalized_symbol,
                existing.initial_importance,
                existing.expires_at.isoformat(),
            )
            return existing

        # Use UUID4 for uniqueness; include a short SHA-256 prefix of content for readability
        content_hash = hashlib.sha256(
            f"{event_type}_{normalized_symbol}_{normalized_headline}".encode()
        ).hexdigest()[:8]
        contract_id = f"{content_hash}_{uuid.uuid4().hex[:8]}"

        if not 0.0 <= minimum_importance <= initial_importance <= 1.0:
            raise ValueError("事件重要性必須符合 0 <= minimum <= initial <= 1")
        expires_at = now + timedelta(hours=duration_hours)

        contract = NewsEventContract(
            contract_id=contract_id,
            event_type=event_type,
            symbol=normalized_symbol,
            headline=headline,
            initial_importance=float(initial_importance),
            minimum_importance=float(minimum_importance),
            urgency=_urgency_from_importance(initial_importance),
            decay_mode=decay_mode,
            decay_rate=float(duration_hours),
            created_at=now,
            expires_at=expires_at,
            price_at_creation=float(price_at_creation),
        )

        self._contracts[contract_id] = contract
        self._save()

        logger.info(
            "📋 新合約建立 [%s/%s] importance=%.2f urgency=%s expires=%s",
            event_type,
            symbol,
            initial_importance,
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
            normalized_symbol = symbol.strip().upper()
            active = [
                contract
                for contract in active
                if contract.symbol.strip().upper() in {normalized_symbol, "CRYPTO"}
            ]

        # 舊資料可能已在去重邏輯加入前重複寫入。讀取時仍需去重，
        # 否則歷史殘值會持續扭曲彙總事件強度。
        deduplicated: Dict[tuple[str, str, str], NewsEventContract] = {}
        for contract in sorted(active, key=lambda item: item.created_at, reverse=True):
            key = (
                contract.symbol.strip().upper(),
                contract.event_type.casefold(),
                " ".join(contract.headline.casefold().split()),
            )
            deduplicated.setdefault(key, contract)
        return list(deduplicated.values())

    def get_memory_snapshot(
        self,
        symbol: Optional[str] = None,
        at_time: Optional[datetime] = None,
    ) -> Dict:
        """輸出平常交易判斷使用的濃縮事件記憶。

        原始新聞與完整標題保留在新聞檔案及事件合約內供查證／訓練；交易
        迴圈只讀事件類型、衰減後重要性與剩餘時間，避免每輪重讀全文。
        此方法只負責確定性計算，不判斷多空方向。
        """
        now = at_time or datetime.now()
        active = self.get_active_contracts(symbol=symbol, at_time=now)
        return {
            "snapshot_at": now.isoformat(),
            "symbol": symbol.strip().upper() if symbol else None,
            "aggregate_intensity": self.get_aggregated_intensity(
                symbol=symbol,
                at_time=now,
            ),
            "active_events": [
                {
                    "contract_id": contract.contract_id,
                    "event_type": contract.event_type,
                    "current_importance": contract.get_current_importance(now),
                    "remaining_hours": max(
                        0.0,
                        (contract.expires_at - now).total_seconds() / 3600.0,
                    ),
                    "urgency": contract.urgency,
                    "expires_at": contract.expires_at.isoformat(),
                }
                for contract in active
            ],
        }

    def get_aggregated_intensity(
        self,
        symbol: Optional[str] = None,
        at_time: Optional[datetime] = None,
    ) -> float:
        """
        彙總所有有效合約的衰減後重要性，正規化至 [0.0, 1.0]。

        用於 Meta-Learner feature_extractor 的 event_intensity 欄位（[6] 維）。

        Args:
            symbol  : 若指定，只計算該交易對相關合約
            at_time : 計算時間點

        Returns:
            彙總重要性 [0.0, 1.0]，0.0 表示無有效合約
        """
        active = self.get_active_contracts(symbol=symbol, at_time=at_time)
        if not active:
            return 0.0

        total = sum(c.get_current_importance(at_time) for c in active)
        # 使用 tanh 壓縮；多個事件只增加重要性，不形成規則式方向。
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
        changed = False
        now = datetime.now()

        for contract in list(self._contracts.values()):
            if contract.resolved:
                continue
            if not contract.is_expired(now):
                continue

            if contract.price_at_creation <= 0:
                contract.resolved = True
                contract.resolved_at = now
                contract.training_label = None
                changed = True
                logger.warning(
                    "舊事件合約 %s 缺少建立時價格，已結束但不產生訓練標籤",
                    contract.contract_id,
                )
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
            changed = True

        if changed:
            self._save()
        if validated > 0:
            logger.info("🔄 驗證閉環：共產生 %d 份真實結果標籤", validated)

        return validated

    def get_training_data(self) -> List[Dict]:
        """
        取得所有已驗證合約作為 Meta-Learner 訓練資料。

        只返回 label 不為 None 且有效價格的合約。

        Returns:
            訓練資料字典列表，各包含 initial_importance, realized_pnl_pct, training_label 等欄位
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
