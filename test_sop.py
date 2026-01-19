"""
測試 SOP 自動化系統第一步
"""
import sys
sys.path.append('src')
import asyncio
from bioneuronai.sop_automation import SOPAutomationSystem

async def main():
    print('🎯 測試 SOP 第一步：每日開盤前檢查')
    print('=' * 50)
    
    try:
        sop = SOPAutomationSystem()
        print('✅ SOP系統初始化完成')
        
        # 執行檢查
        results = await sop.execute_daily_premarket_check()
        
        print('\n📊 檢查結果摘要:')
        overall = results['overall_assessment']
        print(f'市場狀態: {overall["market_status"]}')
        print(f'系統狀態: {overall["system_status"]}')
        print(f'計劃狀態: {overall["plan_status"]}')
        print(f'綜合評估: {overall["status"]}')
        print(f'建議: {overall["recommendation"]}')
        
        # 生成報告
        report = sop.generate_daily_report()
        print('\n📋 完整報告:')
        print(report)
        
        return True
        
    except Exception as e:
        print(f'❌ 測試失敗: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(main())
    print(f'\n🎯 測試結果: {"✅ 成功" if result else "❌ 失敗"}')