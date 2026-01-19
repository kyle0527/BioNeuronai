"""
AI 自我進化系統 (Self-Improvement System)
==========================================
通過用戶反饋和自我評估實現持續進化

核心機制：
1. 對話記錄與評分
2. 錯誤案例收集
3. 自動生成改進訓練數據
4. 週期性微調
"""

import torch
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class Interaction:
    """交互記錄"""
    timestamp: str
    user_input: str
    model_output: str
    confidence_score: float
    user_feedback: Optional[str] = None  # "good", "bad", "excellent"
    user_rating: Optional[int] = None  # 1-5 stars
    error_type: Optional[str] = None  # "factual", "logic", "unhelpful"
    correct_answer: Optional[str] = None  # 用戶提供的正確答案
    context: Optional[Dict] = None
    
    def to_training_sample(self) -> Optional[Dict]:
        """轉換為訓練樣本"""
        if self.user_feedback == "good" or self.user_feedback == "excellent":
            return {
                "input": self.user_input,
                "output": self.model_output,
                "quality": "high" if self.user_feedback == "excellent" else "medium"
            }
        elif self.correct_answer:
            # 用戶糾正了錯誤
            return {
                "input": self.user_input,
                "output": self.correct_answer,
                "quality": "corrected",
                "original_error": self.model_output
            }
        return None


class SelfImprovementSystem:
    """AI 自我進化系統"""
    
    def __init__(self, data_dir: str = "./evolution_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 交互歷史
        self.interactions: List[Interaction] = []
        self.interactions_file = self.data_dir / "interactions.jsonl"
        
        # 待改進的案例
        self.improvement_cases_file = self.data_dir / "improvement_cases.json"
        
        # 新生成的訓練數據
        self.new_training_data_file = self.data_dir / "new_training_data.json"
        
        # 統計
        self.stats: Dict[str, Any] = {
            "total_interactions": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "corrections_received": 0,
            "training_samples_generated": 0,
            "positive_rate": 0.0
        }
        
        self._load_data()
    
    def record_interaction(
        self,
        user_input: str,
        model_output: str,
        confidence_score: float,
        context: Optional[Dict] = None
    ) -> str:
        """
        記錄一次交互
        
        Returns:
            interaction_id: 用於後續反饋
        """
        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            model_output=model_output,
            confidence_score=confidence_score,
            context=context
        )
        
        self.interactions.append(interaction)
        self.stats["total_interactions"] += 1
        
        # 持久化
        self._save_interaction(interaction)
        
        # 生成 ID
        interaction_id = hashlib.md5(
            f"{interaction.timestamp}{user_input}".encode()
        ).hexdigest()[:8]
        
        return interaction_id
    
    def add_feedback(
        self,
        interaction_id: str,
        feedback: str,
        rating: Optional[int] = None,
        correct_answer: Optional[str] = None,
        error_type: Optional[str] = None
    ):
        """
        添加用戶反饋
        
        Args:
            interaction_id: 交互 ID
            feedback: "good", "bad", "excellent"
            rating: 1-5 星評分
            correct_answer: 正確答案（如果模型錯了）
            error_type: 錯誤類型
        """
        # 找到對應的交互（簡化版，實際應該用 ID 索引）
        if self.interactions:
            interaction = self.interactions[-1]  # 假設是最近的
            interaction.user_feedback = feedback
            interaction.user_rating = rating
            interaction.correct_answer = correct_answer
            interaction.error_type = error_type
            
            # 更新統計
            if feedback in ["good", "excellent"]:
                self.stats["positive_feedback"] += 1
            elif feedback == "bad":
                self.stats["negative_feedback"] += 1
            
            if correct_answer:
                self.stats["corrections_received"] += 1
            
            # 保存改進案例
            if feedback == "bad" or correct_answer:
                self._save_improvement_case(interaction)
    
    def generate_training_data(
        self,
        min_confidence: float = 0.7,
        min_rating: int = 4
    ) -> List[Dict]:
        """
        從高質量交互生成新訓練數據
        
        Args:
            min_confidence: 最低信心閾值
            min_rating: 最低評分
            
        Returns:
            新的訓練樣本列表
        """
        new_samples = []
        
        for interaction in self.interactions:
            # 只選擇高質量的交互
            if (interaction.confidence_score >= min_confidence and
                interaction.user_feedback in ["good", "excellent"] and
                (interaction.user_rating is None or interaction.user_rating >= min_rating)):
                
                sample = interaction.to_training_sample()
                if sample:
                    new_samples.append(sample)
            
            # 或者用戶糾正的答案
            elif interaction.correct_answer:
                sample = interaction.to_training_sample()
                if sample:
                    new_samples.append(sample)
        
        # 保存新訓練數據
        if new_samples:
            self._save_training_data(new_samples)
            self.stats["training_samples_generated"] += len(new_samples)
        
        return new_samples
    
    def analyze_weaknesses(self) -> Dict[str, Any]:
        """
        分析模型的弱點
        
        Returns:
            弱點分析報告
        """
        weaknesses = {
            "low_confidence_topics": [],
            "common_errors": {},
            "improvement_areas": []
        }
        
        # 分析低信心回答
        low_conf_interactions = [
            i for i in self.interactions 
            if i.confidence_score < 0.5
        ]
        
        # 提取主題（簡化版）
        for interaction in low_conf_interactions[:10]:
            weaknesses["low_confidence_topics"].append({
                "input": interaction.user_input[:100],
                "confidence": interaction.confidence_score
            })
        
        # 統計錯誤類型
        for interaction in self.interactions:
            if interaction.error_type:
                error_type = interaction.error_type
                weaknesses["common_errors"][error_type] = \
                    weaknesses["common_errors"].get(error_type, 0) + 1
        
        # 改進建議
        if weaknesses["common_errors"]:
            top_errors = sorted(
                weaknesses["common_errors"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for error_type, count in top_errors:
                weaknesses["improvement_areas"].append({
                    "area": error_type,
                    "frequency": count,
                    "suggestion": self._get_improvement_suggestion(error_type)
                })
        
        return weaknesses
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        if self.stats["total_interactions"] > 0:
            self.stats["positive_rate"] = float(
                self.stats["positive_feedback"] / 
                self.stats["total_interactions"]
            )
        
        return self.stats
    
    def _save_interaction(self, interaction: Interaction):
        """保存交互記錄"""
        with open(self.interactions_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(interaction), ensure_ascii=False) + '\n')
    
    def _save_improvement_case(self, interaction: Interaction):
        """保存待改進案例"""
        cases = []
        if self.improvement_cases_file.exists():
            with open(self.improvement_cases_file, 'r', encoding='utf-8') as f:
                cases = json.load(f)
        
        cases.append(asdict(interaction))
        
        with open(self.improvement_cases_file, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
    
    def _save_training_data(self, samples: List[Dict]):
        """保存新訓練數據"""
        existing = []
        if self.new_training_data_file.exists():
            with open(self.new_training_data_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        
        existing.extend(samples)
        
        with open(self.new_training_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    
    def _load_data(self):
        """載入已有數據"""
        if self.interactions_file.exists():
            with open(self.interactions_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.interactions.append(Interaction(**data))
            
            self.stats["total_interactions"] = len(self.interactions)
            self.stats["positive_feedback"] = sum(
                1 for i in self.interactions 
                if i.user_feedback in ["good", "excellent"]
            )
            self.stats["negative_feedback"] = sum(
                1 for i in self.interactions 
                if i.user_feedback == "bad"
            )
    
    def _get_improvement_suggestion(self, error_type: str) -> str:
        """根據錯誤類型給出改進建議"""
        suggestions = {
            "factual": "增加事實性知識訓練數據，啟用 RAG 檢索",
            "logic": "增加邏輯推理訓練樣本",
            "unhelpful": "改進回答的實用性和具體性",
            "hallucination": "降低生成溫度，提高誠實生成閾值"
        }
        return suggestions.get(error_type, "需要更多訓練數據")


def create_self_improvement_system(data_dir: str = "./evolution_data") -> SelfImprovementSystem:
    """便捷函數：創建自我進化系統"""
    return SelfImprovementSystem(data_dir)


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AI 自我進化系統演示")
    print("=" * 80)
    
    # 創建系統
    system = create_self_improvement_system()
    
    # 模擬一些交互
    print("\n1️⃣ 記錄交互")
    id1 = system.record_interaction(
        user_input="什麼是 Python?",
        model_output="Python 是一種流行的編程語言...",
        confidence_score=0.92
    )
    print(f"   交互已記錄: {id1}")
    
    # 添加正面反饋
    print("\n2️⃣ 添加正面反饋")
    system.add_feedback(id1, feedback="excellent", rating=5)
    print("   ✅ 用戶給予 5 星好評")
    
    # 記錄一個低質量的回答
    print("\n3️⃣ 記錄錯誤回答")
    id2 = system.record_interaction(
        user_input="2050 年的首都在哪？",
        model_output="2050 年的首都是火星城。",
        confidence_score=0.3
    )
    
    # 用戶糾正
    system.add_feedback(
        id2,
        feedback="bad",
        error_type="hallucination",
        correct_answer="我無法預測 2050 年的事情，這超出我的知識範圍。"
    )
    print("   ❌ 用戶指出錯誤並提供正確答案")
    
    # 生成新訓練數據
    print("\n4️⃣ 生成新訓練數據")
    new_samples = system.generate_training_data(min_confidence=0.7)
    print(f"   📚 生成了 {len(new_samples)} 個新訓練樣本")
    
    # 分析弱點
    print("\n5️⃣ 分析模型弱點")
    weaknesses = system.analyze_weaknesses()
    print(f"   🔍 發現 {len(weaknesses['low_confidence_topics'])} 個低信心主題")
    print(f"   🐛 常見錯誤: {weaknesses['common_errors']}")
    
    # 統計
    print("\n6️⃣ 整體統計")
    stats = system.get_statistics()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    print("\n" + "=" * 80)
    print("💡 下一步：用新訓練數據進行微調訓練")
    print("=" * 80)
