# 逐步教程：儀表板 / Step-by-step: Observability Dashboard

1. **資料管線 Data Pipeline**
   - 收集 `novelty_score`、安全模組 `Severity`、工具使用紀錄。
2. **指標設計 Metric Design**
   - 設定 KPI：`Novelty Rolling Avg`、`Risk Escalation Count`、`Tool Approval Rate`。
3. **視覺化 Visualization**
   - 使用時間序列圖與風險矩陣，同時標註 `[ZH]/[EN]` 圖例。
4. **告警設定 Alerting**
   - 當高風險事件連續三次以上觸發時，發送多語通知給安全團隊。
