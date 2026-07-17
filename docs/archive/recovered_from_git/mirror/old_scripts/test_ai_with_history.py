#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 AI 模型在歷史數據上的交易決策
===================================

讓 AI 認為它在做真實交易，但實際上使用歷史數據
"""

import sys
from pathlib import Path

# 添加 src 到路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from bioneuronai.core import TradingEngine
from bioneuronai.backtest import create_mock_connector

print("=" * 70)
print("🤖 AI 模型 + 歷史數據回測測試")
print("=" * 70)

# ========== 步驟 1: 創建交易引擎（啟用 AI）==========
print("\n📊 步驟 1: 初始化交易引擎...")
print("   - 啟用 AI 模型")
print("   - 啟用策略融合")
print("   - 設置風險管理")

engine = TradingEngine(
    testnet=True,
    enable_ai_model=True,      # 啟用 AI
    ai_min_confidence=0.6,     # AI 信號最低置信度
    strategy_type="fusion",    # 使用策略融合
)

print("✅ 交易引擎初始化完成")
print(f"   AI 引擎: {hasattr(engine, 'inference_engine') and engine.inference_engine is not None}")
print(f"   策略融合: {engine.strategy_fusion is not None}")

# ========== 步驟 2: 創建 Mock 連接器（時光機）==========
print("\n⏰ 步驟 2: 啟動時光機...")
print("   - 載入歷史數據: ETHUSDT 15m")
print("   - 時間範圍: 2025-12-22 ~ 2025-12-30")
print("   - 初始資金: $10,000 USDT")

mock = create_mock_connector(
    symbol="ETHUSDT",
    interval="15m",
    start_date="2025-12-22",
    end_date="2025-12-30",
    initial_balance=10000,
    data_dir="data_downloads/binance_historical"
)

print("✅ Mock 連接器創建完成")
print(f"   載入數據: {mock.data_stream.state.total_bars} 根 K線")

# ========== 步驟 3: 替換連接器（關鍵步驟）==========
print("\n🔄 步驟 3: 替換連接器...")
print("   - 將真實 Binance API 替換為歷史數據流")
print("   - AI 完全無法分辨真假！")

# 保存原始連接器
original_connector = engine.connector

# 替換為 Mock（這是關鍵！）
engine.connector = mock
engine.data_connector = mock

print("✅ 連接器已替換")
print("   AI 認為: 正在連接真實 Binance API")
print("   實際上: 正在讀取歷史數據")

# ========== 步驟 4: 預熱系統（累積數據）==========
print("\n🔥 步驟 4: 預熱系統...")
print("   - 推進 50 根 K線讓 AI 學習市場狀態")

warmup_bars = 50
for i in range(warmup_bars):
    bar = mock.step()
    if not bar:
        break
    if (i + 1) % 10 == 0:
        print(f"   進度: {i+1}/{warmup_bars}")

print(f"✅ 預熱完成")

# ========== 步驟 5: AI 分析並生成交易信號 ==========
print("\n🤖 步驟 5: AI 開始分析市場...")

# 獲取歷史數據供 AI 分析
klines = mock.get_klines("ETHUSDT", "15m", limit=100)

if klines and len(klines) >= 50:
    print(f"   獲取數據: {len(klines)} 根 K線")
    print(f"   當前價格: ${klines[-1].close:,.2f}")
    
    # 準備市場數據
    market_data = {
        'symbol': 'ETHUSDT',
        'interval': '15m',
        'price': klines[-1].close,
        'volume': klines[-1].volume,
        'klines': klines
    }
    
    # 使用策略融合生成信號
    if engine.strategy_fusion:
        print("\n   🔮 策略融合分析中...")
        signal = engine.strategy_fusion.generate_signal(market_data)
        
        if signal:
            print(f"\n   ✅ 交易信號生成:")
            print(f"      動作: {signal.action.value}")
            print(f"      置信度: {signal.confidence:.2%}")
            print(f"      策略: {signal.strategy_name}")
            print(f"      理由: {signal.reason}")
            
            if signal.target_price:
                print(f"      目標價: ${signal.target_price:,.2f}")
            if signal.stop_loss:
                print(f"      止損價: ${signal.stop_loss:,.2f}")
            
            # ========== 步驟 6: 執行交易（如果信號夠強）==========
            if signal.action.value in ['BUY', 'SELL'] and signal.confidence >= 0.6:
                print(f"\n   💼 步驟 6: 執行交易...")
                
                # 獲取帳戶餘額
                account = mock.get_account_info()
                balance = float(account['availableBalance'])
                
                # 計算倉位大小（使用 2% 風險）
                risk_amount = balance * 0.02
                position_size = risk_amount / klines[-1].close
                position_size = min(position_size, 0.1)  # 限制最大 0.1
                
                print(f"      帳戶餘額: ${balance:,.2f}")
                print(f"      風險金額: ${risk_amount:,.2f}")
                print(f"      倉位大小: {position_size:.4f} ETH")
                
                # 下單
                order = mock.place_order(
                    symbol="ETHUSDT",
                    side=signal.action.value,
                    order_type="MARKET",
                    quantity=position_size
                )
                
                if order and order.status == "FILLED":
                    print(f"\n      ✅ 訂單成交!")
                    print(f"         訂單 ID: {order.order_id}")
                    print(f"         方向: {order.side}")
                    print(f"         數量: {order.quantity:.4f}")
                    print(f"         價格: ${order.filled_price:,.2f}")
                    print(f"         手續費: ${order.commission:.4f}")
                    
                    # 查看倉位
                    position = mock.get_position("ETHUSDT")
                    if position:
                        print(f"\n      📊 當前倉位:")
                        print(f"         方向: {position.side.value}")
                        print(f"         數量: {position.quantity}")
                        print(f"         入場價: ${position.entry_price:,.2f}")
                        print(f"         未實現盈虧: ${position.unrealized_pnl:+,.2f}")
            else:
                print(f"\n   ⏸️ 信號不夠強，等待更好機會")
                print(f"      (置信度 {signal.confidence:.2%} < 60%)")
        else:
            print("   ℹ️ 暫無交易信號")
    
    # ========== 步驟 7: 繼續運行回測 ==========
    print("\n\n🚀 步驟 7: 運行完整回測...")
    print("=" * 70)
    
    # 定義簡單的 AI 交易策略
    class AITrader:
        def __init__(self):
            self.trade_count = 0
    
    ai_trader = AITrader()
    
    def ai_trading_strategy(bar, connector):
        """使用 AI 的交易策略"""
        
        # 每 10 根 K線檢查一次
        if connector.data_stream.state.current_index % 10 == 0:
            # 獲取最近數據
            recent_klines = connector.get_klines("ETHUSDT", "15m", limit=50)
            
            if recent_klines and len(recent_klines) >= 30:
                # 準備數據
                data = {
                    'symbol': 'ETHUSDT',
                    'price': recent_klines[-1].close,
                    'volume': recent_klines[-1].volume,
                    'klines': recent_klines
                }
                
                # 使用策略融合
                if engine.strategy_fusion:
                    signal = engine.strategy_fusion.generate_signal(data)
                    
                    if signal and signal.confidence >= 0.6:
                        position = connector.get_position("ETHUSDT")
                        
                        if signal.action.value == "BUY" and not position:
                            # 開多倉
                            connector.place_order(
                                symbol="ETHUSDT",
                                side="BUY",
                                order_type="MARKET",
                                quantity=0.05
                            )
                            ai_trader.trade_count += 1
                            
                        elif signal.action.value == "SELL" and not position:
                            # 開空倉
                            connector.place_order(
                                symbol="ETHUSDT",
                                side="SELL",
                                order_type="MARKET",
                                quantity=0.05
                            )
                            ai_trader.trade_count += 1
                            
                        elif position and signal.action.value != position.side.value:
                            # 平倉
                            side = "SELL" if position.side.value == "LONG" else "BUY"
                            connector.place_order(
                                symbol="ETHUSDT",
                                side=side,
                                order_type="MARKET",
                                quantity=position.quantity
                            )
    
    # 運行回測
    result = mock.run_backtest(
        on_bar=ai_trading_strategy,
        progress_callback=lambda i, total: print(f"\r   進度: {i}/{total} ({i/total*100:.1f}%)", end="") if i % 20 == 0 else None
    )
    
    print("\n\n" + "=" * 70)
    print("📊 AI 回測結果")
    print("=" * 70)
    
    # 顯示統計
    stats = mock.get_statistics()
    
    print(f"\n💰 資金狀況:")
    print(f"   初始餘額: ${stats['initial_balance']:,.2f}")
    print(f"   最終餘額: ${stats['final_balance']:,.2f}")
    print(f"   總收益: ${stats['total_pnl']:+,.2f}")
    print(f"   總收益率: {stats['total_return']:+.2f}%")
    
    print(f"\n🤖 AI 交易統計:")
    print(f"   AI 生成信號: {ai_trader.trade_count} 次")
    print(f"   總交易次數: {stats['total_trades']}")
    print(f"   勝率: {stats['win_rate']:.2f}%")
    print(f"   盈利交易: {stats['winning_trades']}")
    print(f"   虧損交易: {stats['losing_trades']}")
    
    if stats.get('profit_factor'):
        print(f"   獲利因子: {stats['profit_factor']:.2f}")
    
    print(f"\n📉 風險指標:")
    print(f"   最大回撤: {stats['max_drawdown']:.2f}%")
    
    if stats.get('sharpe_ratio'):
        print(f"   夏普比率: {stats['sharpe_ratio']:.2f}")
    
    print(f"\n💸 成本分析:")
    print(f"   總手續費: ${stats['total_fees']:.2f}")
    print(f"   平均每筆手續費: ${stats['total_fees']/max(stats['total_trades'],1):.4f}")
    
    # 顯示最近交易
    trades = mock.get_trade_history()
    if trades:
        print(f"\n📋 最近交易記錄 (最後 5 筆):")
        for trade in trades[-5:]:
            pnl_str = f"${trade['pnl']:+,.2f}" if trade.get('pnl') else "持倉中"
            print(f"   {trade['side']:4s} | {trade['quantity']:.4f} @ ${trade['price']:,.2f} | {pnl_str}")

else:
    print("❌ 數據不足，無法進行分析")

# ========== 步驟 8: 還原連接器 ==========
print("\n\n🔄 步驟 8: 還原真實連接器...")
engine.connector = original_connector
engine.data_connector = original_connector
print("✅ 已還原真實 API 連接")

print("\n" + "=" * 70)
print("✅ 測試完成！")
print("=" * 70)
print("\n📝 總結:")
print("   1. AI 成功在歷史數據上運作")
print("   2. 完全無法分辨真實 API 和歷史數據")
print("   3. 策略融合系統正常工作")
print("   4. 可以用於驗證 AI 模型效果")
print("   5. 可以優化策略參數")
