"""
訓練數據管理器
=============
完整的訓練數據生成、管理和驗證系統

功能：
- 數據模板和生成器
- 數據質量驗證
- 數據集劃分（訓練/驗證/測試）
- 數據統計和可視化
- 數據導入導出
- 自動數據擴充
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import hashlib


@dataclass
class DataSample:
    """數據樣本"""
    id: str
    type: str  # conversation, knowledge, instruction, functional
    category: str  # search, judgment, reasoning, etc.
    input_text: str
    output_text: Optional[str] = None
    metadata: Optional[Dict] = None
    language: str = "mixed"  # en, zh, mixed
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # 自動檢測語言
        if self.language == "mixed":
            self.language = self._detect_language()
    
    def _detect_language(self) -> str:
        """檢測文本語言"""
        text = self.input_text + (self.output_text or "")
        
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        
        total = chinese_chars + english_chars
        if total == 0:
            return "unknown"
        
        zh_ratio = chinese_chars / total
        
        if zh_ratio > 0.7:
            return "zh"
        elif zh_ratio < 0.3:
            return "en"
        else:
            return "mixed"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DataSample':
        return cls(**data)


class DataGenerator:
    """數據生成器 - AI 老師風格"""
    
    def __init__(self):
        self.sample_id_counter = 0
    
    def generate_id(self) -> str:
        """生成唯一ID"""
        self.sample_id_counter += 1
        return f"sample_{self.sample_id_counter:06d}"
    
    def generate_conversations(self, count: int = 50) -> List[DataSample]:
        """生成對話數據"""
        templates = [
            # 中文對話
            {
                "inputs": ["你好", "您好", "嗨", "早安", "晚安"],
                "outputs": [
                    "你好！我是AI助手，很高興為你服務。",
                    "您好！有什麼我可以幫助你的嗎？",
                    "嗨！很高興見到你！",
                    "早安！希望你有美好的一天！",
                    "晚安！祝你有個好夢！"
                ]
            },
            # 英文對話
            {
                "inputs": ["Hello", "Hi", "Good morning", "Good evening"],
                "outputs": [
                    "Hello! I'm an AI assistant. How can I help you?",
                    "Hi there! What can I do for you today?",
                    "Good morning! Hope you have a great day!",
                    "Good evening! How may I assist you?"
                ]
            },
            # 功能查詢
            {
                "inputs": ["你能做什麼", "你的功能", "你會什麼"],
                "outputs": [
                    "我可以幫助你進行對話、回答問題、提供建議、處理文本等。",
                    "我具備對話、問答、分析、翻譯等多種能力。",
                    "我可以進行中英文對話、知識問答、文本分析等。"
                ]
            },
        ]
        
        samples = []
        for _ in range(count):
            template = random.choice(templates)
            input_text = random.choice(template["inputs"])
            output_text = random.choice(template["outputs"])
            
            samples.append(DataSample(
                id=self.generate_id(),
                type="conversation",
                category="general",
                input_text=input_text,
                output_text=output_text
            ))
        
        return samples
    
    def generate_knowledge(self, count: int = 50) -> List[DataSample]:
        """生成知識數據"""
        knowledge_base = [
            # AI/ML 知識
            "人工智慧是計算機科學的一個分支，致力於創造能夠模擬人類智能的系統。",
            "機器學習是AI的核心技術，通過數據和經驗來改進算法性能。",
            "深度學習使用多層神經網絡來學習數據的層次化表示。",
            "自然語言處理幫助計算機理解和生成人類語言。",
            "Artificial Intelligence is revolutionizing many industries.",
            "Machine learning algorithms can identify patterns in data.",
            "Deep learning has achieved remarkable results in image recognition.",
            "Natural language processing enables human-computer interaction.",
            
            # 編程知識
            "Python是一種高級編程語言，以其簡潔性和可讀性著稱。",
            "PyTorch是一個流行的深度學習框架，提供靈活的模型構建方式。",
            "Git是版本控制系統，幫助開發者管理代碼變更。",
            "Python is widely used in data science and AI development.",
            "PyTorch provides dynamic computational graphs for neural networks.",
            "Git enables collaborative software development.",
            
            # 通用知識
            "學習是一個持續的過程，需要堅持和耐心。",
            "溝通是人際交往的關鍵技能。",
            "創新思維能幫助我們解決複雜問題。",
            "Learning is a lifelong journey of discovery.",
            "Communication is essential for effective collaboration.",
            "Critical thinking helps us make better decisions.",
        ]
        
        samples = []
        for _ in range(count):
            knowledge = random.choice(knowledge_base)
            
            samples.append(DataSample(
                id=self.generate_id(),
                type="knowledge",
                category="general",
                input_text=knowledge,
                output_text=None
            ))
        
        return samples
    
    def generate_functional_data(self, count: int = 100) -> List[DataSample]:
        """生成功能性數據（搜索、判斷、推理等）"""
        
        functional_templates = {
            "search": [
                {
                    "input": "搜索關於{topic}的資料",
                    "output": "我會搜索{topic}相關內容。關鍵詞：{topic}、{related}。範圍：文檔、網頁、資料庫。",
                    "topics": ["機器學習", "Python", "深度學習", "AI"],
                    "related": ["算法", "框架", "應用", "理論"]
                },
                {
                    "input": "Find information about {topic}",
                    "output": "I'll search for {topic} information. Keywords: {topic}, {related}. Sources: documents, web, database.",
                    "topics": ["machine learning", "Python", "deep learning", "AI"],
                    "related": ["algorithms", "frameworks", "applications", "theory"]
                },
            ],
            "judgment": [
                {
                    "input": "判斷：{statement}",
                    "output": "分析：{analysis}。判斷：{result}。理由：{reason}。",
                    "statements": ["Python是編程語言", "地球是平的", "AI能思考", "1+1=2"],
                    "analyses": ["檢查事實", "評估證據", "邏輯推理", "常識判斷"],
                    "results": ["正確", "錯誤", "部分正確", "需要更多信息"],
                    "reasons": ["符合事實", "違背科學", "定義不清", "證據充分"]
                },
            ],
            "reasoning": [
                {
                    "input": "前提：{premise} 推理：",
                    "output": "根據前提：{premise}。邏輯推導：{logic}。結論：{conclusion}。",
                    "premises": ["所有人都會死，蘇格拉底是人", "如果下雨就帶傘，現在下雨了"],
                    "logics": ["三段論推理", "條件推理"],
                    "conclusions": ["所以蘇格拉底會死", "所以應該帶傘"]
                },
            ],
            "analysis": [
                {
                    "input": "分析：{data}",
                    "output": "數據：{data}。模式：{pattern}。分析：{analysis}。結論：{conclusion}。",
                    "data_points": ["銷售增長50%", "錯誤率下降", "用戶活躍度上升"],
                    "patterns": ["上升趨勢", "改善跡象", "正向指標"],
                    "analyses": ["可能原因分析", "影響因素", "相關性研究"],
                    "conclusions": ["表現良好", "需要保持", "值得關注"]
                },
            ],
        }
        
        samples = []
        for category, templates in functional_templates.items():
            for _ in range(count // len(functional_templates)):
                template = random.choice(templates)
                
                # 填充模板
                input_text = str(template["input"])
                output_text = str(template["output"])
                
                # 隨機替換占位符
                for key, values in template.items():
                    if key not in ["input", "output"] and isinstance(values, list):
                        value = random.choice(values)
                        placeholder = "{" + key.rstrip('s') + "}"
                        input_text = input_text.replace(placeholder, value)
                        output_text = output_text.replace(placeholder, value)
                
                samples.append(DataSample(
                    id=self.generate_id(),
                    type="functional",
                    category=category,
                    input_text=input_text,
                    output_text=output_text
                ))
        
        return samples


class DatasetManager:
    """數據集管理器"""
    
    def __init__(self, data_dir: str = "training/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.samples: List[DataSample] = []
    
    def add_samples(self, samples: List[DataSample]):
        """添加樣本"""
        self.samples.extend(samples)
        print(f"✅ 添加了 {len(samples)} 個樣本")
    
    def load_from_file(self, filepath: str):
        """從文件載入"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.samples = [DataSample.from_dict(d) for d in data]
        print(f"✅ 從 {filepath} 載入了 {len(self.samples)} 個樣本")
    
    def save_to_file(self, filepath: str):
        """保存到文件"""
        data = [s.to_dict() for s in self.samples]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 保存了 {len(self.samples)} 個樣本到 {filepath}")
    
    def split_dataset(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        shuffle: bool = True
    ) -> Tuple[List[DataSample], List[DataSample], List[DataSample]]:
        """劃分數據集"""
        
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "比例之和必須為1"
        
        samples = self.samples.copy()
        if shuffle:
            random.shuffle(samples)
        
        n = len(samples)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        train_set = samples[:train_end]
        val_set = samples[train_end:val_end]
        test_set = samples[val_end:]
        
        print("📊 數據集劃分:")
        print(f"   訓練集: {len(train_set)} ({len(train_set)/n*100:.1f}%)")
        print(f"   驗證集: {len(val_set)} ({len(val_set)/n*100:.1f}%)")
        print(f"   測試集: {len(test_set)} ({len(test_set)/n*100:.1f}%)")
        
        return train_set, val_set, test_set
    
    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        stats = {
            "total_samples": len(self.samples),
            "by_type": Counter(s.type for s in self.samples),
            "by_category": Counter(s.category for s in self.samples),
            "by_language": Counter(s.language for s in self.samples),
        }
        
        return stats
    
    def print_statistics(self):
        """打印統計信息"""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("📊 數據集統計")
        print("="*60)
        
        print(f"\n總樣本數: {stats['total_samples']}")
        
        print("\n按類型:")
        for type_name, count in stats['by_type'].items():
            print(f"  {type_name}: {count} ({count/stats['total_samples']*100:.1f}%)")
        
        print("\n按類別:")
        for category, count in stats['by_category'].items():
            print(f"  {category}: {count} ({count/stats['total_samples']*100:.1f}%)")
        
        print("\n按語言:")
        for lang, count in stats['by_language'].items():
            print(f"  {lang}: {count} ({count/stats['total_samples']*100:.1f}%)")
        
        print("="*60 + "\n")
    
    def validate_data(self) -> List[str]:
        """驗證數據質量"""
        issues = []
        
        for i, sample in enumerate(self.samples):
            # 檢查必填字段
            if not sample.input_text:
                issues.append(f"樣本 {i} ({sample.id}): 缺少輸入文本")
            
            # 檢查長度
            if len(sample.input_text) < 2:
                issues.append(f"樣本 {i} ({sample.id}): 輸入文本過短")
            
            if sample.output_text and len(sample.output_text) < 2:
                issues.append(f"樣本 {i} ({sample.id}): 輸出文本過短")
            
            # 檢查重複ID
            ids = [s.id for s in self.samples]
            if ids.count(sample.id) > 1:
                issues.append(f"樣本 {i} ({sample.id}): ID重複")
        
        return issues
    
    def remove_duplicates(self) -> int:
        """移除重複樣本"""
        seen = set()
        unique_samples = []
        
        for sample in self.samples:
            # 使用輸入文本的哈希作為唯一標識
            key = hashlib.md5(sample.input_text.encode()).hexdigest()
            
            if key not in seen:
                seen.add(key)
                unique_samples.append(sample)
        
        removed = len(self.samples) - len(unique_samples)
        self.samples = unique_samples
        
        if removed > 0:
            print(f"🗑️  移除了 {removed} 個重複樣本")
        
        return removed


def main():
    """示範用法"""
    print("="*60)
    print("🏗️  訓練數據管理器")
    print("="*60)
    
    # 創建生成器
    generator = DataGenerator()
    
    # 生成數據
    print("\n📝 生成訓練數據...")
    conversations = generator.generate_conversations(50)
    knowledge = generator.generate_knowledge(50)
    functional = generator.generate_functional_data(100)
    
    # 創建管理器
    manager = DatasetManager()
    
    # 添加數據
    manager.add_samples(conversations)
    manager.add_samples(knowledge)
    manager.add_samples(functional)
    
    # 統計
    manager.print_statistics()
    
    # 驗證
    print("🔍 驗證數據質量...")
    issues = manager.validate_data()
    if issues:
        print(f"⚠️  發現 {len(issues)} 個問題:")
        for issue in issues[:5]:  # 只顯示前5個
            print(f"   - {issue}")
    else:
        print("✅ 數據質量良好")
    
    # 移除重複
    manager.remove_duplicates()
    
    # 劃分數據集
    print("\n📊 劃分數據集...")
    train, val, test = manager.split_dataset()
    
    # 保存
    print("\n💾 保存數據...")
    manager.save_to_file("training/data/training_data.json")
    
    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
