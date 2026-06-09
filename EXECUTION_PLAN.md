# BioNeuronAI 商業級「一步到位」執行計劃（Week 1-2 具體可執行版）

**目標**：讓模型（TinyLLM）的參數真正驅動交易決策結構，並讓自學習閉環產生可驗證的真實 artifact（而非 shim + 空轉）。

**為什麼這是關鍵**：
- 目前模型只有 ~25-40% 權重 + 512 維只用 23 維 + v1 資料被硬塞成 v2 格式 → 模型參數對實際下單（方向、SL、TP、lev、size）的影響很小。
- 學習閉環接通但沒有真實 v2 格式資料 + 沒有 checkpoint → 「交易即訓練」還沒開始真正發生。

這個計劃專注 **最高槓桿的 6 個具體步驟**，每步都有：
- 確切指令（Windows pwsh 相容）
- 要改的檔案 + 行號提示
- 驗證方式（跑完看什麼輸出 / 什麼檔案出現）
- 預期結果

完成後你會看到：
- 模型輸出 65 維真實結構被使用
- 新聞開始提供主要方向偏好（不是只擋逆勢）
- ActionRecord 裡有原生 16x64 patches + 真實 65 維 raw_signal
- 第一次出現真實 lora_*.pt checkpoint
- paper-live 記錄顯示 AI 貢獻明顯增加

---

## 先決條件（5 分鐘檢查）

1. 確認你在專案根目錄：
   ```powershell
   cd C:\D\E\BioNeuronai
   pwd
   ```

2. 確認 Python 環境可用（3.13）：
   ```powershell
   python --version
   pip list | findstr torch
   ```

3. 確認 active model 存在：
   ```powershell
   ls model/my_100m_model_trained_20260510.pth
   ```

4. （推薦）先備份目前狀態：
   ```powershell
   git status
   # 如果想安全，先不要 commit，之後再決定
   ```

---

## Step 0: 建立基線（必須先做，30-60 分鐘）

**目的**：知道「改之前」模型貢獻有多少，之後才有對比。

執行：
```powershell
# 1. 跑一個短的 paper-live（讓它跑 20-50 筆交易或 1-2 小時）
python main.py trade --paper-live --paper-balance 10000 --symbol BTCUSDT --interval 1m --max-trades 30

# 按 Ctrl+C 停止（或讓它自然跑一段時間）

# 2. 查看最近的 paper_live 記錄（看 AI 有沒有被記錄）
Get-Content data/bioneuronai/trading/paper_live/orders.jsonl -Tail 5

# 3. 查看 signal_history 最後幾筆（看 features + signal）
python -c "
import json
with open('data/signal_history.jsonl') as f:
    lines = f.readlines()[-3:]
for i, line in enumerate(lines):
    d = json.loads(line)
    print(f'--- record {i} ---')
    print('features len:', len(d.get('features', [[]])[0]) if d.get('features') else 0)
    print('has ai_signal_score or model info:', 'ai' in str(d).lower() or 'model' in str(d).lower())
    print('keys:', list(d.keys())[:8])
"
```

**驗證通過條件**：
- orders.jsonl 有最近的交易
- signal_history 主要是 1024 維 features
- （此時）應該看不到明顯的 AI 65 維輸出或 direction_bias

記錄下目前的：
- 總交易數
- 勝率 / 總 PnL（如果有 summary）
- AI 信號被採用的感覺（從 log 看 "🤖 AI" 出現頻率）

---

## Step 1: 讓新聞從「過濾器」變成「方向提供者」（P1，最快見效）

**檔案**：
- src/bioneuronai/strategies/strategy_fusion.py （目前只有 _apply_asymmetric_filter）
- src/bioneuronai/analysis/news/analyzer.py 或 rag/services/news_adapter.py
- src/bioneuronai/core/trading_engine.py （_fuse_signals）

**具體要做的事**：
在 NewsAdapter / CryptoNewsAnalyzer 新增 `get_direction_bias(symbol)` 方法，回傳：
```python
{"direction": "LONG" | "SHORT" | "NEUTRAL", "strength": 0.0-1.0, "reason": "string"}
```

然後在 fusion 層優先使用這個 bias 作為框架。

**立即可執行的修改**：

先在 `src/bioneuronai/analysis/news/analyzer.py` 裡找 `CryptoNewsAnalyzer` class，新增方法。

最小可運行版（加在 analyzer.py 合適 class 裡）：

```python
def get_direction_bias(self, symbol: str = "BTCUSDT") -> dict:
    """新增：回傳主要方向偏好（這是 P1 核心）"""
    try:
        result = self.analyze_news(symbol, hours=6)
        score = getattr(result, 'event_score', 0.0) or getattr(result, 'sentiment_score', 0.0)
        
        if score > 1.5:
            return {"direction": "LONG", "strength": min(1.0, abs(score)/5), "reason": f"強烈看多 (score={score:.2f})"}
        elif score < -1.5:
            return {"direction": "SHORT", "strength": min(1.0, abs(score)/5), "reason": f"強烈看空 (score={score:.2f})"}
        else:
            return {"direction": "NEUTRAL", "strength": 0.3, "reason": f"中性 (score={score:.2f})"}
    except Exception as e:
        return {"direction": "NEUTRAL", "strength": 0.0, "reason": f"分析失敗: {e}"}
```

然後在 `trading_engine.py` 的 `_process_market_data` 附近，抓到 news 後呼叫 bias，並傳給 generate_trading_signal。

在 `_fuse_signals` 裡加優先判斷（讓新聞強度高時主導方向框架）。

**驗證**：
跑一次 trade 命令，看 log 是否出現 direction bias，或在 _record_decision 裡把 bias 記進 ActionRecord。

---

## Step 2: 讓 InferenceEngine 真正支援 v2 輸出（P3，核心）

目前 InferenceEngine 主要走 1024 扁平 + 512 輸出 + 23 維解讀。

**要改的檔案**：`src/bioneuronai/core/inference_engine.py`

**具體步驟**：

1. 在 InferenceEngine.__init__ 加入 flag：
   ```python
   self.use_v2_mode: bool = False   # 新增
   ```

2. 在 load_model 後可以切換：
   ```python
   def enable_v2_mode(self):
       self.use_v2_mode = True
       # 之後 predict 時走 patch 路徑 + 65 維 interpreter
   ```

3. 修改 predict 方法，讓 use_v2_mode 時：
   - 把 klines 轉成 16x64 patches
   - 呼叫 model.forward_signal(patches) 拿 raw 65 維 + decoded
   - 用對應的解讀建立 TradingSignal（對應 tiny_llm_v2 OUTPUT_LAYOUT）

**最小起步版**（建議先加 flag + 一個 stub + 簡單 patch 轉換）：

在 `predict` 函數開頭加 if。

**驗證**：
```powershell
python -c "
from src.bioneuronai.core.inference_engine import InferenceEngine
eng = InferenceEngine()
eng.load_model('my_100m_model')
eng.enable_v2_mode()
# 給一些 klines 測試
print('v2 mode enabled, now call predict with real klines to see 65-dim output')
"
```

---

## Step 3: 清理 ActionRecord 產生邏輯（去 shim）

**檔案**：`src/bioneuronai/core/trading_engine.py` 的 `_record_decision` 方法。

目前有 reshape(16,64) + pad to 65 的 shim。

**改成**：
- 當 v2 模式時，直接從 inference_engine 拿真正的 patches 和 65 維 raw。
- 把 fill_decision 傳入的 decoded 包含 uncertainty、hold_period_probs、pattern_probs 等正確結構。

目標：讓存進記憶層的是原生 v2 格式資料。

---

## Step 4: 確保 OnlineLearner 真的被啟動並產生 checkpoint

**檔案**：`src/bioneuronai/core/trading_engine.py`

在 `load_ai_model` 成功後，確保 OnlineLearner 被初始化（指向正確的 live model）。

在 T2 (notify_trade_closed) 時會自動呼叫 learner.record_outcome。

**驗證**：
跑 paper-live 一段時間後，檢查：
```powershell
ls data/bioneuronai/checkpoints/lora/
```
是否有 lora_step_*.pt 出現。

---

## Step 5: 執行 + 驗證（最重要）

1. 改完上面後，重新跑同樣的 paper-live 命令。
2. 跑驗證：
   - 檢查 lora checkpoint 是否出現
   - 檢查 extreme_vault 是否有東西
   - 檢查最近 ActionRecord / signal log 是否有 direction_bias + 65 維 + patches
   - 對比 Step 0 的 AI 貢獻頻率與現在

---

## 執行順序建議（最現實的 1 週計劃）

**Day 1**：Step 0 基線 + Step 1 新聞 bias 原型（加 get_direction_bias + 簡單融合調整）
**Day 2-3**：Step 2 InferenceEngine 加 v2 flag + 最小 patch 支援 + Step 3 清理 record shim
**Day 4**：Step 4 確保 learner 啟動 + 小修正
**Day 5-7**：Step 5 跑對比實驗 + 收集數據 + 記錄改善

每改完一個大步，就跑一次短 paper-live（--max-trades 20）做對比。

---

## 後續（Week 3+ 讓它真正能跟商業產品比）

- 訓練/適配一個真正的 v2 checkpoint（用 nlp/training/unified_trainer 針對 signal 任務）
- 把新聞 bias + v2 65 維 + Meta-Learner 做 end-to-end 驗證
- 建立自動化 before/after + regime 報告
- 前端 dashboard 顯示「這次決策 AI 貢獻了多少 % 以及學習後的改善」

---

**現在就開始的命令（複製貼上執行）**：

```powershell
# 1. 先做基線
python main.py trade --paper-live --paper-balance 10000 --symbol BTCUSDT --interval 1m --max-trades 25

# 2. 看目前狀態
Get-Content data/bioneuronai/trading/paper_live/orders.jsonl -Tail 3
```

改完 Step 1-2 後，再跑一次同樣命令，然後比對差異。

---

需要我現在就產生**第一批精準的 search_replace 修改**（新聞 bias + InferenceEngine v2 flag + record 清理）直接幫你套用嗎？

還是你想先自己跑 Step 0 基線，跑完告訴我結果，我再給下一批精準 patch？

告訴我你的下一步，我立刻給可執行的東西。