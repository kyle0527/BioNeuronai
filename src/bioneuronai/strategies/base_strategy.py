"""
策略基類 (Base Strategy)
================

所有交易策略的抽象基類。

核心功能模塊：
1. 市場分析 (analyze_market)
2. 入場條件評估 (evaluate_entry_conditions)
3. 執行入場 (execute_entry)
4. 倉位管理 (manage_position)
5. 出場條件評估 (evaluate_exit_conditions)
6. 執行出場 (execute_exit)
7. 風險控制 (control_risk)
8. 性能追蹤 (track_performance)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import logging

from config.trading_costs import TradingCostCalculator

logger = logging.getLogger(__name__)


class StrategyState(Enum):
    """"""
    IDLE = "idle"                    # 
    ANALYZING = "analyzing"          # 
    ENTRY_READY = "entry_ready"      # 
    POSITION_OPEN = "position_open"  # 
    SCALING_IN = "scaling_in"        # 
    SCALING_OUT = "scaling_out"      # 
    EXIT_READY = "exit_ready"        # 
    COOLDOWN = "cooldown"            # 


class SignalStrength(Enum):
    """"""
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


class MarketCondition(Enum):
    """"""
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    SIDEWAYS = "sideways"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class RiskParameters:
    """"""
    max_position_size_pct: float = 5.0       #  (%)
    max_risk_per_trade_pct: float = 1.0      #  (%)
    max_daily_loss_pct: float = 3.0          #  (%)
    max_concurrent_trades: int = 3           # 
    min_risk_reward_ratio: float = 2.0       # 
    trailing_stop_activation: float = 1.5    #  (R)
    trailing_stop_distance: float = 0.5      #  (R)
    max_holding_period_hours: int = 168      #  ()
    cooldown_after_loss: int = 2             #  ()
    correlation_limit: float = 0.7           # 


@dataclass
class TradeSetup:
    """ - """
    symbol: str
    direction: str  # 'long' or 'short'
    
    # 
    entry_price: float
    entry_conditions: List[str] = field(default_factory=list)
    entry_confirmations: int = 0
    required_confirmations: int = 3
    
    # 
    stop_loss: float = 0.0
    take_profit_1: float = 0.0  #  (R:R 2:1)
    take_profit_2: float = 0.0  #  (R:R 4:1)
    take_profit_3: float = 0.0  #  (R:R 6:1+)
    
    # 
    total_position_size: float = 0.0
    entry_portions: int = 3  # 
    exit_portions: Dict[str, float] = field(default_factory=dict)
    # {'tp1': 0.35, 'tp2': 0.35, 'tp3': 0.30}
    
    # 
    risk_amount: float = 0.0
    risk_reward_ratio: float = 0.0
    
    # 
    signal_strength: SignalStrength = SignalStrength.MODERATE
    market_condition: MarketCondition = MarketCondition.SIDEWAYS
    
    # 
    setup_time: datetime = field(default_factory=datetime.now)
    valid_until: datetime = field(default_factory=datetime.now)
    max_entry_wait_minutes: int = 30
    
    # 
    key_levels: Dict[str, float] = field(default_factory=dict)
    invalidation_conditions: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """"""
        return datetime.now() < self.valid_until
    
    def has_enough_confirmations(self) -> bool:
        """"""
        return self.entry_confirmations >= self.required_confirmations


@dataclass
class TradeExecution:
    """"""
    trade_id: str
    setup: TradeSetup
    
    # 
    actual_entry_price: float = 0.0
    entry_slippage: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    entry_fills: List[Dict] = field(default_factory=list)
    
    # 
    current_position_size: float = 0.0
    average_entry_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # 
    exit_fills: List[Dict] = field(default_factory=list)
    average_exit_price: float = 0.0
    exit_time: Optional[datetime] = None
    exit_reason: str = ""
    
    # 
    trailing_stop_price: Optional[float] = None
    trailing_stop_activated: bool = False
    highest_price_since_entry: float = 0.0  # 
    lowest_price_since_entry: float = float('inf')  # 
    
    # 
    max_favorable_excursion: float = 0.0   # MFE
    max_adverse_excursion: float = 0.0     # MAE
    holding_duration: timedelta = field(default_factory=timedelta)
    
    def calculate_r_multiple(self) -> float:
        """ R  ()"""
        if self.setup.risk_amount == 0:
            return 0.0
        return (self.realized_pnl + self.unrealized_pnl) / self.setup.risk_amount


@dataclass
class PositionManagement:
    """"""
    # 
    entry_portions_filled: int = 0
    entry_portions_total: int = 3
    next_entry_price: Optional[float] = None
    
    # 
    exit_portions_filled: int = 0
    exit_portions_total: int = 3
    tp1_filled: bool = False
    tp2_filled: bool = False
    tp3_filled: bool = False
    
    # 
    stop_loss_moved_to_breakeven: bool = False
    stop_loss_trailing: bool = False
    current_stop_loss: float = 0.0
    
    # /
    scaling_in_allowed: bool = True
    scaling_out_in_progress: bool = False


@dataclass
class StrategyPerformance:
    """"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0

    total_profit: float = 0.0
    total_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    average_win: float = 0.0
    average_loss: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0

    average_r_multiple: float = 0.0
    expectancy: float = 0.0

    max_drawdown: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    current_streak: int = 0

    average_holding_time: timedelta = field(default_factory=timedelta)
    trades_today: int = 0
    daily_pnl: float = 0.0

    # 內部累計欄位（不對外展示，用於增量計算）
    _total_r_sum: float = field(default=0.0, repr=False)
    _total_holding_seconds: float = field(default=0.0, repr=False)
    _peak_net_pnl: float = field(default=0.0, repr=False)
    _last_trade_date: str = field(default="", repr=False)  # "YYYY-MM-DD"

    def update(self, trade: 'TradeExecution') -> None:
        """每筆交易完成後呼叫，更新所有績效欄位。"""
        self.total_trades += 1
        pnl = trade.realized_pnl

        # ── PnL / 勝敗統計 ──────────────────────────────────────────
        if pnl > 0:
            self.winning_trades += 1
            self.total_profit += pnl
            self.largest_win = max(self.largest_win, pnl)
            self.current_streak = self.current_streak + 1 if self.current_streak >= 0 else 1
            self.max_consecutive_wins = max(self.max_consecutive_wins, self.current_streak)
        elif pnl < 0:
            self.losing_trades += 1
            self.total_loss += abs(pnl)
            self.largest_loss = max(self.largest_loss, abs(pnl))
            self.current_streak = self.current_streak - 1 if self.current_streak <= 0 else -1
            self.max_consecutive_losses = max(self.max_consecutive_losses, abs(self.current_streak))
        else:
            self.breakeven_trades += 1

        # ── 衍生統計 ────────────────────────────────────────────────
        if self.winning_trades > 0:
            self.average_win = self.total_profit / self.winning_trades
        if self.losing_trades > 0:
            self.average_loss = self.total_loss / self.losing_trades
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        if self.total_loss > 0:
            self.profit_factor = self.total_profit / self.total_loss
        self.expectancy = (
            self.win_rate * self.average_win
            - (1 - self.win_rate) * self.average_loss
        )

        # ── R 倍數（累計均值）────────────────────────────────────────
        r = trade.calculate_r_multiple()
        self._total_r_sum += r
        self.average_r_multiple = self._total_r_sum / self.total_trades

        # ── 平均持倉時間 ─────────────────────────────────────────────
        if trade.holding_duration.total_seconds() > 0:
            self._total_holding_seconds += trade.holding_duration.total_seconds()
            self.average_holding_time = timedelta(
                seconds=self._total_holding_seconds / self.total_trades
            )

        # ── 每日統計（日期變更時重置）────────────────────────────────
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._last_trade_date:
            self.trades_today = 0
            self.daily_pnl = 0.0
            self._last_trade_date = today
        self.trades_today += 1
        self.daily_pnl += pnl

        # ── Max Drawdown（以累計淨 PnL 峰值計算）────────────────────
        net_pnl = self.total_profit - self.total_loss
        self._peak_net_pnl = max(self._peak_net_pnl, net_pnl)
        if self._peak_net_pnl > 0:
            drawdown = (self._peak_net_pnl - net_pnl) / self._peak_net_pnl
            self.max_drawdown = max(self.max_drawdown, drawdown)


class BaseStrategy(ABC):
    """
    
    
    
    """
    
    def __init__(
        self,
        name: str,
        timeframe: str = "1h",
        risk_params: Optional[RiskParameters] = None,
    ):
        self.name = name
        self.timeframe = timeframe
        self.risk_params = risk_params or RiskParameters()
        
        self.state = StrategyState.IDLE
        self.performance = StrategyPerformance()
        
        self.current_setup: Optional[TradeSetup] = None
        self.active_trades: Dict[str, TradeExecution] = {}
        self.trade_history: List[TradeExecution] = []

        self._last_analysis_time: Optional[datetime] = None
        self._cooldown_until: Optional[datetime] = None
        self.cost_calculator = TradingCostCalculator(
            vip_level=0,
            use_bnb=False,
            default_leverage=5,
        )

    def _finalize_analysis_state(self) -> None:
        """分析結束後同步狀態，避免持倉中被誤重置為 idle。"""
        self.state = (
            StrategyState.POSITION_OPEN
            if self.active_trades
            else StrategyState.IDLE
        )
        
    # ========================
    # 1. 
    # ========================
    
    @abstractmethod
    def analyze_market(
        self, 
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        
        
        
        - market_condition: MarketCondition
        - trend_direction: str ('up', 'down', 'sideways')
        - trend_strength: float (0-100)
        - volatility: str ('low', 'normal', 'high')
        - key_levels: Dict[str, float] (/)
        - analysis_summary: str
        """
        pass
    
    # ========================
    # 2. 
    # ========================
    
    @abstractmethod
    def evaluate_entry_conditions(
        self,
        market_analysis: Dict[str, Any],
        ohlcv_data: np.ndarray,
    ) -> Optional[TradeSetup]:
        """
        
        
        
        1. 
        2. 
        3. 
        4. 
        5. 
        
         TradeSetup  None
        """
        pass
    
    def validate_setup(self, setup: TradeSetup) -> Tuple[bool, List[str]]:
        """
        
        
        Returns:
            (is_valid, list of validation messages)
        """
        messages = []
        is_valid = True
        
        # 1. 
        if setup.risk_reward_ratio < self.risk_params.min_risk_reward_ratio:
            messages.append(
                f" {setup.risk_reward_ratio:.2f} "
                f"<  {self.risk_params.min_risk_reward_ratio}"
            )
            is_valid = False
        
        # 2. 
        if not setup.has_enough_confirmations():
            messages.append(
                f" {setup.entry_confirmations} "
                f"<  {setup.required_confirmations}"
            )
            is_valid = False
        
        # 3. 
        if setup.total_position_size <= 0:
            messages.append("")
            is_valid = False
        
        # 4. 
        if setup.stop_loss == 0:
            messages.append("")
            is_valid = False
        
        # 5. 
        if not setup.is_valid():
            messages.append("")
            is_valid = False
        
        # 6. 
        if self._cooldown_until and datetime.now() < self._cooldown_until:
            messages.append(
                f" {self._cooldown_until.strftime('%H:%M')}"
            )
            is_valid = False
        
        # 7. 
        if len(self.active_trades) >= self.risk_params.max_concurrent_trades:
            messages.append(
                f" {self.risk_params.max_concurrent_trades}"
            )
            is_valid = False
        
        return is_valid, messages

    def _entry_side_for_setup(self, setup: TradeSetup) -> str:
        """將策略方向轉成訂單方向。"""
        return "BUY" if setup.direction == "long" else "SELL"

    def _check_connector_entry_conflict(
        self,
        setup: TradeSetup,
        connector: Any,
    ) -> Tuple[bool, str]:
        """檢查 connector 層是否已有待成交進場單或既有持倉。"""
        if connector is None:
            return False, ""

        side = self._entry_side_for_setup(setup)

        try:
            if hasattr(connector, "has_pending_entry_order"):
                if bool(connector.has_pending_entry_order(setup.symbol, side=side)):
                    return True, f"已有待成交進場單: {setup.symbol} {side}"

            if hasattr(connector, "has_open_position"):
                if bool(connector.has_open_position(setup.symbol)):
                    return True, f"已有持倉: {setup.symbol}"
        except Exception as exc:
            logger.warning("檢查 connector 進場衝突時失敗: %s", exc)

        return False, ""

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _get_dynamic_cost_inputs(
        self,
        setup: TradeSetup,
        connector: Any,
    ) -> Tuple[Optional[float], Optional[float]]:
        """從 connector 提取資金費率與即時 spread。"""
        if connector is None:
            return None, None

        funding_rate: Optional[float] = None
        spread_bps: Optional[float] = None
        try:
            if hasattr(connector, "get_premium_index"):
                premium = connector.get_premium_index(setup.symbol)
                if premium:
                    funding_rate = self._safe_float(premium.get("lastFundingRate"))
        except Exception as exc:
            logger.debug("提取 funding rate 失敗: %s", exc)

        try:
            if hasattr(connector, "get_book_ticker"):
                ticker = connector.get_book_ticker(setup.symbol)
                if ticker:
                    best_bid = self._safe_float(ticker.get("bidPrice"))
                    best_ask = self._safe_float(ticker.get("askPrice"))
                    mid = (best_bid + best_ask) / 2
                    if mid > 0:
                        spread_bps = ((best_ask - best_bid) / mid) * 10000
        except Exception as exc:
            logger.debug("提取 spread 失敗: %s", exc)

        return funding_rate, spread_bps

    def _estimate_liquidation_price(
        self,
        setup: TradeSetup,
        leverage: Optional[int] = None,
    ) -> float:
        """使用既有交易成本計算器估算強平價。"""
        if setup.entry_price <= 0 or setup.total_position_size <= 0:
            return 0.0
        costs = self.cost_calculator.calculate_entry_exit_costs(
            position_size_usd=setup.total_position_size * setup.entry_price,
            entry_price=setup.entry_price,
            exit_price=setup.entry_price,
            symbol=setup.symbol,
            leverage=leverage or self.cost_calculator.default_leverage,
            position_side=setup.direction if setup.direction in ("long", "short") else "long",
        )
        return float(costs.get("liquidation_price", 0.0))

    def _get_primary_take_profit(self, setup: TradeSetup) -> float:
        """取得策略最保守的第一個止盈目標。"""
        for price in (setup.take_profit_1, setup.take_profit_2, setup.take_profit_3):
            if price and price > 0:
                return float(price)
        return 0.0

    def _passes_pre_entry_guards(
        self,
        setup: TradeSetup,
        connector: Any,
    ) -> Tuple[bool, str]:
        """進場前統一檢查：成本效益與止損必須先於強平。"""
        leverage = self.cost_calculator.default_leverage
        liquidation_price = self._estimate_liquidation_price(setup, leverage=leverage)
        if liquidation_price > 0:
            if setup.direction == "long" and setup.stop_loss <= liquidation_price:
                return False, f"止損 {setup.stop_loss:.2f} 未高於強平價 {liquidation_price:.2f}"
            if setup.direction == "short" and setup.stop_loss >= liquidation_price:
                return False, f"止損 {setup.stop_loss:.2f} 未低於強平價 {liquidation_price:.2f}"

        take_profit = self._get_primary_take_profit(setup)
        if take_profit > 0 and setup.entry_price > 0 and setup.total_position_size > 0:
            funding_rate, spread_bps = self._get_dynamic_cost_inputs(setup, connector)
            min_profit_pct = self.cost_calculator.get_minimum_profit_target(
                position_size_usd=setup.total_position_size * setup.entry_price,
                symbol=setup.symbol,
                desired_profit_margin=0.0,
                leverage=leverage,
                based_on="notional",
                funding_rate=funding_rate,
                spread_bps=spread_bps,
                position_side=setup.direction if setup.direction in ("long", "short") else "long",
            )
            expected_profit_pct = abs(take_profit - setup.entry_price) / setup.entry_price * 100
            if expected_profit_pct < min_profit_pct:
                return False, (
                    f"預期利潤 {expected_profit_pct:.3f}% 低於最低成本門檻 {min_profit_pct:.3f}%"
                )

        return True, ""
    
    # ========================
    # 3. 
    # ========================
    
    @abstractmethod
    def execute_entry(
        self,
        setup: TradeSetup,
        connector: Any,  # BinanceFuturesConnector
    ) -> Optional[TradeExecution]:
        """
        
        
        
        1. 
        2. 
        3.  (/)
        4. 
        5. 
        """
        pass
    
    # ========================
    # 4. 
    # ========================
    
    @abstractmethod
    def manage_position(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> PositionManagement:
        """
        
        
        
        1. 
        2. 
        3. 
        4. 
        5. 
        """
        pass
    
    def update_trailing_stop(
        self,
        trade: TradeExecution,
        current_price: float,
    ) -> Optional[float]:
        """"""
        r_multiple = trade.calculate_r_multiple()
        
        #  1.5R 
        if r_multiple >= self.risk_params.trailing_stop_activation:
            if not trade.trailing_stop_activated:
                trade.trailing_stop_activated = True
                logger.info(
                    f" @ R={r_multiple:.2f}"
                )
            
            risk_per_unit = abs(
                trade.setup.entry_price - trade.setup.stop_loss
            )
            trail_distance = risk_per_unit * self.risk_params.trailing_stop_distance
            
            if trade.setup.direction == 'long':
                trade.highest_price_since_entry = max(
                    trade.highest_price_since_entry,
                    current_price
                )
                new_stop = trade.highest_price_since_entry - trail_distance
                
                if trade.trailing_stop_price is None or new_stop > trade.trailing_stop_price:
                    trade.trailing_stop_price = new_stop
                    return new_stop
            else:
                trade.lowest_price_since_entry = min(
                    trade.lowest_price_since_entry,
                    current_price
                )
                new_stop = trade.lowest_price_since_entry + trail_distance
                
                if trade.trailing_stop_price is None or new_stop < trade.trailing_stop_price:
                    trade.trailing_stop_price = new_stop
                    return new_stop
        
        return None
    
    # ========================
    # 5. 
    # ========================
    
    @abstractmethod
    def evaluate_exit_conditions(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Tuple[bool, str]:
        """
        
        
        
        1. 
        2. 
        3. 
        4. 
        5. 
        6. 
        
        Returns:
            (should_exit, exit_reason)
        """
        pass
    
    def check_time_based_exit(
        self,
        trade: TradeExecution,
    ) -> Tuple[bool, str]:
        """"""
        holding_time = datetime.now() - trade.entry_time
        max_holding = timedelta(hours=self.risk_params.max_holding_period_hours)
        
        if holding_time > max_holding:
            return True, f" ({self.risk_params.max_holding_period_hours}h)"
        
        return False, ""
    
    # ========================
    # 6. 
    # ========================
    
    @abstractmethod
    def execute_exit(
        self,
        trade: TradeExecution,
        reason: str,
        connector: Any,
        partial_exit: bool = False,
        exit_portion: float = 1.0,
    ) -> bool:
        """
        
        
        
        1.  vs 
        2. 
        3. 
        4. 
        5. 
        """
        pass
    
    # ========================
    # 7. 
    # ========================
    
    def control_risk(
        self,
        account_balance: float,
        daily_pnl: float,
    ) -> Dict[str, Any]:
        """
        
        
        Returns:
            {
                'can_trade': bool,
                'position_size_multiplier': float,
                'warnings': List[str],
                'actions': List[str]
            }
        """
        result: Dict[str, Any] = {
            'can_trade': True,
            'position_size_multiplier': 1.0,
            'warnings': [],
            'actions': [],
        }
        
        # 
        daily_loss_pct = (daily_pnl / account_balance) * 100 if account_balance > 0 else 0
        if daily_loss_pct < 0:
            if abs(daily_loss_pct) >= self.risk_params.max_daily_loss_pct:
                result['can_trade'] = False
                result['warnings'].append(
                    f" ({abs(daily_loss_pct):.2f}%)"
                )
                result['actions'].append("")
            elif abs(daily_loss_pct) >= self.risk_params.max_daily_loss_pct * 0.7:
                result['position_size_multiplier'] = 0.5
                result['warnings'].append(
                    " 50%"
                )
        
        # 
        if self.performance.current_streak <= -3:
            result['position_size_multiplier'] *= 0.75
            result['warnings'].append(
                f" {abs(self.performance.current_streak)} "
            )
        
        if self.performance.current_streak <= -5:
            result['can_trade'] = False
            result['warnings'].append("")
            result['actions'].append("")
        
        return result
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_multiplier: float = 1.0,
    ) -> float:
        """
        
        
        
        """
        risk_amount = account_balance * (self.risk_params.max_risk_per_trade_pct / 100)
        risk_amount *= risk_multiplier
        
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit == 0:
            return 0.0
        
        position_size = risk_amount / risk_per_unit
        
        # 
        max_position_value = account_balance * (self.risk_params.max_position_size_pct / 100)
        max_position_size = max_position_value / entry_price
        
        return min(position_size, max_position_size)
    
    # ========================
    # 8. 
    # ========================
    
    def track_performance(self) -> Dict[str, Any]:
        """"""
        return {
            'strategy_name': self.name,
            'timeframe': self.timeframe,
            'total_trades': self.performance.total_trades,
            'win_rate': f"{self.performance.win_rate * 100:.1f}%",
            'profit_factor': f"{self.performance.profit_factor:.2f}",
            'average_r_multiple': f"{self.performance.average_r_multiple:.2f}R",
            'expectancy': f"${self.performance.expectancy:.2f}",
            'max_drawdown': f"{self.performance.max_drawdown:.2f}%",
            'largest_win': f"${self.performance.largest_win:.2f}",
            'largest_loss': f"${self.performance.largest_loss:.2f}",
            'current_streak': self.performance.current_streak,
            'max_consecutive_wins': self.performance.max_consecutive_wins,
            'max_consecutive_losses': self.performance.max_consecutive_losses,
        }
    
    # ========================
    # 
    # ========================
    
    def run_iteration(
        self,
        ohlcv_data: np.ndarray,
        current_price: float,
        account_balance: float,
        connector: Any,
        additional_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        
        
        
        """
        result: Dict[str, Any] = {
            'state': self.state.value,
            'actions_taken': [],
            'signals': [],
            'errors': [],
        }
        
        try:
            # 1. 
            market_analysis = self.analyze_market(ohlcv_data, additional_data)
            result['market_analysis'] = market_analysis
            
            # 2. 
            for trade_id, trade in list(self.active_trades.items()):
                # 
                should_exit, exit_reason = self.evaluate_exit_conditions(
                    trade, current_price, ohlcv_data
                )
                
                if should_exit:
                    success = self.execute_exit(trade, exit_reason, connector)
                    if success:
                        result['actions_taken'].append(
                            f": {trade.setup.symbol} - {exit_reason}"
                        )
                        del self.active_trades[trade_id]
                else:
                    # 
                    position_mgmt = self.manage_position(
                        trade, current_price, ohlcv_data
                    )
                    result['position_management'] = position_mgmt
            
            # 3. 
            risk_check = self.control_risk(
                account_balance,
                self.performance.daily_pnl
            )
            result['risk_check'] = risk_check
            
            if not risk_check['can_trade']:
                result['signals'].append("")
                return result
            
            # 4. 
            if self.state == StrategyState.IDLE:
                setup = self.evaluate_entry_conditions(market_analysis, ohlcv_data)
                
                if setup:
                    # First calculate position size
                    setup.total_position_size = self.calculate_position_size(
                        account_balance,
                        setup.entry_price,
                        setup.stop_loss,
                        risk_check['position_size_multiplier']
                    )

                    # 
                    is_valid, messages = self.validate_setup(setup)
                    
                    if is_valid:
                        has_conflict, conflict_reason = self._check_connector_entry_conflict(
                            setup,
                            connector,
                        )
                        if has_conflict:
                            result['signals'].append(conflict_reason)
                            return result

                        # 
                        new_trade: Optional[TradeExecution] = self.execute_entry(setup, connector)
                        if new_trade:
                            self.active_trades[new_trade.trade_id] = new_trade
                            self.state = StrategyState.POSITION_OPEN
                            result['actions_taken'].append(
                                f": {setup.symbol} {setup.direction} @ {setup.entry_price}"
                            )
                    else:
                        result['signals'].append(
                            f": {', '.join(messages)}"
                        )
        
        except Exception as e:
            logger.error(f": {e}")
            result['errors'].append(str(e))
        
        return result


class StrategyRegistry:
    """"""
    
    _strategies: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, strategy_class: type):
        """"""
        cls._strategies[name] = strategy_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """"""
        return cls._strategies.get(name)
    
    @classmethod
    def list_all(cls) -> List[str]:
        """"""
        return list(cls._strategies.keys())
