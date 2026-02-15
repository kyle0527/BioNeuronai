#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真正的策略回測驗證系統
=======================

功能:
1. 載入真實歷史數據 (ETHUSDT 1h)
2. 對每個策略進行逐 bar 回測
3. 產生交易信號並模擬執行
4. 計算績效指標 (Sharpe, Drawdown, Win Rate, Return)
5. 比較所有策略表現

Author: BioNeuronAI
Date: 2026-02-15
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import json
import traceback
import zipfile
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# 匯入策略
from src.bioneuronai.strategies.trend_following import TrendFollowingStrategy
from src.bioneuronai.strategies.swing_trading import SwingTradingStrategy
from src.bioneuronai.strategies.mean_reversion import MeanReversionStrategy
from src.bioneuronai.strategies.breakout_trading import BreakoutTradingStrategy
from src.bioneuronai.strategies.base_strategy import MarketCondition, SignalStrength


@dataclass
class Trade:
    """單筆交易記錄"""
    entry_time: datetime
    entry_price: float
    direction: str  # 'long' or 'short'
    position_size: float
    stop_loss: float
    take_profit: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    exit_reason: str = ""


@dataclass
class BacktestResult:
    """回測結果"""
    strategy_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_return: float = 0.0
    total_return_percent: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_holding_time: float = 0.0  # bars
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    signals: List[Dict] = field(default_factory=list)


class StrategyBacktester:
    """策略回測器"""
    
    def __init__(
        self, 
        initial_capital: float = 10000.0,
        commission: float = 0.001,  # 0.1% 手續費
        slippage: float = 0.0005,   # 0.05% 滑價
        risk_per_trade: float = 0.02,  # 每筆交易風險 2%
        min_bars_for_analysis: int = 200  # 最少需要的 bars
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.risk_per_trade = risk_per_trade
        self.min_bars_for_analysis = min_bars_for_analysis
        
    def run_backtest(
        self, 
        strategy, 
        ohlcv_data: np.ndarray,
        strategy_name: str
    ) -> BacktestResult:
        """運行回測
        
        Args:
            strategy: 策略實例
            ohlcv_data: OHLCV 數據 numpy array [timestamp, open, high, low, close, volume]
            strategy_name: 策略名稱
            
        Returns:
            BacktestResult: 回測結果
        """
        result = BacktestResult(strategy_name=strategy_name)
        
        # 初始化
        capital = self.initial_capital
        position = None  # 當前持倉
        equity_curve = [capital]
        peak_equity = capital
        max_drawdown = 0.0
        
        trades: List[Trade] = []
        signals: List[Dict] = []
        returns: List[float] = []
        
        n_bars = len(ohlcv_data)
        print(f"\n{'='*60}")
        print(f"回測策略: {strategy_name}")
        print(f"數據筆數: {n_bars}")
        print(f"{'='*60}")
        
        # 逐 bar 回測
        for i in range(self.min_bars_for_analysis, n_bars):
            # 取得當前 bar 之前的歷史數據
            historical_data = ohlcv_data[:i+1]
            current_bar = ohlcv_data[i]
            
            timestamp = datetime.fromtimestamp(current_bar[0] / 1000)
            current_price = current_bar[4]  # close
            high = current_bar[2]
            low = current_bar[3]
            
            # 檢查是否有持倉需要平倉
            if position is not None:
                exit_signal = self._check_exit_conditions(
                    position, current_price, high, low, timestamp
                )
                if exit_signal:
                    # 平倉
                    position.exit_time = timestamp
                    position.exit_price = exit_signal['exit_price']
                    position.exit_reason = exit_signal['reason']
                    
                    # 計算 P&L
                    if position.direction == 'long':
                        pnl = (position.exit_price - position.entry_price) * position.position_size
                    else:
                        pnl = (position.entry_price - position.exit_price) * position.position_size
                    
                    # 扣除手續費
                    pnl -= position.entry_price * position.position_size * self.commission
                    pnl -= position.exit_price * position.position_size * self.commission
                    
                    position.pnl = pnl
                    position.pnl_percent = pnl / (position.entry_price * position.position_size) * 100
                    
                    capital += pnl
                    trades.append(position)
                    
                    signals.append({
                        'timestamp': timestamp.isoformat(),
                        'type': 'exit',
                        'direction': position.direction,
                        'price': position.exit_price,
                        'reason': position.exit_reason,
                        'pnl': position.pnl
                    })
                    
                    position = None
            
            # 如果沒有持倉，檢查進場信號
            if position is None:
                try:
                    # 分析市場
                    market_analysis = strategy.analyze_market(historical_data)
                    
                    # 添加 symbol 字段（策略需要）
                    market_analysis['symbol'] = 'ETHUSDT'
                    
                    # 評估進場條件
                    trade_setup = strategy.evaluate_entry_conditions(
                        market_analysis, historical_data
                    )
                    
                    if trade_setup is not None:
                        # 產生進場信號
                        direction = trade_setup.direction
                        
                        # 計算進場價格（考慮滑價）
                        entry_price = current_price
                        if direction == 'long':
                            entry_price *= (1 + self.slippage)
                        else:
                            entry_price *= (1 - self.slippage)
                        
                        # 計算倉位大小（基於風險管理）
                        risk_amount = capital * self.risk_per_trade
                        stop_distance = abs(entry_price - trade_setup.stop_loss)
                        if stop_distance > 0:
                            position_size = risk_amount / stop_distance
                        else:
                            position_size = capital * 0.1 / entry_price  # 默認 10% 資金
                        
                        # 限制最大倉位為資本的 50%
                        max_position_value = capital * 0.5
                        position_size = min(position_size, max_position_value / entry_price)
                        
                        # 創建交易
                        position = Trade(
                            entry_time=timestamp,
                            entry_price=entry_price,
                            direction=direction,
                            position_size=position_size,
                            stop_loss=trade_setup.stop_loss,
                            take_profit=trade_setup.take_profit_1 if hasattr(trade_setup, 'take_profit_1') else trade_setup.stop_loss * 2 - entry_price
                        )
                        
                        signals.append({
                            'timestamp': timestamp.isoformat(),
                            'type': 'entry',
                            'direction': direction,
                            'price': entry_price,
                            'stop_loss': trade_setup.stop_loss,
                            'signal_strength': str(trade_setup.signal_strength) if hasattr(trade_setup, 'signal_strength') else 'UNKNOWN'
                        })
                        
                except Exception as e:
                    # 策略可能拋出異常，跳過這個 bar
                    pass
            
            # 更新權益曲線
            current_equity = capital
            if position is not None:
                # 計算未實現損益
                if position.direction == 'long':
                    unrealized_pnl = (current_price - position.entry_price) * position.position_size
                else:
                    unrealized_pnl = (position.entry_price - current_price) * position.position_size
                current_equity += unrealized_pnl
            
            equity_curve.append(current_equity)
            
            # 計算回報率
            if len(equity_curve) > 1:
                daily_return = (equity_curve[-1] - equity_curve[-2]) / equity_curve[-2]
                returns.append(daily_return)
            
            # 更新最大回撤
            if current_equity > peak_equity:
                peak_equity = current_equity
            drawdown = (peak_equity - current_equity) / peak_equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 如果還有持倉，強制平倉
        if position is not None:
            last_bar = ohlcv_data[-1]
            position.exit_time = datetime.fromtimestamp(last_bar[0] / 1000)
            position.exit_price = last_bar[4]
            position.exit_reason = "end_of_data"
            
            if position.direction == 'long':
                pnl = (position.exit_price - position.entry_price) * position.position_size
            else:
                pnl = (position.entry_price - position.exit_price) * position.position_size
            
            pnl -= position.entry_price * position.position_size * self.commission
            pnl -= position.exit_price * position.position_size * self.commission
            
            position.pnl = pnl
            position.pnl_percent = pnl / (position.entry_price * position.position_size) * 100
            capital += pnl
            trades.append(position)
        
        # 計算統計指標
        result = self._calculate_statistics(
            strategy_name, trades, equity_curve, returns, 
            max_drawdown, signals, capital
        )
        
        return result
    
    def _check_exit_conditions(
        self, 
        position: Trade, 
        current_price: float,
        high: float,
        low: float,
        timestamp: datetime
    ) -> Optional[Dict]:
        """檢查平倉條件"""
        
        if position.direction == 'long':
            # 多頭止損
            if low <= position.stop_loss:
                return {
                    'exit_price': position.stop_loss * (1 - self.slippage),
                    'reason': 'stop_loss'
                }
            # 多頭止盈
            if high >= position.take_profit:
                return {
                    'exit_price': position.take_profit * (1 - self.slippage),
                    'reason': 'take_profit'
                }
        else:
            # 空頭止損
            if high >= position.stop_loss:
                return {
                    'exit_price': position.stop_loss * (1 + self.slippage),
                    'reason': 'stop_loss'
                }
            # 空頭止盈
            if low <= position.take_profit:
                return {
                    'exit_price': position.take_profit * (1 + self.slippage),
                    'reason': 'take_profit'
                }
        
        return None
    
    def _calculate_statistics(
        self,
        strategy_name: str,
        trades: List[Trade],
        equity_curve: List[float],
        returns: List[float],
        max_drawdown: float,
        signals: List[Dict],
        final_capital: float
    ) -> BacktestResult:
        """計算回測統計指標"""
        
        result = BacktestResult(strategy_name=strategy_name)
        result.trades = trades
        result.equity_curve = equity_curve
        result.signals = signals
        
        # 交易統計
        result.total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        
        result.winning_trades = len(winning_trades)
        result.losing_trades = len(losing_trades)
        result.win_rate = result.winning_trades / result.total_trades * 100 if result.total_trades > 0 else 0
        
        # 回報統計
        result.total_return = final_capital - self.initial_capital
        result.total_return_percent = result.total_return / self.initial_capital * 100
        
        # 最大回撤
        result.max_drawdown_percent = max_drawdown * 100
        result.max_drawdown = self.initial_capital * max_drawdown
        
        # 平均獲利/虧損
        if winning_trades:
            result.avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades)
            result.largest_win = max(t.pnl for t in winning_trades)
        if losing_trades:
            result.avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades)
            result.largest_loss = min(t.pnl for t in losing_trades)
        
        # 獲利因子
        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 1
        result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # 計算 Sharpe Ratio (假設無風險利率為 0)
        if returns and len(returns) > 1:
            returns_array = np.array(returns)
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            # 年化 (假設 1h K線，1年約 8760 小時)
            result.sharpe_ratio = (mean_return / std_return) * np.sqrt(8760) if std_return > 0 else 0
            
            # Sortino Ratio (只考慮下行風險)
            downside_returns = returns_array[returns_array < 0]
            if len(downside_returns) > 0:
                downside_std = np.std(downside_returns)
                result.sortino_ratio = (mean_return / downside_std) * np.sqrt(8760) if downside_std > 0 else 0
        
        # 平均持倉時間
        if trades:
            holding_times = []
            for t in trades:
                if t.exit_time and t.entry_time:
                    hours = (t.exit_time - t.entry_time).total_seconds() / 3600
                    holding_times.append(hours)
            if holding_times:
                result.avg_holding_time = sum(holding_times) / len(holding_times)
        
        return result


def load_training_data(data_path: str = "training_data") -> np.ndarray:
    """載入訓練數據"""
    data_root = Path(data_path) / "data_downloads" / "binance_historical" / "data" / "futures" / "um" / "daily" / "klines" / "ETHUSDT" / "1h"
    
    if not data_root.exists():
        raise FileNotFoundError(f"數據目錄不存在: {data_root}")
    
    print(f"掃描數據目錄: {data_root}")
    
    all_data = []
    
    for date_range_dir in data_root.iterdir():
        if not date_range_dir.is_dir():
            continue
        
        print(f"  掃描: {date_range_dir.name}")
        
        zip_files = sorted(date_range_dir.glob("ETHUSDT-1h-*.zip"))
        
        for zip_file in zip_files:
            try:
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    csv_name = zip_file.stem + '.csv'
                    with zf.open(csv_name) as f:
                        df = pd.read_csv(f)
                
                # 標準化列名
                df = df.rename(columns={'open_time': 'timestamp'})
                
                # 轉換時間戳
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # 只保留需要的列
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
                # 轉換為數值類型
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df = df.dropna()
                
                if not df.empty:
                    all_data.append(df)
                    
            except Exception as e:
                print(f"    ✗ 加載失敗: {zip_file.name} - {e}")
    
    if not all_data:
        raise ValueError("未找到任何數據")
    
    # 合併所有數據
    df = pd.concat(all_data, ignore_index=True)
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"載入數據: {len(df)} 筆")
    print(f"時間範圍: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
    print(f"價格範圍: ${df['close'].min():.2f} ~ ${df['close'].max():.2f}")
    
    # 轉換為 numpy array
    ohlcv = np.zeros((len(df), 6))
    ohlcv[:, 0] = df['timestamp'].astype(np.int64) // 10**6  # timestamp (ms)
    ohlcv[:, 1] = df['open'].values
    ohlcv[:, 2] = df['high'].values
    ohlcv[:, 3] = df['low'].values
    ohlcv[:, 4] = df['close'].values
    ohlcv[:, 5] = df['volume'].values
    
    return ohlcv


def print_comparison_table(results: List[BacktestResult]):
    """打印策略比較表"""
    print("\n")
    print("=" * 100)
    print("策略績效比較表")
    print("=" * 100)
    
    headers = ["策略名稱", "交易次數", "勝率%", "總回報%", "最大回撤%", "Sharpe", "Sortino", "獲利因子"]
    row_format = "{:<20} {:>10} {:>10} {:>12} {:>12} {:>10} {:>10} {:>10}"
    
    print(row_format.format(*headers))
    print("-" * 100)
    
    for r in results:
        print(row_format.format(
            r.strategy_name,
            r.total_trades,
            f"{r.win_rate:.1f}",
            f"{r.total_return_percent:.2f}",
            f"{r.max_drawdown_percent:.2f}",
            f"{r.sharpe_ratio:.3f}",
            f"{r.sortino_ratio:.3f}",
            f"{r.profit_factor:.2f}"
        ))
    
    print("=" * 100)
    
    # 找出最佳策略
    if results:
        best_sharpe = max(results, key=lambda x: x.sharpe_ratio)
        best_return = max(results, key=lambda x: x.total_return_percent)
        best_winrate = max(results, key=lambda x: x.win_rate)
        
        print("\n最佳策略:")
        print(f"  • 最高 Sharpe Ratio: {best_sharpe.strategy_name} ({best_sharpe.sharpe_ratio:.3f})")
        print(f"  • 最高總回報: {best_return.strategy_name} ({best_return.total_return_percent:.2f}%)")
        print(f"  • 最高勝率: {best_winrate.strategy_name} ({best_winrate.win_rate:.1f}%)")


def print_trade_details(result: BacktestResult, max_trades: int = 10):
    """打印交易詳情"""
    print(f"\n{result.strategy_name} 交易詳情 (最近 {max_trades} 筆):")
    print("-" * 80)
    
    for trade in result.trades[-max_trades:]:
        status = "✅" if trade.pnl > 0 else "❌"
        exit_price_str = f"${trade.exit_price:.2f}" if trade.exit_price else "N/A"
        print(f"  {status} {trade.entry_time.strftime('%m/%d %H:%M')} "
              f"{trade.direction.upper():5s} @ ${trade.entry_price:.2f} "
              f"→ {exit_price_str} "
              f"P&L: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%) "
              f"[{trade.exit_reason}]")


def save_results(results: List[BacktestResult], output_dir: str = "validation_results"):
    """保存回測結果"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存摘要報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"BACKTEST_REPORT_{timestamp}.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 策略回測驗證報告\n\n")
        f.write(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 策略績效比較\n\n")
        f.write("| 策略 | 交易次數 | 勝率% | 總回報% | 最大回撤% | Sharpe | Profit Factor |\n")
        f.write("|------|---------|-------|---------|-----------|--------|---------------|\n")
        
        for r in results:
            f.write(f"| {r.strategy_name} | {r.total_trades} | {r.win_rate:.1f} | "
                   f"{r.total_return_percent:.2f} | {r.max_drawdown_percent:.2f} | "
                   f"{r.sharpe_ratio:.3f} | {r.profit_factor:.2f} |\n")
        
        f.write("\n## 詳細分析\n\n")
        
        for r in results:
            f.write(f"### {r.strategy_name}\n\n")
            f.write(f"- **交易次數**: {r.total_trades}\n")
            f.write(f"- **勝率**: {r.win_rate:.1f}%\n")
            f.write(f"- **總回報**: ${r.total_return:.2f} ({r.total_return_percent:.2f}%)\n")
            f.write(f"- **最大回撤**: ${r.max_drawdown:.2f} ({r.max_drawdown_percent:.2f}%)\n")
            f.write(f"- **Sharpe Ratio**: {r.sharpe_ratio:.3f}\n")
            f.write(f"- **Sortino Ratio**: {r.sortino_ratio:.3f}\n")
            f.write(f"- **獲利因子**: {r.profit_factor:.2f}\n")
            f.write(f"- **平均獲利**: ${r.avg_win:.2f}\n")
            f.write(f"- **平均虧損**: ${r.avg_loss:.2f}\n")
            f.write(f"- **最大單筆獲利**: ${r.largest_win:.2f}\n")
            f.write(f"- **最大單筆虧損**: ${r.largest_loss:.2f}\n")
            f.write(f"- **平均持倉時間**: {r.avg_holding_time:.1f} 小時\n\n")
    
    print(f"\n報告已保存至: {report_path}")
    
    # 保存 JSON 數據
    json_path = os.path.join(output_dir, f"backtest_data_{timestamp}.json")
    
    json_data = {
        'timestamp': timestamp,
        'strategies': []
    }
    
    for r in results:
        strategy_data = {
            'name': r.strategy_name,
            'metrics': {
                'total_trades': r.total_trades,
                'winning_trades': r.winning_trades,
                'losing_trades': r.losing_trades,
                'win_rate': r.win_rate,
                'total_return': r.total_return,
                'total_return_percent': r.total_return_percent,
                'max_drawdown': r.max_drawdown,
                'max_drawdown_percent': r.max_drawdown_percent,
                'sharpe_ratio': r.sharpe_ratio,
                'sortino_ratio': r.sortino_ratio,
                'profit_factor': r.profit_factor,
            },
            'signals_count': len(r.signals)
        }
        json_data['strategies'].append(strategy_data)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"數據已保存至: {json_path}")


def main():
    """主函數"""
    print("=" * 60)
    print("BioNeuronAI 策略回測驗證系統")
    print("=" * 60)
    
    try:
        # 1. 載入數據
        print("\n[1/4] 載入訓練數據...")
        ohlcv_data = load_training_data("training_data")
        
        # 2. 初始化策略
        print("\n[2/4] 初始化策略...")
        strategies = {
            'TrendFollowing': TrendFollowingStrategy(),
            'SwingTrading': SwingTradingStrategy(),
            'MeanReversion': MeanReversionStrategy(),
            'BreakoutTrading': BreakoutTradingStrategy(),
        }
        
        # 3. 運行回測
        print("\n[3/4] 運行策略回測...")
        backtester = StrategyBacktester(
            initial_capital=10000,
            commission=0.001,  # Binance 0.1%
            slippage=0.0005,
            risk_per_trade=0.02
        )
        
        results = []
        for name, strategy in strategies.items():
            try:
                result = backtester.run_backtest(strategy, ohlcv_data, name)
                results.append(result)
                
                print(f"\n{name} 回測完成:")
                print(f"  交易次數: {result.total_trades}")
                print(f"  勝率: {result.win_rate:.1f}%")
                print(f"  總回報: {result.total_return_percent:.2f}%")
                print(f"  最大回撤: {result.max_drawdown_percent:.2f}%")
                print(f"  Sharpe: {result.sharpe_ratio:.3f}")
                
            except Exception as e:
                print(f"\n{name} 回測失敗: {str(e)}")
                traceback.print_exc()
        
        # 4. 輸出結果
        print("\n[4/4] 生成報告...")
        
        if results:
            print_comparison_table(results)
            
            # 打印每個策略的交易詳情
            for result in results:
                if result.total_trades > 0:
                    print_trade_details(result, max_trades=5)
            
            # 保存結果
            save_results(results)
        else:
            print("\n⚠️ 沒有策略成功完成回測")
        
        print("\n" + "=" * 60)
        print("回測驗證完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n錯誤: {str(e)}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
