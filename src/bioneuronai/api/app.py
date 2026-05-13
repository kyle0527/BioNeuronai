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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── 路徑設定 ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bioneuronai.api.models import (  # noqa: E402
    ModelPromoteRequest,
    TradeStartRequest,
    TrainingStartRequest,
)
from bioneuronai.api.routes.analysis import router as analysis_router  # noqa: E402
from bioneuronai.api.routes.backtest import router as backtest_router  # noqa: E402
from bioneuronai.api.routes.chat import create_router as create_chat_router  # noqa: E402
from bioneuronai.api.routes.dashboard import create_router as create_dashboard_router  # noqa: E402
from bioneuronai.api.routes.system import router as system_router  # noqa: E402
from bioneuronai.api.routes.trading import create_router as create_trading_router  # noqa: E402
from bioneuronai.api.routes.training import create_router as create_training_router  # noqa: E402

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
        materialized_path: Optional[str]
        resolved_runtime_path = req.model_path
        materialized = self._resolve_promoted_path(req.model_path, req.model_name)
        materialized_path = str(materialized)

        if req.validate_path:
            if not materialized.exists():
                raise FileNotFoundError(f"model artifact not found: {materialized}")

        if req.model_path.endswith("/") or not Path(req.model_path).suffix:
            os.environ["MODEL_DIR"] = str(materialized.parent)
            os.environ.pop("MODEL_PATH", None)
        else:
            os.environ["MODEL_PATH"] = str(materialized)
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
        if not resolved.is_absolute():
            resolved = PROJECT_ROOT / resolved
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
            resolved_dir = self._resolve_promoted_path(model_path, str(active.get("model_name") or "my_100m_model")).parent
            os.environ.setdefault("MODEL_DIR", str(resolved_dir))
        else:
            os.environ.setdefault("MODEL_PATH", str(self._resolve_promoted_path(model_path, "")))


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

app.include_router(system_router)
app.include_router(analysis_router)
app.include_router(backtest_router)
app.include_router(create_trading_router(_trade_manager))
app.include_router(create_training_router(_training_job_manager, _model_promotion_manager))
app.include_router(create_chat_router(_trade_manager, logger))
app.include_router(create_dashboard_router(_trade_manager, PROJECT_ROOT, logger))
