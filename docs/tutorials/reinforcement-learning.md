# 逐步教程：強化學習整合 / Step-by-step: Reinforcement Learning Integration

1. **定義狀態空間 Define State Space**
   - 使用神經元輸出、`novelty_score`、安全模組風險為觀測向量。
2. **獎勵設計 Reward Design**
   - 提供 `(novelty_score - risk_penalty)` 作為探索激勵，
     其中 `risk_penalty` 依安全模組 `Severity` 調整。
3. **策略更新 Policy Update**
   - 於高新穎性狀態執行策略梯度或 Q-learning 更新。
4. **安全約束 Safety Constraints**
   - 當安全模組輸出 `HIGH` 時，強制採取保守動作或觸發人工審查。
5. **持續學習 Continuous Learning**
   - 將訓練資料與事件記錄同步到 RAG 管線供後續推理。
