"""
小型大語言模型 (Tiny LLM)
========================
基於 Transformer 的小型語言模型
- 100M 參數
- GPT-like 架構
- 支持文本生成
- 可訓練和微調
- KV Cache 加速推理
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
import math
import json
import time
from dataclasses import dataclass


@dataclass
class GenerationConfig:
    """生成配置參數"""
    max_new_tokens: int = 50
    temperature: float = 1.0
    top_k: Optional[int] = 50
    top_p: Optional[float] = 0.95
    repetition_penalty: float = 1.0
    do_sample: bool = True
    num_beams: int = 1
    early_stopping: bool = False
    use_cache: bool = True
    pad_token_id: Optional[int] = None
    eos_token_id: Optional[int] = None
    bos_token_id: Optional[int] = None


class TinyLLMConfig:
    """小型 LLM 配置"""
    
    def __init__(
        self,
        vocab_size: int = 50257,  # GPT-2 詞彙大小
        max_seq_length: int = 512,  # 最大序列長度
        embed_dim: int = 768,  # 嵌入維度
        num_heads: int = 12,  # 注意力頭數
        num_layers: int = 12,  # Transformer 層數
        ffn_dim: int = 3072,  # FFN 中間維度
        dropout: float = 0.1,
        attention_dropout: float = 0.1,
    ):
        self.vocab_size = vocab_size
        self.max_seq_length = max_seq_length
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.ffn_dim = ffn_dim
        self.dropout = dropout
        self.attention_dropout = attention_dropout
    
    def to_dict(self) -> Dict:
        return self.__dict__
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'TinyLLMConfig':
        return cls(**config_dict)


class MultiHeadAttention(nn.Module):
    """多頭自注意力機制（支持 KV Cache）"""
    
    def __init__(self, config: TinyLLMConfig):
        super().__init__()
        assert config.embed_dim % config.num_heads == 0
        
        self.embed_dim = config.embed_dim
        self.num_heads = config.num_heads
        self.head_dim = config.embed_dim // config.num_heads
        
        # QKV 投影
        self.qkv_proj = nn.Linear(config.embed_dim, 3 * config.embed_dim)
        self.out_proj = nn.Linear(config.embed_dim, config.embed_dim)
        
        self.dropout = nn.Dropout(config.attention_dropout)
        
        # 縮放因子
        self.scale = self.head_dim ** -0.5
    
    def forward(
        self, 
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        batch_size, seq_len, _ = x.shape
        
        # 計算 Q, K, V
        qkv = self.qkv_proj(x)
        qkv = qkv.reshape(batch_size, seq_len, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, H, L, D)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # 使用 KV Cache
        if past_key_value is not None:
            past_key, past_value = past_key_value
            k = torch.cat([past_key, k], dim=2)
            v = torch.cat([past_value, v], dim=2)
        
        # 儲存 KV Cache
        if use_cache:
            present_key_value = (k, v)
        else:
            present_key_value = None
        
        # 計算注意力分數
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        
        # 應用因果遮罩（防止看到未來的 token）
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask == 0, float('-inf'))
        
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # 加權求和
        attn_output = torch.matmul(attn_weights, v)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.reshape(batch_size, seq_len, self.embed_dim)
        
        # 輸出投影
        output = self.out_proj(attn_output)
        
        return output, present_key_value
        
        return output


class FeedForward(nn.Module):
    """前饋網路"""
    
    def __init__(self, config: TinyLLMConfig):
        super().__init__()
        self.fc1 = nn.Linear(config.embed_dim, config.ffn_dim)
        self.fc2 = nn.Linear(config.ffn_dim, config.embed_dim)
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = F.gelu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class TransformerBlock(nn.Module):
    """Transformer 區塊"""
    
    def __init__(self, config: TinyLLMConfig):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.embed_dim)
        self.attn = MultiHeadAttention(config)
        self.ln2 = nn.LayerNorm(config.embed_dim)
        self.ffn = FeedForward(config)
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(
        self, 
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]]:
        # 注意力 + 殘差
        attn_output, present_key_value = self.attn(
            self.ln1(x), 
            mask, 
            past_key_value=past_key_value,
            use_cache=use_cache
        )
        x = x + self.dropout(attn_output)
        
        # FFN + 殘差
        x = x + self.dropout(self.ffn(self.ln2(x)))
        
        if use_cache:
            return x, present_key_value
        return x


class TinyLLM(nn.Module):
    """小型大語言模型
    
    基於 GPT 架構的小型語言模型
    參數量: ~100M
    """
    
    def __init__(self, config: TinyLLMConfig):
        super().__init__()
        self.config = config
        
        # Token 嵌入
        self.token_embedding = nn.Embedding(config.vocab_size, config.embed_dim)
        
        # 位置編碼
        self.position_embedding = nn.Embedding(config.max_seq_length, config.embed_dim)
        
        # Transformer 層
        self.blocks = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.num_layers)
        ])
        
        # 最終 Layer Norm
        self.ln_f = nn.LayerNorm(config.embed_dim)
        
        # 輸出頭（語言模型頭）
        self.lm_head = nn.Linear(config.embed_dim, config.vocab_size, bias=False)
        
        # 權重共享：token embedding 和 lm_head 共享權重
        self.lm_head.weight = self.token_embedding.weight
        
        self.dropout = nn.Dropout(config.dropout)
        
        # 初始化權重
        self._init_weights()
    
    def _init_weights(self):
        """初始化模型權重"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    torch.nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            elif isinstance(module, nn.LayerNorm):
                torch.nn.init.zeros_(module.bias)
                torch.nn.init.ones_(module.weight)
    
    def _create_causal_mask(self, seq_len: int, device: torch.device) -> torch.Tensor:
        """創建因果遮罩（下三角矩陣）"""
        mask = torch.tril(torch.ones(seq_len, seq_len, device=device))
        mask = mask.unsqueeze(0).unsqueeze(0)  # (1, 1, L, L)
        return mask
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_values: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None,
        use_cache: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, List[Tuple[torch.Tensor, torch.Tensor]]]]:
        """
        Args:
            input_ids: (batch_size, seq_len)
            attention_mask: (batch_size, seq_len) optional
            past_key_values: List of past key-value pairs for each layer
            use_cache: Whether to return key-value pairs
        
        Returns:
            logits: (batch_size, seq_len, vocab_size)
            present_key_values: List of present key-value pairs (if use_cache=True)
        """
        batch_size, seq_len = input_ids.shape
        device = input_ids.device
        
        # Token 嵌入
        token_embeds = self.token_embedding(input_ids)
        
        # 位置嵌入
        if past_key_values is not None:
            # 使用 KV Cache 時，只處理新 token
            past_length = past_key_values[0][0].shape[2]
            positions = torch.arange(past_length, past_length + seq_len, device=device).unsqueeze(0)
        else:
            positions = torch.arange(0, seq_len, device=device).unsqueeze(0)
        
        position_embeds = self.position_embedding(positions)
        
        # 組合嵌入
        x = self.dropout(token_embeds + position_embeds)
        
        # 創建因果遮罩
        if past_key_values is not None:
            # 使用 KV Cache 時，只需要對新 token 的遮罩
            causal_mask = None  # 已經有 past_key_values，不需要完整遮罩
        else:
            causal_mask = self._create_causal_mask(seq_len, device)
        
        # 通過 Transformer 層
        present_key_values = []
        for i, block in enumerate(self.blocks):
            past_kv = past_key_values[i] if past_key_values is not None else None
            
            if use_cache:
                x, present_kv = block(x, causal_mask, past_key_value=past_kv, use_cache=True)
                present_key_values.append(present_kv)
            else:
                x = block(x, causal_mask, past_key_value=past_kv, use_cache=False)
        
        # 最終 Layer Norm
        x = self.ln_f(x)
        
        # 語言模型頭
        logits = self.lm_head(x)
        
        if use_cache:
            return logits, present_key_values
        return logits
    
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 50,
        temperature: float = 1.0,
        top_k: Optional[int] = 50,
        top_p: Optional[float] = 0.95,
        repetition_penalty: float = 1.0,
        use_cache: bool = True,
        eos_token_id: Optional[int] = None,
        pad_token_id: Optional[int] = None,
        do_sample: bool = True
    ) -> torch.Tensor:
        """生成文本（支持 KV Cache 加速）
        
        Args:
            input_ids: (batch_size, seq_len) 輸入 token IDs
            max_new_tokens: 最大生成 token 數
            temperature: 溫度參數（越高越隨機）
            top_k: Top-K 採樣
            top_p: Top-P (nucleus) 採樣
            repetition_penalty: 重複懲罰係數 (>1 降低重複)
            use_cache: 是否使用 KV Cache（大幅加速）
            eos_token_id: EOS token ID（生成結束標記）
            pad_token_id: PAD token ID
            do_sample: 是否採樣（False 則使用貪婪搜索）
        
        Returns:
            generated_ids: (batch_size, seq_len + actual_generated_tokens)
        """
        self.eval()
        batch_size = input_ids.shape[0]
        device = input_ids.device
        
        # 記錄原始長度
        original_length = input_ids.shape[1]
        
        # 初始化 past_key_values
        past_key_values = None
        
        with torch.no_grad():
            for step in range(max_new_tokens):
                # 如果使用 KV Cache，只處理最後一個 token
                if use_cache and past_key_values is not None:
                    input_ids_step = input_ids[:, -1:]
                else:
                    # 不使用 cache 時，處理完整序列（但限制最大長度）
                    if input_ids.shape[1] > self.config.max_seq_length:
                        input_ids_step = input_ids[:, -self.config.max_seq_length:]
                    else:
                        input_ids_step = input_ids
                
                # 前向傳播
                if use_cache:
                    logits, past_key_values = self(
                        input_ids_step, 
                        past_key_values=past_key_values,
                        use_cache=True
                    )
                else:
                    logits = self(input_ids_step, use_cache=False)
                
                # 取最後一個 token 的 logits
                next_token_logits = logits[:, -1, :]
                
                # 應用重複懲罰
                if repetition_penalty != 1.0:
                    for i in range(batch_size):
                        for token_id in set(input_ids[i].tolist()):
                            if next_token_logits[i, token_id] < 0:
                                next_token_logits[i, token_id] *= repetition_penalty
                            else:
                                next_token_logits[i, token_id] /= repetition_penalty
                
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
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    # 移除累積概率超過閾值的 tokens
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    
                    # 還原到原始順序
                    indices_to_remove = sorted_indices_to_remove.scatter(
                        1, sorted_indices, sorted_indices_to_remove
                    )
                    next_token_logits[indices_to_remove] = -float('inf')
                
                # 採樣或貪婪選擇
                if do_sample:
                    probs = F.softmax(next_token_logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                else:
                    next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
                
                # 添加到序列
                input_ids = torch.cat([input_ids, next_token], dim=1)
                
                # 檢查是否遇到 EOS token
                if eos_token_id is not None:
                    if (next_token == eos_token_id).all():
                        break
        
        return input_ids
    
    def count_parameters(self) -> int:
        """計算總參數數量"""
        return sum(p.numel() for p in self.parameters())
    
    def count_trainable_parameters(self) -> int:
        """計算可訓練參數數量"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def create_tiny_llm(
    vocab_size: int = 50257,
    max_seq_length: int = 512,
    embed_dim: int = 768,
    num_layers: int = 12,
    device: str = "cpu"
) -> TinyLLM:
    """創建小型 LLM
    
    Args:
        vocab_size: 詞彙表大小
        max_seq_length: 最大序列長度
        embed_dim: 嵌入維度
        num_layers: Transformer 層數
        device: 設備
    
    Returns:
        TinyLLM 模型
    """
    config = TinyLLMConfig(
        vocab_size=vocab_size,
        max_seq_length=max_seq_length,
        embed_dim=embed_dim,
        num_heads=12,
        num_layers=num_layers,
        ffn_dim=embed_dim * 4,
        dropout=0.1,
        attention_dropout=0.1,
    )
    
    model = TinyLLM(config)
    model = model.to(device)
    
    return model


def save_llm(model: TinyLLM, path: str, metadata: Optional[Dict] = None) -> None:
    """保存 TinyLLM 模型"""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    save_dict = {
        "state_dict": model.state_dict(),
        "config": model.config.to_dict(),
        "total_params": model.count_parameters(),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_type": "TinyLLM",
    }
    
    if metadata:
        save_dict["metadata"] = metadata
    
    torch.save(save_dict, path_obj)
    
    file_size = path_obj.stat().st_size / 1024 / 1024
    print(f"✅ LLM 模型已保存: {path_obj}")
    print(f"   檔案大小: {file_size:.2f} MB")


def load_llm(path: str, device: str = "cpu") -> Tuple[TinyLLM, Dict]:
    """載入 LLM 模型"""
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    
    config = TinyLLMConfig.from_dict(checkpoint["config"])
    model = TinyLLM(config)
    model.load_state_dict(checkpoint["state_dict"])
    model = model.to(device)
    
    return model, checkpoint


def print_llm_info(model: TinyLLM) -> None:
    """打印 LLM 信息"""
    total_params = model.count_parameters()
    trainable_params = model.count_trainable_parameters()
    
    print("=" * 70)
    print("🤖 小型大語言模型 (Tiny LLM)")
    print("=" * 70)
    print(f"詞彙表大小: {model.config.vocab_size:,}")
    print(f"最大序列長度: {model.config.max_seq_length}")
    print(f"嵌入維度: {model.config.embed_dim}")
    print(f"注意力頭數: {model.config.num_heads}")
    print(f"Transformer 層數: {model.config.num_layers}")
    print(f"FFN 維度: {model.config.ffn_dim}")
    print()
    print(f"總參數數量: {total_params:,} ({total_params / 1e6:.2f}M)")
    print(f"可訓練參數: {trainable_params:,}")
    print(f"模型大小 (float32): {total_params * 4 / 1024 / 1024:.2f} MB")
    print(f"模型大小 (float16): {total_params * 2 / 1024 / 1024:.2f} MB")
    print("=" * 70)


# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 創建小型大語言模型 (Tiny LLM)")
    print("=" * 70)
    
    # 選擇設備
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用設備: {device}\n")
    
    # 創建模型
    print("📦 創建模型...")
    model = create_tiny_llm(
        vocab_size=50257,  # GPT-2 詞彙表
        max_seq_length=512,
        embed_dim=768,
        num_layers=12,
        device=device
    )
    
    # 打印信息
    print_llm_info(model)
    
    # 測試推理
    print("\n🔮 測試推理...")
    batch_size = 2
    seq_len = 32
    test_input = torch.randint(0, model.config.vocab_size, (batch_size, seq_len)).to(device)
    
    start = time.time()
    with torch.no_grad():
        logits = model(test_input)
    inference_time = time.time() - start
    
    print(f"輸入形狀: {test_input.shape}")
    print(f"輸出形狀: {logits.shape}")
    print(f"推理時間: {inference_time * 1000:.2f} ms")
    
    # 測試文本生成
    print("\n✨ 測試文本生成...")
    prompt = torch.randint(0, model.config.vocab_size, (1, 10)).to(device)
    
    start = time.time()
    generated = model.generate(
        prompt,
        max_new_tokens=20,
        temperature=0.8,
        top_k=50,
        top_p=0.95
    )
    gen_time = time.time() - start
    
    print(f"輸入序列長度: {prompt.shape[1]}")
    print(f"生成序列長度: {generated.shape[1]}")
    print(f"生成時間: {gen_time:.2f} s")
    print(f"生成速度: {(generated.shape[1] - prompt.shape[1]) / gen_time:.2f} tokens/s")
    
    # 保存模型
    print("\n💾 保存模型...")
    save_llm(model, "model/tiny_llm_100m.pth", metadata={
        "name": "我的專屬小型LLM",
        "version": "1.0.0",
        "description": "基於 Transformer 的小型大語言模型",
        "architecture": "GPT-like",
        "training_status": "未訓練（隨機初始化）"
    })
    
    print("\n✅ 完成!")
    print("\n" + "=" * 70)
    print("📚 使用說明:")
    print("=" * 70)
    print("1. 這是一個隨機初始化的模型，需要訓練才能使用")
    print("2. 可以用來訓練自己的語言模型")
    print("3. 支持標準的文本生成功能（generate 方法）")
    print("4. 架構與 GPT-2 類似，可以參考相關訓練代碼")
    print("=" * 70)
