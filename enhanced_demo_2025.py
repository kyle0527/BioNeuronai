"""
BioNeuronAI 2025 完整演示
========================

展示最新的AI架構優化和RAG集成功能
"""

import numpy as np
import time
import json
from typing import Dict, List, Any

def print_header(title: str):
    """打印標題"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_section(title: str):
    """打印節標題"""
    print(f"\n--- {title} ---")

def print_results(results: Dict[str, Any]):
    """格式化打印結果"""
    for key, value in results.items():
        if isinstance(value, (int, float)):
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        elif isinstance(value, list) and len(value) > 0:
            print(f"  {key}: {len(value)} items")
        elif isinstance(value, dict):
            print(f"  {key}: {len(value)} keys")
        else:
            print(f"  {key}: {value}")

def demo_enhanced_core():
    """演示增強核心功能"""
    print_header("BioNeuronAI 增強核心演示 - 2025優化版")
    
    try:
        # 導入組件
        from bioneuronai import (
            EnhancedBioCore, AttentionConfig, MemoryConfig, MoEConfig
        )
        
        print_section("1. 初始化增強核心")
        
        # 配置參數
        attention_config = AttentionConfig(
            num_heads=8,
            head_dim=64,
            use_sparse=True,
            sparse_ratio=0.1
        )
        
        memory_config = MemoryConfig(
            working_memory_size=256,
            episodic_memory_size=500,
            semantic_memory_size=2000
        )
        
        moe_config = MoEConfig(
            num_experts=6,
            top_k_experts=2
        )
        
        # 創建增強核心
        core = EnhancedBioCore(
            input_dim=512,
            hidden_dims=[1024, 2048, 1024, 512],
            output_dim=256,
            attention_config=attention_config,
            memory_config=memory_config,
            moe_config=moe_config,
            enable_rag=True
        )
        
        print(f"✅ 增強核心初始化成功")
        print(f"  總參數量: {core.count_parameters():,}")
        
        print_section("2. 基本前向傳播")
        
        # 測試基本前向傳播
        test_input = np.random.randn(512).astype(np.float32)
        
        start_time = time.time()
        result = core.forward(test_input, use_attention=True, use_memory=True, use_moe=True)
        processing_time = time.time() - start_time
        
        print(f"✅ 前向傳播完成")
        print(f"  處理時間: {processing_time:.4f}秒")
        print(f"  輸出值: {result['output']:.6f}")
        print(f"  層數輸出: {len(result['layer_outputs'])}層")
        
        if result['moe_info']:
            print(f"  選中專家: {result['moe_info']['selected_experts']}")
            print(f"  專家權重: {[f'{w:.3f}' for w in result['moe_info']['expert_weights']]}")
        
        print_section("3. 記憶系統測試")
        
        # 添加多個輸入來測試記憶
        test_inputs = [
            np.random.randn(512).astype(np.float32) * 0.5,
            np.random.randn(512).astype(np.float32) * 1.0,
            np.random.randn(512).astype(np.float32) * 1.5,
        ]
        
        for i, inp in enumerate(test_inputs):
            result = core.forward(inp, context={'test_id': i})
            print(f"  輸入 {i+1}: 輸出 = {result['output']:.6f}")
        
        # 檢查記憶統計
        stats = core.get_system_statistics()
        print(f"✅ 記憶系統統計:")
        print_results(stats['memory_stats'])
        
        print_section("4. 學習能力測試")
        
        # 創建學習數據
        learning_inputs = [np.random.randn(512).astype(np.float32) for _ in range(5)]
        learning_targets = [np.array([i * 0.1]) for i in range(5)]
        
        print("開始學習...")
        start_time = time.time()
        core.learn(learning_inputs, learning_targets, learning_rate=0.01, epochs=3)
        learning_time = time.time() - start_time
        
        print(f"✅ 學習完成，耗時: {learning_time:.2f}秒")
        
        # 測試學習效果
        test_result = core.forward(learning_inputs[0])
        print(f"  學習前目標: {learning_targets[0][0]:.3f}")
        print(f"  學習後輸出: {test_result['output']:.3f}")
        
        print_section("5. 系統統計總覽")
        final_stats = core.get_system_statistics()
        print_results(final_stats)
        
        return core
        
    except ImportError as e:
        print(f"❌ 增強核心組件導入失敗: {e}")
        return None
    except Exception as e:
        print(f"❌ 增強核心演示失敗: {e}")
        return None

def demo_rag_system():
    """演示RAG系統功能"""
    print_header("RAG (檢索增強生成) 系統演示")
    
    try:
        from bioneuronai import BioRAGSystem, Document
        
        print_section("1. 初始化RAG系統")
        
        rag_system = BioRAGSystem(
            db_path="demo_rag.db",
            embedding_dim=768
        )
        
        print("✅ RAG系統初始化成功")
        
        print_section("2. 添加知識文檔")
        
        # 添加一些示例文檔
        documents = [
            {
                'content': """
                人工智能(AI)是指由機器展現出的智能行為。現代AI主要基於深度學習和神經網路。
                大型語言模型如GPT、Claude等能夠理解和生成自然語言，在各個領域都有廣泛應用。
                """,
                'metadata': {'category': 'AI基礎', 'language': 'zh'}
            },
            {
                'content': """
                RAG(Retrieval-Augmented Generation)是一種結合資訊檢索和文本生成的技術。
                它能夠從知識庫中檢索相關信息，然後基於檢索到的內容生成準確的回答。
                這種方法有效減少了大型語言模型的幻覺問題。
                """,
                'metadata': {'category': 'RAG技術', 'language': 'zh'}
            },
            {
                'content': """
                生物啟發式神經網路模擬大腦神經元的工作原理。這包括Hebbian學習、
                時間記憶、新奇性檢測等機制。BioNeuronAI就是基於這些原理構建的工具包。
                """,
                'metadata': {'category': 'BioNeuronAI', 'language': 'zh'}
            },
            {
                'content': """
                2024-2025年AI發展趨勢包括：混合架構模型、多模態集成、長上下文處理、
                參數效率優化、邊緣AI部署等。這些技術正在推動AI向更高效、更智能的方向發展。
                """,
                'metadata': {'category': 'AI趨勢', 'language': 'zh'}
            }
        ]
        
        doc_ids = []
        for i, doc_data in enumerate(documents):
            doc_id = rag_system.add_document(
                content=doc_data['content'],
                doc_id=f"demo_doc_{i+1}",
                metadata=doc_data['metadata']
            )
            doc_ids.append(doc_id)
            print(f"  📄 添加文檔: {doc_id}")
        
        print(f"✅ 成功添加 {len(doc_ids)} 個文檔")
        
        print_section("3. 查詢測試")
        
        queries = [
            "什麼是RAG技術？",
            "BioNeuronAI有什麼特點？",
            "2025年AI發展趨勢是什麼？",
            "深度學習和神經網路的關係？"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n查詢 {i}: {query}")
            
            start_time = time.time()
            result = rag_system.query(query, max_docs=2)
            query_time = time.time() - start_time
            
            print(f"  ⏱️  查詢時間: {query_time:.3f}秒")
            print(f"  📚 檢索文檔數: {len(result['sources'])}")
            print(f"  🎯 相關性分數: {result['retrieval_scores']}")
            print(f"  💬 回答: {result['response'][:100]}...")
        
        print_section("4. RAG統計信息")
        stats = rag_system.get_statistics()
        print_results(stats)
        
        return rag_system
        
    except ImportError as e:
        print(f"❌ RAG系統組件導入失敗: {e}")
        return None
    except Exception as e:
        print(f"❌ RAG系統演示失敗: {e}")
        return None

def demo_integration():
    """演示核心+RAG集成功能"""
    print_header("增強核心 + RAG集成演示")
    
    try:
        from bioneuronai import EnhancedBioCore
        
        print_section("1. 初始化集成系統")
        
        core = EnhancedBioCore(
            input_dim=256,
            hidden_dims=[512, 1024, 512],
            output_dim=128,
            enable_rag=True,
            rag_db_path="integration_demo.db"
        )
        
        print("✅ 集成系統初始化成功")
        
        print_section("2. 添加領域知識")
        
        knowledge_docs = [
            "神經可塑性是大腦適應和學習的基礎機制。",
            "Hebbian學習規則：一起放電的神經元會加強連接。",
            "注意力機制幫助模型聚焦於重要信息。",
            "稀疏連接可以提高神經網路的效率。"
        ]
        
        for doc in knowledge_docs:
            doc_id = core.add_knowledge(doc)
            print(f"  ➕ 添加知識: {doc_id}")
        
        print_section("3. 知識增強推理")
        
        # 測試輸入
        test_input = np.random.randn(256).astype(np.float32)
        
        # 不使用RAG的推理
        result_no_rag = core.forward(test_input, use_memory=True)
        
        # 使用RAG的推理
        result_with_rag = core.forward(
            test_input, 
            use_memory=True,
            query_rag="什麼是神經可塑性？"
        )
        
        print(f"  🧠 無RAG輸出: {result_no_rag['output']:.6f}")
        print(f"  📚 有RAG輸出: {result_with_rag['output']:.6f}")
        
        if result_with_rag['rag_context']:
            print(f"  📖 RAG來源數量: {len(result_with_rag['rag_context']['sources'])}")
            print(f"  ⚡ RAG檢索時間: {result_with_rag['rag_context']['retrieval_time']:.3f}秒")
        
        print_section("4. 直接知識查詢")
        
        knowledge_queries = [
            "什麼是Hebbian學習？",
            "注意力機制的作用是什麼？",
            "稀疏連接有什麼好處？"
        ]
        
        for query in knowledge_queries:
            result = core.query_knowledge(query)
            print(f"  ❓ 查詢: {query}")
            print(f"  💡 回答: {result['response'][:80]}...")
            print()
        
        return core
        
    except Exception as e:
        print(f"❌ 集成演示失敗: {e}")
        return None

def demo_optimization_insights():
    """演示AI優化建議"""
    print_header("2024-2025 AI優化建議")
    
    try:
        from bioneuronai import (
            AI_ARCHITECTURE_TRENDS_2024_2025,
            RAG_OPTIMIZATION_STRATEGIES,
            IMPLEMENTATION_PRIORITY,
            ROADMAP_2025
        )
        
        print_section("1. AI架構趨勢")
        for trend, info in list(AI_ARCHITECTURE_TRENDS_2024_2025.items())[:3]:
            print(f"📊 {trend}")
            print(f"  描述: {info['description']}")
            if 'benefits' in info:
                print(f"  優勢: {', '.join(info['benefits'][:2])}")
            print()
        
        print_section("2. RAG優化策略")
        strategies = RAG_OPTIMIZATION_STRATEGIES['檢索策略']
        print(f"🎯 混合檢索組件: {', '.join(strategies['hybrid_retrieval']['components'])}")
        print(f"🔄 融合方法: {', '.join(strategies['hybrid_retrieval']['fusion_methods'])}")
        
        print_section("3. 實現優先級")
        for priority, tasks in IMPLEMENTATION_PRIORITY.items():
            print(f"⭐ {priority}")
            for task in tasks[:2]:
                print(f"  - {task}")
            print()
        
        print_section("4. 2025技術路線圖")
        for quarter, info in list(ROADMAP_2025.items())[:2]:
            print(f"📅 {quarter}: {info['目標']}")
            for task in info['任務'][:2]:
                print(f"  • {task}")
            print()
        
    except ImportError as e:
        print(f"❌ 優化建議組件導入失敗: {e}")
    except Exception as e:
        print(f"❌ 優化建議演示失敗: {e}")

def performance_benchmark():
    """性能基準測試"""
    print_header("性能基準測試")
    
    try:
        from bioneuronai import EnhancedBioCore, MegaBioNet, NetworkTopology
        
        print_section("1. 核心架構對比")
        
        # 測試數據
        test_sizes = [100, 500, 1000]
        
        for size in test_sizes:
            print(f"\n測試輸入大小: {size}")
            
            # 增強核心測試
            try:
                core = EnhancedBioCore(
                    input_dim=size,
                    hidden_dims=[size*2, size*4, size*2],
                    output_dim=size//2,
                    enable_rag=False  # 關閉RAG以純測試計算
                )
                
                test_input = np.random.randn(size).astype(np.float32)
                
                # 預熱
                core.forward(test_input)
                
                # 正式測試
                times = []
                for _ in range(5):
                    start = time.time()
                    result = core.forward(test_input)
                    times.append(time.time() - start)
                
                avg_time = np.mean(times)
                params = core.count_parameters()
                
                print(f"  🚀 增強核心: {avg_time:.4f}秒, {params:,}參數")
                
            except Exception as e:
                print(f"  ❌ 增強核心測試失敗: {e}")
            
            # Mega核心測試 (如果可用)
            try:
                topology = NetworkTopology(
                    input_dim=size,
                    hidden_layers=[size*2, size*3, size*2],
                    output_dim=size//2
                )
                
                mega_net = MegaBioNet(topology, sparsity=0.9)
                
                # 預熱
                mega_net.forward(test_input)
                
                # 正式測試
                times = []
                for _ in range(5):
                    start = time.time()
                    result = mega_net.forward(test_input)
                    times.append(time.time() - start)
                
                avg_time = np.mean(times)
                params = topology.total_parameters
                
                print(f"  ⚡ Mega核心: {avg_time:.4f}秒, {params:,}參數")
                
            except Exception as e:
                print(f"  ❌ Mega核心測試失敗: {e}")
        
        print_section("2. 記憶體使用分析")
        
        # 簡單的記憶體使用估算
        test_dims = [512, 1024, 2048]
        
        for dim in test_dims:
            try:
                core = EnhancedBioCore(
                    input_dim=dim,
                    hidden_dims=[dim*2, dim*3, dim*2],
                    output_dim=dim,
                    enable_rag=False
                )
                
                params = core.count_parameters()
                # 估算記憶體使用 (假設 float32)
                memory_mb = (params * 4) / (1024 * 1024)
                
                print(f"  📊 維度 {dim}: {params:,}參數, ~{memory_mb:.1f}MB")
                
            except Exception as e:
                print(f"  ❌ 維度 {dim} 測試失敗: {e}")
        
    except Exception as e:
        print(f"❌ 性能基準測試失敗: {e}")

def main():
    """主演示函數"""
    print("🧠 BioNeuronAI 2025 - 完整功能演示")
    print("基於最新AI研究趨勢的生物啟發式神經網路系統")
    print("包含RAG集成、注意力機制、記憶系統和專家混合等先進特性")
    
    try:
        # 1. 增強核心演示
        enhanced_core = demo_enhanced_core()
        
        # 2. RAG系統演示  
        rag_system = demo_rag_system()
        
        # 3. 集成功能演示
        integrated_system = demo_integration()
        
        # 4. AI優化建議
        demo_optimization_insights()
        
        # 5. 性能基準測試
        performance_benchmark()
        
        print_header("演示總結")
        print("✅ 增強核心演示完成" if enhanced_core else "❌ 增強核心演示失敗")
        print("✅ RAG系統演示完成" if rag_system else "❌ RAG系統演示失敗")
        print("✅ 集成功能演示完成" if integrated_system else "❌ 集成功能演示失敗")
        
        print("\n🎉 BioNeuronAI 2025演示完成！")
        print("\n主要成果:")
        print("• 實現了基於2024-2025最新研究的AI架構優化")
        print("• 集成了完整的RAG檢索增強生成系統")
        print("• 添加了生物啟發的注意力機制和記憶系統") 
        print("• 實現了混合專家(MoE)架構")
        print("• 提供了完整的性能評估和優化建議")
        
        print(f"\n📈 系統規模:")
        if enhanced_core:
            stats = enhanced_core.get_system_statistics()
            print(f"• 增強核心參數: {enhanced_core.count_parameters():,}")
            print(f"• 前向傳播次數: {stats['forward_count']}")
            print(f"• 平均處理時間: {stats['avg_processing_time']:.4f}秒")
        
        if rag_system:
            rag_stats = rag_system.get_statistics()
            print(f"• RAG知識庫文檔: {rag_stats['total_documents']}")
            print(f"• RAG查詢次數: {rag_stats['total_queries']}")
            print(f"• 平均檢索時間: {rag_stats['avg_retrieval_time']:.4f}秒")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用戶中斷")
    except Exception as e:
        print(f"\n❌ 演示過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()