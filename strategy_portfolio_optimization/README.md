# strategy_portfolio_optimization/ — 投組優化結果

> **更新日期**: 2026-04-07

此目錄存放 `StrategyPortfolioOptimizer` 每次執行後輸出的最佳投組配置 JSON。

## 產生來源

`StrategyPortfolioOptimizer.optimize()` 執行後自動寫入：

```python
from bioneuronai.strategies.portfolio_optimizer import StrategyPortfolioOptimizer
optimizer = StrategyPortfolioOptimizer()
result = await optimizer.optimize(candidates_dir="strategy_arena_results/")
```

## 檔案格式

```
best_portfolio_YYYYMMDD_HHMMSS.json
```

包含欄位：策略組合、各策略權重分配、預期 Sharpe、最大回撤、相關性矩陣

## 與 strategy_arena_results/ 的關係

```
strategy_arena_results/  ←  各策略個體最佳結果
        ↓
strategy_portfolio_optimization/  ←  多策略組合的最佳配置
        ↓
StrategySelector  ←  根據組合配置動態分配信號權重
```

> 此目錄下的檔案不應提交至版本控制。

> 📖 上層目錄：[根目錄 README](../README.md)
