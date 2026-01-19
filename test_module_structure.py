"""
測試新的模組化架構
"""
import sys
sys.path.append('src')

def test_imports():
    """測試所有模組是否能正常導入"""
    print('🧪 測試模組化架構導入...')
    print('=' * 60)
    
    try:
        # 測試核心模組
        print('\n📦 測試 core 模組...')
        from bioneuronai.core import TradingEngine, SelfImprovementSystem
        print('✅ core.TradingEngine')
        print('✅ core.SelfImprovementSystem')
        
        # 測試分析模組
        print('\n📦 測試 analysis 模組...')
        from bioneuronai.analysis import CryptoNewsAnalyzer, MarketKeywords
        print('✅ analysis.CryptoNewsAnalyzer')
        print('✅ analysis.MarketKeywords')
        
        # 測試自動化模組
        print('\n📦 測試 automation 模組...')
        from bioneuronai.automation import SOPAutomation, PreTradeAutomation
        print('✅ automation.SOPAutomation')
        print('✅ automation.PreTradeAutomation')
        
        # 測試服務模組
        print('\n📦 測試 services 模組...')
        from bioneuronai.services import TradingDatabase, ExchangeRateService
        print('✅ services.TradingDatabase')
        print('✅ services.ExchangeRateService')
        
        # 測試計劃模組
        print('\n📦 測試 planning 模組...')
        from bioneuronai.planning import TradingPlanGenerator
        print('✅ planning.TradingPlanGenerator')
        
        # 測試主模組導入
        print('\n📦 測試主模組導入...')
        from bioneuronai import (
            TradingEngine as TE,
            CryptoNewsAnalyzer as CNA,
            SOPAutomation as SOPA,
            TradingDatabase as DB,
            TradingPlanGenerator as TPG
        )
        print('✅ 從 bioneuronai 主模組導入')
        
        # 測試向後兼容別名
        print('\n📦 測試向後兼容性...')
        from bioneuronai import CryptoFuturesTrader
        from bioneuronai.services import Database
        print('✅ CryptoFuturesTrader (別名)')
        print('✅ Database (別名)')
        
        print('\n' + '=' * 60)
        print('🎉 所有模組導入測試通過！')
        print('🏗️  新架構結構：')
        print('   ├── core/       (核心引擎)')
        print('   ├── analysis/   (分析服務)')
        print('   ├── automation/ (自動化)')
        print('   ├── services/   (外部服務)')
        print('   └── planning/   (計劃系統)')
        return True
        
    except Exception as e:
        print(f'\n❌ 導入失敗: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
