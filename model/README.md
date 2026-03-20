# 交易模型權重

## 目錄

- [當前模型](#當前模型)
- [Git LFS 說明](#git-lfs-說明)
- [為什麼選擇這個模型？](#為什麼選擇這個模型)
- [輸入特徵設計](#輸入特徵設計)
- [整合到交易系統](#整合到交易系統)
- [注意事項](#注意事項)
- [後續優化方向](#後續優化方向)
- [子目錄文檔](#子目錄文檔)

---

## 當前模型

### my_100m_model.pth (445 MB)

**架構**: MLP (Multi-Layer Perceptron)
**參數量**: ~111M
**用途**: 加密貨幣日內短線交易決策
**儲存方式**: Git LFS（Large File Storage）

#### 模型結構
```
輸入層: 1024 維特徵向量
  ↓
隱藏層1: 8192 維 (Layer Norm + GELU + Dropout)
  ↓
隱藏層2: 8192 維 (Layer Norm + GELU + Dropout)
  ↓
隱藏層3: 4096 維 (Layer Norm + GELU + Dropout)
  ↓
輸出層: 512 維
```

#### 推理速度
- CPU: ~2-5ms
- GPU: ~0.5-1ms

---

## Git LFS 說明

模型權重 `my_100m_model.pth`（445 MB）透過 **Git LFS** 管理，不直接存放在 Git 物件中。

### 本地取得權重步驟

```bash
# 1. 安裝 Git LFS（若尚未安裝）
# macOS
brew install git-lfs

# Ubuntu / Debian
sudo apt install git-lfs

# Windows
# 下載安裝：https://git-lfs.com

# 2. 初始化 Git LFS
git lfs install

# 3. 拉取權重檔案
git lfs pull
```

### 驗證權重是否已下載

```bash
# 檢查檔案大小（應約 445 MB）
ls -lh model/my_100m_model.pth

# 若顯示 134 bytes 且內容開頭為 "version https://git-lfs.github.com/spec/v1"
# 表示只有 LFS pointer，需要執行 git lfs pull
```

### LFS 追蹤設定

`.gitattributes` 中已設定：
```
model/my_100m_model.pth filter=lfs diff=lfs merge=lfs -text
```

### 注意事項

- 雲端 CI/CD 環境可能不支援 LFS，需確認環境已安裝 `git-lfs` 並執行 `git lfs pull`
- Docker 建構時，需在 `COPY` 前確保 LFS 檔案已下載
- 推論引擎使用 `weights_only=True` 載入，LFS pointer 檔案（134 bytes 文字檔）無法被 `torch.load()` 解析，必須取得完整權重

---

#### 使用方式

```python
import torch
from pathlib import Path

# 載入模型
model_path = Path("model/my_100m_model.pth")
checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)

# 創建模型實例
from archived.pytorch_100m_model import HundredMillionModel
model = HundredMillionModel(
    input_dim=1024,
    hidden_dims=[8192, 8192, 4096],
    output_dim=512
)
model.load_state_dict(checkpoint)
model.eval()

# 推論
with torch.no_grad():
    features = torch.randn(1, 1024)  # 你的市場特徵
    output = model(features)
```

## 🎯 為什麼選擇這個模型？

### ✅ 適合日內短線交易
1. **速度快** - 毫秒級響應，適合高頻決策
2. **固定輸入** - 接受當前市場狀態的特徵向量
3. **簡單高效** - 不需要複雜的序列處理

### ❌ 不選擇 Transformer (tiny_llm_100m.pth)
1. 推理較慢 (~50-100ms)
2. 需要序列輸入（歷史K線）
3. 內存消耗大
4. 對日內短線來說過於複雜

## 📊 輸入特徵設計

模型需要 1024 維特徵向量，建議包含：

### 技術指標類 (~100 維)
- RSI (多週期: 7, 14, 21)
- MACD (線、信號線、柱狀圖)
- 布林帶 (上、中、下軌)
- KDJ, ATR, OBV 等

### 價格行為類 (~100 維)
- 當前價格、開盤價、最高價、最低價
- 各週期收益率 (1m, 5m, 15m, 30m, 1h)
- 價格動量、加速度

### 成交量類 (~50 維)
- 當前成交量
- 成交量比率
- 買賣壓力指標

### 市場微觀結構 (~100 維)
- 買賣價差
- 訂單簿深度
- 大單流入/流出

### 時間特徵 (~50 維)
- 小時 (0-23)
- 星期 (0-6)
- 是否交易高峰期

### 跨品種相關性 (~200 維)
- BTC-ETH 相關性
- 與主流幣種的相對強度
- 市場情緒指標

### 其他特徵 (~424 維)
- 預留空間供未來擴展
- 可加入新聞情緒分數
- 資金費率等

## 🔗 整合到交易系統

模型權重放在此目錄後，在交易系統中的引用路徑：

```python
# 從項目根目錄引用
model_path = "model/my_100m_model.pth"

# 或使用絕對路徑
model_path = Path(__file__).parent.parent / "model" / "my_100m_model.pth"
```

### 與 Analysis 模組整合

模型的 1024 維輸入特徵由 `analysis` 模組的 `MarketMicrostructure` 類生成：

```python
from bioneuronai.analysis import MarketMicrostructure

# 初始化特徵工程器
feature_engineer = MarketMicrostructure()

# 生成模型輸入特徵
features_1024d = feature_engineer.create_model_features(market_data, orderbook_data)

# 輸入到模型進行預測
prediction = model.predict(features_1024d)
```

特徵包括：
- 技術指標計算
- 市場微觀結構分析
- 成交量分布特徵
- 清算風險評估
- 時間和季節性特徵

## 📝 注意事項

1. **特徵標準化**: 輸入特徵需要標準化/歸一化
2. **模型微調**: 建議使用真實交易數據進行微調
3. **版本管理**: 訓練新版本後保留舊版本做對比
4. **性能監控**: 持續追蹤模型預測準確率

## 🚀 後續優化方向

1. 收集實盤交易數據
2. 使用強化學習進一步訓練
3. 添加對抗訓練提高魯棒性
4. 針對不同市場環境訓練專門模型

---

## 📁 子目錄文檔

| 子目錄 | 說明 | README |
|--------|------|--------|
| `tiny_llm_en_zh/` | 英中雙語 LLM 基礎版本（未訓練） | [README](tiny_llm_en_zh/README.md) |
| `tiny_llm_en_zh_trained/` | 英中雙語 LLM 訓練版本 ⭐ 推薦 | [README](tiny_llm_en_zh_trained/README.md) |

---

**最後更新**: 2026-03-20
**模型狀態**: Git LFS 管理，本地 `git lfs pull` 後可用於推論

> 📖 上層目錄：[根目錄 README](../README.md)
