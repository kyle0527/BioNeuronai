#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG 系統測試腳本
================

測試 RAG 系統的完整功能和性能
"""

import sys
from pathlib import Path

# 添加 src 路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_embedding_service():
    """測試嵌入服務"""
    print("\n" + "="*60)
    print("測試 1: EmbeddingService - 文本向量化")
    print("="*60)
    
    try:
        from rag.core.embeddings import EmbeddingService, EmbeddingModel
        
        # 測試本地模型
        print("\n測試本地模型...")
        service = EmbeddingService(model=EmbeddingModel.LOCAL_MINILM)
        
        # 單文本嵌入
        text = "Bitcoin price analysis for trading strategy"
        result = service.embed(text)
        print("✅ 單文本嵌入成功")
        print(f"   - 模型: {result.model}")
        print(f"   - 維度: {result.dimensions}")
        print(f"   - 向量形狀: {result.embedding.shape}")
        
        # 批量嵌入
        texts = [
            "Bitcoin bullish trend confirmed",
            "Ethereum shows bearish divergence",
            "Market volatility increases"
        ]
        results = service.embed_batch(texts)
        print(f"\n✅ 批量嵌入成功: {len(results)} 個文本")
        
        # 相似度測試
        sim = service.cosine_similarity(results[0].embedding, results[1].embedding)
        print(f"\n✅ 相似度計算成功: {sim:.4f}")
        
        # 統計信息
        stats = service.get_stats()
        print("\n📊 統計信息:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_base():
    """測試知識庫"""
    print("\n" + "="*60)
    print("測試 2: InternalKnowledgeBase - 內部知識庫")
    print("="*60)
    
    try:
        from rag.core.embeddings import EmbeddingService, EmbeddingModel
        from rag.internal.knowledge_base import InternalKnowledgeBase, DocumentType
        
        # 初始化服務
        print("\n初始化知識庫...")
        embedding_service = EmbeddingService(model=EmbeddingModel.LOCAL_MINILM)
        kb = InternalKnowledgeBase(
            storage_path="./rag_test_data",
            embedding_service=embedding_service,
            auto_load=True
        )
        
        stats = kb.get_stats()
        print("✅ 知識庫初始化成功")
        print(f"   - 文檔總數: {stats['total_documents']}")
        print(f"   - 按類型: {stats['by_type']}")
        
        # 搜索測試
        print("\n測試搜索功能...")
        queries = [
            "風險管理規則",
            "止損策略",
            "新聞交易",
            "市場狀態判斷"
        ]
        
        for query in queries:
            results = kb.search(query, top_k=3)
            print(f"\n查詢: '{query}'")
            print(f"   找到 {len(results)} 個相關文檔:")
            for i, doc in enumerate(results, 1):
                print(f"   {i}. {doc.title} (相關性: {doc.score:.3f})")
        
        # 添加自定義文檔
        print("\n測試添加文檔...")
        doc = kb.add_document(
            doc_id="test_doc_1",
            title="測試交易規則",
            content="這是一個測試交易規則的內容，用於測試知識庫的添加功能。",
            doc_type=DocumentType.TRADING_RULE,
            tags=["test", "demo"]
        )
        print(f"✅ 添加文檔成功: {doc.title}")
        
        # 保存測試
        kb.save_to_storage()
        print("✅ 知識庫已保存")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_retriever():
    """測試統一檢索器"""
    print("\n" + "="*60)
    print("測試 3: UnifiedRetriever - 統一檢索器")
    print("="*60)
    
    try:
        from rag.core.embeddings import EmbeddingService, EmbeddingModel
        from rag.core.retriever import UnifiedRetriever, RetrievalQuery, RetrievalSource
        from rag.internal.knowledge_base import InternalKnowledgeBase
        
        # 初始化組件
        print("\n初始化檢索器...")
        embedding_service = EmbeddingService(model=EmbeddingModel.LOCAL_MINILM)
        kb = InternalKnowledgeBase(
            embedding_service=embedding_service,
            auto_load=True
        )
        
        retriever = UnifiedRetriever(
            embedding_service=embedding_service,
            internal_kb=kb
        )
        print("✅ 檢索器初始化成功")
        
        # 簡單查詢
        print("\n測試簡單查詢...")
        results = retriever.retrieve("止損策略")
        print(f"✅ 找到 {len(results)} 個結果")
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. {result.title or '無標題'}")
            print(f"      相關性: {result.relevance_score:.3f}")
            print(f"      來源: {result.source.value}")
        
        # 進階查詢
        print("\n測試進階查詢...")
        query = RetrievalQuery(
            query="交易風險控制",
            sources=[RetrievalSource.INTERNAL_KNOWLEDGE],
            top_k=5,
            min_relevance=0.3
        )
        results = retriever.retrieve(query)
        print(f"✅ 找到 {len(results)} 個高相關性結果")
        
        # 統計信息
        stats = retriever.get_stats()
        print("\n📊 檢索器狀態:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """測試整合功能"""
    print("\n" + "="*60)
    print("測試 4: 完整整合測試")
    print("="*60)
    
    try:
        from rag import (
            EmbeddingService,
            UnifiedRetriever,
            InternalKnowledgeBase,
            RetrievalQuery,
            RetrievalSource,
            get_rag_status
        )
        
        # 檢查狀態
        print("\n檢查 RAG 系統狀態...")
        status = get_rag_status()
        print("✅ 系統狀態:")
        for key, value in status.items():
            print(f"   - {key}: {value}")
        
        # 完整工作流程
        print("\n執行完整工作流程...")
        
        # 1. 初始化
        embedding_service = EmbeddingService()
        kb = InternalKnowledgeBase(embedding_service=embedding_service)
        retriever = UnifiedRetriever(
            embedding_service=embedding_service,
            internal_kb=kb
        )
        
        # 2. 添加業務數據
        kb.add_document(
            doc_id="strategy_001",
            title="比特幣趨勢策略",
            content="""
            比特幣趨勢交易策略：
            1. 使用 EMA 50/200 判斷主趨勢
            2. RSI > 50 確認多頭動能
            3. 成交量放大確認突破
            4. 風險管理：2% 止損，6% 止盈
            適用市場：強趨勢
            """,
            tags=["bitcoin", "trend", "strategy"]
        )
        
        kb.add_document(
            doc_id="risk_001",
            title="倉位管理規則",
            content="""
            倉位管理基本規則：
            1. 單筆交易不超過總資金 2%
            2. 總持倉不超過 20%
            3. 同類型幣種不超過 3 個
            4. 每日最多 5 筆新交易
            """,
            tags=["risk", "position", "management"]
        )
        
        print("✅ 已添加 2 個策略文檔")
        
        # 3. 執行交易決策查詢
        print("\n模擬交易決策查詢...")
        
        trading_query = """
        我想交易 BTCUSDT，當前市場顯示：
        - 價格突破 EMA 200
        - RSI 為 65
        - 成交量增加 30%
        
        請問我應該如何操作？需要注意哪些風險？
        """
        
        results = retriever.retrieve(
            RetrievalQuery(
                query=trading_query,
                sources=[RetrievalSource.INTERNAL_KNOWLEDGE],
                top_k=5,
                min_relevance=0.2
            )
        )
        
        print(f"\n📋 查詢結果 ({len(results)} 條):")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   相關性: {result.relevance_score:.3f}")
            print(f"   內容摘要: {result.content[:100]}...")
        
        print("\n✅ 整合測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """性能測試"""
    print("\n" + "="*60)
    print("測試 5: 性能基準測試")
    print("="*60)
    
    try:
        import time
        from rag.core.embeddings import EmbeddingService, EmbeddingModel
        from rag.internal.knowledge_base import InternalKnowledgeBase
        
        # 初始化
        embedding_service = EmbeddingService(
            model=EmbeddingModel.LOCAL_MINILM,
            cache_enabled=True
        )
        kb = InternalKnowledgeBase(embedding_service=embedding_service)
        
        # 測試嵌入速度
        print("\n測試嵌入速度...")
        texts = [f"Test embedding performance with text {i}" for i in range(100)]
        
        start = time.time()
        _ = embedding_service.embed_batch(texts)  # 僅測量性能，不使用結果
        elapsed = time.time() - start
        
        print("✅ 批量嵌入 100 個文本")
        print(f"   - 總時間: {elapsed:.2f}s")
        print(f"   - 平均: {elapsed/len(texts)*1000:.2f}ms/文本")
        print(f"   - 速度: {len(texts)/elapsed:.1f} 文本/秒")
        
        # 測試搜索速度
        print("\n測試搜索速度...")
        queries = [
            "risk management",
            "trading strategy",
            "market analysis",
            "stop loss",
            "position sizing"
        ]
        
        search_times = []
        for query in queries:
            start = time.time()
            _ = kb.search(query, top_k=5)  # 僅測量性能
            elapsed = time.time() - start
            search_times.append(elapsed)
        
        avg_search_time = sum(search_times) / len(search_times)
        print(f"✅ 執行了 {len(queries)} 次搜索")
        print(f"   - 平均時間: {avg_search_time*1000:.2f}ms")
        print(f"   - 最快: {min(search_times)*1000:.2f}ms")
        print(f"   - 最慢: {max(search_times)*1000:.2f}ms")
        
        # 緩存效果測試
        print("\n測試緩存效果...")
        test_text = "Test cache performance"
        
        # 第一次（無緩存）
        start = time.time()
        embedding_service.embed(test_text)
        time_no_cache = time.time() - start
        
        # 第二次（有緩存）
        start = time.time()
        embedding_service.embed(test_text)
        time_with_cache = time.time() - start
        
        print("✅ 緩存性能")
        print(f"   - 無緩存: {time_no_cache*1000:.2f}ms")
        print(f"   - 有緩存: {time_with_cache*1000:.2f}ms")
        print(f"   - 提速: {time_no_cache/time_with_cache:.1f}x")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試函數"""
    print("\n" + "="*60)
    print("🚀 BioNeuronAI RAG 系統測試套件")
    print("="*60)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("嵌入服務", test_embedding_service),
        ("知識庫", test_knowledge_base),
        ("統一檢索器", test_unified_retriever),
        ("整合功能", test_integration),
        ("性能基準", test_performance),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            success = test_func()
            results[name] = success
        except Exception as e:
            print(f"\n❌ 測試 '{name}' 發生異常: {e}")
            results[name] = False
    
    # 總結
    print("\n" + "="*60)
    print("📊 測試總結")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, success in results.items():
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"{status} - {name}")
    
    print(f"\n總計: {passed}/{total} 通過 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有測試通過！RAG 系統運作正常")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 個測試失敗，請檢查問題")
        return 1


if __name__ == "__main__":
    exit(main())
