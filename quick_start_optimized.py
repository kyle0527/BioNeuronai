#!/usr/bin/env python3
"""
快速啟動 BioNeuronAI - Jules Session 整合版
============================================

整合 Jules Session 優化配置後的快速測試腳本
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_optimized_config():
    """測試優化配置"""
    print("🔧 測試 Jules Session 優化配置...")
    
    # 測試優化的風險配置
    try:
        import json
        risk_config_path = Path(__file__).parent / "trading_data_optimized" / "risk_config_optimized.json"
        if risk_config_path.exists():
            with open(risk_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"✅ 優化風險配置載入成功:")
                print(f"   - 最大風險: {config['max_risk_per_trade']*100}%")
                print(f"   - 止盈目標: {config['default_take_profit']*100}%")
                print(f"   - 最大倉位: {config['max_position_ratio']*100}%")
        else:
            print("❌ 優化配置文件不存在")
    except Exception as e:
        print(f"❌ 配置載入失敗: {e}")

def test_system_modules():
    """測試系統模組"""
    print("\n🧠 測試 BioNeuronAI 系統模組...")
    
    try:
        from bioneuronai import TradingEngine
        print("✅ 交易引擎模組載入成功")
        
        # 創建測試引擎
        engine = TradingEngine(testnet=True)
        print("✅ 交易引擎初始化成功")
        
        # 測試價格獲取
        price_data = engine.get_real_time_price("BTCUSDT")
        if price_data:
            print(f"✅ 價格獲取成功: {price_data.symbol} ${price_data.price:.2f}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模組載入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 系統測試失敗: {e}")
        return False

def run_simulation_test():
    """運行模擬測試"""
    print("\n🎯 啟動模擬交易測試...")
    
    try:
        # 導入優化的模擬環境
        simulation_path = Path(__file__).parent / "simulate_trading_environment_optimized.py"
        if simulation_path.exists():
            print("✅ 找到優化的模擬環境")
            print("💡 要運行完整模擬，請執行:")
            print(f"   python {simulation_path}")
        else:
            print("❌ 模擬環境文件不存在")
            
    except Exception as e:
        print(f"❌ 模擬測試失敗: {e}")

def main():
    """主函數"""
    print("="*60)
    print("🚀 BioNeuronAI - Jules Session 整合版快速測試")
    print("   版本: 2026-01-28 優化版")
    print("="*60)
    
    # 1. 測試配置
    test_optimized_config()
    
    # 2. 測試系統模組
    success = test_system_modules()
    
    # 3. 模擬測試準備
    run_simulation_test()
    
    print("\n" + "="*60)
    if success:
        print("🎉 Jules Session 整合測試完成 - 系統就緒!")
        print("💡 下一步:")
        print("   1. 配置 config/trading_config.py 中的 API 金鑰")
        print("   2. 運行 simulate_trading_environment_optimized.py 進行模擬")
        print("   3. 啟動實際交易 (建議先使用測試網)")
    else:
        print("⚠️  系統測試未完全通過，請檢查依賴和配置")
    print("="*60)

if __name__ == "__main__":
    main()