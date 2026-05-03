# BioNeuronAI 開發日誌

## 2026-05-02 — Meta-Learner 策略權重神經網路 初版整合

### 📋 開發背景

本次開發在一次對話中完成，目標是**將 `AIStrategyFusion` 從「寫死的 If-Else 規則」升級為「由神經網路動態決定策略資金權重」**，並確保所有實作都使用真實歷史資料，而非假資料（`torch.randn`）。

---

### ✅ 本次完成的工作

#### 1. 新建 `meta_learner` 子套件

路徑：`src/bioneuronai/strategies/meta_learner/`

| 檔案 | 功能 | 重要設計決策 |
|------|------|------|
| `__init__.py` | 套件入口 | 匯出三個核心類別 |
| `model.py` | 神經網路模型 (`MetaLearnerModel`) | 68→128→64→5，LayerNorm，Xavier 初始化 |
| `feature_extractor.py` | 從 OHLCV 計算 60 維技術特徵 + 8 維事件特徵 | 所有指標均正規化至 [-1, 1] 或 [0, 1] |
| `trainer.py` | 完整訓練管線 | 真實資料載入、軟標籤生成、KL 散度損失、Early Stopping |

#### 2. 新建訓練腳本

`tools/train_meta_learner.py` — 一鍵執行訓練的 CLI 腳本

#### 3. 更新 `strategy_fusion.py`

- 新增 `FusionMethod.META_LEARNER` 枚舉值
- 將 `_fuse_by_meta_learner()` 從「寫死假數字」改為「真正載入並呼叫訓練好的模型」
- 實作懶加載機制（Lazy Loading），避免每次融合都重新載入模型
- 完整的降級機制（Fallback）：若模型未訓練或 PyTorch 未安裝，自動回退到 WEIGHTED_VOTE

#### 4. 首次訓練完成

| 訓練指標 | 數值 |
|------|------|
| 資料來源 | `backtest/data/binance_historical` (BTCUSDT 1H 2020-2023) |
| K 線總數 | 34,141 根 |
| 訓練樣本數 | 3,406 個（視窗 80 根，步長 10） |
| 訓練集 / 驗證集 | 2,896 / 510 |
| 最佳驗證損失 | 0.5358（KL 散度，Epoch 18 達到） |
| Early Stopping | 在 Epoch 33 觸發（patience=15） |
| 模型儲存路徑 | `rl_models/meta_learner.pth` |
| 訓練紀錄 | `rl_models/meta_learner_training_log.json` |

---

### 🧠 技術設計說明

#### 特徵工程（`feature_extractor.py`）

市場特徵共 **60 維**，分組如下：

```
[0-2]   均線系列 (SMA20, SMA50, 均線交叉)
[3]     RSI(14)
[4-6]   MACD(12,26,9) 三線
[7-8]   布林通道寬度 + 位置
[9]     ATR(14)
[10]    ADX(14)
[11-15] 多週期動能 (1, 3, 5, 10, 20 根)
[16-17] 成交量比率 (20期, 5期)
[18-19] 最高/最低價分位數
[20-22] K 線形態 (實體、上影線、下影線)
[23-24] 波動率 (20期, 5期)
[25-26] Stochastic(14,3)
[27]    Williams %R(14)
[28]    CCI(14)
[29]    ROC(10)
[30-49] 過去 20 根標準化收益率序列
[50-59] 過去 10 根標準化成交量序列
```

事件特徵共 **8 維**：
```
[0] 新聞情緒分數 (-1 ~ +1)
[1] 恐慌貪婪指數 (0 ~ 1)
[2] OI 變化 (%)
[3] 資金費率
[4] BTC 市佔率
[5] 市值變化
[6] 事件強度 (衰減後)
[7] RAG 歷史勝率
```

#### 標籤生成策略

對每個時間視窗，用輕量代理函數模擬各策略方向（±1），再乘以未來 5 根 K 線的實際報酬，得出「各策略的預期績效分數」。透過 Softmax 正規化後得到軟標籤（Soft Labels）。

> **局限性**：目前標籤是基於技術指標的「方向 × 報酬」代理值，而非完整策略回測的真實 PnL。後續應以 `NewsEventContract` 的驗證資料替換。

#### 模型規格

```
Input: [market_features (60D) | event_features (8D)] → 68D

Linear(68, 128) → LayerNorm(128) → ReLU → Dropout(0.2)
Linear(128, 64) → LayerNorm(64)  → ReLU → Dropout(0.1)
Linear(64, 5)   → Softmax

Output: [trend_following, swing_trading, mean_reversion, breakout, direction_change]
        weights sum to 1.0 (資金分配比例)

Total Parameters: 17,797
```

---

### ⚠️ 已知限制與技術債

| 問題 | 影響 | 建議處理時機 |
|------|------|------|
| 訓練標籤為代理標籤（非真實 PnL） | 模型可能學到次優的策略選擇邏輯 | 待 NewsEventContract 完成後重訓 |
| 事件特徵 (8 維) 目前全為 neutral 預設值 | Meta-Learner 無法感知新聞事件的影響 | 待 CryptoNewsAnalyzer 整合完成後接入 |
| 模型未納入 RL 持續學習機制 | 無法隨市場環境自動適應 | Phase 4 目標（尚未規劃） |
| 訓練資料僅涵蓋 2020-2023 | 缺少 2024-2026 市場環境 | 補充近期資料後重訓 |

---

### 🔄 如何使用

#### 重新訓練模型

```bash
# 在專案根目錄下執行
python tools/train_meta_learner.py
```

#### 切換至 Meta-Learner 模式

在 `trading_engine.py` 或 `core/` 相關初始化中：

```python
from bioneuronai.strategies.strategy_fusion import AIStrategyFusion, FusionMethod

# 改用神經網路決定策略權重
fusion = AIStrategyFusion(fusion_method=FusionMethod.META_LEARNER)
```

#### 使用預設的啟發式模式（現行安全模式）

```python
# 不傳參數，預設使用 MARKET_ADAPTIVE（啟發式規則）
fusion = AIStrategyFusion()
```

---

### 📌 下一步建議

1. **[高優先] 實作 `NewsEventContract`**：這是讓 Meta-Learner 的 8 維事件特徵得到真實資料的前提
2. **[中優先] 整合 CryptoNewsAnalyzer 情緒輸出**：在 `generate_fusion_signal()` 呼叫時傳入真實 `news_sentiment`
3. **[低優先] 補充 2024-2026 訓練資料**：下載近期 K 線資料並重訓

---

*開發者：AI-assisted session (Antigravity)*
*開發環境：PyTorch 2.9.1+cpu, NumPy 2.3.4, Python on Windows*
