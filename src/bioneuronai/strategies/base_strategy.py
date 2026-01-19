"""
交易策略基礎類別
================

定義所有策略必須實現的完整流程框架。
每個策略不是簡單的訊號產生器，而是完整的交易系統。

完整流程包含：
1. 市場環境分析 (analyze_market)
2. 進場條件評估 (evaluate_entry_conditions)
3. 進場執行 (execute_entry)
4. 部位管理 (manage_position)
5. 出場條件評估 (evaluate_exit_conditions)
6. 出場執行 (execute_exit)
7. 風險控制 (control_risk)
8. 績效追蹤 (track_performance)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)


class StrategyState(Enum):
    """策略狀態"""
    IDLE = "idle"                    # 空閒，等待機會
    ANALYZING = "analyzing"          # 分析中
    ENTRY_READY = "entry_ready"      # 準備進場
    POSITION_OPEN = "position_open"  # 持有部位
    SCALING_IN = "scaling_in"        # 加碼中
    SCALING_OUT = "scaling_out"      # 減碼中
    EXIT_READY = "exit_ready"        # 準備出場
    COOLDOWN = "cooldown"            # 冷卻期


class SignalStrength(Enum):
    """訊號強度等級"""
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


class MarketCondition(Enum):
    """市場狀態"""
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    SIDEWAYS = "sideways"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class RiskParameters:
    """風險參數"""
    max_position_size_pct: float = 5.0       # 最大部位大小 (%)
    max_risk_per_trade_pct: float = 1.0      # 每筆交易最大風險 (%)
    max_daily_loss_pct: float = 3.0          # 每日最大損失 (%)
    max_concurrent_trades: int = 3           # 最大同時持倉數
    min_risk_reward_ratio: float = 2.0       # 最小風險報酬比
    trailing_stop_activation: float = 1.5    # 追蹤止損啟動 (R倍數)
    trailing_stop_distance: float = 0.5      # 追蹤止損距離 (R倍數)
    max_holding_period_hours: int = 168      # 最大持倉時間 (小時)
    cooldown_after_loss: int = 2             # 虧損後冷卻期 (小時)
    correlation_limit: float = 0.7           # 關聯性限制


@dataclass
class TradeSetup:
    """交易設置 - 進場前的完整規劃"""
    symbol: str
    direction: str  # 'long' or 'short'
    
    # 進場條件
    entry_price: float
    entry_conditions: List[str] = field(default_factory=list)
    entry_confirmations: int = 0
    required_confirmations: int = 3
    
    # 出場規劃
    stop_loss: float = 0.0
    take_profit_1: float = 0.0  # 第一目標 (R:R 2:1)
    take_profit_2: float = 0.0  # 第二目標 (R:R 4:1)
    take_profit_3: float = 0.0  # 第三目標 (R:R 6:1+)
    
    # 部位規劃
    total_position_size: float = 0.0
    entry_portions: int = 3  # 分批進場次數
    exit_portions: Dict[str, float] = field(default_factory=dict)
    # {'tp1': 0.35, 'tp2': 0.35, 'tp3': 0.30}
    
    # 風險計算
    risk_amount: float = 0.0
    risk_reward_ratio: float = 0.0
    
    # 訊號分析
    signal_strength: SignalStrength = SignalStrength.MODERATE
    market_condition: MarketCondition = MarketCondition.SIDEWAYS
    
    # 時間相關
    setup_time: datetime = field(default_factory=datetime.now)
    valid_until: datetime = field(default_factory=datetime.now)
    max_entry_wait_minutes: int = 30
    
    # 額外分析
    key_levels: Dict[str, float] = field(default_factory=dict)
    invalidation_conditions: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """檢查設置是否仍然有效"""
        return datetime.now() < self.valid_until
    
    def has_enough_confirmations(self) -> bool:
        """檢查是否有足夠的確認訊號"""
        return self.entry_confirmations >= self.required_confirmations


@dataclass
class TradeExecution:
    """交易執行記錄"""
    trade_id: str
    setup: TradeSetup
    
    # 進場執行
    actual_entry_price: float = 0.0
    entry_slippage: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    entry_fills: List[Dict] = field(default_factory=list)
    
    # 部位狀態
    current_position_size: float = 0.0
    average_entry_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # 出場執行
    exit_fills: List[Dict] = field(default_factory=list)
    average_exit_price: float = 0.0
    exit_time: Optional[datetime] = None
    exit_reason: str = ""
    
    # 追蹤止損
    trailing_stop_price: Optional[float] = None
    trailing_stop_activated: bool = False
    highest_price_since_entry: float = 0.0  # 多單用
    lowest_price_since_entry: float = float('inf')  # 空單用
    
    # 統計
    max_favorable_excursion: float = 0.0   # MFE
    max_adverse_excursion: float = 0.0     # MAE
    holding_duration: timedelta = field(default_factory=timedelta)
    
    def calculate_r_multiple(self) -> float:
        """計算 R 倍數 (盈虧相對於初始風險)"""
        if self.setup.risk_amount == 0:
            return 0.0
        return (self.realized_pnl + self.unrealized_pnl) / self.setup.risk_amount


@dataclass
class PositionManagement:
    """部位管理狀態"""
    # 分批進場
    entry_portions_filled: int = 0
    entry_portions_total: int = 3
    next_entry_price: Optional[float] = None
    
    # 分批出場
    exit_portions_filled: int = 0
    exit_portions_total: int = 3
    tp1_filled: bool = False
    tp2_filled: bool = False
    tp3_filled: bool = False
    
    # 動態調整
    stop_loss_moved_to_breakeven: bool = False
    stop_loss_trailing: bool = False
    current_stop_loss: float = 0.0
    
    # 加碼/減碼
    scaling_in_allowed: bool = True
    scaling_out_in_progress: bool = False


@dataclass
class StrategyPerformance:
    """策略績效追蹤"""
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
    current_streak: int = 0  # 正數=連勝，負數=連敗
    
    average_holding_time: timedelta = field(default_factory=timedelta)
    trades_today: int = 0
    daily_pnl: float = 0.0
    
    def update(self, trade: TradeExecution):
        """更新績效統計"""
        self.total_trades += 1
        
        pnl = trade.realized_pnl
        if pnl > 0:
            self.winning_trades += 1
            self.total_profit += pnl
            self.largest_win = max(self.largest_win, pnl)
            if self.current_streak >= 0:
                self.current_streak += 1
            else:
                self.current_streak = 1
            self.max_consecutive_wins = max(
                self.max_consecutive_wins, 
                self.current_streak
            )
        elif pnl < 0:
            self.losing_trades += 1
            self.total_loss += abs(pnl)
            self.largest_loss = max(self.largest_loss, abs(pnl))
            if self.current_streak <= 0:
                self.current_streak -= 1
            else:
                self.current_streak = -1
            self.max_consecutive_losses = max(
                self.max_consecutive_losses, 
                abs(self.current_streak)
            )
        else:
            self.breakeven_trades += 1
        
        # 計算衍生指標
        if self.winning_trades > 0:
            self.average_win = self.total_profit / self.winning_trades
        if self.losing_trades > 0:
            self.average_loss = self.total_loss / self.losing_trades
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        if self.total_loss > 0:
            self.profit_factor = self.total_profit / self.total_loss
        
        # 期望值 = (勝率 × 平均獲利) - (敗率 × 平均虧損)
        self.expectancy = (
            self.win_rate * self.average_win - 
            (1 - self.win_rate) * self.average_loss
        )


class BaseStrategy(ABC):
    """
    交易策略基礎類別
    
    所有策略必須實現完整的交易流程，不僅僅是訊號產生。
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
        
    # ========================
    # 1. 市場環境分析
    # ========================
    
    @abstractmethod
    def analyze_market(
        self, 
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        分析市場環境
        
        必須返回：
        - market_condition: MarketCondition
        - trend_direction: str ('up', 'down', 'sideways')
        - trend_strength: float (0-100)
        - volatility: str ('low', 'normal', 'high')
        - key_levels: Dict[str, float] (支撐/阻力)
        - analysis_summary: str
        """
        pass
    
    # ========================
    # 2. 進場條件評估
    # ========================
    
    @abstractmethod
    def evaluate_entry_conditions(
        self,
        market_analysis: Dict[str, Any],
        ohlcv_data: np.ndarray,
    ) -> Optional[TradeSetup]:
        """
        評估進場條件
        
        必須檢查多重確認：
        1. 趨勢方向確認
        2. 動能確認
        3. 價量確認
        4. 時間確認
        5. 風險報酬確認
        
        返回 TradeSetup 如果條件滿足，否則返回 None
        """
        pass
    
    def validate_setup(self, setup: TradeSetup) -> Tuple[bool, List[str]]:
        """
        驗證交易設置
        
        Returns:
            (is_valid, list of validation messages)
        """
        messages = []
        is_valid = True
        
        # 1. 風險報酬比檢查
        if setup.risk_reward_ratio < self.risk_params.min_risk_reward_ratio:
            messages.append(
                f"風險報酬比 {setup.risk_reward_ratio:.2f} "
                f"< 最小要求 {self.risk_params.min_risk_reward_ratio}"
            )
            is_valid = False
        
        # 2. 確認訊號檢查
        if not setup.has_enough_confirmations():
            messages.append(
                f"確認訊號 {setup.entry_confirmations} "
                f"< 要求 {setup.required_confirmations}"
            )
            is_valid = False
        
        # 3. 部位大小檢查
        if setup.total_position_size <= 0:
            messages.append("部位大小無效")
            is_valid = False
        
        # 4. 停損設置檢查
        if setup.stop_loss == 0:
            messages.append("未設置停損")
            is_valid = False
        
        # 5. 有效期檢查
        if not setup.is_valid():
            messages.append("設置已過期")
            is_valid = False
        
        # 6. 冷卻期檢查
        if self._cooldown_until and datetime.now() < self._cooldown_until:
            messages.append(
                f"冷卻期中，直到 {self._cooldown_until.strftime('%H:%M')}"
            )
            is_valid = False
        
        # 7. 最大持倉數檢查
        if len(self.active_trades) >= self.risk_params.max_concurrent_trades:
            messages.append(
                f"已達最大持倉數 {self.risk_params.max_concurrent_trades}"
            )
            is_valid = False
        
        return is_valid, messages
    
    # ========================
    # 3. 進場執行
    # ========================
    
    @abstractmethod
    def execute_entry(
        self,
        setup: TradeSetup,
        connector: Any,  # BinanceFuturesConnector
    ) -> Optional[TradeExecution]:
        """
        執行進場
        
        必須處理：
        1. 分批進場邏輯
        2. 滑點控制
        3. 訂單類型選擇 (限價/市價)
        4. 停損單設置
        5. 錯誤處理
        """
        pass
    
    # ========================
    # 4. 部位管理
    # ========================
    
    @abstractmethod
    def manage_position(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> PositionManagement:
        """
        管理持倉部位
        
        必須處理：
        1. 追蹤止損更新
        2. 移動停損到損益平衡
        3. 分批獲利了結
        4. 加碼機會評估
        5. 減碼決策
        """
        pass
    
    def update_trailing_stop(
        self,
        trade: TradeExecution,
        current_price: float,
    ) -> Optional[float]:
        """更新追蹤止損"""
        r_multiple = trade.calculate_r_multiple()
        
        # 當盈利達到 1.5R 時啟動追蹤止損
        if r_multiple >= self.risk_params.trailing_stop_activation:
            if not trade.trailing_stop_activated:
                trade.trailing_stop_activated = True
                logger.info(
                    f"追蹤止損啟動 @ R={r_multiple:.2f}"
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
    # 5. 出場條件評估
    # ========================
    
    @abstractmethod
    def evaluate_exit_conditions(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Tuple[bool, str]:
        """
        評估出場條件
        
        必須檢查：
        1. 停損觸發
        2. 目標價達成
        3. 追蹤止損觸發
        4. 時間止損
        5. 趨勢反轉訊號
        6. 異常波動
        
        Returns:
            (should_exit, exit_reason)
        """
        pass
    
    def check_time_based_exit(
        self,
        trade: TradeExecution,
    ) -> Tuple[bool, str]:
        """檢查時間相關的出場條件"""
        holding_time = datetime.now() - trade.entry_time
        max_holding = timedelta(hours=self.risk_params.max_holding_period_hours)
        
        if holding_time > max_holding:
            return True, f"超過最大持倉時間 ({self.risk_params.max_holding_period_hours}h)"
        
        return False, ""
    
    # ========================
    # 6. 出場執行
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
        執行出場
        
        必須處理：
        1. 完全出場 vs 部分出場
        2. 訂單類型選擇
        3. 滑點控制
        4. 績效記錄更新
        5. 冷卻期設置（如果虧損）
        """
        pass
    
    # ========================
    # 7. 風險控制
    # ========================
    
    def control_risk(
        self,
        account_balance: float,
        daily_pnl: float,
    ) -> Dict[str, Any]:
        """
        風險控制檢查
        
        Returns:
            {
                'can_trade': bool,
                'position_size_multiplier': float,
                'warnings': List[str],
                'actions': List[str]
            }
        """
        result = {
            'can_trade': True,
            'position_size_multiplier': 1.0,
            'warnings': [],
            'actions': [],
        }
        
        # 每日損失限制
        daily_loss_pct = (daily_pnl / account_balance) * 100 if account_balance > 0 else 0
        if daily_loss_pct < 0:
            if abs(daily_loss_pct) >= self.risk_params.max_daily_loss_pct:
                result['can_trade'] = False
                result['warnings'].append(
                    f"已達每日最大損失限制 ({abs(daily_loss_pct):.2f}%)"
                )
                result['actions'].append("停止今日交易")
            elif abs(daily_loss_pct) >= self.risk_params.max_daily_loss_pct * 0.7:
                result['position_size_multiplier'] = 0.5
                result['warnings'].append(
                    f"接近每日最大損失限制，減少部位大小 50%"
                )
        
        # 連敗控制
        if self.performance.current_streak <= -3:
            result['position_size_multiplier'] *= 0.75
            result['warnings'].append(
                f"連敗 {abs(self.performance.current_streak)} 次，減少部位大小"
            )
        
        if self.performance.current_streak <= -5:
            result['can_trade'] = False
            result['warnings'].append("連敗過多，建議暫停交易")
            result['actions'].append("檢視策略執行")
        
        return result
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_multiplier: float = 1.0,
    ) -> float:
        """
        計算部位大小
        
        基於固定風險百分比法則
        """
        risk_amount = account_balance * (self.risk_params.max_risk_per_trade_pct / 100)
        risk_amount *= risk_multiplier
        
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit == 0:
            return 0.0
        
        position_size = risk_amount / risk_per_unit
        
        # 確保不超過最大部位大小
        max_position_value = account_balance * (self.risk_params.max_position_size_pct / 100)
        max_position_size = max_position_value / entry_price
        
        return min(position_size, max_position_size)
    
    # ========================
    # 8. 績效追蹤
    # ========================
    
    def track_performance(self) -> Dict[str, Any]:
        """獲取績效摘要"""
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
    # 主要交易循環
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
        執行一次策略迭代
        
        這是策略的主要執行入口
        """
        result = {
            'state': self.state.value,
            'actions_taken': [],
            'signals': [],
            'errors': [],
        }
        
        try:
            # 1. 市場分析
            market_analysis = self.analyze_market(ohlcv_data, additional_data)
            result['market_analysis'] = market_analysis
            
            # 2. 管理現有持倉
            for trade_id, trade in list(self.active_trades.items()):
                # 評估出場條件
                should_exit, exit_reason = self.evaluate_exit_conditions(
                    trade, current_price, ohlcv_data
                )
                
                if should_exit:
                    success = self.execute_exit(trade, exit_reason, connector)
                    if success:
                        result['actions_taken'].append(
                            f"出場: {trade.setup.symbol} - {exit_reason}"
                        )
                        del self.active_trades[trade_id]
                else:
                    # 管理持倉
                    position_mgmt = self.manage_position(
                        trade, current_price, ohlcv_data
                    )
                    result['position_management'] = position_mgmt
            
            # 3. 風險控制檢查
            risk_check = self.control_risk(
                account_balance,
                self.performance.daily_pnl
            )
            result['risk_check'] = risk_check
            
            if not risk_check['can_trade']:
                result['signals'].append("風險控制：暫停交易")
                return result
            
            # 4. 評估新進場機會
            if self.state == StrategyState.IDLE:
                setup = self.evaluate_entry_conditions(market_analysis, ohlcv_data)
                
                if setup:
                    # 驗證設置
                    is_valid, messages = self.validate_setup(setup)
                    
                    if is_valid:
                        # 調整部位大小
                        setup.total_position_size = self.calculate_position_size(
                            account_balance,
                            setup.entry_price,
                            setup.stop_loss,
                            risk_check['position_size_multiplier']
                        )
                        
                        # 執行進場
                        trade = self.execute_entry(setup, connector)
                        if trade:
                            self.active_trades[trade.trade_id] = trade
                            self.state = StrategyState.POSITION_OPEN
                            result['actions_taken'].append(
                                f"進場: {setup.symbol} {setup.direction} @ {setup.entry_price}"
                            )
                    else:
                        result['signals'].append(
                            f"設置驗證失敗: {', '.join(messages)}"
                        )
        
        except Exception as e:
            logger.error(f"策略執行錯誤: {e}")
            result['errors'].append(str(e))
        
        return result


class StrategyRegistry:
    """策略註冊表"""
    
    _strategies: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, strategy_class: type):
        """註冊策略"""
        cls._strategies[name] = strategy_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """獲取策略類別"""
        return cls._strategies.get(name)
    
    @classmethod
    def list_all(cls) -> List[str]:
        """列出所有已註冊的策略"""
        return list(cls._strategies.keys())
