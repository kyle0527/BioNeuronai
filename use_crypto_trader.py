"""
虛擬貨幣期貨交易系統 - 快速啟動腳本
========================================
"""

import sys
import time
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 從新模組化架構導入
from src.bioneuronai import CryptoFuturesTrader
import logging

logger = logging.getLogger(__name__)

# 可以從配置文件導入
try:
    from config.trading_config import (
        BINANCE_API_KEY,
        BINANCE_API_SECRET,
        USE_TESTNET,
        TRADING_PAIRS,
        AUTO_TRADE_ENABLED,
        USE_STRATEGY_FUSION,
        MAX_RISK_PER_TRADE,
        MAX_TRADES_PER_DAY,
        MIN_SIGNAL_CONFIDENCE
    )
except ImportError:
    # 使用默認值
    BINANCE_API_KEY = ""
    BINANCE_API_SECRET = ""
    USE_TESTNET = True
    TRADING_PAIRS = ["BTCUSDT"]
    AUTO_TRADE_ENABLED = False
    USE_STRATEGY_FUSION = True
    MAX_RISK_PER_TRADE = 0.02
    MAX_TRADES_PER_DAY = 10
    MIN_SIGNAL_CONFIDENCE = 0.65


def print_banner():
    """顯示啟動橫幅"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🚀 BioNeuronai 虛擬貨幣期貨交易系統 🚀            ║
║                                                          ║
║  🧠 整合 AI 策略融合系統（三大策略 + 動態權重）          ║
║  🛡️ 完整風險管理（止損/止盈/回撤保護）                  ║
║  📡 Binance Futures API 實時交易                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """顯示功能選單"""
    menu = """
請選擇功能：

0️⃣  📰 查看新聞分析（交易前必看！）
1️⃣  獲取實時價格
2️⃣  查看賬戶信息
3️⃣  開始監控市場（實時 WebSocket + AI 分析）
4️⃣  查看策略權重和表現
5️⃣  查看風險管理統計
6️⃣  切換自動交易模式
7️⃣  切換新聞分析開關
8️⃣  停止監控
9️⃣  保存所有數據並退出

請輸入選項 (0-9): """
    return input(menu).strip()


def main():
    """主程序"""
    print_banner()
    
    # 顯示配置信息
    print("\n📋 當前配置：")
    print(f"   模式: {'🧪 測試網' if USE_TESTNET else '💰 正式網'}")
    print(f"   API 配置: {'✅ 已設置' if BINANCE_API_KEY else '❌ 未設置'}")
    print(f"   策略系統: {'🧠 AI 策略融合' if USE_STRATEGY_FUSION else '📊 簡單策略'}")
    print(f"   自動交易: {'🟢 啟用' if AUTO_TRADE_ENABLED else '🔴 禁用'}")
    print(f"   監控交易對: {', '.join(TRADING_PAIRS)}")
    print(f"   風險管理: 單筆風險 {MAX_RISK_PER_TRADE:.1%} | 每日限制 {MAX_TRADES_PER_DAY} 筆")
    print(f"   最低置信度: {MIN_SIGNAL_CONFIDENCE:.1%}")
    
    # 創建交易器
    print("\n🔧 初始化交易系統...")
    trader = CryptoFuturesTrader(
        api_key=BINANCE_API_KEY,
        api_secret=BINANCE_API_SECRET,
        testnet=USE_TESTNET,
        use_strategy_fusion=USE_STRATEGY_FUSION
    )
    trader.auto_trade = AUTO_TRADE_ENABLED
    
    # 配置風險管理
    trader.risk_manager.max_risk_per_trade = MAX_RISK_PER_TRADE
    trader.risk_manager.max_trades_per_day = MAX_TRADES_PER_DAY
    trader.risk_manager.min_confidence = MIN_SIGNAL_CONFIDENCE
    
    print("✅ 系統初始化完成！\n")
    
    # 主循環
    monitoring_active = False
    
    try:
        while True:
            choice = print_menu()
            
            if choice == "0":
                # 📰 新聞分析
                print("\n" + "=" * 60)
                print("📰 加密貨幣新聞分析")
                print("=" * 60)
                
                for symbol in TRADING_PAIRS:
                    print(f"\n🔍 分析 {symbol} 新聞中...")
                    summary = trader.get_news_summary(symbol)
                    print(summary)
                    
                    # 顯示是否適合交易
                    if trader.news_analyzer:
                        can_trade, reason = trader.news_analyzer.should_trade(symbol)
                        print()
                        if can_trade:
                            print(f"✅ {symbol} 新聞評估: 適合交易")
                        else:
                            print(f"⚠️  {symbol} 新聞評估: 建議暫緩")
                        print(f"   原因: {reason}")
                    
                    print()
            
            elif choice == "1":
                # 獲取實時價格
                print("\n📊 獲取實時價格...")
                for symbol in TRADING_PAIRS:
                    price = trader.get_real_time_price(symbol)
                    if price:
                        print(f"   {symbol}: ${price.price:,.2f}")
                    else:
                        print(f"   {symbol}: 獲取失敗")
                print()
            
            elif choice == "2":
                # 查看賬戶信息
                print("\n💼 賬戶信息...")
                account = trader.get_account_summary()
                print(f"   狀態: {account['status']}")
                print(f"   餘額: ${account['balance']:,.2f} USDT")
                print(f"   持倉數: {len(account['positions'])}")
                print()
            
            elif choice == "3":
                # 開始監控
                if not monitoring_active:
                    print("\n👁️  開始實時監控...")
                    print("   (監控將在後台運行，你可以繼續使用其他功能)")
                    print("   按 Ctrl+C 隨時停止\n")
                    
                    for symbol in TRADING_PAIRS:
                        trader.start_monitoring(symbol)
                    
                    monitoring_active = True
                    print("✅ 監控已啟動\n")
                else:
                    print("\n⚠️  監控已在運行中\n")
            
            elif choice == "4":
                # 查看策略權重和表現
                print("\n⚖️  策略權重和表現報告：")
                if hasattr(trader.strategy, 'weights'):
                    print("\n   當前權重：")
                    for strategy_name, weight in getattr(trader.strategy, 'weights', {}).items():
                        print(f"      • {strategy_name}: {weight:.3f}")
                    
                    print("\n   歷史表現：")
                    if hasattr(trader.strategy, 'get_strategy_report'):
                        report = trader.get_strategy_report()
                        for strategy_name, stats in report.items():
                            if isinstance(stats, dict) and 'total_trades' in stats:
                                print(f"\n      {strategy_name}:")
                                for key, value in stats.items():
                                    print(f"         {key}: {value}")
                else:
                    print("   當前使用簡單策略，無權重系統")
                print()
            
            elif choice == "5":
                # 查看風險管理統計
                print("\n📊 風險管理統計：")
                stats = trader.risk_manager.get_statistics()
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                print()
            
            elif choice == "6":
                # 切換自動交易
                trader.auto_trade = not trader.auto_trade
                status = "🟢 已啟用" if trader.auto_trade else "🔴 已禁用"
                print(f"\n🤖 自動交易模式: {status}")
                if trader.auto_trade:
                    print("⚠️  警告：自動交易已啟用，系統將自動執行交易！")
                    print("   風險管理規則會自動檢查每筆交易")
                print()
            
            elif choice == "7":
                # 切換新聞分析
                if hasattr(trader, 'enable_news_analysis'):
                    trader.set_news_analysis(not trader.enable_news_analysis)
                    status = "🟢 已啟用" if trader.enable_news_analysis else "🔴 已禁用"
                    print(f"\n📰 新聞分析: {status}")
                    if trader.enable_news_analysis:
                        print("   系統將在交易前自動檢查新聞風險")
                else:
                    print("\n⚠️  新聞分析服務不可用")
                print()
            
            elif choice == "8":
                # 停止監控
                if monitoring_active:
                    print("\n⏹️  停止監控...")
                    trader.stop_monitoring()
                    monitoring_active = False
                    print("✅ 監控已停止\n")
                else:
                    print("\n⚠️  監控未啟動\n")
            
            elif choice == "9":
                # 保存並退出
                print("\n💾 正在保存所有數據...")
                if monitoring_active:
                    trader.stop_monitoring()
                trader.save_signals_history()
                print("✅ 所有數據已保存")
                print("\n👋 感謝使用 BioNeuronai 交易系統！")
                print("   數據保存位置: trading_data/")
                break
            
            else:
                print("\n❌ 無效選項，請重試\n")
            
            # 短暫延遲
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  收到中斷信號...")
        print("💾 正在保存數據...")
        trader.save_signals_history()
        print("✅ 數據已保存")
        print("👋 再見！")
    
    except Exception as e:
        logger.error(f"發生錯誤: {e}")
        print(f"\n❌ 錯誤: {e}")


if __name__ == "__main__":
    # 檢查依賴
    try:
        import websocket
        import requests
    except ImportError as e:
        print("❌ 缺少必要的套件！")
        print("\n請執行以下命令安裝：")
        print("   pip install websocket-client requests")
        sys.exit(1)
    
    # 運行主程序
    main()
