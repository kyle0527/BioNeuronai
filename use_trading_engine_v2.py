"""
 - 
"""

import time
from bioneuronai import TradingEngine


def main():
    """"""
    print("=" * 60)
    print(" BioNeuronai  v2.0")
    print("    - ")
    print("=" * 60)
    
    # 
    trader = TradingEngine(
        api_key="",  #  API Key
        api_secret="",  #  API Secret
        testnet=True,  # 
        strategy_type="fusion",  # 
        risk_config_path=None  # 
    )
    
    # 
    print("\\n ...")
    price_data = trader.get_real_time_price("BTCUSDT")
    if price_data:
        print(f"   BTC/USDT: ${price_data.price:,.2f}")
    
    # 
    print("\\n ...")
    account = trader.get_account_summary()
    print(f"   : {account['status']}")
    print(f"   : ${account['balance']:,.2f}")
    
    # 
    risk_stats = account['risk_stats']
    print(f"\\n  :")
    print(f"   : {risk_stats['parameters']['max_risk_per_trade']*100:.1f}%")
    print(f"   : {risk_stats['parameters']['max_trades_per_day']} ")
    print(f"   : {risk_stats['current_drawdown']}")
    
    # 
    auto_trade_input = input("\\n🤖 (y/N): ").lower()
    if auto_trade_input == 'y':
        trader.enable_auto_trading()
        print(" ")
    else:
        print(" ")
    
    # 
    print("\\n   ( Ctrl+C )...")
    trader.start_monitoring("BTCUSDT")
    
    # 
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n\\n⏹  ")
        trader.stop_monitoring()
        trader.save_all_data()
        print("[] ")


if __name__ == "__main__":
    main()