# trading_plan_data/ — 交易計劃輸出

> **更新日期**: 2026-04-07

此目錄存放 `TradingPlanController` 產生的完整交易計劃 JSON 輸出。

## 產生來源

執行 CLI `plan` 指令或 API `/api/v1/plan` 時自動寫入：

```bash
python -m bioneuronai.cli.main plan --symbol BTCUSDT
```

## 檔案格式

```
trading_plan_data/
└── trading_plan_YYYYMMDD_HHMMSS.json   # 每次執行產生一個時間戳記檔案
```

## 內容

每份計劃包含 10 步驟分析結果：
1. 市場狀態識別
2. 宏觀市場掃描（恐懼貪婪指數、全球市值等）
3. 技術分析
4. 風險評估
5-10. 執行計劃與倉位建議

> 此目錄下的檔案不應提交至版本控制。

> 📖 上層目錄：[根目錄 README](../README.md)
