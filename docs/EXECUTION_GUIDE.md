# Step-by-Step Execution Guide

本指南提供執行 24 個 PR 合併的詳細步驟。
This guide provides detailed steps for executing the merge of all 24 PRs.

## 🚀 準備工作 (Prerequisites)

### 1. 環境檢查

```bash
# 確認 Git 版本
git --version  # 需要 >= 2.0

# 確認 Python 版本
python --version  # 需要 >= 3.8

# 確認在正確的目錄
cd /path/to/BioNeuronai
pwd

# 確認在 main 分支且是最新
git checkout main
git pull origin main

# 確認工作區乾淨
git status  # 應顯示 "nothing to commit, working tree clean"
```

### 2. 安裝依賴（如果需要運行測試）

```bash
pip install -e .
pip install pytest pytest-cov black isort flake8 mypy
```

### 3. 設置 GitHub 認證（可選但建議）

```bash
# 使用 GitHub CLI
gh auth login

# 或配置 Git 憑證
git config --global credential.helper store
```

## 📋 Phase 1: 核心架構 (Core Architecture)

**目標**: 合併 PRs #25, #16, #8  
**預計時間**: 2-4 小時  
**優先級**: 🔴 HIGH

### Step 1.1: 檢測衝突

```bash
# 檢查 Phase 1 的所有 PR
python scripts/check_merge_conflicts.py --phase 1 --report phase1_conflicts.md

# 查看報告
cat phase1_conflicts.md
```

**預期結果**:
- 報告列出所有衝突的文件
- 衝突類型分析（core/tests/config/docs）
- 每個 PR 的衝突摘要

### Step 1.2: 審查報告並制定策略

閱讀報告後，回答：
- [ ] 哪些文件有衝突？
- [ ] 衝突類型是什麼？
- [ ] 需要哪種解決策略？（參考快速參考指南）

### Step 1.3: 開始合併 PR #25

```bash
# 乾運行測試
python scripts/batch_merge_prs.py --pr-list 25 --dry-run

# 如果看起來可行，開始實際合併
python scripts/batch_merge_prs.py --pr-list 25 --interactive
```

**互動式流程**:

1. **如果沒有衝突** → 腳本自動合併 ✅
2. **如果有衝突** → 選擇選項:
   - 選項 1: 手動解決現在
   - 選項 2: 跳過此 PR
   - 選項 3: 中止

如果選擇選項 1（手動解決）:

```bash
# 衝突會顯示在這些文件中
git diff --name-only --diff-filter=U

# 手動編輯每個衝突文件
vim src/bioneuronai/core.py  # 或你喜歡的編輯器

# 在文件中找到衝突標記：
# <<<<<<< HEAD
# ... main branch code ...
# =======
# ... PR branch code ...
# >>>>>>> pr-25

# 解決衝突後，標記為已解決
git add src/bioneuronai/core.py

# 按 ENTER 繼續腳本
```

### Step 1.4: 驗證 PR #25 合併

```bash
# 運行測試
pytest tests/ -v

# 檢查代碼風格
black src/ tests/
isort src/ tests/
flake8 src/ tests/ --max-line-length=88

# 類型檢查
mypy src/ --ignore-missing-imports

# 運行範例
python examples/basic_demo.py
```

**檢查清單**:
- [ ] 所有測試通過
- [ ] 代碼風格正確
- [ ] 範例運行成功
- [ ] 無明顯錯誤或警告

### Step 1.5: 記錄解決過程

使用模板記錄 PR #25 的解決過程：

```bash
# 複製模板
cp docs/CONFLICT_RESOLUTION_LOG_TEMPLATE.md logs/PR_25_resolution.md

# 編輯並填寫
vim logs/PR_25_resolution.md
```

填寫內容:
- 衝突文件列表
- 選擇的解決策略
- 詳細的解決步驟
- API 變更（如果有）
- 測試結果

### Step 1.6: 提交合併

```bash
# 如果使用腳本，它會自動提交
# 如果手動合併，使用：
git commit -m "Merge PR #25: Refactor BioNeuron architecture with strategy base class"

# 推送到遠程
git push origin main
```

### Step 1.7: 重複 PR #16

```bash
# 確保在最新的 main
git pull origin main

# 重複 Steps 1.3-1.6 for PR #16
python scripts/batch_merge_prs.py --pr-list 16 --interactive
```

### Step 1.8: 重複 PR #8

```bash
# 確保在最新的 main
git pull origin main

# 重複 Steps 1.3-1.6 for PR #8
python scripts/batch_merge_prs.py --pr-list 8 --interactive
```

### Phase 1 完成檢查

- [ ] PR #25 已合併並驗證
- [ ] PR #16 已合併並驗證
- [ ] PR #8 已合併並驗證
- [ ] 所有測試通過
- [ ] 解決過程已記錄
- [ ] 代碼已推送到 main

---

## 📋 Phase 2: 功能模組 (Feature Modules)

**目標**: 合併 PRs #20, #14, #13, #6  
**預計時間**: 3-5 小時  
**優先級**: 🟡 MEDIUM

### Step 2.1: 更新並檢測衝突

```bash
# 確保 main 最新
git checkout main
git pull origin main

# 檢查 Phase 2 衝突
python scripts/check_merge_conflicts.py --phase 2 --report phase2_conflicts.md
cat phase2_conflicts.md
```

### Step 2.2: 批量合併或逐個合併

**選項 A: 批量合併（如果衝突少）**
```bash
python scripts/batch_merge_prs.py --phase 2 --interactive
```

**選項 B: 逐個合併（推薦）**
```bash
# PR #20: Security package
python scripts/batch_merge_prs.py --pr-list 20 --interactive
# 驗證...

# PR #14: Security refactor
python scripts/batch_merge_prs.py --pr-list 14 --interactive
# 驗證...

# PR #13: Vectorization
python scripts/batch_merge_prs.py --pr-list 13 --interactive
# 驗證...

# PR #6: Persistence
python scripts/batch_merge_prs.py --pr-list 6 --interactive
# 驗證...
```

### Step 2.3: 特別注意安全模組整合

PR #20 和 #14 都涉及安全模組，可能需要：

```bash
# 檢查是否需要創建新的安全包
ls -la src/bioneuronai/security/

# 如果需要整合多個安全模組
# 1. 創建統一的 security/ 包
mkdir -p src/bioneuronai/security/
touch src/bioneuronai/security/__init__.py

# 2. 移動相關文件
# 3. 更新導入語句
# 4. 添加向後兼容層
```

### Phase 2 完成檢查

- [ ] 所有 4 個 PR 已合併
- [ ] 安全模組統一整合
- [ ] 測試全部通過
- [ ] 性能基準測試通過
- [ ] 解決日誌已記錄

---

## 📋 Phase 3: CLI 和工具 (CLI & Tools)

**目標**: 合併 PRs #19, #5, #15  
**預計時間**: 2-3 小時  
**優先級**: 🟡 MEDIUM

### Step 3.1: 檢測衝突

```bash
git pull origin main
python scripts/check_merge_conflicts.py --phase 3 --report phase3_conflicts.md
```

### Step 3.2: Typer CLI 整合

PR #19 和 #5 都涉及 Typer CLI：

```bash
# 檢查現有 CLI
cat src/bioneuronai/cli.py

# 合併 PR
python scripts/batch_merge_prs.py --phase 3 --interactive
```

**特別注意**:
- CLI 接口變更
- 新的依賴（typer, streamlit）
- 向後兼容性

### Step 3.3: 測試 CLI 功能

```bash
# 測試新的 CLI
bioneuron-cli --help

# 如果有 Streamlit 儀表板
streamlit run src/bioneuronai/dashboard.py  # 如果存在
```

### Phase 3 完成檢查

- [ ] CLI 工具正常工作
- [ ] 儀表板可以啟動（如果適用）
- [ ] 配置文件支持正常
- [ ] 文檔已更新

---

## 📋 Phase 4-6: 剩餘階段

對於 Phase 4, 5, 6，重複相同的模式：

```bash
# 對每個 Phase:
# 1. 檢測衝突
python scripts/check_merge_conflicts.py --phase N --report phaseN.md

# 2. 合併 PR
python scripts/batch_merge_prs.py --phase N --interactive

# 3. 驗證
pytest tests/ -v
black src/ tests/
isort src/ tests/

# 4. 記錄
# 填寫解決日誌

# 5. 推送
git push origin main
```

---

## 🎯 最終驗證

所有 24 個 PR 合併後：

### 完整測試套件

```bash
# 完整測試
pytest tests/ -v --cov=bioneuronai --cov-report=html

# 查看覆蓋率報告
open htmlcov/index.html  # 或在瀏覽器中打開
```

### 代碼質量檢查

```bash
# 格式化
black src/ tests/ examples/
isort src/ tests/ examples/

# Linting
flake8 src/ tests/ examples/ --max-line-length=88 --extend-ignore=E203,W503

# 類型檢查
mypy src/ --ignore-missing-imports
```

### 功能測試

```bash
# 運行所有範例
python examples/basic_demo.py
python examples/advanced_demo.py
python examples/rag_chatbot.py
python examples/applications_demo.py

# 測試 CLI
bioneuron-cli --help
# 測試各種 CLI 命令
```

### 文檔驗證

```bash
# 檢查所有文檔鏈接
# 確保 README 是最新的
# 驗證 API 文檔

# 如果有文檔站點
cd docs/
# 構建文檔（如果適用）
```

---

## 📊 進度追蹤表

在執行過程中填寫：

```
Phase 1: Core Architecture
  ├─ PR #25: [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄
  ├─ PR #16: [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄
  └─ PR #8:  [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄

Phase 2: Feature Modules
  ├─ PR #20: [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄
  ├─ PR #14: [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄
  ├─ PR #13: [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄
  └─ PR #6:  [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄

Phase 3: CLI & Tools
  ├─ PR #19: [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄
  ├─ PR #5:  [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄
  └─ PR #15: [ ] 檢測 [ ] 合併 [ ] 驗證 [ ] 記錄

... 繼續 Phase 4, 5, 6 ...
```

---

## 🚨 故障排除

### 問題：無法獲取 PR 分支

```bash
# 檢查網絡連接
ping github.com

# 檢查 Git 配置
git remote -v

# 手動獲取
git fetch origin pull/25/head:pr-25
```

### 問題：衝突太複雜

```bash
# 中止當前合併
git merge --abort

# 查看快速參考
cat docs/CONFLICT_RESOLUTION_QUICK_REFERENCE.md

# 尋求幫助
# 在 GitHub issue 中討論
```

### 問題：測試失敗

```bash
# 查看詳細錯誤
pytest tests/ -vv

# 只運行失敗的測試
pytest tests/test_specific.py -vv

# 回滾如果需要
git revert HEAD
```

---

## ✅ 完成確認

所有步驟完成後：

- [ ] 24 個 PR 全部合併
- [ ] 所有測試通過
- [ ] 代碼質量檢查通過
- [ ] 範例全部運行
- [ ] 文檔已更新
- [ ] 解決日誌已記錄
- [ ] 性能無退化
- [ ] 無安全漏洞

**恭喜！🎉 所有 PR 已成功合併！**

---

## 📝 後續步驟

1. **發布新版本**
   ```bash
   # 更新版本號
   # 創建 release tag
   git tag -a v0.2.0 -m "Merged all 24 PRs"
   git push origin v0.2.0
   ```

2. **更新文檔**
   - 更新 CHANGELOG
   - 發布 release notes
   - 更新 README 如果需要

3. **通知團隊**
   - 在 PR 中留言
   - 發送郵件通知
   - 更新專案狀態

4. **監控**
   - 觀察 CI/CD 狀態
   - 檢查問題報告
   - 收集用戶反饋
