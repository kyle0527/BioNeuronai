"""
幣安 USDT-M 合約交易領域雙語訓練資料
=====================================
涵蓋：
1. 合約基礎概念（槓桿、保證金、資金費率、清算）
2. 訂單類型與使用場景
3. 風險管理規則與計算
4. 常見交易策略問答
5. 系統功能操作問答
6. 市場分析對話

語言：繁體中文 / English / 混合
資料格式與 data_manager.DataSample 相容
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import List, Dict

# 確保 data_manager 可以被 import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nlp.training.data_manager import DataSample, DataGenerator


# ===========================================================================
# 一、合約基礎概念
# ===========================================================================

FUTURES_BASICS: List[Dict] = [
    # --- 永續合約 ---
    {
        "input": "什麼是永續合約？",
        "output": (
            "永續合約（Perpetual Futures）是一種沒有到期日的加密貨幣衍生品。"
            "與傳統期貨不同，它不需要在固定日期交割，持倉者可以無限期持有。"
            "幣安 USDT-M 永續合約以 USDT 計價和結算，是目前交易量最大的加密衍生品之一。"
        ),
    },
    {
        "input": "What is a perpetual futures contract?",
        "output": (
            "A perpetual futures contract is a derivative product with no expiration date. "
            "Unlike traditional futures, there is no fixed settlement date — positions can be held indefinitely. "
            "Binance USDT-M perpetual futures are denominated and settled in USDT, "
            "making them one of the highest-volume crypto derivatives available."
        ),
    },
    # --- 槓桿 ---
    {
        "input": "幣安合約最高可以用多少倍槓桿？",
        "output": (
            "幣安 USDT-M 合約的槓桿上限依幣種而異：\n"
            "• BTCUSDT：最高 125 倍\n"
            "• ETHUSDT：最高 100 倍\n"
            "• 其他主流幣：通常 20–75 倍\n\n"
            "⚠️ 新帳戶（開戶 30 天內）槓桿上限為 20 倍。\n"
            "建議新手使用 3–5 倍槓桿，高槓桿會大幅提高爆倉風險。"
        ),
    },
    {
        "input": "What is the maximum leverage on Binance futures?",
        "output": (
            "Maximum leverage on Binance USDT-M futures depends on the trading pair:\n"
            "• BTCUSDT: up to 125x\n"
            "• ETHUSDT: up to 100x\n"
            "• Most altcoins: 20x–75x\n\n"
            "⚠️ Accounts newer than 30 days are capped at 20x leverage.\n"
            "Beginners should use 3–5x. High leverage dramatically increases liquidation risk."
        ),
    },
    # --- 逐倉 vs 全倉 ---
    {
        "input": "逐倉保證金和全倉保證金有什麼差別？",
        "output": (
            "【逐倉（Isolated Margin）】\n"
            "• 每個倉位使用獨立的保證金，損失上限就是該倉位投入的金額\n"
            "• 爆倉只影響單一倉位，不會波及帳戶其他資金\n"
            "• 適合新手或想嚴格控制單筆風險的交易者\n\n"
            "【全倉（Cross Margin）】\n"
            "• 帳戶所有餘額共同作為所有倉位的保證金\n"
            "• 盈利倉位可以支援虧損倉位，不容易爆倉\n"
            "• 但若市場極端波動，可能損失全部帳戶資金\n"
            "• 適合對倉位管理有經驗的交易者"
        ),
    },
    {
        "input": "What is the difference between isolated margin and cross margin?",
        "output": (
            "[Isolated Margin]\n"
            "• Each position uses its own separate margin — max loss is capped at that amount\n"
            "• Liquidation only affects that specific position, not your entire account\n"
            "• Recommended for beginners or traders who want strict per-trade risk control\n\n"
            "[Cross Margin]\n"
            "• All account balance is shared as margin across all positions\n"
            "• Profitable positions can support losing ones, reducing liquidation frequency\n"
            "• Risk: extreme market moves can wipe the entire account\n"
            "• Better suited for experienced traders managing multiple positions"
        ),
    },
    # --- 資金費率 ---
    {
        "input": "資金費率是什麼？怎麼計算？",
        "output": (
            "資金費率（Funding Rate）是永續合約特有的機制，每 8 小時結算一次，"
            "用來讓合約價格貼近現貨市場：\n\n"
            "• 費率為正 → 多頭（做多方）付給空頭，代表市場偏多頭情緒\n"
            "• 費率為負 → 空頭付給多頭，代表市場偏空頭情緒\n\n"
            "計算方式：\n"
            "  支付金額 = 倉位名義價值 × 資金費率\n\n"
            "例：持有 1 BTC 多單，名義價值 $60,000，費率 0.01%\n"
            "  支付 = 60,000 × 0.0001 = $6（付給空頭方）\n\n"
            "資金費率是影響持倉成本的重要因素，長時間持倉需特別關注。"
        ),
    },
    {
        "input": "How does the funding rate work on Binance futures?",
        "output": (
            "The funding rate is a mechanism unique to perpetual contracts. It settles every 8 hours "
            "to keep the perpetual price aligned with the spot market:\n\n"
            "• Positive rate → long positions pay short positions (bullish market sentiment)\n"
            "• Negative rate → short positions pay long positions (bearish sentiment)\n\n"
            "Calculation:\n"
            "  Payment = Notional Position Value × Funding Rate\n\n"
            "Example: Holding 1 BTC long at $60,000, funding rate = 0.01%\n"
            "  Cost = $60,000 × 0.0001 = $6 (paid to shorts)\n\n"
            "Funding rates significantly impact the cost of holding positions overnight or long-term."
        ),
    },
    # --- 標記價格 ---
    {
        "input": "標記價格和最後成交價有什麼不同？",
        "output": (
            "• 最後成交價（Last Price）：合約市場中最後一筆實際成交的價格，會因短期流動性或操控而波動\n"
            "• 標記價格（Mark Price）：由幣安根據多個主流現貨交易所的價格加權計算，反映公允市場價值\n\n"
            "幣安使用標記價格來：\n"
            "1. 觸發爆倉 → 防止因短暫插針或操控引發不公平清算\n"
            "2. 計算未實現損益\n\n"
            "實際例子：若有人在合約市場砸盤導致最後成交價短暫大跌，"
            "但現貨價格正常，標記價格不變，你的倉位不會被清算。"
        ),
    },
    # --- 爆倉/清算 ---
    {
        "input": "爆倉價格怎麼計算？",
        "output": (
            "逐倉模式下的簡化公式：\n\n"
            "做多爆倉價 ≈ 開倉均價 × (1 - 1/槓桿 + 維持保證金率)\n"
            "做空爆倉價 ≈ 開倉均價 × (1 + 1/槓桿 - 維持保證金率)\n\n"
            "以 BTC 多單為例（開倉價 $60,000，10 倍槓桿，維持保證金率約 0.5%）：\n"
            "  爆倉價 ≈ 60,000 × (1 - 0.1 + 0.005) ≈ $54,300\n\n"
            "⚠️ 實際爆倉價請以幣安介面顯示為準，公式因倉位層級而略有不同。\n"
            "最佳做法：設定止損單，讓系統在爆倉前自動平倉，避免清算手續費（約倉位名義價值的 0.5%）。"
        ),
    },
    {
        "input": "How is the liquidation price calculated?",
        "output": (
            "Simplified formula for isolated margin:\n\n"
            "Long liquidation price ≈ Entry Price × (1 - 1/Leverage + Maintenance Margin Rate)\n"
            "Short liquidation price ≈ Entry Price × (1 + 1/Leverage - Maintenance Margin Rate)\n\n"
            "Example (BTCUSDT long, entry $60,000, 10x leverage, ~0.5% maintenance margin rate):\n"
            "  Liquidation ≈ $60,000 × (1 - 0.1 + 0.005) ≈ $54,300\n\n"
            "⚠️ Always check the exact liquidation price in the Binance interface — it varies by position tier.\n"
            "Best practice: set a stop-loss to close the position before liquidation "
            "and avoid the 0.5% liquidation penalty."
        ),
    },
    # --- ADL ---
    {
        "input": "什麼是 ADL 自動減倉？",
        "output": (
            "ADL（Auto-Deleveraging，自動減倉）是幣安的最後手段機制：\n\n"
            "當某個爆倉訂單的損失超過保險基金能承擔的範圍時，"
            "幣安會強制對盈利方向的持倉者部分平倉，來彌補虧損方的缺口。\n\n"
            "被 ADL 的條件（排名越靠前越容易被選中）：\n"
            "• 盈利越高\n"
            "• 槓桿使用越高\n\n"
            "⚠️ 被 ADL 不收手續費，但會強制以破產價格（Bankruptcy Price）平倉，"
            "即使你的倉位是盈利的。\n\n"
            "幣安介面有 ADL 風險燈，顯示你目前被 ADL 的機率，建議定期檢查。"
        ),
    },
]


# ===========================================================================
# 二、訂單類型
# ===========================================================================

ORDER_TYPES: List[Dict] = [
    {
        "input": "市價單和限價單的差別是什麼？什麼情況用哪個？",
        "output": (
            "【市價單（Market Order）】\n"
            "• 以當前最優市場價格立即成交\n"
            "• 優點：保證成交，速度快\n"
            "• 缺點：滑點（高波動時實際成交價可能偏差較大）\n"
            "• 適用：急需進出場、追急漲急跌、重要消息公布後\n\n"
            "【限價單（Limit Order）】\n"
            "• 指定價格掛單，只在達到指定價格時成交\n"
            "• 優點：控制進場價格，有機會享有 Maker 手續費優惠\n"
            "• 缺點：若價格未到達，訂單不會成交\n"
            "• 適用：有耐心等待理想進場點、量化策略掛單"
        ),
    },
    {
        "input": "What is a stop-market order and when should I use it?",
        "output": (
            "A stop-market order has two parts:\n"
            "1. Stop price — triggers the order\n"
            "2. Market order — executes immediately after trigger\n\n"
            "How it works: when the mark price reaches your stop price, "
            "a market order is placed automatically.\n\n"
            "Best used for:\n"
            "• Stop-loss protection — exit quickly when price moves against you\n"
            "• Breakout entries — enter long when price breaks above resistance\n\n"
            "⚠️ The execution price is not guaranteed after trigger. "
            "In fast markets, slippage can occur. "
            "For tighter price control, use a stop-limit order instead."
        ),
    },
    {
        "input": "追蹤止損單怎麼用？",
        "output": (
            "追蹤止損單（Trailing Stop）會隨著價格朝有利方向移動而自動調整止損位：\n\n"
            "• 做多時：止損點隨價格上漲而上移，但價格下跌時止損點不變\n"
            "• 做空時：止損點隨價格下跌而下移，但價格上漲時止損點不變\n\n"
            "設定參數：\n"
            "• 回調距離（Callback Rate）：通常設 1–3%\n\n"
            "使用場景：\n"
            "• 趨勢行情中希望讓利潤奔跑，同時保護已有獲利\n"
            "• 不想盯盤，讓系統自動追蹤\n\n"
            "範例：BTC 從 $60,000 做多，設 2% 追蹤止損。\n"
            "BTC 漲到 $65,000，止損跟到 $63,700（65,000 × 0.98）。\n"
            "之後 BTC 跌到 $63,700，自動平倉，鎖定利潤。"
        ),
    },
    {
        "input": "止損限價單和止損市價單哪個比較好？",
        "output": (
            "【止損市價單（Stop-Market）】\n"
            "✓ 保證觸發後一定成交\n"
            "✗ 成交價格不確定（極端行情可能嚴重滑點）\n\n"
            "【止損限價單（Stop-Limit）】\n"
            "✓ 可以控制最差成交價格\n"
            "✗ 若市場跳空（Gap），價格越過限價而不成交，止損失效\n\n"
            "建議：\n"
            "• 一般行情：止損限價單（設稍微寬鬆的限價，如止損價再下移 0.1%）\n"
            "• 重大消息、極端波動：止損市價單（確保成交優先）\n"
            "• 最穩健做法：同時設置止損市價單作為最後防線"
        ),
    },
]


# ===========================================================================
# 三、風險管理
# ===========================================================================

RISK_MANAGEMENT: List[Dict] = [
    {
        "input": "一筆交易應該承擔多少風險？",
        "output": (
            "業界標準建議：每筆交易風險不超過帳戶總資金的 1–2%。\n\n"
            "以 $10,000 帳戶為例（風險設定 1%）：\n"
            "• 每筆最大損失 = $100\n"
            "• 若止損距離為 2%（即價格下跌 2% 就止損）\n"
            "• 倉位大小 = 100 ÷ 0.02 = $5,000 名義價值\n\n"
            "這種方式即使連續虧損 10 筆，帳戶仍有約 $9,044（虧損 <10%）。\n\n"
            "⚠️ 高槓桿不等於大風險，關鍵是控制每筆的倉位大小。"
        ),
    },
    {
        "input": "What is a good risk-reward ratio for futures trading?",
        "output": (
            "A minimum risk-reward ratio (RRR) of 1:2 is the industry standard baseline — "
            "meaning for every $1 you risk, you aim to make $2.\n\n"
            "Common setups:\n"
            "• Conservative: 1:2 RRR (e.g., stop-loss 2%, take-profit 4%)\n"
            "• Moderate: 1:3 RRR (stop 1.5%, target 4.5%)\n"
            "• Aggressive trend trades: 1:5 or higher\n\n"
            "Even with a 40% win rate, a 1:2 RRR strategy is profitable:\n"
            "  40 wins × $2 = $80 profit\n"
            "  60 losses × $1 = $60 loss\n"
            "  Net = +$20\n\n"
            "BioNeuronai's default minimum RRR is configurable in RiskParameters."
        ),
    },
    {
        "input": "R倍數是什麼？",
        "output": (
            "R 倍數（R-Multiple）是衡量交易結果相對於初始風險的指標：\n\n"
            "  R = 實際損益 ÷ 初始風險金額\n\n"
            "範例：初始風險 $100\n"
            "• 獲利 $250 → +2.5R\n"
            "• 虧損 $100（觸及止損）→ -1R\n"
            "• 虧損 $200（未止損）→ -2R（不良習慣）\n\n"
            "使用 R 倍數的好處：\n"
            "• 可以比較不同倉位大小的交易績效\n"
            "• 目標是長期平均 R > 1（每筆交易期望值為正）\n"
            "• BioNeuronai 系統會自動追蹤每筆交易的 R 倍數"
        ),
    },
    {
        "input": "什麼時候不應該交易？",
        "output": (
            "以下情況建議暫停交易：\n\n"
            "1. 重大新聞發布前後 — 美聯儲利率決議、CPI、非農數據、幣圈重大監管消息\n"
            "2. 市場極端波動期（恐慌指數極高）\n"
            "3. 流動性不足的深夜時段（滑點風險增加）\n"
            "4. 連續虧損後情緒受影響時\n"
            "5. 倉位已達最大風險限制\n\n"
            "BioNeuronai 的 PhaseRouter 和 PreTradeCheckSystem 會自動偵測以上情況，"
            "在高風險環境下限制或停止自動交易。"
        ),
    },
    {
        "input": "How do I calculate position size on Binance futures?",
        "output": (
            "Position size formula:\n\n"
            "  Contract Quantity = (Account Balance × Risk %) ÷ (Entry Price × Stop Loss %)\n\n"
            "Example:\n"
            "  Account: $10,000 | Risk: 1% ($100)\n"
            "  BTC entry: $60,000 | Stop-loss: 2% below entry ($58,800)\n\n"
            "  Quantity = $100 ÷ ($60,000 × 0.02) = $100 ÷ $1,200 = 0.0833 BTC\n"
            "  Notional value = 0.0833 × $60,000 = $5,000\n\n"
            "With 10x leverage, required margin = $5,000 ÷ 10 = $500\n\n"
            "BioNeuronai's TradingEngine._calculate_position_size() handles this automatically."
        ),
    },
]


# ===========================================================================
# 四、交易策略問答
# ===========================================================================

STRATEGY_QA: List[Dict] = [
    {
        "input": "趨勢跟隨策略的核心邏輯是什麼？",
        "output": (
            "趨勢跟隨策略（Trend Following）的核心原則：\n\n"
            "「順勢而為，讓利潤奔跑，快速止損」\n\n"
            "進場條件（做多範例）：\n"
            "• 短期均線（如 EMA21）在長期均線（EMA55、EMA200）之上\n"
            "• ADX > 25（趨勢強度足夠）\n"
            "• MACD 多頭排列\n"
            "• 在回撤時進場而非追高\n\n"
            "出場邏輯：\n"
            "• 止損設在近期支撐位或 ATR 的 1.5–2 倍以下\n"
            "• 分批止盈（TP1 = 1R, TP2 = 2R, TP3 = 讓利潤跑）\n"
            "• 均線交叉走壞時平倉\n\n"
            "最適合的市場：強趨勢行情（避開震盪盤整期）"
        ),
    },
    {
        "input": "均值回歸策略在什麼情況下有效？",
        "output": (
            "均值回歸策略（Mean Reversion）適用條件：\n\n"
            "✅ 適合的市場環境：\n"
            "• 盤整震盪市（無明顯趨勢）\n"
            "• 低波動率環境\n"
            "• 布林通道擠壓（Squeeze）後剛釋放\n\n"
            "進場信號（做多範例）：\n"
            "• 價格觸及布林帶下軌（BB %B < 0）\n"
            "• RSI < 30（超賣）\n"
            "• Z-Score < -2（偏離均值 2 個標準差）\n"
            "• 出現看漲反轉 K 棒（錘頭、吞噬）\n\n"
            "❌ 避免使用的情況：\n"
            "• 強趨勢行情（STRONG_UPTREND / STRONG_DOWNTREND）\n"
            "• 重大消息發布前後"
        ),
    },
    {
        "input": "What is the Direction Change strategy?",
        "output": (
            "The Direction Change (DC) strategy is an event-driven approach "
            "based on detecting significant price reversals:\n\n"
            "Core concept:\n"
            "• Identifies 'DC events' — price moves that exceed a defined threshold (e.g., 1% ATR)\n"
            "• Classifies market phases: upturn, downturn, and OS (overshoot) retracements\n\n"
            "Entry conditions:\n"
            "• Wait for a confirmed DC event (direction change confirmed)\n"
            "• Enter during the OS (retracement) phase for better risk-reward\n"
            "• Confirm with volume and momentum indicators\n\n"
            "Strengths:\n"
            "• Works in both trending and volatile markets\n"
            "• Captures reversals early with tight stops\n\n"
            "This is one of the 5 strategies in BioNeuronai's AIStrategyFusion."
        ),
    },
    {
        "input": "突破策略怎麼判斷假突破？",
        "output": (
            "假突破（Fakeout）的識別方法：\n\n"
            "真突破特徵：\n"
            "• 收盤價明顯突破關鍵位（不只是影線穿過）\n"
            "• 伴隨成交量放大（通常是均量的 1.5 倍以上）\n"
            "• 突破後有回測該位置支撐（再確認）\n\n"
            "假突破特徵：\n"
            "• 突破後迅速拉回到區間內\n"
            "• 成交量沒有明顯放大\n"
            "• 突破發生在流動性差的時段\n"
            "• K 棒收盤回到突破位以下\n\n"
            "應對方式：\n"
            "• 等待突破後的回測確認再進場\n"
            "• 止損設在突破位以下，不要追高\n"
            "• 過濾掉成交量不足的突破信號"
        ),
    },
]


# ===========================================================================
# 五、BioNeuronai 系統功能說明
# ===========================================================================

SYSTEM_FEATURES: List[Dict] = [
    {
        "input": "BioNeuronai 是什麼？有什麼功能？",
        "output": (
            "BioNeuronai 是一套 AI 驅動的幣安 USDT-M 永續合約自動交易系統，主要功能包括：\n\n"
            "【策略層】\n"
            "• 5 種基礎策略：趨勢跟隨、擺動交易、均值回歸、突破、方向轉換\n"
            "• AIStrategyFusion：多策略 AI 融合（5 種融合方式）\n"
            "• PhaseRouter：依市場時段自動切換策略\n\n"
            "【AI 層】\n"
            "• 100M 參數推論模型（分析 1024 維市場特徵）\n"
            "• NLP 新聞情緒分析（RAG 知識庫）\n"
            "• 三模態動態融合：策略(65%) + AI推論(25%) + 新聞(10%)\n\n"
            "【工具層】\n"
            "• 歷史回測引擎（含 Sharpe / Sortino / Calmar 統計）\n"
            "• 遺傳演算法策略優化\n"
            "• 交易前風險檢查系統\n"
            "• REST API + CLI 介面"
        ),
    },
    {
        "input": "How do I start backtesting with BioNeuronai?",
        "output": (
            "To run a backtest with BioNeuronai, use the CLI:\n\n"
            "  python main.py backtest --symbol BTCUSDT --interval 1h \\\n"
            "    --start-date 2024-01-01 --end-date 2024-12-31 \\\n"
            "    --balance 10000 --warmup-bars 200\n\n"
            "Or via the REST API:\n"
            "  POST /api/v1/backtest/run\n"
            "  { 'symbol': 'BTCUSDT', 'interval': '1h', 'initial_balance': 10000 }\n\n"
            "Available intervals: 1m, 5m, 15m, 1h, 4h, 1d\n\n"
            "Results include:\n"
            "• Total return, max drawdown, Sharpe / Sortino / Calmar ratios\n"
            "• Trade-by-trade order history (orders.jsonl)\n"
            "• Equity curve and summary statistics"
        ),
    },
    {
        "input": "如何查看目前的系統狀態？",
        "output": (
            "可以用以下方式檢查 BioNeuronai 系統狀態：\n\n"
            "【CLI】\n"
            "  python main.py status\n\n"
            "【REST API】\n"
            "  GET /api/v1/status\n"
            "  回傳各模組可用性：策略、AI推論、新聞分析、資料庫等\n\n"
            "【主要模組狀態指標】\n"
            "• strategy_selector：策略選擇器\n"
            "• inference_engine：AI 推論引擎（需要 PyTorch + 已訓練模型）\n"
            "• news_analyzer：新聞情緒分析\n"
            "• rag_checker：RAG 交易前檢查\n"
            "• database：交易記錄資料庫"
        ),
    },
    {
        "input": "三模態融合是怎麼運作的？",
        "output": (
            "BioNeuronai 使用三模態動態加權融合來決定最終交易信號：\n\n"
            "【三個模態】\n"
            "1. 策略信號（65%）：5 種技術分析策略的融合結果\n"
            "2. AI 推論（25%）：100M 神經網路分析 1024 維市場特徵\n"
            "3. 新聞情緒（10%）：NLP 新聞分析的情緒分數\n\n"
            "【動態調整】\n"
            "依市場 Regime 自動切換權重：\n"
            "• 強趨勢：策略 70% / AI 25% / 新聞 5%\n"
            "• 震盪盤整：策略 50% / AI 40% / 新聞 10%\n"
            "• 高波動：策略 45% / AI 40% / 新聞 15%\n"
            "• 新聞事件：策略 35% / AI 35% / 新聞 30%\n\n"
            "一致信號（策略和 AI 方向相同）會額外加成信心值（+5%，上限 95%）。"
        ),
    },
]


# ===========================================================================
# 六、市場分析對話
# ===========================================================================

MARKET_ANALYSIS: List[Dict] = [
    {
        "input": "RSI 怎麼看？超買超賣怎麼用？",
        "output": (
            "RSI（相對強弱指數）衡量一段時間內漲跌的相對強度，範圍 0–100：\n\n"
            "• RSI > 70：超買區域，可能面臨回調\n"
            "• RSI < 30：超賣區域，可能出現反彈\n"
            "• RSI = 50：中性，多空平衡\n\n"
            "進階用法：\n"
            "• 背離（Divergence）：價格創新高但 RSI 未創新高 → 看跌背離，注意轉折\n"
            "• 強勢市場：RSI 常在 40–80 震盪，超賣線應改用 40\n"
            "• 弱勢市場：RSI 常在 20–60 震盪，超買線應改用 60\n\n"
            "⚠️ 在強趨勢中，RSI 可以長期維持超買/超賣狀態，不能單獨作為進出場依據。"
        ),
    },
    {
        "input": "What does a MACD crossover signal mean?",
        "output": (
            "MACD (Moving Average Convergence Divergence) crossover signals:\n\n"
            "Bullish crossover (buy signal):\n"
            "• MACD line crosses above the signal line\n"
            "• Especially significant when occurring below the zero line\n"
            "• Stronger when confirmed by histogram turning positive\n\n"
            "Bearish crossover (sell signal):\n"
            "• MACD line crosses below the signal line\n"
            "• More reliable when above the zero line\n\n"
            "Important notes:\n"
            "• MACD is a lagging indicator — use it for trend confirmation, not early entry\n"
            "• In choppy markets, MACD generates many false signals\n"
            "• Combine with price action (support/resistance) for better accuracy\n\n"
            "BioNeuronai's TrendFollowingStrategy uses EMA(12/26) MACD as a core filter."
        ),
    },
    {
        "input": "布林通道怎麼用於交易？",
        "output": (
            "布林通道（Bollinger Bands）由三條線組成：\n"
            "• 中軌：20 期移動平均線\n"
            "• 上軌：中軌 + 2 倍標準差\n"
            "• 下軌：中軌 - 2 倍標準差\n\n"
            "主要應用：\n\n"
            "1. 均值回歸（Squeeze 策略）\n"
            "   • 帶寬收窄（Squeeze）→ 即將出現大行情\n"
            "   • 帶寬突然放大 → 行情啟動，跟隨方向\n\n"
            "2. 超買超賣\n"
            "   • 收盤價突破上軌 → 可能超買（注意回調）\n"
            "   • 收盤價突破下軌 → 可能超賣（注意反彈）\n\n"
            "3. 趨勢確認\n"
            "   • 多頭行情中，價格沿上軌運行（走帶狀）\n"
            "   • 空頭行情中，價格沿下軌運行\n\n"
            "BioNeuronai 的 MeanReversionStrategy 使用 BB %B 和 Squeeze 指標作為核心信號。"
        ),
    },
    {
        "input": "資金費率很高是什麼意思？應該怎麼做？",
        "output": (
            "資金費率解讀：\n\n"
            "【費率偏高（> 0.05%）】\n"
            "→ 多頭情緒過熱，市場過度槓桿化做多\n"
            "→ 做多者每 8 小時需持續付出成本\n"
            "→ 歷史上高費率往往對應價格頂部區域\n"
            "→ 注意做多成本，可能有回調壓力\n\n"
            "【費率偏低/負值（< -0.01%）】\n"
            "→ 空頭情緒過濃，市場超賣\n"
            "→ 做空者持續付費，空頭套牢壓力大\n"
            "→ 可能對應底部區域，注意多頭機會\n\n"
            "【策略運用】\n"
            "• 高資金費率下避免新開多單或縮小多倉\n"
            "• 考慮資金費率套利：現貨做多 + 合約做空（對沖費率收益）\n"
            "• BioNeuronai AI 模型將資金費率納入 1024 維特徵向量中"
        ),
    },
]


# ===========================================================================
# 組合與導出
# ===========================================================================

ALL_TRADING_DATA: List[Dict] = (
    FUTURES_BASICS
    + ORDER_TYPES
    + RISK_MANAGEMENT
    + STRATEGY_QA
    + SYSTEM_FEATURES
    + MARKET_ANALYSIS
)


def generate_trading_samples(count: int = -1) -> List[DataSample]:
    """
    生成交易領域訓練樣本。

    Args:
        count: 要生成的樣本數，-1 表示返回所有樣本（含隨機增強）

    Returns:
        List[DataSample]，與 data_manager 格式相容
    """
    gen = DataGenerator()
    samples: List[DataSample] = []

    pool = ALL_TRADING_DATA.copy()

    # 基礎樣本（全部）
    for item in pool:
        samples.append(DataSample(
            id=gen.generate_id(),
            type="conversation",
            category="trading",
            input_text=item["input"],
            output_text=item["output"],
            metadata={"domain": "binance_futures"},
        ))

    # 若需要更多，隨機抽樣並輕微改寫問法
    if count > len(samples):
        extra_needed = count - len(samples)
        question_prefixes_zh = ["請問", "幫我解釋", "說明一下", "能告訴我"]
        question_prefixes_en = ["Can you explain", "Please tell me about", "What is", "How does"]

        for _ in range(extra_needed):
            item = random.choice(pool)
            lang = "zh" if any("\u4e00" <= c <= "\u9fff" for c in item["input"]) else "en"
            if lang == "zh":
                prefix = random.choice(question_prefixes_zh)
                new_input = f"{prefix}{item['input'].lstrip('什麼是請問').strip('？?')}"
            else:
                prefix = random.choice(question_prefixes_en)
                new_input = f"{prefix} {item['input'].lstrip('What is').strip('?').strip()}"

            samples.append(DataSample(
                id=gen.generate_id(),
                type="conversation",
                category="trading",
                input_text=new_input,
                output_text=item["output"],
                metadata={"domain": "binance_futures", "augmented": True},
            ))

    if count == -1:
        return samples
    return samples[:count]


def get_sample_count() -> Dict[str, int]:
    """回傳各類別樣本數量統計"""
    return {
        "futures_basics":   len(FUTURES_BASICS),
        "order_types":      len(ORDER_TYPES),
        "risk_management":  len(RISK_MANAGEMENT),
        "strategy_qa":      len(STRATEGY_QA),
        "system_features":  len(SYSTEM_FEATURES),
        "market_analysis":  len(MARKET_ANALYSIS),
        "total":            len(ALL_TRADING_DATA),
    }


if __name__ == "__main__":
    stats = get_sample_count()
    print("=== 交易領域訓練資料統計 ===")
    for k, v in stats.items():
        print(f"  {k}: {v} 筆")
    samples = generate_trading_samples()
    print(f"\n總樣本數（含原始）: {len(samples)}")
    print("\n範例樣本：")
    s = random.choice(samples)
    print(f"  ID: {s.id}")
    print(f"  語言: {s.language}")
    print(f"  輸入: {s.input_text[:60]}...")
    print(f"  輸出: {s.output_text[:80]}...")
