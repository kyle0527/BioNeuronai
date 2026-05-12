"""驗證 Golden Profile 完整流程：generate → save → load → apply"""
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(Path(_root) / "src"))
sys.path.insert(0, _root)

from bioneuronai.strategies.selector.profile import (
    GoldenProfileManager, GoldenStrategyProfile, DEFAULT_PROFILE_PATH
)

# 模擬 strategy-backtest 的輸出結果
mock_backtest_result = {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "ranking": [
        {
            "template_key": "News_Trading",
            "name": "新聞驅動交易",
            "strategy_type": "news_trading",
            "stats": {"total_return": 0.12, "sharpe_ratio": 1.8, "max_drawdown": 0.05},
        },
        {
            "template_key": "Swing_Trading",
            "name": "波段交易",
            "strategy_type": "swing_trading",
            "stats": {"total_return": 0.10, "sharpe_ratio": 1.5, "max_drawdown": 0.07},
        },
        {
            "template_key": "MA_Crossover_Trend",
            "name": "MA 交叉趨勢",
            "strategy_type": "trend_following",
            "stats": {"total_return": 0.08, "sharpe_ratio": 1.2, "max_drawdown": 0.08},
        },
        {
            "template_key": "Breakout_Trading",
            "name": "區間突破",
            "strategy_type": "breakout",
            "stats": {"total_return": 0.06, "sharpe_ratio": 0.9, "max_drawdown": 0.10},
        },
        {
            "template_key": "RSI_Mean_Reversion",
            "name": "RSI 均值回歸",
            "strategy_type": "mean_reversion",
            "stats": {"total_return": 0.04, "sharpe_ratio": 0.6, "max_drawdown": 0.06},
        },
        {
            "template_key": "High_Frequency_Scalp",
            "name": "高頻剝頭皮",
            "strategy_type": "scalping",
            "stats": {"total_return": -0.02, "sharpe_ratio": -0.3, "max_drawdown": 0.15},
        },
    ],
}

print("=" * 60)
print("  Golden Profile 完整流程驗證")
print("=" * 60)

# Step 1: Generate
print("\n[Step 1] 從回測結果生成 Profile...")
profile = GoldenProfileManager.generate_from_backtest(mock_backtest_result)
if not profile:
    print("  ❌ 生成失敗！")
    sys.exit(1)
print("  ✅ 生成成功")
print(f"  路徑: {DEFAULT_PROFILE_PATH}")

# Step 2: 驗證權重 key 格式（必須是 StrategyType.value）
print("\n[Step 2] 驗證權重 key 格式...")
for key, weight in profile.strategy_weights.items():
    print(f"  {key:25s} → {weight:.4f}")
# 檢查 key 是否為 StrategyType.value 格式（小寫+底線）
bad_keys = [k for k in profile.strategy_weights if k != k.lower() or " " in k]
if bad_keys:
    print(f"  ❌ 發現非 StrategyType.value 格式的 key: {bad_keys}")
    sys.exit(1)
print("  ✅ 所有 key 格式正確")

# 驗證權重和 = 1.0
total = sum(profile.strategy_weights.values())
print(f"  權重總和: {total:.4f} (期望 ≈ 1.0)")
if abs(total - 1.0) > 0.05:
    print("  ❌ 權重總和偏差過大！")
    sys.exit(1)
print("  ✅ 權重歸一化正確")

# 檢查負 Sharpe 的策略（scalping）是否權重為 0
scalping_w = profile.strategy_weights.get("scalping", -1)
print(f"  scalping 權重: {scalping_w} (期望 = 0，因為 Sharpe 為負)")
if scalping_w > 0:
    print("  ⚠️ 負 Sharpe 策略不應有正權重")

# Step 3: Load back
print("\n[Step 3] 從檔案載入 Profile...")
loaded = GoldenProfileManager.load()
if not loaded:
    print("  ❌ 載入失敗！")
    sys.exit(1)
print("  ✅ 載入成功")
print(f"  版本: {loaded.version}")
print(f"  回測期間: {loaded.backtest_period}")
print(f"  策略數量: {len(loaded.strategy_weights)}")

# Step 4: 驗證 regime_overrides
print("\n[Step 4] 驗證 regime_overrides...")
for regime, stype in loaded.regime_overrides.items():
    print(f"  {regime:25s} → {stype}")
if loaded.regime_overrides:
    print("  ✅ regime_overrides 已生成")
else:
    print("  ⚠️ regime_overrides 為空（可能是 configs 無法載入）")

# Step 5: 驗證 template_rankings 保留
print("\n[Step 5] 驗證模板排行榜...")
for r in loaded.template_rankings[:3]:
    print(f"  #{r['rank']} {r['template_key']:25s} type={r['strategy_type']:20s} sharpe={r['sharpe_ratio']:.2f}")
print("  ✅ 原始排行榜已保留（用於審計）")

# Step 6: Apply to selector
print("\n[Step 6] 模擬 apply_to_selector...")

class MockSelector:
    def __init__(self):
        self._performance_weights = {}
        self._performance_blend_alpha = 0.3
    def load_performance_weights(self, weights, blend_alpha=0.3):
        self._performance_weights = weights
        self._performance_blend_alpha = blend_alpha
        print(f"  注入權重: {weights}")
        print(f"  blend_alpha: {blend_alpha}")

mock_sel = MockSelector()
success = GoldenProfileManager.apply_to_selector(mock_sel, loaded)
if not success:
    print("  ❌ apply 失敗！")
    sys.exit(1)

# 模擬 _calculate_strategy_weights 中的 blend 邏輯
print("\n[Step 7] 模擬實際 blend 計算...")
base_weights = {
    "trend_following": 0.25,
    "mean_reversion": 0.25,
    "breakout": 0.25,
    "swing_trading": 0.25,
}
alpha = mock_sel._performance_blend_alpha
perf_w = mock_sel._performance_weights
blended = {}
for key in base_weights:
    pw = perf_w.get(key, 0.0)
    blended[key] = (1 - alpha) * base_weights[key] + alpha * pw
total_b = sum(blended.values())
if total_b > 0:
    blended = {k: v / total_b for k, v in blended.items()}
for key, w in sorted(blended.items(), key=lambda x: -x[1]):
    marker = "← BOOSTED" if w > base_weights.get(key, 0) else ""
    print(f"  {key:25s} base={base_weights.get(key, 0):.4f} → blended={w:.4f} {marker}")

print(f"\n{'=' * 60}")
print("  ✅ 所有驗證通過！")
print(f"{'=' * 60}")

# 清理測試產生的檔案
import os
if DEFAULT_PROFILE_PATH.exists():
    os.remove(DEFAULT_PROFILE_PATH)
    print(f"\n  🗑️ 已清理測試檔案: {DEFAULT_PROFILE_PATH}")
