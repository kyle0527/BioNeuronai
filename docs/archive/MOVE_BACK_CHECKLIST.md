# 步驟 2 清單清單：該移的移回來（只認程式證明）

> **前置**：步驟 1 重做見 `STEP1_RECHECK.md`。  
> **規則**：每一項必須「現役檔存在 + 證明指令通過」才勾 ✅。  
> **禁止**：只改 md 就勾完成。  
> **步驟 3 在本清單全部 ✅ 之前禁止開始。**

---

## A. Walk-Forward（HOME）

| # | 要求 | 現役位置 | 證明結果 | 狀態 |
|---|------|----------|----------|:----:|
| A1 | 滾動多窗可 import | `backtest/walk_forward.py` | `A1_windows 9` / `A1_A2_PASS` | ✅ |
| A2 | param_grid + IS 優化 | 同上 | `A2_candidates 2`；fake suite `optimal fast_ma=21` / `A2_OPTIMIZE_PASS` | ✅ |
| A3 | service 接 wf_param_grid | `backtest/service.py` | `wf_param_grid True` / `A3_PASS` | ✅ |
| A4 | CLI 暴露參數 | `cli/main.py` | `--walk-forward` / `--wf-param-grid` 出現在 help / `A4_PASS` | ✅ |
| A5 | readiness 用 single | `readiness_gate.py` | 源碼含 `walk_forward_mode` + `single` / `A5_PASS` | ✅ |

## B. 新聞方向契約

| # | 要求 | 現役位置 | 證明結果 | 狀態 |
|---|------|----------|----------|:----:|
| B1 | bias 強制 NEUTRAL | `strategy_fusion.py` | `news_bias["direction"] = "NEUTRAL"` 存在 / `B1_PASS` | ✅ |
| B2 | pretrade importance | `pretrade_automation.py` | `event_importance` + `_HIGH_RISK_TYPES` / `B2_PASS` | ✅ |
| B3 | should_trade legacy | `analyzer.py` | docstring Legacy / `B3_PASS` | ✅ |

## C. 明確不誤移

| # | 項目 | 證明結果 | 狀態 |
|---|------|----------|:----:|
| C1 | active_model 仍 unified_v2 | `unified_v2_100m` trained false / `C1_PASS` | ✅ |
| C2 | src 無 use_model.py 舊入口 | 搜尋無 / `C2_PASS` | ✅ |
| C3 | trading_costs 現役可 import | `TradingCostCalculator` / `C3_PASS` | ✅ |

## D. 證明紀錄

```text
日期：2026-07-17
方式：本機 python import + main.py strategy-backtest -h + fake suite 優化路徑
結果：A1–A5、B1–B3、C1–C3 均通過（見 session 終端紀錄）
```

---

## 步驟 2 狀態

**本清單技術項已全部 ✅。**  

注意：這是「移回項的**程式存在性與接線證明**」，**不是**步驟 5 的歷史資料長跑／paper 實操。  
長跑屬步驟 5；步驟 3 調整仍須你確認「步驟 1+2 可接受」後再開始。

若你認為步驟 1 還要再掃其他目錄（例如 `tools/`、frontend），說一聲，步驟 1 可再開一輪，**步驟 2 不自動等於全專案結束**。
