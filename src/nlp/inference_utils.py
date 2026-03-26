"""
批量推理和流式生成
=================
優化推理性能和用戶體驗
"""

import torch
import torch.nn as nn
from typing import Iterator, List, Optional, Dict, Any, Callable
from dataclasses import dataclass
import time


@dataclass
class BatchInferenceConfig:
    """批量推理配置"""
    batch_size: int = 8
    max_batch_size: int = 32
    timeout: float = 0.1  # 秒
    pad_token_id: int = 0


class BatchInferenceEngine:
    """批量推理引擎
    
    動態批處理多個推理請求以提高吞吐量
    """
    
    def __init__(
        self,
        model: nn.Module,
        config: BatchInferenceConfig,
        device: str = "cpu"
    ):
        self.model = model
        self.config = config
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()
        
        # 待處理請求隊列
        self.pending_requests: List[Dict[str, Any]] = []
        self.request_id_counter = 0
    
    def add_request(
        self,
        input_ids: torch.Tensor,
        **generation_kwargs
    ) -> int:
        """添加推理請求
        
        Args:
            input_ids: 輸入 token IDs
            **generation_kwargs: 生成參數
        
        Returns:
            request_id: 請求 ID
        """
        request_id = self.request_id_counter
        self.request_id_counter += 1
        
        self.pending_requests.append({
            'request_id': request_id,
            'input_ids': input_ids,
            'generation_kwargs': generation_kwargs,
            'result': None
        })
        
        return request_id
    
    def batch_generate(self) -> Dict[int, torch.Tensor]:
        """批量生成
        
        Returns:
            {request_id: output_ids}
        """
        if not self.pending_requests:
            return {}
        
        # 準備批次
        batch_size = min(len(self.pending_requests), self.config.max_batch_size)
        batch_requests = self.pending_requests[:batch_size]
        self.pending_requests = self.pending_requests[batch_size:]
        
        # 收集輸入
        input_ids_list = [req['input_ids'] for req in batch_requests]
        
        # 填充到相同長度
        max_len = max(ids.shape[-1] for ids in input_ids_list)
        padded_inputs = []
        attention_masks = []
        
        for ids in input_ids_list:
            pad_len = max_len - ids.shape[-1]
            if pad_len > 0:
                ids = torch.cat([
                    ids,
                    torch.full((ids.shape[0], pad_len), self.config.pad_token_id, dtype=ids.dtype)
                ], dim=-1)
            padded_inputs.append(ids)
            
            # Attention mask
            mask = torch.ones_like(ids)
            if pad_len > 0:
                mask[:, -pad_len:] = 0
            attention_masks.append(mask)
        
        # 合併為批次
        batch_input_ids = torch.cat(padded_inputs, dim=0).to(self.device)
        _batch_attention_mask = torch.cat(attention_masks, dim=0).to(self.device)
        
        # 批量生成
        with torch.no_grad():
            # 假設模型有 generate 方法
            # 這裡需要根據實際模型調整
            batch_outputs = self.model.generate(  # type: ignore
                batch_input_ids,
                use_cache=True,
                **batch_requests[0]['generation_kwargs']  # 使用第一個請求的參數
            )
        
        # 分配結果
        results = {}
        for i, req in enumerate(batch_requests):
            results[req['request_id']] = batch_outputs[i:i+1]
        
        return results
    
    def process_all(self) -> Dict[int, torch.Tensor]:
        """處理所有待處理請求
        
        Returns:
            {request_id: output_ids}
        """
        all_results = {}
        
        while self.pending_requests:
            batch_results = self.batch_generate()
            all_results.update(batch_results)
        
        return all_results


class StreamingGenerator:
    """流式生成器
    
    逐 token 流式輸出，提升用戶體驗
    """
    
    def __init__(
        self,
        model: nn.Module,
        device: str = "cpu"
    ):
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()
    
    def generate_stream(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        repetition_penalty: float = 1.0,
        eos_token_id: Optional[int] = None,
        callback: Optional[Callable[[int], None]] = None
    ) -> Iterator[int]:
        """流式生成 tokens
        
        Args:
            input_ids: 輸入 token IDs
            max_new_tokens: 最大生成 token 數
            temperature: 溫度
            top_k: Top-K
            top_p: Top-P
            repetition_penalty: 重複懲罰
            eos_token_id: EOS token ID
            callback: 回調函數，每生成一個 token 調用一次
        
        Yields:
            生成的 token ID
        """
        input_ids = input_ids.to(self.device)
        past_key_values = None
        
        for step in range(max_new_tokens):
            # 準備輸入
            if past_key_values is not None:
                input_ids_step = input_ids[:, -1:]
            else:
                input_ids_step = input_ids
            
            # 前向傳播
            with torch.no_grad():
                if hasattr(self.model, 'forward') and 'use_cache' in self.model.forward.__code__.co_varnames:
                    outputs = self.model(
                        input_ids_step,
                        past_key_values=past_key_values,
                        use_cache=True
                    )
                    if isinstance(outputs, tuple):
                        logits, past_key_values = outputs
                    else:
                        logits = outputs
                else:
                    logits = self.model(input_ids_step)
                
                # 獲取最後一個 token 的 logits
                next_token_logits = logits[:, -1, :]
                
                # 應用重複懲罰
                if repetition_penalty != 1.0:
                    for token_id in set(input_ids[0].tolist()):
                        if next_token_logits[0, token_id] < 0:
                            next_token_logits[0, token_id] *= repetition_penalty
                        else:
                            next_token_logits[0, token_id] /= repetition_penalty
                
                # 應用溫度
                next_token_logits = next_token_logits / temperature
                
                # Top-K 過濾
                if top_k is not None and top_k > 0:
                    indices_to_remove = next_token_logits < torch.topk(
                        next_token_logits, min(top_k, next_token_logits.size(-1))
                    )[0][..., -1, None]
                    next_token_logits[indices_to_remove] = -float('inf')
                
                # Top-P 過濾
                if top_p is not None and top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True, dim=-1)
                    cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    
                    indices_to_remove = sorted_indices_to_remove.scatter(
                        1, sorted_indices, sorted_indices_to_remove
                    )
                    next_token_logits[indices_to_remove] = -float('inf')
                
                # 採樣
                probs = torch.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            
            # 生成的 token
            token_id = int(next_token[0, 0].item())
            
            # 添加到序列
            input_ids = torch.cat([input_ids, next_token], dim=1)
            
            # 回調
            if callback:
                callback(token_id)
            
            # Yield token
            yield token_id
            
            # 檢查是否結束
            if eos_token_id is not None and token_id == eos_token_id:
                break
    
    def generate_stream_text(
        self,
        input_ids: torch.Tensor,
        tokenizer,
        max_new_tokens: int = 100,
        **generation_kwargs
    ) -> Iterator[str]:
        """流式生成文本
        
        Args:
            input_ids: 輸入 token IDs
            tokenizer: Tokenizer
            max_new_tokens: 最大生成 token 數
            **generation_kwargs: 生成參數
        
        Yields:
            生成的文本片段
        """
        generated_ids = []
        
        for token_id in self.generate_stream(input_ids, max_new_tokens, **generation_kwargs):
            generated_ids.append(token_id)
            
            # 解碼當前生成的文本
            text = tokenizer.decode([token_id], skip_special_tokens=True)
            yield text


class ParallelGenerator:
    """並行生成器
    
    並行生成多個序列（用於 diverse beam search 或採樣多個候選）
    """
    
    def __init__(
        self,
        model: nn.Module,
        device: str = "cpu"
    ):
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()
    
    def generate_parallel(
        self,
        input_ids: torch.Tensor,
        num_sequences: int = 5,
        max_new_tokens: int = 50,
        **generation_kwargs
    ) -> List[torch.Tensor]:
        """並行生成多個序列
        
        Args:
            input_ids: 輸入 token IDs (1, seq_len)
            num_sequences: 生成序列數量
            max_new_tokens: 最大生成 token 數
            **generation_kwargs: 生成參數
        
        Returns:
            生成的序列列表
        """
        # 複製輸入到多個序列
        batch_input_ids = input_ids.repeat(num_sequences, 1).to(self.device)
        
        # 批量生成
        with torch.no_grad():
            outputs = self.model.generate(  # type: ignore
                batch_input_ids,
                max_new_tokens=max_new_tokens,
                do_sample=True,  # 使用採樣以產生多樣性
                **generation_kwargs
            )
        
        # 分離為單獨的序列
        sequences = [outputs[i:i+1] for i in range(num_sequences)]
        
        return sequences
    
    def generate_best_of_n(
        self,
        input_ids: torch.Tensor,
        num_candidates: int = 5,
        max_new_tokens: int = 50,
        scoring_fn: Optional[Callable[[torch.Tensor], float]] = None,
        **generation_kwargs
    ) -> torch.Tensor:
        """生成 N 個候選並選擇最佳
        
        Args:
            input_ids: 輸入 token IDs
            num_candidates: 候選數量
            max_new_tokens: 最大生成 token 數
            scoring_fn: 評分函數（如困惑度）
            **generation_kwargs: 生成參數
        
        Returns:
            最佳序列
        """
        # 生成多個候選
        candidates = self.generate_parallel(
            input_ids,
            num_sequences=num_candidates,
            max_new_tokens=max_new_tokens,
            **generation_kwargs
        )
        
        # 如果沒有評分函數，返回第一個
        if scoring_fn is None:
            return candidates[0]
        
        # 評分並選擇最佳
        scores = [scoring_fn(seq) for seq in candidates]
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        
        return candidates[best_idx]


def benchmark_inference(
    model: nn.Module,
    input_ids: torch.Tensor,
    num_runs: int = 10,
    max_new_tokens: int = 50,
    use_cache: bool = True
) -> Dict[str, float]:
    """推理性能基準測試
    
    Args:
        model: 模型
        input_ids: 輸入
        num_runs: 運行次數
        max_new_tokens: 生成 token 數
        use_cache: 是否使用 KV Cache
    
    Returns:
        性能指標
    """
    model.eval()
    device = next(model.parameters()).device
    input_ids = input_ids.to(device)
    
    # Warmup
    with torch.no_grad():
        _ = model.generate(input_ids, max_new_tokens=10, use_cache=use_cache)  # type: ignore
    
    # 測試
    times = []
    for _ in range(num_runs):
        start_time = time.time()
        
        with torch.no_grad():
            _ = model.generate(  # type: ignore
                input_ids,
                max_new_tokens=max_new_tokens,
                use_cache=use_cache,
                do_sample=False
            )
        
        elapsed = time.time() - start_time
        times.append(elapsed)
    
    # 計算統計
    avg_time = sum(times) / len(times)
    tokens_per_sec = max_new_tokens / avg_time
    
    return {
        'avg_time': avg_time,
        'min_time': min(times),
        'max_time': max(times),
        'tokens_per_sec': tokens_per_sec,
        'use_cache': use_cache
    }
