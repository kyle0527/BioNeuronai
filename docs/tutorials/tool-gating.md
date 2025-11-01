# 逐步教程：工具閘門 / Step-by-step: Tool Gating

1. **定義工具描述 Define Tool Metadata**
   - 為每個工具加入 `[ZH]/[EN]` 雙語說明，供前端與代理判斷。
2. **建立信任分數管線 Build Trust Score Pipeline**
   - 使用 Hebbian 新穎性作為探索訊號，安全模組輸出作為抑制訊號。
3. **決策圖 Decision Graph**
   - 若 `novelty_score < 0.3` 且安全模組回報低風險，允許工具執行。
   - 否則要求額外審查或人工確認。
4. **審計紀錄 Auditing**
   - 記錄工具輸入/輸出與風險標籤，方便於儀表板呈現。
