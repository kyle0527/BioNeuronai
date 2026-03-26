"""
幻覺檢測模塊 (Hallucination Detection)
用於檢測模型生成中的幻覺、矛盾和不一致內容
"""

import torch
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional
import re
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class HallucinationConfig:
    """幻覺檢測配置"""
    # 重複檢測：檢測過度重複的內容
    repetition_window: int = 20  # 檢測窗口大小
    repetition_threshold: float = 0.5  # 重複比例閾值
    
    # 自相矛盾檢測
    check_contradiction: bool = True
    
    # 知識一致性檢測
    check_factual_consistency: bool = True
    
    # 語義連貫性檢測
    check_semantic_coherence: bool = True
    
    # 信心閾值（低於此值可能產生幻覺）
    confidence_threshold: float = 0.4


class HallucinationDetector:
    """幻覺檢測器"""
    
    def __init__(self, config: Optional[HallucinationConfig] = None):
        self.config = config or HallucinationConfig()
    
    def detect_repetition(
        self, 
        token_ids: List[int], 
        window_size: Optional[int] = None
    ) -> Tuple[bool, float]:
        """
        檢測過度重複
        
        Args:
            token_ids: 生成的 token ID 序列
            window_size: 檢測窗口大小
        
        Returns:
            is_repetitive: 是否過度重複
            repetition_ratio: 重複比例
        """
        if len(token_ids) < 2:
            return False, 0.0
        
        window_size = window_size or self.config.repetition_window
        
        # 檢測連續重複
        consecutive_repeats = 0
        for i in range(1, len(token_ids)):
            if token_ids[i] == token_ids[i-1]:
                consecutive_repeats += 1
        
        consecutive_ratio = consecutive_repeats / len(token_ids)
        
        # 檢測窗口內的重複
        if len(token_ids) > window_size:
            window_tokens = token_ids[-window_size:]
            unique_tokens = len(set(window_tokens))
            window_ratio = 1.0 - (unique_tokens / len(window_tokens))
        else:
            window_ratio = 0.0
        
        # 綜合判斷
        repetition_ratio = max(consecutive_ratio, window_ratio)
        is_repetitive = repetition_ratio > self.config.repetition_threshold
        
        return is_repetitive, repetition_ratio
    
    def detect_pattern_repetition(
        self, 
        token_ids: List[int], 
        max_pattern_length: int = 10
    ) -> Tuple[bool, List[Tuple[List[int], int]]]:
        """
        檢測重複的模式（如 "A B C A B C A B C"）
        
        Args:
            token_ids: token ID 序列
            max_pattern_length: 最大模式長度
        
        Returns:
            has_pattern: 是否存在重複模式
            patterns: 檢測到的模式列表 [(pattern, count), ...]
        """
        if len(token_ids) < 4:
            return False, []
        
        patterns = []
        
        # 檢測不同長度的模式
        for pattern_len in range(2, min(max_pattern_length + 1, len(token_ids) // 2 + 1)):
            pattern_counts: defaultdict[tuple[int, ...], int] = defaultdict(int)
            
            # 滑動窗口提取模式
            for i in range(len(token_ids) - pattern_len + 1):
                pattern = tuple(token_ids[i:i + pattern_len])
                pattern_counts[pattern] += 1
            
            # 找出重複次數 >= 3 的模式
            for pattern, count in pattern_counts.items():
                if count >= 3:
                    patterns.append((list(pattern), count))
        
        has_pattern = len(patterns) > 0
        return has_pattern, patterns
    
    def detect_semantic_drift(
        self, 
        embeddings: torch.Tensor, 
        window_size: int = 5
    ) -> Tuple[bool, float]:
        """
        檢測語義漂移（生成內容逐漸偏離主題）
        
        Args:
            embeddings: token embeddings [seq_len, hidden_dim]
            window_size: 比較窗口大小
        
        Returns:
            has_drift: 是否存在語義漂移
            drift_score: 漂移分數（0-1，越高越偏離）
        """
        if len(embeddings) < window_size * 2:
            return False, 0.0
        
        # 計算前後窗口的平均embedding
        start_window = embeddings[:window_size].mean(dim=0)
        end_window = embeddings[-window_size:].mean(dim=0)
        
        # 計算餘弦相似度
        similarity = F.cosine_similarity(
            start_window.unsqueeze(0), 
            end_window.unsqueeze(0)
        ).item()
        
        # 相似度越低，漂移越嚴重
        drift_score = 1.0 - similarity
        has_drift = drift_score > 0.5  # 閾值可調整
        
        return has_drift, drift_score
    
    def detect_contradiction(
        self, 
        text: str
    ) -> Tuple[bool, List[Tuple[str, str]]]:
        """
        檢測文本中的自相矛盾
        使用簡單的規則和關鍵詞匹配
        
        Args:
            text: 生成的文本
        
        Returns:
            has_contradiction: 是否存在矛盾
            contradictions: 矛盾對列表
        """
        # 分句
        sentences = [s.strip() for s in text.split('。') if s.strip()]
        
        if len(sentences) < 2:
            return False, []
        
        # 矛盾關鍵詞對
        contradiction_patterns = [
            (r'是', r'不是|非'),
            (r'有', r'沒有|無'),
            (r'可以', r'不可以|不能'),
            (r'會', r'不會'),
            (r'對', r'錯|不對'),
            (r'正確', r'錯誤|不正確'),
            (r'是的', r'不是|否'),
        ]
        
        contradictions = []
        
        # 檢測相鄰句子的矛盾
        for i in range(len(sentences) - 1):
            sent1 = sentences[i]
            sent2 = sentences[i + 1]
            
            # 檢查是否包含矛盾關鍵詞
            for pos_pattern, neg_pattern in contradiction_patterns:
                if (re.search(pos_pattern, sent1) and re.search(neg_pattern, sent2)) or \
                   (re.search(neg_pattern, sent1) and re.search(pos_pattern, sent2)):
                    contradictions.append((sent1, sent2))
                    break
        
        has_contradiction = len(contradictions) > 0
        return has_contradiction, contradictions
    
    def detect_factual_inconsistency(
        self, 
        text: str, 
        known_facts: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        檢測事實不一致
        與已知事實進行對比
        
        Args:
            text: 生成的文本
            known_facts: 已知事實字典 {entity: fact}
        
        Returns:
            has_inconsistency: 是否存在不一致
            inconsistent_facts: 不一致的事實列表
        """
        if known_facts is None:
            return False, []
        
        inconsistent_facts = []
        
        # 簡單的實體-事實匹配
        for entity, correct_fact in known_facts.items():
            if entity in text:
                # 檢查是否包含正確事實
                if correct_fact not in text:
                    inconsistent_facts.append(
                        f"關於'{entity}'的描述可能不準確"
                    )
        
        has_inconsistency = len(inconsistent_facts) > 0
        return has_inconsistency, inconsistent_facts
    
    def compute_hallucination_score(
        self, 
        token_ids: List[int],
        confidence_scores: Optional[torch.Tensor] = None,
        text: Optional[str] = None
    ) -> Dict[str, float]:
        """
        計算綜合幻覺分數
        
        Args:
            token_ids: token ID 序列
            confidence_scores: 每個 token 的信心分數
            text: 生成的文本（用於高級檢測）
        
        Returns:
            scores: 各項分數字典
        """
        scores = {}
        
        # 1. 重複檢測
        is_repetitive, repetition_ratio = self.detect_repetition(token_ids)
        scores['repetition_score'] = repetition_ratio
        
        # 2. 模式重複檢測
        has_pattern, patterns = self.detect_pattern_repetition(token_ids)
        scores['pattern_repetition_score'] = 1.0 if has_pattern else 0.0
        
        # 3. 信心分數（如果提供）
        if confidence_scores is not None:
            avg_confidence = confidence_scores.mean().item()
            scores['confidence_score'] = avg_confidence
            scores['low_confidence_score'] = (
                1.0 if avg_confidence < self.config.confidence_threshold else 0.0
            )
        
        # 4. 文本級檢測（如果提供）
        if text is not None:
            has_contradiction, _ = self.detect_contradiction(text)
            scores['contradiction_score'] = 1.0 if has_contradiction else 0.0
        
        # 5. 綜合幻覺分數（加權平均）
        weights = {
            'repetition_score': 0.3,
            'pattern_repetition_score': 0.2,
            'low_confidence_score': 0.3,
            'contradiction_score': 0.2
        }
        
        overall_score = 0.0
        total_weight = 0.0
        for key, weight in weights.items():
            if key in scores:
                overall_score += scores[key] * weight
                total_weight += weight
        
        if total_weight > 0:
            scores['overall_hallucination_score'] = overall_score / total_weight
        else:
            scores['overall_hallucination_score'] = 0.0
        
        return scores


class SelfConsistencyChecker:
    """
    自我一致性檢查器
    通過多次生成並比較結果來評估一致性
    """
    
    def __init__(self, num_samples: int = 5):
        """
        Args:
            num_samples: 生成樣本數量
        """
        self.num_samples = num_samples
    
    def check_consistency(
        self, 
        generated_texts: List[str]
    ) -> Tuple[float, List[str]]:
        """
        檢查多個生成結果的一致性
        
        Args:
            generated_texts: 多個生成的文本
        
        Returns:
            consistency_score: 一致性分數（0-1）
            common_elements: 共同的元素
        """
        if len(generated_texts) < 2:
            return 1.0, generated_texts
        
        # 將文本分詞（簡單的空格分詞）
        tokenized_texts = [set(text.split()) for text in generated_texts]
        
        # 計算交集
        common_tokens = set.intersection(*tokenized_texts)
        
        # 計算並集
        all_tokens = set.union(*tokenized_texts)
        
        # Jaccard 相似度
        if len(all_tokens) > 0:
            consistency_score = len(common_tokens) / len(all_tokens)
        else:
            consistency_score = 1.0
        
        common_elements = list(common_tokens)
        
        return consistency_score, common_elements
    
    def find_majority_answer(
        self, 
        generated_texts: List[str]
    ) -> Tuple[str, int, float]:
        """
        找出多數答案（用於QA任務）
        
        Args:
            generated_texts: 多個生成的文本
        
        Returns:
            majority_answer: 多數答案
            count: 出現次數
            confidence: 信心分數
        """
        # 統計每個答案的出現次數
        answer_counts: defaultdict[str, int] = defaultdict(int)
        for text in generated_texts:
            # 簡單的答案提取（可以根據具體任務調整）
            answer = text.strip()
            answer_counts[answer] += 1
        
        # 找出出現最多的答案
        if answer_counts:
            majority_answer = max(answer_counts.items(), key=lambda x: x[1])[0]
            count = answer_counts[majority_answer]
            confidence = count / len(generated_texts)
        else:
            majority_answer = ""
            count = 0
            confidence = 0.0
        
        return majority_answer, count, confidence


class GroundingValidator:
    """
    基於檢索的驗證器（Grounding Validator）
    用於驗證生成內容是否有依據
    """
    
    def __init__(self, knowledge_base: Optional[List[str]] = None):
        """
        Args:
            knowledge_base: 知識庫（文檔列表）
        """
        self.knowledge_base = knowledge_base or []
    
    def has_grounding(
        self, 
        generated_text: str, 
        source_documents: Optional[List[str]] = None
    ) -> Tuple[bool, float, List[str]]:
        """
        檢查生成內容是否有來源依據
        
        Args:
            generated_text: 生成的文本
            source_documents: 來源文檔（如果為None，使用知識庫）
        
        Returns:
            is_grounded: 是否有依據
            grounding_score: 依據分數
            supporting_docs: 支持的文檔
        """
        docs = source_documents if source_documents else self.knowledge_base
        
        if not docs:
            # 沒有知識庫，無法驗證
            return False, 0.0, []
        
        # 將生成文本分詞
        gen_tokens = set(generated_text.split())
        
        supporting_docs = []
        overlap_scores = []
        
        # 檢查每個文檔
        for doc in docs:
            doc_tokens = set(doc.split())
            
            # 計算重疊
            overlap = len(gen_tokens & doc_tokens)
            if overlap > 0:
                overlap_score = overlap / len(gen_tokens)
                if overlap_score > 0.3:  # 閾值可調整
                    supporting_docs.append(doc)
                    overlap_scores.append(overlap_score)
        
        # 計算綜合依據分數
        if overlap_scores:
            grounding_score = max(overlap_scores)
            is_grounded = grounding_score > 0.5
        else:
            grounding_score = 0.0
            is_grounded = False
        
        return is_grounded, grounding_score, supporting_docs


def demonstrate_hallucination_detection():
    """演示幻覺檢測的使用"""
    print("=== 幻覺檢測演示 ===\n")
    
    detector = HallucinationDetector()
    
    # 1. 重複檢測
    print("1. 重複檢測:")
    repetitive_tokens = [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3]
    is_rep, ratio = detector.detect_repetition(repetitive_tokens)
    print(f"   Token序列: {repetitive_tokens}")
    print(f"   是否重複: {is_rep}, 重複比例: {ratio:.2f}\n")
    
    # 2. 模式重複檢測
    print("2. 模式重複檢測:")
    pattern_tokens = [10, 20, 30, 10, 20, 30, 10, 20, 30]
    has_pattern, patterns = detector.detect_pattern_repetition(pattern_tokens)
    print(f"   Token序列: {pattern_tokens}")
    print(f"   存在重複模式: {has_pattern}")
    if patterns:
        print(f"   檢測到的模式: {patterns}\n")
    
    # 3. 矛盾檢測
    print("3. 矛盾檢測:")
    contradictory_text = "這個方法是有效的。這個方法是無效的。"
    has_contra, contras = detector.detect_contradiction(contradictory_text)
    print(f"   文本: {contradictory_text}")
    print(f"   存在矛盾: {has_contra}")
    if contras:
        print(f"   矛盾對: {contras}\n")
    
    # 4. 自我一致性檢查
    print("4. 自我一致性檢查:")
    checker = SelfConsistencyChecker()
    texts = [
        "巴黎是法國的首都",
        "法國的首都是巴黎",
        "巴黎是法國首都城市"
    ]
    consistency, common = checker.check_consistency(texts)
    print(f"   生成的文本數: {len(texts)}")
    print(f"   一致性分數: {consistency:.2f}")
    print(f"   共同元素: {common}\n")
    
    # 5. 綜合幻覺分數
    print("5. 綜合幻覺分數:")
    test_tokens = [1, 1, 1, 2, 2, 2, 3, 3, 3]
    confidence = torch.tensor([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
    scores = detector.compute_hallucination_score(
        test_tokens, 
        confidence, 
        "測試文本"
    )
    print("   各項分數:")
    for key, value in scores.items():
        print(f"   - {key}: {value:.3f}")


if __name__ == "__main__":
    demonstrate_hallucination_detection()
