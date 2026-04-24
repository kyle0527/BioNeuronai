# 方案 B：ML Meta-Learner 堆疊融合

> 建立日期：2026-04-24  
> 版本：v1.0  
> 系列文件：策略融合路線圖 [2/4]  
> 前置文件：`STRATEGY_FUSION_ROADMAP_OVERVIEW.md`

---

## 一、核心概念

### 1.1 什麼是 ML Meta-Learner

Meta-Learner（元學習器）是「學習如何學習」的一層。在多策略融合中，它的職責是：

> **「不是你告訴它該怎麼投票，而是它從歷史回測中自己學會：哪些策略信號的組合，在哪種市場條件下，最後會帶來正期望值。」**

### 1.2 與現有系統的根本差異

**現有系統（加權投票）：**
```
信號判斷規則由人寫死：
  - 趨勢市 → 趨勢策略 × 1.5
  - 避免策略 × 0.5
  - 信心門檻 0.7
```

**Meta-Learner 系統：**
```
信號判斷規則由歷史資料學習：
  - 每一筆歷史 K 線 → 當時的所有策略信號 → 實際結果（盈/虧）
  - XGBoost/LightGBM 學習：「哪些輸入特徵組合 → 最終盈利概率最高」
  - 推論時輸出概率分佈，而不是固定比重
```

### 1.3 業界參考

**ML for Trading (Stefan Jansen) 的做法：**
- 第 11 章：Random Forest 作為 Alpha 因子組合器
- 第 12 章：XGBoost/LightGBM 的 Gradient Boosting 提升
- 第 24 章：WorldQuant 101 Formulaic Alphas → 用 ML 決定哪些 Alpha 因子有效

**核心思路（第 8 章 ML4T Workflow）：**
```
Alpha 因子 1, 2, 3, ... N    ← 你的多個策略的信號
         ↓ 合併成特徵矩陣
         XGBoost (ML 模型)
         ↓ 訓練：最大化預測準確率 / Sharpe
         輸出：下一根 K 線的方向概率 → 轉換成倉位目標
```

---

## 二、在 BioNeuronAI 中的具體設計

### 2.1 特徵工程：策略信號 → 數值特徵

每一個時間步，從每個策略收集以下特徵：

```python
# 特徵向量示意（每個策略各出幾個數值）
features = {
    # TrendFollowing 策略特徵
    "tf_direction":   +1 / 0 / -1,    # 做多=+1, 觀望=0, 做空=-1
    "tf_confidence":  0.0 ~ 1.0,       # 策略信心
    "tf_strength":    0.0 ~ 1.0,       # 信號強度
    "tf_sl_pct":      0.005 ~ 0.03,    # 建議止損%
    "tf_tp_ratio":    1.5 ~ 3.0,       # 建議盈虧比

    # MeanReversion 策略特徵
    "mr_direction":   +1 / 0 / -1,
    "mr_confidence":  0.0 ~ 1.0,
    "mr_strength":    0.0 ~ 1.0,
    "mr_zscore":      -3.0 ~ 3.0,      # 均值回歸的 Z-Score（有解釋意義）

    # SwingTrading 策略特徵
    "sw_direction":   +1 / 0 / -1,
    "sw_confidence":  0.0 ~ 1.0,
    "sw_rsi":         0 ~ 100,          # 策略用到的 RSI 值

    # Breakout 策略特徵
    "bo_direction":   +1 / 0 / -1,
    "bo_confidence":  0.0 ~ 1.0,
    "bo_vol_ratio":   0.5 ~ 3.0,       # 突破時的成交量放大倍數

    # 市場體制特徵（MarketEvaluator 輸出）
    "market_adx":          0 ~ 100,    # ADX 趨勢強度
    "market_atr_ratio":    0.5 ~ 2.0,  # ATR 相對比值（波動性）
    "market_volume_ratio": 0.5 ~ 3.0,  # 量能比
    "market_regime":       0 ~ 4,      # 趨勢/震盪/高波動 的 label encode

    # 新聞情緒
    "news_event_score":    -1.0 ~ 1.0,

    # 信號共識度（派生特徵）
    "agreement_score":     0.0 ~ 1.0,  # 所有策略方向一致時 = 1.0
    "bullish_count":       0 ~ 4,
    "bearish_count":       0 ~ 4,
    "neutral_count":       0 ~ 4,
}
# 總計約 25~35 個特徵
```

### 2.2 標籤工程：如何定義「正確答案」

訓練監督式 ML 需要標籤（什麼叫做「正確決策」）：

**方法 1：固定持有期標籤（最簡單）**
```python
# 在時間 t 做多，持有 N 根 K 線後的報酬
# N 根後收益 > threshold → 標籤 = LONG
# N 根後收益 < -threshold → 標籤 = SHORT
# 中間 → 標籤 = FLAT
label = np.sign(future_return_Nbars) if abs(future_return_Nbars) > threshold else 0
```

**方法 2：最佳回測策略標籤（更合理）**
```python
# 利用 backtest/service.py 的回測結果：
# 對每一個時間點，找出「當時哪個策略的 TradeSetup 如果執行，會帶來最好結果」
# 作為訓練目標
best_strategy = argmax(strategy_forward_returns)  # 哪個策略的信號最準
```

**方法 3：多目標標籤（最完整）**
```python
# 同時預測：
# 1. 方向（多/空/觀望）→ 分類任務
# 2. 預期報酬率      → 迴歸任務
# 3. 建議倉位大小     → 迴歸任務（與預期 Sharpe 掛鉤）
```

### 2.3 模型選擇

**首選：LightGBM**
- 速度快，適合 OHLCV 時序特徵
- 原生支援缺失值
- SHAP 值可解釋
- 記憶體效率高

**備選：XGBoost**
- 精度略高，速度略慢
- 成熟工具，文件豐富

**備選：簡單線性模型（Logistic Regression）**
- 基線用途
- 可解釋性最高
- 若線性已夠用，不需要複雜模型

**不建議在此層用深度神經網路：**
- 特徵數量少（25-35個），不值得上 DNN
- 過擬合風險更高
- 缺乏可解釋性

### 2.4 時序交叉驗證（防止未來資訊洩漏）

**重要：** 金融時序資料不能用普通 K-Fold，必須用 TimeSeriesSplit。

```
訓練集 ─────────────────────────┐
                                ▼
2024-01 ────── 2024-09 | 2024-10 (驗證)
2024-01 ────── 2024-10 | 2024-11 (驗證)
2024-01 ────── 2024-11 | 2024-12 (驗證)
...
```

這等同於已實作的 **Walk-Forward IS/OOS** 框架，可以直接復用 `backtest/service.py` 的 `_compute_walk_forward_split()`。

---

## 三、實作規劃

### 3.1 新增檔案：`src/bioneuronai/strategies/ml_meta_learner.py`

```python
"""
ML Meta-Learner 策略融合
========================
用 LightGBM 學習「哪些策略信號組合在哪種市場下有效」

架構：
  多策略信號 + 市場特徵 → LightGBM → 最終方向概率 → 倉位目標
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetaLearnerInput:
    """Meta-Learner 的輸入特徵向量"""
    # 來自各策略的特徵
    strategy_features: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # 市場體制特徵
    market_features: Dict[str, float] = field(default_factory=dict)
    # 新聞情緒
    event_score: float = 0.0
    # 計算後的派生特徵
    agreement_score: float = 0.5


@dataclass
class MetaLearnerOutput:
    """Meta-Learner 的輸出"""
    long_prob: float = 0.0    # 做多概率
    short_prob: float = 0.0   # 做空概率
    flat_prob: float = 0.0    # 觀望概率
    recommended_direction: str = "flat"  # long / short / flat
    confidence: float = 0.0
    model_version: str = "v0"
    feature_importances: Optional[Dict[str, float]] = None  # SHAP 或 feature importance


class MLMetaLearner:
    """
    ML Meta-Learner：學習策略信號的最優組合方式

    使用方式：
      # 訓練
      learner = MLMetaLearner()
      learner.train(X_train, y_train)
      learner.save("rl_models/meta_learner_v1.pkl")

      # 推論
      learner = MLMetaLearner.load("rl_models/meta_learner_v1.pkl")
      output = learner.predict(meta_input)
    """

    MODEL_PATH_DEFAULT = "rl_models/meta_learner.pkl"

    def __init__(
        self,
        model_type: str = "lightgbm",  # lightgbm / xgboost / logistic
        n_estimators: int = 200,
        max_depth: int = 5,
        learning_rate: float = 0.05,
        use_shap: bool = True,
    ):
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.use_shap = use_shap
        self._model = None
        self._feature_names: List[str] = []
        self._is_trained = False

    def build_feature_vector(self, meta_input: MetaLearnerInput) -> np.ndarray:
        """將 MetaLearnerInput 轉換為 numpy 特徵向量"""
        features = []
        feature_names = []

        # 各策略特徵
        for strategy_name, strat_feats in meta_input.strategy_features.items():
            for feat_name, feat_val in strat_feats.items():
                features.append(float(feat_val))
                feature_names.append(f"{strategy_name}_{feat_name}")

        # 市場特徵
        for feat_name, feat_val in meta_input.market_features.items():
            features.append(float(feat_val))
            feature_names.append(f"market_{feat_name}")

        # 新聞情緒
        features.append(float(meta_input.event_score))
        feature_names.append("event_score")

        # 派生特徵
        features.append(float(meta_input.agreement_score))
        feature_names.append("agreement_score")

        if not self._feature_names:
            self._feature_names = feature_names

        return np.array(features, dtype=np.float32)

    def train(
        self,
        X: np.ndarray,     # shape: (n_samples, n_features)
        y: np.ndarray,     # shape: (n_samples,), values: {-1, 0, 1}
        eval_set=None,
    ) -> Dict[str, Any]:
        """
        訓練 Meta-Learner

        Args:
            X: 特徵矩陣
            y: 標籤（-1=空, 0=觀望, 1=多）
            eval_set: 驗證集 (X_val, y_val)

        Returns:
            訓練結果摘要（準確率、F1、特徵重要性）
        """
        try:
            if self.model_type == "lightgbm":
                import lightgbm as lgb
                self._model = lgb.LGBMClassifier(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    learning_rate=self.learning_rate,
                    num_leaves=31,
                    random_state=42,
                    class_weight="balanced",
                )
            elif self.model_type == "xgboost":
                import xgboost as xgb
                self._model = xgb.XGBClassifier(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    learning_rate=self.learning_rate,
                    random_state=42,
                )
            else:
                from sklearn.linear_model import LogisticRegression
                self._model = LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                )

            self._model.fit(X, y)
            self._is_trained = True

            # 計算訓練集準確率（僅供參考，真正重要的是 OOS 表現）
            train_acc = float(np.mean(self._model.predict(X) == y))
            logger.info(f"Meta-Learner 訓練完成 | 模型:{self.model_type} | 訓練準確率:{train_acc:.3f}")
            return {"train_accuracy": train_acc, "n_samples": len(X), "n_features": X.shape[1]}

        except ImportError as e:
            logger.error(f"缺少依賴: {e}. 請執行 pip install lightgbm 或 pip install xgboost")
            raise

    def predict(self, meta_input: MetaLearnerInput) -> MetaLearnerOutput:
        """
        推論：給定當前策略信號，輸出最終方向決策
        """
        if not self._is_trained or self._model is None:
            logger.warning("Meta-Learner 尚未訓練，回傳預設輸出")
            return MetaLearnerOutput()

        x = self.build_feature_vector(meta_input).reshape(1, -1)
        proba = self._model.predict_proba(x)[0]

        # 模型 class 順序: [-1, 0, 1] 對應 [short, flat, long]
        classes = list(self._model.classes_)
        short_prob = float(proba[classes.index(-1)] if -1 in classes else 0.0)
        flat_prob  = float(proba[classes.index(0)]  if  0 in classes else 0.0)
        long_prob  = float(proba[classes.index(1)]  if  1 in classes else 0.0)

        max_prob = max(long_prob, short_prob, flat_prob)
        if max_prob == long_prob:
            direction = "long"
        elif max_prob == short_prob:
            direction = "short"
        else:
            direction = "flat"

        return MetaLearnerOutput(
            long_prob=long_prob,
            short_prob=short_prob,
            flat_prob=flat_prob,
            recommended_direction=direction,
            confidence=max_prob,
        )

    def save(self, path: str) -> None:
        import pickle
        with open(path, "wb") as f:
            pickle.dump({"model": self._model, "feature_names": self._feature_names}, f)
        logger.info(f"Meta-Learner 已儲存至 {path}")

    @classmethod
    def load(cls, path: str) -> "MLMetaLearner":
        import pickle
        instance = cls()
        with open(path, "rb") as f:
            data = pickle.load(f)
        instance._model = data["model"]
        instance._feature_names = data["feature_names"]
        instance._is_trained = True
        logger.info(f"Meta-Learner 已從 {path} 載入")
        return instance
```

### 3.2 修改 `strategy_fusion.py`：新增 ENSEMBLE_ML 模式

在 `FusionMethod` 中新增：
```python
class FusionMethod(Enum):
    ...
    ENSEMBLE_ML = "ensemble_ml"  # 新增：ML Meta-Learner 融合
```

在 `AIStrategyFusion` 中新增對應的 `_fuse_by_ensemble_ml()` 方法：
```python
def _fuse_by_ensemble_ml(
    self,
    strategy_signals: Dict[str, Optional[TradeSetup]],
    market_features: Dict[str, float],
    event_score: float = 0.0,
) -> FusionSignal:
    """使用 ML Meta-Learner 進行融合"""
    if self._meta_learner is None:
        logger.warning("Meta-Learner 未載入，回退至 MARKET_ADAPTIVE 模式")
        return self._fuse_by_market_adaptive(strategy_signals, ...)

    # 構建 MetaLearnerInput
    meta_input = self._build_meta_learner_input(strategy_signals, market_features, event_score)
    output = self._meta_learner.predict(meta_input)

    # 從信心最高的策略中選出對應方向的 TradeSetup
    selected_setup = self._select_setup_by_direction(strategy_signals, output.recommended_direction)

    return FusionSignal(
        consensus_direction=output.recommended_direction,
        confidence_score=output.confidence,
        should_trade=output.confidence > 0.55 and output.recommended_direction != "flat",
        selected_setup=selected_setup,
        fusion_method_used=FusionMethod.ENSEMBLE_ML,
    )
```

### 3.3 訓練資料生成腳本：`tools/train_meta_learner.py`

**工作流程：**
```
1. 讀取 840+ 每日 zip（2024-01-01 ~ 2026-04-21）
2. 對每一根 K 線，執行所有策略的 generate_signal()
3. 計算各策略信號的特徵向量
4. 計算前瞻標籤（未來 4/12/24 根 K 線的最佳方向）
5. 用 TimeSeriesSplit 進行交叉驗證
6. 訓練 LightGBM，選最佳模型
7. 儲存至 rl_models/meta_learner.pkl
```

---

## 四、整合到現有回測反饋循環

已有的 `build_selector_performance_weights()` 可以作為 Meta-Learner 訓練的前置步驟：

```
① 每次完整回測結束
        ↓
② build_selector_performance_weights(results) → 取得各策略表現
        ↓
③ 同時儲存每根 K 線的策略信號特徵（訓練資料）
        ↓
④ 當資料量足夠時，訓練 MLMetaLearner
        ↓
⑤ AIStrategyFusion 切換至 ENSEMBLE_ML 模式
        ↓
⑥ selector.load_performance_weights() 依舊更新 blend 比重
   (兩個機制並行，Meta-Learner 做方向決策，Blend 做倉位分配)
```

---

## 五、效果驗證計劃

### 5.1 A/B 測試設計

```
用相同時間段：2024-10-01 ~ 2024-12-31

組 A（現有系統）：
  - MARKET_ADAPTIVE 模式
  - 測量：Sharpe、勝率、最大回撤

組 B（Meta-Learner）：
  - ENSEMBLE_ML 模式（用 2024-01~09 訓練的模型）
  - 同樣的費率和滑點
  - 測量：Sharpe、勝率、最大回撤

結論標準：
  - B 的 Sharpe > A 的 Sharpe × 1.1 → Meta-Learner 有效
  - B 的最大回撤 < A 的最大回撤 × 1.2 → 風險可接受
```

### 5.2 特徵重要性分析（可解釋性）

```python
# 使用 SHAP 分析 Meta-Learner 學到了什麼
import shap
explainer = shap.TreeExplainer(learner._model)
shap_values = explainer.shap_values(X_val)
shap.summary_plot(shap_values, X_val, feature_names=learner._feature_names)
```

---

## 六、預估工時

| 任務 | 工時 |
|------|------|
| 設計並實作特徵提取（`build_feature_vector()`） | 2-3 天 |
| 實作訓練資料生成腳本 | 2-3 天 |
| 實作 `MLMetaLearner` 類別 | 1-2 天 |
| 整合到 `AIStrategyFusion` | 1 天 |
| 訓練 + 驗證 + 調參 | 3-5 天 |
| **合計** | **約 2-3 週** |

---

## 七、依賴清單

```toml
# 需要新增至 pyproject.toml 的依賴
lightgbm>=4.0.0          # 首選 ML 模型
xgboost>=2.0.0           # 備選 ML 模型（可選）
shap>=0.44.0             # 特徵解釋（可選，但強烈建議）
scikit-learn>=1.3.0      # TimeSeriesSplit, 評估指標（可能已有）
```

---

## 八、風險與注意事項

### 8.1 未來資訊洩漏（Data Leakage）

**最嚴重的錯誤：** 在計算標籤時使用了未來資訊。

```python
# ❌ 錯誤：用當前和未來的資料計算技術指標作為特徵
features["rsi"] = rsi_at_close_of_this_bar   # 這根K線還沒收盤時拿不到

# ✅ 正確：特徵只能用已確認的歷史資料
features["rsi"] = rsi_at_close_of_PREVIOUS_bar  # 已收盤K線的RSI
```

### 8.2 過擬合風險

```
• 用 BTC/USDT 1h 2024年資料訓練，對 2024年有效，但 2025/2026年市場結構改變了
• 緩解方式：
  - Walk-Forward 重訓練（每個月重新訓練一次）
  - 用多時框架（1h + 4h + 日K）的特徵增加泛化能力
  - 限制模型複雜度（max_depth <= 6，n_estimators <= 300）
```

### 8.3 樣本不平衡

```
• BTC 的歷史通常多頭居多，導致 LONG 樣本遠多於 SHORT
• 解決方式：class_weight="balanced"（LightGBM/XGBoost 支援）
```

---

*下一份文件：`STRATEGY_FUSION_PLAN_C_REGIME_ROUTING.md`（硬性體制路由，最快落地的方案）*
