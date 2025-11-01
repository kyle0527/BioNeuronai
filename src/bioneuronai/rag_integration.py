"""
BioNeuronAI RAG集成模組
======================

基於2024-2025最新技術趨勢的檢索增強生成(RAG)系統
結合生物啟發式神經網路與現代資訊檢索技術

主要特點:
- 混合檢索策略 (密集向量 + 稀疏檢索 + 圖結構)
- 自適應分塊策略
- 多模態知識庫
- 實時知識更新
- 層次化記憶系統
"""

import json
import pickle
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

from .mega_core import MegaBioNet, NetworkTopology
from .core import BioNeuron


@dataclass
class Document:
    """文檔結構"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    timestamp: float = field(default_factory=time.time)
    chunks: List[str] = field(default_factory=list)
    
    
@dataclass
class QueryResult:
    """查詢結果"""
    documents: List[Document]
    scores: List[float]
    retrieval_time: float
    generation_time: Optional[float] = None
    
    
class BaseRetriever(ABC):
    """基礎檢索器介面"""
    
    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """編碼文本為向量"""
        pass
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> QueryResult:
        """檢索相關文檔"""
        pass
    
    @abstractmethod
    def add_document(self, document: Document) -> None:
        """添加文檔到索引"""
        pass


class AdaptiveChunker:
    """自適應分塊策略
    
    根據內容特性動態調整分塊大小和重疊
    """
    
    def __init__(
        self,
        base_chunk_size: int = 512,
        max_chunk_size: int = 2048,
        overlap_ratio: float = 0.1,
        semantic_threshold: float = 0.7
    ):
        self.base_chunk_size = base_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_ratio = overlap_ratio
        self.semantic_threshold = semantic_threshold
        
    def chunk_text(self, text: str, metadata: Dict = None) -> List[str]:
        """基於內容特性的智能分塊"""
        # 基礎分割 - 按句子
        sentences = self._split_sentences(text)
        
        # 動態調整塊大小
        if metadata and 'content_type' in metadata:
            chunk_size = self._get_adaptive_size(metadata['content_type'])
        else:
            chunk_size = self.base_chunk_size
            
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            # 檢查是否需要開始新塊
            if (current_length + sentence_length > chunk_size and 
                current_chunk and 
                current_length > chunk_size * 0.5):
                
                chunks.append(current_chunk.strip())
                
                # 計算重疊內容
                overlap_size = int(chunk_size * self.overlap_ratio)
                overlap_words = current_chunk.split()[-overlap_size:]
                current_chunk = " ".join(overlap_words) + " " + sentence
                current_length = len(overlap_words) + sentence_length
            else:
                current_chunk += " " + sentence
                current_length += sentence_length
                
        # 添加最後一塊
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        # 簡單的句子分割，可以用更複雜的NLP工具替換
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_adaptive_size(self, content_type: str) -> int:
        """根據內容類型調整塊大小"""
        size_map = {
            'technical': self.max_chunk_size,  # 技術文檔需要更大的上下文
            'conversational': self.base_chunk_size // 2,  # 對話内容較短
            'narrative': int(self.base_chunk_size * 1.5),  # 敘述性內容適中
            'code': self.base_chunk_size,  # 代碼保持標準大小
        }
        return size_map.get(content_type, self.base_chunk_size)


class BioNeuronEmbedder:
    """基於生物神經網路的嵌入器
    
    使用BioNeuronAI的核心架構進行文本嵌入
    """
    
    def __init__(
        self,
        embedding_dim: int = 768,
        vocab_size: int = 50000,
        context_window: int = 512
    ):
        self.embedding_dim = embedding_dim
        self.vocab_size = vocab_size
        self.context_window = context_window
        
        # 使用MegaBioNet作為主幹
        topology = NetworkTopology(
            input_dim=vocab_size,
            hidden_layers=[2048, 1024, embedding_dim],
            output_dim=embedding_dim
        )
        
        self.encoder = MegaBioNet(topology, sparsity=0.9)
        
        # 詞彙表和tokenizer (簡化版)
        self.vocab = {}
        self.reverse_vocab = {}
        self._init_vocab()
        
    def _init_vocab(self):
        """初始化詞彙表 (簡化版本)"""
        # 在實際應用中，這裡會加載預訓練的tokenizer
        common_words = [
            '<pad>', '<unk>', '<cls>', '<sep>',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        ]
        
        for i, word in enumerate(common_words):
            self.vocab[word] = i
            self.reverse_vocab[i] = word
            
    def tokenize(self, text: str) -> List[int]:
        """簡單的tokenization"""
        words = text.lower().split()
        tokens = []
        
        for word in words[:self.context_window]:
            token_id = self.vocab.get(word, self.vocab.get('<unk>', 1))
            tokens.append(token_id)
            
        # 填充到固定長度
        while len(tokens) < self.context_window:
            tokens.append(self.vocab.get('<pad>', 0))
            
        return tokens[:self.context_window]
    
    def encode(self, text: str) -> np.ndarray:
        """編碼文本為向量"""
        tokens = self.tokenize(text)
        
        # 轉換為one-hot或嵌入向量
        input_vector = np.zeros(self.vocab_size, dtype=np.float32)
        
        # 簡單的詞袋模型
        for token in tokens:
            if token < self.vocab_size:
                input_vector[token] = 1.0
                
        # 通過神經網路編碼
        embedding = self.encoder.forward(input_vector)
        
        # 標準化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding


class HybridRetriever(BaseRetriever):
    """混合檢索器
    
    結合密集向量檢索、稀疏檢索和圖結構檢索
    """
    
    def __init__(
        self,
        embedder: BioNeuronEmbedder,
        db_path: str = "knowledge_base.db",
        use_graph: bool = True
    ):
        self.embedder = embedder
        self.db_path = db_path
        self.use_graph = use_graph
        
        # 初始化數據庫
        self._init_database()
        
        # 文檔索引
        self.documents: Dict[str, Document] = {}
        self.embeddings: List[np.ndarray] = []
        self.doc_ids: List[str] = []
        
        # 圖結構 (簡化版)
        if use_graph:
            self.doc_graph: Dict[str, List[str]] = {}
            
        # 分塊器
        self.chunker = AdaptiveChunker()
        
    def _init_database(self):
        """初始化SQLite數據庫"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.lock = threading.Lock()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT,
                metadata TEXT,
                embedding BLOB,
                timestamp REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT,
                chunk_text TEXT,
                chunk_embedding BLOB,
                chunk_index INTEGER,
                FOREIGN KEY (doc_id) REFERENCES documents (id)
            )
        ''')
        
        self.conn.commit()
        
    def encode(self, text: str) -> np.ndarray:
        """使用BioNeuron嵌入器編碼"""
        return self.embedder.encode(text)
    
    def add_document(self, document: Document) -> None:
        """添加文檔到知識庫"""
        # 生成嵌入
        document.embedding = self.encode(document.content)
        
        # 分塊處理
        document.chunks = self.chunker.chunk_text(
            document.content, 
            document.metadata
        )
        
        # 存儲到內存索引
        self.documents[document.id] = document
        self.embeddings.append(document.embedding)
        self.doc_ids.append(document.id)
        
        # 存儲到數據庫
        with self.lock:
            cursor = self.conn.cursor()
            
            # 插入文檔
            cursor.execute('''
                INSERT OR REPLACE INTO documents 
                (id, content, metadata, embedding, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                document.id,
                document.content,
                json.dumps(document.metadata),
                pickle.dumps(document.embedding),
                document.timestamp
            ))
            
            # 插入分塊
            for i, chunk in enumerate(document.chunks):
                chunk_embedding = self.encode(chunk)
                cursor.execute('''
                    INSERT OR REPLACE INTO chunks
                    (id, doc_id, chunk_text, chunk_embedding, chunk_index)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    f"{document.id}_chunk_{i}",
                    document.id,
                    chunk,
                    pickle.dumps(chunk_embedding),
                    i
                ))
                
            self.conn.commit()
            
        # 更新圖結構
        if self.use_graph:
            self._update_graph(document)
    
    def _update_graph(self, document: Document):
        """更新文檔圖結構"""
        if document.id not in self.doc_graph:
            self.doc_graph[document.id] = []
            
        # 計算與現有文檔的相似度
        doc_embedding = document.embedding
        
        for existing_id, existing_doc in self.documents.items():
            if existing_id != document.id:
                similarity = self._cosine_similarity(
                    doc_embedding, 
                    existing_doc.embedding
                )
                
                # 如果相似度超過閾值，建立連接
                if similarity > 0.7:
                    if existing_id not in self.doc_graph[document.id]:
                        self.doc_graph[document.id].append(existing_id)
                    if document.id not in self.doc_graph.get(existing_id, []):
                        self.doc_graph.setdefault(existing_id, []).append(document.id)
    
    def retrieve(self, query: str, top_k: int = 5) -> QueryResult:
        """混合檢索策略"""
        start_time = time.time()
        
        # 1. 密集向量檢索
        query_embedding = self.encode(query)
        dense_scores = self._dense_retrieval(query_embedding, top_k * 2)
        
        # 2. 稀疏檢索 (關鍵詞匹配)
        sparse_scores = self._sparse_retrieval(query, top_k * 2)
        
        # 3. 圖結構擴展
        if self.use_graph:
            graph_scores = self._graph_retrieval(dense_scores, sparse_scores)
        else:
            graph_scores = {}
            
        # 4. 融合分數
        final_scores = self._fuse_scores(dense_scores, sparse_scores, graph_scores)
        
        # 5. 選取top-k結果
        sorted_results = sorted(
            final_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:top_k]
        
        # 構建結果
        retrieved_docs = []
        scores = []
        
        for doc_id, score in sorted_results:
            if doc_id in self.documents:
                retrieved_docs.append(self.documents[doc_id])
                scores.append(score)
                
        retrieval_time = time.time() - start_time
        
        return QueryResult(
            documents=retrieved_docs,
            scores=scores,
            retrieval_time=retrieval_time
        )
    
    def _dense_retrieval(self, query_embedding: np.ndarray, top_k: int) -> Dict[str, float]:
        """密集向量檢索"""
        scores = {}
        
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            doc_id = self.doc_ids[i]
            scores[doc_id] = similarity
            
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k])
    
    def _sparse_retrieval(self, query: str, top_k: int) -> Dict[str, float]:
        """稀疏檢索 (簡化的TF-IDF)"""
        query_terms = set(query.lower().split())
        scores = {}
        
        for doc_id, document in self.documents.items():
            doc_terms = set(document.content.lower().split())
            
            # 計算Jaccard相似度
            intersection = len(query_terms & doc_terms)
            union = len(query_terms | doc_terms)
            
            if union > 0:
                scores[doc_id] = intersection / union
            else:
                scores[doc_id] = 0.0
                
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k])
    
    def _graph_retrieval(self, dense_scores: Dict[str, float], sparse_scores: Dict[str, float]) -> Dict[str, float]:
        """基於圖結構的檢索擴展"""
        graph_scores = {}
        
        # 從密集和稀疏檢索的高分文檔開始
        seed_docs = set(list(dense_scores.keys())[:3] + list(sparse_scores.keys())[:3])
        
        for doc_id in seed_docs:
            if doc_id in self.doc_graph:
                for neighbor_id in self.doc_graph[doc_id]:
                    # 傳播分數 (衰減係數 0.5)
                    base_score = max(
                        dense_scores.get(doc_id, 0),
                        sparse_scores.get(doc_id, 0)
                    )
                    graph_scores[neighbor_id] = base_score * 0.5
                    
        return graph_scores
    
    def _fuse_scores(
        self, 
        dense_scores: Dict[str, float], 
        sparse_scores: Dict[str, float], 
        graph_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """融合不同檢索策略的分數"""
        all_docs = set(dense_scores.keys()) | set(sparse_scores.keys()) | set(graph_scores.keys())
        
        final_scores = {}
        
        for doc_id in all_docs:
            # 權重融合: 密集檢索 40%, 稀疏檢索 35%, 圖檢索 25%
            dense_score = dense_scores.get(doc_id, 0) * 0.4
            sparse_score = sparse_scores.get(doc_id, 0) * 0.35
            graph_score = graph_scores.get(doc_id, 0) * 0.25
            
            final_scores[doc_id] = dense_score + sparse_score + graph_score
            
        return final_scores
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算餘弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)


class MemoryAugmentedGenerator:
    """記憶增強生成器
    
    結合RAG檢索結果與BioNeuron的記憶機制
    """
    
    def __init__(
        self,
        retriever: HybridRetriever,
        generator_config: Dict = None
    ):
        self.retriever = retriever
        self.config = generator_config or {}
        
        # 記憶系統
        self.short_term_memory = []  # 最近的查詢-回答對
        self.long_term_memory = {}   # 主題相關的記憶
        
        # 生成參數
        self.max_context_length = self.config.get('max_context_length', 2048)
        self.memory_decay = self.config.get('memory_decay', 0.9)
        
    def generate_response(
        self, 
        query: str, 
        max_docs: int = 5,
        include_memory: bool = True
    ) -> Dict[str, Any]:
        """生成增強回答"""
        start_time = time.time()
        
        # 1. 檢索相關文檔
        retrieval_result = self.retriever.retrieve(query, max_docs)
        
        # 2. 構建上下文
        context = self._build_context(query, retrieval_result, include_memory)
        
        # 3. 生成回答 (簡化版 - 實際中會使用LLM)
        response = self._generate_from_context(query, context)
        
        # 4. 更新記憶
        if include_memory:
            self._update_memory(query, response, retrieval_result)
            
        generation_time = time.time() - start_time
        retrieval_result.generation_time = generation_time
        
        return {
            'response': response,
            'sources': [doc.id for doc in retrieval_result.documents],
            'retrieval_scores': retrieval_result.scores,
            'retrieval_time': retrieval_result.retrieval_time,
            'generation_time': generation_time,
            'context_length': len(context)
        }
    
    def _build_context(
        self, 
        query: str, 
        retrieval_result: QueryResult, 
        include_memory: bool
    ) -> str:
        """構建生成上下文"""
        context_parts = []
        
        # 添加檢索到的文檔
        for i, doc in enumerate(retrieval_result.documents):
            score = retrieval_result.scores[i]
            context_parts.append(f"[Source {i+1}] (Score: {score:.3f})")
            context_parts.append(doc.content[:500] + "...")  # 截斷長文檔
            context_parts.append("")
        
        # 添加記憶內容
        if include_memory:
            relevant_memory = self._get_relevant_memory(query)
            if relevant_memory:
                context_parts.append("[Memory Context]")
                context_parts.extend(relevant_memory)
                context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # 截斷過長的上下文
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + "..."
            
        return context
    
    def _generate_from_context(self, query: str, context: str) -> str:
        """從上下文生成回答 (簡化版)"""
        # 這是一個簡化的生成器
        # 實際應用中會使用GPT、Claude等LLM
        
        # 基於關鍵詞匹配的簡單回答生成
        query_words = set(query.lower().split())
        context_sentences = context.split('\n')
        
        relevant_sentences = []
        for sentence in context_sentences:
            if sentence.strip():
                sentence_words = set(sentence.lower().split())
                overlap = len(query_words & sentence_words)
                if overlap > 0:
                    relevant_sentences.append((sentence, overlap))
        
        # 排序並選擇最相關的句子
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        
        if relevant_sentences:
            top_sentences = [s[0] for s in relevant_sentences[:3]]
            response = "Based on the available information: " + " ".join(top_sentences)
        else:
            response = "I don't have enough information to answer this question."
            
        return response
    
    def _update_memory(self, query: str, response: str, retrieval_result: QueryResult):
        """更新記憶系統"""
        # 更新短期記憶
        memory_entry = {
            'query': query,
            'response': response,
            'timestamp': time.time(),
            'sources': [doc.id for doc in retrieval_result.documents]
        }
        
        self.short_term_memory.append(memory_entry)
        
        # 保持短期記憶大小
        if len(self.short_term_memory) > 10:
            self.short_term_memory.pop(0)
        
        # 更新長期記憶 (基於主題)
        topic = self._extract_topic(query)
        if topic:
            if topic not in self.long_term_memory:
                self.long_term_memory[topic] = []
            
            self.long_term_memory[topic].append(memory_entry)
            
            # 保持長期記憶大小並應用衰減
            if len(self.long_term_memory[topic]) > 20:
                self.long_term_memory[topic].pop(0)
    
    def _get_relevant_memory(self, query: str) -> List[str]:
        """獲取相關記憶"""
        relevant_memory = []
        
        # 檢查短期記憶
        for memory in self.short_term_memory[-3:]:  # 最近3次對話
            relevant_memory.append(f"Previous: {memory['query']} -> {memory['response']}")
        
        # 檢查長期記憶
        topic = self._extract_topic(query)
        if topic and topic in self.long_term_memory:
            for memory in self.long_term_memory[topic][-2:]:  # 相關主題的最近2次
                relevant_memory.append(f"Related: {memory['response']}")
        
        return relevant_memory
    
    def _extract_topic(self, query: str) -> Optional[str]:
        """提取查詢主題 (簡化版)"""
        # 簡單的主題提取 - 實際中會使用更複雜的NLP技術
        words = query.lower().split()
        
        # 預定義主題關鍵詞
        topic_keywords = {
            'technology': ['ai', 'machine', 'learning', 'neural', 'network', 'algorithm'],
            'science': ['research', 'experiment', 'data', 'analysis', 'study'],
            'business': ['market', 'customer', 'sales', 'revenue', 'strategy'],
            'health': ['medical', 'health', 'disease', 'treatment', 'patient']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in words for keyword in keywords):
                return topic
        
        return None


class BioRAGSystem:
    """完整的BioNeuronAI RAG系統
    
    整合所有組件的主要介面
    """
    
    def __init__(
        self,
        db_path: str = "bioneuron_rag.db",
        embedding_dim: int = 768,
        config: Dict = None
    ):
        self.config = config or {}
        
        # 初始化組件
        self.embedder = BioNeuronEmbedder(embedding_dim=embedding_dim)
        self.retriever = HybridRetriever(self.embedder, db_path)
        self.generator = MemoryAugmentedGenerator(self.retriever, config)
        
        # 統計信息
        self.stats = {
            'total_documents': 0,
            'total_queries': 0,
            'avg_retrieval_time': 0.0,
            'avg_generation_time': 0.0
        }
    
    def add_document(self, content: str, doc_id: str = None, metadata: Dict = None) -> str:
        """添加文檔到知識庫"""
        if not doc_id:
            doc_id = f"doc_{int(time.time() * 1000)}"
            
        document = Document(
            id=doc_id,
            content=content,
            metadata=metadata or {}
        )
        
        self.retriever.add_document(document)
        self.stats['total_documents'] += 1
        
        return doc_id
    
    def query(
        self, 
        question: str, 
        max_docs: int = 5,
        include_memory: bool = True
    ) -> Dict[str, Any]:
        """查詢RAG系統"""
        result = self.generator.generate_response(
            question, 
            max_docs=max_docs,
            include_memory=include_memory
        )
        
        # 更新統計
        self.stats['total_queries'] += 1
        self.stats['avg_retrieval_time'] = (
            (self.stats['avg_retrieval_time'] * (self.stats['total_queries'] - 1) + 
             result['retrieval_time']) / self.stats['total_queries']
        )
        self.stats['avg_generation_time'] = (
            (self.stats['avg_generation_time'] * (self.stats['total_queries'] - 1) + 
             result['generation_time']) / self.stats['total_queries']
        )
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取系統統計信息"""
        return {
            **self.stats,
            'embedder_params': self.embedder.encoder.count_parameters(),
            'knowledge_base_size': len(self.retriever.documents)
        }
    
    def export_knowledge_base(self, filepath: str):
        """導出知識庫"""
        export_data = {
            'documents': {
                doc_id: {
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'chunks': doc.chunks,
                    'timestamp': doc.timestamp
                }
                for doc_id, doc in self.retriever.documents.items()
            },
            'stats': self.stats
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def import_knowledge_base(self, filepath: str):
        """導入知識庫"""
        with open(filepath, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        for doc_id, doc_data in import_data['documents'].items():
            document = Document(
                id=doc_id,
                content=doc_data['content'],
                metadata=doc_data['metadata']
            )
            document.chunks = doc_data.get('chunks', [])
            document.timestamp = doc_data.get('timestamp', time.time())
            
            self.retriever.add_document(document)