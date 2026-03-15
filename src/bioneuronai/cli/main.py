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


def cmd_backtest(args: argparse.Namespace) -> None:
    """
    歷史回測命令

    使用 BacktestEngine + MockBinanceConnector 對 AI 推論引擎進行回測。
    需要 binance_historical/ 目錄中的歷史 K 線數據。

    Example:
        python main.py backtest --symbol ETHUSDT --interval 1h
    """
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Backtest  {args.symbol} / {args.interval}")
    print(f"{'='*60}")

    try:
        from backtest import BacktestEngine, BacktestConfig, KlineBar, MockBinanceConnector
        from bioneuronai.core.trading_engine import TradingEngine
    except ImportError as e:
        logger.error("回測模組載入失敗: %s", e)
        logger.error("確認 backtest/ 目錄存在且 TradingEngine 可用")
        sys.exit(1)

    engine_holder: dict = {}

    def ai_strategy(bar: "KlineBar", connector: "MockBinanceConnector") -> None:
        """AI 推論策略 - 每根 K 線呼叫一次"""
        if "engine" not in engine_holder:
            return

        trading_engine: TradingEngine = engine_holder["engine"]
        symbol = bar.symbol
        current_price = bar.close

        klines = connector.data_stream.get_klines_until_now(100)
        if not klines or len(klines) < 20:
            return

        if not (trading_engine.inference_engine and trading_engine.ai_model_loaded):
            return

        try:
            signal = trading_engine.inference_engine.predict(
                symbol=symbol,
                current_price=current_price,
                klines=klines,
            )
            sig_str = signal.signal_type.value
            conf = signal.confidence
            bar_idx = connector.data_stream.state.current_index

            print(
                f"  Bar{bar_idx:4d} | ${current_price:>9.2f} | {sig_str:<15} | {conf:.1%}",
                end="",
            )

            account = connector.get_account_info()
            pos = next(
                (
                    p
                    for p in account["positions"]
                    if p["symbol"] == symbol and abs(p["positionAmt"]) > 0
                ),
                None,
            )

            if "long" in sig_str and (not pos or float(pos["positionAmt"]) <= 0):
                if pos and float(pos["positionAmt"]) < 0:
                    connector.place_order(symbol, "BUY", "MARKET", abs(float(pos["positionAmt"])))
                connector.place_order(symbol, "BUY", "MARKET", 0.05)
                print(" -> LONG")
            elif "short" in sig_str and (not pos or float(pos["positionAmt"]) >= 0):
                if pos and float(pos["positionAmt"]) > 0:
                    connector.place_order(symbol, "SELL", "MARKET", float(pos["positionAmt"]))
                connector.place_order(symbol, "SELL", "MARKET", 0.05)
                print(" -> SHORT")
            else:
                print()

        except Exception as exc:
            logger.warning("AI 推論失敗: %s", exc)

    # 建立 TradingEngine（載入 AI 模型）
    print("\n[1/2] 初始化 TradingEngine ...")
    try:
        te = TradingEngine(testnet=True)
        engine_holder["engine"] = te
        print("      TradingEngine OK")
    except Exception as exc:
        logger.warning("TradingEngine 初始化失敗，以無 AI 模式執行: %s", exc)

    # 建立並執行回測
    print(f"[2/2] 啟動回測  {args.symbol} {args.interval} ...")
    try:
        backtest_engine = BacktestEngine(
            symbol=args.symbol,
            interval=args.interval,
            start_date=args.start_date,
            end_date=getattr(args, "end_date", None),
            initial_balance=args.balance,
        )
        result = backtest_engine.run(ai_strategy)
        _print_backtest_result(result)
    except FileNotFoundError:
        logger.error(
            "找不到 %s / %s 的歷史數據，請先執行 tools/data_download/ 下載",
            args.symbol,
            args.interval,
        )
        sys.exit(1)


def _print_backtest_result(result: object) -> None:
    """顯示回測結果摘要"""
    print(f"\n{'='*60}")
    print("  回測結果")
    print(f"{'='*60}")
    for attr in ("total_return", "sharpe_ratio", "max_drawdown", "win_rate", "total_trades"):
        value = getattr(result, attr, None)
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
    print(f"{'='*60}\n")


# ─────────────────────────────────────────────────────────────────────────────


def cmd_simulate(args: argparse.Namespace) -> None:
    """
    紙交易模擬命令

    使用 MockBinanceConnector.next_tick() 逐 K 線推進，不產生真實訂單。
    需要 binance_historical/ 目錄中的歷史 K 線數據。

    Example:
        python main.py simulate --symbol BTCUSDT --interval 15m --bars 300
    """
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Simulate  {args.symbol} / {args.interval}")
    print(f"{'='*60}")

    try:
        from backtest import MockBinanceConnector
        from bioneuronai.core.trading_engine import TradingEngine
    except ImportError as e:
        logger.error("模擬模組載入失敗: %s", e)
        sys.exit(1)

    print(f"\n  初始資金   : ${args.balance:,.2f}")
    print(f"  模擬 K 線數: {args.bars}")
    print(f"  交易對     : {args.symbol}  週期: {args.interval}\n")

    try:
        te = TradingEngine(testnet=True)
        print("  TradingEngine 已初始化")
    except Exception as exc:
        logger.warning("TradingEngine 初始化失敗（無 AI 模式）: %s", exc)
        te = None

    try:
        mock = MockBinanceConnector(
            symbol=args.symbol,
            interval=args.interval,
            initial_balance=args.balance,
            start_date=getattr(args, "start_date", None),
            end_date=getattr(args, "end_date", None),
        )
    except Exception as exc:
        logger.error("MockBinanceConnector 初始化失敗: %s", exc)
        sys.exit(1)

    bar_count = 0
    print(f"  模擬執行中 ... (限制 {args.bars} 根 K 線)\n")

    # 使用 next_tick() 逐根推進（MockBinanceConnector 的正確接口）
    while mock.next_tick() and bar_count < args.bars:
        bar = mock._current_bar
        if bar is None:
            continue

        bar_count += 1

        if te and te.inference_engine and te.ai_model_loaded:
            try:
                klines = mock.data_stream.get_klines_until_now(50)
                signal = te.inference_engine.predict(
                    symbol=bar.symbol,
                    current_price=bar.close,
                    klines=klines,
                )
                if bar_count % 20 == 0:
                    print(
                        f"  [{bar_count:4d}] ${bar.close:>9.2f}"
                        f"  {signal.signal_type.value:<15}"
                        f"  conf={signal.confidence:.1%}"
                    )
            except Exception:
                if bar_count % 20 == 0:
                    print(f"  [{bar_count:4d}] ${bar.close:>9.2f}  (AI 推論失敗)")
        elif bar_count % 20 == 0:
            print(f"  [{bar_count:4d}] ${bar.close:>9.2f}  (無 AI 模型)")

    acct = mock.get_account_info()
    final_balance = float(acct.get("totalWalletBalance", args.balance))
    pnl = final_balance - args.balance
    stats = mock.virtual_account.get_stats() if hasattr(mock, "virtual_account") else {}
    print(f"\n  {'─'*50}")
    print(f"  最終餘額  : ${final_balance:,.2f}")
    print(f"  PnL       : {pnl:+,.2f} USDT")
    if stats:
        print(f"  總報酬率  : {stats.get('total_return', 0):.2f}%")
        print(f"  總交易次數: {stats.get('total_trades', 0)}")
        print(f"  勝率      : {stats.get('win_rate', 0):.1f}%")
    print(f"  {'─'*50}\n")


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
        engine = TradingEngine(testnet=not use_live)
        print("  TradingEngine 已初始化")

        price_data = engine.get_real_time_price(args.symbol)
        if price_data:
            print(f"  即時價格 [{args.symbol}]: ${price_data.price:.2f}")

        print("\n  按 Ctrl+C 停止交易\n")
        engine.run()

    except KeyboardInterrupt:
        print("\n  交易已停止。")
    except Exception as exc:
        logger.error("交易執行失敗: %s", exc)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────


def cmd_plan(args: argparse.Namespace) -> None:
    """
    每日 SOP 交易計劃命令

    優先使用 TradingPlanController（10 步驟完整計劃），
    若不可用則 fallback 至 SOPAutomationSystem（基礎版）。

    Example:
        python main.py plan
        python main.py plan --output daily_plan.json
    """
    import asyncio

    print(f"\n{'='*60}")
    print("  BioNeuronai Daily Trading Plan  (10-Step SOP)")
    print(f"{'='*60}\n")

    report: Optional[dict] = None

    # ── 優先：TradingPlanController（完整 10 步驟，async）────────────────────
    try:
        from bioneuronai.trading.plan_controller import TradingPlanController

        controller = TradingPlanController()
        print("  [模式] TradingPlanController (10-Step)\n")

        async def _run_plan() -> dict:
            return await controller.create_comprehensive_plan()

        report = asyncio.run(_run_plan())
        print("  [OK] 10 步驟計劃生成完畢")

    except ImportError as e:
        logger.warning("TradingPlanController 不可用，切換至 SOPAutomation: %s", e)
    except Exception as exc:
        logger.warning("TradingPlanController 執行失敗，切換至 SOPAutomation: %s", exc)

    # ── Fallback：SOPAutomationSystem（同步版）───────────────────────────────
    if report is None:
        try:
            from bioneuronai.trading.sop_automation import SOPAutomationSystem

            sop = SOPAutomationSystem()
            print("  [模式] SOPAutomationSystem (基礎版)\n")
            report = sop.execute_daily_premarket_check()
            print("  [OK] 市場分析完畢")
        except ImportError as e:
            logger.error("SOPAutomationSystem 也不可用: %s", e)
            sys.exit(1)
        except Exception as exc:
            logger.error("計劃生成失敗: %s", exc)
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
        from bioneuronai.trading.pretrade_automation import PreTradeCheckSystem
    except ImportError as e:
        logger.error("PreTradeCheckSystem 載入失敗: %s", e)
        sys.exit(1)

    checker = PreTradeCheckSystem()
    print(f"  [START] 執行進場前檢查: {args.symbol} {args.action} ...\n")

    try:
        result = checker.execute_pretrade_check(
            symbol=args.symbol,
            action=args.action,
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
        ("bioneuronai.trading.sop_automation", "SOPAutomationSystem", "SOPSystem"),
        ("bioneuronai.trading.plan_controller", "TradingPlanController", "PlanController"),
        ("bioneuronai.trading.pretrade_automation", "PreTradeCheckSystem", "PreTradeCheck"),
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
    sp.set_defaults(func=cmd_simulate)

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

    # ── status ────────────────────────────────────────────────────────────────
    statp = subparsers.add_parser("status", help="系統健康狀態檢查")
    statp.set_defaults(func=cmd_status)

    return parser


def cli_main(argv: Optional[list] = None) -> None:
    """
    CLI 主入口函數

    Args:
        argv: 命令列參數列表，預設使用 sys.argv[1:]
    """
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
