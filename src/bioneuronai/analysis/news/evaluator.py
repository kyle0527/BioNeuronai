"""
規則式事件評估器
================

RuleBasedEvaluator - 新聞大腦

功能：
1. 使用關鍵字規則檢測重大事件
2. 產生事件並存入 event_memory 資料庫
3. 檢測事件結束條件 (Hard Stop) 並自動解析事件
4. 為 strategy_fusion 提供 event_score

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Protocol, Tuple, cast

# 2. 本地模組
from ..._paths import resolve_project_path
from .models import NewsArticle

# 設置日誌
logger = logging.getLogger(__name__)


class EventDatabase(Protocol):
    def save_event(self, event_info: Dict[str, Any]) -> Optional[str]: ...
    def get_active_events(
        self, event_type: Optional[str] = None, symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...
    def resolve_event(self, event_id: str, resolution_note: Optional[str] = None) -> bool: ...
    def calculate_total_event_score(
        self, symbol: Optional[str] = None
    ) -> Tuple[float, List[Dict[str, Any]]]: ...

# ========================================
# EventRule 定義
# ========================================

# 直接從 schemas 導入 (Single Source of Truth)
from schemas.rag import EventRule  # noqa: E402
logger.debug("已從 schemas.rag 導入 EventRule")


class RuleBasedEvaluator:
    """
    規則式事件評估器 - 新聞大腦
    
    核心功能：
    1. 使用關鍵字規則檢測重大事件
    2. 產生事件並存入 event_memory 資料庫
    3. 檢測事件結束條件 (Hard Stop) 並自動解析事件
    4. 為 strategy_fusion 提供 event_score
    
    使用範例：
        from bioneuronai.analysis.news import RuleBasedEvaluator
        
        evaluator = RuleBasedEvaluator()
        
        # 評估一則新聞
        event_info = evaluator.evaluate_headline(
            headline="Breaking: Major exchange hacked, $100M stolen",
            source="Reuters",
            source_confidence=0.9
        )
        
        if event_info:
            print(f"檢測到事件: {event_info['event_type']}, 分數: {event_info['score']}")
    """
    
    # 預設規則定義
    DEFAULT_RULES: List[EventRule] = [
        # 戰爭/地緣政治
        EventRule(
            event_type="WAR",
            trigger_keywords=[
                "war", "military strike", "invasion", "attack on",
                "missile", "nuclear threat", "armed conflict"
            ],
            termination_keywords=[
                "ceasefire", "peace agreement", "truce", "war ended",
                "conflict resolved", "de-escalation"
            ],
            base_score=-0.8,
            decay_hours=72
        ),
        
        # 駭客/安全事件
        EventRule(
            event_type="HACK",
            trigger_keywords=[
                "hacked", "hack", "exploit", "stolen", "breach",
                "security incident", "funds stolen", "vulnerability exploited",
                "private keys compromised", "hot wallet drained"
            ],
            termination_keywords=[
                "funds recovered", "hacker identified", "security restored",
                "patch deployed", "vulnerability fixed", "compensation announced"
            ],
            base_score=-0.7,
            decay_hours=48
        ),
        
        # 監管風險
        EventRule(
            event_type="REGULATION",
            trigger_keywords=[
                "sec lawsuit", "regulatory crackdown", "banned", "illegal",
                "regulatory action", "investigation launched", "subpoena",
                "enforcement action", "crypto ban"
            ],
            termination_keywords=[
                "case dismissed", "settlement reached", "charges dropped",
                "regulatory approval", "compliance achieved", "ban lifted"
            ],
            base_score=-0.6,
            decay_hours=168  # 7天
        ),
        
        # 總體經濟
        EventRule(
            event_type="MACRO",
            trigger_keywords=[
                "rate hike", "fed raises", "inflation surge", "recession",
                "economic crisis", "bank failure", "liquidity crisis",
                "market crash", "systemic risk"
            ],
            termination_keywords=[
                "rate cut", "fed pauses", "inflation cools", "recovery",
                "economic rebound", "bailout approved", "liquidity restored"
            ],
            base_score=-0.5,
            decay_hours=120  # 5天
        ),
        
        # 交易所問題
        EventRule(
            event_type="EXCHANGE_ISSUE",
            trigger_keywords=[
                "exchange halts", "withdrawal suspended", "insolvency",
                "bankruptcy filing", "exchange down", "liquidity issues",
                "trading halted"
            ],
            termination_keywords=[
                "withdrawals resumed", "trading resumed", "exchange recovered",
                "liquidity restored", "operations normal"
            ],
            base_score=-0.65,
            decay_hours=48
        ),
        
        # 正面事件：ETF批准
        EventRule(
            event_type="ETF_APPROVAL",
            trigger_keywords=[
                "etf approved", "etf approval", "sec approves etf",
                "spot etf approved"
            ],
            termination_keywords=[],  # 正面事件不需要結束條件
            base_score=0.8,
            decay_hours=72
        ),
        
        # 正面事件：機構採用
        EventRule(
            event_type="INSTITUTIONAL",
            trigger_keywords=[
                "institutional adoption", "major investment", "billion dollar",
                "hedge fund buys", "corporate treasury", "mass adoption"
            ],
            termination_keywords=[],
            base_score=0.6,
            decay_hours=48
        ),
    ]
    
    def __init__(self, custom_rules: Optional[List[EventRule]] = None):
        """
        初始化規則式評估器

        規則載入優先順序：
        1. config/event_rules.json（外部配置，UI 面板 / AI 可直接編輯）
        2. DEFAULT_RULES（程式碼預設值，JSON 不存在時的 fallback）
        3. custom_rules（呼叫端注入，會附加在上述規則之後）

        Args:
            custom_rules: 額外注入的規則，會與載入的規則合併
        """
        self.rules = self._load_rules_from_json()
        if custom_rules:
            self.rules.extend(custom_rules)

        # 嘗試連接資料庫
        self._db: Optional[EventDatabase] = None
        self._connect_db()

        logger.info(f"✅ RuleBasedEvaluator 初始化完成，載入 {len(self.rules)} 條規則")

    def _load_rules_from_json(self) -> List[EventRule]:
        """從 config/event_rules.json 載入規則，失敗時 fallback 到 DEFAULT_RULES。"""
        import json as _json

        rules_path = resolve_project_path("config/event_rules.json")
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                data = _json.load(f)
            rules = [EventRule(**r) for r in data.get("rules", [])]
            if rules:
                logger.info(f"從 config/event_rules.json 載入 {len(rules)} 條規則")
                return rules
            logger.warning("config/event_rules.json 的 rules 為空，使用 DEFAULT_RULES")
        except FileNotFoundError:
            logger.info("config/event_rules.json 不存在，使用 DEFAULT_RULES")
        except Exception as exc:
            logger.warning(f"載入 event_rules.json 失敗（{exc}），使用 DEFAULT_RULES")

        return self.DEFAULT_RULES.copy()
    
    def _connect_db(self) -> None:
        """連接資料庫管理器"""
        db_path = resolve_project_path("data/bioneuronai/trading/runtime/trading.db")
        try:
            from ...data.database_manager import get_database_manager
            self._db = cast(EventDatabase, get_database_manager(str(db_path)))
            logger.debug("RuleBasedEvaluator 已連接 DatabaseManager: %s", db_path)
        except Exception as e:
            self._db = None
            raise RuntimeError(f"RuleBasedEvaluator 無法連接資料庫 {db_path}: {e}") from e

    def _require_db(self) -> EventDatabase:
        """取得資料庫，若不可用則直接拋錯。"""
        if self._db is None:
            raise RuntimeError("RuleBasedEvaluator 資料庫未初始化")
        return self._db
    
    def evaluate_headline(
        self,
        headline: str,
        source: str = "unknown",
        source_confidence: float = 0.5,
        affected_symbols: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        評估單則新聞標題
        
        Args:
            headline: 新聞標題
            source: 來源
            source_confidence: 來源可信度 (0-1)
            affected_symbols: 影響的交易對，逗號分隔
            
        Returns:
            事件資訊 dict 或 None (無匹配)
        """
        headline_lower = headline.lower()
        
        # 1. 先檢查是否有事件結束 (Hard Stop)
        self._check_termination_keywords(headline_lower)
        
        # 2. 檢查是否觸發新事件
        for rule in self.rules:
            for keyword in rule.trigger_keywords:
                if keyword in headline_lower:
                    event_info = self._create_event(
                        rule=rule,
                        headline=headline,
                        matched_keyword=keyword,
                        source=source,
                        source_confidence=source_confidence,
                        affected_symbols=affected_symbols
                    )
                    return event_info
        
        return None
    
    def _create_event(
        self,
        rule: EventRule,
        headline: str,
        matched_keyword: str,
        source: str,
        source_confidence: float,
        affected_symbols: Optional[str]
    ) -> Dict[str, Any]:
        """創建事件並存入資料庫"""
        # 生成事件 ID
        event_id = hashlib.md5(
            f"{rule.event_type}_{headline}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # 構建終止條件描述
        termination_desc = None
        if rule.termination_keywords:
            termination_desc = f"Keywords: {', '.join(rule.termination_keywords[:3])}..."
        
        event_info = {
            'event_id': event_id,
            'event_type': rule.event_type,
            'headline': headline,
            'score': rule.base_score,
            'status': 'ACTIVE',
            'termination_condition': termination_desc,
            'embedding_id': None,  # 預留給未來 NLP
            'source': source,
            'source_confidence': source_confidence,
            'affected_symbols': affected_symbols,
            'metadata': f"matched: {matched_keyword}; decay_hours: {rule.decay_hours}"
        }
        
        # 存入資料庫
        saved_id = self._require_db().save_event(event_info)
        if not saved_id:
            raise RuntimeError(f"事件已匹配但寫入 event_memory 失敗: {headline[:80]}")

        logger.info(f"🧠 事件已記錄: [{rule.event_type}] {headline[:40]}...")
        
        return event_info
    
    def _check_termination_keywords(self, headline_lower: str) -> None:
        """檢查是否有事件結束關鍵字，自動解析相關事件 (Hard Stop)"""
        db = self._require_db()

        for rule in self.rules:
            for term_keyword in rule.termination_keywords:
                if term_keyword in headline_lower:
                    # 找到所有該類型的 ACTIVE 事件並解析
                    active_events = db.get_active_events(event_type=rule.event_type)
                    for event in active_events:
                        db.resolve_event(
                            event['event_id'],
                            resolution_note=f"Terminated by keyword: {term_keyword}"
                        )
                        logger.info(f"🛑 Hard Stop: {rule.event_type} 事件已解析 (keyword: {term_keyword})")
    
    def get_current_event_score(self, symbol: Optional[str] = None) -> Tuple[float, List[Dict[str, Any]]]:
        """
        獲取當前的事件總分
        
        Args:
            symbol: 過濾特定交易對
            
        Returns:
            (total_score, active_events_list)
        """
        return self._require_db().calculate_total_event_score(symbol)
    
    def evaluate_news_batch(self, articles: List[NewsArticle]) -> List[Dict[str, Any]]:
        """
        批量評估新聞文章
        
        Args:
            articles: NewsArticle 列表
            
        Returns:
            檢測到的事件列表
        """
        detected_events = []
        
        for article in articles:
            event_info = self.evaluate_headline(
                headline=article.title,
                source=article.source,
                source_confidence=article.source_credibility,
                affected_symbols=','.join(article.coins_mentioned) if article.coins_mentioned else None
            )
            
            if event_info:
                detected_events.append(event_info)
        
        if detected_events:
            logger.info(
                f"📰 批量評估完成: 從 {len(articles)} 則新聞中檢測到 {len(detected_events)} 個事件"
            )
        
        return detected_events
    
    def cleanup_expired_events(self) -> int:
        """
        清理過期事件 (根據 decay_hours)
        
        Returns:
            清理的事件數量
        """
        db = self._require_db()

        cleaned = 0
        active_events = db.get_active_events()
        
        for event in active_events:
            # 從 metadata 解析 decay_hours
            metadata = event.get('metadata', '')
            decay_hours = 24  # 預設
            
            if 'decay_hours:' in metadata:
                try:
                    decay_str = metadata.split('decay_hours:')[1].strip()
                    decay_hours = int(decay_str.split(';')[0].strip())
                except (ValueError, IndexError):
                    pass
            
            # 檢查是否過期
            created_at = datetime.fromisoformat(event['created_at'])
            if datetime.now() > created_at + timedelta(hours=decay_hours):
                db.resolve_event(
                    event['event_id'],
                    resolution_note=f"Auto-expired after {decay_hours} hours"
                )
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"🧹 已清理 {cleaned} 個過期事件")
        
        return cleaned


# ========================================
# 單例管理
# ========================================

_rule_evaluator: Optional[RuleBasedEvaluator] = None


def get_rule_evaluator() -> RuleBasedEvaluator:
    """獲取規則評估器單例"""
    global _rule_evaluator
    if _rule_evaluator is None:
        _rule_evaluator = RuleBasedEvaluator()
    return _rule_evaluator
