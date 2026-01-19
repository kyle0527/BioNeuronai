"""
三大交易策略測試與演示
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bioneuronai.trading_strategies import (
    Strategy1_RSI_Divergence,
    Strategy2_Bollinger_Bands_Breakout,
    Strategy3_MACD_Trend_Following,
    StrategyFusion,
    MarketData
)
from datetime import datetime
import random


def generate_sample_market_data(base_price: float = 50000.0, volatility: float = 0.02) -> MarketData:
    """生成模擬市場數據"""
    price_change = random.gauss(0, volatility)
    new_price = float(base_price) * (1 + price_change)
    
    high = new_price * (1 + abs(random.gauss(0, 0.005)))
    low = new_price * (1 - abs(random.gauss(0, 0.005)))
    open_price = new_price + random.gauss(0, new_price * 0.001)
    
    return MarketData(
        symbol="BTCUSDT",
        price=new_price,
        volume=random.uniform(100, 1000),
        timestamp=datetime.now(),
        high=high,
        low=low,
        open=open_price,
        close=new_price,
        bid=new_price - 10,
        ask=new_price + 10,
        funding_rate=0.0001,
        open_interest=10000
    )


def test_individual_strategies():
    """測試三個獨立策略"""
    print("=" * 80)
    print("📊 獨立策略測試")
    print("=" * 80)
    
    # 初始化策略
    rsi_strategy = Strategy1_RSI_Divergence()
    bb_strategy = Strategy2_Bollinger_Bands_Breakout()
    macd_strategy = Strategy3_MACD_Trend_Following()
    
    base_price = 50000
    
    print("\n🔄 生成 50 根 K 線數據...\n")
    
    for i in range(50):
        market_data = generate_sample_market_data(base_price)
        base_price = market_data.close  # 價格連續性
        
        # 每 10 根 K 線顯示一次信號
        if i % 10 == 9:
            print(f"\n📈 K 線 #{i+1} - 價格: ${market_data.close:,.2f}")
            print("-" * 80)
            
            # RSI 策略
            signal1 = rsi_strategy.analyze(market_data)
            print(f"\n🔵 策略一: RSI 背離")
            print(f"   動作: {signal1.action}")
            print(f"   置信度: {signal1.confidence:.2%}")
            print(f"   原因: {signal1.reason}")
            if signal1.stop_loss:
                print(f"   止損: ${signal1.stop_loss:,.2f}")
            if signal1.take_profit:
                print(f"   止盈: ${signal1.take_profit:,.2f}")
            
            # 布林帶策略
            signal2 = bb_strategy.analyze(market_data)
            print(f"\n🟢 策略二: 布林帶突破")
            print(f"   動作: {signal2.action}")
            print(f"   置信度: {signal2.confidence:.2%}")
            print(f"   原因: {signal2.reason}")
            if signal2.stop_loss:
                print(f"   止損: ${signal2.stop_loss:,.2f}")
            if signal2.take_profit:
                print(f"   止盈: ${signal2.take_profit:,.2f}")
            
            # MACD 策略
            signal3 = macd_strategy.analyze(market_data)
            print(f"\n🟡 策略三: MACD 趨勢跟隨")
            print(f"   動作: {signal3.action}")
            print(f"   置信度: {signal3.confidence:.2%}")
            print(f"   原因: {signal3.reason}")
            if signal3.stop_loss:
                print(f"   止損: ${signal3.stop_loss:,.2f}")
            if signal3.take_profit:
                print(f"   止盈: ${signal3.take_profit:,.2f}")


def test_strategy_fusion():
    """測試策略融合系統"""
    print("\n\n" + "=" * 80)
    print("🤖 AI 策略融合測試")
    print("=" * 80)
    
    fusion = StrategyFusion()
    base_price = 50000
    
    print("\n🧠 AI 正在學習市場模式...")
    print("📊 融合三種策略: RSI背離 + 布林帶突破 + MACD趨勢")
    print("\n🔄 開始模擬交易...\n")
    
    # 模擬 100 根 K 線
    for i in range(100):
        market_data = generate_sample_market_data(base_price)
        base_price = market_data.close
        
        # 獲取融合信號
        fused_signal = fusion.analyze(market_data)
        
        # 模擬交易結果 (簡化)
        if fused_signal.action in ["BUY", "SELL"]:
            # 隨機生成盈虧 (實際應該根據真實價格變動)
            simulated_pnl = random.gauss(0.01, 0.03)  # 平均 1% 收益,標準差 3%
            
            # 更新策略表現
            for signal_data in fusion.signal_history[-1]['individual_signals']:
                if signal_data.action == fused_signal.action:
                    fusion.update_strategy_performance(
                        signal_data.strategy_name,
                        simulated_pnl
                    )
        
        # 每 20 根 K 線顯示一次詳細信號
        if i % 20 == 19:
            print(f"\n{'='*80}")
            print(f"📈 K 線 #{i+1} - 價格: ${market_data.close:,.2f}")
            print(f"{'='*80}")
            
            print(f"\n🎯 融合信號:")
            print(f"   動作: {fused_signal.action}")
            print(f"   置信度: {fused_signal.confidence:.2%}")
            print(f"   原因:\n{fused_signal.reason}")
            if fused_signal.stop_loss:
                print(f"   止損: ${fused_signal.stop_loss:,.2f}")
            if fused_signal.take_profit:
                print(f"   止盈: ${fused_signal.take_profit:,.2f}")
    
    # 顯示策略表現報告
    print("\n\n" + "=" * 80)
    print("📊 策略表現報告")
    print("=" * 80)
    
    report = fusion.get_strategy_report()
    
    for strategy_name, stats in report.items():
        print(f"\n🎯 {strategy_name}:")
        for key, value in stats.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print("\n\n💡 AI 學習總結:")
    print("-" * 80)
    print("✓ AI 已經根據歷史表現動態調整了各策略的權重")
    print("✓ 表現較好的策略會獲得更高權重")
    print("✓ 系統會持續學習並優化融合方法")
    print("✓ 這是一個自我進化的交易系統\n")


def show_strategy_comparison():
    """顯示三種策略的對比說明"""
    print("\n" + "=" * 80)
    print("📚 三大交易策略詳細說明")
    print("=" * 80)
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ 策略一：RSI 背離策略 (RSI Divergence)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 原理：相對強弱指數 (RSI) 測量價格動量                                      │
│ 信號：                                                                      │
│   • 牛背離：價格創新低但 RSI 未創新低 → 買入                               │
│   • 熊背離：價格創新高但 RSI 未創新高 → 賣出                               │
│   • RSI < 30：超賣區域 → 買入機會                                          │
│   • RSI > 70：超買區域 → 賣出機會                                          │
│ 優勢：                                                                      │
│   ✓ 捕捉趨勢反轉點                                                          │
│   ✓ 背離信號領先價格變化                                                    │
│   ✓ 超買超賣區域明確                                                        │
│ 適用：震盪市場、區間交易                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 策略二：布林帶突破策略 (Bollinger Bands Breakout)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 原理：基於標準差的動態支撐阻力帶                                            │
│ 信號：                                                                      │
│   • 突破上軌 + 成交量放大 → 強勢做多                                       │
│   • 跌破下軌 + 成交量放大 → 超賣反彈                                       │
│   • 布林帶收縮 (帶寬 < 10%) → 大行情前兆                                   │
│   • 遠離中軌 → 均值回歸交易                                                │
│ 優勢：                                                                      │
│   ✓ 自動適應波動性                                                          │
│   ✓ 結合成交量確認提高準確度                                                │
│   ✓ 布林帶收縮預示突破                                                      │
│ 適用：趨勢市場、突破交易                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 策略三：MACD 趨勢跟隨策略 (MACD Trend Following)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 原理：移動平均收斂發散指標,捕捉趨勢和動量                                  │
│ 信號：                                                                      │
│   • 金叉 (MACD 上穿信號線) → 買入                                          │
│   • 死叉 (MACD 下穿信號線) → 賣出                                          │
│   • 零軸上方 → 多頭市場,增強買入信心                                       │
│   • 柱狀圖擴張 → 動量增強                                                  │
│ 優勢：                                                                      │
│   ✓ 同時捕捉趨勢方向和動量強度                                              │
│   ✓ 金叉/死叉信號明確                                                       │
│   ✓ 適合中長期趨勢跟隨                                                      │
│ 適用：趨勢市場、中長線交易                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🤖 AI 融合策略 (Strategy Fusion)                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 原理：智能融合三種策略,動態調整權重                                        │
│ 方法：                                                                      │
│   1. 多數投票：統計各策略的方向                                            │
│   2. 加權平均：根據歷史表現分配權重                                        │
│   3. 動態學習：持續優化權重分配                                            │
│   4. 信號篩選：只採用高置信度信號                                          │
│ 自我進化機制：                                                              │
│   • 記錄每個策略的盈虧                                                      │
│   • 計算勝率、平均收益、夏普比率                                            │
│   • 動態調整策略權重                                                        │
│   • 表現好的策略獲得更高權重                                                │
│ 優勢：                                                                      │
│   ✓ 結合多種策略的優勢                                                      │
│   ✓ 自動適應市場變化                                                        │
│   ✓ 降低單一策略的風險                                                      │
│   ✓ 持續學習和優化                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
""")


def main():
    """主函數"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║        🚀 BioNeuronai 加密貨幣交易策略系統 🚀                              ║
║                                                                            ║
║        三大經典策略 + AI 自主融合與進化                                    ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    # 顯示策略說明
    show_strategy_comparison()
    
    input("\n按 Enter 鍵開始測試獨立策略...")
    
    # 測試獨立策略
    test_individual_strategies()
    
    input("\n\n按 Enter 鍵開始測試 AI 融合策略...")
    
    # 測試融合策略
    test_strategy_fusion()
    
    print("\n" + "=" * 80)
    print("✅ 測試完成!")
    print("=" * 80)
    print("""
💡 下一步：

1. 將這些策略集成到 crypto_futures_trader.py
2. 在 trading_config.py 中選擇要使用的策略
3. 先在測試網練習,觀察 AI 的學習過程
4. AI 會根據實際交易結果自動優化策略權重

⚠️  記住：
• 每個策略都有其適用的市場環境
• 融合策略通過 AI 學習找出最佳組合
• 風險管理永遠是第一位的
• 持續監控和調整很重要
""")


if __name__ == "__main__":
    main()
