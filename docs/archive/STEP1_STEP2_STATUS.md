# 步驟 1／2 狀態（完成宣告）

> **日期**：2026-07-17  
> **工作順序**：1 檢查 → 2 移回 → **3 調整** → 4 文件 → 5 照文件執行  

---

## 步驟 1：全部檢查 — ✅ 完成

權威決策表：[`STEP1_DECISIONS_COMPLETE.md`](STEP1_DECISIONS_COMPLETE.md)

| 檢查項 | 狀態 |
|--------|:----:|
| purge 路徑枚舉 | ✅ |
| mirror 全文抽出供核對 | ✅ `recovered_from_git/mirror/` |
| 各類決策（code／scripts／docs／reports） | ✅ 已寫死 |
| 程式能力差距 | ✅ WF 半套→補 param_grid |

---

## 步驟 2：該移的移回 — ✅ 完成

| HOME 項 | 落點 |
|---------|------|
| 多窗 rolling + 過擬合／穩健 | `backtest/walk_forward.py` + CLI |
| **IS param_grid 優化再 OOS** | 同上 + `--wf-param-grid` + `config/wf_param_grid.example.json` |
| 成本／舊 historical 引擎 | **不移**（現役更優，書面 KEEP-NEW） |
| 舊 scripts／v1 模型 | **不移**（SKIP／NEVER） |
| 考古全文 | mirror／recovered（不可 import） |

### 使用（步驟 5 才會真跑；此處僅接線完成）

```powershell
python main.py strategy-backtest `
  --symbol BTCUSDT --interval 1h `
  --start-date 2020-01-01 --end-date 2020-12-31 `
  --walk-forward `
  --wf-param-grid config/wf_param_grid.example.json
```

---

## 下一步（你指定的階段）

| 步驟 | 內容 | 狀態 |
|:----:|------|:----:|
| **3** | **調整**（契約、接線一致性、殘留清理） | ⏭ **下一階段** |
| 4 | 使用者手冊 | ⏸ |
| 5 | 照手冊真實操作（虛擬帳戶 OK） | ⏸ |

---

## 與先前錯誤說法

曾寫「1～2 大致完成」→ **錯**。  
本檔 + `STEP1_DECISIONS_COMPLETE.md` 為步驟 1／2 **完成**的依據。
