#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略信號調試腳本
================
檢查為什麼策略沒有產生交易信號
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.bioneuronai.strategies.trend_following import TrendFollowingStrategy
from src.bioneuronai.strategies.swing_trading import SwingTradingStrategy
from src.bioneuronai.strategies.mean_reversion import MeanReversionStrategy
from src.bioneuronai.strategies.breakout_trading import BreakoutTradingStrategy


def load_data():
    """載入數據"""
    data_root = Path("training_data/data_downloads/binance_historical/data/futures/um/daily/klines/ETHUSDT/1h")
    
    all_data = []
    for date_range_dir in data_root.iterdir():
        if not date_range_dir.is_dir():
            continue
        
        for zip_file in sorted(date_range_dir.glob("ETHUSDT-1h-*.zip")):
            with zipfile.ZipFile(zip_file, 'r') as zf:
                csv_name = zip_file.stem + '.csv'
                with zf.open(csv_name) as f:
                    df = pd.read_csv(f)
            
            df = df.rename(columns={'open_time': 'timestamp'})
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna()
            
            if not df.empty:
                all_data.append(df)
    
    df = pd.concat(all_data, ignore_index=True)
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 轉換為 numpy array
    ohlcv = np.zeros((len(df), 6))
    ohlcv[:, 0] = df['timestamp'].astype(np.int64) // 10**6
    ohlcv[:, 1] = df['open'].values
    ohlcv[:, 2] = df['high'].values
    ohlcv[:, 3] = df['low'].values
    ohlcv[:, 4] = df['close'].values
    ohlcv[:, 5] = df['volume'].values
    
    return ohlcv, df


def debug_strategy(strategy, ohlcv_data, strategy_name, bar_index=250):
    """調試策略分析"""
    print(f"\n{'='*60}")
    print(f"調試策略: {strategy_name}")
    print(f"{'='*60}")
    
    # 取得歷史數據到 bar_index
    historical = ohlcv_data[:bar_index+1]
    
    print(f"數據筆數: {len(historical)}")
    print(f"最新價格: ${historical[-1, 4]:.2f}")
    
    try:
        # 分析市場
        analysis = strategy.analyze_market(historical)
        
        print(f"\n市場分析結果:")
        print(f"  market_condition: {analysis.get('market_condition')}")
        print(f"  trend_direction: {analysis.get('trend_direction')}")
        print(f"  trend_strength: {analysis.get('trend_strength')}")
        print(f"  volatility: {analysis.get('volatility')}")
        print(f"  current_price: {analysis.get('current_price')}")
        
        # 如果有 trend_analysis，打印更多細節
        trend = analysis.get('trend_analysis')
        if trend:
            print(f"\n  趨勢分析詳情:")
            print(f"    primary_trend: {getattr(trend, 'primary_trend', 'N/A')}")
            print(f"    adx_value: {getattr(trend, 'adx_value', 'N/A')}")
            print(f"    adx_trending: {getattr(trend, 'adx_trending', 'N/A')}")
            print(f"    price_above_ema21: {getattr(trend, 'price_above_ema21', 'N/A')}")
            print(f"    price_above_ema55: {getattr(trend, 'price_above_ema55', 'N/A')}")
            print(f"    ema21_above_ema55: {getattr(trend, 'ema21_above_ema55', 'N/A')}")
        
        # 評估進場條件
        setup = strategy.evaluate_entry_conditions(analysis, historical)
        
        if setup:
            print(f"\n✅ 產生交易設定:")
            print(f"  direction: {setup.direction}")
            print(f"  entry_price: ${setup.entry_price:.2f}")
            print(f"  stop_loss: ${setup.stop_loss:.2f}")
            print(f"  signal_strength: {setup.signal_strength}")
        else:
            print(f"\n❌ 沒有產生交易設定")
            
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()


def find_signals(strategy, ohlcv_data, strategy_name, start_bar=200, max_bars=520):
    """尋找策略在哪些 bar 產生信號"""
    print(f"\n{'='*60}")
    print(f"搜索 {strategy_name} 信號 (bar {start_bar} ~ {max_bars})")
    print(f"{'='*60}")
    
    signals_found = 0
    
    for i in range(start_bar, min(max_bars, len(ohlcv_data))):
        historical = ohlcv_data[:i+1]
        
        try:
            analysis = strategy.analyze_market(historical)
            setup = strategy.evaluate_entry_conditions(analysis, historical)
            
            if setup:
                signals_found += 1
                timestamp = datetime.fromtimestamp(ohlcv_data[i, 0] / 1000)
                print(f"  ✅ Bar {i} [{timestamp}] - {setup.direction} @ ${setup.entry_price:.2f}")
                
                if signals_found >= 10:
                    print(f"  ... (已找到 10 個信號，停止搜索)")
                    break
                    
        except Exception as e:
            pass
    
    if signals_found == 0:
        print(f"  ❌ 未找到任何信號")
        
        # 檢查最後幾個 bar 的趨勢分析
        print(f"\n  最後 5 個 bar 的趨勢分析:")
        for i in range(max(start_bar, max_bars-5), min(max_bars, len(ohlcv_data))):
            historical = ohlcv_data[:i+1]
            try:
                analysis = strategy.analyze_market(historical)
                trend = analysis.get('trend_analysis')
                print(f"    Bar {i}: trend={analysis.get('trend_direction')}, "
                      f"strength={analysis.get('trend_strength'):.1f}, "
                      f"adx={getattr(trend, 'adx_value', 0):.1f}")
            except:
                pass
    
    return signals_found


def main():
    print("策略信號調試工具")
    print("=" * 60)
    
    # 載入數據
    print("\n載入數據...")
    ohlcv, df = load_data()
    print(f"載入 {len(ohlcv)} 筆數據")
    
    # 初始化策略
    strategies = {
        'TrendFollowing': TrendFollowingStrategy(),
        'SwingTrading': SwingTradingStrategy(),
        'MeanReversion': MeanReversionStrategy(),
        'BreakoutTrading': BreakoutTradingStrategy(),
    }
    
    # 調試每個策略
    for name, strategy in strategies.items():
        # 先在特定 bar 調試
        debug_strategy(strategy, ohlcv, name, bar_index=300)
        
        # 搜索信號
        find_signals(strategy, ohlcv, name)


if __name__ == "__main__":
    main()
