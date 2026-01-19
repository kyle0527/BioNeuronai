# Planning 計劃模組

智能交易計劃生成系統。

## 📋 模組概述

Planning 模組提供完整的交易計劃生成功能，基於市場分析、策略評估和風險計算。

## 🎯 主要組件

### 1. TradingPlanGenerator (交易計劃生成器)

生成完整的交易計劃，包括市場分析、策略選擇、風險參數和交易對建議。

**主要功能：**
- 深度市場環境分析
- 策略性能評估和選擇
- 精確風險參數計算
- 智能交易對選擇
- 計劃優化和驗證
- 回測驗證

**計劃生成流程：**

```
第一階段：市場環境深度分析
    ├── 宏觀經濟環境
    ├── 加密市場總體趨勢
    ├── 比特幣主導地位分析
    ├── 市場情緒指標
    └── 新聞事件影響評估

第二階段：策略選擇與優化
    ├── 歷史策略表現評估
    ├── 當前市場適配度分析
    ├── 策略組合優化
    └── 預期收益率估算

第三階段：風險參數精確計算
    ├── 波動率分析
    ├── VaR (風險價值) 計算
    ├── 最大回撤預測
    ├── 槓桿倍數建議
    └── 倉位大小計算

第四階段：交易對智能選擇
    ├── 流動性評分
    ├── 波動率評分
    ├── 價差成本分析
    ├── 技術設置評分
    ├── 基本面評分
    └── 綜合排序

第五階段：計劃優化與驗證
    ├── 參數優化
    ├── 約束條件檢查
    ├── 風險收益比優化
    └── 計劃可行性驗證

第六階段：執行環境準備
    ├── API 連接驗證
    ├── 資金充足性檢查
    ├── 監控系統設置
    └── 緊急止損準備
```

**使用示例：**
```python
from bioneuronai.planning import TradingPlanGenerator

# 初始化計劃生成器
planner = TradingPlanGenerator()

# 生成完整交易計劃
plan = await planner.generate_comprehensive_trading_plan()

# 查看計劃內容
print("📊 市場分析:")
print(f"  市場狀況: {plan['market_analysis']['condition']}")
print(f"  趨勢方向: {plan['market_analysis']['trend']}")
print(f"  情緒指標: {plan['market_analysis']['sentiment']:.2f}")

print("\n🎯 策略選擇:")
for strategy in plan['strategy_selection']['recommended_strategies']:
    print(f"  {strategy['name']}: {strategy['weight']:.1%}")

print("\n⚖️ 風險參數:")
print(f"  最大倉位: {plan['risk_params']['max_position_size']:.1%}")
print(f"  建議槓桿: {plan['risk_params']['leverage']}x")
print(f"  每筆風險: {plan['risk_params']['risk_per_trade']:.2%}")

print("\n💎 推薦交易對:")
for pair in plan['recommended_pairs'][:5]:
    print(f"  {pair['symbol']}: 評分 {pair['score']:.2f}")
```

### 2. MarketConditionAnalyzer (市場狀況分析器)

分析當前市場環境和趨勢。

**分析維度：**
- 📈 趨勢分析（牛市/熊市/震盪）
- 📊 波動率水平
- 💧 流動性狀況
- 📰 新聞情緒
- 🌐 宏觀經濟因素

**使用示例：**
```python
from bioneuronai.planning import MarketConditionAnalyzer

analyzer = MarketConditionAnalyzer()
analysis = await analyzer.analyze_current_market()

print(f"市場狀態: {analysis.condition}")        # BULLISH/BEARISH/RANGING
print(f"趨勢強度: {analysis.trend_strength}")   # 0-100
print(f"波動率: {analysis.volatility}")         # LOW/MEDIUM/HIGH
```

### 3. StrategyPerformanceEvaluator (策略性能評估器)

評估和比較不同交易策略的歷史表現。

**評估指標：**
- 📈 總收益率
- 📊 夏普比率
- 📉 最大回撤
- 🎯 勝率
- 💰 盈虧比
- 📅 平均持倉時間

**使用示例：**
```python
from bioneuronai.planning import StrategyPerformanceEvaluator

evaluator = StrategyPerformanceEvaluator()
performance = await evaluator.evaluate_strategies(days=30)

for strategy, metrics in performance.items():
    print(f"\n{strategy}:")
    print(f"  收益率: {metrics.total_return:.2%}")
    print(f"  夏普比率: {metrics.sharpe_ratio:.2f}")
    print(f"  最大回撤: {metrics.max_drawdown:.2%}")
    print(f"  勝率: {metrics.win_rate:.2%}")
```

### 4. RiskParameterCalculator (風險參數計算器)

基於市場狀況和帳戶情況計算最優風險參數。

**計算參數：**
- 最大倉位大小
- 建議槓桿倍數
- 單筆交易風險
- 止損止盈位置
- 每日交易次數限制

**使用示例：**
```python
from bioneuronai.planning import RiskParameterCalculator

calculator = RiskParameterCalculator()
params = await calculator.calculate_risk_parameters(
    account_balance=10000,
    market_volatility=0.03,
    risk_tolerance="MEDIUM"
)

print(f"最大倉位: {params.max_position_size:.1%}")
print(f"建議槓桿: {params.leverage}x")
print(f"每筆風險: {params.risk_per_trade:.2%}")
```

### 5. TradingPairSelector (交易對選擇器)

智能選擇最適合當前市場的交易對。

**選擇標準：**
- 流動性評分
- 波動率適配
- 價差成本
- 技術設置質量
- 新聞敏感度
- 相關性分析

**使用示例：**
```python
from bioneuronai.planning import TradingPairSelector

selector = TradingPairSelector()
pairs = await selector.select_best_pairs(
    market_condition="BULLISH",
    count=5
)

for pair in pairs:
    print(f"{pair.symbol}: 綜合評分 {pair.overall_score:.2f}")
    print(f"  流動性: {pair.liquidity_score:.2f}")
    print(f"  波動率: {pair.volatility_score:.2f}")
```

### 6. PlanOptimizer (計劃優化器)

優化交易計劃參數以達到最佳風險收益比。

**優化目標：**
- 最大化預期收益
- 最小化風險暴露
- 平衡多元化程度
- 滿足約束條件

### 7. PlanBacktester (計劃回測器)

對生成的交易計劃進行歷史回測驗證。

**回測功能：**
- 歷史數據模擬
- 性能指標計算
- 風險指標評估
- 壓力測試

## 📦 導出 API

```python
from bioneuronai.planning import (
    TradingPlanGenerator,          # 計劃生成器
    MarketConditionAnalyzer,       # 市場分析器
    StrategyPerformanceEvaluator,  # 策略評估器
    RiskParameterCalculator,       # 風險計算器
    TradingPairSelector,           # 交易對選擇器
    PlanOptimizer,                 # 計劃優化器
    PlanBacktester,                # 回測器
)
```

## 🔗 依賴關係

**內部依賴：**
- `core.TradingEngine` - 策略執行（可選）
- `analysis.CryptoNewsAnalyzer` - 新聞分析（可選）
- `services.TradingDatabase` - 歷史數據（可選）

**外部依賴：**
- `pandas` - 數據分析
- `numpy` - 數值計算
- `scipy` - 統計分析

## 🎨 架構設計

```
planning/
├── trading_plan_system.py      # 計劃生成核心
└── __init__.py                # 模組導出
```

## 🔧 配置說明

```python
# 計劃生成配置
PLANNING_CONFIG = {
    "default_timeframe": "24h",          # 計劃有效期
    "min_pairs": 3,                      # 最少交易對數
    "max_pairs": 10,                     # 最多交易對數
    "risk_free_rate": 0.02,             # 無風險利率
    "optimization_iterations": 100,      # 優化迭代次數
}

# 風險參數默認值
RISK_DEFAULTS = {
    "CONSERVATIVE": {
        "max_position": 0.05,
        "max_leverage": 1,
        "risk_per_trade": 0.01,
    },
    "MODERATE": {
        "max_position": 0.10,
        "max_leverage": 2,
        "risk_per_trade": 0.02,
    },
    "AGGRESSIVE": {
        "max_position": 0.20,
        "max_leverage": 3,
        "risk_per_trade": 0.03,
    },
}
```

## 📝 使用場景

### 場景 1：每日計劃生成

```python
async def generate_daily_plan():
    planner = TradingPlanGenerator()
    
    # 生成今日交易計劃
    plan = await planner.generate_comprehensive_trading_plan()
    
    # 保存計劃
    await planner._save_trading_plan(plan)
    
    # 執行計劃
    print("📋 今日交易計劃已生成")
    print(f"計劃版本: {plan['plan_version']}")
    print(f"有效期: {plan['validity_period']} 小時")
    
    return plan
```

### 場景 2：風險等級調整

```python
async def adjust_risk_level(risk_level: str):
    calculator = RiskParameterCalculator()
    
    # 計算不同風險等級的參數
    params = await calculator.calculate_risk_parameters(
        account_balance=10000,
        market_volatility=0.03,
        risk_tolerance=risk_level  # CONSERVATIVE/MODERATE/AGGRESSIVE
    )
    
    print(f"{risk_level} 風險等級參數:")
    print(f"  最大倉位: {params.max_position_size:.1%}")
    print(f"  建議槓桿: {params.leverage}x")
```

### 場景 3：市場適應性分析

```python
async def analyze_market_adaptation():
    analyzer = MarketConditionAnalyzer()
    evaluator = StrategyPerformanceEvaluator()
    
    # 分析當前市場
    market = await analyzer.analyze_current_market()
    
    # 評估策略適配度
    performance = await evaluator.evaluate_strategies(days=30)
    
    # 選擇最適合的策略
    best_strategies = [
        s for s, p in performance.items()
        if p.sharpe_ratio > 1.0
    ]
    
    print(f"當前市場: {market.condition}")
    print(f"推薦策略: {', '.join(best_strategies)}")
```

## ⚠️ 注意事項

1. **計劃更新**：市場變化時應重新生成計劃
2. **參數驗證**：確保風險參數符合個人承受能力
3. **回測驗證**：新策略應先進行充分回測
4. **靈活調整**：計劃是建議，實際執行要靈活應變

## 🚀 快速開始

```python
import asyncio
from bioneuronai.planning import TradingPlanGenerator

async def main():
    # 生成交易計劃
    planner = TradingPlanGenerator()
    plan = await planner.generate_comprehensive_trading_plan()
    
    # 顯示計劃摘要
    print("📋 交易計劃生成完成")
    print(f"\n市場狀況: {plan['market_analysis']['condition']}")
    print(f"推薦策略: {plan['strategy_selection']['primary_strategy']}")
    print(f"風險等級: {plan['risk_params']['risk_level']}")
    print(f"\n推薦交易對 (前5):")
    for pair in plan['recommended_pairs'][:5]:
        print(f"  {pair['symbol']}: {pair['score']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📈 性能指標

- 完整計劃生成：30-60 秒
- 市場分析：10-15 秒
- 策略評估：5-10 秒
- 交易對選擇：5-10 秒
- 計劃優化：10-20 秒

## 🔄 版本歷史

- v2.1.0 - 模組化重構，改進生成流程
- v2.0.0 - 新增計劃優化和回測功能
- v1.5.0 - 改進風險參數計算
- v1.0.0 - 初始版本
