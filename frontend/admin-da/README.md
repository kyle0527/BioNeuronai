# BioNeuronAI Admin Dashboard

> **部署狀態：暫緩（第二階段）**
>
> 本前端為管理儀板原始碼，保留供後續整併使用；目前不作為正式部署目標。
> 第一階段正式 UI 主線是 `frontend/devops-d/` 的 Operations Dashboard。

## 目前定位

`frontend/admin-da/` 主要包含管理後台與 WebSocket 儀表板相關實作，例如風控摘要、訂單歷史、稽核與管理視圖。這些功能與目前後端 API 有部分可重用內容，但尚未完成端點逐項驗收，因此不列入目前 Docker frontend build 或日常操作手冊的主流程。

## 使用限制

- 不作為 `docker-compose.yml` 的 frontend build context。
- 不保證所有 API / WebSocket path 已與目前 `src/bioneuronai/api/routes/` 完全對齊。
- 若要重新啟用，需先完成 API path、WebSocket payload、風控設定與訂單資料格式驗證。

## 第二階段整理方向

1. 將仍有價值的管理面板移入 `frontend/devops-d`。
2. 移除或改寫與目前 API 不一致的 mock/demo 資料。
3. 實際啟動 API + Vite 逐頁確認，再決定是否保留為獨立 app。
