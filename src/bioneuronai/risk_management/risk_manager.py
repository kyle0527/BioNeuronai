"""
風險管理系統
專門處理交易風險控制和資金管理
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class RiskParameters:
    """風險參數配置"""
    
    def __init__(self):
        # 基本風險參數
        self.max_risk_per_trade = 0.02  # 單筆最大風險 2%
        self.max_drawdown = 0.10  # 最大回撤 10%
        self.max_trades_per_day = 10  # 每日最大交易次數
        self.min_confidence = 0.65  # 最低信號置信度
        
        # 倉位管理
        self.max_position_ratio = 0.25  # 最大單倉位比例
        self.max_correlation = 0.7  # 最大相關性
        
        # 止損止盈
        self.default_stop_loss = 0.02  # 預設止損 2%
        self.default_take_profit = 0.04  # 預設止盈 4%
        
        # 時間控制
        self.trading_hours_start = 0  # 交易時間開始（24小時制）
        self.trading_hours_end = 23  # 交易時間結束
        
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'max_risk_per_trade': self.max_risk_per_trade,
            'max_drawdown': self.max_drawdown,
            'max_trades_per_day': self.max_trades_per_day,
            'min_confidence': self.min_confidence,
            'max_position_ratio': self.max_position_ratio,
            'max_correlation': self.max_correlation,
            'default_stop_loss': self.default_stop_loss,
            'default_take_profit': self.default_take_profit,
            'trading_hours_start': self.trading_hours_start,
            'trading_hours_end': self.trading_hours_end
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RiskParameters':
        """從字典創建"""
        params = cls()
        for key, value in data.items():
            if hasattr(params, key):
                setattr(params, key, value)
        return params


class PositionSizeCalculator:
    """倉位大小計算器"""
    
    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """凱利公式計算最優倉位"""
        if avg_loss == 0 or win_rate <= 0:
            return 0.0
        
        win_loss_ratio = avg_win / avg_loss
        kelly_fraction = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # 保守起見，使用 Kelly 分數的一半
        return max(0, min(kelly_fraction * 0.5, 0.25))
    
    @staticmethod
    def fixed_risk(account_balance: float, risk_per_trade: float, 
                  entry_price: float, stop_loss_price: float) -> float:
        """固定風險計算倉位"""
        if stop_loss_price <= 0 or entry_price <= 0:
            return 0.0
        
        risk_amount = account_balance * risk_per_trade
        price_risk = abs(entry_price - stop_loss_price) / entry_price
        
        if price_risk == 0:
            return 0.0
        
        return risk_amount / (entry_price * price_risk)
    
    @staticmethod
    def volatility_adjusted(base_position: float, volatility: float, 
                           base_volatility: float = 0.25) -> float:
        """波動率調整倉位"""
        if volatility <= 0:
            return base_position
        
        volatility_factor = base_volatility / volatility
        return base_position * min(volatility_factor, 2.0)  # 最大調整2倍


class DrawdownTracker:
    """回撤追蹤器"""
    
    def __init__(self):
        self.peak_balance = 0.0
        self.current_balance = 0.0
        self.max_drawdown = 0.0
        self.balance_history = []
    
    def update(self, new_balance: float):
        """更新餘額"""
        self.current_balance = new_balance
        self.balance_history.append({
            'balance': new_balance,
            'timestamp': datetime.now()
        })
        
        # 更新峰值
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
        
        # 計算當前回撤
        if self.peak_balance > 0:
            current_drawdown = (self.peak_balance - new_balance) / self.peak_balance
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
    
    def get_current_drawdown(self) -> float:
        """獲取當前回撤百分比"""
        if self.peak_balance <= 0:
            return 0.0
        return (self.peak_balance - self.current_balance) / self.peak_balance
    
    def is_drawdown_exceeded(self, max_allowed: float) -> bool:
        """檢查是否超過最大回撤"""
        return self.get_current_drawdown() > max_allowed


class TradeCounter:
    """交易計數器"""
    
    def __init__(self):
        self.daily_trades = 0
        self.last_trade_date = datetime.now().date()
        self.total_trades = 0
        self.trade_log = []
    
    def can_trade(self, max_daily_trades: int) -> Tuple[bool, str]:
        """檢查是否可以交易"""
        today = datetime.now().date()
        
        # 重置每日計數
        if today != self.last_trade_date:
            self.daily_trades = 0
            self.last_trade_date = today
        
        if self.daily_trades >= max_daily_trades:
            return False, f"已達每日最大交易次數 ({max_daily_trades})"
        
        return True, "交易次數檢查通過"
    
    def record_trade(self, trade_info: Dict):
        """記錄交易"""
        today = datetime.now().date()
        
        if today != self.last_trade_date:
            self.daily_trades = 0
            self.last_trade_date = today
        
        self.daily_trades += 1
        self.total_trades += 1
        
        trade_record = {
            **trade_info,
            'timestamp': datetime.now().isoformat(),
            'daily_count': self.daily_trades
        }
        
        self.trade_log.append(trade_record)
        
        # 只保留最近 1000 筆記錄
        if len(self.trade_log) > 1000:
            self.trade_log.pop(0)


class RiskManager:
    """
    綜合風險管理系統
    
    功能：
    - 倉位大小計算
    - 回撤監控
    - 交易頻率控制
    - 置信度檢查
    - 時間窗口控制
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # 載入配置
        if config_path and Path(config_path).exists():
            self.parameters = self._load_config(config_path)
        else:
            self.parameters = RiskParameters()
        
        # 初始化組件
        self.position_calculator = PositionSizeCalculator()
        self.drawdown_tracker = DrawdownTracker()
        self.trade_counter = TradeCounter()
        
        # 統計數據
        self.performance_stats = {
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0
        }
        
        logger.info("風險管理系統已初始化")
    
    # 向後兼容屬性
    @property
    def max_risk_per_trade(self) -> float:
        return self.parameters.max_risk_per_trade
    
    @max_risk_per_trade.setter
    def max_risk_per_trade(self, value: float):
        self.parameters.max_risk_per_trade = value
    
    @property
    def max_trades_per_day(self) -> int:
        return self.parameters.max_trades_per_day
    
    @max_trades_per_day.setter
    def max_trades_per_day(self, value: int):
        self.parameters.max_trades_per_day = value
    
    @property
    def min_confidence(self) -> float:
        return self.parameters.min_confidence
    
    @min_confidence.setter
    def min_confidence(self, value: float):
        self.parameters.min_confidence = value
    
    def _load_config(self, config_path: str) -> RiskParameters:
        """載入風險配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return RiskParameters.from_dict(config_data)
        except Exception as e:
            logger.warning(f"載入風險配置失敗: {e}，使用默認配置")
            return RiskParameters()
    
    def save_config(self, config_path: str):
        """保存風險配置"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.parameters.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"風險配置已保存: {config_path}")
        except Exception as e:
            logger.error(f"保存風險配置失敗: {e}")
    
    def calculate_position_size(
        self, 
        account_balance: float, 
        entry_price: float, 
        stop_loss_price: Optional[float] = None,
        method: str = "fixed_risk"
    ) -> float:
        """計算倉位大小"""
        if not stop_loss_price:
            stop_loss_price = entry_price * (1 - self.parameters.default_stop_loss)
        
        if method == "kelly":
            # 使用凱利公式
            size = self.position_calculator.kelly_criterion(
                self.performance_stats['win_rate'],
                self.performance_stats['avg_win'],
                self.performance_stats['avg_loss']
            )
            return account_balance * size / entry_price
        
        elif method == "fixed_risk":
            # 固定風險法
            return self.position_calculator.fixed_risk(
                account_balance,
                self.parameters.max_risk_per_trade,
                entry_price,
                stop_loss_price
            )
        
        else:
            logger.warning(f"未知的倉位計算方法: {method}")
            return 0.0
    
    def check_can_trade(
        self, 
        signal_confidence: float,
        account_balance: float,
        current_hour: Optional[int] = None
    ) -> Tuple[bool, str]:
        """綜合交易檢查"""
        
        # 1. 置信度檢查
        if signal_confidence < self.parameters.min_confidence:
            return False, f"信號置信度不足 ({signal_confidence:.2%} < {self.parameters.min_confidence:.2%})"
        
        # 2. 交易次數檢查
        can_trade_count, count_reason = self.trade_counter.can_trade(self.parameters.max_trades_per_day)
        if not can_trade_count:
            return False, count_reason
        
        # 3. 回撤檢查
        if self.drawdown_tracker.is_drawdown_exceeded(self.parameters.max_drawdown):
            current_dd = self.drawdown_tracker.get_current_drawdown()
            return False, f"超過最大回撤限制 ({current_dd:.2%} > {self.parameters.max_drawdown:.2%})"
        
        # 4. 交易時間檢查
        current_hour = current_hour or datetime.now().hour
        if not (self.parameters.trading_hours_start <= current_hour <= self.parameters.trading_hours_end):
            return False, f"當前不在交易時間內 ({current_hour}:00)"
        
        # 5. 餘額檢查
        if account_balance <= 0:
            return False, "賬戶餘額不足"
        
        return True, "通過所有風險檢查"
    
    def update_balance(self, new_balance: float):
        """更新餘額"""
        self.drawdown_tracker.update(new_balance)
    
    def record_trade(self, trade_info: Dict):
        """記錄交易"""
        self.trade_counter.record_trade(trade_info)
        
        # 更新統計數據
        self._update_performance_stats()
    
    def _update_performance_stats(self):
        """更新表現統計"""
        trades = self.trade_counter.trade_log
        
        if len(trades) < 10:  # 需要至少10筆交易才計算
            return
        
        profits = [t.get('profit', 0) for t in trades if 'profit' in t]
        
        if profits:
            wins = [p for p in profits if p > 0]
            losses = [abs(p) for p in profits if p < 0]
            
            self.performance_stats['win_rate'] = len(wins) / len(profits)
            self.performance_stats['avg_win'] = sum(wins) / len(wins) if wins else 0
            self.performance_stats['avg_loss'] = sum(losses) / len(losses) if losses else 0
            
            if self.performance_stats['avg_loss'] > 0:
                self.performance_stats['profit_factor'] = (
                    self.performance_stats['avg_win'] / self.performance_stats['avg_loss']
                )
    
    def get_risk_statistics(self) -> Dict:
        """獲取風險統計信息"""
        return {
            'parameters': self.parameters.to_dict(),
            'current_drawdown': f"{self.drawdown_tracker.get_current_drawdown():.2%}",
            'max_drawdown': f"{self.drawdown_tracker.max_drawdown:.2%}",
            'daily_trades': self.trade_counter.daily_trades,
            'total_trades': self.trade_counter.total_trades,
            'performance_stats': self.performance_stats,
            'peak_balance': self.drawdown_tracker.peak_balance,
            'current_balance': self.drawdown_tracker.current_balance
        }
    
    def get_statistics(self) -> Dict:
        """獲取統計信息（向後兼容方法）"""
        return self.get_risk_statistics()
    
    def reset_daily_counters(self):
        """重置每日計數器（用於測試或手動重置）"""
        self.trade_counter.daily_trades = 0
        self.trade_counter.last_trade_date = datetime.now().date()
        logger.info("每日交易計數器已重置")
    
    def update_risk_parameters(self, **kwargs):
        """動態更新風險參數"""
        for key, value in kwargs.items():
            if hasattr(self.parameters, key):
                old_value = getattr(self.parameters, key)
                setattr(self.parameters, key, value)
                logger.info(f"風險參數已更新: {key} = {old_value} -> {value}")
            else:
                logger.warning(f"未知的風險參數: {key}")