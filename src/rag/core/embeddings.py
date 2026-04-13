# -*- coding: utf-8 -*-
"""
向量嵌入服務 (Embedding Service)
================================

支持多種嵌入模型：
- 本地模型 (sentence-transformers)
- OpenAI API
- HuggingFace API
"""

import logging
import hashlib
import re
from typing import List, Dict, Optional, Any, cast
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingModel(Enum):
    """支援的嵌入模型"""
    # 本地模型 (免費)
    LOCAL_MINILM = "all-MiniLM-L6-v2"           # 384維, 快速
    LOCAL_MPNET = "all-mpnet-base-v2"           # 768維, 高品質
    LOCAL_MULTILINGUAL = "paraphrase-multilingual-MiniLM-L12-v2"  # 多語言
    
    # OpenAI (付費)
    OPENAI_SMALL = "text-embedding-3-small"     # 1536維
    OPENAI_LARGE = "text-embedding-3-large"     # 3072維
    OPENAI_ADA = "text-embedding-ada-002"       # 1536維 (舊版)
    
    # 自定義
    CUSTOM = "custom"


@dataclass
class EmbeddingResult:
    """嵌入結果"""
    text: str
    embedding: np.ndarray
    model: str
    dimensions: int
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def hash(self) -> str:
        """文本哈希用於緩存"""
        return hashlib.md5(self.text.encode()).hexdigest()


class EmbeddingService:
    """
    統一嵌入服務
    
    支援本地和遠程模型，提供：
    - 文本向量化
    - 批量處理
    - 緩存機制
    - 相似度計算
    """
    
    def __init__(
        self,
        model: EmbeddingModel = EmbeddingModel.LOCAL_MINILM,
        api_key: Optional[str] = None,
        cache_enabled: bool = True,
        max_cache_size: int = 10000
    ):
        self.model_type = model
        self.api_key = api_key
        self.cache_enabled = cache_enabled
        self.max_cache_size = max_cache_size
        
        self._model = None
        self._cache: Dict[str, np.ndarray] = {}
        self._dimensions = self._get_model_dimensions()
        
        self._initialize_model()
        
    def _get_model_dimensions(self) -> int:
        """獲取模型輸出維度"""
        dims = {
            EmbeddingModel.LOCAL_MINILM: 384,
            EmbeddingModel.LOCAL_MPNET: 768,
            EmbeddingModel.LOCAL_MULTILINGUAL: 384,
            EmbeddingModel.OPENAI_SMALL: 1536,
            EmbeddingModel.OPENAI_LARGE: 3072,
            EmbeddingModel.OPENAI_ADA: 1536,
        }
        return dims.get(self.model_type, 384)
    
    def _initialize_model(self):
        """初始化嵌入模型"""
        if self.model_type.value.startswith("text-embedding"):
            # OpenAI 模型 - 延遲加載
            logger.info(f"OpenAI 嵌入模型已配置: {self.model_type.value}")
        else:
            # 本地模型
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_type.value)
                logger.info(f"本地嵌入模型已加載: {self.model_type.value}")
            except ImportError:
                logger.warning("sentence-transformers 未安裝，將使用 deterministic hashed embedding")
                self._model = None
            except Exception as e:
                logger.error(f"模型加載失敗: {e}")
                self._model = None
    
    def embed(self, text: str) -> EmbeddingResult:
        """
        將文本轉換為向量嵌入
        
        Args:
            text: 輸入文本
            
        Returns:
            EmbeddingResult 包含嵌入向量
        """
        # 檢查緩存
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if self.cache_enabled and cache_key in self._cache:
            return EmbeddingResult(
                text=text,
                embedding=self._cache[cache_key],
                model=self.model_type.value,
                dimensions=self._dimensions,
                metadata={"from_cache": True}
            )
        
        # 生成嵌入
        embedding = self._generate_embedding(text)
        
        # 存入緩存
        if self.cache_enabled:
            if len(self._cache) >= self.max_cache_size:
                # 簡單的 LRU: 移除最舊的項目
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[cache_key] = embedding
        
        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model=self.model_type.value,
            dimensions=self._dimensions
        )
    
    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量嵌入"""
        results: List[Optional[EmbeddingResult]] = []
        
        # 分離已緩存和需要計算的
        to_embed = []
        to_embed_indices = []
        
        for i, text in enumerate(texts):
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if self.cache_enabled and cache_key in self._cache:
                results.append(EmbeddingResult(
                    text=text,
                    embedding=self._cache[cache_key],
                    model=self.model_type.value,
                    dimensions=self._dimensions,
                    metadata={"from_cache": True}
                ))
            else:
                to_embed.append(text)
                to_embed_indices.append(i)
                results.append(None)  # 占位
        
        # 批量計算
        if to_embed:
            embeddings = self._generate_embeddings_batch(to_embed)
            for idx, (text, emb) in zip(to_embed_indices, zip(to_embed, embeddings)):
                cache_key = hashlib.md5(text.encode()).hexdigest()
                if self.cache_enabled:
                    self._cache[cache_key] = emb
                results[idx] = EmbeddingResult(
                    text=text,
                    embedding=emb,
                    model=self.model_type.value,
                    dimensions=self._dimensions
                )
        
        return [result for result in results if result is not None]
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成單個嵌入"""
        if self.model_type.value.startswith("text-embedding"):
            return self._openai_embed(text)
        elif self._model is not None:
            return cast(np.ndarray, self._model.encode(text, convert_to_numpy=True))
        else:
            return self._simple_embed(text)
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """批量生成嵌入"""
        if self.model_type.value.startswith("text-embedding"):
            return [self._openai_embed(t) for t in texts]
        elif self._model is not None:
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return list(embeddings)
        else:
            return [self._simple_embed(t) for t in texts]
    
    def _openai_embed(self, text: str) -> np.ndarray:
        """使用 OpenAI API 生成嵌入"""
        if not self.api_key:
            logger.warning("OpenAI API key 未設置，使用簡單嵌入")
            return self._simple_embed(text)
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.embeddings.create(
                input=text,
                model=self.model_type.value
            )
            return cast(np.ndarray, np.array(response.data[0].embedding))
        except Exception as e:
            logger.error(f"OpenAI 嵌入失敗: {e}")
            return self._simple_embed(text)
    
    def _simple_embed(self, text: str) -> np.ndarray:
        """Deterministic hashed embedding 備援方案，避免隨機向量污染檢索結果。"""
        vector = np.zeros(self._dimensions, dtype=np.float32)
        normalized = text.lower().strip()
        if not normalized:
            return vector

        tokens = re.findall(r"[\w]+", normalized)
        if not tokens:
            tokens = list(normalized)

        # 混合 unigram / bigram，保留基本詞序資訊
        features = list(tokens)
        features.extend(
            f"{tokens[i]}::{tokens[i + 1]}"
            for i in range(len(tokens) - 1)
        )

        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算餘弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    @staticmethod
    def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算歐氏距離"""
        return float(np.linalg.norm(vec1 - vec2))
    
    def find_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[tuple]:
        """
        找出最相似的向量
        
        Returns:
            List of (index, similarity_score)
        """
        similarities = []
        for i, emb in enumerate(candidate_embeddings):
            sim = self.cosine_similarity(query_embedding, emb)
            similarities.append((i, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    @property
    def dimensions(self) -> int:
        """嵌入維度"""
        return self._dimensions
    
    @property
    def model_name(self) -> str:
        """模型名稱"""
        return self.model_type.value
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            "model": self.model_type.value,
            "dimensions": self._dimensions,
            "cache_size": len(self._cache),
            "cache_enabled": self.cache_enabled,
            "max_cache_size": self.max_cache_size
        }
