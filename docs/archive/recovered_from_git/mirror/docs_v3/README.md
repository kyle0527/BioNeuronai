# 📚 BioNeuronAI v3.x 文檔歸檔說明

**歸檔日期**: 2026年1月26日  
**版本**: v3.x → v4.0 升級歸檔

---

## 目錄

- [歸檔內容](#-歸檔內容)
- [v4.0 主要變更](#-v40-主要變更)
- [新版文檔位置](#-新版文檔位置)
- [遷移指南](#-遷移指南)
- [保留理由](#-保留理由)
- [注意事項](#%EF%B8%8F-注意事項)
- [需要幫助？](#-需要幫助)

---

## 📋 歸檔內容

本目錄包含 BioNeuronAI v3.x 版本的操作手冊，這些文檔已被新版 **v4.0 統一操作手冊** 取代。

### 已歸檔文檔列表

| 文件名 | 版本 | 歸檔原因 |
|--------|------|----------|
| USER_MANUAL.md | v3.1 | 已整合至 v4.0 主手冊 |
| NEWS_ANALYZER_GUIDE.md | v3.0 | 已升級為 RLHF 系統 |
| CRYPTO_TRADING_SOP.md | v1.0 | 已整合至 v4.0 SOP 章節 |
| TRADING_STRATEGIES_GUIDE.md | v3.0 | 已整合至策略系統章節 |
| CRYPTO_TRADING_GUIDE.md | v2.0 | 已整合至快速入門 |
| CRYPTO_TRADING_README.md | v3.0 | 已整合至系統簡介 |

---

## 🆕 v4.0 主要變更

### 新增功能
- ✨ **基因演算法策略進化** - Island Model 並行演化
- ✨ **RL Meta-Agent 策略融合** - 43維狀態空間 + Transformer Policy
- ✨ **RLHF 新聞預測驗證** - 自動化預測循環 + 人類反饋

### 文檔改進
- 📚 整合 6 個獨立手冊 → 1 個統一主手冊
- 📚 添加完整 ML 算法說明與使用指南
- 📚 統一版本號為 v4.0
- 📚 改進結構與導航

---

## 📖 新版文檔位置

### 主要文檔
- **統一操作手冊**: `docs/BIONEURONAI_MASTER_MANUAL.md` ⭐
- **完整實現計劃**: `_out/COMPLETE_IMPLEMENTATION_PLAN.md`

### 技術文檔（保留）
- `docs/BINANCE_TESTNET_STEP_BY_STEP.md`
- `docs/DATA_SOURCES_GUIDE.md`
- `docs/DATABASE_UPGRADE_GUIDE.md`
- `docs/DEVELOPMENT_TOOLS.md`
- `docs/TRADING_COSTS_GUIDE.md`
- `docs/QUICKSTART_V2.1.md`
- `docs/DAILY_REPORT_CHECKLIST.md`
- `docs/TRADING_PLAN_10_STEPS.md`

---

## 🔄 遷移指南

### 從 v3.x 升級到 v4.0

1. **更新依賴**:
   ```bash
   pip install stable-baselines3==2.2.1 gymnasium==0.29.1 deap==1.4.1 schedule
   ```

2. **閱讀新手冊**:
   - 閱讀 `BIONEURONAI_MASTER_MANUAL.md` 第 7 章（三大 ML 核心系統）

3. **運行測試**:
   ```bash
   python tests/test_ml_systems.py
   ```

4. **查看舊文檔**（如需參考）:
   - 本目錄 (`archived/docs_v3/`) 保留所有舊版文檔

---

## 📝 保留理由

這些文檔被保留作為：
- 📜 歷史參考
- 🔍 版本對比
- 🎓 學習演進過程
- 🛠️ 故障排除參考

---

## ⚠️ 注意事項

1. **不建議使用舊文檔**:
   - v3.x 文檔可能包含過時信息
   - 請優先參考 v4.0 主手冊

2. **舊文檔內容已整合**:
   - 有用內容已合併到 v4.0 主手冊
   - 無需單獨閱讀舊文檔

3. **如遇衝突**:
   - 以 v4.0 主手冊為準
   - 舊文檔僅供參考

---

## 📞 需要幫助？

如果你在使用 v4.0 時遇到問題：

1. ✅ 先查閱 `BIONEURONAI_MASTER_MANUAL.md` 的 [常見問題 FAQ](#常見問題-faq) 章節
2. ✅ 參考 `COMPLETE_IMPLEMENTATION_PLAN.md` 的技術細節
3. ✅ 在 GitHub Issues 報告問題

---

**版權所有** © 2026 BioNeuronAI Team

> 📖 上層目錄：[archived/README.md](../README.md)
