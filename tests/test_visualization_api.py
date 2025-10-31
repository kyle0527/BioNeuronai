from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from bioneuronai.core import BioNet
from bioneuronai.visualization.api import app
from bioneuronai.visualization.stats import (
    InputRecord,
    collect_snapshot_from_bionet,
    default_stats_hub,
)


@pytest.fixture(autouse=True)
def _reset_hub() -> None:
    default_stats_hub.reset()
    yield
    default_stats_hub.reset()


def test_stats_endpoint_returns_serializable_snapshot() -> None:
    async def runner() -> None:
        net = BioNet()
        snapshot = collect_snapshot_from_bionet(net)
        default_stats_hub.update_snapshot(snapshot)
        default_stats_hub.log_input(
            InputRecord(values=[0.1, 0.9], outputs=[0.2, 0.3, 0.4], novelty=0.5, tag="pytest")
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert "snapshot" in data
        assert "inputs" in data
        assert "novelty_trend" in data
        assert "summary" in data

        snapshot_payload = data["snapshot"]
        assert set(snapshot_payload).issuperset({"novelty", "thresholds", "weight_distribution", "metadata", "timestamp"})
        assert isinstance(snapshot_payload["novelty"], dict)
        assert isinstance(snapshot_payload["thresholds"], dict)
        assert isinstance(snapshot_payload["weight_distribution"], dict)

        last_input = data["inputs"][-1]
        assert last_input["tag"] == "pytest"
        assert pytest.approx(last_input["novelty"], rel=1e-3) == 0.5

        summary = data["summary"]
        assert summary["inputs_logged"] >= 1
        assert summary["novelty_mean"] >= 0
        assert summary["threshold_mean"] >= 0

    asyncio.run(runner())


def test_inputs_endpoint_appends_history() -> None:
    async def runner() -> None:
        net = BioNet()
        default_stats_hub.update_snapshot(collect_snapshot_from_bionet(net))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            post_resp = await client.post(
                "/inputs",
                json={"values": [0.3, 0.7], "novelty": 0.2, "outputs": [0.4, 0.6, 0.8], "tag": "demo"},
            )
            assert post_resp.status_code == 204

            stats_resp = await client.get("/stats")

        assert stats_resp.status_code == 200
        inputs = stats_resp.json()["inputs"]
        assert inputs
        assert inputs[-1]["tag"] == "demo"
        assert pytest.approx(inputs[-1]["novelty"], rel=1e-3) == 0.2

    asyncio.run(runner())


def test_security_endpoint_updates_summary() -> None:
    async def runner() -> None:
        net = BioNet()
        default_stats_hub.update_snapshot(collect_snapshot_from_bionet(net))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/security",
                json={
                    "progress": 0.75,
                    "current_phase": "測試階段",
                    "issues_found": 2,
                    "notes": "pytest",
                },
            )
            assert resp.status_code == 204

            stats_resp = await client.get("/stats")
            assert stats_resp.status_code == 200

        payload = stats_resp.json()
        assert payload["snapshot"]["security_scan"]["current_phase"] == "測試階段"
        assert payload["snapshot"]["security_scan"]["issues_found"] == 2
        assert pytest.approx(payload["summary"]["security_progress"], rel=1e-3) == 0.75
        assert payload["summary"]["security_phase"] == "測試階段"
        assert payload["summary"]["security_issues"] == 2

    asyncio.run(runner())


def test_security_endpoint_requires_snapshot() -> None:
    async def runner() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/security",
                json={"progress": 0.3, "current_phase": "init"},
            )
            assert resp.status_code == 400

    asyncio.run(runner())
