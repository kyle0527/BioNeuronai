# my_100m_model 重訓前後技術報告
> 日期：2026-05-10
> 範圍：`my_100m_model.pth` 原始基準、`best_model_run1.pth`、`best_model_run2.pth`、`my_100m_model_trained_20260510.pth`

---

## 1. 結論摘要

本次檢查確認，雲端訓練後的 `best_model_run1.pth` 與 `best_model_run2.pth` 已搬入專案 `model/` 目錄，且檔案雜湊與下載資料夾來源一致。現役模型不是直接使用 raw `best_model_run2.pth`，而是使用已包裝為 runtime 相容格式的：

```text
model/my_100m_model_trained_20260510.pth
```

該現役模型已登記於：

```text
config/active_model.json
```

從數值看，Run2 是目前三者中最適合保留為現役版本的模型：

| 項目 | 原始模型 | Run1 | Run2 / 現役 |
| --- | ---: | ---: | ---: |
| QA eval loss | 10.6886 | 8.6487 | 7.1112 |
| QA perplexity | 43,853 | 5,703 | 1,226 |
| QA top-1 accuracy | 0.00% | 5.07% | 21.23% |
| 參數量 | 134,682,368 | 134,682,368 | 134,682,368 |
| tensor key 數 | 159 | 159 | 159 |

重要限制：這些數字可以證明模型已改變、可載入、在現有交易問答資料上的 next-token 表現改善，也可以證明交易訊號輸出向量明顯不同；但尚不能證明實盤或回測績效改善。交易績效仍需要固定 K 線區間回放，比較收益、回撤、Sharpe、勝率、交易次數與成本後才能定論。

---

## 2. 檔案與角色

### 2.1 原始模型

```text
model/my_100m_model.pth
```

角色：原始基準與回退版本。

格式：

```python
{
  "state_dict": ...,
  "config": ...
}
```

此格式可直接提供 `TinyLLMConfig` 所需設定，例如：

```text
vocab_size=30000
max_seq_length=512
embed_dim=768
num_heads=12
num_layers=12
ffn_dim=3072
use_numeric_mode=True
numeric_input_dim=1024
signal_output_dim=512
numeric_seq_len=16
```

### 2.2 訓練後 raw 權重

```text
model/best_model_run1.pth
model/best_model_run2.pth
```

角色：雲端訓練產出的 raw state_dict，供比較、備援與重新包裝使用。

格式：

```python
OrderedDict(...)
```

這兩個檔案缺少 `config`。若直接交給目前 runtime 載入器，在某些路徑會因預設 `TinyLLMConfig` 使用 `vocab_size=50257` 而與權重中的 `vocab_size=30000` 不相容。因此不建議把 raw run 檔直接 promote 成主線。

### 2.3 現役包裝模型

```text
model/my_100m_model_trained_20260510.pth
```

角色：將 `best_model_run2.pth` 的 state_dict 加上原始模型 config 後形成的 runtime 相容 checkpoint。

格式：

```python
{
  "state_dict": <best_model_run2 state_dict>,
  "config": <copied from my_100m_model.pth>,
  "metadata": ...
}
```

它是目前 `config/active_model.json` 指向的現役交易模型。

---

## 3. 純看格式與架構的差異

若只看模型內容結構與架構，訓練前後的結論是：

| 比較項 | 原始模型 | Run1 / Run2 raw | 現役包裝 Run2 |
| --- | --- | --- | --- |
| checkpoint 容器 | `dict` | `OrderedDict` | `dict` |
| 是否含 `config` | 是 | 否 | 是 |
| 是否含 `state_dict` key | 是 | 否，本身就是 state_dict | 是 |
| 模型類別 | TinyLLM | TinyLLM | TinyLLM |
| 是否支援文字路徑 | 是 | 是 | 是 |
| 是否支援 numeric signal path | 是 | 是 | 是 |
| `numeric_proj` | 有 | 有 | 有 |
| `signal_head` | 有 | 有 | 有 |
| tensor key 數 | 159 | 159 | 159 |
| 參數量 | 134,682,368 | 134,682,368 | 134,682,368 |

所以它們不是不同架構的模型；架構完全相同，差異主要是：

1. 權重數值不同。
2. raw run 檔缺少 runtime config。
3. 現役包裝檔補回 config，因此可被現有 `InferenceEngine` 穩定載入。

---

## 4. 權重數值差異

權重層級比較結果：

| 比較 | 相對 L2 差異 | 最大單點差異 | 改變 tensor | 總 tensor |
| --- | ---: | ---: | ---: | ---: |
| 原始 vs Run1 | 0.060147 | 0.029516 | 159 | 159 |
| 原始 vs Run2 | 0.062681 | 0.029463 | 159 | 159 |
| Run1 vs Run2 | 0.015812 | 0.000856 | 149 | 159 |

解讀：

- Run1 與 Run2 都不是原始模型的單純複製，所有 159 個 tensor 都相對原始模型發生變化。
- Run2 比 Run1 距離原始模型略遠，代表它在同一架構上經過更多或不同階段的訓練更新。
- Run1 與 Run2 彼此很接近，表示兩者是同一訓練脈絡下的相鄰或相近成果，而不是完全不同來源的模型。

---

## 5. 問答能力差異

### 5.1 驗證資料

使用專案內現有資料：

```text
src/nlp/training/trading_dialogue_data.py::ALL_TRADING_DATA
```

資料量：

| 項目 | 數量 |
| --- | ---: |
| QA 樣本 | 33 |
| 有效 token | 4,597 |
| tokenizer | `model/tokenizer/vocab.json` |
| 評估方式 | next-token prediction |

### 5.2 指標

| 模型 | Loss | Perplexity | Top-1 Accuracy |
| --- | ---: | ---: | ---: |
| 原始模型 | 10.6886 | 43,853 | 0.00% |
| Run1 | 8.6487 | 5,703 | 5.07% |
| Run2 / 現役 | 7.1112 | 1,226 | 21.23% |

相對改善：

| 比較 | Loss 下降 | Perplexity 下降 | Accuracy 改善 |
| --- | ---: | ---: | ---: |
| Run1 vs 原始 | 19.1% | 87.0% | +5.07 percentage points |
| Run2 vs 原始 | 33.5% | 97.2% | +21.23 percentage points |
| Run2 vs Run1 | 17.8% | 78.5% | +16.16 percentage points |

### 5.3 這些數字代表什麼

這組評估衡量的是：模型看到交易問答格式的前文後，預測下一個 token 的能力。

有用之處：

- 能量化模型是否更貼近專案內交易問答語料。
- 能比較原始模型、Run1、Run2 的語言建模能力。
- Loss 與 perplexity 明顯下降，表示 Run2 在這批資料上的回答延續能力更好。

限制：

- 這不是一般聊天 benchmark。
- 樣本只有 33 筆，不能代表所有問題。
- next-token accuracy 改善不等於回答一定正確，也不等於交易建議可靠。
- 這裡沒有做人工語義評分，沒有判斷答案是否金融上完全正確。

---

## 6. 交易訊號能力差異

### 6.1 驗證方式

使用相同輸入直接呼叫：

```python
TinyLLM.forward_signal(input_tensor)
```

輸入 shape：

```text
(batch, 16, 1024)
```

輸出 shape：

```text
(batch, 512)
```

比較三組固定輸入：

| 輸入 | 目的 |
| --- | --- |
| zeros | 檢查無訊號基準輸入下輸出分布 |
| random_batch8 | 檢查一般數值擾動下輸出分布 |
| trend_like | 檢查簡化趨勢型特徵下輸出分布 |

### 6.2 輸出向量幅度

| 輸入 | 原始 norm | Run1 norm | Run2 norm |
| --- | ---: | ---: | ---: |
| zeros | 12.2042 | 15.6209 | 15.0867 |
| random_batch8 | 12.8540 | 17.1145 | 16.6941 |
| trend_like | 12.4192 | 16.1937 | 15.1217 |

Run2 相對原始模型：

| 輸入 | norm 變化 |
| --- | ---: |
| zeros | +23.6% |
| random_batch8 | +29.9% |
| trend_like | +21.8% |

解讀：訓練後模型的 signal head 輸出幅度更大，代表同一輸入下產生的 512 維交易訊號向量分布已明顯改變。

### 6.3 輸出向量相似度

| 輸入 | 原始 vs Run1 cosine | 原始 vs Run2 cosine | Run1 vs Run2 cosine |
| --- | ---: | ---: | ---: |
| zeros | 0.0464 | 0.0491 | 0.9658 |
| random_batch8 | 0.2251 | 0.2213 | 0.9634 |
| trend_like | 0.2422 | 0.2587 | 0.9586 |

解讀：

- 原始模型與訓練後模型的 signal output 幾乎不是同方向向量。
- Run1 與 Run2 的 signal output 高度相似。
- 這再次證明訓練後模型不是只有檔案格式變更，而是實際輸出行為已改變。

### 6.4 SignalInterpreter 解讀結果

使用目前 `SignalInterpreter` 對第一筆輸出做解讀：

| 輸入 | 模型 | signal | confidence | risk | leverage | position |
| --- | --- | --- | ---: | --- | ---: | ---: |
| zeros | 原始 | neutral | 19.99% | medium | 6 | 7.54% |
| zeros | Run1 | neutral | 32.93% | high | 3 | 4.58% |
| zeros | Run2 | neutral | 35.75% | low | 3 | 4.85% |
| random_batch8 | 原始 | neutral | 39.70% | extreme | 2 | 7.59% |
| random_batch8 | Run1 | neutral | 39.14% | extreme | 4 | 5.54% |
| random_batch8 | Run2 | neutral | 39.67% | extreme | 2 | 5.69% |
| trend_like | 原始 | neutral | 25.92% | medium | 2 | 4.60% |
| trend_like | Run1 | neutral | 33.59% | low | 2 | 3.10% |
| trend_like | Run2 | neutral | 36.43% | medium | 2 | 3.21% |

解讀：

- 在這三組固定輸入中，方向仍是 `neutral`。
- 訓練後模型通常提高 confidence，但並未直接變成 aggressive long/short。
- risk、leverage、position 的解讀發生變化，代表下游交易參數會受影響。

限制：

- zeros/random/trend_like 是工程檢查輸入，不是真實完整市場情境。
- 這能驗證推論管線和輸出差異，但不能代表交易收益。
- 若要判斷交易效果，必須用真實 K 線、交易成本、滑價與回測引擎做完整回放。

---

## 7. 使用的驗證方法與有效性

### 7.1 檔案一致性驗證

方法：

```powershell
Get-FileHash -Algorithm SHA256 ...
```

結果：

| 檔案 | SHA256 |
| --- | --- |
| `model/best_model_run1.pth` | `FCF682CB8E5A45E4A85A2BDBFB2D6548A1F7FE6F2AB83A4B7C9CA95D51601D37` |
| `model/best_model_run2.pth` | `B6657850D691ECD33EE1282DA6AD3654A25DA754587D5B559218D1E358D2DE90` |
| `model/my_100m_model.pth` | `54EFBE4F49C5082ED05D4D9C1EF0F95158168B3BE576818F9509A59343F50EAA` |
| `model/my_100m_model_trained_20260510.pth` | `4124C71CBA4EB562C7E25E213C7280550FFEDF7F5AEF25981F19B92042AF539F` |

有效性：

- 可以證明搬入專案的 raw 權重與下載來源一致。
- 可以防止誤用同名但不同內容的檔案。

限制：

- 只能證明檔案一致，不能證明模型品質。

### 7.2 checkpoint 結構檢查

方法：

```python
torch.load(path, map_location="cpu", weights_only=True)
```

檢查項：

- checkpoint type
- key 數量
- tensor shape
- 是否包含 `numeric_proj`
- 是否包含 `signal_head`
- 是否包含 `config`

有效性：

- 可以確認模型架構是否與 runtime 相容。
- 可以確認 raw run 檔缺少 config 的問題。

限制：

- 不能評估回答品質或交易績效。

### 7.3 runtime 載入驗證

方法：

```python
from bioneuronai.core.inference_engine import InferenceEngine

engine = InferenceEngine(warmup=False)
engine.load_model("my_100m_model")
```

結果：

```text
resolved: C:\D\E\BioNeuronai\model\my_100m_model_trained_20260510.pth
is_ready: True
active_model: my_100m_model
output_shape: (1, 512)
finite: True
```

有效性：

- 可以證明目前專案主推論路徑能載入現役模型。
- 可以證明 `config/active_model.json` 已實際接入 `ModelLoader`。
- 可以證明 `forward_signal()` 可正常輸出 512 維交易訊號。

限制：

- 只證明可運行，不證明交易績效。

### 7.4 API 狀態驗證

方法：

```http
GET /api/v1/model/status
```

結果顯示：

```text
active_model.model_path = C:\D\E\BioNeuronai\model\my_100m_model_trained_20260510.pth
env.MODEL_PATH = C:\D\E\BioNeuronai\model\my_100m_model_trained_20260510.pth
```

有效性：

- 可以證明 API 層已知道目前 promoted 模型。
- 可以證明 UI/API 的模型狀態查詢與 `config/active_model.json` 對齊。

限制：

- API status 不等於交易引擎已載入模型。
- 若 API 行程未重啟，程式碼變更需重啟後才會進入該行程。

### 7.5 語言問答評估

方法：

- 使用 `ALL_TRADING_DATA` 的 33 筆交易問答。
- 使用同一個 tokenizer。
- 對 `[BOS] input [SEP] output [EOS]` 做 next-token prediction。
- 計算 cross entropy loss、perplexity、top-1 accuracy。

有效性：

- 可以比較模型在專案內交易問答資料上的語言建模能力。
- 適合判斷訓練後模型是否更貼近專案的問答語料。

限制：

- 樣本太少，不能代表泛化能力。
- 不是人工答案品質評分。
- 不能代表交易績效。

### 7.6 交易訊號輸出比較

方法：

- 使用相同固定輸入跑 `forward_signal()`。
- 比較輸出 norm、MSE、MAE、max abs、cosine similarity。
- 再由 `SignalInterpreter` 解讀 signal、confidence、risk、leverage、position。

有效性：

- 可以證明訓練前後模型對相同數值輸入的輸出行為已改變。
- 可以量化下游交易訊號解讀可能受到的影響。

限制：

- 固定輸入不是完整市場回放。
- 不能判斷長期收益、回撤或風險報酬。

---

## 8. 目前還不能宣稱的事

以下項目尚未完成足夠驗證，因此不應在文件或 UI 中寫成已證實：

1. 不能宣稱 Run2 一定比原始模型更會交易。
2. 不能宣稱 Run2 已通過實盤或 testnet 獲利驗證。
3. 不能宣稱 Run2 的 long/short 方向判斷更準。
4. 不能宣稱 QA 回答已達可直接作為投資建議的品質。
5. 不能把 raw `best_model_run2.pth` 視為 runtime 首選；首選應是包裝後的 `my_100m_model_trained_20260510.pth`。

---

## 9. 下一步建議

### 9.1 固定資料區間回測

用相同 K 線、相同手續費、相同滑價，比較：

| 比較組 | 模型 |
| --- | --- |
| baseline | `model/my_100m_model.pth` |
| candidate | `model/my_100m_model_trained_20260510.pth` |

應收集：

- total return
- max drawdown
- Sharpe
- Sortino
- win rate
- trade count
- gross PnL
- net PnL
- total fees
- average holding time

### 9.2 Shadow mode

若接近真實交易，建議先使用 monitor only 或 testnet：

- 不下真倉，只記錄模型建議。
- 與實際策略融合結果並排比較。
- 至少跑過不同市場狀態：趨勢、盤整、急跌、反彈。

### 9.3 建立正式模型評估紀錄

後續每次 promote 前，至少記錄：

- source checkpoint
- SHA256
- training data manifest
- training command
- validation loss
- fixed backtest result
- runtime load result
- promote timestamp

---

## 10. 最終判定

以目前已完成的驗證來看：

1. `best_model_run1.pth` 與 `best_model_run2.pth` 已正確搬入專案。
2. Run2 已被包裝成 runtime 相容 checkpoint。
3. `config/active_model.json` 已指向現役 Run2 包裝模型。
4. 核心 `ModelLoader` 已能在沒有環境變數時讀取 `config/active_model.json`。
5. 現役模型可被 `InferenceEngine` 載入並輸出 `(1, 512)` 的 finite signal vector。
6. 問答資料上的數值評估顯示 Run2 明顯優於原始模型與 Run1。
7. 交易訊號輸出顯示 Run2 與原始模型行為有明顯差異。
8. 尚未完成交易績效驗證，因此 Run2 可視為「已接入且可運行的訓練後候選/現役模型」，但不能視為「已證實獲利改善的模型」。
