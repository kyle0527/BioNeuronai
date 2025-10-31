# 🎓 安全檢測模組訓練指南

## 📋 概述

本指南將幫助您訓練和優化生產級安全檢測模組，包括 SQL 注入、IDOR 和認證漏洞檢測。

## 🎯 訓練目標

1. **提高檢測準確率** - 減少誤報和漏報
2. **優化檢測策略** - 調整 payload 和閾值
3. **增強適應性** - 針對不同應用類型優化
4. **性能優化** - 減少檢測時間和資源消耗

---

## 🔬 訓練方法

### 方法一：基於真實數據的監督學習

#### 1. 準備訓練數據集

```python
# training_data_collection.py
import asyncio
import httpx
from src.bioneuronai.security import (
    EnhancedAuthModule,
    ProductionIDORModule,
    ProductionSQLiModule,
)

# 收集已知漏洞的樣本
known_vulnerabilities = [
    {
        "url": "http://testphp.vulnweb.com/artists.php",
        "parameter": "artist",
        "vulnerability_type": "sqli",
        "is_vulnerable": True
    },
    {
        "url": "http://demo.testfire.net/bank/login.jsp",
        "parameter": "username",
        "vulnerability_type": "auth",
        "is_vulnerable": True
    },
    # ... 更多樣本
]

# 收集正常（無漏洞）的樣本
normal_samples = [
    {
        "url": "https://www.google.com/search",
        "parameter": "q",
        "vulnerability_type": "sqli",
        "is_vulnerable": False
    },
    # ... 更多樣本
]
```

#### 2. 執行檢測並記錄結果

```python
# training_executor.py
import json
from datetime import datetime

async def collect_training_data():
    """收集訓練數據"""
    results = []
    
    async with httpx.AsyncClient() as client:
        sqli_module = ProductionSQLiModule()
        
        for sample in known_vulnerabilities + normal_samples:
            # 構建任務對象
            task = create_task_from_sample(sample)
            
            # 執行檢測
            start_time = datetime.now()
            findings = await sqli_module.execute_detection(task, client)
            detection_time = (datetime.now() - start_time).total_seconds()
            
            # 記錄結果
            result = {
                "sample": sample,
                "detected": len(findings) > 0,
                "confidence": findings[0].vulnerability.confidence if findings else None,
                "detection_time": detection_time,
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            
            print(f"✓ 測試完成: {sample['url']}")
    
    # 保存訓練數據
    with open("training_results.json", "w") as f:
        json.dump(results, indent=2)
    
    return results

# 執行數據收集
asyncio.run(collect_training_data())
```

#### 3. 分析檢測結果

```python
# analysis.py
import json
import pandas as pd

def analyze_detection_accuracy():
    """分析檢測準確率"""
    with open("training_results.json") as f:
        results = json.load(f)
    
    df = pd.DataFrame(results)
    
    # 計算混淆矩陣
    true_positives = len(df[(df['sample.is_vulnerable'] == True) & (df['detected'] == True)])
    false_positives = len(df[(df['sample.is_vulnerable'] == False) & (df['detected'] == True)])
    true_negatives = len(df[(df['sample.is_vulnerable'] == False) & (df['detected'] == False)])
    false_negatives = len(df[(df['sample.is_vulnerable'] == True) & (df['detected'] == False)])
    
    # 計算指標
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"🎯 檢測準確率分析:")
    print(f"   Precision (精確率): {precision:.2%}")
    print(f"   Recall (召回率): {recall:.2%}")
    print(f"   F1 Score: {f1_score:.2%}")
    print(f"\n📊 混淆矩陣:")
    print(f"   TP: {true_positives}, FP: {false_positives}")
    print(f"   TN: {true_negatives}, FN: {false_negatives}")
    
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "confusion_matrix": {
            "tp": true_positives,
            "fp": false_positives,
            "tn": true_negatives,
            "fn": false_negatives
        }
    }
```

---

### 方法二：參數優化（超參數調優）

#### 1. 定義可調整的參數

```python
# hyperparameter_tuning.py
from dataclasses import dataclass
from typing import List

@dataclass
class SQLiModuleConfig:
    """SQLi 模組可調參數"""
    max_column_count: int = 10          # 最大列數檢測
    time_delay_threshold: float = 3.0   # 時間延遲閾值（秒）
    similarity_threshold: float = 0.8   # 響應相似度閾值
    max_payloads_per_type: int = 5      # 每種類型的最大 payload 數量
    request_timeout: float = 15.0       # 請求超時時間
    
@dataclass
class IDORModuleConfig:
    """IDOR 模組可調參數"""
    max_test_ids: int = 10              # 最大測試 ID 數量
    length_diff_threshold: int = 100    # 響應長度差異閾值
    enable_admin_path_test: bool = True # 是否啟用管理員路徑測試
    
@dataclass
class AuthModuleConfig:
    """認證模組可調參數"""
    max_credentials: int = 15           # 最大憑證測試數量
    success_indicators_count: int = 5   # 成功指標數量
    enable_csrf_detection: bool = True  # 是否啟用 CSRF 檢測
```

#### 2. 使用網格搜索優化參數

```python
# grid_search.py
import asyncio
from itertools import product

async def grid_search_optimization():
    """網格搜索最佳參數組合"""
    
    # 定義參數搜索空間
    param_grid = {
        "time_delay_threshold": [2.0, 3.0, 5.0],
        "similarity_threshold": [0.7, 0.8, 0.9],
        "max_payloads_per_type": [3, 5, 10]
    }
    
    best_score = 0
    best_params = None
    
    # 生成所有參數組合
    param_combinations = list(product(*param_grid.values()))
    
    for params in param_combinations:
        config = dict(zip(param_grid.keys(), params))
        
        # 使用當前參數配置運行測試
        score = await evaluate_configuration(config)
        
        print(f"📊 測試配置: {config}")
        print(f"   F1 Score: {score:.3f}")
        
        if score > best_score:
            best_score = score
            best_params = config
    
    print(f"\n🏆 最佳配置:")
    print(f"   參數: {best_params}")
    print(f"   F1 Score: {best_score:.3f}")
    
    return best_params, best_score

async def evaluate_configuration(config):
    """評估特定配置的性能"""
    # 使用配置創建模組
    # 運行測試數據集
    # 計算 F1 score
    # ... (實現細節)
    pass
```

---

### 方法三：基於反饋的強化學習

#### 1. 收集用戶反饋

```python
# feedback_collection.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DetectionFeedback:
    """檢測結果反饋"""
    finding_id: str
    url: str
    parameter: str
    detected_vulnerability: str
    is_true_positive: bool          # 用戶確認是否為真陽性
    false_positive_reason: str | None  # 如果是誤報，原因是什麼
    timestamp: datetime
    
class FeedbackCollector:
    """反饋收集器"""
    
    def __init__(self):
        self.feedbacks: List[DetectionFeedback] = []
    
    def add_feedback(self, feedback: DetectionFeedback):
        """添加反饋"""
        self.feedbacks.append(feedback)
        self._update_detection_rules(feedback)
    
    def _update_detection_rules(self, feedback: DetectionFeedback):
        """根據反饋更新檢測規則"""
        if not feedback.is_true_positive:
            # 如果是誤報，調整檢測邏輯
            if "response_length" in feedback.false_positive_reason:
                # 提高響應長度差異閾值
                pass
            elif "time_based" in feedback.false_positive_reason:
                # 調整時間檢測閾值
                pass
```

#### 2. 實現自適應學習

```python
# adaptive_learning.py
import numpy as np

class AdaptiveDetectionEngine:
    """自適應檢測引擎"""
    
    def __init__(self):
        self.payload_success_rate = {}  # 記錄每個 payload 的成功率
        self.confidence_history = []     # 置信度歷史
        
    def update_payload_performance(self, payload: str, is_successful: bool):
        """更新 payload 性能統計"""
        if payload not in self.payload_success_rate:
            self.payload_success_rate[payload] = {
                "attempts": 0,
                "successes": 0
            }
        
        self.payload_success_rate[payload]["attempts"] += 1
        if is_successful:
            self.payload_success_rate[payload]["successes"] += 1
    
    def get_best_payloads(self, top_k: int = 5) -> List[str]:
        """獲取效果最好的 top-k payloads"""
        ranked_payloads = sorted(
            self.payload_success_rate.items(),
            key=lambda x: x[1]["successes"] / max(1, x[1]["attempts"]),
            reverse=True
        )
        return [p[0] for p in ranked_payloads[:top_k]]
    
    def adjust_confidence_threshold(self):
        """動態調整置信度閾值"""
        if len(self.confidence_history) < 10:
            return 0.7  # 默認閾值
        
        # 基於歷史表現調整閾值
        recent_avg = np.mean(self.confidence_history[-50:])
        if recent_avg > 0.8:
            return 0.75  # 提高閾值，減少誤報
        elif recent_avg < 0.6:
            return 0.65  # 降低閾值，增加召回率
        return 0.7
```

---

### 方法四：遷移學習（使用 BioNeuron）

#### 1. 將檢測特徵轉換為神經網絡輸入

```python
# bio_neuron_integration.py
from src.bioneuronai.improved_core import ImprovedBioNeuron
import numpy as np

class NeuralDetectionAdapter:
    """將檢測特徵適配到 BioNeuron"""
    
    def __init__(self):
        # 創建多個神經元，每個負責不同的檢測維度
        self.response_length_neuron = ImprovedBioNeuron(
            num_inputs=3,  # [baseline_length, test_length, diff_ratio]
            threshold=0.7,
            learning_rate=0.01
        )
        
        self.time_anomaly_neuron = ImprovedBioNeuron(
            num_inputs=3,  # [baseline_time, test_time, delay_ratio]
            threshold=0.75,
            learning_rate=0.01
        )
        
        self.content_similarity_neuron = ImprovedBioNeuron(
            num_inputs=4,  # [similarity, keyword_diff, structure_diff, error_count]
            threshold=0.8,
            learning_rate=0.01
        )
    
    def extract_features(self, baseline_response, test_response):
        """從響應中提取特徵"""
        # 長度特徵
        baseline_len = len(baseline_response.text)
        test_len = len(test_response.text)
        len_diff_ratio = abs(test_len - baseline_len) / max(baseline_len, 1)
        length_features = [
            baseline_len / 10000,  # 歸一化
            test_len / 10000,
            min(len_diff_ratio, 1.0)
        ]
        
        # 時間特徵
        baseline_time = baseline_response.elapsed.total_seconds()
        test_time = test_response.elapsed.total_seconds()
        time_diff_ratio = abs(test_time - baseline_time) / max(baseline_time, 0.1)
        time_features = [
            min(baseline_time / 10, 1.0),
            min(test_time / 10, 1.0),
            min(time_diff_ratio, 1.0)
        ]
        
        # 內容特徵
        similarity = self._calculate_similarity(baseline_response.text, test_response.text)
        keyword_diff = self._count_keyword_differences(baseline_response.text, test_response.text)
        error_count = self._count_error_indicators(test_response.text)
        content_features = [
            similarity,
            min(keyword_diff / 10, 1.0),
            0.5,  # structure_diff (簡化)
            min(error_count / 5, 1.0)
        ]
        
        return {
            "length": length_features,
            "time": time_features,
            "content": content_features
        }
    
    def predict_vulnerability(self, baseline_response, test_response):
        """使用神經網絡預測是否存在漏洞"""
        features = self.extract_features(baseline_response, test_response)
        
        # 每個神經元獨立判斷
        length_signal = self.response_length_neuron.forward(features["length"])
        time_signal = self.time_anomaly_neuron.forward(features["time"])
        content_signal = self.content_similarity_neuron.forward(features["content"])
        
        # 綜合判斷
        combined_score = (length_signal + time_signal + content_signal) / 3.0
        is_vulnerable = combined_score > 0.6
        
        return is_vulnerable, combined_score
    
    def train(self, baseline_response, test_response, is_vulnerable: bool):
        """訓練神經網絡"""
        features = self.extract_features(baseline_response, test_response)
        
        # 使用真實標籤進行 Hebbian 學習
        target_output = 1.0 if is_vulnerable else 0.0
        
        self.response_length_neuron.hebbian_learn(features["length"], target_output)
        self.time_anomaly_neuron.hebbian_learn(features["time"], target_output)
        self.content_similarity_neuron.hebbian_learn(features["content"], target_output)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """計算文本相似度"""
        # 簡化實現
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    
    def _count_keyword_differences(self, text1: str, text2: str) -> int:
        """統計關鍵字差異數量"""
        keywords1 = set(word for word in text1.lower().split() if len(word) > 3)
        keywords2 = set(word for word in text2.lower().split() if len(word) > 3)
        return len(keywords1.symmetric_difference(keywords2))
    
    def _count_error_indicators(self, text: str) -> int:
        """統計錯誤指標數量"""
        error_patterns = [
            "error", "exception", "warning", "mysql", "oracle", 
            "syntax", "unexpected", "failed"
        ]
        return sum(1 for pattern in error_patterns if pattern in text.lower())
```

#### 2. 訓練循環

```python
# training_loop.py
async def train_neural_detector():
    """訓練神經檢測器"""
    adapter = NeuralDetectionAdapter()
    
    async with httpx.AsyncClient() as client:
        # 訓練階段
        for epoch in range(10):
            print(f"\n🔄 Epoch {epoch + 1}/10")
            
            for sample in training_samples:
                # 獲取響應
                baseline = await client.get(sample["url"])
                test_url = f"{sample['url']}?{sample['parameter']}={sample['payload']}"
                test_response = await client.get(test_url)
                
                # 訓練
                adapter.train(
                    baseline, 
                    test_response, 
                    is_vulnerable=sample["is_vulnerable"]
                )
            
            # 驗證
            accuracy = await validate_detector(adapter, validation_samples)
            print(f"   驗證準確率: {accuracy:.2%}")
        
        # 保存模型
        save_detector_model(adapter)

async def validate_detector(adapter, validation_samples):
    """驗證檢測器性能"""
    correct = 0
    total = len(validation_samples)
    
    async with httpx.AsyncClient() as client:
        for sample in validation_samples:
            baseline = await client.get(sample["url"])
            test_url = f"{sample['url']}?{sample['parameter']}={sample['payload']}"
            test_response = await client.get(test_url)
            
            is_vulnerable, confidence = adapter.predict_vulnerability(baseline, test_response)
            
            if is_vulnerable == sample["is_vulnerable"]:
                correct += 1
    
    return correct / total
```

---

## 📊 訓練數據來源

### 1. 公開漏洞測試平台
```python
TRAINING_SOURCES = {
    "sqli": [
        "http://testphp.vulnweb.com/",
        "http://demo.testfire.net/",
        "https://portswigger.net/web-security/sql-injection",
    ],
    "idor": [
        "https://owasp.org/www-project-webgoat/",
        "https://github.com/WebGoat/WebGoat",
    ],
    "auth": [
        "http://demo.testfire.net/login.jsp",
        "https://juice-shop.herokuapp.com/",
    ]
}
```

### 2. 創建自己的測試環境
```bash
# 使用 Docker 建立測試環境
docker pull vulnerables/web-dvwa
docker run -d -p 80:80 vulnerables/web-dvwa

docker pull bkimminich/juice-shop
docker run -d -p 3000:3000 bkimminich/juice-shop
```

---

## 🎯 訓練最佳實踐

### 1. 數據平衡
- 確保有漏洞樣本和無漏洞樣本的比例平衡（建議 1:1 或 1:2）
- 包含不同類型的應用（Web、API、Mobile Backend）

### 2. 迭代訓練
```python
# 每週執行一次訓練循環
def weekly_training_cycle():
    # 1. 收集上週的檢測反饋
    feedbacks = load_weekly_feedbacks()
    
    # 2. 更新訓練數據集
    update_training_dataset(feedbacks)
    
    # 3. 重新訓練模型
    new_model = train_detector()
    
    # 4. A/B 測試
    if new_model.performance > current_model.performance:
        deploy_model(new_model)
```

### 3. 監控和評估
```python
# 持續監控指標
METRICS_TO_TRACK = [
    "precision",         # 精確率
    "recall",            # 召回率
    "f1_score",          # F1 分數
    "detection_time",    # 檢測時間
    "false_positive_rate",  # 誤報率
    "false_negative_rate",  # 漏報率
]
```

---

## 🚀 開始訓練

### 快速開始腳本
```python
# quick_start_training.py
import asyncio
from training_executor import collect_training_data
from analysis import analyze_detection_accuracy
from adaptive_learning import AdaptiveDetectionEngine

async def main():
    print("🎓 開始訓練安全檢測模組...")
    
    # 步驟 1: 收集訓練數據
    print("\n📊 步驟 1: 收集訓練數據")
    results = await collect_training_data()
    print(f"   收集了 {len(results)} 個樣本")
    
    # 步驟 2: 分析準確率
    print("\n📈 步驟 2: 分析檢測準確率")
    metrics = analyze_detection_accuracy()
    
    # 步驟 3: 優化參數
    print("\n⚙️  步驟 3: 優化檢測參數")
    best_params = await grid_search_optimization()
    
    # 步驟 4: 訓練神經檢測器
    print("\n🧠 步驟 4: 訓練神經檢測器")
    await train_neural_detector()
    
    print("\n✅ 訓練完成！")
    print(f"   最終 F1 Score: {metrics['f1_score']:.2%}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 進階主題

1. **集成學習** - 結合多個檢測模型的結果
2. **主動學習** - 主動選擇最有價值的樣本進行標註
3. **遷移學習** - 利用已訓練的模型快速適應新場景
4. **對抗訓練** - 訓練對抗 WAF 和防護機制的檢測能力

---

## 🔗 相關資源

- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- Scikit-learn 文檔: https://scikit-learn.org/
- PyTorch 教程: https://pytorch.org/tutorials/