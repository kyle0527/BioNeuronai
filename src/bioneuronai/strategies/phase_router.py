"""
交易階段路由器 (Trading Phase Router)
====================================

核心理念：不同交易階段使用不同策略
例如：開盤用突破策略、中盤用趨勢策略、收盤用均值回歸

工作流程：
1. 識別當前交易階段（開盤、盤中、收盤等）
2. 根據市場狀態動態調整階段劃分
3. 為每個階段選擇最優策略
4. 階段過渡時平滑切換

階段類型：
- MARKET_OPEN: 開盤階段（高波動）
- EARLY_SESSION: 早盤（建倉期）
- MID_SESSION: 盤中（主趨勢）
- LATE_SESSION: 尾盤（減倉期）
- MARKET_CLOSE: 收盤（平倉）
- PRE_NEWS: 新聞事件前
- POST_NEWS: 新聞事件後

創建日期：2026-02-14
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np

from .base_strategy import BaseStrategy, TradeSetup, MarketCondition
from .trend_following import TrendFollowingStrategy
from .swing_trading import SwingTradingStrategy
from .mean_reversion import MeanReversionStrategy
from .breakout_trading import BreakoutTradingStrategy

logger = logging.getLogger(__name__)


class TradingPhase(Enum):
    """交易階段"""
    MARKET_OPEN = "market_open"           # 開盤 (高波動)
    EARLY_SESSION = "early_session"       # 早盤 (建倉)
    MID_SESSION = "mid_session"           # 盤中 (主趨勢)
    LATE_SESSION = "late_session"         # 尾盤 (減倉)
    MARKET_CLOSE = "market_close"         # 收盤 (平倉)
    PRE_NEWS = "pre_news"                 # 新聞前
    POST_NEWS = "post_news"               # 新聞後
    HIGH_VOLATILITY = "high_volatility"   # 高波動期
    LOW_VOLATILITY = "low_volatility"     # 低波動期


class TradeActionPhase(Enum):
    """交易動作階段 - 入場/持倉/出場分開使用不同策略"""
    ENTRY = "entry"       # 入場階段 - 決定何時/如何進場
    HOLD = "hold"         # 持倉階段 - 監控加減倉時機
    EXIT = "exit"         # 出場階段 - 決定何時/如何出場


class PhaseAction(Enum):
    """階段動作"""
    ENTER_LONG = "enter_long"       # 做多入場
    ENTER_SHORT = "enter_short"     # 做空入場
    HOLD = "hold"                   # 持倉
    SCALE_IN = "scale_in"           # 加倉
    SCALE_OUT = "scale_out"         # 減倉
    EXIT = "exit"                   # 平倉
    WAIT = "wait"                   # 觀望


@dataclass
class PhaseConfig:
    """階段配置"""
    phase: TradingPhase
    
    # 時間範圍（UTC時間，24小時制）
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None
    
    # 推薦策略（按優先級排序）
    primary_strategy: str = "trend_following"
    secondary_strategy: Optional[str] = None
    fallback_strategy: str = "swing_trading"
    
    # 交易動作階段專屬策略配置 (AI 可動態調整)
    # 若設置，則覆蓋 primary_strategy
    entry_strategy: Optional[str] = None   # 入場專用策略
    hold_strategy: Optional[str] = None    # 持倉專用策略
    exit_strategy: Optional[str] = None    # 出場專用策略
    
    # 推薦動作
    preferred_actions: List[PhaseAction] = field(default_factory=lambda: [PhaseAction.HOLD])
    forbidden_actions: List[PhaseAction] = field(default_factory=list)
    
    # 風險參數調整
    position_size_multiplier: float = 1.0  # 倉位大小倍數
    risk_multiplier: float = 1.0           # 風險倍數
    
    # 市場條件要求
    required_conditions: List[MarketCondition] = field(default_factory=list)
    unfavorable_conditions: List[MarketCondition] = field(default_factory=list)
    
    # 過渡設置
    allow_carry_position: bool = True  # 是否允許持倉跨階段
    force_exit_on_end: bool = False    # 階段結束時強制平倉


@dataclass
class StrategyPerformanceRecord:
    """策略績效記錄 - 用於 AI 動態選擇"""
    strategy_name: str
    phase: TradingPhase
    action_phase: TradeActionPhase
    
    # 績效指標
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.5
    avg_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 1.0
    
    # 最近表現 (用於快速適應)
    recent_trades: int = 0
    recent_wins: int = 0
    recent_pnl: float = 0.0
    
    # 時間戳
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PhaseState:
    """當前階段狀態"""
    current_phase: TradingPhase
    phase_config: PhaseConfig
    phase_start_time: datetime
    time_in_phase_minutes: int = 0
    
    # 階段統計
    trades_in_phase: int = 0
    pnl_in_phase: float = 0.0
    phase_volatility: float = 0.0
    
    # 階段過渡
    next_phase: Optional[TradingPhase] = None
    transition_in_minutes: Optional[int] = None


class TradingPhaseRouter:
    """
    交易階段路由器
    
    根據時間、市場狀態、新聞事件等動態路由到不同策略
    實現「開盤用A、中盤用B、收盤用C」的智能策略組合
    
    核心功能:
    - 動態策略註冊/移除（可隨時增減策略）
    - AI 績效學習（根據歷史表現自動選擇策略）
    - 交易動作階段分離（入場/持倉/出場分別用不同策略）
    """
    
    def __init__(self, timeframe: str = "1h", enable_ai_selection: bool = True):
        self.timeframe = timeframe
        self.enable_ai_selection = enable_ai_selection
        self.current_state: Optional[PhaseState] = None
        self.phase_history: List[PhaseState] = []
        
        # 初始化所有策略實例（可動態增減）
        self.strategies: Dict[str, BaseStrategy] = {
            'trend_following': TrendFollowingStrategy(timeframe),
            'swing_trading': SwingTradingStrategy(timeframe),
            'mean_reversion': MeanReversionStrategy(timeframe),
            'breakout_trading': BreakoutTradingStrategy(timeframe),
        }
        
        # 階段配置（可自定義）
        self.phase_configs = self._create_default_phase_configs()
        
        # 性能追蹤（用於 AI 選擇）
        self.phase_performance: Dict[TradingPhase, Dict[str, float]] = {}
        
        # 策略績效記錄（key: "phase_actionphase_strategy"）
        self.strategy_performance: Dict[str, StrategyPerformanceRecord] = {}
        
        logger.info("🎯 交易階段路由器已初始化")
        logger.info(f"   - 時間框架: {timeframe}")
        logger.info(f"   - 可用策略: {list(self.strategies.keys())}")
        logger.info(f"   - 階段數量: {len(self.phase_configs)}")
        logger.info(f"   - AI 選擇: {'啟用' if enable_ai_selection else '停用'}")
    
    # ==========================================
    # 策略動態註冊/移除
    # ==========================================
    
    def register_strategy(self, name: str, strategy: BaseStrategy) -> bool:
        """
        動態註冊策略（支持任意增減）
        
        Args:
            name: 策略名稱
            strategy: 策略實例
            
        Returns:
            是否成功
        """
        if name in self.strategies:
            logger.warning(f"⚠️ 策略 {name} 已存在，將被覆蓋")
        
        self.strategies[name] = strategy
        logger.info(f"✅ 已註冊策略: {name} ({strategy.__class__.__name__})")
        return True
    
    def unregister_strategy(self, name: str) -> bool:
        """
        移除策略
        
        Args:
            name: 策略名稱
            
        Returns:
            是否成功
        """
        if name not in self.strategies:
            logger.warning(f"⚠️ 策略 {name} 不存在")
            return False
        
        # 檢查是否有階段正在使用此策略
        for phase, config in self.phase_configs.items():
            if config.primary_strategy == name:
                logger.warning(f"⚠️ 策略 {name} 正被 {phase.value} 使用，已切換為 swing_trading")
                config.primary_strategy = "swing_trading"
        
        del self.strategies[name]
        logger.info(f"🗑️ 已移除策略: {name}")
        return True
    
    def list_strategies(self) -> List[str]:
        """列出所有可用策略"""
        return list(self.strategies.keys())
    
    # ==========================================
    # AI 策略選擇器
    # ==========================================
    
    def get_best_strategy_for_action(
        self,
        phase: TradingPhase,
        action_phase: TradeActionPhase,
    ) -> str:
        """
        AI 根據績效選擇最佳策略
        
        Args:
            phase: 交易階段
            action_phase: 交易動作階段（入場/持倉/出場）
            
        Returns:
            最佳策略名稱
        """
        if not self.enable_ai_selection:
            # 不使用 AI，直接返回配置的策略
            return self._get_configured_strategy(phase, action_phase)
        
        # 查找該階段+動作的所有績效記錄
        candidates: List[Tuple[str, float]] = []
        
        for strategy_name in self.strategies.keys():
            key = f"{phase.value}_{action_phase.value}_{strategy_name}"
            
            if key in self.strategy_performance:
                record = self.strategy_performance[key]
                # 計算綜合得分（可調整權重）
                score = self._calculate_strategy_score(record)
                candidates.append((strategy_name, score))
            else:
                # 沒有記錄，給予中等初始分數（鼓勵探索）
                candidates.append((strategy_name, 0.5))
        
        if not candidates:
            return self._get_configured_strategy(phase, action_phase)
        
        # 選擇得分最高的策略
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_strategy = candidates[0][0]
        
        logger.debug(f"🤖 AI 選擇: {phase.value}/{action_phase.value} → {best_strategy}")
        
        return best_strategy
    
    def _calculate_strategy_score(self, record: StrategyPerformanceRecord) -> float:
        """計算策略綜合得分"""
        # 權重配置
        win_rate_weight = 0.3
        profit_factor_weight = 0.25
        recent_weight = 0.25
        sharpe_weight = 0.2
        
        # 正規化各指標
        win_rate_score = record.win_rate
        pf_score = min(record.profit_factor / 3.0, 1.0)  # profit_factor 3.0 算滿分
        sharpe_score = min(max(record.sharpe_ratio / 2.0, 0), 1.0)  # sharpe 2.0 算滿分
        
        # 最近績效
        if record.recent_trades > 0:
            recent_win_rate = record.recent_wins / record.recent_trades
        else:
            recent_win_rate = 0.5
        
        score = (
            win_rate_weight * win_rate_score +
            profit_factor_weight * pf_score +
            recent_weight * recent_win_rate +
            sharpe_weight * sharpe_score
        )
        
        return score
    
    def _get_configured_strategy(
        self,
        phase: TradingPhase,
        action_phase: TradeActionPhase
    ) -> str:
        """獲取配置的策略（非 AI 模式）"""
        config = self.phase_configs[phase]
        
        # 優先使用動作階段專屬策略
        if action_phase == TradeActionPhase.ENTRY and config.entry_strategy:
            return config.entry_strategy
        if action_phase == TradeActionPhase.HOLD and config.hold_strategy:
            return config.hold_strategy
        if action_phase == TradeActionPhase.EXIT and config.exit_strategy:
            return config.exit_strategy
        
        # 降級到主策略
        return config.primary_strategy
    
    def update_strategy_performance(
        self,
        phase: TradingPhase,
        action_phase: TradeActionPhase,
        strategy_name: str,
        trade_pnl: float,
        trade_won: bool,
    ):
        """
        更新策略績效（用於 AI 學習）
        
        Args:
            phase: 交易階段
            action_phase: 交易動作階段
            strategy_name: 策略名稱
            trade_pnl: 交易損益
            trade_won: 是否獲利
        """
        key = f"{phase.value}_{action_phase.value}_{strategy_name}"
        
        if key not in self.strategy_performance:
            self.strategy_performance[key] = StrategyPerformanceRecord(
                strategy_name=strategy_name,
                phase=phase,
                action_phase=action_phase,
            )
        
        record = self.strategy_performance[key]
        
        # 更新總體統計
        record.total_trades += 1
        record.total_pnl += trade_pnl
        if trade_won:
            record.winning_trades += 1
        
        # 計算衍生指標
        record.win_rate = record.winning_trades / record.total_trades
        record.avg_pnl = record.total_pnl / record.total_trades
        
        # 更新最近績效（只保留最近 20 筆）
        record.recent_trades = min(record.recent_trades + 1, 20)
        if record.recent_trades < 20:
            record.recent_wins += 1 if trade_won else 0
            record.recent_pnl += trade_pnl
        
        record.last_updated = datetime.now()
        
        logger.debug(f"📊 更新績效: {key} | 勝率: {record.win_rate:.1%}")
    
    def configure_phase_strategies(
        self,
        phase: TradingPhase,
        entry_strategy: Optional[str] = None,
        hold_strategy: Optional[str] = None,
        exit_strategy: Optional[str] = None,
    ):
        """
        為特定階段配置入場/持倉/出場策略
        
        示例：開盤用突破入場、趨勢持倉、均值回歸出場
        
        Args:
            phase: 交易階段
            entry_strategy: 入場策略
            hold_strategy: 持倉策略
            exit_strategy: 出場策略
        """
        config = self.phase_configs[phase]
        
        if entry_strategy and entry_strategy in self.strategies:
            config.entry_strategy = entry_strategy
        if hold_strategy and hold_strategy in self.strategies:
            config.hold_strategy = hold_strategy
        if exit_strategy and exit_strategy in self.strategies:
            config.exit_strategy = exit_strategy
        
        logger.info(f"✨ 階段 {phase.value} 策略配置:")
        logger.info(f"   - 入場: {config.entry_strategy or config.primary_strategy}")
        logger.info(f"   - 持倉: {config.hold_strategy or config.primary_strategy}")
        logger.info(f"   - 出場: {config.exit_strategy or config.primary_strategy}")
    
    def _create_default_phase_configs(self) -> Dict[TradingPhase, PhaseConfig]:
        """創建預設階段配置"""
        configs = {}
        
        # 🌅 開盤階段 (00:00-02:00 UTC) - 高波動突破
        configs[TradingPhase.MARKET_OPEN] = PhaseConfig(
            phase=TradingPhase.MARKET_OPEN,
            start_hour=0,
            end_hour=2,
            primary_strategy="breakout_trading",
            secondary_strategy="trend_following",
            preferred_actions=[PhaseAction.ENTER_LONG, PhaseAction.ENTER_SHORT],
            position_size_multiplier=0.7,  # 減少倉位（高風險）
            risk_multiplier=1.2,
            unfavorable_conditions=[MarketCondition.LOW_VOLATILITY],
        )
        
        # 🌄 早盤階段 (02:00-08:00 UTC) - 趨勢建立
        configs[TradingPhase.EARLY_SESSION] = PhaseConfig(
            phase=TradingPhase.EARLY_SESSION,
            start_hour=2,
            end_hour=8,
            primary_strategy="trend_following",
            secondary_strategy="swing_trading",
            preferred_actions=[PhaseAction.ENTER_LONG, PhaseAction.ENTER_SHORT, PhaseAction.SCALE_IN],
            position_size_multiplier=1.0,
            required_conditions=[MarketCondition.UPTREND, MarketCondition.DOWNTREND],
        )
        
        # ☀️ 盤中階段 (08:00-16:00 UTC) - 主趨勢跟隨
        configs[TradingPhase.MID_SESSION] = PhaseConfig(
            phase=TradingPhase.MID_SESSION,
            start_hour=8,
            end_hour=16,
            primary_strategy="trend_following",
            secondary_strategy="swing_trading",
            fallback_strategy="mean_reversion",
            preferred_actions=[PhaseAction.HOLD, PhaseAction.SCALE_IN],
            position_size_multiplier=1.2,  # 增加倉位（穩定期）
            allow_carry_position=True,
        )
        
        # 🌆 尾盤階段 (16:00-22:00 UTC) - 減倉整理
        configs[TradingPhase.LATE_SESSION] = PhaseConfig(
            phase=TradingPhase.LATE_SESSION,
            start_hour=16,
            end_hour=22,
            primary_strategy="swing_trading",
            secondary_strategy="mean_reversion",
            preferred_actions=[PhaseAction.SCALE_OUT, PhaseAction.EXIT],
            forbidden_actions=[PhaseAction.ENTER_LONG, PhaseAction.ENTER_SHORT],
            position_size_multiplier=0.8,
        )
        
        # 🌃 收盤階段 (22:00-24:00 UTC) - 平倉離場
        configs[TradingPhase.MARKET_CLOSE] = PhaseConfig(
            phase=TradingPhase.MARKET_CLOSE,
            start_hour=22,
            end_hour=24,
            primary_strategy="mean_reversion",
            preferred_actions=[PhaseAction.EXIT],
            forbidden_actions=[PhaseAction.ENTER_LONG, PhaseAction.ENTER_SHORT, PhaseAction.SCALE_IN],
            position_size_multiplier=0.5,
            force_exit_on_end=True,
        )
        
        # 📰 新聞事件前 - 保守觀望
        configs[TradingPhase.PRE_NEWS] = PhaseConfig(
            phase=TradingPhase.PRE_NEWS,
            primary_strategy="swing_trading",
            preferred_actions=[PhaseAction.WAIT, PhaseAction.SCALE_OUT],
            forbidden_actions=[PhaseAction.ENTER_LONG, PhaseAction.ENTER_SHORT],
            position_size_multiplier=0.3,
            risk_multiplier=0.5,
        )
        
        # 📢 新聞事件後 - 快速反應
        configs[TradingPhase.POST_NEWS] = PhaseConfig(
            phase=TradingPhase.POST_NEWS,
            primary_strategy="breakout_trading",
            secondary_strategy="trend_following",
            preferred_actions=[PhaseAction.ENTER_LONG, PhaseAction.ENTER_SHORT],
            position_size_multiplier=0.8,
            risk_multiplier=1.5,
        )
        
        # 🔥 高波動期 - 突破為主
        configs[TradingPhase.HIGH_VOLATILITY] = PhaseConfig(
            phase=TradingPhase.HIGH_VOLATILITY,
            primary_strategy="breakout_trading",
            fallback_strategy="trend_following",
            preferred_actions=[PhaseAction.ENTER_LONG, PhaseAction.ENTER_SHORT],
            position_size_multiplier=0.6,
            risk_multiplier=1.3,
        )
        
        # 😴 低波動期 - 均值回歸
        configs[TradingPhase.LOW_VOLATILITY] = PhaseConfig(
            phase=TradingPhase.LOW_VOLATILITY,
            primary_strategy="mean_reversion",
            secondary_strategy="swing_trading",
            preferred_actions=[PhaseAction.ENTER_LONG, PhaseAction.ENTER_SHORT],
            position_size_multiplier=1.1,
            required_conditions=[MarketCondition.SIDEWAYS, MarketCondition.LOW_VOLATILITY],
        )
        
        return configs
    
    def _check_news_phase(
        self,
        current_time: datetime,
        has_news_event: bool,
        news_event_time: Optional[datetime]
    ) -> Optional[TradingPhase]:
        """檢查是否處於新聞相關階段"""
        if not (has_news_event and news_event_time):
            return None
        
        time_to_news = (news_event_time - current_time).total_seconds() / 60
        
        if -5 <= time_to_news <= 30:
            return TradingPhase.PRE_NEWS if time_to_news > 0 else TradingPhase.POST_NEWS
        
        return None
    
    def _check_volatility_phase(self, volatility: Optional[float]) -> Optional[TradingPhase]:
        """檢查是否處於波動率異常階段"""
        if volatility is None:
            return None
        
        if volatility > 0.7:
            return TradingPhase.HIGH_VOLATILITY
        if volatility < 0.2:
            return TradingPhase.LOW_VOLATILITY
        
        return None
    
    def _check_time_based_phase(
        self,
        current_time: datetime,
    ) -> TradingPhase:
        """根據時間識別交易階段"""
        hour = current_time.hour
        
        for phase, config in self.phase_configs.items():
            if self._is_phase_time_match(hour, config):
                return phase
        
        return TradingPhase.MID_SESSION
    
    def _is_phase_time_match(self, hour: int, config: PhaseConfig) -> bool:
        """檢查時間是否匹配階段配置"""
        if config.start_hour is None or config.end_hour is None:
            return False
        return config.start_hour <= hour < config.end_hour
    
    def _is_market_unfavorable(self, market_condition: Optional[MarketCondition], config: PhaseConfig) -> bool:
        """檢查市場條件是否不利"""
        if market_condition and config.unfavorable_conditions:
            return market_condition in config.unfavorable_conditions
        return False
    
    def identify_phase(
        self,
        current_time: datetime,
        has_news_event: bool = False,
        news_event_time: Optional[datetime] = None,
        volatility: Optional[float] = None,
    ) -> TradingPhase:
        """
        識別當前交易階段
        
        Args:
            current_time: 當前時間
            has_news_event: 是否有新聞事件
            news_event_time: 新聞事件時間
            volatility: 當前波動率 (0-1)
        
        Returns:
            當前交易階段
        """
        # 優先級1: 新聞事件
        news_phase = self._check_news_phase(current_time, has_news_event, news_event_time)
        if news_phase:
            return news_phase
        
        # 優先級2: 波動率異常
        volatility_phase = self._check_volatility_phase(volatility)
        if volatility_phase:
            return volatility_phase
        
        # 優先級3: 基於時間
        return self._check_time_based_phase(current_time)
    
    def get_strategy_for_phase(
        self,
        phase: TradingPhase,
        action_phase: TradeActionPhase = TradeActionPhase.ENTRY,
    ) -> BaseStrategy:
        """
        獲取當前階段的最優策略
        
        Args:
            phase: 交易階段
            action_phase: 交易動作階段（入場/持倉/出場）
        
        Returns:
            策略實例
        """
        # 使用 AI 選擇最佳策略
        strategy_name = self.get_best_strategy_for_action(phase, action_phase)
        
        # 嘗試獲取策略實例
        strategy = self.strategies.get(strategy_name)
        if strategy:
            return strategy
        
        # 降級嘗試
        config = self.phase_configs[phase]
        
        # 嘗試主策略
        primary = self.strategies.get(config.primary_strategy)
        if primary:
            return primary
        
        # 嘗試次要策略
        if config.secondary_strategy:
            secondary = self.strategies.get(config.secondary_strategy)
            if secondary:
                return secondary
        
        # 後備策略
        fallback = self.strategies.get(config.fallback_strategy)
        if fallback:
            return fallback
        
        # 最後的保障
        return list(self.strategies.values())[0]

    def _infer_hold_or_exit(
        self,
        current_phase: TradingPhase,
        market_data: Dict[str, Any],
    ) -> TradeActionPhase:
        """推斷持倉應 HOLD 或 EXIT。

        EXIT conditions (any one sufficient):
        - Phase is MARKET_CLOSE or LATE_SESSION (session risk)
        - holding_hours > 80 % of max_holding_hours (time-based stop)
        - unrealized_r_multiple < -1.0 (adverse move exceeds 1 R)
        """
        holding_hours: float = market_data.get('holding_hours', 0)
        unrealized_r: float = market_data.get('unrealized_r_multiple', 0.0)
        max_hours: float = market_data.get('max_holding_hours', 72)

        exit_phases = (TradingPhase.MARKET_CLOSE, TradingPhase.LATE_SESSION)
        if (
            current_phase in exit_phases
            or holding_hours > max_hours * 0.8
            or unrealized_r < -1.0
        ):
            return TradeActionPhase.EXIT
        return TradeActionPhase.HOLD

    def _resolve_action_phase(
        self,
        current_phase: TradingPhase,
        market_data: Dict[str, Any],
        has_position: bool,
        action_phase: Optional[TradeActionPhase],
    ) -> TradeActionPhase:
        """決定本次路由的交易動作階段。"""
        if action_phase is not None:
            return action_phase
        if not has_position:
            return TradeActionPhase.ENTRY
        return self._infer_hold_or_exit(current_phase, market_data)

    def _resolve_phase_context(
        self,
        current_time: datetime,
        market_data: Dict[str, Any],
    ) -> Tuple[TradingPhase, Optional[MarketCondition], float]:
        """解析當前交易階段與其上下文。"""
        market_condition = market_data.get('market_condition')
        volatility = market_data.get('volatility', 0.5)
        has_news = market_data.get('has_news_event', False)
        news_time = market_data.get('news_event_time')

        current_phase = self.identify_phase(
            current_time=current_time,
            has_news_event=has_news,
            news_event_time=news_time,
            volatility=volatility,
        )
        return current_phase, market_condition, volatility

    def _build_market_analysis(
        self,
        strategy: BaseStrategy,
        market_data: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Any]:
        """執行策略分析並回傳 OHLCV 與分析結果。"""
        ohlcv_data = market_data.get('ohlcv', np.array([]))  # type: ignore
        market_analysis = strategy.analyze_market(ohlcv_data)
        if isinstance(market_analysis, dict):
            symbol = str(market_data.get("symbol", "") or "").strip()
            if symbol:
                market_analysis.setdefault("symbol", symbol)
        return market_analysis, ohlcv_data

    def _generate_phase_signal(
        self,
        strategy: BaseStrategy,
        config: PhaseConfig,
        market_data: Dict[str, Any],
        action_allowed: bool,
    ) -> Optional[TradeSetup]:
        """根據當前階段與策略生成交易信號。"""
        if not action_allowed:
            return None

        market_analysis, ohlcv_data = self._build_market_analysis(strategy, market_data)
        signal = strategy.evaluate_entry_conditions(market_analysis, ohlcv_data)
        if signal:
            signal = self._adjust_signal_for_phase(signal, config)
        return signal

    def _build_decision_payload(
        self,
        current_time: datetime,
        current_phase: TradingPhase,
        action_phase: TradeActionPhase,
        strategy: BaseStrategy,
        signal: Optional[TradeSetup],
        config: PhaseConfig,
        market_condition: Optional[MarketCondition],
        volatility: float,
    ) -> Dict[str, Any]:
        """組裝 PhaseRouter 的最終決策結果。"""
        return {
            'timestamp': current_time.isoformat(),
            'phase': current_phase.value,
            'action_phase': action_phase.value,
            'strategy_used': strategy.__class__.__name__,
            'ai_selection_enabled': self.enable_ai_selection,
            'signal': signal,
            'config': {
                'position_size_multiplier': config.position_size_multiplier,
                'risk_multiplier': config.risk_multiplier,
                'preferred_actions': [a.value for a in config.preferred_actions],
                'forbidden_actions': [a.value for a in config.forbidden_actions],
            },
            'market_condition': market_condition.value if market_condition else None,
            'volatility': volatility,
        }

    def route_trading_decision(
        self,
        current_time: datetime,
        market_data: Dict[str, Any],
        has_position: bool = False,
        position_direction: Optional[str] = None,
        action_phase: Optional[TradeActionPhase] = None,
    ) -> Dict[str, Any]:
        """
        路由交易決策 - 主入口函數
        
        支援 AI 策略編排：根據交易動作階段（入場/持倉/出場）選擇最優策略
        
        Args:
            current_time: 當前時間
            market_data: 市場數據
            has_position: 是否有持倉
            position_direction: 持倉方向 ('long'/'short')
            action_phase: 交易動作階段（入場/持倉/出場），若為 None 則自動推斷
        
        Returns:
            交易決策結果
        """

        # 1. 識別當前階段
        current_phase, market_condition, volatility = self._resolve_phase_context(
            current_time=current_time,
            market_data=market_data,
        )

        # 2. 更新階段狀態
        if self.current_state is None or self.current_state.current_phase != current_phase:
            self._transition_to_phase(current_phase, current_time)

        # 3. 自動推斷交易動作階段
        resolved_action_phase = self._resolve_action_phase(
            current_phase=current_phase,
            market_data=market_data,
            has_position=has_position,
            action_phase=action_phase,
        )

        # 4. 獲取階段配置和策略（AI 選擇最優策略）
        config = self.phase_configs[current_phase]
        strategy = self.get_strategy_for_phase(current_phase, resolved_action_phase)

        # 5. 檢查階段動作限制
        action_allowed = self._check_action_allowed(config, has_position, position_direction)

        # 6. 生成交易信號
        signal = self._generate_phase_signal(
            strategy=strategy,
            config=config,
            market_data=market_data,
            action_allowed=action_allowed,
        )

        # 7. 構建決策結果（包含 AI 策略編排信息）
        decision = self._build_decision_payload(
            current_time=current_time,
            current_phase=current_phase,
            action_phase=resolved_action_phase,
            strategy=strategy,
            signal=signal,
            config=config,
            market_condition=market_condition,
            volatility=volatility,
        )

        logger.info(
            f"📍 階段路由: {current_phase.value} | "
            f"動作: {resolved_action_phase.value} | "
            f"策略: {strategy.__class__.__name__} | "
            f"AI選擇: {'✓' if self.enable_ai_selection else '✗'}"
        )
        
        return decision
    
    def _transition_to_phase(self, new_phase: TradingPhase, current_time: datetime):
        """過渡到新階段"""
        
        # 保存舊階段到歷史
        if self.current_state:
            self.phase_history.append(self.current_state)
            logger.info(f"🔄 階段切換: {self.current_state.current_phase.value} → {new_phase.value}")
        
        # 創建新階段狀態
        config = self.phase_configs[new_phase]
        self.current_state = PhaseState(
            current_phase=new_phase,
            phase_config=config,
            phase_start_time=current_time,
        )
    
    def _check_action_allowed(
        self,
        config: PhaseConfig,
        has_position: bool,
        _position_direction: Optional[str] = None,  # 前綴 _ 表示保留但未使用
    ) -> bool:
        """
        檢查當前階段是否允許交易動作
        
        Args:
            config: 階段配置
            has_position: 是否有持倉
            _position_direction: 持倉方向 (保留參數，未來可能使用)
        """
        # 如果有持倉
        if has_position:
            if config.force_exit_on_end:
                return True  # 允許平倉動作
            
            if not config.allow_carry_position:
                return False  # 不允許任何動作
        
        # 檢查禁止動作
        if not has_position and PhaseAction.ENTER_LONG in config.forbidden_actions:
            return False
        
        return True
    
    def _adjust_signal_for_phase(
        self,
        signal: Optional[TradeSetup],
        config: PhaseConfig,
    ) -> Optional[TradeSetup]:
        """根據階段配置調整信號"""
        if not signal:
            return None
        
        # 調整倉位大小
        signal.total_position_size *= config.position_size_multiplier
        
        # 調整止損與止盈距離 (基於風險倍數)
        if abs(config.risk_multiplier - 1.0) > 1e-9:
            entry_price = float(signal.entry_price)
            stop_distance = abs(entry_price - float(signal.stop_loss))
            adjusted_distance = stop_distance * config.risk_multiplier
            if signal.direction == "long":
                signal.stop_loss = entry_price - adjusted_distance
                signal.take_profit_1 = entry_price + adjusted_distance * 2
                signal.take_profit_2 = entry_price + adjusted_distance * 4
                signal.take_profit_3 = entry_price + adjusted_distance * 6
            else:
                signal.stop_loss = entry_price + adjusted_distance
                signal.take_profit_1 = entry_price - adjusted_distance * 2
                signal.take_profit_2 = entry_price - adjusted_distance * 4
                signal.take_profit_3 = entry_price - adjusted_distance * 6
        
        return signal
    
    def get_phase_statistics(self) -> Dict[str, Any]:
        """獲取階段統計信息"""
        stats = {}
        
        for phase in TradingPhase:
            phase_states = [s for s in self.phase_history if s.current_phase == phase]
            
            if phase_states:
                stats[phase.value] = {
                    'count': len(phase_states),
                    'total_trades': sum(s.trades_in_phase for s in phase_states),
                    'total_pnl': sum(s.pnl_in_phase for s in phase_states),
                    'avg_pnl': np.mean([s.pnl_in_phase for s in phase_states]),
                }
        
        return stats
    
    def save_phase_configs(self, filepath: str):
        """保存階段配置"""
        configs_dict = {}
        for phase, config in self.phase_configs.items():
            configs_dict[phase.value] = {
                'start_hour': config.start_hour,
                'end_hour': config.end_hour,
                'primary_strategy': config.primary_strategy,
                'secondary_strategy': config.secondary_strategy,
                'position_size_multiplier': config.position_size_multiplier,
                'risk_multiplier': config.risk_multiplier,
                'preferred_actions': [a.value for a in config.preferred_actions],
                'forbidden_actions': [a.value for a in config.forbidden_actions],
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(configs_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 階段配置已保存: {filepath}")
    
    def _update_phase_config(
        self,
        phase: TradingPhase,
        config_data: Dict[str, Any]
    ):
        """更新單個階段配置"""
        existing = self.phase_configs[phase]
        
        # 更新可配置的屬性
        if 'position_size_multiplier' in config_data:
            existing.position_size_multiplier = config_data['position_size_multiplier']
        if 'risk_multiplier' in config_data:
            existing.risk_multiplier = config_data['risk_multiplier']
        if 'primary_strategy' in config_data:
            existing.primary_strategy = config_data['primary_strategy']
        if 'secondary_strategy' in config_data:
            existing.secondary_strategy = config_data['secondary_strategy']
    
    def load_phase_configs(self, filepath: str):
        """載入階段配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            configs_dict = json.load(f)
        
        # 解析並更新配置
        for phase_name, config_data in configs_dict.items():
            try:
                phase = TradingPhase(phase_name)
                if phase in self.phase_configs:
                    self._update_phase_config(phase, config_data)
                    logger.info(f"  ✅ 更新階段配置: {phase_name}")
            except ValueError:
                logger.warning(f"  ⚠️ 未知階段: {phase_name}")
        
        logger.info(f"📂 階段配置已載入: {filepath}")


# ============================================================================
# 使用示例
# ============================================================================

def demo():
    """演示如何使用階段路由器"""
    
    # 創建路由器
    router = TradingPhaseRouter(timeframe="1h")
    
    # 模擬市場數據
    market_data = {
        'price': 50000.0,
        'volatility': 0.5,
        'market_condition': MarketCondition.UPTREND,
        'has_news_event': False,
    }
    
    # 不同時間點的決策
    test_times = [
        datetime(2024, 1, 1, 1, 0),   # 開盤
        datetime(2024, 1, 1, 5, 0),   # 早盤
        datetime(2024, 1, 1, 12, 0),  # 盤中
        datetime(2024, 1, 1, 18, 0),  # 尾盤
        datetime(2024, 1, 1, 23, 0),  # 收盤
    ]
    
    for test_time in test_times:
        decision = router.route_trading_decision(
            current_time=test_time,
            market_data=market_data,
            has_position=False,
        )
        
        print(f"\n時間: {test_time.strftime('%H:%M')}")
        print(f"階段: {decision['phase']}")
        print(f"策略: {decision['strategy_used']}")
        print(f"倉位倍數: {decision['config']['position_size_multiplier']}")
    
    # 統計信息
    stats = router.get_phase_statistics()
    print(f"\n階段統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    demo()
