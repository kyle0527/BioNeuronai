# Runtime 與輸出產物手冊

> 範圍：使用者如何找到每次操作後產生的結果、log、runtime、模型與資料產物。

---

## 📑 目錄

- [1. 產物範圍](#1-產物範圍)
- [2. 找到最近的回測結果](#2-找到最近的回測結果)
- [3. API 查詢 runtime](#3-api-查詢-runtime)
- [4. 驗收產物判斷](#4-驗收產物判斷)
- [5. Git 狀態排查](#5-git-狀態排查)
- [6. 保留與清理原則](#6-保留與清理原則)

---

## 1. 產物範圍

本手冊只描述使用者實際操作後需要辨識的輸出位置與檢查方式，包含：

- `backtest/runtime/<run_id>/`
- `output/`
- `logs/`
- `model/`
- `src/data/bioneuronai/`

實際檔案會依操作入口不同而變化，請以該次 run 的目錄內容與 API 回應為準。

---

## 2. 找到最近的回測結果

```powershell
Get-ChildItem backtest\runtime -Directory |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 5 Name, LastWriteTime
```

查看某次 run：

```powershell
Get-ChildItem backtest\runtime\<run_id>
```

常見檔案：

```text
status.json
summary.json
trades.json
orders.json
```

不同 run 類型可能產生不同檔案，以實際目錄為準。

---

## 3. API 查詢 runtime

啟動 API 後：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/backtest/runs"
```

查單一 run：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/backtest/runs/<run_id>"
```

---

## 4. 驗收產物判斷

| 操作 | 應看到 |
|---|---|
| `simulate` | `Run ID`、runtime 目錄 |
| `backtest` | 統計數字、交易次數、runtime 目錄 |
| `strategy-backtest` | 策略比較結果與 runtime |
| `frontend build` | `frontend/devops-d/dist/` |
| API status | JSON 回應 |

---

## 5. Git 狀態排查

實際操作後請檢查：

```powershell
git status --short
```

若出現 runtime、logs、DB 類檔案變更，先判斷是否為執行產物。不要把敏感資訊或大型資料誤提交。

---

## 6. 保留與清理原則

| 產物 | 建議 |
|---|---|
| 成功驗收的 runtime | 可保留作證據 |
| 臨時短測試 runtime | 可定期清理 |
| `model/*.pth` | 不隨意刪除 |
| `data/processed/*.pt` | 不隨意刪除 |
| `.env` | 不提交 |
