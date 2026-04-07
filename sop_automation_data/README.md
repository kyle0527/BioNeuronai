# sop_automation_data/ — SOP 自動化檢查記錄

> **更新日期**: 2026-04-07

此目錄存放 `SOPAutomationSystem` 的執行輸出（JSON 格式）。

## 產生來源

CLI `plan` 指令在沒有 `TradingPlanController` 時的 fallback，或明確呼叫 SOP 時自動寫入：

```bash
python -m bioneuronai.cli.main plan --symbol BTCUSDT
```

## 檔案格式

```
sop_check_YYYYMMDD_HHMMSS.json
```

每個檔案包含：
- 市場掃描結果（多空訊號、技術指標）
- 風險評估（帳戶餘額、回撤狀態）
- 執行建議（進場時機、止損止盈位置）

> 此目錄下的檔案不應提交至版本控制。

> 📖 上層目錄：[根目錄 README](../README.md)
