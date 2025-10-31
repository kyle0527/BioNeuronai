
# BioNeuronAI 文件中心 / Documentation Hub

歡迎來到 BioNeuronAI 的官方文件。此站點涵蓋項目概覽、技術白皮書、API 參考、
以及多語逐步教程，協助您快速整合 Hebbian 新穎性計算與安全模組。

Welcome to the official BioNeuronAI documentation site. Here you will find an
overview of the project, a technical whitepaper, auto-generated API references,
and bilingual step-by-step tutorials that show how to integrate Hebbian
novelty computation with safety modules.

## 內容導覽 / Navigation

- [技術白皮書 / Technical Whitepaper](whitepaper.md)
- [API 參考 / API Reference](api/core.md)
- [逐步教程 / Tutorials](tutorials/rag.md)

## 快速開始 / Quick Start

```bash
pip install -e .[docs]
mkdocs serve
```

啟動本地文件伺服器以瀏覽互動式文件。Start the local documentation
server to explore the interactive docs experience.
=======
# BioNeuronAI 官方網站

歡迎來到 BioNeuronAI 的官方網站！本頁面作為 GitHub Pages 首頁，提供最新版本公告、發展路線圖與使用者故事。

## 📢 版本公告

| 版本 | 發佈日期 | 亮點 |
| ---- | -------- | ---- |
| v0.4.0 | 2024-06-15 | 新增新穎性閘門，與安全模組整合，支援多場景部署；改善記憶管理。 |
| v0.3.2 | 2024-04-28 | 提升 Hebbian 學習穩定性，新增 CLI 工具。 |
| v0.3.0 | 2024-03-10 | 引入多層 BioNet 架構並提供標準化測試集。 |
| v0.2.1 | 2024-01-18 | 優化權重初始化，加入更多範例腳本。 |
| v0.2.0 | 2023-12-05 | 開放外部擴充 API，支援自定義突觸更新。 |

最新發佈詳細資訊與升級步驟請見 [版本說明](./release-notes.md)。

## 🗺️ 發展路線圖

| 時程 | 目標 | 說明 |
| ---- | ---- | ---- |
| 2024 Q3 | 新穎性閘門 + 安全模組聯合調適 | 與合作夥伴展開實境 A/B 測試，優化即時關鍵事件檢測。 |
| 2024 Q4 | 強化學習整合 | 提供策略學習模組與回饋循環介面。 |
| 2025 Q1 | 可視化監控儀表板 | 建立即時運行監控與告警系統。 |
| 2025 Q2 | 產業垂直化解決方案 | 提供醫療、製造、客服等專用模板。 |

如欲參與路線圖規劃，請於 [社群活動頁面](./community-engagement.md) 留意工作坊與黑客松。

## 🌟 使用者故事

- **臨床決策支援團隊**：透過新穎性閘門，自動篩選出與既有案例不同的患者樣態，將臨床審核時間縮短 35%。
- **製造業品質管理部門**：安全模組阻擋異常控制訊號，結合新穎性評分降低誤判率 42%，產線停機減少 18%。
- **客服自動化團隊**：在 RAG 管線中使用新穎性閘門過濾低可信回應，並以安全模組審核工具操作，客服滿意度提升 12%。

更多實際案例分析請參考 [案例研究與量化成效報告](./case-study.md)。

## 🔧 開發者資源

### 合併衝突解決指南

隨著專案快速發展，我們建立了完整的合併衝突解決框架：

- **[合併衝突解決指南](./MERGE_CONFLICT_RESOLUTION_GUIDE.md)** - 完整的策略和流程文檔
- **[快速參考指南](./CONFLICT_RESOLUTION_QUICK_REFERENCE.md)** - 常見衝突模式及解決方案
- **[衝突解決日誌模板](./CONFLICT_RESOLUTION_LOG_TEMPLATE.md)** - 記錄解決過程的標準模板

### 自動化工具

- `scripts/check_merge_conflicts.py` - 自動檢測跨 PR 的合併衝突
- `scripts/batch_merge_prs.py` - 批量合併 PR 的輔助工具
- 查看 `scripts/README.md` 了解詳細使用方法

## 📬 聯絡我們

- 產品/策略諮詢：`product@bioneuron.ai`
- 社群合作與活動：`community@bioneuron.ai`
- 技術支援：`support@bioneuron.ai`

歡迎關注我們的 [GitHub 倉庫](https://github.com/kyle0527/BioNeuronai)，追蹤最新動態。

