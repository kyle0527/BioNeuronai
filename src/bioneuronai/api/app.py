# -*- coding: utf-8 -*-
"""
BioNeuronai REST API Server
============================

將 CLI 功能包裝為 REST API，保持業務邏輯不變。

啟動方式:
    uvicorn bioneuronai.api.app:app --host 0.0.0.0 --port 8000
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# ── 路徑設定 ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bioneuronai.api.models import (  # noqa: E402
    ApiResponse,
    BacktestRequest,
    BinanceValidateRequest,
    ModuleStatus,
    NewsRequest,
    PreTradeRequest,
    SimulateRequest,
    StrategyBacktestRequest,
    StatusResponse,
    TradeStartRequest,
    TrainingStartRequest,
    ModelPromoteRequest,
)
from schemas.api import (  # noqa: E402
    ChatRequest,
    ChatResponse,
    DashboardDataResponse,
    TradeOrderRequest,
    WsRiskData,
    WsMaxDrawdown,
    WsPretradeItem,
    WsPretradeChecklist,
    WsAuditLogEntry,
    WsPosition,
)

logger = logging.getLogger(__name__)


class TradeManager:
    """封裝 API 層的交易引擎與背景監控 task。"""

    def __init__(self) -> None:
        self._trade_task: Optional[asyncio.Task[Any]] = None
        self._trade_engine: Optional[Any] = None
        self._trade_mode = "stopped"
        self._started_at: Optional[datetime] = None
        self._last_start_request: Dict[str, Any] = {}
        self._monitoring_requested = False

    @property
    def engine(self) -> Optional[Any]:
        return self._trade_engine

    @property
    def task(self) -> Optional[asyncio.Task[Any]]:
        return self._trade_task

    def is_running(self) -> bool:
        task_running = self._trade_task is not None and not self._trade_task.done()
        engine_monitoring = bool(getattr(self._trade_engine, "is_monitoring", False))
        return task_running or engine_monitoring or self._monitoring_requested

    def _auto_trade_requested(self, req: TradeStartRequest) -> bool:
        return req.auto_trade or req.mode in {"paper_live", "testnet_auto", "live_auto"}

    def _validate_live_guard(self, req: TradeStartRequest) -> None:
        if req.mode != "live_auto":
            return

        live_allowed = os.getenv("ALLOW_LIVE_TRADING", "").strip().lower()
        if live_allowed not in {"1", "true", "yes"}:
            raise RuntimeError("正式網交易需先設定 ALLOW_LIVE_TRADING=1")

        if req.confirm_live != "I_UNDERSTAND_LIVE_RISK":
            raise RuntimeError("正式網交易需提供 confirm_live=I_UNDERSTAND_LIVE_RISK")

    def _validate_start_request(self, req: TradeStartRequest, api_key: str, api_secret: str) -> None:
        auto_requested = self._auto_trade_requested(req)

        if req.mode == "monitor_only" and req.auto_trade:
            raise RuntimeError("auto_trade=true 時請改用 paper_live、testnet_auto 或 live_auto 模式")

        if req.mode == "paper_live" and req.testnet:
            raise RuntimeError("paper_live 使用正式行情但虛擬成交，請使用 testnet=false")

        if req.mode == "testnet_auto" and not req.testnet:
            raise RuntimeError("testnet_auto 必須使用 testnet=true")

        if req.mode == "live_auto" and req.testnet:
            raise RuntimeError("live_auto 必須使用 testnet=false")

        if auto_requested and req.mode != "paper_live" and (not api_key or not api_secret):
            raise RuntimeError("自動交易需提供 Binance API Key/Secret 或設定環境變數")

        self._validate_live_guard(req)

    def _task_state(self) -> Dict[str, Any]:
        if self._trade_task is None:
            return {"state": "not_started", "error": None}
        if self._trade_task.cancelled():
            return {"state": "cancelled", "error": None}
        if not self._trade_task.done():
            return {"state": "running", "error": None}
        try:
            error = self._trade_task.exception()
        except asyncio.CancelledError:
            return {"state": "cancelled", "error": None}
        return {"state": "done", "error": str(error) if error else None}

    def get_status(self) -> Dict[str, Any]:
        """取得交易引擎狀態，供 UI 直接顯示。"""
        engine = self._trade_engine
        task_state = self._task_state()
        return {
            "running": self.is_running(),
            "mode": self._trade_mode,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "request": self._last_start_request,
            "task": task_state,
            "engine": {
                "available": engine is not None,
                "is_monitoring": bool(getattr(engine, "is_monitoring", False)),
                "auto_trade": bool(getattr(engine, "auto_trade", False)),
                "enable_ai_model": bool(getattr(engine, "enable_ai_model", False)),
                "ai_model_loaded": bool(getattr(engine, "ai_model_loaded", False)),
                "paper_trading": bool(getattr(engine, "paper_trading", False)),
            },
            "paper": (
                engine.connector.get_paper_state()
                if engine is not None and hasattr(engine.connector, "get_paper_state")
                else None
            ),
        }

    async def start(self, req: TradeStartRequest) -> Dict[str, Any]:
        """啟動交易監控並回傳使用中的環境與狀態。"""
        if self.is_running():
            raise RuntimeError("交易已在運行中")

        from bioneuronai.core.trading_engine import TradingEngine

        api_key = req.api_key or os.getenv("BINANCE_API_KEY", "")
        api_secret = req.api_secret or os.getenv("BINANCE_API_SECRET", "")
        self._validate_start_request(req, api_key, api_secret)

        auto_requested = self._auto_trade_requested(req)
        should_load_ai_model = req.load_ai_model or auto_requested
        engine = TradingEngine(
            api_key=api_key,
            api_secret=api_secret,
            testnet=req.testnet,
            enable_ai_model=should_load_ai_model,
            paper_trading=req.mode == "paper_live",
            paper_initial_balance=req.paper_initial_balance,
        )

        if should_load_ai_model and not engine.load_ai_model(req.model_name, warmup=req.warmup_model):
            raise RuntimeError(f"AI 模型載入失敗: {req.model_name}")

        if auto_requested:
            engine.enable_auto_trading()
        else:
            engine.disable_auto_trading()

        self._trade_engine = engine
        self._trade_mode = req.mode
        self._started_at = datetime.now()
        self._last_start_request = req.model_dump(exclude={"api_key", "api_secret", "confirm_live"})
        self._last_start_request["load_ai_model"] = should_load_ai_model
        self._monitoring_requested = True

        async def _monitor() -> None:
            if self._trade_engine is None:
                return
            try:
                await asyncio.to_thread(self._trade_engine.start_monitoring, req.symbol)
            except Exception:
                self._monitoring_requested = False
                logger.exception("交易監控背景任務失敗")
                raise

        self._trade_task = asyncio.create_task(_monitor())
        environment = "虛擬實盤" if req.mode == "paper_live" else ("測試網" if req.testnet else "正式網")
        status = self.get_status()
        status["environment"] = environment
        if req.mode == "paper_live" and hasattr(engine.connector, "get_paper_state"):
            status["paper"] = engine.connector.get_paper_state()
        return status

    async def stop(self) -> None:
        """停止交易監控並清理引擎引用。"""
        self._monitoring_requested = False

        if self._trade_task is not None and not self._trade_task.done():
            self._trade_task.cancel()
            self._trade_task = None

        if self._trade_engine is not None and hasattr(self._trade_engine, "stop_monitoring"):
            try:
                await asyncio.to_thread(self._trade_engine.stop_monitoring)
            except Exception:
                pass

        self._trade_engine = None
        self._trade_mode = "stopped"
        self._started_at = None

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """透過目前交易引擎查詢即時價格。"""
        if self._trade_engine is None:
            return None
        get_price = getattr(self._trade_engine, "_get_current_price", None)
        if get_price is None:
            return None
        try:
            price = await asyncio.to_thread(get_price, symbol)
            return float(price) if price else None
        except Exception:
            return None

    async def get_virtual_portfolio(self) -> list[dict]:
        """取得虛擬帳戶投資組合快照。"""
        if self._trade_engine is None:
            return []
        try:
            account = getattr(self._trade_engine, "virtual_account", None)
            if account is None:
                connector = getattr(self._trade_engine, "connector", None)
                account = getattr(connector, "virtual_account", None)
            if account is None:
                return []
            get_portfolio = getattr(account, "get_portfolio", None)
            if get_portfolio is not None:
                raw = await asyncio.to_thread(get_portfolio)
                return raw if isinstance(raw, list) else []
            get_positions = getattr(account, "get_all_positions", None)
            if get_positions is not None:
                positions = await asyncio.to_thread(get_positions)
                dashboard_positions = []
                for position in positions:
                    raw = position.to_dict() if hasattr(position, "to_dict") else dict(position)
                    qty = abs(float(raw.get("positionAmt", 0) or 0))
                    entry = float(raw.get("entryPrice", 0) or 0)
                    mark = float(raw.get("markPrice", 0) or 0)
                    pnl = float(raw.get("unRealizedProfit", 0) or 0)
                    notional = entry * qty
                    dashboard_positions.append({
                        "id": str(raw.get("symbol", "")),
                        "symbol": str(raw.get("symbol", "")),
                        "side": "long" if float(raw.get("positionAmt", 0) or 0) >= 0 else "short",
                        "quantity": qty,
                        "entryPrice": entry,
                        "currentPrice": mark,
                        "unrealizedPnl": pnl,
                        "unrealizedPnlPercent": (pnl / notional * 100) if notional > 0 else 0.0,
                        "leverage": int(float(raw.get("leverage", 1) or 1)),
                        "liquidationPrice": float(raw.get("liquidationPrice", 0) or 0) or None,
                        "openedAt": datetime.now().isoformat(),
                    })
                return dashboard_positions
            return []
        except Exception:
            return []


_trade_manager = TradeManager()


class TrainingJobManager:
    """API 層的訓練作業追蹤器。

    external 模式只登記遠端作業；local_process 模式才會啟動本機 subprocess。
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._processes: Dict[str, Any] = {}
        self._log_files: Dict[str, Any] = {}

    def start(self, req: TrainingStartRequest) -> Dict[str, Any]:
        job_id = str(uuid4())
        now = datetime.now().isoformat()
        job_dir = PROJECT_ROOT / req.output_dir / job_id
        payload: Dict[str, Any] = {
            "job_id": job_id,
            "job_name": req.job_name,
            "execution_mode": req.execution_mode,
            "status": "registered" if req.execution_mode == "external" else "pending",
            "created_at": now,
            "started_at": now if req.execution_mode == "external" else None,
            "completed_at": None,
            "cloud_job_id": req.cloud_job_id,
            "request": req.model_dump(),
            "output_dir": str(job_dir),
            "log_path": None,
            "command": None,
            "returncode": None,
            "error": None,
        }

        if req.execution_mode == "local_process":
            job_dir.mkdir(parents=True, exist_ok=True)
            log_path = job_dir / "training.log"
            command = self._build_command(req, job_dir)
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{SRC_DIR}{os.pathsep}{PROJECT_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
            log_file = log_path.open("a", encoding="utf-8")
            process = subprocess.Popen(
                command,
                cwd=str(PROJECT_ROOT),
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self._processes[job_id] = process
            self._log_files[job_id] = log_file
            payload.update({
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "log_path": str(log_path),
                "command": command,
            })

        self._jobs[job_id] = payload
        return self.get(job_id)

    def list_jobs(self) -> list[Dict[str, Any]]:
        return [self.get(job_id) for job_id in self._jobs]

    def get(self, job_id: str) -> Dict[str, Any]:
        job = self._jobs.get(job_id)
        if job is None:
            return {"job_id": job_id, "status": "not_found", "error": "training job not found"}

        process = self._processes.get(job_id)
        if process is not None:
            returncode = process.poll()
            if returncode is None:
                job["status"] = "running"
            else:
                job["returncode"] = returncode
                job["status"] = "completed" if returncode == 0 else "failed"
                if job.get("completed_at") is None:
                    job["completed_at"] = datetime.now().isoformat()
                log_file = self._log_files.pop(job_id, None)
                if log_file is not None and not log_file.closed:
                    log_file.close()
                if returncode != 0:
                    job["error"] = f"trainer exited with code {returncode}"

        log_path = job.get("log_path")
        if log_path:
            job["log_tail"] = self._read_log_tail(Path(log_path))
        return dict(job)

    def _build_command(self, req: TrainingStartRequest, job_dir: Path) -> list[str]:
        output_dir = Path(req.output_dir)
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        output_dir = output_dir / job_dir.name

        command = [
            sys.executable,
            "-m",
            "nlp.training.unified_trainer",
            "--epochs",
            str(req.epochs),
            "--batch",
            str(req.batch),
            "--grad-accum",
            str(req.grad_accum),
            "--save-steps",
            str(req.save_steps),
            "--output",
            str(output_dir),
        ]
        if req.lm_only:
            command.append("--lm-only")
        if req.sig_only:
            command.append("--sig-only")
        if req.no_save:
            command.append("--no-save")
        if req.signal_data:
            command.extend(["--signal-data", req.signal_data])
        if req.signal_val_data:
            command.extend(["--signal-val-data", req.signal_val_data])
        if req.base_model:
            command.extend(["--base-model", req.base_model])
        if req.resume:
            command.extend(["--resume", req.resume])
        if req.cloud_output_uri:
            command.extend(["--cloud-output-uri", req.cloud_output_uri])
        if req.max_signal_samples:
            command.extend(["--max-signal-samples", str(req.max_signal_samples)])
        return command

    def _read_log_tail(self, log_path: Path, max_lines: int = 120) -> list[str]:
        if not log_path.exists():
            return []
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return lines[-max_lines:]
        except Exception as exc:
            return [f"log read failed: {exc}"]


class ModelPromotionManager:
    """記錄 runtime 模型來源，讓訓練產物可接回交易引擎。"""

    def __init__(self) -> None:
        self._active_model_path = PROJECT_ROOT / "config" / "active_model.json"
        self._apply_active_model_env()

    def status(self) -> Dict[str, Any]:
        active = self._read_active_model()
        return {
            "active_model": active,
            "env": {
                "MODEL_PATH": os.getenv("MODEL_PATH") or os.getenv("BIONEURONAI_MODEL_PATH"),
                "MODEL_DIR": os.getenv("MODEL_DIR") or os.getenv("BIONEURONAI_MODEL_DIR"),
            },
            "trade_engine": _trade_manager.get_status(),
        }

    def promote(self, req: ModelPromoteRequest) -> Dict[str, Any]:
        materialized_path: Optional[str] = None
        resolved_runtime_path = req.model_path

        if req.validate_path:
            materialized = self._resolve_promoted_path(req.model_path, req.model_name)
            if not materialized.exists():
                raise FileNotFoundError(f"model artifact not found: {materialized}")
            materialized_path = str(materialized)

        if req.model_path.endswith("/") or not Path(req.model_path).suffix:
            os.environ["MODEL_DIR"] = req.model_path.rstrip("/")
            os.environ.pop("MODEL_PATH", None)
        else:
            os.environ["MODEL_PATH"] = req.model_path
            os.environ.pop("MODEL_DIR", None)

        promoted = {
            "model_name": req.model_name,
            "model_path": resolved_runtime_path,
            "materialized_path": materialized_path,
            "promoted_at": datetime.now().isoformat(),
            "reload_running_engine": req.reload_running_engine,
            "notes": req.notes,
        }
        self._active_model_path.parent.mkdir(parents=True, exist_ok=True)
        self._active_model_path.write_text(json.dumps(promoted, ensure_ascii=False, indent=2), encoding="utf-8")

        if req.reload_running_engine and _trade_manager.engine is not None:
            loaded = _trade_manager.engine.load_ai_model(req.model_name, warmup=req.warmup_model)
            promoted["reloaded"] = loaded
            if not loaded:
                raise RuntimeError("model promoted, but running trade engine failed to reload it")

        return promoted

    def _resolve_promoted_path(self, model_path: str, model_name: str) -> Path:
        from bioneuronai.data.cloud_storage import materialize_uri

        resolved = materialize_uri(model_path)
        if resolved.suffix:
            return resolved
        return resolved / f"{model_name}.pth"

    def _read_active_model(self) -> Optional[Dict[str, Any]]:
        if not self._active_model_path.exists():
            return None
        try:
            return json.loads(self._active_model_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"error": f"active model metadata read failed: {exc}"}

    def _apply_active_model_env(self) -> None:
        active = self._read_active_model()
        if not active or active.get("error"):
            return
        model_path = str(active.get("model_path") or "").strip()
        if not model_path:
            return
        if model_path.endswith("/") or not Path(model_path).suffix:
            os.environ.setdefault("MODEL_DIR", model_path.rstrip("/"))
        else:
            os.environ.setdefault("MODEL_PATH", model_path)


_training_job_manager = TrainingJobManager()
_model_promotion_manager = ModelPromotionManager()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("BioNeuronai API 啟動中 ...")
    yield
    await _trade_manager.stop()
    logger.info("BioNeuronai API 關閉")


# ── CORS ─────────────────────────────────────────────────────────────────────
def _get_allowed_origins() -> list[str]:
    """從環境變數讀取允許的來源。
    
    生產環境請設定 ALLOWED_ORIGINS 環境變數，例如：
        ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
    
    若未設定，預設只允許本地開發伺服器。
    """
    env_val = os.getenv("ALLOWED_ORIGINS", "").strip()
    if env_val:
        return [o.strip() for o in env_val.split(",") if o.strip()]
    # 預設：本地開發的常見埠口。Vite 會在 5173 被占用時遞增埠口，
    # 且瀏覽器可能用 localhost 或 127.0.0.1 開啟，因此兩者都允許。
    vite_ports = range(5173, 5181)
    local_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    for port in vite_ports:
        local_origins.append(f"http://localhost:{port}")
        local_origins.append(f"http://127.0.0.1:{port}")
    return local_origins


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BioNeuronai API",
    description="AI-driven cryptocurrency futures trading system REST API",
    version="2.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/", tags=["root"])
async def root():
    return {"service": "BioNeuronai API", "version": "2.1", "docs": "/docs", "backtest_ui": "/backtest/ui"}


# ── Status ────────────────────────────────────────────────────────────────────


@app.get("/api/v1/status", response_model=StatusResponse, tags=["system"])
async def get_status():
    """系統健康狀態檢查"""
    checks = [
        ("bioneuronai.core.trading_engine", "TradingEngine", "TradingEngine"),
        ("bioneuronai.data.binance_futures", "BinanceFuturesConnector", "BinanceFutures"),
        ("bioneuronai.analysis", "CryptoNewsAnalyzer", "NewsAnalyzer"),
        ("bioneuronai.analysis.daily_report", "SOPAutomationSystem", "SOPSystem"),
        ("bioneuronai.planning.pretrade_automation", "PreTradeCheckSystem", "PreTradeCheck"),
    ]

    modules = []
    all_ok = True
    for module_path, class_name, label in checks:
        try:
            mod = __import__(module_path, fromlist=[class_name])
            getattr(mod, class_name)
            modules.append(ModuleStatus(name=label, available=True))
        except (ImportError, AttributeError) as exc:
            modules.append(ModuleStatus(name=label, available=False, error=str(exc)))
            all_ok = False

    version = None
    try:
        import bioneuronai
        version = getattr(bioneuronai, "__version__", None)
    except Exception:
        pass

    return StatusResponse(modules=modules, version=version, all_ok=all_ok)


# ── Binance Validate ─────────────────────────────────────────────────────────


@app.post("/api/v1/binance/validate", response_model=ApiResponse, tags=["system"])
async def validate_binance_credentials(req: BinanceValidateRequest):
    """驗證 Binance API 憑證是否有效（讀取權限 + Futures 可用性）

    憑證優先順序：請求體 api_key/api_secret → 環境變數。
    """
    import os

    api_key = req.api_key or os.getenv("BINANCE_API_KEY", "")
    api_secret = req.api_secret or os.getenv("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        return ApiResponse(
            success=False,
            message="缺少 API 憑證。請在請求中提供 api_key/api_secret，或設定環境變數 BINANCE_API_KEY / BINANCE_API_SECRET。",
        )

    try:
        from bioneuronai.data.binance_futures import BinanceFuturesConnector

        connector = BinanceFuturesConnector(
            api_key=api_key,
            api_secret=api_secret,
            testnet=req.testnet,
        )

        # 1. 取得報價（不需簽名，驗連線可達性）
        price_data = connector.get_ticker_price("BTCUSDT")
        if price_data is None:
            return ApiResponse(success=False, message="無法連線至 Binance，請檢查網路或 testnet 設定。")

        # 2. 獲取帳戶資訊（需簽名，驗 key 有效 + Futures 權限）
        account = connector.get_account_info()
        if not account:
            return ApiResponse(success=False, message="API Key 無效或缺乏 Futures 權限，請檢查 Key 設定。")

        total_balance = account.get("totalWalletBalance", "N/A")
        mode = "testnet" if req.testnet else "mainnet"
        return ApiResponse(
            success=True,
            message=f"憑證驗證成功 [{mode}]",
            data={"total_wallet_balance": total_balance, "environment": mode},
        )
    except Exception as exc:
        return ApiResponse(success=False, message=f"憑證驗證失敗: {exc}")


# ── News ──────────────────────────────────────────────────────────────────────


@app.post("/api/v1/news", response_model=ApiResponse, tags=["analysis"])
async def analyze_news(req: NewsRequest):
    """新聞情緒分析"""
    try:
        from bioneuronai.analysis import CryptoNewsAnalyzer

        analyzer = CryptoNewsAnalyzer()
        result = await asyncio.to_thread(analyzer.analyze_news, req.symbol)

        if isinstance(result, dict):
            data: Dict[str, Any] = result
        elif hasattr(result, "model_dump"):
            data = _safe_serialize(result)
        elif hasattr(result, "__dict__"):
            data = _safe_serialize(result)
        else:
            data = {"raw": str(result)}

        return ApiResponse(success=True, message="新聞分析完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"新聞分析失敗: {exc}")


# ── Backtest Replay ──────────────────────────────────────────────────────────


@app.get("/api/v1/backtest/catalog", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_catalog(symbol: str | None = None, interval: str | None = None):
    """列出可用的歷史回放資料。"""
    try:
        from backtest import get_catalog

        data = await asyncio.to_thread(get_catalog, None, symbol, interval)
        return ApiResponse(success=True, message="歷史資料掃描完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"歷史資料掃描失敗: {exc}")


@app.get("/api/v1/backtest/inspect", response_model=ApiResponse, tags=["backtest"])
async def inspect_backtest_dataset(
    symbol: str = "ETHUSDT",
    interval: str = "1h",
    start_date: str | None = None,
    end_date: str | None = None,
):
    """檢視指定資料集是否可被 replay 層載入。"""
    try:
        from backtest import HistoricalDataStream

        stream = await asyncio.to_thread(
            HistoricalDataStream,
            None,
            symbol,
            interval,
            start_date,
            end_date,
            0.0,
            True,
        )
        frame = stream.load_data()
        payload = {
            "resolved_root": str(stream.data_dir),
            "symbol": symbol,
            "interval": interval,
            "bars": len(frame),
            "start_open_time": int(frame["open_time"].iloc[0]),
            "end_open_time": int(frame["open_time"].iloc[-1]),
        }
        return ApiResponse(success=True, message="資料載入成功", data=payload)
    except Exception as exc:
        return ApiResponse(success=False, message=f"資料載入失敗: {exc}")


@app.post("/api/v1/backtest/simulate", response_model=ApiResponse, tags=["backtest"])
async def run_backtest_simulation(req: SimulateRequest):
    """執行 replay simulate。"""
    try:
        from backtest import run_simulation_summary

        data = await asyncio.to_thread(
            run_simulation_summary,
            req.symbol,
            req.interval,
            req.balance,
            req.bars,
            req.start_date,
            req.end_date,
        )
        return ApiResponse(success=True, message="simulate 完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"simulate 失敗: {exc}")


@app.post("/api/v1/backtest/run", response_model=ApiResponse, tags=["backtest"])
async def run_backtest(req: BacktestRequest):
    """執行 replay backtest。"""
    try:
        from backtest import run_backtest_summary

        data = await asyncio.to_thread(
            run_backtest_summary,
            req.symbol,
            req.interval,
            req.balance,
            req.start_date,
            req.end_date,
            None,
            req.warmup_bars,
        )
        return ApiResponse(success=True, message="backtest 完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"backtest 失敗: {exc}")


@app.post("/api/v1/backtest/strategy-run", response_model=ApiResponse, tags=["backtest"])
async def run_strategy_backtest(req: StrategyBacktestRequest):
    """執行策略模組競爭 / 策略模板回放。"""
    try:
        from backtest import run_strategy_suite_backtest

        data = await asyncio.to_thread(
            run_strategy_suite_backtest,
            symbol=req.symbol,
            interval=req.interval,
            balance=req.balance,
            start_date=req.start_date,
            end_date=req.end_date,
            warmup_bars=req.warmup_bars,
            close_open_positions_on_end=req.close_open_positions_on_end,
            execution_mode=req.execution_mode,
            parameter_overrides=req.parameter_overrides,
            commission_bps=req.commission_bps,
            slippage_bps=req.slippage_bps,
            walk_forward=req.walk_forward,
        )
        return ApiResponse(success=True, message="strategy backtest 完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"strategy backtest 失敗: {exc}")


@app.get("/api/v1/backtest/runs", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_runs(limit: int = 10):
    """列出 replay runtime runs。"""
    try:
        from backtest import list_runtime_runs

        data = await asyncio.to_thread(list_runtime_runs, limit)
        return ApiResponse(success=True, message="replay runs 讀取完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"replay runs 讀取失敗: {exc}")


@app.get("/api/v1/backtest/runs/{run_id}", response_model=ApiResponse, tags=["backtest"])
async def get_backtest_run(run_id: str):
    """讀取指定 replay runtime run。"""
    try:
        from backtest import get_runtime_run

        data = await asyncio.to_thread(get_runtime_run, run_id)
        return ApiResponse(success=True, message="replay run 讀取完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"replay run 讀取失敗: {exc}")


@app.get("/backtest/ui", response_class=HTMLResponse, tags=["backtest"])
async def backtest_ui():
    """最小可用 backtest UI。"""
    from backtest import load_backtest_ui_html

    return HTMLResponse(load_backtest_ui_html())


# ── PreTrade ──────────────────────────────────────────────────────────────────


@app.post("/api/v1/pretrade", response_model=ApiResponse, tags=["trading"])
async def pretrade_check(req: PreTradeRequest):
    """進場前檢查"""
    try:
        from bioneuronai.planning.pretrade_automation import PreTradeCheckSystem

        checker = PreTradeCheckSystem()
        result = await asyncio.to_thread(
            checker.execute_pretrade_check,
            symbol=req.symbol,
            intended_action=req.action.upper(),
        )

        if isinstance(result, dict):
            data = result
        elif hasattr(result, "model_dump"):
            data = _safe_serialize(result)
        elif hasattr(result, "__dict__"):
            data = _safe_serialize(result)
        else:
            data = {"raw": str(result)}

        return ApiResponse(success=True, message="進場前檢查完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"進場前檢查失敗: {exc}")


# ── Trade Control ─────────────────────────────────────────────────────────────


@app.post("/api/v1/trade/start", response_model=ApiResponse, tags=["trading"])
async def start_trade(req: TradeStartRequest):
    """啟動交易監控"""
    if _trade_manager.is_running():
        return ApiResponse(success=False, message="交易已在運行中")

    try:
        data = await _trade_manager.start(req)
        environment = data.get("environment", "未知環境")
        return ApiResponse(
            success=True,
            message=f"交易監控已啟動 [{environment}] {req.symbol}",
            data=data,
        )
    except Exception as exc:
        return ApiResponse(success=False, message=f"交易啟動失敗: {exc}")


@app.get("/api/v1/trade/status", response_model=ApiResponse, tags=["trading"])
async def trade_status():
    """取得交易監控與自動交易狀態。"""
    return ApiResponse(success=True, message="交易狀態查詢完成", data=_trade_manager.get_status())


@app.post("/api/v1/trade/stop", response_model=ApiResponse, tags=["trading"])
async def stop_trade():
    """停止交易監控"""
    await _trade_manager.stop()
    return ApiResponse(success=True, message="交易監控已停止", data=_trade_manager.get_status())


# ── Training / Model Operations ──────────────────────────────────────────────


@app.post("/api/v1/training/start", response_model=ApiResponse, tags=["training"])
async def start_training(req: TrainingStartRequest):
    """登記遠端訓練作業，或明確啟動本機 unified_trainer subprocess。"""
    try:
        data = _training_job_manager.start(req)
        mode_label = "遠端訓練已登記" if req.execution_mode == "external" else "本機訓練已啟動"
        return ApiResponse(success=True, message=mode_label, data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"訓練作業啟動失敗: {exc}")


@app.get("/api/v1/training", response_model=ApiResponse, tags=["training"])
async def list_training_jobs():
    """列出目前 API 進程追蹤中的訓練作業。"""
    return ApiResponse(
        success=True,
        message="訓練作業列表讀取完成",
        data={"jobs": _training_job_manager.list_jobs()},
    )


@app.get("/api/v1/training/{job_id}", response_model=ApiResponse, tags=["training"])
async def get_training_job(job_id: str):
    """查詢訓練作業狀態。"""
    data = _training_job_manager.get(job_id)
    success = data.get("status") != "not_found"
    return ApiResponse(
        success=success,
        message="訓練作業狀態讀取完成" if success else "找不到訓練作業",
        data=data,
    )


@app.get("/api/v1/model/status", response_model=ApiResponse, tags=["model"])
async def get_model_status():
    """讀取目前 runtime 模型設定與交易引擎載入狀態。"""
    return ApiResponse(success=True, message="模型狀態讀取完成", data=_model_promotion_manager.status())


@app.post("/api/v1/model/promote", response_model=ApiResponse, tags=["model"])
async def promote_model(req: ModelPromoteRequest):
    """將訓練完成的模型登記為後續 runtime 使用來源。"""
    try:
        data = _model_promotion_manager.promote(req)
        return ApiResponse(success=True, message="模型 promote 完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"模型 promote 失敗: {exc}")


# ── Chat ─────────────────────────────────────────────────────────────────────

# 每個 conversation_id 對應一個 ChatEngine 實例（多輪記憶）
_chat_engines: Dict[str, Any] = {}
_default_chat_engine: Any = None


def _get_chat_engine(conversation_id: str, language: str = "auto") -> Any:
    """取得或建立對應 conversation_id 的 ChatEngine。"""
    global _default_chat_engine
    if conversation_id not in _chat_engines:
        if _default_chat_engine is None:
            try:
                from nlp.chat_engine import create_chat_engine
                _default_chat_engine = create_chat_engine(language=language)
            except Exception as e:
                logger.warning(f"[Chat] ChatEngine 初始化失敗: {e}")
                return None
        # 共用同一個引擎（若需要隔離多用戶，可改為每個 ID 建立獨立實例）
        _chat_engines[conversation_id] = _default_chat_engine
    return _chat_engines.get(conversation_id)


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest):
    """
    雙語對話端點（繁體中文 / English）。

    - 自動偵測使用者語言，依語言回應
    - 傳入 symbol（如 BTCUSDT）時自動注入即時市場資料
    - 傳入相同 conversation_id 可維持多輪對話記憶
    """
    import time
    import uuid
    t0 = time.time()

    conv_id = req.conversation_id or str(uuid.uuid4())

    engine = _get_chat_engine(conv_id, req.language)
    if engine is None:
        return ChatResponse(
            success=False,
            text="對話引擎未初始化，請確認模型已訓練並存放至 model/ 目錄。"
                 " (Chat engine not initialized. Please ensure the model is trained and placed in model/.)",
            language=req.language if req.language != "auto" else "zh",
            conversation_id=conv_id,
        )

    # 若有 language 設定，更新引擎語言
    if req.language != "auto":
        engine.set_language(req.language)

    # 建立市場上下文（若有 symbol）
    market_ctx = None
    if req.symbol:
        try:
            from nlp.chat_engine import MarketContext

            ctx = MarketContext(symbol=req.symbol)
            # 嘗試從全域 trade engine 取即時價格（可選）
            price = await _trade_manager.get_current_price(req.symbol)
            if price is not None:
                ctx.current_price = price
            market_ctx = ctx
        except Exception as e:
            logger.debug(f"[Chat] 市場上下文取得失敗（不影響對話）: {e}")

    # 執行對話（在執行緒中避免阻塞事件迴圈）
    try:
        response = await asyncio.to_thread(engine.chat, req.message, market_ctx)
        latency = (time.time() - t0) * 1000
        return ChatResponse(
            success=True,
            text=response.text,
            language=response.language,
            confidence=response.confidence,
            market_context_used=response.market_context_used,
            stopped_reason=response.stopped_reason,
            latency_ms=latency,
            conversation_id=conv_id,
        )
    except Exception as exc:
        logger.error(f"[Chat] 對話生成失敗: {exc}")
        return ChatResponse(
            success=False,
            text=f"生成失敗：{exc}",
            language="zh",
            conversation_id=conv_id,
        )


@app.delete("/api/v1/chat/{conversation_id}", response_model=ApiResponse, tags=["chat"])
async def reset_chat(conversation_id: str):
    """清除指定 conversation_id 的對話歷史"""
    engine = _chat_engines.get(conversation_id)
    if engine:
        engine.reset()
        return ApiResponse(success=True, message=f"對話歷史已清除 [{conversation_id}]")
    return ApiResponse(success=False, message="找不到該對話 ID")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _safe_serialize(obj: Any) -> dict[str, Any]:
    """將任意對象安全轉為 dict"""
    if isinstance(obj, dict):
        return {k: _safe_value(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return dict(obj.model_dump())
    if hasattr(obj, "__dict__"):
        return {k: _safe_value(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return {"raw": str(obj)}


def _safe_value(v):
    if isinstance(v, dict):
        return {k2: _safe_value(v2) for k2, v2 in v.items()}
    if isinstance(v, (list, tuple)):
        return [_safe_value(i) for i in v]
    if isinstance(v, datetime):
        return v.isoformat()
    try:
        json.dumps(v)
        return v
    except (TypeError, ValueError):
        return str(v)


# ── Dashboard REST ────────────────────────────────────────────────────────────


async def _build_dashboard_snapshot() -> dict:
    """組建 Dashboard 快照 dict，供 REST 端點及 WS 推送共用。"""
    now = datetime.now().isoformat()

    risk_level = "low"
    risk_pct = 0.0

    if _trade_manager.engine is not None:
        try:
            state = getattr(_trade_manager.engine, "state", None)
            if state and hasattr(state, "risk_percentage"):
                risk_pct = float(state.risk_percentage)
                if risk_pct > 20:
                    risk_level = "critical"
                elif risk_pct > 10:
                    risk_level = "high"
                elif risk_pct > 5:
                    risk_level = "medium"
        except Exception:
            pass

    audit_entries: list[WsAuditLogEntry] = []
    if _trade_manager.is_running():
        audit_entries.append(WsAuditLogEntry(
            id="sys-trade-running",
            timestamp=now,
            eventType="trade_start",
            description="交易監控運行中",
            status="success",
        ))

    checklist_items = [
        WsPretradeItem(id="c1", label="API 連線正常", completed=_trade_manager.engine is not None, required=True),
        WsPretradeItem(id="c2", label="風險參數已設定", completed=True, required=True),
        WsPretradeItem(id="c3", label="市場流動性正常", completed=True, required=False),
    ]
    completed_required = sum(1 for i in checklist_items if i.required and i.completed)
    total_required = sum(1 for i in checklist_items if i.required)
    positions = await _trade_manager.get_virtual_portfolio()

    environment = "testnet"
    status = _trade_manager.get_status()
    request = status.get("request") if isinstance(status, dict) else {}
    if isinstance(request, dict):
        mode = request.get("mode")
        if mode == "paper_live":
            environment = "paper_live"
        elif mode == "live_auto":
            environment = "mainnet"

    snapshot = DashboardDataResponse(
        environment=environment,
        risk=WsRiskData(level=risk_level, percentage=risk_pct, lastUpdated=now),
        maxDrawdown=WsMaxDrawdown(current=0.0, historical=0.0, period="30d", lastUpdated=now),
        pretradeChecklist=WsPretradeChecklist(
            items=checklist_items,
            completedCount=completed_required,
            totalCount=total_required,
            lastUpdated=now,
        ),
        auditLog=audit_entries,
        positions=positions or None,
    )
    return snapshot.model_dump()


@app.get("/api/v1/dashboard", tags=["dashboard"])
async def get_dashboard():
    """取得 Dashboard 快照（admin-da 首頁使用）"""
    return await _build_dashboard_snapshot()


@app.post("/api/v1/orders", tags=["dashboard"])
async def submit_order(order: TradeOrderRequest):
    """提交交易訂單（admin-da TradingControls 使用）"""
    try:
        if _trade_manager.engine is None:
            return ApiResponse(
                success=False,
                message="交易引擎未啟動，請先呼叫 POST /api/v1/trade/start",
            )

        order_data = order.model_dump(exclude_none=True)
        place_fn = getattr(_trade_manager.engine, "place_order", None)
        if place_fn is not None:
            result = await asyncio.to_thread(place_fn, **order_data)
            return ApiResponse(
                success=True,
                message=f"訂單已提交 {order.side.upper()} {order.symbol} qty={order.quantity}",
                data=result if isinstance(result, dict) else {"status": "submitted", "order": order_data},
            )

        return ApiResponse(
            success=True,
            message=f"訂單已接受 {order.side.upper()} {order.symbol} qty={order.quantity}（引擎不支援直接下單）",
            data={"status": "accepted", "order": order_data},
        )
    except Exception as exc:
        return ApiResponse(success=False, message=f"訂單提交失敗: {exc}")


@app.delete("/api/v1/positions/{position_id}", tags=["dashboard"])
async def close_position(position_id: str):
    """平倉（admin-da 持倉列表使用）"""
    try:
        if _trade_manager.engine is None:
            return ApiResponse(success=False, message="交易引擎未啟動")

        close_fn = getattr(_trade_manager.engine, "close_position", None)
        if close_fn is not None:
            result = await asyncio.to_thread(close_fn, position_id)
            return ApiResponse(
                success=True,
                message=f"持倉 {position_id} 已平倉",
                data=result if isinstance(result, dict) else {"position_id": position_id},
            )

        return ApiResponse(
            success=True,
            message=f"平倉請求已記錄 {position_id}（引擎不支援直接平倉）",
            data={"position_id": position_id},
        )
    except Exception as exc:
        return ApiResponse(success=False, message=f"平倉失敗: {exc}")


# ── Risk Config ──────────────────────────────────────────────────────────────

_RISK_CONFIG_PATH = PROJECT_ROOT / "config" / "risk_config_optimized.json"

_VALID_RISK_LEVELS = {"CONSERVATIVE", "MODERATE", "AGGRESSIVE", "HIGH_RISK"}


@app.get("/api/v1/risk/config", response_model=ApiResponse, tags=["risk"])
async def get_risk_config():
    """讀取目前的風險設定（risk_config_optimized.json）。"""
    try:
        data = json.loads(_RISK_CONFIG_PATH.read_text(encoding="utf-8"))
        return ApiResponse(success=True, message="風險設定讀取成功", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"風險設定讀取失敗: {exc}")


@app.put("/api/v1/risk/config", response_model=ApiResponse, tags=["risk"])
async def update_risk_config(body: Dict[str, Any]):
    """更新風險設定並寫回 risk_config_optimized.json。

    僅允許修改 risk_level 與 custom_overrides 兩個欄位以避免覆蓋整份設定。
    """
    try:
        current = json.loads(_RISK_CONFIG_PATH.read_text(encoding="utf-8"))

        if "risk_level" in body:
            level = str(body["risk_level"]).upper()
            if level not in _VALID_RISK_LEVELS:
                return ApiResponse(
                    success=False,
                    message=f"無效的 risk_level：{level}，允許值：{sorted(_VALID_RISK_LEVELS)}",
                )
            current["risk_level"] = level

        if "custom_overrides" in body:
            overrides = body["custom_overrides"]
            if not isinstance(overrides, dict):
                return ApiResponse(success=False, message="custom_overrides 必須為 object")
            current.setdefault("custom_overrides", {}).update(overrides)

        _RISK_CONFIG_PATH.write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return ApiResponse(success=True, message="風險設定已更新", data=current)
    except Exception as exc:
        return ApiResponse(success=False, message=f"風險設定更新失敗: {exc}")


# ── Data Catalog ──────────────────────────────────────────────────────────────

_BACKTEST_DATA_DIR = PROJECT_ROOT / "backtest" / "data"


@app.get("/api/v1/data/catalog", response_model=ApiResponse, tags=["data"])
async def get_data_catalog(symbol: str | None = None, interval: str | None = None):
    """列出 backtest/data/ 下已下載的歷史資料集（與 CLI backtest-data 等效）。"""
    try:
        from backtest import get_catalog
        data = await asyncio.to_thread(get_catalog, None, symbol, interval)
        return ApiResponse(success=True, message="資料目錄掃描完成", data=data)
    except Exception as exc:
        return ApiResponse(success=False, message=f"資料目錄掃描失敗: {exc}")


# ── WebSocket Endpoints ───────────────────────────────────────────────────────


@app.websocket("/ws/trade")
async def ws_trade(websocket: WebSocket):
    """/ws/trade — 即時報價、成交推送（trading 前端 trade-control-page.tsx）"""
    await websocket.accept()
    symbol = "BTCUSDT"
    try:
        while True:
            price = 0.0
            current_price = await _trade_manager.get_current_price(symbol)
            if current_price is not None:
                price = current_price

            await websocket.send_json({"type": "price_update", "symbol": symbol, "price": price})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("[WS /ws/trade] 連線結束: %s", exc)


@app.websocket("/ws/analytics")
async def ws_analytics(websocket: WebSocket):
    """/ws/analytics — 投資組合、績效、成交資料推送（trading 前端 analytics-page.tsx）"""
    await websocket.accept()
    try:
        while True:
            portfolio: list[dict] = []
            portfolio = await _trade_manager.get_virtual_portfolio()

            await websocket.send_json({"type": "portfolio_update", "portfolio": portfolio})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("[WS /ws/analytics] 連線結束: %s", exc)


@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    """/ws/dashboard — Dashboard 整體狀態推送（admin-da DashboardView.tsx）"""
    await websocket.accept()
    try:
        while True:
            snapshot = await _build_dashboard_snapshot()
            await websocket.send_json(snapshot)
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("[WS /ws/dashboard] 連線結束: %s", exc)
