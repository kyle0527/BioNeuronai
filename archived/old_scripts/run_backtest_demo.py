#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回測範例腳本
============

展示如何使用回測引擎進行策略測試

使用方式:
    python run_backtest_demo.py
"""

import sys
from pathlib import Path

# 添加 src 到路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from bioneuronai.backtest import (
    BacktestEngine,
    BacktestConfig,
    MockBinanceConnector,
    quick_backtest,
    create_mock_connector,
)
from bioneuronai.backtest.data_stream import KlineBar


def simple_ma_strategy(bar: KlineBar, connector: MockBinanceConnector):
    """
    簡單移動平均線策略
    
    規則:
    - 價格上穿 20MA: 做多
    - 價格下穿 20MA: 做空
    """
    # 獲取歷史 K線 (防偷看: 只能看到當前時間之前的數據)
    klines = connector.get_klines(bar.symbol, limit=25)
    
    if not klines or len(klines) < 20:
        return
    
    # 計算 20 MA
    closes = [float(k[4]) for k in klines[-20:]]
    ma20 = sum(closes) / len(closes)
    
    # 獲取當前倉位
    position = connector.get_position(bar.symbol)
    current_price = bar.close
    
    # 交易邏輯
    if current_price > ma20 * 1.001:  # 上穿 MA + 0.1%
        if position is None:
            # 開多倉
            connector.place_order(
                symbol=bar.symbol,
                side="BUY",
                order_type="MARKET",
                quantity=0.01,
                stop_loss=current_price * 0.98,  # 2% 止損
                take_profit=current_price * 1.04  # 4% 止盈
            )
        elif position.side.value == "SHORT":
            # 平空倉
            connector.place_order(
                symbol=bar.symbol,
                side="BUY",
                order_type="MARKET",
                quantity=position.quantity
            )
    
    elif current_price < ma20 * 0.999:  # 下穿 MA - 0.1%
        if position is None:
            # 開空倉
            connector.place_order(
                symbol=bar.symbol,
                side="SELL",
                order_type="MARKET",
                quantity=0.01,
                stop_loss=current_price * 1.02,
                take_profit=current_price * 0.96
            )
        elif position.side.value == "LONG":
            # 平多倉
            connector.place_order(
                symbol=bar.symbol,
                side="SELL",
                order_type="MARKET",
                quantity=position.quantity
            )


def rsi_divergence_strategy(bar: KlineBar, connector: MockBinanceConnector):
    """
    RSI 超買超賣策略
    
    規則:
    - RSI < 30: 做多 (超賣)
    - RSI > 70: 做空 (超買)
    """
    klines = connector.get_klines(bar.symbol, limit=20)
    
    if not klines or len(klines) < 14:
        return
    
    # 計算 RSI
    closes = [float(k[4]) for k in klines]
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < 14:
        return
    
    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14
    
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    # 獲取倉位
    position = connector.get_position(bar.symbol)
    
    # 交易邏輯
    if rsi < 30 and position is None:
        connector.place_order(bar.symbol, "BUY", "MARKET", 0.01)
    elif rsi > 70 and position is None:
        connector.place_order(bar.symbol, "SELL", "MARKET", 0.01)
    elif position:
        # 獲利了結
        if position.unrealized_pnl > 50:  # 盈利 $50
            side = "SELL" if position.side.value == "LONG" else "BUY"
            connector.place_order(bar.symbol, side, "MARKET", position.quantity)


def demo_quick_backtest():
    """示範快速回測"""
    print("\n" + "=" * 60)
    print("📊 快速回測示範 - 簡單 MA 策略")
    print("=" * 60)
    
    result = quick_backtest(
        strategy=simple_ma_strategy,
        symbol="BTCUSDT",
        interval="1m",
        start_date="2025-12-22",  # 使用現有數據的日期
        end_date="2025-12-22",
        initial_balance=10000,
        data_dir="data_downloads/binance_historical"
    )
    
    return result


def demo_full_backtest():
    """示範完整回測"""
    print("\n" + "=" * 60)
    print("📊 完整回測示範 - RSI 策略")
    print("=" * 60)
    
    config = BacktestConfig(
        data_dir="data_downloads/binance_historical",
        symbol="ETHUSDT",
        interval="1m",
        start_date="2025-12-22",
        end_date="2025-12-22",
        initial_balance=10000,
        leverage=2,
        warmup_bars=50,
    )
    
    engine = BacktestEngine(config=config)
    result = engine.run(rsi_divergence_strategy)
    
    return result


def demo_with_trading_engine():
    """
    示範與 TradingEngine 整合
    
    這是最強大的用法：TradingEngine 完全不知道它在跑回測!
    """
    print("\n" + "=" * 60)
    print("📊 TradingEngine 整合示範")
    print("=" * 60)
    
    # 1. 創建 Mock 連接器
    mock = create_mock_connector(
        symbol="BTCUSDT",
        start_date="2025-12-22",
        end_date="2025-12-22",
        initial_balance=10000,
        data_dir="data_downloads/binance_historical"
    )
    
    print("\n✅ Mock 連接器已創建")
    print("📝 現在可以用它替換 TradingEngine 的連接器:")
    print("   engine = TradingEngine()")
    print("   engine.connector = mock  # 替換!")
    print("\n💡 TradingEngine 會以為它在做真實交易")
    print("   但實際上是在歷史數據上運行回測")
    
    # 示範手動回放
    print("\n🔄 手動回放示範 (前 10 根 K線):")
    
    bar_count = 0
    for bar in mock.data_stream.stream_bars():
        bar_count += 1
        if bar_count <= 10:
            print(f"   Bar {bar_count}: {bar.close:.2f} USDT @ {bar.open_time}")
        elif bar_count == 11:
            print("   ...")
            break
    
    mock.data_stream.reset()
    
    return mock


def main():
    """主程式"""
    print("\n" + "🎯" * 30)
    print("   BioNeuronAI 回測引擎示範")
    print("🎯" * 30)
    
    try:
        # 示範 1: 快速回測
        result1 = demo_quick_backtest()
        
        # 示範 2: 完整回測  
        result2 = demo_full_backtest()
        
        # 示範 3: TradingEngine 整合
        mock = demo_with_trading_engine()
        
        print("\n" + "=" * 60)
        print("✅ 所有示範完成!")
        print("=" * 60)
        
        print("\n📚 下一步:")
        print("   1. 閱讀 src/bioneuronai/backtest/README.md")
        print("   2. 修改策略函數嘗試不同的交易邏輯")
        print("   3. 下載更多歷史數據進行長期回測")
        print("   4. 將 Mock 連接器整合到 TradingEngine")
        
    except FileNotFoundError as e:
        print(f"\n❌ 數據文件未找到: {e}")
        print("\n📝 請先下載歷史數據:")
        print("   cd data_downloads")
        print("   python scripts/download-kline.py -s BTCUSDT -i 1m")
    
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
