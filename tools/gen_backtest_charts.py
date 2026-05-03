"""Generate performance chart PNGs from a backtest result.json."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

RUN_DIR = Path(__file__).parent.parent / "backtest/runtime/20260503_005554_cc68c4bb"
OUT_DIR = Path(__file__).parent.parent / "docs/assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

result = json.loads((RUN_DIR / "result.json").read_text(encoding="utf-8"))
orders = [json.loads(l) for l in (RUN_DIR / "orders.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

timestamps = [datetime.fromtimestamp(t / 1000) if isinstance(t, (int, float)) else datetime.fromisoformat(str(t)) for t in result["timestamps"]]
equity = result["equity_curve"]
drawdown = [d * 100 for d in result["drawdown_curve"]]

# ── equity_curve.png ──────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(timestamps, equity, linewidth=1, color="#2196F3", label="Portfolio equity")
ax.axhline(10000, linestyle="--", linewidth=0.8, color="#9E9E9E", label="Initial balance ($10 000)")
ax.set_title("BioNeuronAI Backtest — Equity Curve\nBTCUSDT 1h · 2022-01-01 to 2022-12-31", fontsize=12)
ax.set_ylabel("Equity (USDT)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_major_locator(mdates.MonthLocator())
plt.xticks(rotation=30, ha="right")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_DIR / "equity_curve.png", dpi=150)
plt.close()
print("Saved equity_curve.png")

# ── drawdown.png ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 4))
ax.fill_between(timestamps, drawdown, 0, alpha=0.6, color="#F44336", label="Drawdown")
ax.plot(timestamps, drawdown, linewidth=0.8, color="#F44336")
ax.set_title("BioNeuronAI Backtest — Drawdown\nBTCUSDT 1h · 2022-01-01 to 2022-12-31", fontsize=12)
ax.set_ylabel("Drawdown (%)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_major_locator(mdates.MonthLocator())
plt.xticks(rotation=30, ha="right")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_DIR / "drawdown.png", dpi=150)
plt.close()
print("Saved drawdown.png")

# ── signal_vs_price.png ───────────────────────────────────────────────────────
# Use equity curve as price proxy (relative) overlaid with BUY/SELL markers
buy_times, buy_prices = [], []
sell_times, sell_prices = [], []
for o in orders:
    receipt = o.get("receipt", {})
    if not receipt.get("accepted"):
        continue
    avg_price = receipt.get("avg_price") or receipt.get("raw", {}).get("avgPrice")
    raw_time = receipt.get("raw", {}).get("time")
    side = o.get("intent", {}).get("side", "")
    if avg_price and raw_time:
        t = datetime.fromtimestamp(int(raw_time) / 1000)
        if side == "BUY":
            buy_times.append(t)
            buy_prices.append(float(avg_price))
        elif side == "SELL":
            sell_times.append(t)
            sell_prices.append(float(avg_price))

# Build a simplified hourly price series from equity (just first 2000 points for clarity)
N = min(2000, len(timestamps))
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(timestamps[:N], equity[:N], linewidth=1, color="#607D8B", alpha=0.6, label="Portfolio equity")
ax2 = ax.twinx()

# Filter buy/sell to first N timestamps window
ts_end = timestamps[N - 1]
bt = [(t, p) for t, p in zip(buy_times, buy_prices) if t <= ts_end]
st = [(t, p) for t, p in zip(sell_times, sell_prices) if t <= ts_end]
if bt:
    bx, by = zip(*bt)
    ax2.scatter(bx, by, marker="^", color="#4CAF50", s=30, zorder=5, label="BUY")
if st:
    sx, sy = zip(*st)
    ax2.scatter(sx, sy, marker="v", color="#F44336", s=30, zorder=5, label="SELL")
ax2.set_ylabel("Fill price (USDT)")
ax.set_ylabel("Equity (USDT)")
ax.set_title("BioNeuronAI — Signal vs Price (first 2000 bars)\nBTCUSDT 1h · 2022-01-01", fontsize=12)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
plt.xticks(rotation=30, ha="right")
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_DIR / "signal_vs_price.png", dpi=150)
plt.close()
print("Saved signal_vs_price.png")

print("All charts generated in", OUT_DIR)
