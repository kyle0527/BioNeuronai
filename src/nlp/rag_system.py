"""
RAG (Retrieval-Augmented Generation) 系統
========================================
⚠️ **已廢棄 (DEPRECATED)** ⚠️

此實現已被 `src/rag/` 模組取代。

新代碼請使用:
    from rag.core import EmbeddingService, UnifiedRetriever
    from rag.internal import InternalKnowledgeBase

遷移指南: 請參考 MIGRATION_RAG.md

此檔案將在 2026-04-26 後移除。

---

原功能說明：
檢索增強生成系統，結合向量檢索和語言模型生成

核心功能：
- 文檔嵌入和索引
- 向量相似度檢索
- 上下文增強生成
- 多種檢索策略
- 記憶和緩存管理
"""

import warnings

warnings.warn(
    "nlp.rag_system.RAGSystem 已廢棄，請使用 src/rag/ 模組。"
    "詳見 MIGRATION_RAG.md",
    DeprecationWarning,
    stacklevel=2
)

import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import json
import pickle
from datetime import datetime
import hashlib


@dataclass
class Document:
    """文檔數據結構"""
    text: str
    metadata: Optional[Dict] = None
    embedding: Optional[np.ndarray] = None
    doc_id: Optional[str] = None
    
    def __post_init__(self):
        if self.doc_id is None:
            # 生成文檔 ID
            self.doc_id = hashlib.md5(self.text.encode()).hexdigest()[:16]
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RetrievalResult:
    """檢索結果"""
    document: Document
    score: float
    rank: int


class SimpleEmbedding(nn.Module):
    """簡單的嵌入模型（可替換為更強大的模型）"""
    
    def __init__(self, vocab_size: int = 50000, embed_dim: int = 384):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.pooling = nn.AdaptiveAvgPool1d(1)
    
    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Args:
            input_ids: [batch_size, seq_len]
        Returns:
            embeddings: [batch_size, embed_dim]
        """
        # 嵌入
        embeds = self.embedding(input_ids)  # [batch, seq, dim]
        
        # 平均池化
        embeds = embeds.transpose(1, 2)  # [batch, dim, seq]
        pooled = self.pooling(embeds).squeeze(-1)  # [batch, dim]
        
        # L2 正規化
        pooled = nn.functional.normalize(pooled, p=2, dim=1)
        
        return pooled


class VectorStore:
    """向量存儲和檢索"""
    
    def __init__(self, embed_dim: int = 384):
        self.embed_dim = embed_dim
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index_built = False
    
    def add_documents(self, documents: List[Document]):
        """添加文檔"""
        self.documents.extend(documents)
        self.index_built = False
    
    def build_index(self):
        """構建向量索引"""
        if not self.documents:
            raise ValueError("沒有文檔可以索引")
        
        embeddings = []
        for doc in self.documents:
            if doc.embedding is None:
                raise ValueError(f"文檔 {doc.doc_id} 沒有嵌入向量")
            embeddings.append(doc.embedding)
        
        self.embeddings = np.vstack(embeddings)
        self.index_built = True
        
        print(f"✅ 索引構建完成：{len(self.documents)} 個文檔")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """搜索相似文檔"""
        if not self.index_built or self.embeddings is None:
            raise ValueError("索引未構建，請先調用 build_index()")
        
        # 計算餘弦相似度
        query_embedding = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        similarities = np.dot(self.embeddings, query_embedding)
        
        # 排序並獲取 top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices):
            score = float(similarities[idx])
            if score >= score_threshold:
                results.append(RetrievalResult(
                    document=self.documents[idx],
                    score=score,
                    rank=rank + 1
                ))
        
        return results
    
    def save(self, save_path: Union[str, Path]):
        """保存向量存儲"""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'embed_dim': self.embed_dim,
            'documents': [
                {
                    'text': doc.text,
                    'metadata': doc.metadata,
                    'doc_id': doc.doc_id,
                    'embedding': doc.embedding.tolist() if doc.embedding is not None else None
                }
                for doc in self.documents
            ],
            'embeddings': self.embeddings.tolist() if self.embeddings is not None else None,
            'index_built': self.index_built
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 向量存儲已保存：{save_path}")
    
    @classmethod
    def load(cls, load_path: Union[str, Path]) -> 'VectorStore':
        """載入向量存儲"""
        with open(load_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        store = cls(embed_dim=data['embed_dim'])
        
        # 重建文檔
        for doc_data in data['documents']:
            embedding = np.array(doc_data['embedding']) if doc_data['embedding'] else None
            doc = Document(
                text=doc_data['text'],
                metadata=doc_data['metadata'],
                doc_id=doc_data['doc_id'],
                embedding=embedding
            )
            store.documents.append(doc)
        
        # 重建索引
        if data['embeddings']:
            store.embeddings = np.array(data['embeddings'])
            store.index_built = data['index_built']
        
        print(f"✅ 向量存儲已載入：{len(store.documents)} 個文檔")
        return store


class RAGSystem:
    """RAG 系統主類"""
    
    def __init__(
        self,
        model,
        tokenizer,
        embedding_model: Optional[SimpleEmbedding] = None,
        embed_dim: int = 384,
        device: str = "cpu"
    ):
        """
        Args:
            model: 語言模型（如 TinyLLM）
            tokenizer: 分詞器
            embedding_model: 嵌入模型（可選）
            embed_dim: 嵌入維度
            device: 設備
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.embed_dim = embed_dim
        
        # 嵌入模型
        if embedding_model is None:
            self.embedding_model = SimpleEmbedding(
                vocab_size=tokenizer.vocab_size,
                embed_dim=embed_dim
            )
        else:
            self.embedding_model = embedding_model
        
        self.embedding_model.to(device)
        self.embedding_model.eval()
        
        # 向量存儲
        self.vector_store = VectorStore(embed_dim=embed_dim)
        
        # 配置
        self.top_k = 5
        self.max_context_length = 512
        self.score_threshold = 0.1
        
        print("✅ RAG 系統初始化完成")
        print(f"   設備: {device}")
        print(f"   嵌入維度: {embed_dim}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """將文本編碼為向量"""
        # 分詞
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        
        # 截斷
        if len(token_ids) > 128:
            token_ids = token_ids[:128]
        
        # 轉為 tensor
        input_ids = torch.tensor([token_ids]).to(self.device)
        
        # 生成嵌入
        with torch.no_grad():
            embedding = self.embedding_model(input_ids)
        
        return embedding.cpu().numpy()[0]
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None
    ):
        """添加文檔到知識庫"""
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        print(f"\n📚 添加 {len(texts)} 個文檔...")
        
        documents = []
        for i, (text, metadata) in enumerate(zip(texts, metadatas)):
            # 生成嵌入
            embedding = self.encode_text(text)
            
            # 創建文檔
            doc = Document(
                text=text,
                metadata=metadata,
                embedding=embedding
            )
            documents.append(doc)
            
            if (i + 1) % 10 == 0:
                print(f"  處理進度: {i + 1}/{len(texts)}")
        
        # 添加到存儲
        self.vector_store.add_documents(documents)
        
        print("✅ 文檔添加完成")
    
    def build_index(self):
        """構建檢索索引"""
        self.vector_store.build_index()
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[RetrievalResult]:
        """檢索相關文檔"""
        if top_k is None:
            top_k = self.top_k
        if score_threshold is None:
            score_threshold = self.score_threshold
        
        # 編碼查詢
        query_embedding = self.encode_text(query)
        
        # 檢索
        results = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        return results
    
    def generate_with_context(
        self,
        query: str,
        retrieval_results: List[RetrievalResult],
        max_new_tokens: int = 100,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9
    ) -> Tuple[str, List[RetrievalResult]]:
        """使用檢索到的上下文生成回答"""
        
        # 構建增強提示
        context_parts = []
        for result in retrieval_results:
            context_parts.append(f"[文檔 {result.rank}] {result.document.text}")
        
        context = "\n".join(context_parts)
        
        # 構建完整提示
        prompt = f"""基於以下參考文檔回答問題：

{context}

問題：{query}
回答："""
        
        # 編碼
        token_ids = self.tokenizer.encode(prompt, add_special_tokens=False)
        
        # 截斷（保留空間給生成）
        max_prompt_length = self.max_context_length - max_new_tokens
        if len(token_ids) > max_prompt_length:
            token_ids = token_ids[:max_prompt_length]
        
        input_ids = torch.tensor([token_ids]).to(self.device)
        
        # 生成
        with torch.no_grad():
            output = self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                use_cache=True
            )
        
        # 解碼
        generated_text = self.tokenizer.decode(
            output[0].tolist(),
            skip_special_tokens=True
        )
        
        return generated_text, retrieval_results
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        max_new_tokens: int = 100,
        temperature: float = 0.7,
        show_sources: bool = True
    ) -> Dict:
        """完整的 RAG 查詢流程"""
        
        print(f"\n{'='*70}")
        print(f"🔍 問題：{question}")
        print(f"{'='*70}")
        
        # 1. 檢索相關文檔
        print("\n📖 檢索相關文檔...")
        retrieval_results = self.retrieve(query=question, top_k=top_k)
        
        if not retrieval_results:
            print("⚠️  未找到相關文檔")
            return {
                'question': question,
                'answer': "抱歉，我在知識庫中沒有找到相關信息。",
                'sources': [],
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"✅ 找到 {len(retrieval_results)} 個相關文檔")
        
        if show_sources:
            for result in retrieval_results:
                print(f"   [{result.rank}] 相似度: {result.score:.3f} | {result.document.text[:80]}...")
        
        # 2. 生成回答
        print("\n🤖 生成回答...")
        answer, sources = self.generate_with_context(
            query=question,
            retrieval_results=retrieval_results,
            max_new_tokens=max_new_tokens,
            temperature=temperature
        )
        
        print(f"\n💡 回答：{answer}")
        
        # 構建結果
        result = {
            'question': question,
            'answer': answer,
            'sources': [
                {
                    'rank': r.rank,
                    'text': r.document.text,
                    'score': r.score,
                    'metadata': r.document.metadata
                }
                for r in sources
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def save_knowledge_base(self, save_path: Union[str, Path]):
        """保存知識庫"""
        self.vector_store.save(save_path)
    
    def load_knowledge_base(self, load_path: Union[str, Path]):
        """載入知識庫"""
        self.vector_store = VectorStore.load(load_path)


def create_rag_system(
    model_path: str = "model/tiny_llm_en_zh_trained",
    device: Optional[str] = None
) -> RAGSystem:
    """創建 RAG 系統的便捷函數"""
    import sys
    from pathlib import Path
    
    # 添加路徑
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
    from src.bioneuronai.bilingual_tokenizer import BilingualTokenizer
    
    # 設備
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    print("\n🚀 創建 RAG 系統...")
    print(f"   模型路徑: {model_path}")
    print(f"   設備: {device}")
    
    # 載入模型
    model_path_obj = Path(model_path)
    
    # 載入配置
    with open(model_path_obj / "config.json", 'r') as f:
        config_dict = json.load(f)
    
    config = TinyLLMConfig(
        vocab_size=config_dict["vocab_size"],
        max_seq_length=config_dict["max_position_embeddings"],
        embed_dim=config_dict["hidden_size"],
        num_heads=config_dict["num_attention_heads"],
        num_layers=config_dict["num_hidden_layers"],
    )
    
    # 載入模型
    model = TinyLLM(config)
    weights = torch.load(
        model_path_obj / "pytorch_model.bin",
        map_location=device
    )
    model.load_state_dict(weights)
    model.to(device)
    model.eval()
    
    # 載入分詞器
    tokenizer = BilingualTokenizer.load(str(model_path_obj / "tokenizer.pkl"))
    
    # 創建 RAG 系統
    rag_system = RAGSystem(
        model=model,
        tokenizer=tokenizer,
        embed_dim=384,
        device=device
    )
    
    print("✅ RAG 系統創建完成")
    
    return rag_system


def main():
    """演示 RAG 系統"""
    print("=" * 80)
    print("RAG (Retrieval-Augmented Generation) 系統演示")
    print("=" * 80)
    
    # 創建 RAG 系統
    rag = create_rag_system()
    
    # 添加知識庫文檔
    print("\n" + "=" * 80)
    print("步驟 1: 構建知識庫")
    print("=" * 80)
    
    documents = [
        "Python 是一種高級編程語言，以簡潔和可讀性著稱。",
        "機器學習是人工智慧的一個分支，讓電腦能從數據中學習。",
        "深度學習使用多層神經網絡來處理複雜的模式識別任務。",
        "PyTorch 是一個流行的深度學習框架，由 Facebook 開發。",
        "Transformer 是一種基於注意力機制的神經網絡架構。",
        "RAG 系統結合了檢索和生成，可以基於外部知識回答問題。",
        "向量數據庫用於存儲和檢索高維向量表示的數據。",
        "自然語言處理讓電腦能夠理解和生成人類語言。",
    ]
    
    metadatas = [
        {"source": "Python教程", "category": "編程語言"},
        {"source": "AI基礎", "category": "機器學習"},
        {"source": "AI基礎", "category": "深度學習"},
        {"source": "框架文檔", "category": "工具"},
        {"source": "論文", "category": "架構"},
        {"source": "RAG文檔", "category": "系統"},
        {"source": "數據庫", "category": "存儲"},
        {"source": "NLP", "category": "技術"},
    ]
    
    rag.add_documents(documents, metadatas)
    rag.build_index()
    
    # 查詢示例
    print("\n" + "=" * 80)
    print("步驟 2: RAG 查詢")
    print("=" * 80)
    
    questions = [
        "什麼是 Python？",
        "深度學習是什麼？",
        "RAG 系統如何工作？",
    ]
    
    for question in questions:
        rag.query(
            question=question,
            top_k=3,
            max_new_tokens=50,
            temperature=0.7
        )
    
    # 保存知識庫
    print("\n" + "=" * 80)
    print("步驟 3: 保存知識庫")
    print("=" * 80)
    
    rag.save_knowledge_base("knowledge_base.json")
    
    print("\n✅ RAG 系統演示完成！")


if __name__ == "__main__":
    main()
