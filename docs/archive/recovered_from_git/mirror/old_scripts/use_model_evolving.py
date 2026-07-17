"""
具備自我進化能力的 AI 使用工具
================================
整合反饋收集和持續改進功能

使用方式：
python use_model_evolving.py --enable-evolution
"""

import torch
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
from src.bioneuronai.bilingual_tokenizer import BilingualTokenizer
from src.bioneuronai.self_improvement import create_self_improvement_system
from src.bioneuronai.uncertainty_quantification import UncertaintyQuantifier


class EvolvingAI:
    """具備自我進化能力的 AI 系統"""
    
    def __init__(
        self,
        model_path: str = "./models/tiny_llm_en_zh_trained",
        enable_evolution: bool = True
    ):
        print("=" * 80)
        print("🧬 初始化自我進化 AI 系統")
        print("=" * 80)
        
        # 載入模型
        print("\n📦 載入模型...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        with open(Path(model_path) / "config.json", 'r') as f:
            config_dict = json.load(f)
        
        self.config = TinyLLMConfig(**config_dict)
        self.model = TinyLLM(self.config).to(self.device)
        
        # 載入權重
        weights_file = Path(model_path) / "pytorch_model.bin"
        if weights_file.exists():
            self.model.load_state_dict(torch.load(weights_file, map_location=self.device))
            print(f"   ✅ 已載入訓練權重")
        
        self.model.eval()
        
        # 載入分詞器
        vocab_file = Path(model_path) / "vocab.json"
        if vocab_file.exists():
            self.tokenizer = BilingualTokenizer.load(str(model_path))
        else:
            self.tokenizer = BilingualTokenizer()
        
        # 不確定性量化器
        self.uncertainty = UncertaintyQuantifier()
        
        # 自我進化系統
        self.evolution_enabled = enable_evolution
        if self.evolution_enabled:
            self.evolution_system = create_self_improvement_system()
            print("   🧬 自我進化系統已啟用")
        
        # 對話歷史
        self.conversation_history = []
        
        print(f"\n✅ 系統初始化完成 (設備: {self.device})")
        print("=" * 80)
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 50,
        temperature: float = 0.7,
        record_interaction: bool = True
    ) -> dict:
        """
        生成回應
        
        Returns:
            {
                "response": str,
                "confidence": float,
                "interaction_id": str (如果啟用進化)
            }
        """
        # 編碼
        input_ids = torch.tensor(
            [self.tokenizer.encode(prompt)],
            device=self.device
        )
        
        # 生成
        with torch.no_grad():
            output_ids = self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature
            )
        
        # 解碼
        response = self.tokenizer.decode(output_ids[0].tolist())
        
        # 計算信心分數（使用簡單估計，因為 generate() 不返回 logits）
        output_length = len(output_ids[0]) - len(input_ids[0])
        # 長度越短通常代表越確定，但這只是一個簡單估計
        confidence = min(1.0, max(0.3, 1.0 - output_length / max_new_tokens * 0.5))
        
        result = {
            "response": response,
            "confidence": confidence
        }
        
        # 記錄交互（如果啟用進化）
        if self.evolution_enabled and record_interaction:
            interaction_id = self.evolution_system.record_interaction(
                user_input=prompt,
                model_output=response,
                confidence_score=confidence
            )
            result["interaction_id"] = interaction_id
        
        return result
    
    def chat(self, user_input: str):
        """對話模式"""
        print(f"\n你: {user_input}")
        
        # 生成回應
        result = self.generate(user_input)
        response = result["response"]
        confidence = result["confidence"]
        
        # 顯示回應
        print(f"AI: {response}")
        print(f"💯 信心分數: {confidence:.2%}")
        
        # 如果信心低，提示用戶
        if confidence < 0.5:
            print("⚠️  注意：AI 對這個回答不太確定")
        
        # 詢問反饋（如果啟用進化）
        if self.evolution_enabled:
            interaction_id = result.get("interaction_id")
            if interaction_id:
                self._collect_feedback(interaction_id)
        
        # 記錄歷史
        self.conversation_history.append({
            "user": user_input,
            "ai": response,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })
    
    def _collect_feedback(self, interaction_id: str):
        """收集用戶反饋"""
        print("\n📝 請評價這次回答 (可選，按 Enter 跳過):")
        print("   1) 👍 很好")
        print("   2) 👌 還可以")  
        print("   3) 👎 不好")
        print("   4) ✏️  糾正錯誤")
        
        try:
            choice = input("   選擇 (1-4 或 Enter): ").strip()
            
            if not choice:
                return
            
            if choice == "1":
                self.evolution_system.add_feedback(
                    interaction_id,
                    feedback="excellent",
                    rating=5
                )
                print("   ✅ 感謝反饋！這將幫助 AI 進化")
            
            elif choice == "2":
                self.evolution_system.add_feedback(
                    interaction_id,
                    feedback="good",
                    rating=3
                )
                print("   ✅ 感謝反饋！")
            
            elif choice == "3":
                error_type = input("   錯誤類型 (factual/logic/unhelpful): ").strip()
                self.evolution_system.add_feedback(
                    interaction_id,
                    feedback="bad",
                    error_type=error_type or "unhelpful"
                )
                print("   ✅ 已記錄，AI 會從錯誤中學習")
            
            elif choice == "4":
                correct_answer = input("   正確答案是: ").strip()
                if correct_answer:
                    self.evolution_system.add_feedback(
                        interaction_id,
                        feedback="bad",
                        correct_answer=correct_answer,
                        error_type="factual"
                    )
                    print("   ✅ 感謝糾正！AI 會記住這個")
        
        except KeyboardInterrupt:
            print("\n   (已跳過)")
    
    def interactive_mode(self):
        """交互模式"""
        print("\n" + "=" * 80)
        print("🤖 歡迎使用自我進化 AI 系統")
        print("=" * 80)
        print("\n命令:")
        print("  /stats    - 查看進化統計")
        print("  /evolve   - 生成新訓練數據")
        print("  /analyze  - 分析弱點")
        print("  /help     - 幫助")
        print("  /quit     - 退出")
        print("\n" + "=" * 80 + "\n")
        
        while True:
            try:
                user_input = input("你: ").strip()
                
                if not user_input:
                    continue
                
                # 命令處理
                if user_input == "/quit":
                    print("\n👋 再見！")
                    break
                
                elif user_input == "/stats":
                    self._show_evolution_stats()
                
                elif user_input == "/evolve":
                    self._generate_evolution_data()
                
                elif user_input == "/analyze":
                    self._analyze_weaknesses()
                
                elif user_input == "/help":
                    print("\n💡 提示:")
                    print("   • 每次對話後都可以評分")
                    print("   • AI 會記錄你的反饋")
                    print("   • 定期用 /evolve 生成新訓練數據")
                    print("   • 用新數據重新訓練模型即可進化\n")
                
                else:
                    # 正常對話
                    self.chat(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 再見！")
                break
            except Exception as e:
                print(f"\n❌ 錯誤: {e}\n")
    
    def _show_evolution_stats(self):
        """顯示進化統計"""
        if not self.evolution_enabled:
            print("   ⚠️  自我進化系統未啟用")
            return
        
        stats = self.evolution_system.get_statistics()
        
        print("\n" + "=" * 60)
        print("📊 AI 進化統計")
        print("=" * 60)
        print(f"  總交互次數: {stats['total_interactions']}")
        print(f"  正面反饋: {stats['positive_feedback']}")
        print(f"  負面反饋: {stats['negative_feedback']}")
        print(f"  收到糾正: {stats['corrections_received']}")
        print(f"  生成訓練樣本: {stats['training_samples_generated']}")
        
        if stats['total_interactions'] > 0:
            positive_rate = stats['positive_feedback'] / stats['total_interactions']
            print(f"  滿意度: {positive_rate:.1%}")
        
        print("=" * 60 + "\n")
    
    def _generate_evolution_data(self):
        """生成進化訓練數據"""
        if not self.evolution_enabled:
            print("   ⚠️  自我進化系統未啟用")
            return
        
        print("\n🧬 正在生成新訓練數據...")
        new_samples = self.evolution_system.generate_training_data(
            min_confidence=0.7,
            min_rating=4
        )
        
        print(f"   ✅ 生成了 {len(new_samples)} 個新訓練樣本")
        print(f"   📁 已保存到: evolution_data/new_training_data.json")
        print("\n💡 下一步:")
        print("   1. 查看 evolution_data/new_training_data.json")
        print("   2. 將數據添加到 training/train_with_ai_teacher.py")
        print("   3. 重新訓練模型\n")
    
    def _analyze_weaknesses(self):
        """分析弱點"""
        if not self.evolution_enabled:
            print("   ⚠️  自我進化系統未啟用")
            return
        
        print("\n🔍 分析 AI 的弱點...")
        weaknesses = self.evolution_system.analyze_weaknesses()
        
        print("\n" + "=" * 60)
        print("📋 弱點分析報告")
        print("=" * 60)
        
        if weaknesses["low_confidence_topics"]:
            print("\n❓ 低信心主題:")
            for i, topic in enumerate(weaknesses["low_confidence_topics"][:5], 1):
                print(f"   {i}. {topic['input'][:60]}... (信心: {topic['confidence']:.2f})")
        
        if weaknesses["common_errors"]:
            print("\n🐛 常見錯誤:")
            for error_type, count in weaknesses["common_errors"].items():
                print(f"   • {error_type}: {count} 次")
        
        if weaknesses["improvement_areas"]:
            print("\n💡 改進建議:")
            for area in weaknesses["improvement_areas"]:
                print(f"   • {area['area']} ({area['frequency']} 次)")
                print(f"     建議: {area['suggestion']}")
        
        print("=" * 60 + "\n")


# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="自我進化 AI 系統")
    parser.add_argument("--model", default="./models/tiny_llm_en_zh_trained", help="模型路徑")
    parser.add_argument("--enable-evolution", action="store_true", default=True, help="啟用自我進化")
    parser.add_argument("--disable-evolution", action="store_true", help="禁用自我進化")
    
    args = parser.parse_args()
    
    # 創建系統
    ai = EvolvingAI(
        model_path=args.model,
        enable_evolution=not args.disable_evolution
    )
    
    # 啟動交互模式
    ai.interactive_mode()
