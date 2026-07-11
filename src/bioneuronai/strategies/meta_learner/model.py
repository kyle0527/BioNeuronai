"""
Meta-Learner 神經網路模型定義
==============================
輸入：
  - market_features: 60 維技術指標特徵 (從真實 OHLCV 計算)
  - event_features:  8 維事件上下文特徵 (新聞情緒、VIX 代理等)
輸出：
  - 5 個基礎策略的 Softmax 資金分配權重

設計原則：
  - 輸入維度精確對應 FeatureExtractor 的輸出 (不用亂數填充)
  - 參數量控制在 10 萬以內，防止對市場雜訊過擬合
  - 使用 LayerNorm 取代 BatchNorm，對序列資料更穩定
"""

from pathlib import Path
from typing import Optional, cast

import torch
import torch.nn as nn

# 與 strategy_fusion.py 中的 self.strategies 完全對應
STRATEGY_NAMES = [
    "trend_following",
    "swing_trading",
    "mean_reversion",
    "breakout",
    "direction_change",
]

MARKET_FEATURE_DIM = 60   # FeatureExtractor 輸出的技術特徵維度
EVENT_FEATURE_DIM = 8     # 新聞情緒等事件特徵維度
INPUT_DIM = MARKET_FEATURE_DIM + EVENT_FEATURE_DIM  # = 68
NUM_STRATEGIES = len(STRATEGY_NAMES)  # = 5


class MetaLearnerModel(nn.Module):
    """
    策略融合 Meta-Learner
    結構: 68 -> 128 -> 64 -> 5 (Softmax)
    總參數量: ~18,000 個 (極輕量，防止過擬合)
    """

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(INPUT_DIM, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, NUM_STRATEGIES),
        )
        self.softmax = nn.Softmax(dim=1)
        self._init_weights()

    def _init_weights(self):
        """Xavier 初始化，確保訓練初期各策略權重均等"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(
        self,
        market_features: torch.Tensor,
        event_features: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            market_features: (B, MARKET_FEATURE_DIM) 技術指標特徵
            event_features:  (B, EVENT_FEATURE_DIM)  事件上下文特徵
        Returns:
            weights: (B, NUM_STRATEGIES) 各策略資金分配比例，總和=1
        """
        x = torch.cat([market_features, event_features], dim=1)
        logits = self.net(x)
        return cast(torch.Tensor, self.softmax(logits))

    def predict_weights(
        self,
        market_features: torch.Tensor,
        event_features: torch.Tensor,
    ) -> dict:
        """推理用：返回 {strategy_name: weight} 字典"""
        self.eval()
        with torch.no_grad():
            weights_tensor = self.forward(market_features, event_features)
            weights_np = weights_tensor[0].numpy()
        return dict(zip(STRATEGY_NAMES, weights_np.tolist()))

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path)

    def load(self, path: Path):
        self.load_state_dict(torch.load(path, map_location="cpu"))
        self.eval()

    def total_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
