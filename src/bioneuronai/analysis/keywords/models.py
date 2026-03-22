"""
關鍵字數據模型
==============

包含：
- Keyword: 關鍵字數據類
- KeywordMatch: 匹配結果數據類
- PredictionRecord: 預測記錄數據類

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Keyword:
    """關鍵字資料結構"""
    word: str  # 關鍵字文本
    category: str           # person, institution, event, coin, macro, legislation, tech
    base_weight: float      # 基礎權重 1.0-3.0
    dynamic_weight: float   # 動態權重
    sentiment_bias: str     # positive, negative, neutral, uncertain
    description: str
    
    # 時間戳記
    added_date: str         # 新增日期 (YYYY-MM-DD)
    last_updated: str       # 最後更新
    
    # 統計數據
    hit_count: int = 0           # 命中次數
    prediction_count: int = 0    # 預測次數
    correct_count: int = 0       # 正確次數
    
    # 動態偏差 (修復 dynamic_bias 欄位缺失問題)
    dynamic_bias: float = 0.0

    # 子分類 (v3.0 新增)
    subcategory: str = "general"
    
    @property
    def accuracy(self) -> float:
        """計算預測準確率"""
        if self.prediction_count == 0:
            return 0.5  # 預設 50%
        return self.correct_count / self.prediction_count
    
    @property
    def effective_weight(self) -> float:
        """有效權重 = 基礎權重 × 動態權重"""
        return self.base_weight * self.dynamic_weight
    
    @property
    def days_since_added(self) -> int:
        """計算關鍵字存在天數"""
        added = datetime.strptime(self.added_date, "%Y-%m-%d")
        return (datetime.now() - added).days
    
    @property
    def days_since_updated(self) -> int:
        """計算上次更新天數"""
        updated = datetime.strptime(self.last_updated, "%Y-%m-%d")
        return (datetime.now() - updated).days
    
    @property
    def is_stale(self) -> bool:
        """判斷是否過時 (超過 90 天未更新且準確率低)"""
        return self.days_since_updated > 90 and self.accuracy < 0.4


@dataclass
class PredictionRecord:
    """預測記錄"""
    id: int
    keyword: str
    news_title: str
    predicted_direction: str  # positive, negative, neutral
    actual_direction: Optional[str] = None
    price_before: float = 0.0
    price_after: Optional[float] = None
    price_change_pct: Optional[float] = None
    is_correct: Optional[bool] = None
    created_at: str = ""
    verified_at: Optional[str] = None


@dataclass
class KeywordMatch:
    """關鍵字匹配結果"""
    keyword: str
    category: str
    effective_weight: float
    sentiment_bias: str
    description: str
    accuracy: float
    days_old: int
