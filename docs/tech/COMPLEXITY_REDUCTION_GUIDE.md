# 程式碼複雜度降低指南 (Code Complexity Reduction Guide)

## 📑 目錄

1. 指南概述
2. 什麼是複雜度
3. 如何發現複雜度問題
4. 複雜度度量標準
5. 重構技術
6. 實施步驟
7. 改善目標範例
8. 程式碼複雜度規範
9. 最佳實踐
10. 工具與驗證
11. 附錄: 快速參考
12. 結語

---

## 指南概述

本指南提供系統性的方法來識別、測量和降低程式碼複雜度。適用於任何 Python 專案，旨在提高程式碼的可讀性、可維護性和可測試性。

### 核心原則
- **Code is Read More Often Than Written** - Guido van Rossum
- **Readability Counts** - PEP 20 (The Zen of Python)
- **Code Smell 是深層問題的表面徵兆** - Martin Fowler

---

## 什麼是複雜度

### 認知複雜度 (Cognitive Complexity)
衡量程式碼對人類理解的難度，考慮：
- 嵌套層次 (Nesting Levels)
- 控制流結構 (Control Flow Structures)
- 邏輯分支數量 (Logical Branches)

### 循環複雜度 (Cyclomatic Complexity)
衡量程式碼中獨立路徑的數量：
- 每個 `if`, `for`, `while`, `and`, `or`, `except` 增加 1
- 函數基礎複雜度為 1

### 常見的複雜度來源
1. **長函數 (Long Method)** - 超過 50 行
2. **深層嵌套 (Deep Nesting)** - 超過 3 層
3. **多重職責 (Multiple Responsibilities)** - 函數做太多事
4. **複雜條件 (Complex Conditionals)** - 多重 `and`/`or` 組合
5. **重複程式碼 (Duplicated Code)** - 相同邏輯出現多次

---

## 如何發現複雜度問題

### 自動化檢測工具

#### 1. **Pylint** - 全面的靜態分析
```bash
pylint your_module.py --disable=all --enable=too-many-branches,too-many-statements
```

關鍵檢查項目：
- `R0912`: Too many branches
- `R0914`: Too many local variables
- `R0915`: Too many statements
- `R0911`: Too many return statements

#### 2. **Flake8 + McCabe** - 循環複雜度
```bash
flake8 your_module.py --max-complexity=15
```

#### 3. **Radon** - 複雜度度量專家
```bash
# 循環複雜度
radon cc your_module.py -s

# 可維護性指數
radon mi your_module.py

# 原始度量 (行數、註釋等)
radon raw your_module.py
```

#### 4. **Cognitive-Complexity** - 認知複雜度
```bash
pip install cognitive-complexity
cognitive-complexity your_module.py
```

### 手動識別技巧

#### A. **視覺檢查法**
觀察以下徵兆：
- 函數長度超過一屏 (> 50 行)
- 嵌套層次超過 3 層
- 參數數量超過 5 個
- 需要水平滾動才能看完單行

#### B. **理解時間測試**
- 如果需要超過 1 分鐘才能理解函數功能 → **複雜度過高**
- 如果需要紙筆繪製流程圖才能理解 → **需要重構**

#### C. **修改困難度**
- 修改一個功能需要改動 3 個以上位置 → **耦合度過高**
- 不敢輕易修改程式碼怕影響其他功能 → **缺乏模組化**

---

## 複雜度度量標準

### Radon 複雜度評級

| 等級 | 複雜度範圍 | 風險評估 | 建議動作 |
|------|-----------|---------|---------|
| **A** | 1-5 | 簡單，低風險 | 維持現狀 |
| **B** | 6-10 | 稍微複雜 | 可接受 |
| **C** | 11-20 | 中等複雜 | 考慮重構 |
| **D** | 21-30 | 較複雜 | 應該重構 |
| **E** | 31-40 | 非常複雜 | **必須重構** |
| **F** | 41+ | 極度複雜 | **緊急重構** |

### 建議閾值

| 度量項目 | 最佳實踐 | 可接受上限 | 警戒線 |
|---------|---------|-----------|-------|
| **函數複雜度** | ≤ 10 | 15 | 20 |
| **函數行數** | ≤ 30 | 50 | 100 |
| **嵌套層次** | ≤ 2 | 3 | 4 |
| **參數數量** | ≤ 3 | 5 | 7 |
| **類別方法數** | ≤ 10 | 20 | 30 |
| **模組行數** | ≤ 500 | 1000 | 2000 |

### PEP 8 編碼標準

| 項目 | 限制 | 說明 |
|------|------|------|
| **每行最大字元** | 79 | 程式碼行 |
| **註釋/文檔字串** | 72 | 可讀性優先 |
| **縮排** | 4 空格 | 不使用 Tab |
| **空行** | 頂層函數/類別間 2 行 | 方法間 1 行 |

---

## 重構技術

### 1. Extract Method (提取方法)

**問題**: 函數過長，混合多種職責

**解決方案**: 將邏輯區塊提取為獨立函數

#### Before (複雜度: 25)
```python
def process_data(data):
    # 資料驗證 (20 行)
    if not data:
        raise ValueError("Empty data")
    if not isinstance(data, list):
        raise TypeError("Expected list")
    # ... 更多驗證

    # 資料轉換 (30 行)
    cleaned = []
    for item in data:
        if item.strip():
            cleaned.append(item.lower())
    # ... 更多轉換

    # 資料分析 (40 行)
    results = {}
    for item in cleaned:
        # ... 複雜統計邏輯

    # 結果格式化 (30 行)
    formatted = []
    for key, value in results.items():
        # ... 格式化邏輯

    return formatted
```

#### After (複雜度: 每個函數 ≤ 5)
```python
def process_data(data):
    """主要處理流程，職責清晰"""
    validated_data = validate_data(data)
    cleaned_data = clean_data(validated_data)
    analyzed_results = analyze_data(cleaned_data)
    formatted_output = format_results(analyzed_results)
    return formatted_output

def validate_data(data: list) -> list:
    """單一職責: 驗證輸入資料"""
    if not data:
        raise ValueError("Empty data")
    if not isinstance(data, list):
        raise TypeError("Expected list")
    return data

def clean_data(data: list) -> list:
    """單一職責: 清理和標準化資料"""
    return [item.lower() for item in data if item.strip()]

def analyze_data(data: list) -> dict:
    """單一職責: 資料分析"""
    return {item: len(item) for item in data}

def format_results(results: dict) -> list:
    """單一職責: 格式化輸出"""
    return [f"{k}: {v}" for k, v in results.items()]
```

**效益**:
- 原函數複雜度: 25 → 主函數: 2
- 每個子函數複雜度: ≤ 5
- 可測試性提升 400%
- 可讀性大幅提升

---

### 2. Decompose Conditional (分解條件式)

**問題**: 複雜的條件邏輯難以理解

#### Before (複雜度: 15)
```python
def calculate_discount(customer, order):
    if (customer.is_premium and order.total > 1000 and 
        customer.years_active >= 5 and not customer.has_outstanding_debt and
        order.items_count > 10 and customer.loyalty_points > 500):
        return order.total * 0.25
    elif (customer.is_regular and order.total > 500 and
          customer.years_active >= 2):
        return order.total * 0.15
    elif order.total > 100:
        return order.total * 0.05
    return 0
```

#### After (複雜度: 每個函數 ≤ 5)
```python
def calculate_discount(customer, order):
    """清晰的折扣計算邏輯"""
    if is_premium_discount_eligible(customer, order):
        return order.total * 0.25
    elif is_regular_discount_eligible(customer, order):
        return order.total * 0.15
    elif is_basic_discount_eligible(order):
        return order.total * 0.05
    return 0

def is_premium_discount_eligible(customer, order) -> bool:
    """高級會員資格檢查"""
    return (
        customer.is_premium and
        order.total > 1000 and
        customer.years_active >= 5 and
        not customer.has_outstanding_debt and
        order.items_count > 10 and
        customer.loyalty_points > 500
    )

def is_regular_discount_eligible(customer, order) -> bool:
    """一般會員資格檢查"""
    return (
        customer.is_regular and
        order.total > 500 and
        customer.years_active >= 2
    )

def is_basic_discount_eligible(order) -> bool:
    """基本折扣資格檢查"""
    return order.total > 100
```

**效益**:
- 條件邏輯語義化，一目了然
- 可獨立測試每個條件
- 易於調整折扣規則

---

### 3. Replace Nested Conditional with Guard Clauses (保護子句)

**問題**: 深層嵌套降低可讀性

#### Before (嵌套: 4 層)
```python
def process_payment(payment):
    if payment is not None:
        if payment.is_valid():
            if payment.amount > 0:
                if payment.account.has_sufficient_balance():
                    return payment.execute()
                else:
                    raise InsufficientFundsError()
            else:
                raise InvalidAmountError()
        else:
            raise InvalidPaymentError()
    else:
        raise NullPaymentError()
```

#### After (嵌套: 0 層)
```python
def process_payment(payment):
    """使用早期返回降低嵌套"""
    # Guard clauses: 快速失敗
    if payment is None:
        raise NullPaymentError()

    if not payment.is_valid():
        raise InvalidPaymentError()

    if payment.amount <= 0:
        raise InvalidAmountError()

    if not payment.account.has_sufficient_balance():
        raise InsufficientFundsError()

    # 正常流程
    return payment.execute()
```

**效益**:
- 嵌套層次: 4 → 0
- 正常流程與異常處理分離
- 閱讀順序更自然

---

### 4. Extract Class (提取類別)

**問題**: 一個類別承擔過多職責

#### Before (類別複雜度: 高)
```python
class UserManager:
    """上帝類別 - 做所有事情"""

    def create_user(self, data): ...
    def update_user(self, user_id, data): ...
    def delete_user(self, user_id): ...

    def send_welcome_email(self, user): ...
    def send_password_reset(self, user): ...

    def validate_email(self, email): ...
    def validate_password(self, password): ...

    def log_user_activity(self, user, action): ...
    def generate_activity_report(self, user): ...

    def calculate_user_score(self, user): ...
    def update_user_ranking(self, user): ...
```

#### After (單一職責原則)
```python
class UserRepository:
    """職責: 資料持久化"""
    def create(self, user): ...
    def update(self, user_id, data): ...
    def delete(self, user_id): ...
    def find_by_id(self, user_id): ...

class UserNotificationService:
    """職責: 通知管理"""
    def send_welcome_email(self, user): ...
    def send_password_reset(self, user): ...

class UserValidator:
    """職責: 資料驗證"""
    def validate_email(self, email) -> bool: ...
    def validate_password(self, password) -> bool: ...

class UserActivityTracker:
    """職責: 活動追蹤"""
    def log_activity(self, user, action): ...
    def generate_report(self, user): ...

class UserScoreCalculator:
    """職責: 分數計算"""
    def calculate_score(self, user) -> int: ...
    def update_ranking(self, user): ...
```

**效益**:
- 每個類別職責單一
- 模組化程度高
- 易於測試和維護

---

### 5. Replace Magic Numbers with Named Constants (命名常數)

**問題**: 魔術數字降低可讀性

#### Before
```python
def calculate_fee(amount):
    if amount > 1000:
        return amount * 0.05
    elif amount > 500:
        return amount * 0.08
    else:
        return amount * 0.10 + 5
```

#### After
```python
# 常數定義 (通常在模組頂部)
LARGE_TRANSACTION_THRESHOLD = 1000
MEDIUM_TRANSACTION_THRESHOLD = 500
LARGE_TRANSACTION_FEE_RATE = 0.05
MEDIUM_TRANSACTION_FEE_RATE = 0.08
SMALL_TRANSACTION_FEE_RATE = 0.10
SMALL_TRANSACTION_BASE_FEE = 5

def calculate_fee(amount: float) -> float:
    """計算交易手續費"""
    if amount > LARGE_TRANSACTION_THRESHOLD:
        return amount * LARGE_TRANSACTION_FEE_RATE
    elif amount > MEDIUM_TRANSACTION_THRESHOLD:
        return amount * MEDIUM_TRANSACTION_FEE_RATE
    else:
        return amount * SMALL_TRANSACTION_FEE_RATE + SMALL_TRANSACTION_BASE_FEE
```

---

### 6. Introduce Parameter Object (參數物件)

**問題**: 函數參數過多

#### Before (參數數量: 8)
```python
def create_report(user_id, start_date, end_date, format, 
                  include_charts, include_summary, 
                  sort_by, filter_by):
    ...
```

#### After (參數數量: 1)
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ReportConfig:
    """報表配置參數物件"""
    user_id: int
    start_date: datetime
    end_date: datetime
    format: str = 'pdf'
    include_charts: bool = True
    include_summary: bool = True
    sort_by: str = 'date'
    filter_by: Optional[str] = None

def create_report(config: ReportConfig):
    """使用配置物件簡化參數傳遞"""
    ...

# 使用範例
config = ReportConfig(
    user_id=123,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    format='xlsx'
)
create_report(config)
```

---

### 7. Replace Loop with Comprehension (列表推導式)

**問題**: 傳統迴圈冗長

#### Before (複雜度: 8)
```python
def process_items(items):
    result = []
    for item in items:
        if item.is_valid():
            processed = item.transform()
            if processed.value > 10:
                result.append(processed)
    return result
```

#### After (複雜度: 3)
```python
def process_items(items):
    """使用列表推導式簡化"""
    return [
        item.transform()
        for item in items
        if item.is_valid() and item.transform().value > 10
    ]

# 或者分步驟更清晰
def process_items(items):
    valid_items = (item for item in items if item.is_valid())
    transformed = (item.transform() for item in valid_items)
    return [item for item in transformed if item.value > 10]
```

---

## 實施步驟

### Phase 1: 評估現狀

#### Step 1: 執行自動化分析
```bash
# 生成複雜度報告
radon cc . -s -a --total-average > complexity_report.txt

# 找出最複雜的 20 個函數
radon cc . -s --min C | head -n 50
```

#### Step 2: 建立優先級清單
按以下標準排序：
1. **複雜度 > 30** - 最高優先
2. **複雜度 20-30** - 高優先
3. **複雜度 15-20** - 中優先
4. **頻繁修改的模組** - 提升優先級

#### Step 3: 設定改善目標
```markdown
## 改善目標範例

| 度量 | 當前 | 目標 (1個月) | 目標 (3個月) |
|------|------|-------------|-------------|
| 平均複雜度 | 18.5 | 12.0 | 8.0 |
| F級函數 | 12 | 0 | 0 |
| E級函數 | 35 | 10 | 0 |
| D級函數 | 68 | 30 | 15 |
```

---

### Phase 2: 執行重構

#### 重構流程圖
```
1. 選擇目標函數
   ↓
2. 確保有測試覆蓋
   ↓ (如果沒有)
   2.1 編寫測試
   ↓
3. 識別複雜度來源
   ↓
4. 選擇重構技術
   ↓
5. 小步重構
   ↓
6. 執行測試驗證
   ↓
7. 測量改善效果
   ↓
8. 提交變更
```

#### 重構檢查清單
- [ ] 原有測試全部通過
- [ ] 新增測試覆蓋邊界情況
- [ ] 複雜度降低至目標範圍
- [ ] 文檔已更新
- [ ] 程式碼審查通過
- [ ] 無新增警告或錯誤

---

### Phase 3: 預防複雜度累積

#### 建立 Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: complexity-check
        name: Check Code Complexity
        entry: bash -c 'radon cc . --min C && exit 1 || exit 0'
        language: system
        pass_filenames: false
```

#### CI/CD 整合
```yaml
# .github/workflows/code-quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  complexity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Radon
        run: pip install radon
      - name: Check Complexity
        run: |
          radon cc . --min C --total-average
          if [ $? -ne 0 ]; then
            echo "❌ 發現複雜度過高的函數"
            exit 1
          fi
```

#### 團隊規範
```markdown
## 程式碼複雜度規範

### 提交前檢查
- 新增函數複雜度 ≤ 10
- 修改現有函數不增加複雜度
- 必須提供單元測試

### Code Review 重點
- 函數職責是否單一
- 命名是否清晰
- 是否有改善空間

### 定期審查
- 每週: 檢查新增程式碼
- 每月: 審查複雜度趨勢
- 每季: 重構技術債
```

---

## 最佳實踐

### 1. Single Responsibility Principle (單一職責)
```python
# ❌ 違反 SRP
class User:
    def save_to_database(self): ...
    def send_email(self): ...
    def generate_report(self): ...

# ✅ 遵循 SRP
class User:
    """職責: 使用者資料模型"""
    pass

class UserRepository:
    """職責: 資料持久化"""
    def save(self, user): ...

class UserEmailService:
    """職責: 郵件發送"""
    def send_welcome_email(self, user): ...
```

### 2. Early Return Pattern (早期返回)
```python
# ❌ 深層嵌套
def process(data):
    if data:
        if data.is_valid:
            if data.has_permission:
                return data.execute()
    return None

# ✅ 早期返回
def process(data):
    if not data:
        return None
    if not data.is_valid:
        return None
    if not data.has_permission:
        return None
    return data.execute()
```

### 3. Descriptive Naming (描述性命名)
```python
# ❌ 模糊命名
def proc(d, f):
    r = []
    for i in d:
        if i > f:
            r.append(i * 2)
    return r

# ✅ 描述性命名
def double_values_above_threshold(values: list[float], 
                                   threshold: float) -> list[float]:
    """將超過閾值的數值加倍"""
    return [value * 2 for value in values if value > threshold]
```

### 4. Use Type Hints (類型提示)
```python
# ❌ 無類型資訊
def calculate(x, y, mode):
    if mode == 'sum':
        return x + y
    return x * y

# ✅ 清晰的類型資訊
from typing import Literal

def calculate(
    x: float, 
    y: float, 
    mode: Literal['sum', 'multiply']
) -> float:
    """計算兩數的和或積"""
    if mode == 'sum':
        return x + y
    return x * y
```

### 5. Avoid Deep Nesting (避免深層嵌套)

**建議嵌套層次**: ≤ 3 層

```python
# ❌ 5 層嵌套
def process():
    if condition1:
        if condition2:
            for item in items:
                if item.valid:
                    for sub in item.children:
                        ...  # 太深了！

# ✅ 重構為平面結構
def process():
    if not condition1 or not condition2:
        return

    valid_items = [item for item in items if item.valid]
    for item in valid_items:
        process_children(item.children)

def process_children(children):
    for child in children:
        ...
```

---

## 工具與驗證

### 推薦工具組合

#### 靜態分析工具
```bash
# 安裝工具套件
pip install pylint flake8 radon mccabe mypy black isort

# Pylint: 全面檢查
pylint your_module.py

# Flake8: 風格與複雜度
flake8 your_module.py --max-complexity=10

# Radon: 複雜度專家
radon cc your_module.py -a --total-average

# MyPy: 類型檢查
mypy your_module.py

# Black: 自動格式化
black your_module.py

# isort: 導入排序
isort your_module.py
```

#### IDE 整合

**VS Code 設定** (`settings.json`)
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": ["--max-complexity=10"],
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.sortImports.args": ["--profile", "black"]
}
```

#### 持續監控

**生成趨勢報告**
```bash
# 每週執行並記錄
date >> complexity_history.log
radon cc . --total-average >> complexity_history.log
echo "---" >> complexity_history.log
```

**可視化範例**
```python
import matplotlib.pyplot as plt

# 追蹤複雜度趨勢
weeks = [1, 2, 3, 4, 5, 6, 7, 8]
avg_complexity = [18.5, 17.2, 15.8, 14.1, 12.5, 10.8, 9.2, 8.0]

plt.plot(weeks, avg_complexity, marker='o')
plt.axhline(y=10, color='r', linestyle='--', label='目標')
plt.title('平均複雜度改善趨勢')
plt.xlabel('週數')
plt.ylabel('平均複雜度')
plt.legend()
plt.savefig('complexity_trend.png')
```

---

## 附錄: 快速參考

### 複雜度快速判斷

| 症狀 | 複雜度估計 | 建議動作 |
|------|-----------|---------|
| 函數 > 100 行 | > 30 | 立即重構 |
| 嵌套 > 4 層 | > 20 | 使用 Guard Clauses |
| 參數 > 5 個 | > 15 | Parameter Object |
| if/elif > 5 個 | > 15 | Strategy Pattern |
| 迴圈內嵌迴圈 | > 10 | Extract Method |

### 重構技術選擇

| 問題類型 | 推薦技術 | 複雜度降低 |
|---------|---------|-----------|
| 長函數 | Extract Method | 50-70% |
| 複雜條件 | Decompose Conditional | 40-60% |
| 深層嵌套 | Guard Clauses | 60-80% |
| 多職責類別 | Extract Class | 50-70% |
| 重複程式碼 | Extract Method/Class | 30-50% |

### 常用命令速查

```bash
# 找出最複雜的 10 個函數
radon cc . -s --min E -n 10

# 計算模組維護性指數
radon mi . --show --sort

# 檢查所有檔案的複雜度並失敗如果超標
radon cc . --min D --total-average && echo "✅ 通過" || echo "❌ 失敗"

# 生成 JSON 格式報告
radon cc . -j > complexity.json

# 比較前後差異
radon cc your_module.py > before.txt
# (執行重構)
radon cc your_module.py > after.txt
diff before.txt after.txt
```

---

## 結語

程式碼複雜度管理是持續的過程，而非一次性任務。遵循本指南的原則和技術，可以：

- **提升可讀性** - 程式碼更易理解
- **降低維護成本** - 修改更安全、更快速
- **減少 Bug** - 簡單程式碼更不易出錯
- **提高開發效率** - 新功能開發更順暢

**記住**: *"任何笨蛋都能寫出電腦能理解的程式碼。優秀的程式設計師寫人類能理解的程式碼。"* - Martin Fowler

---

**文檔版本**: 2.1  
**最後更新**: 2024-12-14  
**適用範圍**: Python 3.8+  
**維護者**: AIVA Development Team
