"""
誠實生成模塊 (Honest Generation)
集成不確定性量化和幻覺檢測，實現誠實、可靠的文本生成
"""

import torch
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from .uncertainty_quantification import (
    UncertaintyQuantifier, 
    UncertaintyConfig
)
from .hallucination_detection import (
    HallucinationDetector,
    HallucinationConfig,
    SelfConsistencyChecker
)


@dataclass
class HonestGenerationConfig:
    """誠實生成配置"""
    # 不確定性配置
    uncertainty_config: Optional[UncertaintyConfig] = None
    
    # 幻覺檢測配置
    hallucination_config: Optional[HallucinationConfig] = None
    
    # 信心閾值：低於此值時拒絕生成或輸出"不知道"
    confidence_threshold: float = 0.5
    
    # 幻覺閾值：超過此值時停止生成
    hallucination_threshold: float = 0.6
    
    # 不確定時的回應模板
    uncertainty_responses: Optional[List[str]] = None
    
    # 是否使用自我一致性檢查
    use_self_consistency: bool = True
    
    # 自我一致性採樣次數
    num_consistency_samples: int = 3
    
    # 最小生成長度（避免過早停止）
    min_generation_length: int = 5
    
    # 是否在不確定時停止生成
    stop_on_uncertainty: bool = True
    
    # 是否在檢測到幻覺時停止
    stop_on_hallucination: bool = True
    
    # 是否返回信心分數
    return_confidence: bool = True
    
    # 是否返回詳細診斷信息
    return_diagnostics: bool = False
    
    def __post_init__(self):
        if self.uncertainty_config is None:
            self.uncertainty_config = UncertaintyConfig()
        
        if self.hallucination_config is None:
            self.hallucination_config = HallucinationConfig()
        
        if self.uncertainty_responses is None:
            self.uncertainty_responses = [
                "我不確定這個問題的答案。",
                "對不起，我對此沒有足夠的信心給出回答。",
                "這超出了我的知識範圍，我不知道。",
                "我不太清楚，無法給出準確的回答。",
                "抱歉，我無法確定這個答案。"
            ]


class HonestGenerator:
    """
    誠實生成器
    結合不確定性量化和幻覺檢測，實現可靠的文本生成
    """
    
    def __init__(
        self, 
        model: torch.nn.Module,
        tokenizer,
        config: Optional[HonestGenerationConfig] = None
    ):
        """
        Args:
            model: 語言模型
            tokenizer: 分詞器
            config: 誠實生成配置
        """
        self.model = model
        self.tokenizer = tokenizer
        self.config = config or HonestGenerationConfig()
        
        # 初始化子模塊
        self.uncertainty_quantifier = UncertaintyQuantifier(
            self.config.uncertainty_config
        )
        self.hallucination_detector = HallucinationDetector(
            self.config.hallucination_config
        )
        self.consistency_checker = SelfConsistencyChecker(
            self.config.num_consistency_samples
        )
    
    def _should_stop_generation(
        self,
        confidence: float,
        hallucination_score: float,
        current_length: int
    ) -> Tuple[bool, str]:
        """
        判斷是否應該停止生成
        
        Returns:
            should_stop: 是否停止
            reason: 停止原因
        """
        # 檢查最小長度
        if current_length < self.config.min_generation_length:
            return False, ""
        
        # 檢查信心
        if self.config.stop_on_uncertainty:
            if confidence < self.config.confidence_threshold:
                return True, "low_confidence"
        
        # 檢查幻覺
        if self.config.stop_on_hallucination:
            if hallucination_score > self.config.hallucination_threshold:
                return True, "hallucination_detected"
        
        return False, ""
    
    def _get_uncertainty_response(self) -> str:
        """獲取不確定時的回應"""
        import random
        responses = self.config.uncertainty_responses
        if responses is None or len(responses) == 0:
            return "我不確定這個問題的答案。"
        return random.choice(responses)
    
    @torch.no_grad()
    def generate_with_honesty(
        self,
        input_ids: torch.Tensor,
        max_length: int = 100,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.9,
        **kwargs
    ) -> Dict:
        """
        誠實生成：帶有不確定性感知和幻覺檢測的生成
        
        Args:
            input_ids: 輸入 token IDs [batch_size, seq_len]
            max_length: 最大生成長度
            temperature: 溫度參數
            top_k: Top-K 採樣
            top_p: Top-P 採樣
            **kwargs: 其他生成參數
        
        Returns:
            結果字典，包含:
                - generated_ids: 生成的 token IDs
                - generated_text: 生成的文本
                - confidence_scores: 每個 token 的信心分數
                - hallucination_scores: 幻覺分數
                - stopped_early: 是否提前停止
                - stop_reason: 停止原因
                - overall_confidence: 整體信心
                - is_uncertain: 是否不確定
        """
        self.model.eval()
        
        # 初始化
        generated_ids = input_ids.clone()
        confidence_scores: List[float] = []
        hallucination_scores: List[float] = []
        stopped_early = False
        stop_reason = ""
        
        # 逐token生成
        for step in range(max_length):
            # 前向傳播
            outputs = self.model(generated_ids)
            logits = outputs.logits if hasattr(outputs, 'logits') else outputs
            next_token_logits = logits[:, -1, :]
            
            # 應用溫度
            next_token_logits = next_token_logits / temperature
            
            # 計算信心分數
            confidence = self.uncertainty_quantifier.compute_confidence_score(
                next_token_logits
            )
            confidence_scores.append(confidence.item())
            
            # 檢測不確定性
            token_is_uncertain, metrics = self.uncertainty_quantifier.is_uncertain(
                next_token_logits,
                method="ensemble"
            )
            
            # 計算當前的幻覺分數
            current_tokens = generated_ids[0].tolist()
            hall_scores = self.hallucination_detector.compute_hallucination_score(
                current_tokens,
                confidence_scores=torch.tensor(confidence_scores)
            )
            hallucination_scores.append(hall_scores['overall_hallucination_score'])
            
            # 判斷是否應該停止
            should_stop, reason = self._should_stop_generation(
                confidence.item(),
                hall_scores['overall_hallucination_score'],
                step
            )
            
            if should_stop:
                stopped_early = True
                stop_reason = reason
                break
            
            # 採樣下一個 token
            if top_k > 0:
                indices_to_remove = next_token_logits < torch.topk(next_token_logits, top_k)[0][..., -1, None]
                next_token_logits[indices_to_remove] = float('-inf')
            
            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True)
                cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = 0
                indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                next_token_logits[indices_to_remove] = float('-inf')
            
            # 採樣
            probs = F.softmax(next_token_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            
            # 添加到序列
            generated_ids = torch.cat([generated_ids, next_token], dim=1)
            
            # 檢查是否生成了結束符
            if next_token.item() == getattr(self.tokenizer, 'eos_token_id', None):
                break
        
        # 解碼文本
        generated_text = self.tokenizer.decode(
            generated_ids[0, input_ids.size(1):],
            skip_special_tokens=True
        )
        
        # 如果因為不確定而停止，添加不確定回應
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        is_uncertain = overall_confidence < self.config.confidence_threshold
        
        if stopped_early and stop_reason == "low_confidence":
            generated_text = self._get_uncertainty_response()
        
        # 構建結果
        result = {
            'generated_ids': generated_ids,
            'generated_text': generated_text,
            'stopped_early': stopped_early,
            'stop_reason': stop_reason,
            'is_uncertain': is_uncertain,
        }
        
        if self.config.return_confidence:
            result['confidence_scores'] = confidence_scores
            result['overall_confidence'] = overall_confidence
        
        if self.config.return_diagnostics:
            result['hallucination_scores'] = hallucination_scores
            result['final_hallucination_score'] = (
                hallucination_scores[-1] if hallucination_scores else 0.0
            )
        
        return result
    
    @torch.no_grad()
    def generate_with_self_consistency(
        self,
        input_ids: torch.Tensor,
        num_samples: Optional[int] = None,
        **generation_kwargs
    ) -> Dict:
        """
        使用自我一致性的生成
        生成多個答案，選擇最一致的
        
        Args:
            input_ids: 輸入 token IDs
            num_samples: 採樣次數
            **generation_kwargs: 生成參數
        
        Returns:
            結果字典，包含多個生成結果和一致性信息
        """
        num_samples = num_samples or self.config.num_consistency_samples
        
        # 生成多個樣本
        samples = []
        for _ in range(num_samples):
            result = self.generate_with_honesty(input_ids, **generation_kwargs)
            samples.append(result)
        
        # 提取文本
        texts = [s['generated_text'] for s in samples]
        
        # 檢查一致性
        consistency_score, common_elements = self.consistency_checker.check_consistency(texts)
        
        # 找到多數答案
        majority_text, count, majority_confidence = \
            self.consistency_checker.find_majority_answer(texts)
        
        # 返回結果
        return {
            'samples': samples,
            'texts': texts,
            'consistency_score': consistency_score,
            'common_elements': common_elements,
            'majority_text': majority_text,
            'majority_count': count,
            'majority_confidence': majority_confidence,
            'is_consistent': consistency_score > 0.5
        }
    
    def diagnose_generation(
        self,
        input_text: str,
        generated_text: str,
        token_ids: Optional[List[int]] = None,
        confidence_scores: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        診斷生成質量
        
        Args:
            input_text: 輸入文本
            generated_text: 生成的文本
            token_ids: token ID 序列
            confidence_scores: 信心分數序列
        
        Returns:
            診斷報告
        """
        report: Dict[str, Any] = {
            'input_text': input_text,
            'generated_text': generated_text,
        }
        
        # 幻覺檢測
        if token_ids is not None:
            confidence_tensor = (
                torch.tensor(confidence_scores) 
                if confidence_scores is not None 
                else None
            )
            
            hall_scores = self.hallucination_detector.compute_hallucination_score(
                token_ids,
                confidence_tensor,
                generated_text
            )
            report['hallucination_scores'] = hall_scores
            
            # 重複檢測
            is_rep, rep_ratio = self.hallucination_detector.detect_repetition(token_ids)
            report['is_repetitive'] = is_rep
            report['repetition_ratio'] = rep_ratio
            
            # 模式檢測
            has_pattern, patterns = self.hallucination_detector.detect_pattern_repetition(token_ids)
            report['has_pattern'] = has_pattern
            if has_pattern:
                report['patterns'] = patterns
        
        # 矛盾檢測
        has_contradiction, contradictions = \
            self.hallucination_detector.detect_contradiction(generated_text)
        report['has_contradiction'] = has_contradiction
        if has_contradiction:
            report['contradictions'] = contradictions
        
        # 綜合評估
        issues = []
        if report.get('is_repetitive', False):
            issues.append("內容重複")
        if report.get('has_pattern', False):
            issues.append("模式重複")
        if report.get('has_contradiction', False):
            issues.append("自相矛盾")
        if 'hallucination_scores' in report:
            hall_scores_dict = report['hallucination_scores']
            if isinstance(hall_scores_dict, dict) and hall_scores_dict.get('overall_hallucination_score', 0) > 0.6:
                issues.append("高幻覺風險")
        
        report['issues'] = issues
        report['quality_assessment'] = "良好" if len(issues) == 0 else "需要改進"
        
        return report


def create_honest_generator(
    model: torch.nn.Module,
    tokenizer,
    confidence_threshold: float = 0.5,
    hallucination_threshold: float = 0.6,
    **config_kwargs
) -> HonestGenerator:
    """
    便捷函數：創建誠實生成器
    
    Args:
        model: 語言模型
        tokenizer: 分詞器
        confidence_threshold: 信心閾值
        hallucination_threshold: 幻覺閾值
        **config_kwargs: 其他配置參數
    
    Returns:
        HonestGenerator 實例
    """
    config = HonestGenerationConfig(
        confidence_threshold=confidence_threshold,
        hallucination_threshold=hallucination_threshold,
        **config_kwargs
    )
    
    return HonestGenerator(model, tokenizer, config)


def demonstrate_honest_generation():
    """演示誠實生成的概念"""
    print("=== 誠實生成演示 ===\n")
    
    print("誠實生成的核心原則：")
    print("1. 知道就說知道 - 當模型有足夠信心時，正常生成")
    print("2. 不知道就說不知道 - 當模型信心不足時，誠實承認")
    print("3. 避免幻覺 - 檢測並阻止不可靠的生成")
    print("4. 自我一致性 - 多次生成應該一致")
    print("5. 可解釋性 - 提供信心分數和診斷信息\n")
    
    print("誠實生成配置示例：")
    config = HonestGenerationConfig(
        confidence_threshold=0.5,
        hallucination_threshold=0.6,
        stop_on_uncertainty=True,
        stop_on_hallucination=True,
        use_self_consistency=True,
        num_consistency_samples=3
    )
    
    print(f"  信心閾值: {config.confidence_threshold}")
    print(f"  幻覺閾值: {config.hallucination_threshold}")
    print(f"  低信心時停止: {config.stop_on_uncertainty}")
    print(f"  檢測到幻覺時停止: {config.stop_on_hallucination}")
    print(f"  使用自我一致性: {config.use_self_consistency}")
    print(f"  一致性採樣次數: {config.num_consistency_samples}\n")
    
    print("不確定時的回應示例：")
    responses = config.uncertainty_responses or []
    for i, response in enumerate(responses[:3], 1):
        print(f"  {i}. {response}")
    
    print("\n使用方法：")
    print("""
    # 創建誠實生成器
    generator = create_honest_generator(
        model=model,
        tokenizer=tokenizer,
        confidence_threshold=0.5
    )
    
    # 誠實生成
    result = generator.generate_with_honesty(
        input_ids=input_ids,
        max_length=100
    )
    
    # 檢查結果
    if result['is_uncertain']:
        print("模型表示不確定：", result['generated_text'])
    else:
        print("模型有信心：", result['generated_text'])
        print("信心分數：", result['overall_confidence'])
    """)


if __name__ == "__main__":
    demonstrate_honest_generation()
