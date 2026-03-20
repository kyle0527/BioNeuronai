"""
NLP Training 子模組
==================
包含模型訓練相關工具

主要模組：
- advanced_trainer: 高級訓練器（梯度累積、混合精度、學習率調度）
- train_with_ai_teacher: AI 教師知識蒸餾訓練
- auto_evolve: 自動進化訓練（增量學習）
- data_manager: 訓練數據管理和生成
- view_training_history: 訓練歷史查看和分析
"""

__all__ = [
    "advanced_trainer",
    "train_with_ai_teacher",
    "auto_evolve",
    "data_manager",
    "view_training_history",
]
