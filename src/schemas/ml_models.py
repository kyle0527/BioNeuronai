"""
BioNeuronai 機器學習模型 Schema

定義 AI/ML 模型相關的 Pydantic 模型。
支援模型訓練、預測和評估的完整生命週期管理。

最後更新: 2026-02-14
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, computed_field

from .enums import (
    PredictionType,
    ModelStatus,
    TimeFrame,
    SignalType,
)


class FeatureConfig(BaseModel):
    """特徵配置模型
    
    定義 ML 模型使用的特徵。
    """
    
    # 價格特徵
    use_ohlcv: bool = Field(default=True, description="使用 OHLCV 數據")
    price_lookback: int = Field(default=60, ge=1, description="價格回看期數")
    
    # 技術指標
    technical_indicators: list[str] = Field(
        default_factory=lambda: ["RSI", "MACD", "BB", "ATR", "SMA", "EMA"],
        description="技術指標列表"
    )
    indicator_params: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="指標參數配置"
    )
    
    # 成交量特徵
    use_volume: bool = Field(default=True, description="使用成交量數據")
    volume_indicators: list[str] = Field(
        default_factory=lambda: ["OBV", "VWAP", "Volume_SMA"],
        description="成交量指標"
    )
    
    # 時間特徵
    use_time_features: bool = Field(default=True, description="使用時間特徵")
    time_features: list[str] = Field(
        default_factory=lambda: ["hour", "day_of_week", "is_weekend"],
        description="時間特徵列表"
    )
    
    # 情緒特徵
    use_sentiment: bool = Field(default=False, description="使用情緒數據")
    sentiment_sources: list[str] = Field(
        default_factory=list,
        description="情緒數據來源"
    )
    
    # 鏈上數據
    use_onchain: bool = Field(default=False, description="使用鏈上數據")
    onchain_metrics: list[str] = Field(
        default_factory=list,
        description="鏈上指標"
    )
    
    # 特徵工程
    use_lag_features: bool = Field(default=True, description="使用滯後特徵")
    lag_periods: list[int] = Field(
        default_factory=lambda: [1, 3, 5, 10, 20],
        description="滯後期數"
    )
    use_diff_features: bool = Field(default=True, description="使用差分特徵")
    use_rolling_features: bool = Field(default=True, description="使用滾動窗口特徵")
    rolling_windows: list[int] = Field(
        default_factory=lambda: [5, 10, 20, 50],
        description="滾動窗口大小"
    )
    
    # 正規化
    normalization_method: Literal["minmax", "zscore", "robust", "none"] = Field(
        default="zscore",
        description="正規化方法"
    )


class ModelConfig(BaseModel):
    """模型配置
    
    定義 ML 模型的架構和超參數。
    """
    
    # 模型識別
    model_id: UUID = Field(default_factory=uuid4, description="模型唯一 ID")
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名稱")
    model_version: str = Field(default="1.0.0", description="模型版本")
    description: Optional[str] = Field(None, max_length=500, description="模型描述")
    
    # 模型類型
    model_type: Literal[
        "lstm", "gru", "transformer", "tcn", 
        "xgboost", "lightgbm", "random_forest", 
        "ensemble", "custom"
    ] = Field(..., description="模型類型")
    prediction_type: PredictionType = Field(..., description="預測類型")
    
    # 輸入配置
    input_features: FeatureConfig = Field(
        default_factory=FeatureConfig,
        description="輸入特徵配置"
    )
    sequence_length: int = Field(default=60, ge=1, description="序列長度")
    
    # 輸出配置
    prediction_horizon: int = Field(default=1, ge=1, description="預測時間步")
    output_classes: Optional[int] = Field(None, ge=2, description="分類類別數")
    
    # 訓練配置
    epochs: int = Field(default=100, ge=1, description="訓練輪數")
    batch_size: int = Field(default=32, ge=1, description="批次大小")
    learning_rate: float = Field(default=0.001, gt=0, description="學習率")
    optimizer: str = Field(default="adam", description="優化器")
    loss_function: str = Field(default="mse", description="損失函數")
    
    # 正則化
    dropout_rate: float = Field(default=0.2, ge=0, lt=1, description="Dropout 比率")
    l2_regularization: float = Field(default=0.0001, ge=0, description="L2 正則化")
    early_stopping_patience: int = Field(default=10, ge=1, description="早停耐心值")
    
    # 驗證
    validation_split: float = Field(default=0.2, gt=0, lt=1, description="驗證集比例")
    cross_validation_folds: Optional[int] = Field(None, ge=2, description="交叉驗證折數")
    
    # 超參數
    hyperparameters: dict[str, Any] = Field(
        default_factory=dict,
        description="模型特定超參數"
    )


class ModelMetrics(BaseModel):
    """模型評估指標
    
    記錄模型的各種性能指標。
    """
    
    # 識別
    model_id: UUID = Field(..., description="模型 ID")
    evaluation_date: datetime = Field(
        default_factory=datetime.now,
        description="評估日期"
    )
    dataset_type: Literal["train", "validation", "test", "live"] = Field(
        ..., 
        description="數據集類型"
    )
    
    # 通用指標
    sample_count: int = Field(..., ge=0, description="樣本數量")
    
    # 回歸指標
    mse: Optional[float] = Field(None, ge=0, description="均方誤差")
    rmse: Optional[float] = Field(None, ge=0, description="均方根誤差")
    mae: Optional[float] = Field(None, ge=0, description="平均絕對誤差")
    mape: Optional[float] = Field(None, ge=0, description="平均絕對百分比誤差")
    r2_score: Optional[float] = Field(None, description="R² 決定係數")
    
    # 分類指標
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="準確率")
    precision: Optional[float] = Field(None, ge=0, le=1, description="精確率")
    recall: Optional[float] = Field(None, ge=0, le=1, description="召回率")
    f1_score: Optional[float] = Field(None, ge=0, le=1, description="F1 分數")
    auc_roc: Optional[float] = Field(None, ge=0, le=1, description="AUC-ROC")
    
    # 方向預測
    direction_accuracy: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="方向預測準確率"
    )
    
    # 交易相關指標
    profitable_predictions: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="盈利預測比例"
    )
    average_return_per_prediction: Optional[float] = Field(
        None,
        description="每次預測平均收益"
    )
    
    # 混淆矩陣
    confusion_matrix: Optional[list[list[int]]] = Field(
        None,
        description="混淆矩陣"
    )
    
    # 置信度校準
    calibration_error: Optional[float] = Field(
        None,
        ge=0,
        description="校準誤差"
    )


class ModelPrediction(BaseModel):
    """模型預測結果
    
    記錄單次模型預測的完整信息。
    """
    
    # 預測識別
    prediction_id: UUID = Field(default_factory=uuid4, description="預測唯一 ID")
    model_id: UUID = Field(..., description="模型 ID")
    model_version: str = Field(..., description="模型版本")
    
    # 預測信息
    symbol: str = Field(..., description="預測標的")
    timeframe: TimeFrame = Field(..., description="時間框架")
    prediction_type: PredictionType = Field(..., description="預測類型")
    
    # 時間
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="預測生成時間"
    )
    target_time: datetime = Field(..., description="預測目標時間")
    
    # 預測值
    predicted_value: float = Field(..., description="預測值")
    predicted_direction: Optional[SignalType] = Field(
        None,
        description="預測方向"
    )
    predicted_class: Optional[int] = Field(None, description="預測類別")
    class_probabilities: Optional[dict[str, float]] = Field(
        None,
        description="類別概率分布"
    )
    
    # 置信度
    confidence: float = Field(..., ge=0, le=1, description="預測置信度")
    
    # 不確定性
    prediction_std: Optional[float] = Field(
        None,
        ge=0,
        description="預測標準差"
    )
    prediction_interval_lower: Optional[float] = Field(
        None,
        description="預測區間下界"
    )
    prediction_interval_upper: Optional[float] = Field(
        None,
        description="預測區間上界"
    )
    
    # 特徵重要性 (本次預測)
    feature_importance: Optional[dict[str, float]] = Field(
        None,
        description="特徵重要性"
    )
    
    # 當前市場狀態
    current_price: float = Field(..., gt=0, description="當前價格")
    features_used: list[str] = Field(
        default_factory=list,
        description="使用的特徵"
    )
    
    # 實際結果 (事後填充)
    actual_value: Optional[float] = Field(None, description="實際值")
    actual_direction: Optional[SignalType] = Field(None, description="實際方向")
    prediction_error: Optional[float] = Field(None, description="預測誤差")
    is_correct: Optional[bool] = Field(None, description="預測是否正確")
    
    @computed_field
    @property
    def predicted_change_pct(self) -> float:
        """預測變化百分比"""
        if self.prediction_type in [PredictionType.PRICE, PredictionType.VOLATILITY]:
            return ((self.predicted_value - self.current_price) / self.current_price) * 100
        return 0.0


class ModelRegistry(BaseModel):
    """模型註冊表
    
    管理所有已訓練模型的元數據。
    """
    
    # 模型信息
    model_id: UUID = Field(default_factory=uuid4, description="模型唯一 ID")
    model_name: str = Field(..., description="模型名稱")
    model_version: str = Field(..., description="模型版本")
    status: ModelStatus = Field(..., description="模型狀態")
    
    # 配置
    training_config: ModelConfig = Field(..., description="訓練配置")
    
    # 訓練信息
    trained_at: datetime = Field(..., description="訓練時間")
    training_duration: Optional[timedelta] = Field(None, description="訓練時長")
    training_samples: int = Field(..., ge=0, description="訓練樣本數")
    
    # 性能指標
    train_metrics: Optional[ModelMetrics] = Field(None, description="訓練指標")
    validation_metrics: Optional[ModelMetrics] = Field(None, description="驗證指標")
    test_metrics: Optional[ModelMetrics] = Field(None, description="測試指標")
    live_metrics: Optional[ModelMetrics] = Field(None, description="實盤指標")
    
    # 模型位置
    model_path: str = Field(..., description="模型文件路徑")
    model_size_mb: Optional[float] = Field(None, ge=0, description="模型大小 (MB)")
    
    # 部署信息
    deployed_at: Optional[datetime] = Field(None, description="部署時間")
    last_prediction_at: Optional[datetime] = Field(None, description="最後預測時間")
    total_predictions: int = Field(default=0, ge=0, description="總預測次數")
    
    # 描述
    description: Optional[str] = Field(None, description="模型描述")
    tags: list[str] = Field(default_factory=list, description="標籤")
    
    @computed_field
    @property
    def is_deployed(self) -> bool:
        """模型是否已部署"""
        return self.status == ModelStatus.DEPLOYED


class TrainingJob(BaseModel):
    """訓練任務
    
    管理模型訓練任務的狀態。
    """
    
    # 任務識別
    job_id: UUID = Field(default_factory=uuid4, description="任務 ID")
    training_model_config: ModelConfig = Field(..., description="訓練模型配置")
    
    # 狀態
    status: Literal["pending", "running", "completed", "failed", "canceled"] = Field(
        default="pending",
        description="任務狀態"
    )
    
    # 時間
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="創建時間"
    )
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    
    # 進度
    current_epoch: int = Field(default=0, ge=0, description="當前輪數")
    total_epochs: int = Field(..., ge=1, description="總輪數")
    current_loss: Optional[float] = Field(None, description="當前損失")
    best_loss: Optional[float] = Field(None, description="最佳損失")
    
    # 資源
    gpu_id: Optional[int] = Field(None, ge=0, description="GPU ID")
    memory_usage_mb: Optional[float] = Field(None, ge=0, description="內存使用 (MB)")
    
    # 結果
    result_model_id: Optional[UUID] = Field(None, description="結果模型 ID")
    error_message: Optional[str] = Field(None, description="錯誤信息")
    
    @computed_field
    @property
    def progress_pct(self) -> float:
        """訓練進度百分比"""
        if self.total_epochs == 0:
            return 0.0
        return (self.current_epoch / self.total_epochs) * 100


# =============================================================================
# 導出
# =============================================================================

__all__ = [
    "FeatureConfig",
    "ModelConfig",
    "ModelMetrics",
    "ModelPrediction",
    "ModelRegistry",
    "TrainingJob",
]
