# BioNeuronAI 合併衝突解決指南 (Merge Conflict Resolution Guide)

## 概述 (Overview)

本文檔提供系統性解決 BioNeuronAI 專案中 24 個待合併 Pull Request 的策略和流程。

This document provides a systematic strategy and process for resolving merge conflicts across 24 pending Pull Requests in the BioNeuronAI project.

## 優先順序策略 (Priority Strategy)

### 第一階段：高優先級 - 核心架構重構 (Phase 1: High Priority - Core Architecture)

**原理 (Rationale)**: 核心架構變更會影響所有其他功能，必須首先解決以建立穩定基礎。

1. **PR #25**: "Refactor BioNeuron architecture with strategy base class"
   - **預期衝突 (Expected Conflicts)**: `core.py`, `improved_core.py`, `__init__.py`
   - **解決策略 (Resolution Strategy)**: 
     - 統一神經元基礎類別
     - 採用策略模式重構
     - 保持向後兼容的 API

2. **PR #16**: "Introduce shared neuron base and align BioLayer API"
   - **預期衝突**: 神經元基類、層級 API
   - **解決策略**: 
     - 整合共享基類
     - 標準化層級接口
     - 遷移現有實現

3. **PR #8**: "Add parameterized LIF and STDP neuron types"
   - **預期衝突**: 神經元類型定義
   - **解決策略**:
     - 添加參數化神經元類型
     - 保持現有神經元功能
     - 擴展神經元工廠模式

### 第二階段：中優先級 - 功能模組整合 (Phase 2: Medium Priority - Feature Modules)

**原理**: 在穩定架構基礎上整合功能模組。

4. **PR #20**: "Introduce shared security package and tests"
5. **PR #14**: "Refactor security modules into dedicated package"
   - **預期衝突**: `enhanced_auth_module.py`, `production_idor_module.py`, `production_sqli_module.py`
   - **解決策略**:
     - 建立 `bioneuronai/security/` 套件
     - 整合所有安全模組
     - 統一安全測試框架

6. **PR #13**: "Improve vectorization and add concurrency safeguards"
   - **預期衝突**: 核心計算邏輯
   - **解決策略**:
     - 優化向量化運算
     - 添加線程安全機制
     - 性能基準測試

7. **PR #6**: "Add persistence support and online learning safeguards"
   - **預期衝突**: 神經元狀態管理
   - **解決策略**:
     - 實現序列化/反序列化
     - 添加在線學習保護
     - 版本兼容性處理

### 第三階段：CLI 和工具重構 (Phase 3: CLI and Tools)

8. **PR #19**: "Refactor CLI into Typer app and add Streamlit dashboard"
9. **PR #5**: "Add Typer-based CLI with dashboard streaming"
   - **預期衝突**: `cli.py`
   - **解決策略**:
     - 遷移到 Typer 框架
     - 整合 Streamlit 儀表板
     - 保持 CLI 向後兼容

10. **PR #15**: "Add configurable network builder and CLI config support"
    - **預期衝突**: 網路建構邏輯
    - **解決策略**:
      - 配置驅動的網路建構
      - YAML/JSON 配置支持
      - CLI 配置集成

### 第四階段：網路建構和配置 (Phase 4: Network Building)

11. **PR #24**: "Add configurable network builder and examples"
12. **PR #23**: "Refine improved neuron learning flow"
13. **PR #30**: "Improve network learning APIs and validation checks"
14. **PR #33**: "Refine BioNet serialization and persistence"
    - **解決策略**:
      - 統一網路建構 API
      - 完善學習流程
      - 強化驗證機制

### 第五階段：AI 功能和分析 (Phase 5: AI Features)

15. **PR #29**: "Refine novelty router tool matching and fallback"
16. **PR #22**: "Refine novelty analyzer feature space"
17. **PR #10**: "Add novelty-aware tool gating manager"
18. **PR #12**: "Add curiosity module and reinforcement learning demo"
19. **PR #21**: "Add curiosity-driven RL demo and batching support"
    - **預期衝突**: `common/response_novelty_analyzer.py`, 智能助手集成
    - **解決策略**:
      - 統一新穎性分析框架
      - 整合好奇心模組
      - RL 演示標準化

### 第六階段：文檔、發布和維護 (Phase 6: Documentation)

20-26. **文檔和工具 PRs**
    - **解決策略**:
      - 文檔更新應該最小衝突
      - 合併發布工具
      - 統一文檔結構

## 衝突解決流程 (Conflict Resolution Process)

### 1. 準備階段 (Preparation)

```bash
# 1. 確保本地 main 分支最新
git checkout main
git pull origin main

# 2. 為每個 PR 創建本地分支
git fetch origin pull/ID/head:pr-ID

# 3. 檢查衝突
git checkout pr-ID
git merge main --no-commit --no-ff
```

### 2. 分析衝突 (Analyze Conflicts)

```bash
# 查看所有衝突文件
git diff --name-only --diff-filter=U

# 查看衝突詳情
git diff --check
```

### 3. 解決策略 (Resolution Strategies)

#### 策略 A: 架構優先 (Architecture First)
- 當衝突涉及核心架構時，優先採用更現代/更完整的架構
- 保持 API 向後兼容性
- 遷移舊代碼到新架構

#### 策略 B: 功能合併 (Feature Merging)
- 當兩個 PR 添加不同功能時，保留雙方功能
- 重構以消除重複代碼
- 統一命名和風格

#### 策略 C: 文檔更新 (Documentation Updates)
- 合併所有文檔更新
- 確保一致性
- 移除過時信息

### 4. 測試驗證 (Testing)

```bash
# 安裝依賴
pip install -e .
pip install -r requirements-dev.txt

# 運行測試
pytest tests/ -v

# 檢查代碼風格
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# 類型檢查
mypy src/
```

### 5. 提交合併 (Commit Merge)

```bash
# 解決所有衝突後
git add .
git commit -m "Resolve conflicts: merge PR #ID into main"

# 推送到測試分支
git push origin pr-ID-resolved
```

## 常見衝突模式 (Common Conflict Patterns)

### 模式 1: 重複實現 (Duplicate Implementations)

**症狀**: `core.py` 和 `improved_core.py` 同時存在

**解決方案**:
- 評估兩個實現的優劣
- 整合優點到單一實現
- 提供遷移路徑

```python
# 舊代碼向新代碼的別名
from .improved_core import ImprovedBioNeuron as BioNeuron
```

### 模式 2: API 變更 (API Changes)

**症狀**: 函數簽名不同

**解決方案**:
- 使用可選參數保持向後兼容
- 提供適配器函數
- 添加棄用警告

```python
def forward(self, inputs, *, new_param=None):
    """
    Args:
        inputs: 輸入向量
        new_param: 新參數 (可選，用於新功能)
    """
    if new_param is not None:
        # 新邏輯
        pass
    # 舊邏輯
```

### 模式 3: 配置衝突 (Configuration Conflicts)

**症狀**: `pyproject.toml`, `requirements.txt` 衝突

**解決方案**:
- 合併所有依賴
- 統一版本要求
- 解決版本衝突

```toml
# 取較新但兼容的版本
dependencies = [
    "numpy>=1.21.0",  # 兩個 PR 都需要
    "fastapi>=0.110", # 合併版本需求
]
```

### 模式 4: 測試衝突 (Test Conflicts)

**症狀**: 測試文件衝突

**解決方案**:
- 保留所有測試
- 更新測試以匹配新 API
- 移除重複測試

## 自動化工具 (Automation Tools)

### 衝突檢測腳本 (Conflict Detection Script)

參見: `scripts/check_merge_conflicts.py`

### 批量合併助手 (Batch Merge Helper)

參見: `scripts/batch_merge_prs.py`

### 測試驗證流水線 (Test Validation Pipeline)

參見: `.github/workflows/merge-validation.yml`

## 檢查清單 (Checklist)

每個 PR 合併前的檢查：

- [ ] 所有衝突已解決
- [ ] 代碼通過所有測試
- [ ] 代碼風格符合規範
- [ ] 類型檢查通過
- [ ] 文檔已更新
- [ ] 向後兼容性已驗證
- [ ] 性能影響已評估
- [ ] 安全性已檢查

## 回滾計劃 (Rollback Plan)

如果合併後出現問題：

```bash
# 1. 立即回滾到合併前狀態
git revert <merge-commit-sha>

# 2. 創建修復分支
git checkout -b hotfix/pr-ID-issues

# 3. 修復問題後重新合併
```

## 聯絡資訊 (Contact)

如遇到複雜衝突，請：
1. 在 PR 中標記相關維護者
2. 在 Discord/Slack 討論
3. 必要時安排同步會議

## 參考資源 (References)

- [Git Merge Conflicts Documentation](https://git-scm.com/docs/git-merge)
- [Effective Merge Strategies](https://www.atlassian.com/git/tutorials/using-branches/merge-strategy)
- [Semantic Versioning](https://semver.org/)
