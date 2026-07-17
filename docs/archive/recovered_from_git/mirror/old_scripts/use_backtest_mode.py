#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用歷史數據測試交易引擎
========================

用回測模式（MockBinanceConnector）測試完整交易流程
"""

import sys
import time
from pathlib import Path

# 添加 src 到路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("=" * 60)
print(" BioNeuronai 回測模式測試 v1.0")
print("    - 使用歷史數據模擬真實交易")
print("=" * 60)

from bioneuronai.core.trading_engine import TradingEngine
from bioneuronai.backtest import MockBinanceConnector

def main():
    """主流程"""
    
    # ========== 步驟 1: 創建 Mock 連接器 ==========
    print("\n📊 初始化回測系統...")
    print(f"   交易對: ETHUSDT")
    print(f"   時間週期: 15m")
    print(f"   數據範圍: 2025-12-22 ~ 2025-12-30")
    print(f"   初始資金: $10,000 USDT")
    
    mock_connector = MockBinanceConnector(
        data_dir="data_downloads/binance_historical",
        symbol="ETHUSDT",
        interval="15m",
        start_date="2025-12-22",
        end_date="2025-12-30",
        initial_balance=10000,
        leverage=2,
    )
    
    print("✅ Mock 連接器創建完成")
    
    # ========== 步驟 2: 創建交易引擎 ==========
    print("\n🤖 初始化交易引擎...")
    trader = TradingEngine(
        testnet=True,
        enable_ai_model=True,
        ai_min_confidence=0.5
    )
    
    print("✅ 交易引擎初始化完成")
    
    # ========== 步驟 3: 替換連接器（時光機啟動！）==========
    print("\n⏰ 啟動時光機制...")
    print("   將真實 Binance 連接器替換為歷史數據流")
    
    # 保存原始連接器（以防需要）
    original_connector = trader.connector
    
    # 替換為 Mock 連接器
    trader.connector = mock_connector
    trader.data_connector = mock_connector
    
    print("✅ 時光機已啟動！AI 認為這是真實交易")
    
    # ========== 步驟 4: 獲取當前價格（歷史數據第一根 K 線）==========
    print("\n💰 獲取市場價格...")
    
    # 推進到第一根 K 線
    first_bar = mock_connector.step()
    if first_bar:
        from datetime import datetime
        time_str = datetime.fromtimestamp(first_bar.open_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
        print(f"   時間: {time_str}")
        print(f"   開盤: ${first_bar.open:,.2f}")
        print(f"   最高: ${first_bar.high:,.2f}")
        print(f"   最低: ${first_bar.low:,.2f}")
        print(f"   收盤: ${first_bar.close:,.2f}")
        print(f"   成交量: {first_bar.volume:,.2f}")
    
    # ========== 步驟 5: 查看帳戶信息 ==========
    print("\n📈 帳戶信息:")
    account_info = mock_connector.get_account_info()
    if account_info:
        print(f"   總餘額: ${float(account_info['totalWalletBalance']):,.2f} USDT")
        print(f"   可用餘額: ${float(account_info['availableBalance']):,.2f} USDT")
        print(f"   槓桿: {mock_connector.virtual_account.leverage}x")
    
    # ========== 步驟 6: 生成交易信號 ==========
    print("\n🔮 生成交易信號...")
    
    # 推進 20 根 K 線作為預熱
    print("   預熱系統（20 根 K 線）...")
    for i in range(20):
        bar = mock_connector.step()
        if not bar:
            break
    
    # 使用交易引擎分析
    print("   使用 AI 分析市場...")
    
    # 模擬獲取歷史數據給 AI
    klines = mock_connector.get_klines("ETHUSDT", "15m", limit=100)
    
    if klines and len(klines) > 0:
        # 準備數據格式
        market_data = {
            'symbol': 'ETHUSDT',
            'price': klines[-1].close,
            'volume': klines[-1].volume,
            'klines': klines
        }
        
        # 使用策略融合生成信號
        if hasattr(trader, 'strategy_fusion'):
            signal = trader.strategy_fusion.generate_signal(market_data)
            if signal:
                print(f"\n📊 交易信號:")
                print(f"   動作: {signal.action.value}")
                print(f"   置信度: {signal.confidence:.2%}")
                print(f"   策略: {signal.strategy_name}")
                print(f"   理由: {signal.reason}")
                
                # ========== 步驟 7: 執行模擬交易 ==========
                if signal.action.value in ['BUY', 'SELL'] and signal.confidence > 0.6:
                    print(f"\n💼 執行交易...")
                    
                    # 計算倉位
                    balance = float(account_info['availableBalance'])
                    position_size = min(0.1, balance * 0.02 / klines[-1].close)  # 2% 風險
                    
                    # 下單
                    order = mock_connector.place_order(
                        symbol="ETHUSDT",
                        side=signal.action.value,
                        order_type="MARKET",
                        quantity=position_size
                    )
                    
                    if order and order.status == "FILLED":
                        print(f"   ✅ 訂單成交!")
                        print(f"   訂單 ID: {order.order_id}")
                        print(f"   方向: {order.side}")
                        print(f"   數量: {order.quantity}")
                        print(f"   價格: ${order.filled_price:,.2f}")
                        print(f"   手續費: ${order.commission:.4f} USDT")
    
    # ========== 步驟 8: 運行完整回測 ==========
    print("\n\n🚀 開始完整回測...")
    print("=" * 60)
    
    # 運行回測
    result = mock_connector.run_backtest(
        on_bar=None,  # 使用默認邏輯
        progress_callback=lambda i, total: print(f"\r   進度: {i}/{total} ({i/total*100:.1f}%)", end="") if i % 10 == 0 else None
    )
    
    print("\n\n" + "=" * 60)
    print("📊 回測結果")
    print("=" * 60)
    
    # 顯示結果
    stats = mock_connector.get_statistics()
    
    print(f"\n💰 資金狀況:")
    print(f"   初始餘額: ${stats['initial_balance']:,.2f}")
    print(f"   最終餘額: ${stats['final_balance']:,.2f}")
    print(f"   總收益: ${stats['total_pnl']:+,.2f}")
    print(f"   總收益率: {stats['total_return']:+.2f}%")
    
    print(f"\n📈 交易統計:")
    print(f"   總交易次數: {stats['total_trades']}")
    print(f"   勝率: {stats['win_rate']:.2f}%")
    print(f"   盈利交易: {stats['winning_trades']}")
    print(f"   虧損交易: {stats['losing_trades']}")
    
    if stats['profit_factor']:
        print(f"   獲利因子: {stats['profit_factor']:.2f}")
    
    print(f"\n⚠️ 風險指標:")
    print(f"   最大回撤: {stats['max_drawdown']:.2f}%")
    if stats['sharpe_ratio']:
        print(f"   夏普比率: {stats['sharpe_ratio']:.2f}")
    
    print(f"\n💸 成本:")
    print(f"   總手續費: ${stats['total_fees']:.2f}")
    
    # 查看倉位歷史
    positions = mock_connector.get_position_history()
    if positions:
        print(f"\n📋 倉位歷史 (最近 5 筆):")
        for pos in positions[-5:]:
            print(f"   {pos['side']:5s} | 數量: {pos['quantity']:.4f} | "
                  f"入場: ${pos['entry_price']:,.2f} | "
                  f"出場: ${pos['exit_price']:,.2f} | "
                  f"盈虧: ${pos['realized_pnl']:+.2f}")
    
    print("\n" + "=" * 60)
    print("✅ 回測完成！")
    print("=" * 60)
    
    # ========== 步驟 9: 還原真實連接器 ==========
    print("\n⏰ 關閉時光機，還原真實連接器...")
    trader.connector = original_connector
    trader.data_connector = original_connector
    print("✅ 已還原")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用戶中斷")
    except Exception as e:
        print(f"\n\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
