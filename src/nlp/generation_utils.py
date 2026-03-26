"""
生成工具函數
===========
用於文本生成的高級採樣策略和工具函數
"""

import torch
import torch.nn.functional as F
from typing import Optional, Tuple


def apply_repetition_penalty(
    logits: torch.Tensor,
    generated_ids: torch.Tensor,
    penalty: float = 1.0
) -> torch.Tensor:
    """應用重複懲罰
    
    Args:
        logits: (batch_size, vocab_size) 原始 logits
        generated_ids: (batch_size, seq_len) 已生成的 token IDs
        penalty: 懲罰係數 (>1 降低重複，<1 增加重複)
    
    Returns:
        處理後的 logits
    """
    if penalty == 1.0:
        return logits
    
    batch_size, vocab_size = logits.shape
    
    for i in range(batch_size):
        for token_id in set(generated_ids[i].tolist()):
            # 如果 logit 為正，除以 penalty；如果為負，乘以 penalty
            if logits[i, token_id] < 0:
                logits[i, token_id] *= penalty
            else:
                logits[i, token_id] /= penalty
    
    return logits


def top_k_filtering(
    logits: torch.Tensor,
    top_k: int,
    filter_value: float = -float('inf')
) -> torch.Tensor:
    """Top-K 過濾
    
    保留 top-k 個最高概率的 tokens，其他設為 filter_value
    
    Args:
        logits: (batch_size, vocab_size)
        top_k: 保留的 token 數量
        filter_value: 過濾值
    
    Returns:
        過濾後的 logits
    """
    if top_k <= 0:
        return logits
    
    top_k = min(top_k, logits.size(-1))
    indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
    logits[indices_to_remove] = filter_value
    
    return logits


def top_p_filtering(
    logits: torch.Tensor,
    top_p: float,
    filter_value: float = -float('inf'),
    min_tokens_to_keep: int = 1
) -> torch.Tensor:
    """Top-P (Nucleus) 過濾
    
    保留累積概率達到 top_p 的最小 token 集合
    
    Args:
        logits: (batch_size, vocab_size)
        top_p: 累積概率閾值 (0-1)
        filter_value: 過濾值
        min_tokens_to_keep: 至少保留的 token 數
    
    Returns:
        過濾後的 logits
    """
    if top_p >= 1.0:
        return logits
    
    # 排序
    sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
    
    # 移除累積概率超過閾值的 tokens
    sorted_indices_to_remove = cumulative_probs > top_p
    
    # 保持至少 min_tokens_to_keep 個 tokens
    if min_tokens_to_keep > 1:
        sorted_indices_to_remove[..., :min_tokens_to_keep] = 0
    
    # 將第一個超過閾值的 token 之後的都移除
    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
    sorted_indices_to_remove[..., 0] = 0
    
    # 將標記的位置設為 filter_value
    indices_to_remove = sorted_indices_to_remove.scatter(
        1, sorted_indices, sorted_indices_to_remove
    )
    logits[indices_to_remove] = filter_value
    
    return logits


def apply_temperature(logits: torch.Tensor, temperature: float) -> torch.Tensor:
    """應用溫度縮放
    
    Args:
        logits: (batch_size, vocab_size)
        temperature: 溫度參數 (>1 更隨機，<1 更確定)
    
    Returns:
        縮放後的 logits
    """
    if temperature == 1.0:
        return logits
    
    return logits / temperature


def sample_from_logits(
    logits: torch.Tensor,
    temperature: float = 1.0,
    top_k: Optional[int] = None,
    top_p: Optional[float] = None,
    do_sample: bool = True
) -> torch.Tensor:
    """從 logits 採樣
    
    Args:
        logits: (batch_size, vocab_size) 最後一個位置的 logits
        temperature: 溫度參數
        top_k: Top-K 採樣
        top_p: Top-P (Nucleus) 採樣
        do_sample: 是否採樣（False 則使用 greedy）
    
    Returns:
        next_tokens: (batch_size, 1) 下一個 token
    """
    # 應用溫度
    logits = apply_temperature(logits, temperature)
    
    # 應用 Top-K 過濾
    if top_k is not None and top_k > 0:
        logits = top_k_filtering(logits, top_k)
    
    # 應用 Top-P 過濾
    if top_p is not None and top_p < 1.0:
        logits = top_p_filtering(logits, top_p)
    
    # 採樣或貪婪選擇
    if do_sample:
        probs = F.softmax(logits, dim=-1)
        next_tokens = torch.multinomial(probs, num_samples=1)
    else:
        next_tokens = torch.argmax(logits, dim=-1, keepdim=True)
    
    return next_tokens


def calculate_perplexity(
    model: torch.nn.Module,
    input_ids: torch.Tensor,
    target_ids: Optional[torch.Tensor] = None
) -> float:
    """計算困惑度 (Perplexity)
    
    Args:
        model: 語言模型
        input_ids: (batch_size, seq_len) 輸入序列
        target_ids: (batch_size, seq_len) 目標序列（可選）
    
    Returns:
        perplexity: 困惑度值
    """
    model.eval()
    
    with torch.no_grad():
        if target_ids is None:
            target_ids = input_ids.clone()
        
        # 前向傳播
        logits = model(input_ids)
        
        # 計算 loss
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = target_ids[..., 1:].contiguous()
        
        loss_fct = torch.nn.CrossEntropyLoss(reduction='mean')
        loss = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1)
        )
        
        perplexity = torch.exp(loss).item()
    
    return perplexity


def beam_search(
    model: torch.nn.Module,
    input_ids: torch.Tensor,
    num_beams: int = 5,
    max_length: int = 50,
    early_stopping: bool = True,
    eos_token_id: Optional[int] = None,
    pad_token_id: Optional[int] = None
) -> Tuple[torch.Tensor, float]:
    """Beam Search 解碼
    
    Args:
        model: 語言模型
        input_ids: (1, seq_len) 初始輸入
        num_beams: beam 數量
        max_length: 最大長度
        early_stopping: 是否早停
        eos_token_id: EOS token ID
        pad_token_id: PAD token ID
    
    Returns:
        best_sequence: 最佳序列
        best_score: 最佳分數
    """
    # 初始化 beams: [(sequence, score)]
    beams = [(input_ids[0], 0.0)]
    completed_beams = []
    
    for _ in range(max_length - input_ids.shape[1]):
        all_candidates = []
        
        for sequence, score in beams:
            if eos_token_id is not None and sequence[-1].item() == eos_token_id:
                completed_beams.append((sequence, score))
                continue
            
            # 擴展當前 beam
            with torch.no_grad():
                logits = model(sequence.unsqueeze(0))
                log_probs = F.log_softmax(logits[0, -1, :], dim=-1)
            
            # 取 top-k
            top_log_probs, top_indices = torch.topk(log_probs, num_beams)
            
            for log_prob, token_id in zip(top_log_probs, top_indices):
                new_sequence = torch.cat([sequence, token_id.unsqueeze(0)])
                new_score = score + log_prob.item()
                all_candidates.append((new_sequence, new_score))
        
        # 選擇 top beams
        beams = sorted(all_candidates, key=lambda x: x[1], reverse=True)[:num_beams]
        
        # 早停檢查
        if early_stopping and len(completed_beams) >= num_beams:
            break
    
    # 合併所有 beams
    all_beams = completed_beams + beams
    best_sequence, best_score = max(all_beams, key=lambda x: x[1])
    
    return best_sequence.unsqueeze(0), best_score
