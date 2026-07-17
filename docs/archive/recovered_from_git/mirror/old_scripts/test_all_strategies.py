"""
測試所有策略 - 用 Mock Connector + next_tick()
"""
import sys
sys.path.insert(0, 'src')

import logging
logging.disable(logging.CRITICAL)

from bioneuronai.backtest import MockBinanceConnector
from bioneuronai.strategies import (
    TrendFollowingStrategy,
    SwingTradingStrategy, 
    MeanReversionStrategy,
    BreakoutTradingStrategy,
)

def test_strategy(strategy_class, strategy_name):
    """測試單一策略"""
    print(f"\n{'='*60}")
    print(f"Strategy: {strategy_name}")
    print('='*60)
    
    # 創建 Mock 連接器
    mock = MockBinanceConnector(
        symbol="ETHUSDT",
        interval="15m",
        start_date="2026-01-10",
        end_date="2026-01-15",
        initial_balance=10000,
    )
    
    # 創建策略
    strategy = strategy_class()
    
    # 統計
    signals = {"long": 0, "short": 0, "neutral": 0, "other": 0}
    total_bars = 0
    sample_signals = []
    
    # 推進時間並測試
    while mock.next_tick():
        total_bars += 1
        bar = mock._current_bar
        
        # 獲取歷史數據
        klines = mock.data_stream.get_klines_until_now(100)
        if len(klines) < 30:
            continue
            
        # 策略分析
        try:
            signal = strategy.analyze(
                symbol=bar.symbol,
                klines=klines,
                current_price=bar.close
            )
            
            # 統計信號
            sig_type = signal.signal_type.value.lower() if hasattr(signal, 'signal_type') else str(signal).lower()
            
            if "long" in sig_type:
                signals["long"] += 1
                if len(sample_signals) < 3:
                    sample_signals.append(f"Bar{total_bars}: ${bar.close:.2f} -> LONG ({signal.confidence:.1%})")
            elif "short" in sig_type:
                signals["short"] += 1
                if len(sample_signals) < 3:
                    sample_signals.append(f"Bar{total_bars}: ${bar.close:.2f} -> SHORT ({signal.confidence:.1%})")
            elif "neutral" in sig_type or "hold" in sig_type:
                signals["neutral"] += 1
            else:
                signals["other"] += 1
                
        except Exception as e:
            pass
    
    # 輸出結果
    print(f"Total Bars: {total_bars}")
    print(f"Signals:")
    print(f"  LONG:    {signals['long']:4d} ({signals['long']/total_bars*100:.1f}%)")
    print(f"  SHORT:   {signals['short']:4d} ({signals['short']/total_bars*100:.1f}%)")
    print(f"  NEUTRAL: {signals['neutral']:4d} ({signals['neutral']/total_bars*100:.1f}%)")
    
    if sample_signals:
        print(f"\nSample Signals:")
        for s in sample_signals[:5]:
            print(f"  {s}")
    
    return signals


def main():
    print("="*60)
    print("ALL STRATEGIES TEST")
    print("Period: 2026-01-10 ~ 2026-01-15 (5 days)")
    print("="*60)
    
    strategies = [
        (TrendFollowingStrategy, "Trend Following (趨勢跟蹤)"),
        (SwingTradingStrategy, "Swing Trading (波段交易)"),
        (MeanReversionStrategy, "Mean Reversion (均值回歸)"),
        (BreakoutTradingStrategy, "Breakout Trading (突破交易)"),
    ]
    
    results = {}
    for strategy_class, name in strategies:
        try:
            results[name] = test_strategy(strategy_class, name)
        except Exception as e:
            print(f"\n{name}: ERROR - {e}")
    
    # 總結
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"{'Strategy':<30} {'LONG':>8} {'SHORT':>8} {'NEUTRAL':>8}")
    print("-"*60)
    for name, sigs in results.items():
        short_name = name.split("(")[0].strip()
        print(f"{short_name:<30} {sigs['long']:>8} {sigs['short']:>8} {sigs['neutral']:>8}")


if __name__ == "__main__":
    main()
