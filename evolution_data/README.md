# evolution_data/ — 策略進化與微調資料

> **更新日期**: 2026-07-11

此目錄存放自定義進化與微調資料（JSON/JSONL 格式），供統一多任務訓練器使用。

---

## 數據規格與合約

本系統已於 v2.1 廢棄舊版 `auto_evolve.py` 增量微調模式。所有自定義市場情境與對話資料已收斂為單一資料合約，並由 `unified_trainer.py` 進行多任務（Multi-task）聯合訓練。

訓練資料範例：
```json
[
    {
        "prompt": "什麼是趨勢跟隨策略？",
        "response": "趨勢跟隨策略是順著市場主要趨勢方向交易..."
    }
]
```

---

## 訓練與使用

所有增量微調請透過統一的訓練入口執行：

```bash
# 1. 收集最新行情訊號資料
python main.py collect-signal-data --symbol BTCUSDT --interval 1h --output data/unified_v2_training.jsonl

# 2. 啟動多任務聯合訓練（合併訊號與對話/微調資料）
python -m nlp.training.unified_trainer \
    --signal-data data/unified_v2_training.jsonl \
    --dialogue-data evolution_data/new_data.json
```

---

## 相關連結

* 📖 上層目錄：[專案根目錄 README](../README.md)
* 📖 同級模組：[NLP 模組 README](../src/nlp/README.md)
* 📖 模型管理：[模型資產 README](../model/README.md)
