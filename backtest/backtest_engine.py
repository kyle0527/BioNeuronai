"""
Backtest Engine - 回測引擎主類
==============================

整合所有組件，提供完整的回測功能

主要功能：
1. 與 TradingEngine 無縫對接
2. 自動策略評估
3. 詳細回測報告
4. 性能分析和可視化
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
import json

from .mock_connector import MockBinanceConnector
from .data_stream import HistoricalDataStream, KlineBar
from .virtual_account import VirtualAccount

logger = logging.getLogger(__name__)

# 檔案常量
DEFAULT_DATA_DIR = "data_downloads/binance_historical"


@dataclass
class BacktestConfig:
    """回測配置"""
    # 數據設置
    data_dir: str = DEFAULT_DATA_DIR
    symbol: str = "BTCUSDT"
    interval: str = "1m"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # 帳戶設置
    initial_balance: float = 10000.0
    leverage: int = 1
    maker_fee: float = 0.0002
    taker_fee: float = 0.0004
    slippage_rate: float = 0.0001
    
    # 回測設置
    speed_multiplier: float = 0.0  # 無延遲模式
    warmup_bars: int = 100  # 預熱期 K線數量
    
    # 風險設置
    max_position_size: float = 1.0
    max_daily_loss: float = 0.05  # 5%
    
    def to_dict(self) -> Dict:
        return {
            'data_dir': self.data_dir,
            'symbol': self.symbol,
            'interval': self.interval,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_balance': self.initial_balance,
            'leverage': self.leverage,
            'maker_fee': self.maker_fee,
            'taker_fee': self.taker_fee,
            'slippage_rate': self.slippage_rate,
            'warmup_bars': self.warmup_bars,
        }


@dataclass
class BacktestResult:
    """回測結果"""
    config: BacktestConfig
    stats: Dict[str, Any]
    equity_curve: List[float] = field(default_factory=list)
    trades: List[Dict] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'config': self.config.to_dict(),
            'stats': self.stats,
            'equity_curve': self.equity_curve,
            'trades': self.trades,
            'drawdown_curve': self.drawdown_curve,
            'timestamps': [t.isoformat() for t in self.timestamps],
        }
    
    def save(self, path: str):
        """保存結果到 JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"💾 回測結果已保存: {path}")


class BacktestEngine:
    """
    回測引擎
    
    提供完整的回測框架，讓 TradingEngine 在歷史數據上運行
    無需修改任何交易邏輯代碼
    
    使用方式：
    
    === 方法 1: 快速回測 ===
    
    engine = BacktestEngine(
        data_dir="data_downloads/binance_historical",
        symbol="BTCUSDT",
        start_date="2025-01-01",
        end_date="2025-06-30"
    )
    
    # 定義策略邏輯
    def my_strategy(bar, connector):
        if bar.close > bar.open:
            connector.place_order("BTCUSDT", "BUY", "MARKET", 0.01)
    
    result = engine.run(my_strategy)
    
    === 方法 2: 與 TradingEngine 整合 ===
    
    from bioneuronai.core import TradingEngine
    from backtest import MockBinanceConnector
    
    # 創建 Mock 連接器
    mock = MockBinanceConnector(...)
    
    # 創建 TradingEngine，但替換連接器
    trading_engine = TradingEngine()
    trading_engine.connector = mock
    
    # 現在 TradingEngine 會在歷史數據上運行
    # 它完全不知道這是回測！
    """
    
    def __init__(
        self,
        config: Optional[BacktestConfig] = None,
        # 快捷參數
        data_dir: str = DEFAULT_DATA_DIR,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_balance: float = 10000.0,
        leverage: int = 1,
    ):
        """
        初始化回測引擎
        
        Args:
            config: 完整配置對象
            data_dir: 數據目錄
            symbol: 交易對
            interval: K線間隔
            start_date: 開始日期
            end_date: 結束日期
            initial_balance: 初始餘額
            leverage: 槓桿
        """
        if config:
            self.config = config
        else:
            self.config = BacktestConfig(
                data_dir=data_dir,
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                initial_balance=initial_balance,
                leverage=leverage,
            )
        
        # 創建 Mock 連接器
        self.connector = MockBinanceConnector(
            data_dir=self.config.data_dir,
            symbol=self.config.symbol,
            interval=self.config.interval,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_balance=self.config.initial_balance,
            leverage=self.config.leverage,
            maker_fee=self.config.maker_fee,
            taker_fee=self.config.taker_fee,
            slippage_rate=self.config.slippage_rate,
        )
        
        # 回測記錄
        self._equity_curve: List[float] = []
        self._drawdown_curve: List[float] = []
        self._timestamps: List[datetime] = []
        self._bar_count = 0
        self._warmup_complete = False
        
        logger.info("回測引擎初始化完成")
    
    def run(
        self,
        strategy: Callable[[KlineBar, MockBinanceConnector], None],
        progress_interval: int = 1000,
    ) -> BacktestResult:
        """
        運行回測
        
        Args:
            strategy: 策略函數，接收 (bar, connector)
            progress_interval: 進度報告間隔 (每 N 根 K線)
            
        Returns:
            BacktestResult: 回測結果
        """
        logger.info("=" * 60)
        logger.info("🚀 開始回測")
        logger.info("=" * 60)
        logger.info(f"交易對: {self.config.symbol}")
        logger.info(f"時間區間: {self.config.start_date} ~ {self.config.end_date}")
        logger.info(f"初始餘額: {self.config.initial_balance:,.2f} USDT")
        logger.info(f"預熱期: {self.config.warmup_bars} 根 K線")
        logger.info("=" * 60)
        
        self._bar_count = 0
        self._warmup_complete = False
        peak_equity = self.config.initial_balance
        
        for bar in self.connector.data_stream.stream_bars():
            self._bar_count += 1
            
            # 更新帳戶價格
            self.connector.account.update_price(bar.symbol, bar.close)
            self.connector._current_bar = bar
            
            # 預熱期
            if self._bar_count < self.config.warmup_bars:
                continue
            elif not self._warmup_complete:
                self._warmup_complete = True
                logger.info(f"✅ 預熱完成，開始交易 ({self._bar_count} 根)")
            
            # 執行策略
            try:
                strategy(bar, self.connector)
            except Exception as e:
                logger.error(f"策略執行錯誤: {e}")
            
            # 記錄權益曲線
            equity = self.connector.account.get_total_equity()
            self._equity_curve.append(equity)
            self._timestamps.append(datetime.fromtimestamp(bar.close_time / 1000))
            
            # 計算回撤
            if equity > peak_equity:
                peak_equity = equity
            drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0
            self._drawdown_curve.append(drawdown)
            
            # 進度報告
            if self._bar_count % progress_interval == 0:
                current, total, pct = self.connector.data_stream.get_progress()
                logger.info(
                    f"📊 進度: {pct:.1f}% ({current:,}/{total:,}) | "
                    f"權益: {equity:,.2f} | "
                    f"回撤: {drawdown*100:.2f}%"
                )
        
        # 獲取統計
        stats = self.connector.account.get_stats()
        stats['total_bars'] = self._bar_count
        stats['effective_bars'] = self._bar_count - self.config.warmup_bars
        
        # 計算額外統計
        stats.update(self._calculate_advanced_stats())
        
        # 創建結果
        result = BacktestResult(
            config=self.config,
            stats=stats,
            equity_curve=self._equity_curve,
            trades=[t.to_dict() for t in self.connector.account.trade_history],
            drawdown_curve=self._drawdown_curve,
            timestamps=self._timestamps,
        )
        
        # 打印摘要
        self._print_summary(result)
        
        return result
    
    def _calculate_advanced_stats(self) -> Dict[str, Any]:
        """計算進階統計指標"""
        if not self._equity_curve:
            return {}
        
        import numpy as np
        
        equity = np.array(self._equity_curve)
        returns = np.diff(equity) / equity[:-1] if len(equity) > 1 else np.array([0])
        
        # 夏普比率 (假設無風險利率為 0)
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 * 24 * 60) if np.std(returns) > 0 else 0
        
        # 索提諾比率
        downside_returns = returns[returns < 0]
        sortino = np.mean(returns) / np.std(downside_returns) * np.sqrt(252 * 24 * 60) if len(downside_returns) > 0 and np.std(downside_returns) > 0 else 0
        
        # 卡爾瑪比率
        max_dd = max(self._drawdown_curve) if self._drawdown_curve else 0
        total_return = (equity[-1] - equity[0]) / equity[0] if equity[0] > 0 else 0
        calmar = total_return / max_dd if max_dd > 0 else 0
        
        # 最大連續虧損
        max_consecutive_losses = 0
        current_losses = 0
        for trade in self.connector.account.trade_history:
            if trade.realized_pnl < 0:
                current_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
            else:
                current_losses = 0
        
        # 平均持倉時間 (簡化計算)
        trades = self.connector.account.trade_history
        avg_trade_duration = len(self._equity_curve) / max(len(trades), 1) if trades else 0
        
        return {
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'calmar_ratio': round(calmar, 2),
            'max_consecutive_losses': max_consecutive_losses,
            'avg_bars_per_trade': round(avg_trade_duration, 1),
            'profit_factor': self._calculate_profit_factor(),
        }
    
    def _calculate_profit_factor(self) -> float:
        """計算獲利因子"""
        gross_profit = 0
        gross_loss = 0
        
        for trade in self.connector.account.trade_history:
            if trade.realized_pnl > 0:
                gross_profit += trade.realized_pnl
            else:
                gross_loss += abs(trade.realized_pnl)
        
        return round(gross_profit / gross_loss, 2) if gross_loss > 0 else float('inf')
    
    def _print_summary(self, result: BacktestResult):
        """打印回測摘要"""
        stats = result.stats
        
        print("\n" + "=" * 70)
        print("📊 回測結果摘要")
        print("=" * 70)
        
        print("\n📈 績效指標")
        print("-" * 70)
        print(f"{'初始餘額:':<20} {stats['initial_balance']:>15,.2f} USDT")
        print(f"{'最終餘額:':<20} {stats['current_balance']:>15,.2f} USDT")
        print(f"{'總權益:':<20} {stats['total_equity']:>15,.2f} USDT")
        print(f"{'總收益率:':<20} {stats['total_return']:>15.2f}%")
        print(f"{'實現盈虧:':<20} {stats['total_realized_pnl']:>+15,.2f} USDT")
        
        print("\n📉 風險指標")
        print("-" * 70)
        print(f"{'最大回撤:':<20} {stats['max_drawdown']:>15.2f}%")
        print(f"{'夏普比率:':<20} {stats.get('sharpe_ratio', 0):>15.2f}")
        print(f"{'索提諾比率:':<20} {stats.get('sortino_ratio', 0):>15.2f}")
        print(f"{'卡爾瑪比率:':<20} {stats.get('calmar_ratio', 0):>15.2f}")
        
        print("\n🎯 交易統計")
        print("-" * 70)
        print(f"{'總交易次數:':<20} {stats['total_trades']:>15}")
        print(f"{'勝率:':<20} {stats['win_rate']:>15.1f}%")
        print(f"{'盈利交易:':<20} {stats['winning_trades']:>15}")
        print(f"{'虧損交易:':<20} {stats['losing_trades']:>15}")
        print(f"{'獲利因子:':<20} {stats.get('profit_factor', 0):>15.2f}")
        print(f"{'最大連續虧損:':<20} {stats.get('max_consecutive_losses', 0):>15}")
        
        print("\n💰 成本")
        print("-" * 70)
        print(f"{'總手續費:':<20} {stats['total_commission']:>15,.2f} USDT")
        
        print("\n📅 數據統計")
        print("-" * 70)
        print(f"{'總 K線數:':<20} {stats['total_bars']:>15,}")
        print(f"{'有效 K線數:':<20} {stats['effective_bars']:>15,}")
        print(f"{'平均每筆交易 K線:':<20} {stats.get('avg_bars_per_trade', 0):>15.1f}")
        
        print("=" * 70 + "\n")
    
    def get_connector(self) -> MockBinanceConnector:
        """獲取 Mock 連接器 - 用於替換 TradingEngine 的連接器"""
        return self.connector
    
    def reset(self):
        """重置回測引擎"""
        self.connector.account.reset()
        self.connector.data_stream.reset()
        self._equity_curve.clear()
        self._drawdown_curve.clear()
        self._timestamps.clear()
        self._bar_count = 0
        self._warmup_complete = False
        logger.info("🔄 回測引擎已重置")


# ============================================================
# 便利函數
# ============================================================

def quick_backtest(
    strategy: Callable[[KlineBar, MockBinanceConnector], None],
    symbol: str = "BTCUSDT",
    interval: str = "1m",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    initial_balance: float = 10000.0,
    data_dir: str = DEFAULT_DATA_DIR,
) -> BacktestResult:
    """
    快速回測函數
    
    Example:
        def my_strategy(bar, connector):
            if bar.close > bar.open * 1.001:
                connector.place_order(bar.symbol, "BUY", "MARKET", 0.01)
        
        result = quick_backtest(
            my_strategy,
            symbol="ETHUSDT",
            start_date="2025-01-01",
            end_date="2025-03-31"
        )
    """
    engine = BacktestEngine(
        data_dir=data_dir,
        symbol=symbol,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
    )
    
    return engine.run(strategy)


def create_mock_connector(
    symbol: str = "BTCUSDT",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    initial_balance: float = 10000.0,
    data_dir: str = DEFAULT_DATA_DIR,
) -> MockBinanceConnector:
    """
    快速創建 Mock 連接器
    
    用於替換 TradingEngine 的連接器
    
    Example:
        from backtest import create_mock_connector
        from bioneuronai.core import TradingEngine
        
        # 創建 mock 連接器
        mock = create_mock_connector(
            symbol="BTCUSDT",
            start_date="2025-01-01"
        )
        
        # 創建 TradingEngine
        engine = TradingEngine()
        
        # 替換連接器 - TradingEngine 完全不知道這是回測!
        engine.connector = mock
    """
    return MockBinanceConnector(
        data_dir=data_dir,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
    )
