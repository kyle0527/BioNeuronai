"""
模型量化 (Model Quantization)
============================
支持 8-bit 和 4-bit 量化以減少模型大小和加速推理
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, Any
from pathlib import Path
import json
from dataclasses import dataclass


@dataclass
class QuantizationConfig:
    """量化配置"""
    bits: int = 8  # 8 or 4
    symmetric: bool = True  # 對稱量化
    per_channel: bool = True  # 每通道量化
    dynamic: bool = False  # 動態量化


class QuantizedLinear(nn.Module):
    """量化線性層"""
    weight_int: torch.Tensor
    weight_scale: torch.Tensor
    weight_zero_point: torch.Tensor
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        bits: int = 8,
        bias: bool = True
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.bits = bits
        
        # 量化權重 (int8 or int4)
        self.register_buffer('weight_int', torch.zeros(out_features, in_features, dtype=torch.int8))
        
        # 縮放因子 (per-channel)
        self.register_buffer('weight_scale', torch.ones(out_features, 1))
        
        # 零點 (用於非對稱量化)
        self.register_buffer('weight_zero_point', torch.zeros(out_features, 1, dtype=torch.int8))
        
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features))
        else:
            self.register_parameter('bias', None)
    
    def quantize_weight(self, weight: torch.Tensor, symmetric: bool = True):
        """量化權重
        
        Args:
            weight: 原始權重 (out_features, in_features)
            symmetric: 是否對稱量化
        """
        # 計算每個輸出通道的縮放因子
        if self.bits == 8:
            qmin, qmax = -128, 127
        elif self.bits == 4:
            qmin, qmax = -8, 7
        else:
            raise ValueError(f"不支持的位數: {self.bits}")
        
        # Per-channel 量化
        if symmetric:
            # 對稱量化: scale = max(abs(weight)) / qmax
            abs_max = weight.abs().max(dim=1, keepdim=True)[0]
            self.weight_scale = abs_max / qmax
            self.weight_zero_point.zero_()
        else:
            # 非對稱量化
            min_val = weight.min(dim=1, keepdim=True)[0]
            max_val = weight.max(dim=1, keepdim=True)[0]
            self.weight_scale = (max_val - min_val) / (qmax - qmin)
            self.weight_zero_point = qmin - (min_val / self.weight_scale).round()
        
        # 避免除零
        self.weight_scale = torch.clamp(self.weight_scale, min=1e-8)
        
        # 量化
        weight_q = torch.round(weight / self.weight_scale + self.weight_zero_point)
        self.weight_int = torch.clamp(weight_q, qmin, qmax).to(torch.int8)
    
    def dequantize_weight(self) -> torch.Tensor:
        """反量化權重"""
        return (self.weight_int.float() - self.weight_zero_point.float()) * self.weight_scale
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向傳播
        
        Args:
            x: (batch_size, ..., in_features)
        
        Returns:
            output: (batch_size, ..., out_features)
        """
        # 反量化權重
        weight_fp = self.dequantize_weight()
        
        # 標準線性層計算
        output = torch.nn.functional.linear(x, weight_fp, self.bias)
        
        return output
    
    @classmethod
    def from_float(cls, module: nn.Linear, bits: int = 8, symmetric: bool = True):
        """從浮點層創建量化層
        
        Args:
            module: 原始浮點 Linear 層
            bits: 量化位數
            symmetric: 是否對稱量化
        
        Returns:
            量化後的層
        """
        qlinear = cls(
            module.in_features,
            module.out_features,
            bits=bits,
            bias=module.bias is not None
        )
        
        # 量化權重
        qlinear.quantize_weight(module.weight.data, symmetric=symmetric)
        
        # 複製偏置
        if module.bias is not None:
            qlinear.bias.data = module.bias.data.clone()
        
        return qlinear


class QuantizedEmbedding(nn.Module):
    """量化嵌入層"""
    weight_int: torch.Tensor
    weight_scale: torch.Tensor
    weight_zero_point: torch.Tensor
    
    def __init__(
        self,
        num_embeddings: int,
        embedding_dim: int,
        bits: int = 8
    ):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.bits = bits
        
        # 量化權重
        self.register_buffer('weight_int', torch.zeros(num_embeddings, embedding_dim, dtype=torch.int8))
        self.register_buffer('weight_scale', torch.ones(num_embeddings, 1))
        self.register_buffer('weight_zero_point', torch.zeros(num_embeddings, 1, dtype=torch.int8))
    
    def quantize_weight(self, weight: torch.Tensor, symmetric: bool = True):
        """量化嵌入權重"""
        if self.bits == 8:
            qmin, qmax = -128, 127
        elif self.bits == 4:
            qmin, qmax = -8, 7
        else:
            raise ValueError(f"不支持的位數: {self.bits}")
        
        # Per-token 量化
        if symmetric:
            abs_max = weight.abs().max(dim=1, keepdim=True)[0]
            self.weight_scale = abs_max / qmax
            self.weight_zero_point.zero_()
        else:
            min_val = weight.min(dim=1, keepdim=True)[0]
            max_val = weight.max(dim=1, keepdim=True)[0]
            self.weight_scale = (max_val - min_val) / (qmax - qmin)
            self.weight_zero_point = qmin - (min_val / self.weight_scale).round()
        
        self.weight_scale = torch.clamp(self.weight_scale, min=1e-8)
        
        weight_q = torch.round(weight / self.weight_scale + self.weight_zero_point)
        self.weight_int = torch.clamp(weight_q, qmin, qmax).to(torch.int8)
    
    def dequantize_weight(self) -> torch.Tensor:
        """反量化權重"""
        return (self.weight_int.float() - self.weight_zero_point.float()) * self.weight_scale
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """前向傳播
        
        Args:
            input: (batch_size, seq_len) token indices
        
        Returns:
            embeddings: (batch_size, seq_len, embedding_dim)
        """
        weight_fp = self.dequantize_weight()
        return torch.nn.functional.embedding(input, weight_fp)
    
    @classmethod
    def from_float(cls, module: nn.Embedding, bits: int = 8, symmetric: bool = True):
        """從浮點嵌入層創建量化層"""
        qembed = cls(
            module.num_embeddings,
            module.embedding_dim,
            bits=bits
        )
        
        qembed.quantize_weight(module.weight.data, symmetric=symmetric)
        
        return qembed


def quantize_model(
    model: nn.Module,
    config: QuantizationConfig
) -> nn.Module:
    """量化整個模型
    
    Args:
        model: 原始模型
        config: 量化配置
    
    Returns:
        量化後的模型
    """
    print("開始量化模型...")
    print(f"  位數: {config.bits}-bit")
    print(f"  對稱: {config.symmetric}")
    print(f"  每通道: {config.per_channel}")
    
    # 遞歸替換所有 Linear 和 Embedding 層
    def _replace_with_quantized(module: nn.Module):
        for name, child in module.named_children():
            if isinstance(child, nn.Linear):
                # 替換為量化層
                qlinear = QuantizedLinear.from_float(
                    child,
                    bits=config.bits,
                    symmetric=config.symmetric
                )
                setattr(module, name, qlinear)
            elif isinstance(child, nn.Embedding):
                # 替換為量化嵌入層
                qembed = QuantizedEmbedding.from_float(
                    child,
                    bits=config.bits,
                    symmetric=config.symmetric
                )
                setattr(module, name, qembed)
            else:
                # 遞歸處理子模塊
                _replace_with_quantized(child)
    
    _replace_with_quantized(model)
    
    # 統計
    total_params = sum(p.numel() for p in model.parameters())
    quantized_params = sum(
        p.numel() for n, p in model.named_parameters()
        if 'weight_int' in n or 'weight_scale' in n
    )
    
    print("✓ 量化完成!")
    print(f"  總參數: {total_params:,}")
    print(f"  量化參數: {quantized_params:,}")
    
    return model


def calculate_model_size(model: nn.Module, bits: int = 32) -> Dict[str, Any]:
    """計算模型大小
    
    Args:
        model: 模型
        bits: 每個參數的位數
    
    Returns:
        {'total_params': ..., 'size_mb': ...}
    """
    total_params = 0
    quantized_params = 0.0
    
    for name, param in model.named_parameters():
        if 'weight_int' in name:
            # 量化權重（int8 or int4）
            param_bits = 8  # 默認 8-bit
            if hasattr(model, 'bits'):
                bits_val = getattr(model, 'bits', 8)
                if isinstance(bits_val, int):
                    param_bits = bits_val
            quantized_params += param.numel() * param_bits / 8
        elif 'weight_scale' in name or 'weight_zero_point' in name:
            # 縮放因子和零點（通常是 float32 或 int8）
            if 'zero_point' in name:
                quantized_params += param.numel()  # int8
            else:
                quantized_params += param.numel() * 4  # float32
        else:
            # 普通參數
            total_params += param.numel() * 4  # float32
    
    # 計算總大小（字節）
    total_bytes = total_params + quantized_params
    size_mb = total_bytes / (1024 * 1024)
    
    return {
        'total_params': int((total_params + quantized_params) / 4),
        'size_mb': size_mb,
        'quantized_params': int(quantized_params / 4)
    }


def save_quantized_model(
    model: nn.Module,
    save_path: str,
    config: Optional[QuantizationConfig] = None
):
    """保存量化模型
    
    Args:
        model: 量化模型
        save_path: 保存路徑
        config: 量化配置
    """
    save_dir = Path(save_path)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存模型權重
    torch.save(model.state_dict(), save_dir / 'quantized_model.pth')
    
    # 保存配置
    if config:
        config_dict = {
            'bits': config.bits,
            'symmetric': config.symmetric,
            'per_channel': config.per_channel,
            'dynamic': config.dynamic
        }
        with open(save_dir / 'quantization_config.json', 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    # 計算並保存模型大小信息
    size_info = calculate_model_size(model, bits=config.bits if config else 8)
    with open(save_dir / 'model_size.json', 'w') as f:
        json.dump(size_info, f, indent=2)
    
    print(f"✓ 量化模型已保存至: {save_dir}")
    print(f"  模型大小: {size_info['size_mb']:.2f} MB")


def load_quantized_model(
    model: nn.Module,
    load_path: str
) -> nn.Module:
    """加載量化模型
    
    Args:
        model: 模型架構（未量化）
        load_path: 加載路徑
    
    Returns:
        加載了量化權重的模型
    """
    load_dir = Path(load_path)
    
    # 加載配置
    with open(load_dir / 'quantization_config.json', 'r') as f:
        config_dict = json.load(f)
    
    config = QuantizationConfig(**config_dict)
    
    # 量化模型架構
    model = quantize_model(model, config)
    
    # 加載權重
    state_dict = torch.load(load_dir / 'quantized_model.pth', map_location='cpu')
    model.load_state_dict(state_dict)
    
    print(f"✓ 量化模型已從 {load_dir} 加載")
    
    return model


def compare_model_outputs(
    original_model: nn.Module,
    quantized_model: nn.Module,
    test_input: torch.Tensor
) -> Dict[str, float]:
    """比較原始模型和量化模型的輸出
    
    Args:
        original_model: 原始模型
        quantized_model: 量化模型
        test_input: 測試輸入
    
    Returns:
        {'mse': ..., 'mae': ..., 'max_diff': ...}
    """
    original_model.eval()
    quantized_model.eval()
    
    with torch.no_grad():
        original_output = original_model(test_input)
        quantized_output = quantized_model(test_input)
        
        # 計算差異
        diff = original_output - quantized_output
        mse = torch.mean(diff ** 2).item()
        mae = torch.mean(torch.abs(diff)).item()
        max_diff = torch.max(torch.abs(diff)).item()
        
        return {
            'mse': mse,
            'mae': mae,
            'max_diff': max_diff,
            'relative_error': mae / (torch.mean(torch.abs(original_output)).item() + 1e-8)
        }
