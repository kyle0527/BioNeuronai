# strategy_arena_results/ — 策略競技場結果

> **更新日期**: 2026-04-07

此目錄存放 `StrategyArena`（基因演算法策略競技場）每次執行後篩選出的最佳策略 JSON。

## 產生來源

`StrategyArena.run_evolution()` 每完成一個世代評估後自動寫入：

```python
from bioneuronai.strategies.strategy_arena import StrategyArena
arena = StrategyArena()
best = await arena.run_evolution(symbol="BTCUSDT", generations=10)
```

## 檔案格式

```
best_strategy_YYYYMMDD_HHMMSS.json
```

包含欄位：`id`、`name`、`strategy_type`、`parameters`、`total_return`、`sharpe_ratio`、`sortino_ratio`、`max_drawdown`

## 用途

- 記錄每次進化的最佳個體，供後續分析比較
- `StrategySelector` 可讀取此目錄選擇上線策略
- 可做為 `PortfolioOptimizer` 的候選池

> 此目錄下的檔案不應提交至版本控制。

> 📖 上層目錄：[根目錄 README](../README.md)
