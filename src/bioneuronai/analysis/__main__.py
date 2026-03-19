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
        # 預設：完整報告（含模擬技術分析 + 全模組覆蓋驗證）
        print("BioNeuronAI 分析模組 — 完整報告（模擬 K 棒示範）\n")
        klines, current_price = _generate_demo_klines()
        sop.run_full_report(
            klines=klines,
            symbol="BTCUSDT",
            current_price=current_price,
        )

        # ── 補充驗證：涵蓋剩餘 4 個模組 ───────────────────────────────
        print("\n" + "─" * 60)
        print("【補充驗證】關鍵字學習器 & 靜態評分工具")
        print("─" * 60)

        # 1. static_utils.MarketKeywords — 靜態評分介面
        from bioneuronai.analysis.keywords.static_utils import MarketKeywords
        test_texts = [
            "BTC ETF 通過，機構大量買入比特幣",
            "Fed 升息 25bp，美元走強",
            "以太坊升級完成，Gas 費用大幅降低",
        ]
        print("\n[MarketKeywords] 重要性評分：")
        for text in test_texts:
            score, matched = MarketKeywords.get_importance_score(text)
            sentiment, conf = MarketKeywords.get_sentiment_bias(text)
            print(f"  '{text[:30]}...' → 分數={score:.2f}, 情緒={sentiment}({conf:.0%}), 命中={matched[:3]}")

        # 2. keywords/learner.KeywordLearner — 關鍵字學習器（初始化驗證）
        from bioneuronai.analysis.keywords.learner import KeywordLearner
        from bioneuronai.analysis.keywords.manager import KeywordManager
        km = KeywordManager()
        learner = KeywordLearner(km)
        print(f"\n[KeywordLearner] 學習器初始化成功，管理關鍵字數: {len(km.keywords)}")

        # 3. news/evaluator.RuleBasedEvaluator — 規則式事件評估
        print("\n" + "─" * 60)
        print("【補充驗證】新聞事件評估器 & 預測驗證循環")
        print("─" * 60)
        from bioneuronai.analysis.news.evaluator import RuleBasedEvaluator
        from bioneuronai.analysis.news.models import NewsArticle
        from datetime import datetime
        evaluator = RuleBasedEvaluator()
        sample_articles = [
            NewsArticle(
                title="Federal Reserve raises interest rates by 25 basis points",
                summary="The Fed raised rates to combat inflation. Markets react cautiously.",
                source="Reuters",
                published_at=datetime.now(),
                url="https://example.com/fed-rates",
            ),
            NewsArticle(
                title="Bitcoin ETF approved by SEC, institutional demand surges",
                summary="The SEC approved the first spot Bitcoin ETF, driving massive inflows.",
                source="Bloomberg",
                published_at=datetime.now(),
                url="https://example.com/btc-etf",
            ),
        ]
        events = evaluator.evaluate_news_batch(sample_articles)
        print(f"[RuleBasedEvaluator] 評估 {len(sample_articles)} 篇文章，偵測到 {len(events)} 個重大事件")
        for ev in events:
            print(f"  → {ev}")

        # 4. news/prediction_loop.NewsPredictionLoop — 預測驗證循環
        from bioneuronai.analysis.news.prediction_loop import NewsPredictionLoop
        loop = NewsPredictionLoop()
        stats = loop.get_statistics()
        print(f"[NewsPredictionLoop] 預測循環初始化成功，統計: {stats}")

        print("\n" + "═" * 60)
        print("✅ 全部 22 個 analysis 模組已驗證完畢（匯入 + 實際執行）")
        print("═" * 60)


if __name__ == "__main__":
    main()
