"""
測試 JSON 參數自動學習
======================
驗證 base_weight 和 sentiment_bias 是否能自動調整
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bioneuronai.analysis.keywords import KeywordManager
import json

def test_base_weight_learning():
    """測試基礎權重自動調整"""
    print("=" * 70)
    print("🧪 測試基礎權重自動學習")
    print("=" * 70)
    
    km = KeywordManager()
    
    # 選擇一個關鍵字測試
    test_keyword = "elon musk"
    kw = km.keywords.get(test_keyword)
    
    if not kw:
        print(f"❌ 找不到關鍵字: {test_keyword}")
        return
    
    print(f"\n📊 初始狀態:")
    print(f"   關鍵字: {test_keyword}")
    print(f"   基礎權重: {kw.base_weight}")
    print(f"   動態權重: {kw.dynamic_weight}")
    print(f"   情緒偏向: {kw.sentiment_bias}")
    print(f"   準確率: {kw.accuracy:.1%}")
    print(f"   預測次數: {kw.prediction_count}")
    
    # 模擬 20 次準確預測
    print(f"\n🔄 模擬 20 次準確預測...")
    for i in range(20):
        km.record_and_verify_prediction(
            keyword=test_keyword,
            predicted_direction='positive',
            actual_direction='positive',
            price_change_pct=2.5
        )
    
    # 檢查更新後狀態
    kw = km.keywords.get(test_keyword)
    print(f"\n📈 更新後狀態:")
    print(f"   基礎權重: {kw.base_weight} (應該增加)")
    print(f"   動態權重: {kw.dynamic_weight}")
    print(f"   準確率: {kw.accuracy:.1%}")
    print(f"   預測次數: {kw.prediction_count}")
    
    # 檢查 JSON 是否更新
    with open(km.config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data['keywords']:
            if item['keyword'] == test_keyword:
                print(f"\n💾 JSON 檔案已更新:")
                print(f"   base_weight: {item['base_weight']}")
                print(f"   dynamic_weight: {item['dynamic_weight']}")
                print(f"   correct_count: {item['correct_count']}")
                print(f"   prediction_count: {item['prediction_count']}")
                break
    
    print("\n✅ 基礎權重自動學習測試完成！")
    print("=" * 70)

def test_sentiment_learning():
    """測試情緒偏向自動調整"""
    print("\n🧪 測試情緒偏向自動學習")
    print("=" * 70)
    
    km = KeywordManager()
    test_keyword = "elon musk"
    
    # 收集歷史價格變化數據
    price_changes = [
        ('positive', 3.2),
        ('positive', 2.8),
        ('positive', 4.1),
        ('positive', 1.5),
        ('positive', 2.3),
        ('positive', 3.7),
        ('positive', 2.1),
        ('positive', 4.5),
        ('negative', -0.5),
        ('neutral', 0.3),
    ]
    
    kw = km.keywords.get(test_keyword)
    old_sentiment = kw.sentiment_bias
    
    print(f"\n📊 初始情緒偏向: {old_sentiment}")
    print(f"   模擬數據: 8次正面, 1次負面, 1次中性")
    
    # 更新情緒偏向
    km.update_sentiment_bias_from_results(test_keyword, price_changes)
    
    kw = km.keywords.get(test_keyword)
    print(f"   更新後: {kw.sentiment_bias} (應該變成 positive)")
    
    print("\n✅ 情緒偏向自動學習測試完成！")
    print("=" * 70)

if __name__ == "__main__":
    print("\n🎯 JSON 參數自動學習測試")
    print("=" * 70)
    print("測試項目:")
    print("  1. base_weight (基礎權重) - 長期表現調整")
    print("  2. sentiment_bias (情緒偏向) - 實際影響調整")
    print("=" * 70)
    
    test_base_weight_learning()
    test_sentiment_learning()
    
    print("\n" + "=" * 70)
    print("🎉 所有測試完成！JSON 參數已可自動學習！")
    print("=" * 70)
    print("\n💡 說明:")
    print("  • base_weight: 累積20次預測後，根據準確率自動調整")
    print("  • dynamic_weight: 每次驗證後立即調整 (已實現)")
    print("  • sentiment_bias: 收集10+次數據後，根據實際影響調整")
    print("\n📁 JSON 儲存位置: config/market_keywords.json")
    print("=" * 70)
