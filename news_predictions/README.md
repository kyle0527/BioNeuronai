# news_predictions/ — 新聞預測驗證記錄

> **更新日期**: 2026-04-07

此目錄存放 `CryptoNewsAnalyzer` 的新聞情緒預測輸出與後續驗證結果（JSON 格式）。

## 產生來源

執行 CLI `news` 指令或 API `/api/v1/news` 時自動寫入：

```bash
python -m bioneuronai.cli.main news --symbol BTCUSDT
```

## 用途

- 記錄每次新聞分析的情緒分數與信心度
- 累積後可用於驗證新聞情緒對價格的預測準確率
- 供 RAG 系統更新 `InternalKnowledgeBase`

> 此目錄下的檔案不應提交至版本控制。

> 📖 上層目錄：[根目錄 README](../README.md)
