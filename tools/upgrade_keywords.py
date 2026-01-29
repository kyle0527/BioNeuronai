"""
關鍵字分類架構升級腳本
將現有關鍵字重新分類，並添加新的 macro/legislation 類別
"""

import json
from datetime import datetime
from pathlib import Path

# 定義分類映射規則
CATEGORY_MAPPING = {
    # ===== person 子分類 =====
    'elon musk': ('person', 'tech_ceo'),
    'musk': ('person', 'tech_ceo'),
    'vitalik': ('person', 'crypto_leader'),
    'vitalik buterin': ('person', 'crypto_leader'),
    'cz': ('person', 'crypto_leader'),
    'changpeng zhao': ('person', 'crypto_leader'),
    'michael saylor': ('person', 'crypto_leader'),
    'saylor': ('person', 'crypto_leader'),
    'brian armstrong': ('person', 'crypto_leader'),
    'sam bankman-fried': ('person', 'crypto_leader'),
    'sbf': ('person', 'crypto_leader'),
    'gary gensler': ('person', 'regulator_official'),
    'gensler': ('person', 'regulator_official'),
    'jerome powell': ('person', 'fed_official'),
    'powell': ('person', 'fed_official'),
    'janet yellen': ('person', 'fed_official'),
    'yellen': ('person', 'fed_official'),
    'trump': ('person', 'politician'),
    'donald trump': ('person', 'politician'),
    'biden': ('person', 'politician'),
    'cathie wood': ('person', 'fund_manager'),
    'larry fink': ('person', 'fund_manager'),
    
    # ===== institution 子分類 =====
    'fed': ('institution', 'central_bank'),
    'federal reserve': ('institution', 'central_bank'),
    'fomc': ('institution', 'central_bank'),
    'ecb': ('institution', 'central_bank'),
    'boj': ('institution', 'central_bank'),
    'pboc': ('institution', 'central_bank'),
    'sec': ('institution', 'regulator'),
    'cftc': ('institution', 'regulator'),
    'doj': ('institution', 'regulator'),
    'fbi': ('institution', 'regulator'),
    'fdic': ('institution', 'regulator'),
    'occ': ('institution', 'regulator'),
    'finra': ('institution', 'regulator'),
    'binance': ('institution', 'exchange'),
    'coinbase': ('institution', 'exchange'),
    'kraken': ('institution', 'exchange'),
    'okx': ('institution', 'exchange'),
    'ftx': ('institution', 'exchange'),
    'bybit': ('institution', 'exchange'),
    'blackrock': ('institution', 'fund'),
    'ark invest': ('institution', 'fund'),
    'grayscale': ('institution', 'fund'),
    'fidelity': ('institution', 'fund'),
    'microstrategy': ('institution', 'fund'),
    'jpmorgan': ('institution', 'bank'),
    'goldman sachs': ('institution', 'bank'),
    'morgan stanley': ('institution', 'bank'),
    'bank of america': ('institution', 'bank'),
    'citibank': ('institution', 'bank'),
    
    # ===== event -> market =====
    'rally': ('event', 'market'),
    'crash': ('event', 'market'),
    'dump': ('event', 'market'),
    'pump': ('event', 'market'),
    'correction': ('event', 'market'),
    'bull run': ('event', 'market'),
    'bear market': ('event', 'market'),
    'all-time high': ('event', 'market'),
    'ath': ('event', 'market'),
    'breakout': ('event', 'market'),
    'support': ('event', 'market'),
    'resistance': ('event', 'market'),
    'liquidation': ('event', 'market'),
    'short squeeze': ('event', 'market'),
    'accumulation': ('event', 'market'),
    'distribution': ('event', 'market'),
    
    # ===== event -> security =====
    'hack': ('event', 'security'),
    'hacked': ('event', 'security'),
    'exploit': ('event', 'security'),
    'rug pull': ('event', 'security'),
    'scam': ('event', 'security'),
    'fraud': ('event', 'security'),
    'breach': ('event', 'security'),
    'vulnerability': ('event', 'security'),
    'stolen': ('event', 'security'),
    
    # ===== event -> adoption =====
    'etf approved': ('event', 'adoption'),
    'etf approval': ('event', 'adoption'),
    'etf rejected': ('event', 'adoption'),
    'etf filing': ('event', 'adoption'),
    'partnership': ('event', 'adoption'),
    'listing': ('event', 'adoption'),
    'delisting': ('event', 'adoption'),
    'adoption': ('event', 'adoption'),
    'institutional': ('event', 'adoption'),
    'integration': ('event', 'adoption'),
    
    # ===== event -> legal_action =====
    'lawsuit': ('event', 'legal_action'),
    'sued': ('event', 'legal_action'),
    'settlement': ('event', 'legal_action'),
    'fine': ('event', 'legal_action'),
    'penalty': ('event', 'legal_action'),
    'investigation': ('event', 'legal_action'),
    'subpoena': ('event', 'legal_action'),
    'indictment': ('event', 'legal_action'),
    'charges': ('event', 'legal_action'),
    'arrest': ('event', 'legal_action'),
    'convicted': ('event', 'legal_action'),
    
    # ===== macro -> monetary_policy =====
    'rate hike': ('macro', 'monetary_policy'),
    'rate cut': ('macro', 'monetary_policy'),
    'interest rate': ('macro', 'monetary_policy'),
    'quantitative easing': ('macro', 'monetary_policy'),
    'qe': ('macro', 'monetary_policy'),
    'quantitative tightening': ('macro', 'monetary_policy'),
    'qt': ('macro', 'monetary_policy'),
    'hawkish': ('macro', 'monetary_policy'),
    'dovish': ('macro', 'monetary_policy'),
    'pivot': ('macro', 'monetary_policy'),
    'tapering': ('macro', 'monetary_policy'),
    'balance sheet': ('macro', 'monetary_policy'),
    'monetary policy': ('macro', 'monetary_policy'),
    
    # ===== macro -> economic_data =====
    'cpi': ('macro', 'economic_data'),
    'inflation': ('macro', 'economic_data'),
    'ppi': ('macro', 'economic_data'),
    'gdp': ('macro', 'economic_data'),
    'unemployment': ('macro', 'economic_data'),
    'jobs report': ('macro', 'economic_data'),
    'nonfarm': ('macro', 'economic_data'),
    'nfp': ('macro', 'economic_data'),
    'retail sales': ('macro', 'economic_data'),
    'pce': ('macro', 'economic_data'),
    'consumer confidence': ('macro', 'economic_data'),
    'housing': ('macro', 'economic_data'),
    
    # ===== macro -> fiscal_policy =====
    'stimulus': ('macro', 'fiscal_policy'),
    'debt ceiling': ('macro', 'fiscal_policy'),
    'government shutdown': ('macro', 'fiscal_policy'),
    'budget': ('macro', 'fiscal_policy'),
    'treasury': ('macro', 'fiscal_policy'),
    
    # ===== macro -> global_event =====
    'recession': ('macro', 'global_event'),
    'trade war': ('macro', 'global_event'),
    'tariff': ('macro', 'global_event'),
    'tariffs': ('macro', 'global_event'),
    'sanctions': ('macro', 'global_event'),
    'geopolitical': ('macro', 'global_event'),
    'war': ('macro', 'global_event'),
    'banking crisis': ('macro', 'global_event'),
    'bank failure': ('macro', 'global_event'),
    'default': ('macro', 'global_event'),
    
    # ===== legislation -> us_law =====
    'regulation': ('legislation', 'us_law'),
    'fit21': ('legislation', 'us_law'),
    'stablecoin act': ('legislation', 'us_law'),
    'infrastructure bill': ('legislation', 'us_law'),
    'crypto bill': ('legislation', 'us_law'),
    'howey test': ('legislation', 'us_law'),
    'securities act': ('legislation', 'us_law'),
    
    # ===== legislation -> global_law =====
    'mica': ('legislation', 'global_law'),
    'travel rule': ('legislation', 'global_law'),
    'ban': ('legislation', 'global_law'),
    'aml': ('legislation', 'global_law'),
    'kyc': ('legislation', 'global_law'),
    
    # ===== legislation -> tax_policy =====
    'capital gains': ('legislation', 'tax_policy'),
    'tax': ('legislation', 'tax_policy'),
    'irs': ('legislation', 'tax_policy'),
    'reporting': ('legislation', 'tax_policy'),
    
    # ===== coin 子分類 =====
    'bitcoin': ('coin', 'major'),
    'btc': ('coin', 'major'),
    'ethereum': ('coin', 'major'),
    'eth': ('coin', 'major'),
    'solana': ('coin', 'altcoin'),
    'sol': ('coin', 'altcoin'),
    'dogecoin': ('coin', 'altcoin'),
    'doge': ('coin', 'altcoin'),
    'xrp': ('coin', 'altcoin'),
    'ripple': ('coin', 'altcoin'),
    'cardano': ('coin', 'altcoin'),
    'ada': ('coin', 'altcoin'),
    'avalanche': ('coin', 'altcoin'),
    'avax': ('coin', 'altcoin'),
    'polygon': ('coin', 'altcoin'),
    'matic': ('coin', 'altcoin'),
    'usdt': ('coin', 'stablecoin'),
    'usdc': ('coin', 'stablecoin'),
    'tether': ('coin', 'stablecoin'),
    'dai': ('coin', 'stablecoin'),
    
    # ===== tech 子分類 =====
    'ai': ('tech', 'ai'),
    'artificial intelligence': ('tech', 'ai'),
    'layer 2': ('tech', 'blockchain'),
    'layer2': ('tech', 'blockchain'),
    'l2': ('tech', 'blockchain'),
    'rollup': ('tech', 'blockchain'),
    'scaling': ('tech', 'blockchain'),
    'halving': ('tech', 'blockchain'),
    'merge': ('tech', 'blockchain'),
    'upgrade': ('tech', 'blockchain'),
    'fork': ('tech', 'blockchain'),
    'defi': ('tech', 'blockchain'),
    'nft': ('tech', 'blockchain'),
}

# 新增關鍵字（現有 JSON 中缺少的重要詞彙）
NEW_KEYWORDS = [
    # macro - monetary_policy
    {"keyword": "fomc meeting", "category": "macro", "subcategory": "monetary_policy", "base_weight": 3.0, "sentiment_bias": "uncertain", "description": "聯準會利率決議會議"},
    {"keyword": "fed minutes", "category": "macro", "subcategory": "monetary_policy", "base_weight": 2.5, "sentiment_bias": "uncertain", "description": "聯準會會議紀要"},
    {"keyword": "dot plot", "category": "macro", "subcategory": "monetary_policy", "base_weight": 2.5, "sentiment_bias": "uncertain", "description": "聯準會利率點陣圖"},
    {"keyword": "jackson hole", "category": "macro", "subcategory": "monetary_policy", "base_weight": 2.5, "sentiment_bias": "uncertain", "description": "傑克森霍爾央行年會"},
    
    # macro - economic_data
    {"keyword": "core cpi", "category": "macro", "subcategory": "economic_data", "base_weight": 2.5, "sentiment_bias": "uncertain", "description": "核心消費者物價指數"},
    {"keyword": "core pce", "category": "macro", "subcategory": "economic_data", "base_weight": 2.5, "sentiment_bias": "uncertain", "description": "核心個人消費支出"},
    {"keyword": "initial claims", "category": "macro", "subcategory": "economic_data", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "初請失業金人數"},
    {"keyword": "ism", "category": "macro", "subcategory": "economic_data", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "製造業/服務業PMI"},
    
    # macro - fiscal_policy
    {"keyword": "debt limit", "category": "macro", "subcategory": "fiscal_policy", "base_weight": 2.5, "sentiment_bias": "negative", "description": "債務上限"},
    {"keyword": "fiscal cliff", "category": "macro", "subcategory": "fiscal_policy", "base_weight": 2.5, "sentiment_bias": "negative", "description": "財政懸崖"},
    
    # macro - global_event
    {"keyword": "risk off", "category": "macro", "subcategory": "global_event", "base_weight": 2.0, "sentiment_bias": "negative", "description": "避險情緒"},
    {"keyword": "risk on", "category": "macro", "subcategory": "global_event", "base_weight": 2.0, "sentiment_bias": "positive", "description": "風險偏好"},
    {"keyword": "flight to safety", "category": "macro", "subcategory": "global_event", "base_weight": 2.0, "sentiment_bias": "negative", "description": "資金逃向安全資產"},
    {"keyword": "contagion", "category": "macro", "subcategory": "global_event", "base_weight": 2.5, "sentiment_bias": "negative", "description": "風險蔓延"},
    {"keyword": "systemic risk", "category": "macro", "subcategory": "global_event", "base_weight": 2.5, "sentiment_bias": "negative", "description": "系統性風險"},
    
    # legislation - us_law
    {"keyword": "sab 121", "category": "legislation", "subcategory": "us_law", "base_weight": 2.5, "sentiment_bias": "negative", "description": "SEC銀行託管加密資產規則"},
    {"keyword": "wells notice", "category": "legislation", "subcategory": "us_law", "base_weight": 2.5, "sentiment_bias": "negative", "description": "SEC執法預告"},
    {"keyword": "defi regulation", "category": "legislation", "subcategory": "us_law", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "DeFi監管"},
    {"keyword": "staking regulation", "category": "legislation", "subcategory": "us_law", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "質押監管"},
    
    # legislation - global_law
    {"keyword": "cbdc", "category": "legislation", "subcategory": "global_law", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "央行數位貨幣"},
    {"keyword": "digital euro", "category": "legislation", "subcategory": "global_law", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "數位歐元"},
    {"keyword": "digital yuan", "category": "legislation", "subcategory": "global_law", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "數位人民幣"},
    
    # event - adoption
    {"keyword": "spot etf", "category": "event", "subcategory": "adoption", "base_weight": 3.0, "sentiment_bias": "positive", "description": "現貨ETF"},
    {"keyword": "futures etf", "category": "event", "subcategory": "adoption", "base_weight": 2.5, "sentiment_bias": "positive", "description": "期貨ETF"},
    {"keyword": "etf inflow", "category": "event", "subcategory": "adoption", "base_weight": 2.5, "sentiment_bias": "positive", "description": "ETF資金流入"},
    {"keyword": "etf outflow", "category": "event", "subcategory": "adoption", "base_weight": 2.5, "sentiment_bias": "negative", "description": "ETF資金流出"},
    {"keyword": "whale", "category": "event", "subcategory": "adoption", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "巨鯨"},
    {"keyword": "accumulation", "category": "event", "subcategory": "market", "base_weight": 2.0, "sentiment_bias": "positive", "description": "吸籌"},
    
    # event - market
    {"keyword": "golden cross", "category": "event", "subcategory": "market", "base_weight": 2.0, "sentiment_bias": "positive", "description": "黃金交叉"},
    {"keyword": "death cross", "category": "event", "subcategory": "market", "base_weight": 2.0, "sentiment_bias": "negative", "description": "死亡交叉"},
    {"keyword": "capitulation", "category": "event", "subcategory": "market", "base_weight": 2.5, "sentiment_bias": "negative", "description": "恐慌性拋售"},
    {"keyword": "fomo", "category": "event", "subcategory": "market", "base_weight": 2.0, "sentiment_bias": "positive", "description": "錯失恐懼"},
    {"keyword": "fud", "category": "event", "subcategory": "market", "base_weight": 2.0, "sentiment_bias": "negative", "description": "恐懼、不確定、懷疑"},
    
    # tech - ai
    {"keyword": "ai agent", "category": "tech", "subcategory": "ai", "base_weight": 2.0, "sentiment_bias": "positive", "description": "AI代理"},
    {"keyword": "deepseek", "category": "tech", "subcategory": "ai", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "DeepSeek AI"},
    {"keyword": "chatgpt", "category": "tech", "subcategory": "ai", "base_weight": 1.5, "sentiment_bias": "uncertain", "description": "ChatGPT"},
    
    # person - fed_official
    {"keyword": "waller", "category": "person", "subcategory": "fed_official", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "Fed理事沃勒"},
    {"keyword": "bostic", "category": "person", "subcategory": "fed_official", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "亞特蘭大Fed主席博斯蒂克"},
    {"keyword": "kashkari", "category": "person", "subcategory": "fed_official", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "明尼亞波利斯Fed主席卡什卡利"},
    
    # institution - central_bank
    {"keyword": "bank of japan", "category": "institution", "subcategory": "central_bank", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "日本央行"},
    {"keyword": "bank of england", "category": "institution", "subcategory": "central_bank", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "英國央行"},
    {"keyword": "boe", "category": "institution", "subcategory": "central_bank", "base_weight": 2.0, "sentiment_bias": "uncertain", "description": "英國央行"},
]

def upgrade_keywords():
    """升級關鍵字分類"""
    json_path = Path(__file__).parent.parent / 'config' / 'market_keywords.json'
    
    # 讀取現有關鍵字
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"讀取 {len(data['keywords'])} 個現有關鍵字")
    
    # 更新現有關鍵字的分類
    updated = 0
    for kw in data['keywords']:
        keyword = kw['keyword'].lower()
        if keyword in CATEGORY_MAPPING:
            cat, subcat = CATEGORY_MAPPING[keyword]
            kw['category'] = cat
            kw['subcategory'] = subcat
            updated += 1
        else:
            # 保留原分類，子分類設為 general
            if 'subcategory' not in kw:
                kw['subcategory'] = 'general'
    
    print(f"已更新 {updated} 個關鍵字的子分類")
    
    # 添加新關鍵字
    existing_keywords = {kw['keyword'].lower() for kw in data['keywords']}
    added = 0
    today = datetime.now().strftime('%Y-%m-%d')
    
    for new_kw in NEW_KEYWORDS:
        if new_kw['keyword'].lower() not in existing_keywords:
            data['keywords'].append({
                "keyword": new_kw['keyword'],
                "category": new_kw['category'],
                "subcategory": new_kw['subcategory'],
                "base_weight": new_kw['base_weight'],
                "dynamic_weight": 1.0,
                "sentiment_bias": new_kw['sentiment_bias'],
                "description": new_kw['description'],
                "added_date": today,
                "last_updated": today,
                "hit_count": 0,
                "prediction_count": 0,
                "correct_count": 0
            })
            added += 1
            print(f"  + {new_kw['keyword']} ({new_kw['category']}/{new_kw['subcategory']})")
    
    print(f"\n新增 {added} 個關鍵字")
    
    # 更新元數據
    data['version'] = '3.0'
    data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['total_keywords'] = len(data['keywords'])
    
    # 統計分類
    stats = {}
    for kw in data['keywords']:
        key = f"{kw['category']}/{kw.get('subcategory', 'general')}"
        stats[key] = stats.get(key, 0) + 1
    
    data['category_stats'] = stats
    
    # 保存
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 升級完成！總計 {data['total_keywords']} 個關鍵字")
    print("\n分類統計:")
    for k in sorted(stats.keys()):
        print(f"  {k}: {stats[k]}")
    
    return data

if __name__ == '__main__':
    upgrade_keywords()
