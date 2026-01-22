"""
AI  (Self-Improvement System)
==========================================



1. 
2. 
3. 
4. 
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
    """"""
    timestamp: str
    user_input: str
    model_output: str
    confidence_score: float
    user_feedback: Optional[str] = None  # "good", "bad", "excellent"
    user_rating: Optional[int] = None  # 1-5 stars
    error_type: Optional[str] = None  # "factual", "logic", "unhelpful"
    correct_answer: Optional[str] = None  # 
    context: Optional[Dict] = None
    
    def to_training_sample(self) -> Optional[Dict]:
        """"""
        if self.user_feedback == "good" or self.user_feedback == "excellent":
            return {
                "input": self.user_input,
                "output": self.model_output,
                "quality": "high" if self.user_feedback == "excellent" else "medium"
            }
        elif self.correct_answer:
            # 
            return {
                "input": self.user_input,
                "output": self.correct_answer,
                "quality": "corrected",
                "original_error": self.model_output
            }
        return None


class SelfImprovementSystem:
    """AI """
    
    def __init__(self, data_dir: str = "./evolution_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 
        self.interactions: List[Interaction] = []
        self.interactions_file = self.data_dir / "interactions.jsonl"
        
        # 
        self.improvement_cases_file = self.data_dir / "improvement_cases.json"
        
        # 
        self.new_training_data_file = self.data_dir / "new_training_data.json"
        
        # 
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
        
        
        Returns:
            interaction_id: 
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
        
        # 
        self._save_interaction(interaction)
        
        #  ID
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
        
        
        Args:
            interaction_id:  ID
            feedback: "good", "bad", "excellent"
            rating: 1-5 
            correct_answer: 
            error_type: 
        """
        #  ID 
        if self.interactions:
            interaction = self.interactions[-1]  # 
            interaction.user_feedback = feedback
            interaction.user_rating = rating
            interaction.correct_answer = correct_answer
            interaction.error_type = error_type
            
            # 
            if feedback in ["good", "excellent"]:
                self.stats["positive_feedback"] += 1
            elif feedback == "bad":
                self.stats["negative_feedback"] += 1
            
            if correct_answer:
                self.stats["corrections_received"] += 1
            
            # 
            if feedback == "bad" or correct_answer:
                self._save_improvement_case(interaction)
    
    def generate_training_data(
        self,
        min_confidence: float = 0.7,
        min_rating: int = 4
    ) -> List[Dict]:
        """
        
        
        Args:
            min_confidence: 
            min_rating: 
            
        Returns:
            
        """
        new_samples = []
        
        for interaction in self.interactions:
            # 
            if (interaction.confidence_score >= min_confidence and
                interaction.user_feedback in ["good", "excellent"] and
                (interaction.user_rating is None or interaction.user_rating >= min_rating)):
                
                sample = interaction.to_training_sample()
                if sample:
                    new_samples.append(sample)
            
            # 
            elif interaction.correct_answer:
                sample = interaction.to_training_sample()
                if sample:
                    new_samples.append(sample)
        
        # 
        if new_samples:
            self._save_training_data(new_samples)
            self.stats["training_samples_generated"] += len(new_samples)
        
        return new_samples
    
    def analyze_weaknesses(self) -> Dict[str, Any]:
        """
        
        
        Returns:
            
        """
        weaknesses = {
            "low_confidence_topics": [],
            "common_errors": {},
            "improvement_areas": []
        }
        
        # 
        low_conf_interactions = [
            i for i in self.interactions 
            if i.confidence_score < 0.5
        ]
        
        # 
        for interaction in low_conf_interactions[:10]:
            weaknesses["low_confidence_topics"].append({
                "input": interaction.user_input[:100],
                "confidence": interaction.confidence_score
            })
        
        # 
        for interaction in self.interactions:
            if interaction.error_type:
                error_type = interaction.error_type
                weaknesses["common_errors"][error_type] = \
                    weaknesses["common_errors"].get(error_type, 0) + 1
        
        # 
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
        """"""
        if self.stats["total_interactions"] > 0:
            self.stats["positive_rate"] = float(
                self.stats["positive_feedback"] / 
                self.stats["total_interactions"]
            )
        
        return self.stats
    
    def _save_interaction(self, interaction: Interaction):
        """"""
        with open(self.interactions_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(interaction), ensure_ascii=False) + '\n')
    
    def _save_improvement_case(self, interaction: Interaction):
        """"""
        cases = []
        if self.improvement_cases_file.exists():
            with open(self.improvement_cases_file, 'r', encoding='utf-8') as f:
                cases = json.load(f)
        
        cases.append(asdict(interaction))
        
        with open(self.improvement_cases_file, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
    
    def _save_training_data(self, samples: List[Dict]):
        """"""
        existing = []
        if self.new_training_data_file.exists():
            with open(self.new_training_data_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        
        existing.extend(samples)
        
        with open(self.new_training_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    
    def _load_data(self):
        """"""
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
        """"""
        suggestions = {
            "factual": " RAG ",
            "logic": "",
            "unhelpful": "",
            "hallucination": ""
        }
        return suggestions.get(error_type, "")


def create_self_improvement_system(data_dir: str = "./evolution_data") -> SelfImprovementSystem:
    """"""
    return SelfImprovementSystem(data_dir)


# ============================================================================
# 
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AI ")
    print("=" * 80)
    
    # 
    system = create_self_improvement_system()
    
    # 
    print("\n1⃣ ")
    id1 = system.record_interaction(
        user_input=" Python?",
        model_output="Python ...",
        confidence_score=0.92
    )
    print(f"   : {id1}")
    
    # 
    print("\n2⃣ ")
    system.add_feedback(id1, feedback="excellent", rating=5)
    print("     5 ")
    
    # 
    print("\n3⃣ ")
    id2 = system.record_interaction(
        user_input="2050 ",
        model_output="2050 ",
        confidence_score=0.3
    )
    
    # 
    system.add_feedback(
        id2,
        feedback="bad",
        error_type="hallucination",
        correct_answer=" 2050 "
    )
    print("    ")
    
    # 
    print("\n4⃣ ")
    new_samples = system.generate_training_data(min_confidence=0.7)
    print(f"     {len(new_samples)} ")
    
    # 
    print("\n5⃣ ")
    weaknesses = system.analyze_weaknesses()
    print(f"     {len(weaknesses['low_confidence_topics'])} ")
    print(f"    : {weaknesses['common_errors']}")
    
    # 
    print("\n6⃣ ")
    stats = system.get_statistics()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    print("\n" + "=" * 80)
    print(" ")
    print("=" * 80)
