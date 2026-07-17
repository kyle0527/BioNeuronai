"""
RAG 系統使用工具
==============
方便地使用 RAG 系統進行知識問答

功能：
- 構建知識庫
- 交互式問答
- 批量查詢
- 知識庫管理
"""

import sys
from pathlib import Path
import json
import argparse
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.bioneuronai.rag_system import create_rag_system, Document


def build_knowledge_base(rag, documents_file: Optional[str] = None):
    """構建知識庫"""
    print("\n" + "=" * 80)
    print("📚 構建知識庫")
    print("=" * 80)
    
    documents = []
    metadatas = []
    
    if documents_file:
        # 從文件載入
        print(f"從文件載入：{documents_file}")
        
        with open(documents_file, 'r', encoding='utf-8') as f:
            if documents_file.endswith('.json'):
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, str):
                            documents.append(item)
                            metadatas.append({})
                        elif isinstance(item, dict):
                            documents.append(item.get('text', ''))
                            metadatas.append(item.get('metadata', {}))
            else:
                # 純文本文件，每行一個文檔
                for line in f:
                    line = line.strip()
                    if line:
                        documents.append(line)
                        metadatas.append({})
    else:
        # 默認示例文檔
        print("使用示例文檔")
        documents = [
            "BioNeuronAI 是一個先進的深度學習框架，專注於生物神經網絡模擬。",
            "TinyLLM 是一個輕量級的語言模型，支持英中雙語處理。",
            "KV Cache 技術可以將文本生成速度提升 2-5 倍。",
            "誠實生成模組能讓模型在不確定時承認不知道。",
            "RAG 系統結合檢索和生成，提供基於知識庫的精準回答。",
            "模型支持 ONNX、TorchScript 和 SafeTensors 格式導出。",
            "LoRA 微調技術只需訓練少量參數就能適配新任務。",
            "模型量化可以將模型大小減少 50-75%，保持性能。",
            "Beam Search 可以生成更高質量的文本。",
            "不確定性量化通過熵值評估模型的置信度。",
            "幻覺檢測模組識別生成內容中的重複和矛盾。",
            "批量推理支持同時處理多個輸入，提高效率。",
            "流式生成允許逐 token 輸出，提升用戶體驗。",
            "混合精度訓練可以節省 50% 內存並加速訓練。",
            "梯度累積允許使用更大的有效批次大小。",
        ]
        
        metadatas = [
            {"category": "項目介紹", "source": "README"},
            {"category": "模型", "source": "文檔"},
            {"category": "優化", "source": "功能列表"},
            {"category": "功能", "source": "誠實生成"},
            {"category": "功能", "source": "RAG"},
            {"category": "導出", "source": "工具"},
            {"category": "微調", "source": "LoRA"},
            {"category": "優化", "source": "量化"},
            {"category": "生成", "source": "算法"},
            {"category": "評估", "source": "不確定性"},
            {"category": "檢測", "source": "幻覺"},
            {"category": "推理", "source": "批量"},
            {"category": "生成", "source": "流式"},
            {"category": "訓練", "source": "混合精度"},
            {"category": "訓練", "source": "梯度"},
        ]
    
    print(f"\n添加 {len(documents)} 個文檔...")
    rag.add_documents(documents, metadatas)
    rag.build_index()
    
    return len(documents)


def interactive_mode(rag):
    """交互式問答模式"""
    print("\n" + "=" * 80)
    print("💬 交互式 RAG 問答")
    print("=" * 80)
    print("命令:")
    print("  /help     - 顯示幫助")
    print("  /sources  - 切換顯示來源")
    print("  /topk N   - 設置檢索數量")
    print("  /save     - 保存知識庫")
    print("  /quit     - 退出")
    print("=" * 80 + "\n")
    
    show_sources = True
    top_k = 5
    
    while True:
        try:
            question = input("你的問題: ").strip()
            
            if not question:
                continue
            
            # 命令處理
            if question.startswith('/'):
                if question == '/quit':
                    print("\n👋 再見！")
                    break
                
                elif question == '/help':
                    print("\n命令列表:")
                    print("  /help     - 顯示此幫助")
                    print("  /sources  - 切換顯示/隱藏來源文檔")
                    print("  /topk N   - 設置檢索文檔數量（默認 5）")
                    print("  /save     - 保存知識庫到文件")
                    print("  /quit     - 退出交互模式")
                
                elif question == '/sources':
                    show_sources = not show_sources
                    print(f"\n來源顯示: {'開啟' if show_sources else '關閉'}")
                
                elif question.startswith('/topk'):
                    try:
                        parts = question.split()
                        if len(parts) == 2:
                            top_k = int(parts[1])
                            print(f"\n檢索數量設置為: {top_k}")
                        else:
                            print("\n用法: /topk N （N 為數字）")
                    except ValueError:
                        print("\n錯誤: 請輸入有效的數字")
                
                elif question == '/save':
                    filename = f"knowledge_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    rag.save_knowledge_base(filename)
                    print(f"\n✅ 知識庫已保存: {filename}")
                
                else:
                    print("\n❌ 未知命令，輸入 /help 查看幫助")
                
                continue
            
            # 正常問答
            result = rag.query(
                question=question,
                top_k=top_k,
                max_new_tokens=100,
                temperature=0.7,
                show_sources=show_sources
            )
            
            print()  # 空行
            
        except KeyboardInterrupt:
            print("\n\n👋 再見！")
            break
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")


def batch_query(rag, questions_file: str, output_file: Optional[str] = None):
    """批量查詢"""
    print("\n" + "=" * 80)
    print("📋 批量查詢")
    print("=" * 80)
    
    # 載入問題
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = [line.strip() for line in f if line.strip()]
    
    print(f"載入 {len(questions)} 個問題")
    
    # 批量處理
    results = []
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] 處理中...")
        
        result = rag.query(
            question=question,
            top_k=5,
            max_new_tokens=100,
            show_sources=False
        )
        
        results.append(result)
    
    # 保存結果
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 結果已保存: {output_file}")
    
    return results


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="BioNeuronAI RAG 系統工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--model",
        default="models/tiny_llm_en_zh_trained",
        help="模型路徑"
    )
    
    parser.add_argument(
        "--mode",
        choices=["interactive", "batch", "build"],
        default="interactive",
        help="運行模式"
    )
    
    parser.add_argument(
        "--documents",
        help="文檔文件路徑（用於構建知識庫）"
    )
    
    parser.add_argument(
        "--questions",
        help="問題文件路徑（用於批量查詢）"
    )
    
    parser.add_argument(
        "--output",
        help="輸出文件路徑"
    )
    
    parser.add_argument(
        "--kb-load",
        help="載入已有知識庫"
    )
    
    parser.add_argument(
        "--kb-save",
        help="保存知識庫路徑"
    )
    
    args = parser.parse_args()
    
    try:
        # 創建 RAG 系統
        print(f"\n🚀 初始化 RAG 系統")
        rag = create_rag_system(args.model)
        
        # 載入或構建知識庫
        if args.kb_load:
            print(f"\n📖 載入知識庫: {args.kb_load}")
            rag.load_knowledge_base(args.kb_load)
        else:
            build_knowledge_base(rag, args.documents)
        
        # 根據模式運行
        if args.mode == "interactive":
            interactive_mode(rag)
        
        elif args.mode == "batch":
            if not args.questions:
                print("❌ 批量模式需要 --questions 參數")
                return 1
            
            batch_query(rag, args.questions, args.output)
        
        elif args.mode == "build":
            # 只構建知識庫（已經在上面完成）
            print("\n✅ 知識庫構建完成")
        
        # 保存知識庫
        if args.kb_save:
            rag.save_knowledge_base(args.kb_save)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())
