"""
BioNeuronAI 分析模組 — 完整報告入口
=====================================

以模擬 K 棒資料執行完整分析報告示範。

使用方式：
    python -m bioneuronai.analysis           # 全套報告（含模擬技術分析）
    python -m bioneuronai.analysis --sop     # 僅執行 SOP 每日流程
    python -m bioneuronai.analysis --kw      # 僅執行關鍵字報告

注意：
    此模組作為示範入口，技術分析部分使用隨機模擬 K 棒。
    實際使用時請透過交易所連接器取得真實 K 棒後呼叫：
        sop = SOPAutomationSystem()
        sop.run_full_report(klines=real_klines, symbol="BTCUSDT", current_price=price)
"""

import random
import sys
from dataclasses import dataclass

from bioneuronai.analysis.daily_report import SOPAutomationSystem


# ──────────────────────────────────────────────────────────────
# 示範用 K 棒（僅供 __main__ 使用，不屬於生產代碼）
# ──────────────────────────────────────────────────────────────

@dataclass
class _DemoKline:
    """示範用模擬 K 棒（包含 VolumeProfileCalculator 所需屬性）"""
    symbol: str
    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    taker_buy_volume: float


def _generate_demo_klines(
    symbol: str = "BTCUSDT",
    n: int = 300,
    base_price: float = 95_000.0,
    seed: int = 42
):
    """
    生成模擬 K 棒資料（用於示範技術分析功能）

    Args:
        symbol: 交易對符號
        n: K 棒數量
        base_price: 起始價格
        seed: 隨機種子（固定可重現）

    Returns:
        (klines: List[_DemoKline], final_price: float)
    """
    rng = random.Random(seed)
    price = base_price
    klines = []

    for i in range(n):
        ret = rng.gauss(0.0003, 0.008)   # 微幅向上偏移
        price *= (1 + ret)
        high = price * (1 + abs(rng.gauss(0, 0.003)))
        low  = price * (1 - abs(rng.gauss(0, 0.003)))
        vol  = rng.uniform(500, 2500)
        klines.append(_DemoKline(
            symbol=symbol,
            open_time=i * 900_000,
            close_time=(i + 1) * 900_000 - 1,
            open=low + (high - low) * rng.random(),
            high=high,
            low=low,
            close=price,
            volume=vol,
            taker_buy_volume=vol * rng.uniform(0.35, 0.65),
        ))

    return klines, price


# ──────────────────────────────────────────────────────────────
# 入口點
# ──────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    sop  = SOPAutomationSystem()

    if "--sop" in args:
        # 僅執行 SOP 每日流程（不含技術分析）
        print("BioNeuronAI — SOP 每日市場分析\n")
        sop.run_full_report()

    elif "--kw" in args:
        # 僅執行關鍵字報告
        print("BioNeuronAI — 關鍵字系統報告\n")
        from bioneuronai.analysis.keywords.manager import KeywordManager
        km = KeywordManager()
        km.print_report()

    else:
        # 預設：完整報告（含模擬技術分析）
        print("BioNeuronAI 分析模組 — 完整報告（模擬 K 棒示範）\n")
        klines, current_price = _generate_demo_klines()
        sop.run_full_report(
            klines=klines,
            symbol="BTCUSDT",
            current_price=current_price,
        )


if __name__ == "__main__":
    main()
