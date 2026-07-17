#!/usr/bin/env python3
"""
BioNeuronai CLI - 統一命令入口
================================

所有 CLI / UI 相關操作集中於此模組，禁止在其他地方重複定義入口邏輯。

命令總覽:
    backtest  --symbol ETHUSDT --interval 1h --start-date 2025-01-01
    strategy-backtest --symbol BTCUSDT --interval 1h
    readiness-gate --dry-run
    simulate  --symbol BTCUSDT --balance 100000 --bars 200
    trade     --symbol BTCUSDT --testnet
    autonomous --mode advisor --symbol BTCUSDT
    plan      [--output report.json]
    news      --symbol BTCUSDT --max-items 10
    status

符合 CODE_FIX_GUIDE.md 規範:
    - 程式可運行原則: 此模組含 __main__ 區塊
    - 直接運作驗證原則: 每個命令函數均可獨立驗證
    - 單一數據來源: schema 導入遵循 src/schemas/ 規範
"""

import argparse
import json
import logging
import sys
from datetime import datetime
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

    datasets_value = catalog.get("datasets", [])
    datasets = datasets_value if isinstance(datasets_value, list) else []
    if not datasets:
        print("  找不到任何可用歷史資料。\n")
        return

    for item in datasets:
        if not isinstance(item, dict):
            continue
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
    use_paper_live = getattr(args, "paper_live", False)
    auto_trade = bool(getattr(args, "auto_trade", False) or use_paper_live)

    if use_live and use_paper_live:
        logger.error("--live 與 --paper-live 不可同時使用")
        sys.exit(1)

    if use_live:
        confirm = input("\n[警告] 即將使用真實網路交易，確認請輸入 YES: ")
        if confirm.strip() != "YES":
            print("已取消。")
            return

    if use_paper_live:
        mode = "虛擬實盤（主網行情 / 本機虛擬成交）"
    else:
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
        engine = TradingEngine(
            api_key=api_key,
            api_secret=api_secret,
            testnet=not use_live,
            enable_ai_model=getattr(args, "load_ai_model", True),
            paper_trading=use_paper_live,
            paper_initial_balance=float(getattr(args, "paper_balance", 10000.0)),
        )
        print("  TradingEngine 已初始化")
        if auto_trade:
            engine.enable_auto_trading()
            print("  自動交易: 已啟用")
        else:
            engine.disable_auto_trading()
            print("  自動交易: 未啟用（僅監控）")

        model_name = getattr(args, "model_name", "unified_v2_100m")
        if getattr(args, "load_ai_model", True):
            if engine.load_ai_model(model_name, warmup=getattr(args, "warmup_model", False)):
                print(f"  AI 模型已載入: {model_name}")
            else:
                print(f"  [WARN] AI 模型載入失敗: {model_name}")

        price_data = engine.get_real_time_price(args.symbol)
        if price_data:
            print(f"  即時價格 [{args.symbol}]: ${price_data.price:.2f}")

        if use_paper_live:
            paper_state: dict[str, object] = getattr(
                engine.connector,
                "get_paper_state",
                lambda: {},
            )()
            print(f"  Paper Log: {paper_state.get('log_dir', 'N/A')}")

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
        klines = _load_plan_klines(args)
        account_balance = float(getattr(args, "balance", 10000.0))
        symbol = getattr(args, "symbol", "BTCUSDT")

        async def _run_plan() -> dict:
            return await controller.create_comprehensive_plan(
                klines=klines,
                account_balance=account_balance,
                symbol=symbol,
            )

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


def _load_plan_klines(args: argparse.Namespace) -> list[dict]:
    """從正式 replay 資料根目錄載入 plan 所需的最近 K 線。"""
    symbol = getattr(args, "symbol", "BTCUSDT")
    interval = getattr(args, "interval", "1h")
    limit = int(getattr(args, "klines_limit", 300))
    data_dir = getattr(args, "data_dir", None)

    try:
        from backtest import DEFAULT_DATA_DIR, HistoricalDataStream

        stream = HistoricalDataStream(
            symbol=symbol,
            interval=interval,
            data_dir=data_dir or DEFAULT_DATA_DIR,
            speed_multiplier=0,
        )
        target_open_time = int(datetime.now().timestamp() * 1000)
        klines = stream.get_klines_until_time(target_open_time, limit=limit)
        if klines:
            print(f"  K線資料: {symbol} {interval} / {len(klines)} bars\n")
        else:
            print(f"  [WARN] 找不到 K線資料: {symbol} {interval}\n")
        return klines
    except Exception as exc:
        logger.warning("plan K線資料載入失敗: %s", exc)
        print(f"  [WARN] K線資料載入失敗: {exc}\n")
        return []


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

    checker = PreTradeCheckSystem(account_balance=args.balance)
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


def cmd_autonomous(args: argparse.Namespace) -> None:
    """Run autonomous observe-plan-pretrade-adapt cycle(s); --cycles >1 進入持續閉環."""
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Autonomous Run  [{args.mode}]  {args.symbol}")
    print(f"{'='*60}\n")

    try:
        from bioneuronai.planning.autonomous_operator import (
            AutonomousOperator,
            AutonomousOperatorConfig,
        )
    except ImportError as exc:
        logger.error("AutonomousOperator 載入失敗: %s", exc)
        sys.exit(1)

    config = AutonomousOperatorConfig(
        mode=args.mode,
        symbol=args.symbol,
        intended_action=args.action,
        interval=args.interval,
        account_balance=float(args.balance),
        klines_limit=int(args.klines_limit),
        max_pairs=int(args.max_pairs),
        data_dir=args.data_dir,
        ledger_path=args.ledger_path,
        execute_paper=bool(args.execute_paper),
        paper_initial_balance=float(args.paper_balance),
        paper_notional_fraction=float(args.paper_notional_fraction),
        max_position_hold_cycles=int(getattr(args, "max_position_hold_cycles", 0) or 0),
        reflect_every_cycles=int(getattr(args, "reflect_every", 0) or 0),
        reflection_sample_size=int(getattr(args, "reflection_sample_size", 50) or 50),
    )

    cycles = max(1, int(getattr(args, "cycles", 1) or 1))
    try:
        operator = AutonomousOperator(config)
        if cycles == 1:
            records = [operator.run_once_sync()]
        else:
            # 持續自主迴圈：每輪間隔依 adaptation 決策（next_interval_minutes）
            import asyncio
            records = asyncio.run(operator.run_forever(max_cycles=cycles))
    except Exception as exc:
        logger.error("自主運行失敗: %s", exc, exc_info=True)
        sys.exit(1)

    for record in records:
        _print_autonomous_record(record)

    output_path: Optional[str] = getattr(args, "output", None)
    if output_path:
        payload = records[0] if len(records) == 1 else records
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        print(f"  結果已儲存至: {output_path}")


def _print_autonomous_record(record: dict) -> None:
    adaptation = record.get("adaptation", {})
    print("  決策摘要")
    print(f"    mode: {record.get('mode')}")
    print(f"    symbol: {record.get('symbol')}")
    print(f"    candidates: {', '.join(record.get('candidates', []))}")
    print(f"    plan_status: {record.get('plan_status')}")
    print(f"    plan_execution_ready: {record.get('plan_execution_ready')}")
    print(f"    final_action: {record.get('final_action')}")
    print(f"    can_execute: {adaptation.get('can_execute')}")
    print(f"    risk_multiplier: {adaptation.get('risk_multiplier')}")
    print(f"    confidence_floor: {adaptation.get('confidence_floor')}")
    print(f"    next_interval_minutes: {adaptation.get('next_interval_minutes')}")
    print(f"    reasons: {', '.join(adaptation.get('reasons', []))}")

    ai_decision = record.get("ai_decision") or {}
    ai_signal = ai_decision.get("signal") or {}
    if ai_decision:
        print("\n  Unified AI")
        print(f"    model: {ai_decision.get('model_name')}")
        print(f"    trained: {ai_decision.get('trained')}")
        print(f"    signal: {ai_signal.get('signal_type')}")
        print(f"    confidence: {ai_signal.get('confidence')}")
        print(f"    hold_period: {ai_decision.get('decision_hold_period')}")
        print(f"    valid_until: {ai_decision.get('decision_valid_until')}")

    pretrade_summary = record.get("pretrade_summary", [])
    if pretrade_summary:
        print("\n  Pretrade")
        for item in pretrade_summary:
            print(
                "    "
                f"{item.get('symbol')}: {item.get('status')} "
                f"score={item.get('score_percentage')} "
                f"tech={item.get('technical_status')} "
                f"fund={item.get('fundamental_status')} "
                f"risk={item.get('risk_status')}"
            )

    paper_execution = record.get("paper_execution")
    if paper_execution:
        print("\n  Paper Execution")
        if paper_execution.get("skipped"):
            print(
                f"    skipped: {paper_execution.get('reason')} "
                f"({paper_execution.get('symbol')})"
            )
        else:
            order = paper_execution.get("order") or {}
            qty = paper_execution.get("quantity")
            qty_text = f"{float(qty):.8f}" if qty is not None else "n/a"
            print(
                f"    {paper_execution.get('symbol')} {paper_execution.get('side')} "
                f"qty={qty_text} source={paper_execution.get('quantity_source')} "
                f"status={order.get('status')}"
            )

    print()


# ─────────────────────────────────────────────────────────────────────────────


def cmd_reflect(args: argparse.Namespace) -> None:
    """Run AI reflection loop over EpisodicMemory and refit calibrator temperature."""
    print(f"\n{'='*60}")
    print("  BioNeuronai Reflection Loop")
    print(f"{'='*60}\n")

    try:
        from bioneuronai.planning.reflection_loop import AIReflectionLoop
    except ImportError as exc:
        logger.error("AIReflectionLoop 載入失敗: %s", exc)
        sys.exit(1)

    try:
        result = AIReflectionLoop().run_reflection_cycle(k=int(args.sample_size))
    except Exception as exc:
        logger.error("反思迴圈執行失敗: %s", exc, exc_info=True)
        sys.exit(1)

    print(f"  狀態       : {result.status}")
    print(f"  分析筆數   : {result.total_trades_analyzed}")
    print(f"  虧損筆數   : {result.losing_trades_count}")
    print(f"  平均虧損   : {result.average_loss_pct:.4f}")
    print(f"  建議溫度 T : {result.recommended_temperature}")
    print(f"  報告路徑   : {result.learning_report_path}")
    print(f"{'='*60}\n")

    if getattr(args, "json", False):
        import json as _json
        print(_json.dumps({
            "status": result.status,
            "total_trades_analyzed": result.total_trades_analyzed,
            "losing_trades_count": result.losing_trades_count,
            "average_loss_pct": result.average_loss_pct,
            "recommended_temperature": result.recommended_temperature,
            "learning_report_path": result.learning_report_path,
            "feature_insights": result.feature_insights,
        }, ensure_ascii=False, indent=2, default=str))

    if result.status.startswith("ERROR"):
        sys.exit(1)


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
        from bioneuronai.strategies.strategy_arena import ArenaConfig, StrategyArena
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
        from nlp.chat_engine import MarketContext, create_chat_engine
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


def cmd_strategy_backtest(args: argparse.Namespace) -> None:
    """逐一跑正式策略實例，保存模擬進出場與成交紀錄。"""
    print(f"\n{'='*60}")
    print(f"  BioNeuronai Strategy Backtest  {args.symbol} / {args.interval}")
    print(f"{'='*60}")
    print("  模式       : 歷史 K 線 + MockBinanceConnector 模擬撮合")
    print("  真實下單   : 否")
    print(f"  尾端平倉   : {'是' if args.close_open_positions_on_end else '否'}")

    try:
        from backtest import run_strategy_suite_backtest

        result = run_strategy_suite_backtest(
            symbol=args.symbol,
            interval=args.interval,
            balance=args.balance,
            start_date=args.start_date,
            end_date=args.end_date,
            data_dir=args.data_dir,
            warmup_bars=args.warmup_bars,
            close_open_positions_on_end=args.close_open_positions_on_end,
            execution_mode=args.execution_mode,
            parameter_overrides=args.params,
            commission_bps=args.commission_bps,
            slippage_bps=args.slippage_bps,
            walk_forward=args.walk_forward,
            walk_forward_mode=getattr(args, "walk_forward_mode", "rolling"),
            wf_train_days=getattr(args, "wf_train_days", 90),
            wf_test_days=getattr(args, "wf_test_days", 30),
            wf_step_days=getattr(args, "wf_step_days", 30),
            wf_split_ratio=getattr(args, "wf_split_ratio", 0.7),
            wf_param_grid=getattr(args, "wf_param_grid", None),
            wf_max_grid_candidates=getattr(args, "wf_max_grid_candidates", 48),
        )
    except FileNotFoundError:
        logger.error(
            "找不到 %s / %s 的歷史數據，請先執行 tools/data_download/ 下載",
            args.symbol,
            args.interval,
        )
        sys.exit(1)
    except Exception as exc:
        logger.error("策略回測執行失敗: %s", exc)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        print(f"  輸出檔案   : {output_path}")

    print(f"\n  策略模板   : {result['total_templates']}")
    print(f"  可執行策略 : {result['executable_count']}")
    print(f"  失敗/不可跑: {result['unavailable_count']}")
    print(f"  執行模式   : {result.get('execution_mode')}")
    print(f"  手續費     : {result.get('commission_bps', 4.0):.1f} bps  "
          f"滑點: {result.get('slippage_bps', 1.0):.1f} bps")
    if result.get("parameter_overrides_applied"):
        print(f"  已覆蓋參數 : {', '.join(result['parameter_overrides_applied'])}")
    print(f"\n  {'策略':22} {'引擎':14} {'交易':>6} {'報酬%':>10} "
          f"{'勝率%':>8} {'夏普':>7} {'索提':>7} {'卡爾瑪':>7} "
          f"{'獲利因子':>9}  Runtime")
    print(f"  {'-'*115}")
    for item in result["ranking"]:
        stats = item.get("stats", {})
        pf_raw = stats.get("profit_factor")
        if pf_raw is not None and pf_raw != float("inf"):
            pf_str = f"{float(pf_raw):>9.2f}"
        else:
            pf_str = "inf".rjust(9)
        print(
            f"  {item['template_key'][:22]:22} "
            f"{str(item.get('execution_engine', ''))[:14]:14} "
            f"{int(item.get('trade_count', 0)):>6} "
            f"{float(stats.get('total_return') or 0):>10.4f} "
            f"{float(stats.get('win_rate') or 0):>8.2f} "
            f"{float(stats.get('sharpe_ratio') or 0):>7.2f} "
            f"{float(stats.get('sortino_ratio') or 0):>7.2f} "
            f"{float(stats.get('calmar_ratio') or 0):>7.2f} "
            f"{pf_str}  "
            f"{item.get('run_dir')}"
        )

    # Walk-forward 報告（實際 CLI 產物；非 pytest）
    wf = result.get("walk_forward")
    if wf and wf.get("enabled"):
        mode = wf.get("mode") or "single"
        print(f"\n  Walk-Forward（mode={mode}）")
        if mode == "rolling":
            print(
                f"  窗數={wf.get('total_windows')}  "
                f"train={wf.get('train_window_days')}d "
                f"test={wf.get('test_window_days')}d "
                f"step={wf.get('step_days')}d  "
                f"param_optimize={wf.get('param_optimize')} "
                f"grid_candidates={wf.get('grid_candidates', 0)}"
            )
            print(
                f"  avg train metric={wf.get('avg_train_metric')}  "
                f"avg test metric={wf.get('avg_test_metric')}  "
                f"avg degradation%={wf.get('avg_degradation_pct')}"
            )
            print(
                f"  overfit folds={wf.get('overfitting_windows')}/"
                f"{wf.get('total_windows')} "
                f"rate={float(wf.get('overfitting_rate') or 0):.1%}  "
                f"robustness={wf.get('robustness_score')} "
                f"is_robust={wf.get('is_robust')}"
            )
            print(f"  {'fold':>4} {'train period':24} {'test period':24} "
                  f"{'train':>10} {'test':>10} {'deg%':>8} overfit")
            print(f"  {'-'*90}")
            for fold in wf.get("folds") or []:
                w = fold.get("window") or {}
                print(
                    f"  {int(w.get('window_id') or 0):>4} "
                    f"{str(w.get('train_start'))}→{str(w.get('train_end')):12} "
                    f"{str(w.get('test_start'))}→{str(w.get('test_end')):12} "
                    f"{float(fold.get('train_metric') or 0):>10.4f} "
                    f"{float(fold.get('test_metric') or 0):>10.4f} "
                    f"{float(fold.get('degradation_pct') or 0):>8.1f} "
                    f"{'YES' if fold.get('is_overfitting') else 'no'}"
                )
        else:
            print(f"  IS 期間: {wf.get('is_period')}  OOS 期間: {wf.get('oos_period')}")
            oos_ranking = {
                item["template_key"]: item for item in wf.get("oos_ranking", [])
            }
            print(
                f"  {'':22} {'IS 報酬%':>10} {'OOS 報酬%':>10} "
                f"{'IS Sharpe':>10} {'OOS Sharpe':>11}"
            )
            print(f"  {'-'*65}")
            for item in result["ranking"]:
                tk = item["template_key"]
                is_st = item.get("stats", {})
                oos_item = oos_ranking.get(tk, {})
                oos_st = oos_item.get("stats", {})
                print(
                    f"  {tk[:22]:22} "
                    f"{float(is_st.get('total_return') or 0):>10.4f} "
                    f"{float(oos_st.get('total_return') or 0):>10.4f} "
                    f"{float(is_st.get('sharpe_ratio') or 0):>10.2f} "
                    f"{float(oos_st.get('sharpe_ratio') or 0):>11.2f}"
                )
    elif wf and not wf.get("enabled"):
        print(f"\n  Walk-Forward 未啟用完整結果: {wf.get('reason')}")
    elif wf and not wf.get("enabled"):
        print(f"\n  Walk-forward 未啟用: {wf.get('reason', '')}")

    if result["unavailable"]:
        print("\n  未完成策略:")
        for item in result["unavailable"]:
            print(f"  - {item['template_key']}: {item['reason']}")

    print(f"{'='*60}\n")


def cmd_readiness_gate(args: argparse.Namespace) -> None:
    """正式交易前的 BTC/ETH 多時間框架回測門檻。"""
    symbols = _split_csv_arg(getattr(args, "symbols", None))
    intervals = _split_csv_arg(getattr(args, "intervals", None))

    print(f"\n{'='*60}")
    print("  BioNeuronai Trading Readiness Gate")
    print(f"{'='*60}")
    print(f"  模式       : {'dry-run（只檢查矩陣與資料）' if args.dry_run else '執行策略回測門檻'}")
    print("  真實下單   : 否\n")

    try:
        from backtest import run_trading_readiness_gate

        report = run_trading_readiness_gate(
            config_path=args.config,
            symbols=symbols,
            intervals=intervals,
            start_date=args.start_date,
            end_date=args.end_date,
            data_dir=args.data_dir,
            output=args.output,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        logger.error("readiness gate 執行失敗: %s", exc)
        sys.exit(1)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        summary = report.get("summary", {})
        print(f"  狀態       : {report.get('status')}")
        print(
            f"  矩陣       : total={summary.get('total', 0)} "
            f"passed={summary.get('passed', 0)} "
            f"failed={summary.get('failed', 0)} "
            f"planned={summary.get('planned', 0)}"
        )
        print(f"  期間       : {report.get('start_date')} ~ {report.get('end_date')}")
        print(f"  資料根目錄 : {report.get('data_root')}")
        if report.get("output"):
            print(f"  輸出檔案   : {report['output']}")

        print("\n  Case Results")
        print(f"  {'交易對':10} {'週期':6} {'狀態':8} 說明")
        print(f"  {'-'*60}")
        for case in report.get("cases", []):
            failed = [item for item in case.get("checks", []) if not item.get("passed")]
            detail = failed[0]["detail"] if failed else "OK"
            print(f"  {case['symbol']:10} {case['interval']:6} {case['status']:8} {detail}")

    if report.get("status") == "FAIL":
        sys.exit(1)


def _split_csv_arg(value: Optional[str]) -> Optional[list[str]]:
    """Parse comma-separated CLI overrides."""
    if not value:
        return None
    parsed = [item.strip() for item in value.split(",") if item.strip()]
    return parsed or None


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


def cmd_collect_signal_data(args: argparse.Namespace) -> None:
    """收集 unified_trainer 所需的 signal JSONL 訓練資料。"""
    print(f"\n{'='*60}")
    print(f"  Collect Signal Training Data  {args.symbol} / {args.interval}")
    print(f"{'='*60}")

    try:
        from backtest import collect_signal_training_data

        result = collect_signal_training_data(
            symbol=args.symbol,
            interval=args.interval,
            balance=args.balance,
            start_date=getattr(args, "start_date", None),
            end_date=getattr(args, "end_date", None),
            data_dir=getattr(args, "data_dir", None),
            warmup_bars=args.warmup_bars,
            seq_len=args.seq_len,
            output_path=getattr(args, "output", None),
            max_samples=args.max_samples,
            future_horizon=args.future_horizon,
        )
    except FileNotFoundError:
        logger.error(
            "找不到 %s / %s 的歷史數據，請先執行 tools/data_download/ 下載",
            args.symbol,
            args.interval,
        )
        sys.exit(1)
    except Exception as exc:
        logger.error("signal 訓練資料收集失敗: %s", exc)
        sys.exit(1)

    if result.get("error"):
        logger.error(result["error"])
        sys.exit(1)

    print(f"  Samples     : {result.get('samples_collected', 0)}")
    print(f"  Skipped     : {result.get('skipped_samples', 0)}")
    print(f"  Seq Len     : {result.get('seq_len', args.seq_len)}")
    print(f"  Output Path : {result.get('output_path', 'N/A')}")
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
  python main.py collect-signal-data --symbol BTCUSDT --interval 1h
  python main.py backtest-data --symbol ETHUSDT --interval 1h
  python main.py trade     --testnet
  python main.py trade     --paper-live --paper-balance 10000
  python main.py autonomous --mode advisor --symbol BTCUSDT
  python main.py plan      --output daily_plan.json
  python main.py news      --symbol BTCUSDT --max-items 5
  python main.py pretrade  --symbol BTCUSDT --action long
  python main.py status
  python main.py strategy-backtest --symbol BTCUSDT --interval 1h
  python main.py readiness-gate --dry-run
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

    # ── strategy-backtest ───────────────────────────────────────────────────
    sbp = subparsers.add_parser(
        "strategy-backtest",
        help="逐一評估策略實例，保存模擬進出場/成交紀錄",
    )
    sbp.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                     help="交易對  (預設: BTCUSDT)")
    sbp.add_argument("--interval", default="1h", metavar="INTERVAL",
                     help="K線週期  (預設: 1h)")
    sbp.add_argument("--start-date", default=None, dest="start_date", metavar="YYYY-MM-DD",
                     help="起始日期  (預設: 最早可用)")
    sbp.add_argument("--end-date", default=None, dest="end_date", metavar="YYYY-MM-DD",
                     help="結束日期  (預設: 最新可用)")
    sbp.add_argument("--balance", type=float, default=10000.0, metavar="AMOUNT",
                     help="初始資金  (預設: 10000)")
    sbp.add_argument("--warmup-bars", type=int, default=100, metavar="N",
                     help="預熱 K 線數量  (預設: 100)")
    sbp.add_argument("--data-dir", default=None, dest="data_dir", metavar="PATH",
                     help="歷史資料根目錄  (預設: 自動尋找 repo 內資料)")
    sbp.add_argument("--output", default=None, metavar="FILE",
                     help="輸出策略比較 JSON 檔案  (可選)")
    sbp.add_argument("--params", default=None, metavar="FILE",
                     help="策略參數覆蓋 JSON 檔案，可覆蓋 entry/exit/risk 參數")
    sbp.add_argument("--execution-mode", default="template_rules",
                     choices=["template_rules", "hybrid"],
                     help="template_rules=10 個模板全跑；hybrid=有實體策略類時優先跑策略類")
    sbp.add_argument("--keep-open-positions", action="store_false",
                     dest="close_open_positions_on_end",
                     help="回測結束時不強制平倉；預設會平倉以形成完整進出紀錄")
    sbp.add_argument("--commission-bps", type=float, default=4.0, dest="commission_bps",
                     metavar="BPS",
                     help="Taker 手續費（基點，4 bps = 0.04%%）  (預設: 4.0)")
    sbp.add_argument("--slippage-bps", type=float, default=1.0, dest="slippage_bps",
                     metavar="BPS",
                     help="每筆成交滑點（基點，1 bp = 0.01%%）  (預設: 1.0)")
    sbp.add_argument("--walk-forward", action="store_true", dest="walk_forward",
                     help="開啟 Walk-Forward 驗證（需 --start-date 與 --end-date；預設 rolling 多窗）")
    sbp.add_argument(
        "--walk-forward-mode",
        dest="walk_forward_mode",
        choices=["rolling", "single"],
        default="rolling",
        help="rolling=多窗滾動（舊版能力拿回）；single=一次 70/30 IS/OOS 切分",
    )
    sbp.add_argument("--wf-train-days", type=int, default=90, dest="wf_train_days",
                     help="rolling 模式訓練窗天數（預設 90）")
    sbp.add_argument("--wf-test-days", type=int, default=30, dest="wf_test_days",
                     help="rolling 模式測試窗天數（預設 30）")
    sbp.add_argument("--wf-step-days", type=int, default=30, dest="wf_step_days",
                     help="rolling 模式滾動步長天數（預設 30）")
    sbp.add_argument("--wf-split-ratio", type=float, default=0.7, dest="wf_split_ratio",
                     help="single 模式 IS 佔比（預設 0.7）")
    sbp.add_argument(
        "--wf-param-grid",
        default=None,
        dest="wf_param_grid",
        metavar="FILE",
        help="rolling 時 IS 參數網格 JSON（舊 WalkForwardTester.param_grid；見 config/wf_param_grid.example.json）",
    )
    sbp.add_argument(
        "--wf-max-grid-candidates",
        type=int,
        default=48,
        dest="wf_max_grid_candidates",
        help="param_grid 最多嘗試組合數（預設 48）",
    )
    sbp.set_defaults(func=cmd_strategy_backtest, close_open_positions_on_end=True, walk_forward=False)

    # ── readiness-gate ───────────────────────────────────────────────────────
    rgp = subparsers.add_parser(
        "readiness-gate",
        help="正式交易前的 BTC/ETH 多時間框架回測門檻",
    )
    rgp.add_argument("--config", default=None, metavar="FILE",
                     help="readiness gate JSON 設定檔 (預設: config/trading_readiness_gate.json)")
    rgp.add_argument("--symbols", default=None, metavar="CSV",
                     help="覆蓋交易對矩陣，例如 BTCUSDT,ETHUSDT")
    rgp.add_argument("--intervals", default=None, metavar="CSV",
                     help="覆蓋週期矩陣，例如 1h,4h")
    rgp.add_argument("--start-date", default=None, dest="start_date", metavar="YYYY-MM-DD",
                     help="覆蓋起始日期")
    rgp.add_argument("--end-date", default=None, dest="end_date", metavar="YYYY-MM-DD",
                     help="覆蓋結束日期")
    rgp.add_argument("--data-dir", default=None, dest="data_dir", metavar="PATH",
                     help="歷史資料根目錄")
    rgp.add_argument("--output", default=None, metavar="FILE",
                     help="輸出 PASS/FAIL JSON 報告")
    rgp.add_argument("--dry-run", action="store_true",
                     help="只檢查矩陣、資料與門檻設定，不執行回測")
    rgp.add_argument("--json", action="store_true",
                     help="以 JSON 輸出")
    rgp.set_defaults(func=cmd_readiness_gate)

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

    # ── collect-signal-data ──────────────────────────────────────────────────
    csdp = subparsers.add_parser(
        "collect-signal-data",
        help="收集 unified_trainer 所需的 signal JSONL 訓練資料",
    )
    csdp.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                      help="交易對  (預設: BTCUSDT)")
    csdp.add_argument("--interval", default="1h", metavar="INTERVAL",
                      help="K線週期  (預設: 1h)")
    csdp.add_argument("--balance", type=float, default=10000.0, metavar="AMOUNT",
                      help="回放時使用的初始資金  (預設: 10000)")
    csdp.add_argument("--start-date", default=None, dest="start_date", metavar="YYYY-MM-DD",
                      help="起始日期  (預設: 最早可用)")
    csdp.add_argument("--end-date", default=None, dest="end_date", metavar="YYYY-MM-DD",
                      help="結束日期  (預設: 最新可用)")
    csdp.add_argument("--data-dir", default=None, dest="data_dir", metavar="PATH",
                      help="歷史資料根目錄  (預設: 自動尋找 repo 內資料)")
    csdp.add_argument("--warmup-bars", type=int, default=100, metavar="N",
                      help="特徵提取前預熱 K 線數量  (預設: 100)")
    csdp.add_argument("--seq-len", type=int, default=16, metavar="N",
                      help="每筆樣本的時間步數  (預設: 16)")
    csdp.add_argument("--max-samples", type=int, default=50000, metavar="N",
                      help="最多收集幾筆樣本  (預設: 50000)")
    csdp.add_argument("--future-horizon", type=int, default=12, metavar="N",
                      help="每筆標籤使用的真實未來 K 線數  (預設: 12)")
    csdp.add_argument("--output", default=None, metavar="FILE",
                      help="輸出 JSONL 檔案路徑  (預設: data/unified_v2_training.jsonl)")
    csdp.set_defaults(func=cmd_collect_signal_data)

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
    tp = subparsers.add_parser("trade", help="監控 / 虛擬實盤 / 測試網 / 實盤交易")
    tp.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                    help="交易對  (預設: BTCUSDT)")
    tp.add_argument("--testnet", action="store_true", default=True,
                    help="使用測試網  (預設)")
    tp.add_argument("--paper-live", action="store_true",
                    help="使用主網即時行情，但所有下單只進本機虛擬帳戶")
    tp.add_argument("--paper-balance", type=float, default=10000.0, metavar="AMOUNT",
                    help="paper-live 虛擬帳戶初始 USDT 餘額 (預設: 10000)")
    tp.add_argument("--auto-trade", action="store_true",
                    help="允許收到非 HOLD 訊號後送到目前執行層；paper-live 會自動啟用")
    tp.add_argument("--load-ai-model", action="store_true", default=True,
                    help="啟動時載入 AI 模型 (預設)")
    tp.add_argument("--no-ai-model", action="store_false", dest="load_ai_model",
                    help="啟動時不載入 AI 模型")
    tp.add_argument("--model-name", default="unified_v2_100m", metavar="MODEL",
                    help="AI 模型名稱 (唯一現役模型: unified_v2_100m)")
    tp.add_argument("--warmup-model", action="store_true",
                    help="載入模型後執行 warmup")
    tp.add_argument("--live", action="store_true",
                    help="使用真實網路  [謹慎！需設定 API 金鑰]")
    tp.set_defaults(func=cmd_trade)

    # ── plan ──────────────────────────────────────────────────────────────────
    pp = subparsers.add_parser("plan", help="生成每日 SOP 交易計劃")
    pp.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                    help="交易對  (預設: BTCUSDT)")
    pp.add_argument("--interval", default="1h", metavar="INTERVAL",
                    help="K線週期  (預設: 1h)")
    pp.add_argument("--klines-limit", type=int, default=300, dest="klines_limit", metavar="N",
                    help="載入最近幾根 K線供計劃分析使用  (預設: 300)")
    pp.add_argument("--balance", type=float, default=10000.0, metavar="AMOUNT",
                    help="計劃使用的帳戶資金  (預設: 10000)")
    pp.add_argument("--data-dir", default=None, dest="data_dir", metavar="PATH",
                    help="歷史資料根目錄  (預設: 自動尋找 repo 內資料)")
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
    prtp.add_argument("--balance", type=float, default=None, metavar="AMOUNT",
                      help="advisor/paper 規劃資金；省略時必須有 Binance 帳戶憑證")
    prtp.add_argument("--output", default=None, metavar="FILE",
                      help="輸出 JSON 檔案路徑  (可選)")
    prtp.set_defaults(func=cmd_pretrade)

    # ── autonomous ───────────────────────────────────────────────────────────
    autop = subparsers.add_parser(
        "autonomous",
        help="自主運行：plan -> pretrade -> adaptation -> ledger（--cycles N 進入持續閉環）",
    )
    autop.add_argument(
        "--cycles",
        type=int,
        default=1,
        metavar="N",
        help="運行輪數；1=單輪（預設），>1 進入 run_forever 持續閉環"
             "（每輪間隔依 adaptation 建議，遇 STOP 自動停機）",
    )
    autop.add_argument(
        "--mode",
        choices=["advisor", "paper_auto", "testnet_auto", "live_guarded"],
        default="advisor",
        help="自主模式；預設 advisor 不執行訂單",
    )
    autop.add_argument("--symbol", default="BTCUSDT", metavar="SYMBOL",
                       help="主要交易對  (預設: BTCUSDT)")
    autop.add_argument(
        "--action",
        choices=["BUY", "SELL", "LONG", "SHORT", "buy", "sell", "long", "short"],
        default="BUY",
        help="pretrade 預期方向  (預設: BUY)",
    )
    autop.add_argument("--interval", default="1h", metavar="INTERVAL",
                       help="K線週期  (預設: 1h)")
    autop.add_argument("--balance", type=float, default=10000.0, metavar="AMOUNT",
                       help="計劃用帳戶餘額  (預設: 10000)")
    autop.add_argument("--klines-limit", type=int, default=300, metavar="N",
                       help="載入 K 線數量  (預設: 300)")
    autop.add_argument("--max-pairs", type=int, default=3, metavar="N",
                       help="最多 pretrade 候選交易對  (預設: 3)")
    autop.add_argument("--data-dir", default=None, dest="data_dir", metavar="PATH",
                       help="歷史資料根目錄")
    autop.add_argument("--ledger-path", default=None, metavar="PATH",
                       help="decision ledger JSONL 路徑")
    autop.add_argument("--output", default=None, metavar="FILE",
                       help="輸出本輪決策 JSON")
    autop.add_argument(
        "--execute-paper",
        action="store_true",
        help="僅在 paper_auto 且 pretrade 通過時送出本機 paper order",
    )
    autop.add_argument("--paper-balance", type=float, default=10000.0, metavar="AMOUNT",
                       help="paper 初始餘額  (預設: 10000)")
    autop.add_argument(
        "--paper-notional-fraction",
        type=float,
        default=0.01,
        metavar="RATIO",
        help="pretrade 無 quantity 時的 fallback 比例  (預設: 0.01)",
    )
    autop.add_argument(
        "--max-position-hold-cycles",
        type=int,
        default=0,
        dest="max_position_hold_cycles",
        metavar="N",
        help="卡單自動平倉：持倉超過 N 輪強制出場  (0=停用，預設: 0)",
    )
    autop.add_argument(
        "--reflect-every",
        type=int,
        default=0,
        metavar="N",
        help="run_forever 時每 N 輪執行 reflection_loop  (0=停用，預設: 0)",
    )
    autop.add_argument(
        "--reflection-sample-size",
        type=int,
        default=50,
        metavar="K",
        help="reflection_loop 抽樣 EpisodicMemory 筆數  (預設: 50)",
    )
    autop.set_defaults(func=cmd_autonomous)

    # ── reflect ───────────────────────────────────────────────────────────────
    rflp = subparsers.add_parser(
        "reflect",
        help="AI 反思迴圈：EpisodicMemory → learning_report → calibrator refit",
    )
    rflp.add_argument("--sample-size", type=int, default=50, metavar="K",
                      help="抽樣分析筆數  (預設: 50)")
    rflp.add_argument("--json", action="store_true", help="以 JSON 輸出結果")
    rflp.set_defaults(func=cmd_reflect)

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
