"""TinyLLM v2 — 三模態 MoE 架構

設計原則：
- 數值 patch 化：16 根 K 線各自成一個 token（保留時間結構）
- 文字 token：直接用現有 GPT-2 tokenizer 嵌入空間
- 圖像 token：輕量 CNN，按需啟用
- MoE：6 個 FFN 專家（2 數值 + 2 文字 + 2 通用），每次激活 top-2
- LoRA 從設計層整合（不是事後補丁）
- 輸出頭：65 維全監督（無廢棄潛在空間）
- 骨幹可從 v1 遷移：12 層 attention block 權重相容
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ─────────────────────────────────────────────────────────────────────────────
# 輸出頭佈局（全域常數，與 SignalInterpreterV2 共用）
# ─────────────────────────────────────────────────────────────────────────────
OUTPUT_LAYOUT: Dict[str, Tuple[int, int]] = {
    "direction":       (0,  3),   # Long / Neutral / Short — softmax
    "confidence":      (3,  6),   # Low / Med / High — softmax
    "leverage":        (6,  16),  # 1x-10x — softmax
    "position_size":   (16, 17),  # 0-1 — sigmoid
    "stop_loss_pct":   (17, 18),  # 0-10% — sigmoid
    "take_profit_pct": (18, 19),  # 0-20% — sigmoid
    "hold_period":     (19, 29),  # 10 桶：5m/15m/1h/4h/1d/2d/3d/1w/2w/exit — softmax
    "multi_tf_align":  (29, 34),  # 5 個時框的方向一致性 — tanh
    "pattern":         (34, 54),  # 20 種 K 線形態 — sigmoid（獨立）
    "uncertainty":     (54, 55),  # 0=確定 1=不確定 — sigmoid
    "regime":          (55, 65),  # 10 種市場狀態 — softmax
}
SIGNAL_DIM = 65

HOLD_PERIOD_LABELS = ["5m", "15m", "1h", "4h", "1d", "2d", "3d", "1w", "2w", "exit"]
PATTERN_LABELS = [
    "head_shoulders", "inv_head_shoulders", "double_top", "double_bottom",
    "triple_top", "triple_bottom", "bull_flag", "bear_flag",
    "ascending_triangle", "descending_triangle", "symmetrical_triangle",
    "wedge_rising", "wedge_falling", "cup_handle", "rounding_bottom",
    "gap_up", "gap_down", "engulfing_bull", "engulfing_bear", "doji",
]
REGIME_LABELS = [
    "strong_uptrend", "weak_uptrend", "ranging_tight", "ranging_wide",
    "high_volatility", "downtrend_weak", "downtrend_strong",
    "accumulation", "distribution", "squeeze",
]


# ─────────────────────────────────────────────────────────────────────────────
# 設定
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TinyLLMv2Config:
    # ── 骨幹（與 v1 相容）
    vocab_size: int = 50257
    embed_dim: int = 768
    num_heads: int = 12
    num_layers: int = 12
    ffn_dim: int = 3072
    max_seq_length: int = 512
    dropout: float = 0.1
    attention_dropout: float = 0.1

    # ── 數值模態
    num_patch_features: int = 64    # 每根 K 線的壓縮特徵數
    num_patches: int = 16           # K 線序列長度（16 根）

    # ── 文字模態
    max_text_tokens: int = 128

    # ── 圖像模態（按需啟動）
    image_enabled: bool = False
    image_patch_tokens: int = 16

    # ── MoE
    num_experts: int = 6            # 2 數值 + 2 文字 + 2 通用
    num_active_experts: int = 2     # top-2 路由
    moe_every_n_layers: int = 2     # 每隔 N 層放一個 MoE 層（其餘用標準 FFN）

    # ── LoRA（整合在模型內，不是外掛）
    lora_rank: int = 8
    lora_alpha: float = 16.0
    lora_dropout: float = 0.05

    # ── 輸出
    signal_output_dim: int = SIGNAL_DIM

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: Dict) -> "TinyLLMv2Config":
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid})


# ─────────────────────────────────────────────────────────────────────────────
# LoRA 線性層（整合在模型內，不依賴外部 lora.py）
# ─────────────────────────────────────────────────────────────────────────────
class LoRALinear(nn.Module):
    """帶 LoRA 的線性層；骨幹凍結時只有 A/B 參與梯度。"""

    def __init__(
        self,
        in_features: int,
        out_features: int,
        rank: int = 8,
        alpha: float = 16.0,
        lora_dropout: float = 0.05,
        bias: bool = True,
    ) -> None:
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=bias)
        self.lora_A = nn.Linear(in_features, rank, bias=False)
        self.lora_B = nn.Linear(rank, out_features, bias=False)
        self.lora_drop = nn.Dropout(lora_dropout)
        self.scale = alpha / rank

        nn.init.normal_(self.lora_A.weight, std=1 / rank)
        nn.init.zeros_(self.lora_B.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base = self.linear(x)
        delta = self.lora_B(self.lora_drop(self.lora_A(x))) * self.scale
        return base + delta

    def freeze_base(self) -> None:
        self.linear.weight.requires_grad_(False)
        if self.linear.bias is not None:
            self.linear.bias.requires_grad_(False)

    def unfreeze_base(self) -> None:
        self.linear.weight.requires_grad_(True)
        if self.linear.bias is not None:
            self.linear.bias.requires_grad_(True)


# ─────────────────────────────────────────────────────────────────────────────
# 數值 Patch Encoder
# ─────────────────────────────────────────────────────────────────────────────
class NumericPatchEncoder(nn.Module):
    """64 維緊湊特徵 × 16 根 K 線 → 16 個 768 維 token。"""

    def __init__(self, patch_features: int = 64, embed_dim: int = 768) -> None:
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(patch_features, embed_dim),
            nn.LayerNorm(embed_dim),
        )
        # 數值模態位置嵌入（獨立於文字的 sin/cos 位置）
        self.pos_emb = nn.Embedding(64, embed_dim)

    def forward(self, patches: torch.Tensor) -> torch.Tensor:
        # patches: (B, T, 64) where T = num_patches
        B, T, _ = patches.shape
        pos = torch.arange(T, device=patches.device)
        return self.proj(patches) + self.pos_emb(pos).unsqueeze(0)


# ─────────────────────────────────────────────────────────────────────────────
# 輕量 K 線圖像 Encoder（按需啟用）
# ─────────────────────────────────────────────────────────────────────────────
class ChartImageEncoder(nn.Module):
    """灰度 K 線圖 (128×128) → 16 個 768 維 token，~3M 參數。"""

    def __init__(self, embed_dim: int = 768, num_patch_tokens: int = 16) -> None:
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, stride=2, padding=1),    # 64×64
            nn.GELU(),
            nn.Conv2d(32, 64, 3, stride=2, padding=1),   # 32×32
            nn.GELU(),
            nn.Conv2d(64, 128, 3, stride=2, padding=1),  # 16×16
            nn.GELU(),
            nn.AdaptiveAvgPool2d((4, 4)),                  # 4×4 = 16 patches
        )
        self.proj = nn.Linear(128, embed_dim)
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        # image: (B, 1, 128, 128)
        feat = self.cnn(image)                            # (B, 128, 4, 4)
        B, C, H, W = feat.shape
        feat = feat.view(B, C, H * W).transpose(1, 2)    # (B, 16, 128)
        return self.norm(self.proj(feat))                 # (B, 16, 768)


# ─────────────────────────────────────────────────────────────────────────────
# Modality-Aware MoE（替換 Transformer 內的 FFN）
# ─────────────────────────────────────────────────────────────────────────────
class ModalityMoE(nn.Module):
    """6 個 FFN 專家 + 路由器，top-2 稀疏激活。"""

    def __init__(
        self,
        embed_dim: int,
        num_experts: int = 6,
        num_active: int = 2,
        hidden_dim: int = 3072,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.num_experts = num_experts
        self.num_active = num_active

        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(embed_dim, hidden_dim),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, embed_dim),
            )
            for _ in range(num_experts)
        ])
        # 路由器也用 LoRA，讓它能在線更新路由策略
        self.router = LoRALinear(embed_dim, num_experts, rank=4, alpha=8.0, bias=False)
        self.norm = nn.LayerNorm(embed_dim)

        # 負載均衡損失追蹤（訓練時用）
        self._last_routing_weights: Optional[torch.Tensor] = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, embed_dim)
        B, T, D = x.shape
        x_flat = x.view(B * T, D)

        router_logits = self.router(x_flat)               # (B*T, num_experts)
        router_weights = F.softmax(router_logits, dim=-1)

        # top-2 稀疏激活
        top_w, top_idx = router_weights.topk(self.num_active, dim=-1)
        top_w = top_w / (top_w.sum(dim=-1, keepdim=True) + 1e-9)  # 重新歸一化

        self._last_routing_weights = router_weights.detach()

        # 逐 expert 計算，加權累加
        out = torch.zeros_like(x_flat)
        for e_idx in range(self.num_experts):
            mask = (top_idx == e_idx).any(dim=-1)          # (B*T,)
            if not mask.any():
                continue
            w = torch.where(
                top_idx == e_idx,
                top_w,
                torch.zeros_like(top_w),
            ).sum(dim=-1, keepdim=True)                    # (B*T, 1)
            expert_out = self.experts[e_idx](x_flat)       # (B*T, D)
            out = out + expert_out * w

        return self.norm(out.view(B, T, D))

    def load_balance_loss(self) -> torch.Tensor:
        """輔助損失：防止所有 token 都只路由到同一個 expert。"""
        if self._last_routing_weights is None:
            return torch.tensor(0.0)
        usage = self._last_routing_weights.mean(dim=0)    # (num_experts,)
        target = torch.full_like(usage, 1.0 / self.num_experts)
        return F.mse_loss(usage, target)


# ─────────────────────────────────────────────────────────────────────────────
# Multi-Head Attention（帶 LoRA）
# ─────────────────────────────────────────────────────────────────────────────
class MultiHeadAttentionV2(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int, rank: int = 8, alpha: float = 16.0, dropout: float = 0.1) -> None:
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        assert embed_dim % num_heads == 0

        # Q/K/V/O 全部帶 LoRA（骨幹可凍結，LoRA 持續更新）
        self.q_proj = LoRALinear(embed_dim, embed_dim, rank=rank, alpha=alpha)
        self.k_proj = LoRALinear(embed_dim, embed_dim, rank=rank, alpha=alpha)
        self.v_proj = LoRALinear(embed_dim, embed_dim, rank=rank, alpha=alpha)
        self.o_proj = LoRALinear(embed_dim, embed_dim, rank=rank, alpha=alpha)

        self.attn_drop = nn.Dropout(dropout)
        self.scale = math.sqrt(self.head_dim)

    def forward(
        self,
        x: torch.Tensor,
        causal_mask: Optional[torch.Tensor] = None,
        cross_x: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """支援 self-attention（cross_x=None）和 cross-attention（cross_x 為其他模態 token）。"""
        B, T, D = x.shape
        kv_src = cross_x if cross_x is not None else x
        S = kv_src.shape[1]

        q = self.q_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(kv_src).view(B, S, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(kv_src).view(B, S, self.num_heads, self.head_dim).transpose(1, 2)

        attn = torch.matmul(q, k.transpose(-2, -1)) / self.scale
        if causal_mask is not None and cross_x is None:
            attn = attn + causal_mask
        attn = F.softmax(attn, dim=-1)
        attn = self.attn_drop(attn)

        out = torch.matmul(attn, v).transpose(1, 2).contiguous().view(B, T, D)
        return self.o_proj(out)

    def freeze_base(self) -> None:
        for proj in [self.q_proj, self.k_proj, self.v_proj, self.o_proj]:
            proj.freeze_base()


# ─────────────────────────────────────────────────────────────────────────────
# Transformer Block v2（self-attn + 可選 cross-attn + MoE or FFN）
# ─────────────────────────────────────────────────────────────────────────────
class TransformerBlockV2(nn.Module):
    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        ffn_dim: int,
        use_moe: bool = False,
        num_experts: int = 6,
        num_active: int = 2,
        lora_rank: int = 8,
        lora_alpha: float = 16.0,
        dropout: float = 0.1,
        attention_dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadAttentionV2(
            embed_dim, num_heads, rank=lora_rank, alpha=lora_alpha, dropout=attention_dropout
        )
        # cross-attention：數值 token 對文字 token 的注意力
        self.cross_attn = MultiHeadAttentionV2(
            embed_dim, num_heads, rank=lora_rank, alpha=lora_alpha, dropout=attention_dropout
        )
        self.ln_cross = nn.LayerNorm(embed_dim)
        self.ln2 = nn.LayerNorm(embed_dim)

        if use_moe:
            self.ffn: nn.Module = ModalityMoE(embed_dim, num_experts, num_active, ffn_dim, dropout)
        else:
            self.ffn = nn.Sequential(
                nn.Linear(embed_dim, ffn_dim),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(ffn_dim, embed_dim),
            )
        self.drop = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        causal_mask: Optional[torch.Tensor] = None,
        text_context: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        # self-attention
        x = x + self.drop(self.attn(self.ln1(x), causal_mask=causal_mask))
        # cross-attention（如果有文字 token，數值 token 主動去讀文字）
        if text_context is not None:
            x = x + self.drop(self.cross_attn(self.ln_cross(x), cross_x=text_context))
        # FFN / MoE
        x = x + self.drop(self.ffn(self.ln2(x)))
        return x


# ─────────────────────────────────────────────────────────────────────────────
# 信號解讀輸出頭
# ─────────────────────────────────────────────────────────────────────────────
class TradingSignalHead(nn.Module):
    """768 → 65 維全監督信號。"""

    def __init__(self, embed_dim: int = 768) -> None:
        super().__init__()
        self.proj = LoRALinear(embed_dim, SIGNAL_DIM, rank=4, alpha=8.0)
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 768) — 最後一個數值 token 的表示
        return self.proj(self.norm(x))                    # (B, 65)

    def decode(self, raw: torch.Tensor) -> Dict[str, torch.Tensor]:
        """把原始 65 維輸出解碼成帶語意的字典。"""
        def sl(key: str) -> Tuple[int, int]:
            return OUTPUT_LAYOUT[key]

        return {
            "direction_probs":       F.softmax(raw[..., slice(*sl("direction"))], dim=-1),
            "confidence_probs":      F.softmax(raw[..., slice(*sl("confidence"))], dim=-1),
            "leverage_probs":        F.softmax(raw[..., slice(*sl("leverage"))], dim=-1),
            "position_size":         torch.sigmoid(raw[..., sl("position_size")[0]]).detach(),
            "stop_loss_pct":         (torch.sigmoid(raw[..., sl("stop_loss_pct")[0]]) * 0.10).detach(),
            "take_profit_pct":       (torch.sigmoid(raw[..., sl("take_profit_pct")[0]]) * 0.20).detach(),
            "hold_period_probs":     F.softmax(raw[..., slice(*sl("hold_period"))], dim=-1),
            "multi_tf_align":        torch.tanh(raw[..., slice(*sl("multi_tf_align"))]).detach(),
            "pattern_probs":         torch.sigmoid(raw[..., slice(*sl("pattern"))]).detach(),
            "uncertainty":           torch.sigmoid(raw[..., sl("uncertainty")[0]]).detach(),
            "regime_probs":          F.softmax(raw[..., slice(*sl("regime"))], dim=-1),
        }


# ─────────────────────────────────────────────────────────────────────────────
# TinyLLM v2 主體
# ─────────────────────────────────────────────────────────────────────────────
class TinyLLMv2(nn.Module):
    """三模態 (數值 + 文字 + 圖像) MoE Transformer，LoRA 整合，65 維全監督輸出。

    典型推論流程：
        numeric_patches: (B, 16, 64)   ← 16 根 K 線，每根 64 特徵
        text_ids:        (B, T_text)   ← 可選，新聞/社群/提問
        chart_image:     (B, 1, 128, 128) ← 可選，K 線圖截圖
        → raw_signal:    (B, 65)
        → decoded:       Dict[str, Tensor]
    """

    def __init__(self, config: TinyLLMv2Config) -> None:
        super().__init__()
        self.config = config
        D = config.embed_dim

        # ── 模態 Encoder
        self.numeric_encoder = NumericPatchEncoder(config.num_patch_features, D)
        self.text_embedding = nn.Embedding(config.vocab_size, D)
        self.text_pos_emb = nn.Embedding(config.max_text_tokens, D)
        self.image_encoder = ChartImageEncoder(D, config.image_patch_tokens) if config.image_enabled else None

        # 模態邊界標記 token 嵌入（[NUM_SEP], [TXT_SEP], [IMG_SEP]）
        self.modality_tokens = nn.Embedding(3, D)

        # ── Transformer Blocks（每隔 moe_every_n_layers 用 MoE）
        self.blocks = nn.ModuleList([
            TransformerBlockV2(
                embed_dim=D,
                num_heads=config.num_heads,
                ffn_dim=config.ffn_dim,
                use_moe=(i % config.moe_every_n_layers == 0),
                num_experts=config.num_experts,
                num_active=config.num_active_experts,
                lora_rank=config.lora_rank,
                lora_alpha=config.lora_alpha,
                dropout=config.dropout,
                attention_dropout=config.attention_dropout,
            )
            for i in range(config.num_layers)
        ])

        self.final_norm = nn.LayerNorm(D)
        self.drop = nn.Dropout(config.dropout)

        # ── 信號頭（數值 token 決策輸出）
        self.signal_head = TradingSignalHead(D)

        # ── 文字生成頭（相容 v1 文字模式）
        self.lm_head = nn.Linear(D, config.vocab_size, bias=False)
        self.lm_head.weight = self.text_embedding.weight  # 權重綁定

        self._init_weights()

    def _init_weights(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Linear) and not isinstance(module, LoRALinear):
                nn.init.normal_(module.weight, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, std=0.02)
            elif isinstance(module, nn.LayerNorm):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def _causal_mask(self, T: int, device: torch.device) -> torch.Tensor:
        mask = torch.full((T, T), float("-inf"), device=device)
        mask = torch.triu(mask, diagonal=1)
        return mask.unsqueeze(0).unsqueeze(0)

    def forward_signal(
        self,
        numeric_patches: torch.Tensor,
        text_ids: Optional[torch.Tensor] = None,
        chart_image: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """三模態前向推論，回傳原始 65 維信號與解碼字典。

        Args:
            numeric_patches: (B, 16, 64)
            text_ids:        (B, T_text) or None
            chart_image:     (B, 1, 128, 128) or None

        Returns:
            raw_signal:  (B, 65)
            decoded:     Dict
        """
        B = numeric_patches.shape[0]
        device = numeric_patches.device

        # 1. 數值 tokens: (B, 16, D)
        num_tok = self.numeric_encoder(numeric_patches)
        # 在數值序列前加 [NUM_SEP] 標記
        sep_num = self.modality_tokens(torch.zeros(B, 1, dtype=torch.long, device=device))
        num_tok = torch.cat([sep_num, num_tok], dim=1)   # (B, 17, D)

        # 2. 文字 tokens（可選）
        text_context: Optional[torch.Tensor] = None
        if text_ids is not None:
            T_txt = min(text_ids.shape[1], self.config.max_text_tokens)
            txt = text_ids[:, :T_txt]
            pos = torch.arange(T_txt, device=device)
            text_context = self.drop(
                self.text_embedding(txt) + self.text_pos_emb(pos).unsqueeze(0)
            )                                            # (B, T_txt, D)

        # 3. 圖像 tokens（可選）
        if chart_image is not None and self.image_encoder is not None:
            img_tok = self.image_encoder(chart_image)    # (B, 16, D)
            sep_img = self.modality_tokens(
                torch.full((B, 1), 2, dtype=torch.long, device=device)
            )
            img_tok = torch.cat([sep_img, img_tok], dim=1)
            num_tok = torch.cat([num_tok, img_tok], dim=1)  # 附加在數值序列後

        # 4. 過 Transformer Blocks
        x = self.drop(num_tok)
        causal_mask = self._causal_mask(x.shape[1], device)
        for block in self.blocks:
            x = block(x, causal_mask=causal_mask, text_context=text_context)
        x = self.final_norm(x)

        # 5. 取最後一個「原始」數值 token（index 16，即 K 線序列的最後一根）作為決策表示
        decision_repr = x[:, 16, :]                     # (B, D)
        raw_signal = self.signal_head(decision_repr)     # (B, 65)
        decoded = self.signal_head.decode(raw_signal)
        return raw_signal, decoded

    def forward_text(
        self,
        input_ids: torch.Tensor,
    ) -> torch.Tensor:
        """純文字生成模式（相容 v1），回傳 logits。"""
        B, T = input_ids.shape
        device = input_ids.device
        pos = torch.arange(T, device=device)
        x = self.drop(self.text_embedding(input_ids) + self.text_pos_emb(pos).unsqueeze(0))
        causal_mask = self._causal_mask(T, device)
        for block in self.blocks:
            x = block(x, causal_mask=causal_mask)
        x = self.final_norm(x)
        return self.lm_head(x)

    def load_balance_loss(self) -> torch.Tensor:
        """收集所有 MoE 層的負載均衡損失（訓練用）。"""
        total = torch.tensor(0.0)
        for block in self.blocks:
            if isinstance(block.ffn, ModalityMoE):
                total = total + block.ffn.load_balance_loss()
        return total

    def freeze_backbone(self) -> None:
        """凍結所有參數，然後只解凍 LoRA A/B 矩陣。"""
        for p in self.parameters():
            p.requires_grad_(False)
        for module in self.modules():
            if isinstance(module, LoRALinear):
                module.lora_A.weight.requires_grad_(True)
                module.lora_B.weight.requires_grad_(True)

    def unfreeze_all(self) -> None:
        for p in self.parameters():
            p.requires_grad_(True)

    def lora_parameters(self) -> List[nn.Parameter]:
        params = []
        for module in self.modules():
            if isinstance(module, LoRALinear):
                params.extend([module.lora_A.weight, module.lora_B.weight])
        return params

    def count_parameters(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        lora = sum(p.numel() for p in self.lora_parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {"total": total, "lora_only": lora, "trainable": trainable}

    def save(self, path: str) -> None:
        import json
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"config": self.config.to_dict(), "state_dict": self.state_dict()}, path)

    @classmethod
    def load(cls, path: str, device: str = "cpu") -> "TinyLLMv2":
        checkpoint = torch.load(path, map_location=device)
        config = TinyLLMv2Config.from_dict(checkpoint["config"])
        model = cls(config)
        model.load_state_dict(checkpoint["state_dict"], strict=False)
        return model.to(device)
