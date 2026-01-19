"""
主程序 - 使用重構後的模塊架構
"""

import time
from bioneuronai import TradingEngine


def main():
    """主程序"""
    print("=" * 60)
    print("🚀 BioNeuronai 虛擬貨幣期貨交易系統 v2.0")
    print("   重構版 - 模塊化架構")
    print("=" * 60)
    
    # 創建交易引擎
    trader = TradingEngine(
        api_key="",  # 填入你的 API Key
        api_secret="",  # 填入你的 API Secret
        testnet=True,  # 使用測試網
        strategy_type="fusion",  # 使用策略融合
        risk_config_path=None  # 使用默認風險配置
    )
    
    # 獲取實時價格
    print("\\n📊 獲取實時價格...")
    price_data = trader.get_real_time_price("BTCUSDT")
    if price_data:
        print(f"   BTC/USDT: ${price_data.price:,.2f}")
    
    # 獲取賬戶信息
    print("\\n💼 賬戶信息...")
    account = trader.get_account_summary()
    print(f"   狀態: {account['status']}")
    print(f"   餘額: ${account['balance']:,.2f}")
    
    # 顯示風險設置
    risk_stats = account['risk_stats']
    print(f"\\n⚖️  風險管理設置:")
    print(f"   每筆最大風險: {risk_stats['parameters']['max_risk_per_trade']*100:.1f}%")
    print(f"   每日最大交易: {risk_stats['parameters']['max_trades_per_day']} 筆")
    print(f"   當前回撤: {risk_stats['current_drawdown']}")
    
    # 詢問是否啟用自動交易
    auto_trade_input = input("\\n🤖 是否啟用自動交易？(y/N): ").lower()
    if auto_trade_input == 'y':
        trader.enable_auto_trading()
        print("✅ 自動交易已啟用")
    else:
        print("📊 僅監控模式，不會自動交易")
    
    # 開始監控
    print("\\n👁️  開始實時監控 (按 Ctrl+C 停止)...")
    trader.start_monitoring("BTCUSDT")
    
    # 保持運行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n\\n⏹️  停止監控")
        trader.stop_monitoring()
        trader.save_all_data()
        print("✅ 所有數據已保存")


if __name__ == "__main__":
    main()