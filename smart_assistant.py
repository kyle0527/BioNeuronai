#!/usr/bin/env python3
"""
智能學習助手 - 從你的代碼和操作中學習，提供個性化建議
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, TYPE_CHECKING

sys.path.insert(0, 'src')

if TYPE_CHECKING:
    # Let type checkers know the real type (silence analyzer warnings)
    from bioneuronai.improved_core import ImprovedBioNeuron  # type: ignore
else:
    try:
        # Normal runtime import
        from bioneuronai.improved_core import ImprovedBioNeuron
    except Exception:
        # Minimal runtime stub if the real implementation is unavailable
        class ImprovedBioNeuron:
            def __init__(self, *args, **kwargs):
                pass

            def predict(self, *args, **kwargs):
                return None

            def train(self, *args, **kwargs):
                return None


class SmartLearningAssistant:
    """智能學習助手 - 觀察、學習、建議"""
    
    def __init__(self) -> None:
        self.data_dir = Path("ai_learning_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 神經網絡 - 學習你的編碼習慣
        self.code_pattern_neuron = ImprovedBioNeuron(num_inputs=15, learning_rate=0.05)
        self.error_pattern_neuron = ImprovedBioNeuron(num_inputs=10, learning_rate=0.05)
        
        # 知識庫
        self.knowledge_base = self._load_knowledge()
        
    def _load_knowledge(self) -> Dict[str, Any]:
        """加載已學習的知識"""
        kb_file = self.data_dir / "knowledge_base.json"
        
        if kb_file.exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                data: Dict[str, Any] = json.load(f)
                return data
        
        result: Dict[str, Any] = {
            'frequent_errors': {},
            'coding_patterns': [],
            'improvement_history': [],
            'learned_solutions': {}
        }
        return result
    
    def _save_knowledge(self) -> None:
        """保存學習的知識"""
        kb_file = self.data_dir / "knowledge_base.json"
        
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
    
    def analyze_and_learn(self, workspace_dir: str = ".") -> Dict[str, Any]:
        """分析工作區並學習"""
        workspace = Path(workspace_dir)
        
        print("🧠 開始智能分析和學習...")
        
        insights = {
            'code_health': self._assess_code_health(workspace),
            'common_patterns': self._identify_patterns(workspace),
            'personalized_tips': self._generate_personalized_tips(),
            'next_steps': self._suggest_next_steps()
        }
        
        return insights
    
    def _assess_code_health(self, workspace: Path) -> Dict[str, Any]:
        """評估代碼健康度"""
        python_files = list(workspace.glob("**/*.py"))
        python_files = [f for f in python_files if '__pycache__' not in str(f)]
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for file in python_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    total_lines += len(content.split('\n'))
                    total_functions += content.count('def ')
                    total_classes += content.count('class ')
            except Exception:
                pass
        
        avg_lines_per_func = total_lines / max(total_functions, 1)
        
        health_score = 100
        
        if avg_lines_per_func > 50:
            health_score -= 20
        if total_classes < 5 and total_functions > 50:
            health_score -= 15
        
        return {
            'score': health_score,
            'total_files': len(python_files),
            'total_lines': total_lines,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'avg_lines_per_function': round(avg_lines_per_func, 1),
            'assessment': self._health_assessment(health_score)
        }
    
    def _health_assessment(self, score: float) -> str:
        """健康評估"""
        if score >= 90:
            return "優秀 ✨ - 代碼質量很高"
        elif score >= 75:
            return "良好 👍 - 有一些改進空間"
        elif score >= 60:
            return "一般 🤔 - 需要注意代碼質量"
        else:
            return "需要改進 ⚠️ - 建議重構"
    
    def _identify_patterns(self, workspace: Path) -> List[str]:
        """識別代碼模式"""
        patterns = []
        
        python_files = list(workspace.glob("**/*.py"))
        python_files = [f for f in python_files if '__pycache__' not in str(f)]
        
        has_tests = any('test' in str(f).lower() for f in python_files)
        has_docs = any('doc' in str(f).lower() or str(f).endswith('README.md') for f in workspace.glob("**/*"))
        has_config = any(str(f).endswith(('.yaml', '.yml', '.toml', '.ini')) for f in workspace.glob("*"))
        
        if has_tests:
            patterns.append("✅ 有測試文件 - 這是好習慣")
        else:
            patterns.append("❌ 缺少測試 - 建議添加單元測試")
        
        if has_docs:
            patterns.append("✅ 有文檔 - 便於協作")
        else:
            patterns.append("❌ 缺少文檔 - 建議添加 README 和註釋")
        
        if has_config:
            patterns.append("✅ 有配置文件 - 結構清晰")
        
        return patterns
    
    def _generate_personalized_tips(self) -> List[str]:
        """生成個性化建議"""
        tips = []
        
        # 基於知識庫的建議
        if 'frequent_errors' in self.knowledge_base:
            top_errors = sorted(
                self.knowledge_base['frequent_errors'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            if top_errors:
                tips.append("📌 你常遇到的問題:")
                for error, count in top_errors:
                    tips.append(f"   • {error} (出現 {count} 次)")
        
        # 通用建議
        tips.extend([
            "💡 每天寫完代碼後運行一次代碼分析",
            "💡 使用 git commit 前先運行測試",
            "💡 定期重構，保持代碼簡潔",
            "💡 為複雜函數添加文檔字符串"
        ])
        
        return tips
    
    def _suggest_next_steps(self) -> List[str]:
        """建議下一步行動"""
        return [
            "1️⃣ 運行 'python ai_coding_assistant.py' 查看代碼問題",
            "2️⃣ 處理所有嚴重問題 (紅色)",
            "3️⃣ 添加或更新測試用例",
            "4️⃣ 運行 'black .' 格式化代碼",
            "5️⃣ 提交代碼前運行 'mypy .' 類型檢查"
        ]
    
    def learn_from_fix(self, error_type: str, solution: str) -> None:
        """從修復中學習"""
        if 'frequent_errors' not in self.knowledge_base:
            self.knowledge_base['frequent_errors'] = {}
        
        self.knowledge_base['frequent_errors'][error_type] = \
            self.knowledge_base['frequent_errors'].get(error_type, 0) + 1
        
        if 'learned_solutions' not in self.knowledge_base:
            self.knowledge_base['learned_solutions'] = {}
        
        self.knowledge_base['learned_solutions'][error_type] = solution
        
        self._save_knowledge()
        print(f"✅ 已學習: {error_type}")
    
    def display_insights(self, insights: Dict[str, Any]) -> None:
        """顯示分析結果"""
        print("\n" + "=" * 80)
        print("🧠 智能分析報告")
        print("=" * 80)
        
        # 代碼健康度
        health = insights['code_health']
        print(f"\n📊 代碼健康度: {health['score']}/100")
        print(f"   {health['assessment']}")
        print(f"   • 總文件: {health['total_files']}")
        print(f"   • 總代碼行: {health['total_lines']}")
        print(f"   • 函數數: {health['total_functions']}")
        print(f"   • 類數: {health['total_classes']}")
        print(f"   • 平均函數長度: {health['avg_lines_per_function']} 行")
        
        # 代碼模式
        print("\n🔍 代碼模式識別:")
        for pattern in insights['common_patterns']:
            print(f"   {pattern}")
        
        # 個性化建議
        print("\n💡 個性化建議:")
        for tip in insights['personalized_tips']:
            print(f"   {tip}")
        
        # 下一步
        print("\n🎯 建議的下一步:")
        for step in insights['next_steps']:
            print(f"   {step}")
        
        print("\n" + "=" * 80)


def main() -> None:
    """主函數"""
    print("🤖 智能學習助手")
    print("💪 我會學習你的編碼習慣，提供個性化建議幫你提升\n")
    
    assistant = SmartLearningAssistant()
    
    # 分析並學習
    insights = assistant.analyze_and_learn("src/bioneuronai")
    
    # 顯示結果
    assistant.display_insights(insights)
    
    # 互動學習
    print("\n💬 想要記錄剛解決的問題嗎？(輸入 q 退出)")
    print("   示例: 輸入問題類型和解決方案")
    print("   格式: 問題類型 | 解決方案")
    print("   例如: 類型錯誤 | 使用 typing 模塊添加類型註解")
    
    while True:
        try:
            user_input = input("\n🔧 > ").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit', '']:
                break
            
            if '|' in user_input:
                error_type, solution = user_input.split('|', 1)
                assistant.learn_from_fix(error_type.strip(), solution.strip())
                print("👍 很好！我記住了這個解決方案")
            else:
                print("❌ 格式錯誤，請使用: 問題類型 | 解決方案")
        
        except KeyboardInterrupt:
            break
    
    print("\n👋 下次見！繼續加油！")


if __name__ == "__main__":
    main()
