"""
關鍵字載入器
============

從 JSON 檔案載入關鍵字的功能

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import json
import logging
from pathlib import Path

# 2. 本地模組
from .models import Keyword

logger = logging.getLogger(__name__)


class KeywordLoader:
    """
    關鍵字載入器
    
    負責從 config/keywords/ 目錄載入關鍵字
    支援：
    - 分類目錄載入 (config/keywords/*.json)
    - 單一 JSON 檔案載入
    - 索引檔案讀取 (_index.json)
    """
    
    def __init__(self, keywords_dir: str = "config/keywords", config_path: str = "config/market_keywords.json"):
        self.keywords_dir = keywords_dir
        self.config_path = config_path
    
    def load_from_category_files(self) -> Dict[str, Keyword]:
        """從分類目錄載入關鍵字
        
        Returns:
            Dict[str, Keyword]: 關鍵字字典
        """
        keywords: Dict[str, Keyword] = {}
        keywords_path = Path(self.keywords_dir)
        
        if not keywords_path.exists():
            logger.warning(f"關鍵字目錄不存在: {self.keywords_dir}")
            return keywords
        
        try:
            # 讀取索引檔
            index_file = keywords_path / "_index.json"
            if not index_file.exists():
                # 沒有索引檔，直接掃描所有 JSON 檔案
                json_files = list(keywords_path.glob("*.json"))
                json_files = [f for f in json_files if f.name != "_index.json"]
            else:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                json_files = [
                    keywords_path / cat_info['file']
                    for cat_info in index_data.get('categories', {}).values()
                ]
            
            # 載入各類別檔案
            loaded_count = 0
            for cat_file in json_files:
                if not cat_file.exists():
                    continue
                
                with open(cat_file, 'r', encoding='utf-8') as f:
                    cat_data = json.load(f)
                
                for kw_data in cat_data.get('keywords', []):
                    kw = Keyword(**kw_data)
                    keywords[kw.word] = kw
                    loaded_count += 1
            
            logger.info(f"從 {len(json_files)} 個分類檔案載入 {loaded_count} 個關鍵字")
            
        except Exception as e:
            logger.error(f"載入分類檔案失敗: {e}")
        
        return keywords
    
    def load_from_single_file(self) -> Dict[str, Keyword]:
        """從單一 JSON 載入關鍵字
        
        Returns:
            Dict[str, Keyword]: 關鍵字字典
        """
        keywords: Dict[str, Keyword] = {}
        
        if not Path(self.config_path).exists():
            logger.warning(f"設定檔不存在: {self.config_path}")
            return keywords
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for kw_data in data.get('keywords', []):
                kw = Keyword(**kw_data)
                keywords[kw.word] = kw
            
            logger.info(f"從 {self.config_path} 載入 {len(keywords)} 個關鍵字")
            
        except Exception as e:
            logger.error(f"載入關鍵字失敗: {e}")
        
        return keywords
    
    def load(self) -> Dict[str, Keyword]:
        """載入關鍵字（優先分類目錄）
        
        Returns:
            Dict[str, Keyword]: 關鍵字字典
        """
        # 優先從分類目錄載入
        keywords = self.load_from_category_files()
        
        if keywords:
            return keywords
        
        # 備用：從單一 JSON 載入
        keywords = self.load_from_single_file()
        
        if not keywords:
            logger.warning("⚠️ 無法載入任何關鍵字，請確認 config/keywords/ 目錄存在")
        
        return keywords
