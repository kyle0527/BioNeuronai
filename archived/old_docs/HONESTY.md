# 誠實性功能文檔 (Honesty Features)

## 概述

**"知道就說知道，不知道就說不知道"** - TinyLLM 的誠實性功能確保模型在不確定時能夠誠實承認，而不是產生幻覺內容。

這組功能包含 3 個核心模塊：
1. **不確定性量化** (Uncertainty Quantification) - 評估模型信心
2. **幻覺檢測** (Hallucination Detection) - 識別不可靠內容
3. **誠實生成** (Honest Generation) - 集成誠實生成策略

## 核心能力

### 能力 14: 不確定性量化

評估模型預測的信心程度，避免過度自信的輸出。

**主要功能:**
- **熵計算** - 測量預測的不確定性
- **Top-K 概率質量** - 評估概率分布的集中度
- **最大概率** - 獲取最有信心的預測
- **預測方差** - Monte Carlo Dropout 估計
- **信心分數** - 綜合評估 (0-1)
- **溫度校準** - 調整信心程度
- **校準評估** - ECE/MCE 指標

**使用示例:**
```python
from bioneuronai.uncertainty_quantification import (
    UncertaintyQuantifier,
    UncertaintyConfig
)

# 創建量化器
config = UncertaintyConfig(
    entropy_threshold=2.0,
    max_prob_threshold=0.3,
    top_k_mass_threshold=0.7
)
quantifier = UncertaintyQuantifier(config)

# 評估模型輸出
logits = model(input_ids).logits[:, -1, :]

# 計算信心分數
confidence = quantifier.compute_confidence_score(logits)
print(f"信心分數: {confidence.item():.3f}")

# 判斷是否不確定
is_uncertain, metrics = quantifier.is_uncertain(logits, method="ensemble")
if is_uncertain.item():
    print("模型不確定，建議不生成或提示用戶")
```

**信心指標:**
| 指標 | 說明 | 閾值 | 解釋 |
|------|------|------|------|
| 熵 (Entropy) | 預測分布的混亂程度 | >2.0 | 熵高=不確定 |
| 最大概率 | 最高概率的token | <0.3 | 最大概率低=不確定 |
| Top-K質量 | 前K個token的概率和 | <0.7 | 概率分散=不確定 |
| 信心分數 | 綜合評分 (0-1) | <0.5 | 低於0.5為不確定 |

### 能力 15: 幻覺檢測

檢測模型生成中的幻覺、矛盾和不一致內容。

**主要功能:**
- **重複檢測** - 識別過度重複的內容
- **模式重複** - 檢測重複的序列模式
- **語義漂移** - 發現生成偏離主題
- **自相矛盾** - 檢測前後矛盾的陳述
- **事實一致性** - 與已知事實對比
- **自我一致性** - 多次生成結果對比
- **依據驗證** - 檢查是否有來源支持

**使用示例:**
```python
from bioneuronai.hallucination_detection import (
    HallucinationDetector,
    SelfConsistencyChecker
)

detector = HallucinationDetector()

# 檢測重複
token_ids = [1, 2, 3, 1, 2, 3, 1, 2, 3]
is_repetitive, ratio = detector.detect_repetition(token_ids)
print(f"重複比例: {ratio:.2f}")

# 檢測矛盾
text = "這個方法是有效的。這個方法是無效的。"
has_contradiction, contradictions = detector.detect_contradiction(text)
if has_contradiction:
    print(f"發現矛盾: {contradictions}")

# 綜合幻覺分數
scores = detector.compute_hallucination_score(
    token_ids,
    confidence_scores=confidence_tensor,
    text=generated_text
)
print(f"整體幻覺分數: {scores['overall_hallucination_score']:.3f}")

# 自我一致性檢查
checker = SelfConsistencyChecker(num_samples=5)
consistency, common = checker.check_consistency(generated_texts)
print(f"一致性分數: {consistency:.3f}")
```

**幻覺類型:**
| 類型 | 檢測方法 | 嚴重性 |
|------|----------|--------|
| 過度重複 | 重複比例 | 中等 |
| 模式重複 | 序列模式匹配 | 中等 |
| 自相矛盾 | 關鍵詞對比 | 高 |
| 事實錯誤 | 知識庫驗證 | 高 |
| 語義漂移 | Embedding相似度 | 低 |

### 能力 16: 誠實生成

集成不確定性量化和幻覺檢測，實現誠實、可靠的文本生成。

**主要功能:**
- **信心感知生成** - 根據信心決定是否生成
- **幻覺阻斷** - 檢測到幻覺時停止
- **不確定回應** - 低信心時誠實承認
- **自我一致性驗證** - 多次生成確認
- **生成診斷** - 提供詳細的質量分析
- **可解釋性** - 返回信心分數和診斷信息

**使用示例:**
```python
from bioneuronai.honest_generation import (
    create_honest_generator,
    HonestGenerationConfig
)

# 創建誠實生成器
generator = create_honest_generator(
    model=model,
    tokenizer=tokenizer,
    confidence_threshold=0.5,  # 信心閾值
    hallucination_threshold=0.6,  # 幻覺閾值
    stop_on_uncertainty=True,  # 低信心時停止
    stop_on_hallucination=True  # 檢測到幻覺時停止
)

# 誠實生成
result = generator.generate_with_honesty(
    input_ids=input_ids,
    max_length=100,
    temperature=1.0,
    return_confidence=True,
    return_diagnostics=True
)

# 檢查結果
if result['is_uncertain']:
    print(f"模型不確定: {result['generated_text']}")
    print("可能的原因: 信心不足或檢測到幻覺")
else:
    print(f"生成結果: {result['generated_text']}")
    print(f"整體信心: {result['overall_confidence']:.3f}")

# 使用自我一致性
result = generator.generate_with_self_consistency(
    input_ids=input_ids,
    num_samples=5  # 生成5個樣本
)
print(f"多數答案: {result['majority_text']}")
print(f"一致性: {result['consistency_score']:.3f}")

# 診斷生成質量
report = generator.diagnose_generation(
    input_text="輸入問題",
    generated_text="生成的回答",
    token_ids=token_ids,
    confidence_scores=confidence_scores
)
print(f"質量評估: {report['quality_assessment']}")
if report['issues']:
    print(f"發現問題: {', '.join(report['issues'])}")
```

**配置選項:**
```python
config = HonestGenerationConfig(
    # 閾值設定
    confidence_threshold=0.5,  # 信心閾值
    hallucination_threshold=0.6,  # 幻覺閾值
    
    # 行為控制
    stop_on_uncertainty=True,  # 不確定時停止
    stop_on_hallucination=True,  # 幻覺時停止
    min_generation_length=5,  # 最小生成長度
    
    # 自我一致性
    use_self_consistency=True,  # 使用自我一致性
    num_consistency_samples=3,  # 採樣次數
    
    # 輸出控制
    return_confidence=True,  # 返回信心分數
    return_diagnostics=True,  # 返回診斷信息
    
    # 不確定回應
    uncertainty_responses=[
        "我不確定這個問題的答案。",
        "對不起，我對此沒有足夠的信心給出回答。",
        "這超出了我的知識範圍，我不知道。"
    ]
)
```

## 工作原理

### 誠實生成流程

```
輸入
  ↓
逐Token生成
  ↓
計算信心分數 ←→ 不確定性量化
  ↓
檢測幻覺風險 ←→ 幻覺檢測
  ↓
判斷是否繼續？
  ├─ 是 → 繼續生成
  └─ 否 → 停止並返回不確定回應
```

### 決策邏輯

每生成一個token時：
1. **計算信心分數** - 評估模型對這個token的確定程度
2. **累積幻覺分數** - 檢查是否出現重複、矛盾等問題
3. **綜合判斷** - 如果信心低或幻覺風險高，停止生成
4. **返回結果** - 有信心時返回生成內容，否則誠實承認不知道

## 性能影響

### 計算開銷

| 功能 | 額外計算 | 性能影響 |
|------|----------|----------|
| 不確定性量化 | Softmax + 統計計算 | +5-10% |
| 幻覺檢測 | 序列分析 | +3-5% |
| 自我一致性 | 多次生成 (3-5x) | +200-400% |
| 誠實生成 | 綜合以上 | +10-15% (單次) |

### 優化建議

1. **按需啟用** - 只在需要高可靠性時使用
2. **調整採樣數** - 減少自我一致性的採樣次數
3. **簡化檢測** - 只使用關鍵指標
4. **批量處理** - 對多個請求一起處理

## 實際應用

### 場景1: 問答系統
```python
# 對於問答任務，使用自我一致性確保答案可靠
result = generator.generate_with_self_consistency(
    input_ids=encode_question(question),
    num_samples=5,
    max_length=50
)

if result['consistency_score'] > 0.7:
    answer = result['majority_text']
    confidence = result['majority_confidence']
    print(f"答案: {answer} (信心: {confidence:.2f})")
else:
    print("對於這個問題，我無法給出確定的答案。")
```

### 場景2: 事實陳述
```python
# 檢查生成的事實陳述是否可靠
result = generator.generate_with_honesty(
    input_ids=input_ids,
    confidence_threshold=0.7,  # 更高的閾值
    hallucination_threshold=0.4,  # 更嚴格的幻覺檢測
    max_length=200
)

# 診斷質量
report = generator.diagnose_generation(
    input_text=input_text,
    generated_text=result['generated_text'],
    token_ids=result['generated_ids'][0].tolist(),
    confidence_scores=result['confidence_scores']
)

if report['quality_assessment'] == '良好':
    return result['generated_text']
else:
    return f"無法確定。問題: {', '.join(report['issues'])}"
```

### 場景3: 對話系統
```python
# 實時流式對話，低信心時及時停止
generator_config = HonestGenerationConfig(
    confidence_threshold=0.5,
    stop_on_uncertainty=True,
    min_generation_length=3  # 至少生成3個詞
)

result = generator.generate_with_honesty(
    input_ids=dialogue_context,
    max_length=100,
    temperature=0.8
)

if result['stopped_early']:
    print(f"停止原因: {result['stop_reason']}")
    print(result['generated_text'])  # "我不確定..."
```

## 對比分析

### 傳統生成 vs 誠實生成

| 維度 | 傳統生成 | 誠實生成 |
|------|----------|----------|
| 可靠性 | ❌ 可能產生幻覺 | ✅ 主動避免幻覺 |
| 透明性 | ❌ 無信心指標 | ✅ 提供信心分數 |
| 安全性 | ❌ 可能誤導用戶 | ✅ 誠實承認不知道 |
| 用戶體驗 | 🤔 無法判斷可信度 | ✅ 明確告知不確定性 |
| 計算成本 | ✅ 較低 | ⚠️ 略高 (+10-15%) |
| 生成長度 | ✅ 總能生成內容 | ⚠️ 可能提前停止 |

## 評估指標

### 誠實性指標

```python
# 1. 校準誤差 (Calibration Error)
from bioneuronai.uncertainty_quantification import CalibrationEvaluator

evaluator = CalibrationEvaluator(num_bins=10)
for predictions, targets, confidences in test_data:
    evaluator.add_batch(predictions, targets, confidences)

ece = evaluator.compute_ece()  # Expected Calibration Error
mce = evaluator.compute_mce()  # Maximum Calibration Error

print(f"ECE: {ece:.4f}")  # 越低越好，< 0.1 為良好校準
print(f"MCE: {mce:.4f}")  # 越低越好

# 2. 幻覺率 (Hallucination Rate)
hallucination_count = 0
total_generations = 0

for example in dataset:
    result = generator.generate_with_honesty(example)
    scores = detector.compute_hallucination_score(...)
    
    if scores['overall_hallucination_score'] > threshold:
        hallucination_count += 1
    total_generations += 1

hallucination_rate = hallucination_count / total_generations
print(f"幻覺率: {hallucination_rate:.2%}")

# 3. 誠實率 (Honesty Rate)
uncertain_correct = 0  # 不確定時確實不應該回答
total_uncertain = 0

for example in difficult_dataset:
    result = generator.generate_with_honesty(example)
    if result['is_uncertain']:
        total_uncertain += 1
        if is_actually_uncertain(example):
            uncertain_correct += 1

honesty_rate = uncertain_correct / total_uncertain
print(f"誠實率: {honesty_rate:.2%}")
```

## 最佳實踐

### 1. 根據任務調整閾值
```python
# 高風險任務（醫療、法律）
high_risk_config = HonestGenerationConfig(
    confidence_threshold=0.8,  # 更高
    hallucination_threshold=0.3,  # 更嚴格
)

# 一般對話
general_config = HonestGenerationConfig(
    confidence_threshold=0.5,
    hallucination_threshold=0.6,
)

# 創意生成
creative_config = HonestGenerationConfig(
    confidence_threshold=0.3,  # 更寬鬆
    stop_on_uncertainty=False,  # 不停止
)
```

### 2. 使用自我一致性驗證重要輸出
```python
# 對於重要決策，使用多次生成驗證
result = generator.generate_with_self_consistency(
    input_ids=input_ids,
    num_samples=5
)

if result['consistency_score'] > 0.8:
    # 高一致性，可信
    return result['majority_text']
else:
    # 低一致性，需要人工審核
    return {
        'status': 'uncertain',
        'samples': result['texts'],
        'consistency': result['consistency_score']
    }
```

### 3. 提供診斷信息輔助決策
```python
result = generator.generate_with_honesty(
    input_ids=input_ids,
    return_confidence=True,
    return_diagnostics=True
)

# 給用戶或系統提供詳細信息
response = {
    'text': result['generated_text'],
    'confidence': result['overall_confidence'],
    'reliable': result['overall_confidence'] > 0.7,
    'issues': []
}

if result.get('final_hallucination_score', 0) > 0.5:
    response['issues'].append('可能含有不準確信息')

return response
```

## 限制和改進方向

### 當前限制

1. **無法保證100%準確** - 信心分數是估計值
2. **依賴模型質量** - 基礎模型差則效果有限
3. **計算開銷** - 特別是自我一致性檢查
4. **需要調優** - 閾值需要根據任務調整
5. **簡單的矛盾檢測** - 基於規則，不夠智能

### 未來改進

- [ ] **NLI模型** - 使用自然語言推理檢測矛盾
- [ ] **知識圖譜** - 集成外部知識驗證
- [ ] **對抗訓練** - 訓練模型抵抗幻覺
- [ ] **主動學習** - 從用戶反饋中學習
- [ ] **多模態驗證** - 結合圖像、文本等

## 總結

誠實性功能讓 TinyLLM 具備了**"知道就說知道，不知道就說不知道"**的能力，這是構建可信賴AI系統的重要基礎。

**核心價值:**
- ✅ **可靠性** - 減少錯誤信息
- ✅ **透明性** - 用戶了解可信度
- ✅ **安全性** - 避免誤導和傷害
- ✅ **可控性** - 靈活調整行為

**適用場景:**
- 問答系統
- 事實陳述
- 專業諮詢
- 教育輔導
- 決策支持

**使用建議:**
- 按需啟用，平衡性能和可靠性
- 根據任務調整閾值
- 重要輸出使用自我一致性驗證
- 提供診斷信息輔助人工審核

通過這些功能，TinyLLM 成為一個更加誠實、可靠的語言模型！
