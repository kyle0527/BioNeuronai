# -*- coding: utf-8 -*-
"""
內部知識庫 (Internal Knowledge Base)
====================================

管理交易系統的內部知識：
- 交易規則文檔
- 歷史交易記錄
- 策略配置
- 市場分析報告
"""

import logging
import json
import hashlib
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import numpy as np

# 導入可選的 FAISS 索引
try:
    from .faiss_index import VectorIndex, create_index
    FAISS_INDEX_AVAILABLE = True
except ImportError:
    FAISS_INDEX_AVAILABLE = False
    VectorIndex = None
    create_index = None

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """文檔類型"""
    TRADING_RULE = "trading_rule"           # 交易規則
    STRATEGY_CONFIG = "strategy_config"     # 策略配置
    MARKET_ANALYSIS = "market_analysis"     # 市場分析
    HISTORICAL_TRADE = "historical_trade"   # 歷史交易
    NEWS_ARCHIVE = "news_archive"           # 新聞存檔
    CUSTOM = "custom"                       # 自定義


@dataclass
class KnowledgeDocument:
    """知識文檔"""
    id: str
    title: str
    content: str
    doc_type: DocumentType
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    score: float = 0.0  # 檢索時的相關性分數
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "doc_type": self.doc_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeDocument":
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            doc_type=DocumentType(data["doc_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


class InternalKnowledgeBase:
    """
    內部知識庫管理器
    
    功能：
    - 文檔的增刪改查
    - 向量索引和搜索
    - 持久化存儲
    - 自動更新嵌入
    """
    
    # 預設交易規則
    DEFAULT_TRADING_RULES = [
        {
            "title": "風險管理規則 - 單筆交易風險",
            "content": """
            單筆交易風險控制規則：
            1. 單筆交易最大風險不超過帳戶的 1-2%
            2. 必須設置止損單，止損距離基於 ATR 或關鍵支撐位
            3. 風險報酬比至少 1:2，理想 1:3
            4. 高波動市場下降低倉位大小
            5. 連續虧損 3 次後暫停交易並重新評估
            """,
            "tags": ["risk", "position_sizing", "stop_loss"]
        },
        {
            "title": "進場規則 - 趨勢確認",
            "content": """
            趨勢交易進場規則：
            1. 確認主趨勢方向（使用 EMA 200 或更高時間框架）
            2. 等待回調至支撐/阻力位
            3. 確認動量指標（RSI、MACD）同向
            4. 成交量確認（突破時放量）
            5. 避免在重大新聞發布前 30 分鐘內進場
            """,
            "tags": ["entry", "trend", "confirmation"]
        },
        {
            "title": "出場規則 - 止盈策略",
            "content": """
            止盈策略規則：
            1. 分批止盈：50% 在 1:2 RR，30% 在 1:3 RR，20% 跟蹤止損
            2. 移動止損至成本價當獲利達 1:1
            3. 使用跟蹤止損保護利潤（ATR 的 2-3 倍）
            4. 在關鍵阻力位部分獲利了結
            5. 時間止損：如果 48 小時內未達目標，重新評估
            """,
            "tags": ["exit", "take_profit", "trailing_stop"]
        },
        {
            "title": "新聞交易規則",
            "content": """
            新聞和事件交易規則：
            1. 重大新聞發布前 30 分鐘不開新倉
            2. 負面新聞（監管、駭客、破產）立即評估現有持倉
            3. ETF 批准等重大利好可能導致劇烈波動，謹慎追漲
            4. 關注鏈上數據異常（大額轉帳、交易所流入）
            5. 社交媒體情緒極端時反向思考
            """,
            "tags": ["news", "events", "sentiment"]
        },
        {
            "title": "市場狀態判斷規則",
            "content": """
            市場狀態識別規則：
            1. 強趨勢：ADX > 25，價格持續突破，回調淺
            2. 弱趨勢：ADX 20-25，價格震盪上行/下行
            3. 盤整：ADX < 20，價格在區間內波動
            4. 高波動：ATR 超過 20 日均值 1.5 倍
            5. 根據市場狀態調整策略：趨勢市用趨勢策略，盤整市用區間策略
            """,
            "tags": ["market_regime", "adx", "volatility"]
        }
    ]
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        embedding_service=None,
        auto_load: bool = True,
        use_faiss: bool = True
    ):
        self.storage_path = Path(storage_path) if storage_path else None
        self.embedding_service = embedding_service
        self.documents: Dict[str, KnowledgeDocument] = {}
        self._embeddings_matrix: Optional[np.ndarray] = None
        self._doc_ids: List[str] = []
        
        # FAISS 向量索引（可選加速）
        self._vector_index: Optional[VectorIndex] = None
        self._use_faiss = use_faiss and FAISS_INDEX_AVAILABLE
        if self._use_faiss and create_index:
            # 預設使用 384 維（all-MiniLM-L6-v2）
            self._vector_index = create_index(dimension=384)
            logger.info("✅ FAISS 向量索引已啟用")
        
        if auto_load:
            self._load_default_rules()
            if self.storage_path and self.storage_path.exists():
                self._load_from_storage()
        
        logger.info(f"內部知識庫已初始化，文檔數量: {len(self.documents)}")
    
    def _load_default_rules(self):
        """載入預設交易規則"""
        for i, rule in enumerate(self.DEFAULT_TRADING_RULES):
            doc_id = f"rule_{i+1}"
            self.add_document(
                doc_id=doc_id,
                title=rule["title"],
                content=rule["content"],
                doc_type=DocumentType.TRADING_RULE,
                tags=rule["tags"],
                update_index=False
            )
        self._rebuild_index()
    
    def add_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        doc_type: DocumentType = DocumentType.CUSTOM,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        update_index: bool = True
    ) -> KnowledgeDocument:
        """添加文檔"""
        doc = KnowledgeDocument(
            id=doc_id,
            title=title,
            content=content,
            doc_type=doc_type,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # 生成嵌入
        if self.embedding_service:
            try:
                result = self.embedding_service.embed(f"{title}\n{content}")
                doc.embedding = result.embedding
            except Exception as e:
                logger.warning(f"生成嵌入失敗: {e}")
        
        self.documents[doc_id] = doc
        
        if update_index:
            self._rebuild_index()
        
        return doc
    
    def update_document(
        self,
        doc_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[KnowledgeDocument]:
        """更新文檔"""
        if doc_id not in self.documents:
            return None
        
        doc = self.documents[doc_id]
        if title:
            doc.title = title
        if content:
            doc.content = content
        if tags is not None:
            doc.tags = tags
        if metadata is not None:
            doc.metadata.update(metadata)
        
        doc.updated_at = datetime.now()
        
        # 重新生成嵌入
        if self.embedding_service and (title or content):
            try:
                result = self.embedding_service.embed(f"{doc.title}\n{doc.content}")
                doc.embedding = result.embedding
                self._rebuild_index()
            except Exception as e:
                logger.warning(f"更新嵌入失敗: {e}")
        
        return doc
    
    def delete_document(self, doc_id: str) -> bool:
        """刪除文檔"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._rebuild_index()
            return True
        return False
    
    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """獲取文檔"""
        return self.documents.get(doc_id)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        doc_types: Optional[List[DocumentType]] = None,
        tags: Optional[List[str]] = None
    ) -> List[KnowledgeDocument]:
        """
        搜索文檔
        
        Args:
            query: 搜索查詢
            top_k: 返回數量
            min_score: 最小相關性分數
            doc_types: 過濾文檔類型
            tags: 過濾標籤
        """
        # 向量搜索
        if self.embedding_service and self._embeddings_matrix is not None:
            query_result = self.embedding_service.embed(query)
            
            # 優先使用 FAISS 加速搜索
            if self._use_faiss and self._vector_index is not None:
                distances, indices = self._vector_index.search(
                    query_result.embedding,
                    k=min(top_k * 2, len(self._doc_ids))  # 多取一些用於過濾
                )
                similarities = list(zip(indices, distances))
            else:
                # 降級到原始方法
                similarities = self.embedding_service.find_similar(
                    query_result.embedding,
                    [self.documents[doc_id].embedding for doc_id in self._doc_ids
                     if self.documents[doc_id].embedding is not None],
                    top_k=len(self._doc_ids)
                )
            
            results = []
            for idx, score in similarities:
                if score < min_score:
                    continue
                doc_id = self._doc_ids[idx]
                doc = self.documents[doc_id]
                
                # 類型過濾
                if doc_types and doc.doc_type not in doc_types:
                    continue
                
                # 標籤過濾
                if tags and not any(t in doc.tags for t in tags):
                    continue
                
                doc.score = score
                results.append(doc)
                
                if len(results) >= top_k:
                    break
            
            return results
        
        # 關鍵詞搜索（備用）
        return self._keyword_search(query, top_k, doc_types, tags)
    
    def _keyword_search(
        self,
        query: str,
        top_k: int,
        doc_types: Optional[List[DocumentType]] = None,
        tags: Optional[List[str]] = None
    ) -> List[KnowledgeDocument]:
        """關鍵詞搜索（備用方案）"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_docs = []
        for doc in self.documents.values():
            # 類型過濾
            if doc_types and doc.doc_type not in doc_types:
                continue
            
            # 標籤過濾
            if tags and not any(t in doc.tags for t in tags):
                continue
            
            # 計算簡單的關鍵詞匹配分數
            content_lower = f"{doc.title} {doc.content}".lower()
            matches = sum(1 for word in query_words if word in content_lower)
            score = matches / len(query_words) if query_words else 0
            
            if score > 0:
                doc.score = score
                scored_docs.append(doc)
        
        scored_docs.sort(key=lambda x: x.score, reverse=True)
        return scored_docs[:top_k]
    
    def _rebuild_index(self):
        """重建向量索引"""
        self._doc_ids = list(self.documents.keys())
        embeddings = []
        
        for doc_id in self._doc_ids:
            doc = self.documents[doc_id]
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
            else:
                # 生成簡單的占位嵌入
                embeddings.append(np.zeros(384))
        
        if embeddings:
            self._embeddings_matrix = np.array(embeddings)
            
            # 如果啟用 FAISS，重建索引
            if self._use_faiss and self._vector_index is not None:
                self._vector_index.reset()
                self._vector_index.add(self._embeddings_matrix)
                logger.debug(f"FAISS 索引已更新: {len(embeddings)} 個向量")
    
    def save_to_storage(self):
        """保存到存儲"""
        if not self.storage_path:
            return
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        data = {
            "documents": [doc.to_dict() for doc in self.documents.values()]
        }
        
        with open(self.storage_path / "knowledge_base.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"知識庫已保存: {len(self.documents)} 個文檔")
    
    def _load_from_storage(self):
        """從存儲載入"""
        if self.storage_path is None:
            return
        kb_file = self.storage_path / "knowledge_base.json"
        if not kb_file.exists():
            return
        
        try:
            with open(kb_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for doc_data in data.get("documents", []):
                doc = KnowledgeDocument.from_dict(doc_data)
                self.documents[doc.id] = doc
            
            self._rebuild_index()
            logger.info(f"從存儲載入 {len(self.documents)} 個文檔")
        except Exception as e:
            logger.error(f"載入知識庫失敗: {e}")
    
    def get_by_type(self, doc_type: DocumentType) -> List[KnowledgeDocument]:
        """按類型獲取文檔"""
        return [doc for doc in self.documents.values() if doc.doc_type == doc_type]
    
    def get_by_tags(self, tags: List[str]) -> List[KnowledgeDocument]:
        """按標籤獲取文檔"""
        return [doc for doc in self.documents.values()
                if any(t in doc.tags for t in tags)]
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        type_counts = {}
        for doc in self.documents.values():
            type_name = doc.doc_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "by_type": type_counts,
            "has_embedding_service": self.embedding_service is not None,
            "storage_path": str(self.storage_path) if self.storage_path else None
        }
