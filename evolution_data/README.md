# evolution_data/ — 策略進化訓練資料

> **更新日期**: 2026-04-07

此目錄存放供 `auto_evolve.py` 增量訓練使用的自定義進化資料（JSON 格式）。

## 格式

```json
[
    {
        "prompt": "什麼是趨勢跟隨策略？",
        "response": "趨勢跟隨策略是順著市場主要趨勢方向交易..."
    }
]
```

## 使用

```bash
cd src/nlp/training
python auto_evolve.py \
    --model-path model/my_100m_model.pth \
    --data evolution_data/new_data.json
```

> 目前正式訓練入口為 `unified_trainer.py`，此目錄主要供補充資料的增量訓練使用。

> 📖 上層目錄：[根目錄 README](../README.md)
