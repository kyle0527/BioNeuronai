"""
測試 SOP 第二步：單筆交易前檢查
"""
import sys
sys.path.append('src')
import asyncio
from bioneuronai.pretrade_automation import PreTradeCheckSystem

async def main():
    print('🎯 測試 SOP 第二步：單筆交易前檢查')
    print('=' * 60)
    
    try:
        pretrade = PreTradeCheckSystem()
        print('✅ 交易前檢查系統初始化完成')
        
        # 測試多種情況
        test_cases = [
            {
                "symbol": "BTCUSDT",
                "action": "BUY",
                "source": "AI_FUSION"
            },
            {
                "symbol": "ETHUSDT", 
                "action": "SELL",
                "source": "RSI_DIVERGENCE"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f'\n🧪 測試案例 {i}: {test_case["symbol"]} {test_case["action"]}')
            print('-' * 40)
            
            # 執行檢查
            results = await pretrade.execute_pretrade_check(
                symbol=test_case["symbol"],
                signal_source=test_case["source"],
                intended_action=test_case["action"]
            )
            
            # 顯示結果
            assessment = results['overall_assessment']
            print(f'📊 綜合評分: {assessment["score_percentage"]:.1f}%')
            print(f'🎯 最終決策: {assessment["status"]}')
            print(f'💡 建議: {assessment["recommendation"]}')
            
            # 詳細分析
            print(f'   技術分析: {assessment["technical_status"]}')
            print(f'   基本面: {assessment["fundamental_status"]}')
            print(f'   風險評估: {assessment["risk_status"]}')
            print(f'   訂單參數: {assessment["order_status"]}')
            print(f'   最終確認: {assessment["final_status"]}')
        
        return True
        
    except Exception as e:
        print(f'❌ 測試失敗: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(main())
    print(f'\n🎯 SOP第二步測試結果: {"✅ 成功" if result else "❌ 失敗"}')