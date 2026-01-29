"""
拆分關鍵字 JSON 檔案
將單一 market_keywords.json 拆分為按類別的多個檔案
"""

import json
from datetime import datetime
from pathlib import Path

def split_keywords():
    """將單一 JSON 拆分為多個類別檔案"""
    
    # 讀取原始檔案
    source_path = Path(__file__).parent.parent / 'config' / 'market_keywords.json'
    target_dir = Path(__file__).parent.parent / 'config' / 'keywords'
    target_dir.mkdir(parents=True, exist_ok=True)
    
    with open(source_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"讀取 {len(data['keywords'])} 個關鍵字")
    
    # 按類別分組
    categories = {}
    for kw in data['keywords']:
        cat = kw['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(kw)
    
    # 寫入各類別檔案
    for cat, keywords in categories.items():
        cat_file = target_dir / f"{cat}.json"
        cat_data = {
            "category": cat,
            "description": get_category_description(cat),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(keywords),
            "keywords": keywords
        }
        
        with open(cat_file, 'w', encoding='utf-8') as f:
            json.dump(cat_data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ {cat}.json: {len(keywords)} 個關鍵字")
    
    # 建立索引檔
    index_data = {
        "version": "3.0",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_keywords": len(data['keywords']),
        "categories": {
            cat: {
                "file": f"{cat}.json",
                "count": len(kws),
                "description": get_category_description(cat)
            }
            for cat, kws in categories.items()
        }
    }
    
    index_file = target_dir / "_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 拆分完成！共 {len(categories)} 個類別檔案")
    print(f"   目錄: {target_dir}")
    
    return categories

def get_category_description(cat: str) -> str:
    """獲取類別描述"""
    descriptions = {
        "person": "人物 - 幣圈領袖、Fed官員、政治人物、分析師等",
        "institution": "機構 - 央行、監管機構、交易所、基金、銀行等",
        "macro": "總體經濟 - 貨幣政策、經濟數據、財政政策、全球事件等",
        "legislation": "法規法案 - 美國法案、國際法規、稅務政策等",
        "event": "事件 - 市場動態、安全事件、採用事件、法律行動等",
        "coin": "幣種 - 主流幣、山寨幣、穩定幣等",
        "tech": "技術 - AI、區塊鏈技術等"
    }
    return descriptions.get(cat, cat)

if __name__ == '__main__':
    split_keywords()
