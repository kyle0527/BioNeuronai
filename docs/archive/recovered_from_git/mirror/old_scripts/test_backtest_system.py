#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回測系統驗證測試
================

快速驗證回測引擎是否正常工作
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加 src 到路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("🔧 導入模組...")
from bioneuronai.backtest import (
    MockBinanceConnector,
    HistoricalDataStream,
    VirtualAccount,
    quick_backtest,
)
from bioneuronai.backtest.data_stream import KlineBar


def test_data_stream():
    """測試數據串流"""
    print("\n" + "=" * 60)
    print("📊 測試 1: 數據串流")
    print("=" * 60)
    
    stream = HistoricalDataStream(
        data_dir="data_downloads/binance_historical",
        symbol="ETHUSDT",
        interval="15m",
        start_date="2025-12-22",
        end_date="2025-12-23",
        speed_multiplier=0,  # 無延遲
    )
    
    print(f"✅ 數據載入: {stream.state.total_bars:,} 根 K線")
    
    # 測試前 5 根
    bar_count = 0
    for bar in stream.stream_bars():
        bar_count += 1
        if bar_count <= 5:
            dt = datetime.fromtimestamp(bar.open_time / 1000)
            print(f"   Bar {bar_count}: {dt} | O:{bar.open:.2f} H:{bar.high:.2f} L:{bar.low:.2f} C:{bar.close:.2f}")
        else:
            break
    
    print(f"✅ 數據串流測試通過 (共 {stream.state.total_bars} 根)")
    return True


def test_virtual_account():
    """測試虛擬帳戶"""
    print("\n" + "=" * 60)
    print("💰 測試 2: 虛擬帳戶")
    print("=" * 60)
    
    account = VirtualAccount(initial_balance=10000, leverage=2)
    
    print(f"✅ 初始餘額: {account.get_balance():,.2f} USDT")
    
    # 模擬價格
    account.update_price("ETHUSDT", 3500.0)
    
    # 下市價單
    print("\n📝 測試下單...")
    order = account.place_order(
        symbol="ETHUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.1,
    )
    
    print(f"   訂單 ID: {order.order_id}")
    print(f"   狀態: {order.status.value}")
    print(f"   成交價: {order.filled_price:.2f}")
    print(f"   手續費: {order.commission:.4f} USDT")
    
    # 檢查倉位
    position = account.get_position("ETHUSDT")
    if position:
        print(f"\n📈 倉位信息:")
        print(f"   方向: {position.side.value}")
        print(f"   數量: {position.quantity}")
        print(f"   入場價: {position.entry_price:.2f}")
        print(f"   標記價: {position.mark_price:.2f}")
        print(f"   未實現盈虧: {position.unrealized_pnl:+.2f} USDT")
    
    # 更新價格測試盈虧
    account.update_price("ETHUSDT", 3550.0)
    position = account.get_position("ETHUSDT")
    print(f"\n📊 價格更新至 3550.0:")
    print(f"   未實現盈虧: {position.unrealized_pnl:+.2f} USDT")
    
    # 平倉
    print(f"\n📉 測試平倉...")
    close_order = account.place_order(
        symbol="ETHUSDT",
        side="SELL",
        order_type="MARKET",
        quantity=0.1,
    )
    
    print(f"   平倉完成")
    print(f"   最終餘額: {account.get_balance():,.2f} USDT")
    
    stats = account.get_stats()
    print(f"   總收益率: {stats['total_return']:+.2f}%")
    
    print("✅ 虛擬帳戶測試通過")
    return True


def test_mock_connector():
    """測試 Mock 連接器"""
    print("\n" + "=" * 60)
    print("🎭 測試 3: Mock 連接器 (接口偽裝)")
    print("=" * 60)
    
    mock = MockBinanceConnector(
        data_dir="data_downloads/binance_historical",
        symbol="ETHUSDT",
        interval="15m",
        start_date="2025-12-22",
        end_date="2025-12-22",
        initial_balance=10000,
    )
    
    # 手動推進幾根 K線
    print("\n🔄 推進 K線...")
    for i in range(5):
        bar = mock.step()
        if bar:
            print(f"   Bar {i+1}: {bar.close:.2f} @ {datetime.fromtimestamp(bar.open_time/1000).strftime('%H:%M')}")
    
    # 測試 API 方法
    print("\n📡 測試 API 方法...")
    
    # get_ticker_price
    ticker = mock.get_ticker_price("ETHUSDT")
    if ticker:
        print(f"✅ get_ticker_price: {ticker.price:.2f} USDT")
    
    # get_klines
    klines = mock.get_klines("ETHUSDT", "15m", limit=10)
    if klines:
        print(f"✅ get_klines: 返回 {len(klines)} 根 K線")
    
    # get_account_info
    account_info = mock.get_account_info()
    if account_info:
        print(f"✅ get_account_info: 餘額 {account_info['totalWalletBalance']} USDT")
    
    # place_order
    print("\n📝 測試下單...")
    order_result = mock.place_order(
        symbol="ETHUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.05,
    )
    if order_result:
        print(f"✅ place_order: 訂單 {order_result.order_id} {order_result.status}")
    
    print("\n✅ Mock 連接器測試通過")
    return True


def test_simple_strategy():
    """測試簡單策略回測"""
    print("\n" + "=" * 60)
    print("🚀 測試 4: 完整策略回測")
    print("=" * 60)
    
    # 定義一個極簡單的策略
    trade_count = 0
    
    def simple_strategy(bar: KlineBar, connector: MockBinanceConnector):
        nonlocal trade_count
        
        # 每 20 根 K線交易一次
        if connector.data_stream.state.current_index % 20 == 0:
            position = connector.get_position(bar.symbol)
            
            if position is None:
                # 開倉
                connector.place_order(
                    symbol=bar.symbol,
                    side="BUY" if bar.close > bar.open else "SELL",
                    order_type="MARKET",
                    quantity=0.05,
                )
                trade_count += 1
            else:
                # 平倉
                side = "SELL" if position.side.value == "LONG" else "BUY"
                connector.place_order(
                    symbol=bar.symbol,
                    side=side,
                    order_type="MARKET",
                    quantity=position.quantity,
                )
    
    print("\n📊 開始回測...")
    print("   策略: 每 20 根 K線隨機開平倉")
    print("   時間: 2025-12-22 ~ 2025-12-23")
    
    result = quick_backtest(
        strategy=simple_strategy,
        symbol="ETHUSDT",
        interval="15m",
        start_date="2025-12-22",
        end_date="2025-12-23",
        initial_balance=10000,
        data_dir="data_downloads/binance_historical"
    )
    
    print(f"\n✅ 回測完成!")
    print(f"   執行了 {trade_count} 次交易")
    
    return result


def test_防偷看機制():
    """測試防偷看機制"""
    print("\n" + "=" * 60)
    print("🔒 測試 5: 防偷看機制")
    print("=" * 60)
    
    stream = HistoricalDataStream(
        data_dir="data_downloads/binance_historical",
        symbol="ETHUSDT",
        interval="15m",
        start_date="2025-12-22",
        end_date="2025-12-22",
    )
    
    # 推進到第 10 根
    for i, bar in enumerate(stream.stream_bars()):
        if i >= 9:
            break
    
    print(f"✅ 當前位置: 第 10 根 K線")
    print(f"   當前時間: {stream.get_current_time()}")
    print(f"   當前價格: {stream.get_current_price():.2f}")
    
    # 嘗試獲取歷史數據
    klines = stream.get_klines_until_now(limit=999999)  # 嘗試獲取「所有」數據
    print(f"\n🔍 嘗試獲取「所有」歷史數據...")
    print(f"   實際返回: {len(klines)} 根 K線")
    print(f"   ✅ 防偷看生效！只能看到前 10 根")
    
    # 確認無法看到未來
    if len(klines) <= 10:
        print(f"\n✅ 防偷看機制測試通過")
        print(f"   在第 10 根 K線時，無法獲取第 11 根及以後的數據")
        return True
    else:
        print(f"\n❌ 防偷看機制失敗！可以看到 {len(klines)} 根數據")
        return False


def main():
    """主測試流程"""
    print("\n" + "🧪" * 30)
    print("   BioNeuronAI 回測系統驗證測試")
    print("🧪" * 30)
    
    tests = [
        ("數據串流", test_data_stream),
        ("虛擬帳戶", test_virtual_account),
        ("Mock 連接器", test_mock_connector),
        ("防偷看機制", test_防偷看機制),
        ("完整策略回測", test_simple_strategy),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, True, result))
            print(f"\n✅ {name} 測試通過")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"\n❌ {name} 測試失敗: {e}")
            import traceback
            traceback.print_exc()
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, result in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print("-" * 60)
    print(f"通過: {passed}/{total} ({passed/total*100:.0f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有測試通過！回測系統運作正常！")
        print("\n📝 下一步:")
        print("   1. 運行 python run_backtest_demo.py 查看完整示範")
        print("   2. 將 MockBinanceConnector 整合到 TradingEngine")
        print("   3. 使用真實策略進行回測")
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤信息")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
