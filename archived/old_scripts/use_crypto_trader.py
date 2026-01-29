"""
 - 
========================================
"""

import sys
import time
from pathlib import Path

# 
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 
from src.bioneuronai import CryptoFuturesTrader
import logging

logger = logging.getLogger(__name__)

# 
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
    # 
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
    """"""
    banner = """

                                                          
         BioNeuronai              
                                                          
  🧠  AI  +           
   //                  
   Binance Futures API                          
                                                          

    """
    print(banner)


def print_menu():
    """"""
    menu = """


0⃣   
1⃣  
2⃣  
3⃣   WebSocket + AI 
4⃣  
5⃣  
6⃣  
7⃣  
8⃣  
9⃣  

 (0-9): """
    return input(menu).strip()


def main():
    """"""
    print_banner()
    
    # 
    print("\n ")
    print(f"   : {'🧪 ' if USE_TESTNET else ' '}")
    print(f"   API : {' ' if BINANCE_API_KEY else ' '}")
    print(f"   : {'🧠 AI ' if USE_STRATEGY_FUSION else ' '}")
    print(f"   : {'🟢 ' if AUTO_TRADE_ENABLED else ' '}")
    print(f"   : {', '.join(TRADING_PAIRS)}")
    print(f"   :  {MAX_RISK_PER_TRADE:.1%} |  {MAX_TRADES_PER_DAY} ")
    print(f"   : {MIN_SIGNAL_CONFIDENCE:.1%}")
    
    # 
    print("\n ...")
    trader = CryptoFuturesTrader(
        api_key=BINANCE_API_KEY,
        api_secret=BINANCE_API_SECRET,
        testnet=USE_TESTNET,
        use_strategy_fusion=USE_STRATEGY_FUSION
    )
    trader.auto_trade = AUTO_TRADE_ENABLED
    
    # 
    trader.risk_manager.max_risk_per_trade = MAX_RISK_PER_TRADE
    trader.risk_manager.max_trades_per_day = MAX_TRADES_PER_DAY
    trader.risk_manager.min_confidence = MIN_SIGNAL_CONFIDENCE
    
    print(" \n")
    
    # 
    monitoring_active = False
    
    try:
        while True:
            choice = print_menu()
            
            if choice == "0":
                #  
                print("\n" + "=" * 60)
                print(" ")
                print("=" * 60)
                
                for symbol in TRADING_PAIRS:
                    print(f"\n  {symbol} ...")
                    summary = trader.get_news_summary(symbol)
                    print(summary)
                    
                    # 
                    if trader.news_analyzer:
                        can_trade, reason = trader.news_analyzer.should_trade(symbol)
                        print()
                        if can_trade:
                            print(f" {symbol} : ")
                        else:
                            print(f"  {symbol} : ")
                        print(f"   : {reason}")
                    
                    print()
            
            elif choice == "1":
                # 
                print("\n ...")
                for symbol in TRADING_PAIRS:
                    price = trader.get_real_time_price(symbol)
                    if price:
                        print(f"   {symbol}: ${price.price:,.2f}")
                    else:
                        print(f"   {symbol}: ")
                print()
            
            elif choice == "2":
                # 
                print("\n ...")
                account = trader.get_account_summary()
                print(f"   : {account['status']}")
                print(f"   : ${account['balance']:,.2f} USDT")
                print(f"   : {len(account['positions'])}")
                print()
            
            elif choice == "3":
                # 
                if not monitoring_active:
                    print("\n  ...")
                    print("   ()")
                    print("    Ctrl+C \n")
                    
                    for symbol in TRADING_PAIRS:
                        trader.start_monitoring(symbol)
                    
                    monitoring_active = True
                    print(" \n")
                else:
                    print("\n  \n")
            
            elif choice == "4":
                # 
                print("\n  ")
                if hasattr(trader.strategy, 'weights'):
                    print("\n   ")
                    for strategy_name, weight in getattr(trader.strategy, 'weights', {}).items():
                        print(f"      • {strategy_name}: {weight:.3f}")
                    
                    print("\n   ")
                    if hasattr(trader.strategy, 'get_strategy_report'):
                        report = trader.get_strategy_report()
                        for strategy_name, stats in report.items():
                            if isinstance(stats, dict) and 'total_trades' in stats:
                                print(f"\n      {strategy_name}:")
                                for key, value in stats.items():
                                    print(f"         {key}: {value}")
                else:
                    print("   ")
                print()
            
            elif choice == "5":
                # 
                print("\n ")
                stats = trader.risk_manager.get_statistics()
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                print()
            
            elif choice == "6":
                # 
                trader.auto_trade = not trader.auto_trade
                status = "🟢 " if trader.auto_trade else " "
                print(f"\n🤖 : {status}")
                if trader.auto_trade:
                    print("  ")
                    print("   ")
                print()
            
            elif choice == "7":
                # 
                if hasattr(trader, 'enable_news_analysis'):
                    trader.set_news_analysis(not trader.enable_news_analysis)
                    status = "🟢 " if trader.enable_news_analysis else " "
                    print(f"\n : {status}")
                    if trader.enable_news_analysis:
                        print("   ")
                else:
                    print("\n  ")
                print()
            
            elif choice == "8":
                # 
                if monitoring_active:
                    print("\n⏹  ...")
                    trader.stop_monitoring()
                    monitoring_active = False
                    print(" \n")
                else:
                    print("\n  \n")
            
            elif choice == "9":
                # 
                print("\n ...")
                if monitoring_active:
                    trader.stop_monitoring()
                trader.save_signals_history()
                print(" ")
                print("\n  BioNeuronai ")
                print("   : trading_data/")
                break
            
            else:
                print("\n \n")
            
            # 
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n⏹  ...")
        print(" ...")
        trader.save_signals_history()
        print(" ")
        print(" ")
    
    except Exception as e:
        logger.error(f": {e}")
        print(f"\n : {e}")


if __name__ == "__main__":
    # 
    try:
        import websocket
        import requests
    except ImportError as e:
        print(" ")
        print("\n")
        print("   pip install websocket-client requests")
        sys.exit(1)
    
    # 
    main()
