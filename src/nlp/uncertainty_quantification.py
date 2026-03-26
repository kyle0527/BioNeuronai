"""
不確定性量化模塊 (Uncertainty Quantification)
用於評估模型預測的信心程度，避免過度自信的輸出
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, cast

import numpy as np
import torch
import torch.nn.functional as F


@dataclass
class UncertaintyConfig:
    """不確定性量化配置"""
    # 熵閾值：超過此值認為模型不確定
    entropy_threshold: float = 2.0
    
    # Top-K 概率質量：前K個token的概率和
    top_k_mass_threshold: float = 0.7
    
    # 最大概率閾值：最高概率低於此值認為不確定
    max_prob_threshold: float = 0.3
    
    # 方差閾值：多次採樣的方差
    variance_threshold: float = 0.5
    
    # 採樣次數（用於 Monte Carlo Dropout）
    num_samples: int = 5
    
    # 溫度縮放（用於校準）
    temperature_calibration: float = 1.0
    
    # 是否使用多種指標綜合判斷
    use_ensemble: bool = True


class UncertaintyQuantifier:
    """不確定性量化器"""
    
    def __init__(self, config: Optional[UncertaintyConfig] = None):
        self.config = config or UncertaintyConfig()
    
    def compute_entropy(self, logits: torch.Tensor) -> torch.Tensor:
        """
        計算預測熵（Entropy）
        熵越高，表示模型越不確定
        
        Args:
            logits: 模型輸出的 logits [batch_size, vocab_size]
        
        Returns:
            entropy: 每個樣本的熵 [batch_size]
        """
        probs = F.softmax(logits, dim=-1)
        log_probs = F.log_softmax(logits, dim=-1)
        entropy = -(probs * log_probs).sum(dim=-1)
        return entropy
    
    def compute_top_k_probability_mass(
        self, 
        logits: torch.Tensor, 
        k: int = 10
    ) -> torch.Tensor:
        """
        計算 Top-K 概率質量
        如果前K個token的概率和很低，說明模型不確定
        
        Args:
            logits: 模型輸出 [batch_size, vocab_size]
            k: Top-K 的 K 值
        
        Returns:
            top_k_mass: 前K個token的概率和 [batch_size]
        """
        probs = F.softmax(logits, dim=-1)
        # 確保k不超過vocab_size
        actual_k = min(k, probs.size(-1))
        top_k_probs, _ = torch.topk(probs, k=actual_k, dim=-1)
        top_k_mass = top_k_probs.sum(dim=-1)
        return top_k_mass
    
    def compute_max_probability(self, logits: torch.Tensor) -> torch.Tensor:
        """
        計算最大概率
        最大概率很低說明模型不確定
        
        Args:
            logits: 模型輸出 [batch_size, vocab_size]
        
        Returns:
            max_prob: 最大概率 [batch_size]
        """
        probs = F.softmax(logits, dim=-1)
        max_prob, _ = probs.max(dim=-1)
        return max_prob
    
    def compute_predictive_variance(
        self, 
        logits_list: List[torch.Tensor]
    ) -> torch.Tensor:
        """
        計算預測方差（用於 Monte Carlo Dropout）
        通過多次前向傳播計算方差，評估不確定性
        
        Args:
            logits_list: 多次前向傳播的 logits 列表
        
        Returns:
            variance: 預測方差 [batch_size, vocab_size]
        """
        # 將所有 logits 堆疊
        logits_stack = torch.stack(logits_list, dim=0)  # [num_samples, batch_size, vocab_size]
        
        # 轉換為概率
        probs_stack = F.softmax(logits_stack, dim=-1)
        
        # 計算方差
        variance = probs_stack.var(dim=0)  # [batch_size, vocab_size]
        
        # 返回每個樣本的平均方差
        mean_variance = variance.mean(dim=-1)  # [batch_size]
        return mean_variance
    
    def calibrate_temperature(
        self, 
        logits: torch.Tensor, 
        temperature: float
    ) -> torch.Tensor:
        """
        溫度縮放校準
        調整模型的信心程度，避免過度自信或過度謹慎
        
        Args:
            logits: 原始 logits
            temperature: 溫度參數（>1 降低信心，<1 提高信心）
        
        Returns:
            calibrated_logits: 校準後的 logits
        """
        return logits / temperature
    
    def is_uncertain(
        self, 
        logits: torch.Tensor, 
        method: str = "entropy"
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        判斷模型是否不確定
        
        Args:
            logits: 模型輸出 [batch_size, vocab_size]
            method: 使用的方法 ("entropy", "max_prob", "top_k", "ensemble")
        
        Returns:
            is_uncertain: 是否不確定 [batch_size]
            metrics: 各項指標的值
        """
        metrics = {}
        
        if method == "entropy" or method == "ensemble":
            entropy = self.compute_entropy(logits)
            metrics["entropy"] = entropy
            entropy_uncertain = entropy > self.config.entropy_threshold
            
            if method == "entropy":
                return entropy_uncertain, metrics
        
        if method == "max_prob" or method == "ensemble":
            max_prob = self.compute_max_probability(logits)
            metrics["max_prob"] = max_prob
            max_prob_uncertain = max_prob < self.config.max_prob_threshold
            
            if method == "max_prob":
                return max_prob_uncertain, metrics
        
        if method == "top_k" or method == "ensemble":
            top_k_mass = self.compute_top_k_probability_mass(logits)
            metrics["top_k_mass"] = top_k_mass
            top_k_uncertain = top_k_mass < self.config.top_k_mass_threshold
            
            if method == "top_k":
                return top_k_uncertain, metrics
        
        if method == "ensemble":
            # 綜合多個指標，使用多數投票
            entropy_uncertain = metrics.get("entropy", torch.zeros(logits.size(0))) > self.config.entropy_threshold if "entropy" in metrics else torch.zeros(logits.size(0), dtype=torch.bool)
            max_prob_uncertain = metrics.get("max_prob", torch.ones(logits.size(0))) < self.config.max_prob_threshold if "max_prob" in metrics else torch.zeros(logits.size(0), dtype=torch.bool)
            top_k_uncertain = metrics.get("top_k_mass", torch.ones(logits.size(0))) < self.config.top_k_mass_threshold if "top_k_mass" in metrics else torch.zeros(logits.size(0), dtype=torch.bool)
            
            # 計算投票數
            uncertainty_votes = entropy_uncertain.float() + max_prob_uncertain.float() + top_k_uncertain.float()
            
            # 多數投票（2個或以上指標認為不確定）
            ensemble_uncertain = uncertainty_votes >= 2
            return ensemble_uncertain, metrics
        
        raise ValueError(f"Unknown method: {method}")
    
    def compute_confidence_score(
        self, 
        logits: torch.Tensor
    ) -> torch.Tensor:
        """
        計算信心分數（0-1之間，1表示非常確定）
        
        Args:
            logits: 模型輸出 [batch_size, vocab_size]
        
        Returns:
            confidence: 信心分數 [batch_size]
        """
        # 使用多個指標的加權平均
        max_prob = self.compute_max_probability(logits)
        entropy = self.compute_entropy(logits)
        top_k_mass = self.compute_top_k_probability_mass(logits)
        
        # 歸一化熵（取反，使得低熵=高信心）
        max_entropy = np.log(logits.size(-1))  # 最大可能的熵
        normalized_entropy = 1.0 - (entropy / max_entropy)
        
        # 加權平均
        confidence = (
            0.4 * max_prob + 
            0.3 * normalized_entropy + 
            0.3 * top_k_mass
        )
        
        return cast(torch.Tensor, confidence)


class MonteCarloDropout:
    """
    Monte Carlo Dropout 不確定性估計
    通過在推理時保持 Dropout 啟用，進行多次前向傳播來估計不確定性
    """
    
    def __init__(self, model: torch.nn.Module, num_samples: int = 10):
        """
        Args:
            model: 需要評估的模型
            num_samples: 採樣次數
        """
        self.model = model
        self.num_samples = num_samples
    
    def enable_dropout(self):
        """啟用模型中的所有 Dropout 層"""
        for module in self.model.modules():
            if isinstance(module, torch.nn.Dropout):
                module.train()  # Dropout 在 train 模式下才工作
    
    def disable_dropout(self):
        """禁用模型中的所有 Dropout 層"""
        for module in self.model.modules():
            if isinstance(module, torch.nn.Dropout):
                module.eval()
    
    def predict_with_uncertainty(
        self, 
        input_ids: torch.Tensor, 
        **kwargs
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        使用 MC Dropout 預測並計算不確定性
        
        Args:
            input_ids: 輸入 token IDs
            **kwargs: 傳遞給模型的其他參數
        
        Returns:
            mean_logits: 平均 logits
            variance: 預測方差
            epistemic_uncertainty: 認識不確定性（模型不確定性）
        """
        self.enable_dropout()
        
        logits_list = []
        with torch.no_grad():
            for _ in range(self.num_samples):
                outputs = self.model(input_ids, **kwargs)
                logits = outputs.logits if hasattr(outputs, 'logits') else outputs
                logits_list.append(logits)
        
        self.disable_dropout()
        
        # 計算統計量
        logits_stack = torch.stack(logits_list, dim=0)  # [num_samples, batch, seq, vocab]
        mean_logits = logits_stack.mean(dim=0)
        variance = logits_stack.var(dim=0)
        
        # 認識不確定性（epistemic uncertainty）= 預測的變異性
        epistemic_uncertainty = variance.mean(dim=-1)  # [batch, seq]
        
        return mean_logits, variance, epistemic_uncertainty


class CalibrationEvaluator:
    """
    校準評估器
    評估模型的信心是否經過良好校準
    """
    
    def __init__(self, num_bins: int = 10):
        """
        Args:
            num_bins: 用於計算 ECE 的區間數
        """
        self.num_bins = num_bins
        self.confidences: List[float] = []
        self.accuracies: List[float] = []
    
    def add_batch(
        self, 
        predictions: torch.Tensor, 
        targets: torch.Tensor, 
        confidences: torch.Tensor
    ):
        """
        添加一批預測結果
        
        Args:
            predictions: 預測的類別
            targets: 真實的類別
            confidences: 預測的信心分數
        """
        correct = (predictions == targets).float()
        self.confidences.extend(confidences.cpu().numpy().tolist())
        self.accuracies.extend(correct.cpu().numpy().tolist())
    
    def compute_ece(self) -> float:
        """
        計算 Expected Calibration Error (ECE)
        ECE 衡量模型的信心與實際準確率的差異
        
        Returns:
            ece: Expected Calibration Error
        """
        confidences = np.array(self.confidences)
        accuracies = np.array(self.accuracies)
        
        # 創建區間
        bins = np.linspace(0, 1, self.num_bins + 1)
        
        ece = 0.0
        for i in range(self.num_bins):
            # 找到落在這個區間的樣本
            in_bin = (confidences >= bins[i]) & (confidences < bins[i + 1])
            
            if in_bin.sum() > 0:
                # 區間內的平均信心
                avg_confidence = confidences[in_bin].mean()
                # 區間內的平均準確率
                avg_accuracy = accuracies[in_bin].mean()
                # 區間內的樣本比例
                bin_weight = in_bin.sum() / len(confidences)
                
                # 累加加權誤差
                ece += bin_weight * abs(avg_confidence - avg_accuracy)
        
        return ece
    
    def compute_mce(self) -> float:
        """
        計算 Maximum Calibration Error (MCE)
        MCE 是所有區間中最大的校準誤差
        
        Returns:
            mce: Maximum Calibration Error
        """
        confidences = np.array(self.confidences)
        accuracies = np.array(self.accuracies)
        
        bins = np.linspace(0, 1, self.num_bins + 1)
        
        max_error = 0.0
        for i in range(self.num_bins):
            in_bin = (confidences >= bins[i]) & (confidences < bins[i + 1])
            
            if in_bin.sum() > 0:
                avg_confidence = confidences[in_bin].mean()
                avg_accuracy = accuracies[in_bin].mean()
                error = abs(avg_confidence - avg_accuracy)
                max_error = max(max_error, error)
        
        return max_error


def demonstrate_uncertainty_quantification():
    """演示不確定性量化的使用"""
    print("=== 不確定性量化演示 ===\n")
    
    # 創建配置
    config = UncertaintyConfig(
        entropy_threshold=2.0,
        max_prob_threshold=0.3,
        top_k_mass_threshold=0.7
    )
    
    quantifier = UncertaintyQuantifier(config)
    
    # 模擬不同情況的 logits
    print("1. 高信心預測（一個token概率很高）:")
    high_confidence_logits = torch.tensor([[10.0, 1.0, 0.5, 0.3, 0.2]])
    entropy = quantifier.compute_entropy(high_confidence_logits)
    max_prob = quantifier.compute_max_probability(high_confidence_logits)
    confidence = quantifier.compute_confidence_score(high_confidence_logits)
    print(f"   熵: {entropy.item():.4f}")
    print(f"   最大概率: {max_prob.item():.4f}")
    print(f"   信心分數: {confidence.item():.4f}")
    is_uncertain, _ = quantifier.is_uncertain(high_confidence_logits, method="ensemble")
    print(f"   是否不確定: {is_uncertain.item()}\n")
    
    print("2. 低信心預測（多個token概率相近）:")
    low_confidence_logits = torch.tensor([[1.0, 0.9, 0.8, 0.7, 0.6]])
    entropy = quantifier.compute_entropy(low_confidence_logits)
    max_prob = quantifier.compute_max_probability(low_confidence_logits)
    confidence = quantifier.compute_confidence_score(low_confidence_logits)
    print(f"   熵: {entropy.item():.4f}")
    print(f"   最大概率: {max_prob.item():.4f}")
    print(f"   信心分數: {confidence.item():.4f}")
    is_uncertain, _ = quantifier.is_uncertain(low_confidence_logits, method="ensemble")
    print(f"   是否不確定: {is_uncertain.item()}\n")
    
    print("3. 均勻分布（完全不確定）:")
    uniform_logits = torch.ones(1, 100)  # 100個token概率相同
    entropy = quantifier.compute_entropy(uniform_logits)
    max_prob = quantifier.compute_max_probability(uniform_logits)
    confidence = quantifier.compute_confidence_score(uniform_logits)
    print(f"   熵: {entropy.item():.4f}")
    print(f"   最大概率: {max_prob.item():.4f}")
    print(f"   信心分數: {confidence.item():.4f}")
    is_uncertain, _ = quantifier.is_uncertain(uniform_logits, method="ensemble")
    print(f"   是否不確定: {is_uncertain.item()}\n")


if __name__ == "__main__":
    demonstrate_uncertainty_quantification()
