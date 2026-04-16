#!/usr/bin/env python3
"""
BioNeuronai CLI - 統一命令入口
================================

所有 CLI / UI 相關操作集中於此模組，禁止在其他地方重複定義入口邏輯。

命令總覽:
    backtest  --symbol ETHUSDT --interval 1h --start-date 2025-01-01
    simulate  --symbol BTCUSDT --balance 100000 --bars 200
    trade     --symbol BTCUSDT --testnet
    plan      [--output report.json]
    news      --symbol BTCUSDT --max-items 10
    status

符合 CODE_FIX_GUIDE.md 規範:
    - 程式可運行原則: 此模組含 __main__ 區塊
    - 直接運作驗證原則: 每個命令函數均可獨立驗證
    - 單一數據來源: schema 導入遵循 src/schemas/ 規範
"""

import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Optional

# ── 路徑設定 ────────────────────────────────────────────────────────────────
# 此檔案位於: src/bioneuronai/cli/main.py
# 專案根目錄:  BioNeuronai/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))  # for backtest/ at root level

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# 命令實作
# ══════════════════════════════════════════════════════════════════════════════


def cmd_backtest_data(args: argparse.Namespace) -> None:
    """列出 repo 內可用的歷史回放資料。"""
    print(f"\n{'='*60}")
    print("  BioNeuronai Backtest Data Catalog")
    print(f"{'='*60}\n")

    try:
        from backtest import get_catalog
    except ImportError as exc:
        logger.error("backtest catalog 載入失敗: %s", exc)
        sys.exit(1)

    try:
        catalog = get_catalog(
            data_dir=getattr(args, "data_dir", None),
            symbol=getattr(args, "symbol", None),
            interval=getattr(args, "interval", None),
        )
    except Exception as exc:
        logger.error("歷史資料掃描失敗: %s", exc)
        sys.exit(1)

    if getattr(args, "json", False):
        print(json.dumps(catalog, ensure_ascii=False, indent=2))
        return

    print(f"  資料根目錄: {catalog['root']}")
    print(f"  可用資料組: {catalog['dataset_count']}\n")

    datasets = catalog.get("datasets", [])
    if not datasets:
        print("  找不到任何可用歷史資料。\n")
        return

    for item in datasets:
        print(
            f"  - {item['symbol']:<10} {item['interval']:<6}"
            f"  {item.get('start_date') or 'N/A'} ~ {item.get('end_date') or 'N/A'}"
            f"  | zip={item['zip_count']}"
        )
    print()


# ─────────────────────────────────────────────────────────────────────────────


def cmd_trade(args: argparse.Namespace) -> None:
    """
    實盤 / 測試網交易命令

    在 testnet（預設）或真實網路上執行 AI 交易。
    真實網路需要設定環境變數 BINANCE_API_KEY / BINANCE_API_SECRET。

    Example:
        python main.py trade --testnet
        python main.py trade --live  # 謹慎！
    """
    use_live = getattr(args, "live", False)
    if use_live:
        confirm = input("\n[警告] 即將使用真實網路交易，確認請輸入 YES: ")
        if confirm.strip() != "YES":
            print("已取消。")
            return

    mode = "真實網路" if use_live else "測試網"
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Trade  [{mode}]  {args.symbol}")
    print(f"{'='*60}\n")

    try:
        from bioneuronai.core.trading_engine import TradingEngine
    except ImportError as e:
        logger.error("TradingEngine 載入失敗: %s", e)
        sys.exit(1)

    try:
        import os
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")
        engine = TradingEngine(api_key=api_key, api_secret=api_secret, testnet=not use_live)
        print("  TradingEngine 已初始化")

        price_data = engine.get_real_time_price(args.symbol)
        if price_data:
            print(f"  即時價格 [{args.symbol}]: ${price_data.price:.2f}")

        print("\n  按 Ctrl+C 停止交易\n")
        # TradingEngine 正確入口：start_monitoring(symbol) 內建 WebSocket 監控迴圈
        engine.start_monitoring(args.symbol)

    except KeyboardInterrupt:
        print("\n  交易已停止。")
    except Exception as exc:
        logger.error("交易執行失敗: %s", exc)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────


def cmd_plan(args: argparse.Namespace) -> None:
    """
    每日 SOP 交易計劃命令

    僅使用 TradingPlanController（10 步驟完整計劃）。
    若不可用或執行失敗，直接回報錯誤並停止，不做 legacy fallback。

    Example:
        python main.py plan
        python main.py plan --output daily_plan.json
    """
    import asyncio

    print(f"\n{'='*60}")
    print("  BioNeuronai Daily Trading Plan  (10-Step SOP)")
    print(f"{'='*60}\n")

    # ── 單一路徑：TradingPlanController（完整 10 步驟，async）────────────────
    try:
        from bioneuronai.planning.plan_controller import TradingPlanController

        controller = TradingPlanController()
        print("  [模式] TradingPlanController (10-Step)\n")

        async def _run_plan() -> dict:
            return await controller.create_comprehensive_plan()

        report = asyncio.run(_run_plan())
        print("  [OK] 10 步驟計劃生成完畢")

    except ImportError as e:
        logger.error("TradingPlanController 不可用: %s", e)
        sys.exit(1)
    except Exception as exc:
        logger.error("TradingPlanController 執行失敗: %s", exc)
        sys.exit(1)

    _print_plan_report(report)

    output_path: Optional[str] = getattr(args, "output", None)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"  報告已儲存至: {output_path}")


def _print_plan_report(report: dict) -> None:
    """顯示計劃報告摘要"""
    print(f"  {'─'*50}")
    for key, value in report.items():
        if isinstance(value, dict):
            print(f"  [{key}]")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    print(f"  {'─'*50}\n")


# ─────────────────────────────────────────────────────────────────────────────


def cmd_news(args: argparse.Namespace) -> None:
    """
    新聞情緒分析命令

    擷取最新加密貨幣新聞並進行情緒評分。

    Example:
        python main.py news --symbol BTCUSDT --max-items 5
    """
    print(f"\n{'='*60}")
    print(f"  BioNeuronai News Analysis  {args.symbol}")
    print(f"{'='*60}\n")

    try:
        from bioneuronai.analysis import CryptoNewsAnalyzer
    except ImportError as e:
        logger.error("CryptoNewsAnalyzer 載入失敗: %s", e)
        sys.exit(1)

    analyzer = CryptoNewsAnalyzer()

    try:
        result = analyzer.analyze_news(args.symbol)
        if hasattr(result, "print_news_with_links"):
            result.print_news_with_links(max_items=args.max_items)
        else:
            print(f"  分析結果: {result}")
    except Exception as exc:
        logger.error("新聞分析失敗: %s", exc)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────


def cmd_pretrade(args: argparse.Namespace) -> None:
    """
    進場前檢查命令

    執行 PreTradeCheckSystem 對指定交易對與方向進行技術面、
    基本面、風險參數的完整驗核，確認是否適合進場。

    Example:
        python main.py pretrade --symbol BTCUSDT --action long
        python main.py pretrade --symbol ETHUSDT --action short
    """
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Pre-Trade Check  {args.symbol} / {args.action.upper()}")
    print(f"{'='*60}\n")

    try:
        from bioneuronai.planning.pretrade_automation import PreTradeCheckSystem
    except ImportError as e:
        logger.error("PreTradeCheckSystem 載入失敗: %s", e)
        sys.exit(1)

    checker = PreTradeCheckSystem()
    print(f"  [START] 執行進場前檢查: {args.symbol} {args.action} ...\n")

    try:
        result = checker.execute_pretrade_check(
            symbol=args.symbol,
            intended_action=args.action.upper(),
        )
        _print_pretrade_result(result)

        output_path: Optional[str] = getattr(args, "output", None)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"  結果已儲存至: {output_path}")

    except Exception as exc:
        logger.error("進場前檢查失敗: %s", exc)
        sys.exit(1)


def _print_pretrade_result(result: object) -> None:
    """顯示進場前檢查結果"""
    print(f"  {'─'*50}")
    if isinstance(result, dict):
        for key, value in result.items():
            if isinstance(value, dict):
                print(f"  [{key}]")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
    else:
        # Pydantic model / dataclass
        for attr in ("overall_status", "can_trade", "technical_status",
                     "fundamental_status", "risk_level", "recommended_action"):
            val = getattr(result, attr, None)
            if val is not None:
                print(f"  {attr}: {val}")
    print(f"  {'─'*50}\n")


# ─────────────────────────────────────────────────────────────────────────────


def cmd_evolve(args: argparse.Namespace) -> None:
    """
    策略演化命令（遺傳演算法競技場）

    透過多代遺傳演算法競爭，從策略種群中篩選出最優策略組合。
    結果可輸出至 JSON 檔供後續 trade / backtest 使用。

    Example:
        python main.py evolve
        python main.py evolve --symbol ETHUSDT --generations 20 --population 30
        python main.py evolve --output best_strategy.json
    """
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Evolve  [{args.symbol}]")
    print(f"  種群: {args.population}  代數: {args.generations}")
    print(f"{'='*60}\n")

    try:
        from bioneuronai.strategies.strategy_arena import StrategyArena, ArenaConfig
    except ImportError as e:
        logger.error("StrategyArena 載入失敗: %s", e)
        sys.exit(1)

    try:
        config = ArenaConfig(
            symbol=args.symbol,
            interval=args.interval,
            start_date=args.start_date,
            end_date=args.end_date,
            population_size=args.population,
            max_generations=args.generations,
            warmup_bars=args.warmup_bars,
        )
        arena = StrategyArena(config)
        best = arena.run()

        print(f"\n{'='*60}")
        print(f"  最優策略: {best.name}")
        print(f"  評分:     {best.score:.4f}")
        print(f"  夏普比率: {best.sharpe_ratio:.2f}")
        print(f"  總回報:   {best.total_return * 100:.1f}%")
        print(f"{'='*60}\n")

        if args.output:
            import json
            from pathlib import Path
            result = {
                "name": best.name,
                "strategy_type": best.strategy_type,
                "score": best.score,
                "sharpe_ratio": best.sharpe_ratio,
                "total_return": best.total_return,
                "parameters": best.parameters,
            }
            Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"  結果已儲存至: {args.output}")

    except KeyboardInterrupt:
        print("\n  演化已中止。")
    except Exception as exc:
        logger.error("演化執行失敗: %s", exc)
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:  # noqa: ARG001
    """
    系統健康狀態命令

    依序檢查各模組是否可正常導入，並顯示版本資訊。

    Example:
        python main.py status
    """
    print(f"\n{'='*60}")
    print("  BioNeuronai System Status")
    print(f"{'='*60}\n")

    checks = [
        ("bioneuronai.core.trading_engine", "TradingEngine", "TradingEngine"),
        ("bioneuronai.data.binance_futures", "BinanceFuturesConnector", "BinanceFutures"),
        ("bioneuronai.analysis", "CryptoNewsAnalyzer", "NewsAnalyzer"),
        ("bioneuronai.analysis.daily_report", "SOPAutomationSystem", "SOPSystem"),
        ("bioneuronai.planning.plan_controller", "TradingPlanController", "PlanController"),
        ("bioneuronai.planning.pretrade_automation", "PreTradeCheckSystem", "PreTradeCheck"),
        ("backtest", "BacktestEngine", "BacktestEngine"),
    ]

    all_ok = True
    for module_path, class_name, label in checks:
        try:
            mod = __import__(module_path, fromlist=[class_name])
            getattr(mod, class_name)
            print(f"  [OK] {label}")
        except ImportError as exc:
            print(f"  [--] {label:<20} (ImportError: {exc})")
            all_ok = False
        except AttributeError:
            print(f"  [--] {label:<20} (class not found)")
            all_ok = False

    try:
        import bioneuronai
        print(f"\n  版本: bioneuronai v{bioneuronai.__version__}")
    except Exception:
        pass

    print(f"\n  {'系統正常' if all_ok else '部分模組不可用（詳見上方）'}")
    print(f"{'='*60}\n")


def cmd_chat(args: argparse.Namespace) -> None:
    """
    雙語對話指令：與 BioNeuronai AI 交易助理互動。

    支援繁體中文與英文，可即時注入市場資料。
    輸入 'exit' 或 'quit' 或按 Ctrl+C 結束。

    Example:
        python main.py chat
        python main.py chat --symbol BTCUSDT --language zh
    """
    import sys

    try:
        from nlp.chat_engine import create_chat_engine, MarketContext
    except ImportError:
        print("[錯誤] 無法載入對話引擎，請確認 PyTorch 已安裝且模型存在於 model/ 目錄。")
        print("[Error] Cannot load chat engine. Ensure PyTorch is installed and model exists in model/.")
        sys.exit(1)

    symbol: str = getattr(args, "symbol", "") or ""
    language: str = getattr(args, "language", "auto") or "auto"
    allow_rule_based_fallback: bool = bool(getattr(args, "allow_rule_based_fallback", False))

    print(f"\n{'='*60}")
    print("  BioNeuronai AI 交易助理 / Trading Assistant")
    print(f"  語言模式 / Language: {language}  |  交易對 / Symbol: {symbol or '未設定'}")
    print("  輸入 exit 或 quit 結束 / Type exit or quit to stop")
    print(f"{'='*60}\n")

    engine = create_chat_engine(language=language)
    if engine is None:
        if not allow_rule_based_fallback:
            print("[錯誤] 對話模型未載入；若要使用開發用規則模式，請加上 --allow-rule-based-fallback。")
            print("[Error] Chat model not loaded. Re-run with --allow-rule-based-fallback for development mode.")
            sys.exit(1)
        print("[警告] 模型未載入，已顯式切換到規則型開發模式。")
        print("[Warning] Model not loaded. Entering rule-based development fallback.\n")
        _chat_fallback(symbol)
        return

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再見！/ Goodbye!")
            break

        if user_input.lower() in ("exit", "quit", "bye", "q"):
            print("再見！/ Goodbye!")
            break
        if not user_input:
            continue

        # 市場上下文（若有指定 symbol）
        market_ctx = None
        if symbol:
            market_ctx = MarketContext(symbol=symbol)

        response = engine.chat(user_input, market_ctx)
        print(f"\nAI: {response.text}")
        if response.confidence < 0.5:
            print(f"    [信心值較低: {response.confidence:.0%}，建議再次確認]")
        print()


def _chat_fallback(_symbol: str) -> None:
    """無模型時的簡單問答回退（基於 trading_dialogue_data 關鍵字匹配）"""
    try:
        from nlp.training.trading_dialogue_data import ALL_TRADING_DATA
        qa_map = {item["input"]: item["output"] for item in ALL_TRADING_DATA}
    except ImportError:
        qa_map = {}

    print("[規則模式] / [Rule-based mode]\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再見！/ Goodbye!")
            break
        if user_input.lower() in ("exit", "quit", "bye", "q"):
            print("再見！/ Goodbye!")
            break
        if not user_input:
            continue

        # 簡單關鍵字匹配
        best_match = None
        for question in qa_map:
            if any(kw in user_input for kw in question.split("？")[0].split("?")[0].split()):
                best_match = qa_map[question]
                break

        if best_match:
            print(f"\nAI: {best_match}\n")
        else:
            print("\nAI: 抱歉，我目前無法回答這個問題。請安裝完整模型以獲得更好的回答。\n"
                  "    Sorry, I cannot answer that question. Please install the full model.\n")


def _print_backtest_summary(summary: dict) -> None:
    """顯示 replay service 回傳的回測摘要。"""
    print(f"\n{'='*60}")
    print("  回測結果")
    print(f"{'='*60}")
    stats = summary.get("stats", {})
    for attr in ("total_return", "sharpe_ratio", "max_drawdown", "win_rate", "total_trades"):
        value = stats.get(attr)
        if value is not None:
            label = {
                "total_return": "總報酬率",
                "sharpe_ratio": "夏普比率",
                "max_drawdown": "最大回撤",
                "win_rate": "勝率",
                "total_trades": "總交易次數",
            }.get(attr, attr)
            if isinstance(value, float):
                print(f"  {label:12}: {value:.4f}")
            else:
                print(f"  {label:12}: {value}")


def cmd_backtest(args: argparse.Namespace) -> None:
    """正式 replay backtest CLI，保存 runtime artifacts。"""
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Backtest  {args.symbol} / {args.interval}")
    print(f"{'='*60}")

    try:
        from backtest import run_backtest_summary

        result = run_backtest_summary(
            symbol=args.symbol,
            interval=args.interval,
            balance=args.balance,
            start_date=args.start_date,
            end_date=getattr(args, "end_date", None),
            data_dir=getattr(args, "data_dir", None),
            warmup_bars=args.warmup_bars,
        )
    except FileNotFoundError:
        logger.error(
            "找不到 %s / %s 的歷史數據，請先執行 tools/data_download/ 下載",
            args.symbol,
            args.interval,
        )
        sys.exit(1)
    except Exception as exc:
        logger.error("回測執行失敗: %s", exc)
        sys.exit(1)

    _print_backtest_summary(result)
    print(f"  Run ID      : {result['run_id']}")
    print(f"  Runtime Dir : {result['run_dir']}")
    print(f"{'='*60}\n")


def cmd_simulate(args: argparse.Namespace) -> None:
    """正式 replay simulate CLI，保存 runtime artifacts。"""
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Simulate  {args.symbol} / {args.interval}")
    print(f"{'='*60}")
    print(f"\n  初始資金   : ${args.balance:,.2f}")
    print(f"  模擬 K 線數: {args.bars}")
    print(f"  交易對     : {args.symbol}  週期: {args.interval}\n")

    try:
        from backtest import run_simulation_summary

        result = run_simulation_summary(
            symbol=args.symbol,
            interval=args.interval,
            balance=args.balance,
            bars=args.bars,
            start_date=getattr(args, "start_date", None),
            end_date=getattr(args, "end_date", None),
            data_dir=getattr(args, "data_dir", None),
        )
    except Exception as exc:
        logger.error("模擬執行失敗: %s", exc)
        sys.exit(1)

    final_balance = float(result.get("final_balance", args.balance))
    pnl = final_balance - args.balance
    stats = result.get("stats", {})
    print(f"\n  {'─'*50}")
    print(f"  最終餘額  : ${final_balance:,.2f}")
    print(f"  PnL       : {pnl:+,.2f} USDT")
    print(f"  總報酬率  : {stats.get('total_return', 0):.2f}%")
    print(f"  總交易次數: {stats.get('total_trades', 0)}")
    print(f"  勝率      : {stats.get('win_rate', 0):.1f}%")
    print(f"  Run ID    : {result['run_id']}")
    print(f"  Runtime   : {result['run_dir']}")
    print(f"  {'─'*50}\n")


def cmd_backtest_runs(args: argparse.Namespace) -> None:
    """列出或檢視 replay runtime runs。"""
    try:
        from backtest import get_runtime_run, list_runtime_runs

        if getattr(args, "run_id", None):
            payload = get_runtime_run(args.run_id)
        else:
            payload = list_runtime_runs(limit=args.limit)
    except Exception as exc:
        logger.error("讀取 replay runs 失敗: %s", exc)
        sys.exit(1)

    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if getattr(args, "run_id", None):
        summary = payload.get("summary", {})
        print(f"\n{'='*60}")
        print(f"  Replay Run  {args.run_id}")
        print(f"{'='*60}")
        print(f"  模式       : {summary.get('mode', 'N/A')}")
        print(f"  狀態       : {summary.get('status', 'N/A')}")
        print(f"  交易對     : {summary.get('symbol', 'N/A')} / {summary.get('interval', 'N/A')}")
        print(f"  Runtime    : {payload.get('run_dir', 'N/A')}")
        print(f"  Orders     : {len(payload.get('orders', []))}")
        stats = summary.get("stats", {})
        if stats:
            print(f"  總報酬率  : {stats.get('total_return', 0):.2f}%")
            print(f"  總交易次數: {stats.get('total_trades', 0)}")
        print(f"{'='*60}\n")
        return

    print(f"\n{'='*60}")
    print("  Replay Runtime Runs")
    print(f"{'='*60}")
    for item in payload.get("runs", []):
        print(
            f"  {item.get('run_id', 'N/A')}  "
            f"{item.get('mode', 'N/A'):9}  "
            f"{item.get('symbol', 'N/A'):10}  "
            f"{item.get('interval', 'N/A'):4}  "
            f"{item.get('status', 'N/A')}"
        )
    print(f"{'='*60}\n")


# ══════════════════════════════════════════════════════════════════════════════
# CLI 路由（argparse）
# ══════════════════════════════════════════════════════════════════════════════


def _build_parser() -> argparse.ArgumentParser:
    """建立並回傳 ArgumentParser"""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="BioNeuronai 量化交易系統 - 統一 CLI 入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
命令範例:
  python main.py backtest  --symbol ETHUSDT --interval 1h --start-date 2025-01-01
  python main.py simulate  --symbol BTCUSDT --interval 15m --balance 50000 --bars 300
  python main.py backtest-data --symbol ETHUSDT --interval 1h
  python main.py trade     --testnet
  python main.py plan      --output daily_plan.json
  python main.py news      --symbol BTCUSDT --max-items 5
  python main.py pretrade  --symbol BTCUSDT --action long
  python main.py status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # ── backtest ──────────────────────────────────────────────────────────────
    bp = subparsers.add_parser("backtest", help="歷史數據回測 (MockConnector + AI)")
    bp.add_argument("--symbol", default="ETHUSDT", metavar="SYMBOL",
                    help="交易對  (預設: ETHUSDT)")
    bp.add_argument("--interval", default="1h", metavar="INTERVAL",
                    help="K線週期  (預設: 1h)")
    bp.add_argument("--start-date", default=None, dest="start_date", metavar="YYYY-MM-DD",
                    help="起始日期  (預設: 最早可用)")
    bp.add_argument("--end-date", default=None, dest="end_date", metavar="YYYY-MM-DD",
                    help="結束日期  (預設: 最新可用)")
    bp.add_argument("--balance", type=float, default=10000.0, metavar="AMOUNT",
                    help="初始資金  (預設: 10000)")
    bp.add_argument("--warmup-bars", type=int, default=100, metavar="N",
                    help="預熱 K 線數量  (預設: 100)")
    bp.add_argument("--data-dir", default=None, dest="data_dir", metavar="PATH",
                    help="歷史資料根目錄  (預設: 自動尋找 repo 內資料)")
    bp.set_defaults(func=cmd_backtest)

    # ── simulate ──────────────────────────────────────────────────────────────
    sp = subparsers.add_parser("simulate", help="紙交易模擬 (next_tick 推進，不產生真實訂單)")
    sp.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                    help="交易對  (預設: BTCUSDT)")
    sp.add_argument("--interval", default="15m", metavar="INTERVAL",
                    help="K線週期  (預設: 15m)")
    sp.add_argument("--balance", type=float, default=100000.0, metavar="AMOUNT",
                    help="模擬資金  (預設: 100000)")
    sp.add_argument("--bars", type=int, default=200, metavar="N",
                    help="模擬 K 線數量  (預設: 200)")
    sp.add_argument("--start-date", default=None, dest="start_date", metavar="YYYY-MM-DD",
                    help="起始日期  (可選)")
    sp.add_argument("--end-date", default=None, dest="end_date", metavar="YYYY-MM-DD",
                    help="結束日期  (可選)")
    sp.add_argument("--data-dir", default=None, dest="data_dir", metavar="PATH",
                    help="歷史資料根目錄  (預設: 自動尋找 repo 內資料)")
    sp.set_defaults(func=cmd_simulate)

    # ── backtest-data ────────────────────────────────────────────────────────
    bdp = subparsers.add_parser("backtest-data", help="列出可用歷史回放資料")
    bdp.add_argument("--symbol", default=None, metavar="SYMBOL",
                     help="只顯示指定交易對")
    bdp.add_argument("--interval", default=None, metavar="INTERVAL",
                     help="只顯示指定週期")
    bdp.add_argument("--data-dir", default=None, dest="data_dir", metavar="PATH",
                     help="歷史資料根目錄  (預設: 自動尋找 repo 內資料)")
    bdp.add_argument("--json", action="store_true",
                     help="以 JSON 輸出")
    bdp.set_defaults(func=cmd_backtest_data)

    # ── backtest-runs ────────────────────────────────────────────────────────
    brp = subparsers.add_parser("backtest-runs", help="列出或檢視 replay runtime runs")
    brp.add_argument("--limit", type=int, default=10, metavar="N",
                     help="列出最近 N 筆 runs  (預設: 10)")
    brp.add_argument("--run-id", default=None, metavar="RUN_ID",
                     help="查看指定 run 的詳細資料")
    brp.add_argument("--json", action="store_true",
                     help="以 JSON 輸出")
    brp.set_defaults(func=cmd_backtest_runs)

    # ── trade ─────────────────────────────────────────────────────────────────
    tp = subparsers.add_parser("trade", help="實盤 / 測試網交易")
    tp.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                    help="交易對  (預設: BTCUSDT)")
    tp.add_argument("--testnet", action="store_true", default=True,
                    help="使用測試網  (預設)")
    tp.add_argument("--live", action="store_true",
                    help="使用真實網路  [謹慎！需設定 API 金鑰]")
    tp.set_defaults(func=cmd_trade)

    # ── plan ──────────────────────────────────────────────────────────────────
    pp = subparsers.add_parser("plan", help="生成每日 SOP 交易計劃")
    pp.add_argument("--output", default=None, metavar="FILE",
                    help="輸出 JSON 檔案路徑  (可選)")
    pp.set_defaults(func=cmd_plan)

    # ── news ──────────────────────────────────────────────────────────────────
    np_ = subparsers.add_parser("news", help="新聞情緒分析")
    np_.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                     help="交易對  (預設: BTCUSDT)")
    np_.add_argument("--max-items", type=int, default=10, dest="max_items", metavar="N",
                     help="顯示新聞數量上限  (預設: 10)")
    np_.set_defaults(func=cmd_news)

    # ── pretrade ──────────────────────────────────────────────────────────────
    prtp = subparsers.add_parser("pretrade", help="進場前技術面 / 基本面 / 風險驗核")
    prtp.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                      help="交易對  (預設: BTCUSDT)")
    prtp.add_argument("--action", default="long", choices=["long", "short"],
                      help="交易方向: long / short  (預設: long)")
    prtp.add_argument("--output", default=None, metavar="FILE",
                      help="輸出 JSON 檔案路徑  (可選)")
    prtp.set_defaults(func=cmd_pretrade)

    # ── evolve ────────────────────────────────────────────────────────────────
    ep = subparsers.add_parser("evolve", help="遺傳演算法策略競技場（找出最優策略組合）")
    ep.add_argument("--symbol", default="ETHUSDT", metavar="SYMBOL",
                    help="交易對  (預設: BTCUSDT)")
    ep.add_argument("--interval", default="1h", metavar="INTERVAL",
                    help="K 線週期  (預設: 1h)")
    ep.add_argument("--start-date", default=None, metavar="YYYY-MM-DD",
                    help="開始日期  (可選)")
    ep.add_argument("--end-date", default=None, metavar="YYYY-MM-DD",
                    help="結束日期  (可選)")
    ep.add_argument("--generations", type=int, default=10, metavar="N",
                    help="最大演化代數  (預設: 10)")
    ep.add_argument("--population", type=int, default=20, metavar="N",
                    help="每代種群數量  (預設: 20)")
    ep.add_argument("--warmup-bars", type=int, default=10, metavar="N",
                    help="策略評估預熱 K 線數量  (預設: 10)")
    ep.add_argument("--output", default=None, metavar="FILE",
                    help="輸出最優策略至 JSON 檔案  (可選)")
    ep.set_defaults(func=cmd_evolve)

    # ── status ────────────────────────────────────────────────────────────────
    statp = subparsers.add_parser("status", help="系統健康狀態檢查")
    statp.set_defaults(func=cmd_status)

    # ── chat ──────────────────────────────────────────────────────────────────
    chp = subparsers.add_parser("chat", help="與 AI 交易助理對話（中文 / English）")
    chp.add_argument("--symbol", default="", metavar="SYMBOL",
                     help="交易對（可選，如 BTCUSDT），提供時自動注入即時市場資料")
    chp.add_argument("--language", default="auto", choices=["auto", "zh", "en"],
                     help="回應語言：auto（自動偵測）| zh（繁體中文）| en（英文）  （預設: auto）")
    chp.add_argument("--allow-rule-based-fallback", action="store_true",
                     help="僅供開發模式：若 chat 模型不可用，明確允許退回規則式回應")
    chp.set_defaults(func=cmd_chat)

    return parser


def cli_main(argv: Optional[list] = None) -> None:
    """
    CLI 主入口函數

    Args:
        argv: 命令列參數列表，預設使用 sys.argv[1:]
    """
    # 修正 Windows cp950 終端亂碼：強制 stdout/stderr 使用 UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    parser = _build_parser()
    args = parser.parse_args(argv)
    args.func(args)


# ══════════════════════════════════════════════════════════════════════════════
# 直接執行入口 (符合程式可運行原則)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    cli_main()
