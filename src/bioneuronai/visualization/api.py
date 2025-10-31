"""FastAPI application serving BioNeuronAI dashboard data and assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .stats import (
    InputRecord,
    NetworkSnapshot,
    SecurityScanStatus,
    default_stats_hub,
)

app = FastAPI(title="BioNeuronAI Dashboard", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InputPayload(BaseModel):
    """Incoming payload for streamed input values."""

    values: list[float]
    novelty: Optional[float] = None
    outputs: Optional[list[float]] = None
    tag: Optional[str] = None


class SecurityPayload(BaseModel):
    progress: float = Field(ge=0.0, le=1.0)
    current_phase: str
    issues_found: int = 0
    notes: Optional[str] = None


class SnapshotPayload(BaseModel):
    """Optional endpoint for clients to push pre-built snapshots."""

    snapshot: Dict[str, Any]


@app.get("/", response_class=HTMLResponse)
def dashboard_page() -> HTMLResponse:
    index_path = Path(__file__).with_name("static").joinpath("dashboard.html")
    if not index_path.exists():  # pragma: no cover - sanity guard
        raise HTTPException(status_code=404, detail="Dashboard assets missing")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/stats")
def read_stats() -> Dict[str, Any]:
    return default_stats_hub.get_network_stats()


@app.post("/inputs", status_code=204)
def add_input(payload: InputPayload) -> None:
    record = InputRecord(
        values=payload.values,
        novelty=payload.novelty,
        outputs=payload.outputs,
        tag=payload.tag,
    )
    default_stats_hub.log_input(record)


@app.post("/security", status_code=204)
def update_security(payload: SecurityPayload) -> None:
    current_snapshot = default_stats_hub.get_snapshot()
    if current_snapshot is None:
        raise HTTPException(status_code=400, detail="No snapshot available")

    status = SecurityScanStatus(
        progress=payload.progress,
        current_phase=payload.current_phase,
        issues_found=payload.issues_found,
        notes=payload.notes,
    )
    updated = current_snapshot.clone()
    updated.security_scan = status
    updated.timestamp = status.last_updated
    default_stats_hub.update_snapshot(updated)


@app.post("/snapshot", status_code=204)
def push_snapshot(payload: SnapshotPayload) -> None:
    snapshot = payload.snapshot
    required_fields = {"novelty", "thresholds", "weight_distribution"}
    if not required_fields.issubset(snapshot):
        missing = ", ".join(sorted(required_fields - set(snapshot)))
        raise HTTPException(status_code=400, detail=f"Missing fields: {missing}")

    default_stats_hub.update_snapshot(NetworkSnapshot.from_payload(snapshot))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        async for payload in default_stats_hub.subscribe():
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        return


__all__ = [
    "app",
    "dashboard_page",
    "read_stats",
]
