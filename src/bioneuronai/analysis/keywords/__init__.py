"""
Keywords 子模組
===============

關鍵字管理系統 v3.0 - 拆分後的模組化結構

檔案結構:
    keywords/
    ├── __init__.py     - 模組導出
    ├── models.py       - 資料模型 (Keyword, KeywordMatch, PredictionRecord)
    ├── loader.py       - JSON 載入器 (KeywordLoader)
    ├── manager.py      - 核心管理器 (KeywordManager)
    └── static_utils.py - 靜態工具 (MarketKeywords)

使用方式:
    # 使用靜態包裝類（推薦）
    from bioneuronai.analysis.keywords import MarketKeywords
    
    score, keywords = MarketKeywords.get_importance_score("BTC ETF 通過")
    sentiment, confidence = MarketKeywords.get_sentiment_bias("Fed升息")
    
    # 或使用單例管理器
    from bioneuronai.analysis.keywords import get_keyword_manager
    
    manager = get_keyword_manager()
    matches = manager.find_matches("比特幣創新高")

遵循 CODE_FIX_GUIDE.md 規範
"""

# 資料模型
from .models import Keyword, KeywordMatch, PredictionRecord

# 載入器
from .loader import KeywordLoader

# 核心管理器
from .manager import KeywordManager, get_keyword_manager

# 靜態工具類
from .static_utils import MarketKeywords

# 關鍵字學習器
from .learner import KeywordLearner  # ✅ 從新位置導入

__all__ = [
    # 資料模型
    'Keyword',
    'KeywordMatch', 
    'PredictionRecord',
    # 載入器
    'KeywordLoader',
    # 管理器
    'KeywordManager',
    'get_keyword_manager',
    # 靜態工具
    'MarketKeywords',
    # 學習器
    'KeywordLearner',  # ✅ 新增導出
]
