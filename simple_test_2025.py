"""
BioNeuronAI 簡化測試 - 2025版本
============================

測試核心功能是否正常工作
"""

import numpy as np
import time
import sys
import traceback

def test_basic_import():
    """測試基本導入"""
    print("🔍 測試基本導入...")
    try:
        import bioneuronai as bna
        print(f"✅ BioNeuronAI 導入成功，版本: {getattr(bna, '__version__', 'unknown')}")
        print(f"  可用組件: {len(bna.__all__)}")
        return True
    except Exception as e:
        print(f"❌ 基本導入失敗: {e}")
        return False

def test_mega_core():
    """測試Mega核心"""
    print("\n🧠 測試Mega核心...")
    try:
        from bioneuronai import MegaBioNet, NetworkTopology
        
        # 創建小型網路
        topology = NetworkTopology(
            input_dim=100,
            hidden_layers=[200, 300, 200],
            output_dim=50
        )
        
        net = MegaBioNet(topology, sparsity=0.8)
        print(f"✅ MegaBioNet 創建成功")
        print(f"  設計參數量: {topology.total_parameters:,}")
        print(f"  實際參數量: {net.count_parameters():,}")
        
        # 測試前向傳播
        test_input = np.random.randn(100).astype(np.float32)
        output = net.forward(test_input)
        print(f"  前向傳播輸出: {output.shape if hasattr(output, 'shape') else type(output)}")
        
        return True
    except Exception as e:
        print(f"❌ Mega核心測試失敗: {e}")
        traceback.print_exc()
        return False

def test_rag_system():
    """測試RAG系統"""
    print("\n📚 測試RAG系統...")
    try:
        from bioneuronai import BioRAGSystem
        
        rag = BioRAGSystem(
            db_path="test_rag.db",
            embedding_dim=512
        )
        print("✅ RAG系統創建成功")
        
        # 添加測試文檔
        doc_id = rag.add_document("這是一個測試文檔，包含一些基本信息。")
        print(f"  文檔添加成功: {doc_id}")
        
        # 測試查詢
        result = rag.query("測試信息", max_docs=1)
        print(f"  查詢結果: {len(result.get('sources', []))} 個來源")
        
        return True
    except Exception as e:
        print(f"❌ RAG系統測試失敗: {e}")
        traceback.print_exc()
        return False

def test_ai_optimization():
    """測試AI優化配置"""
    print("\n🚀 測試AI優化配置...")
    try:
        from bioneuronai import (
            AI_ARCHITECTURE_TRENDS_2024_2025,
            RAG_OPTIMIZATION_STRATEGIES
        )
        
        print("✅ AI優化配置導入成功")
        print(f"  架構趨勢數量: {len(AI_ARCHITECTURE_TRENDS_2024_2025)}")
        print(f"  RAG策略數量: {len(RAG_OPTIMIZATION_STRATEGIES)}")
        
        # 顯示一些關鍵信息
        for trend in list(AI_ARCHITECTURE_TRENDS_2024_2025.keys())[:2]:
            print(f"    - {trend}")
        
        return True
    except Exception as e:
        print(f"❌ AI優化配置測試失敗: {e}")
        return False

def test_performance():
    """簡單性能測試"""
    print("\n⚡ 簡單性能測試...")
    try:
        from bioneuronai import MegaBioNet, NetworkTopology
        
        # 測試不同大小
        sizes = [50, 100, 200]
        
        for size in sizes:
            topology = NetworkTopology(
                input_dim=size,
                hidden_layers=[size*2, size*3, size*2],
                output_dim=size
            )
            
            net = MegaBioNet(topology, sparsity=0.9)
            test_input = np.random.randn(size).astype(np.float32)
            
            # 計時
            start_time = time.time()
            output = net.forward(test_input)
            duration = time.time() - start_time
            
            print(f"  大小 {size}: {duration:.4f}秒, 參數 {net.count_parameters():,}")
            
        return True
    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🧬 BioNeuronAI 2025 - 簡化測試")
    print("=" * 50)
    
    tests = [
        ("基本導入", test_basic_import),
        ("Mega核心", test_mega_core),
        ("RAG系統", test_rag_system),
        ("AI優化配置", test_ai_optimization),
        ("性能測試", test_performance)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ {name}測試異常: {e}")
            results[name] = False
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 測試總結:")
    
    passed = sum(results.values())
    total = len(results)
    
    for name, passed_test in results.items():
        status = "✅ 通過" if passed_test else "❌ 失敗"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 總體結果: {passed}/{total} 測試通過 ({100*passed/total:.1f}%)")
    
    if passed == total:
        print("🎉 所有測試都通過了！BioNeuronAI 2025已準備就緒。")
    elif passed > 0:
        print("⚠️  部分功能正常工作，需要進一步調試。")
    else:
        print("😞 所有測試都失敗了，需要檢查安裝和配置。")

if __name__ == "__main__":
    main()