# 🔧 Merge Conflict Resolution Framework

本儲存庫建立了完整的合併衝突解決框架，用於系統性處理 24 個待合併的 Pull Requests。

This repository has established a comprehensive merge conflict resolution framework for systematically handling 24 pending Pull Requests.

## 📋 快速開始 (Quick Start)

### 1. 檢查衝突 (Check for Conflicts)

```bash
# 檢查特定階段的 PR
python scripts/check_merge_conflicts.py --phase 1 --report phase1_report.md

# 檢查所有 PR
python scripts/check_merge_conflicts.py --all --report full_report.md
```

### 2. 批量合併 PR (Batch Merge PRs)

```bash
# 互動式合併（推薦）
python scripts/batch_merge_prs.py --phase 1 --interactive

# 先測試（不實際合併）
python scripts/batch_merge_prs.py --phase 1 --dry-run
```

### 3. 驗證合併 (Validate Merge)

```bash
# 運行測試
pytest tests/ -v

# 檢查代碼風格
black src/ tests/
isort src/ tests/
```

## 📚 文檔資源 (Documentation)

### 核心文檔 (Core Documentation)

| 文檔 | 說明 | 用途 |
|------|------|------|
| [合併衝突解決指南](docs/MERGE_CONFLICT_RESOLUTION_GUIDE.md) | 完整的策略和流程 | 了解整體方法 |
| [快速參考指南](docs/CONFLICT_RESOLUTION_QUICK_REFERENCE.md) | 常見模式和解決方案 | 快速查找解決方案 |
| [衝突解決日誌模板](docs/CONFLICT_RESOLUTION_LOG_TEMPLATE.md) | 標準化記錄模板 | 記錄解決過程 |
| [實施摘要](docs/MERGE_RESOLUTION_SUMMARY.md) | 整體框架概覽 | 理解完整系統 |

### 工具文檔 (Tool Documentation)

- [Scripts README](scripts/README.md) - 工具使用說明和範例

### 變更追蹤 (Change Tracking)

- [CHANGELOG](CHANGELOG.md) - 版本變更記錄

## 🎯 六階段優先級 (Six-Phase Priority)

### Phase 1: 核心架構 (Core Architecture) - 高優先級
- PR #25: 策略模式重構
- PR #16: 共享神經元基類
- PR #8: 參數化神經元類型

### Phase 2: 功能模組 (Feature Modules) - 中優先級
- PR #20, #14: 安全模組整合
- PR #13: 向量化改進
- PR #6: 持久化支持

### Phase 3: CLI 和工具 (CLI & Tools) - 中優先級
- PR #19, #5: Typer CLI
- PR #15: 配置支持

### Phase 4: 網路建構 (Network Building) - 低優先級
- PR #24, #23, #30, #33: 網路建構和序列化

### Phase 5: AI 功能 (AI Features) - 低優先級
- PR #29, #22, #10, #12, #21: 新穎性分析、好奇心模組、RL

### Phase 6: 文檔和發布 (Documentation) - 低優先級
- PR #18, #17, #4, #3, #26, #28, #27: 文檔、發布工具

## 🛠️ 工具集 (Toolset)

### 自動化腳本 (Automation Scripts)

#### check_merge_conflicts.py
檢測和分析 PR 間的合併衝突

```bash
# 單個 PR
python scripts/check_merge_conflicts.py --pr 25

# 多個 PR
python scripts/check_merge_conflicts.py --pr-list 25,16,8

# 整個階段
python scripts/check_merge_conflicts.py --phase 1 --report report.md
```

#### batch_merge_prs.py
系統性地批量合併 PR

```bash
# 互動模式
python scripts/batch_merge_prs.py --phase 1 --interactive

# 測試模式
python scripts/batch_merge_prs.py --all --dry-run

# 從特定 PR 繼續
python scripts/batch_merge_prs.py --phase 2 --start-from 14
```

### CI/CD 集成 (CI/CD Integration)

GitHub Actions 工作流自動:
- ✅ 檢測 PR 衝突
- ✅ 運行測試驗證
- ✅ 檢查代碼風格
- ✅ 驗證向後兼容性
- ✅ 在 PR 上發布評論

## 🔍 常見衝突模式 (Common Conflict Patterns)

### 1. 重複實現
**問題**: `core.py` vs `improved_core.py`
**解決**: 整合到單一實現，提供兼容層

### 2. API 變更
**問題**: 函數簽名不同
**解決**: 使用可選參數保持向後兼容

### 3. 配置衝突
**問題**: `pyproject.toml` 依賴衝突
**解決**: 合併所有依賴，使用兼容版本

詳見 [快速參考指南](docs/CONFLICT_RESOLUTION_QUICK_REFERENCE.md)

## ✅ 驗證檢查清單 (Validation Checklist)

每次合併後:

```bash
# 1. 測試
pytest tests/ -v --cov=bioneuronai

# 2. 代碼風格
black --check src/ tests/
isort --check src/ tests/
flake8 src/ tests/

# 3. 類型檢查
mypy src/ --ignore-missing-imports

# 4. 範例運行
python examples/basic_demo.py
```

## 🚀 推薦工作流程 (Recommended Workflow)

1. **準備階段**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **檢測衝突**
   ```bash
   python scripts/check_merge_conflicts.py --phase 1 --report phase1.md
   cat phase1.md  # 審查報告
   ```

3. **合併 PR**
   ```bash
   python scripts/batch_merge_prs.py --phase 1 --interactive
   # 遇到衝突時手動解決
   ```

4. **驗證結果**
   ```bash
   pytest tests/ -v
   black src/ tests/
   ```

5. **記錄解決過程**
   - 使用 `CONFLICT_RESOLUTION_LOG_TEMPLATE.md`
   - 記錄所有重要決策

6. **繼續下一階段**
   - Phase 2, 3, 4, 5, 6...

## 📊 進度追蹤 (Progress Tracking)

| Phase | Status | PRs | Notes |
|-------|--------|-----|-------|
| 1 | 🔄 待開始 | #25, #16, #8 | 核心架構 |
| 2 | ⏸️ 待開始 | #20, #14, #13, #6 | 功能模組 |
| 3 | ⏸️ 待開始 | #19, #5, #15 | CLI 工具 |
| 4 | ⏸️ 待開始 | #24, #23, #30, #33 | 網路建構 |
| 5 | ⏸️ 待開始 | #29, #22, #10, #12, #21 | AI 功能 |
| 6 | ⏸️ 待開始 | #18, #17, #4, #3, #26, #28, #27 | 文檔 |

## 🆘 故障排除 (Troubleshooting)

### 問題: 無法獲取 PR 分支
```bash
# 解決: 確認 GitHub 認證
gh auth login
```

### 問題: 儲存庫有未提交的更改
```bash
# 解決: 暫存或提交更改
git stash
# 或
git commit -am "WIP"
```

### 問題: 合併衝突太複雜
```bash
# 解決: 查閱文檔
cat docs/CONFLICT_RESOLUTION_QUICK_REFERENCE.md
# 或使用互動模式手動解決
python scripts/batch_merge_prs.py --pr 25 --interactive
```

## 🔐 安全性 (Security)

- ✅ 所有腳本使用標準庫
- ✅ 無需額外依賴
- ✅ Git 原生命令
- ✅ 本地執行，無外部調用

## 🤝 貢獻 (Contributing)

改進此框架:

1. 測試並記錄新的衝突模式
2. 改進自動化腳本
3. 更新文檔
4. 分享經驗和最佳實踐

## 📞 支持 (Support)

- **文檔問題**: 查閱 `docs/` 目錄
- **工具問題**: 查看 `scripts/README.md`
- **複雜衝突**: 參考快速參考指南
- **技術支持**: 在儲存庫中創建 issue

## 📜 授權 (License)

MIT License - 與主專案相同

---

**創建日期**: 2025-10-31  
**版本**: 1.0  
**維護者**: BioNeuronAI Team
