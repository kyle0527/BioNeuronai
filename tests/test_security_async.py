import httpx
import pytest

from aiva_common.schemas import FunctionTaskPayload, FunctionTaskTarget
from bioneuronai.security import (
    EnhancedAuthModule,
    ProductionIDORModule,
    ProductionSQLiModule,
)


def _build_task(url: str, method: str = "GET", parameter: str | None = None) -> FunctionTaskPayload:
    target = FunctionTaskTarget(url=url, method=method, parameter=parameter)
    return FunctionTaskPayload(task_id="task", scan_id="scan", target=target)


def _mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok", request=request)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "module_factory,task",
    [
        (ProductionSQLiModule, _build_task("https://example.com/search", parameter="q")),
        (ProductionIDORModule, _build_task("https://example.com/users/1", parameter="user_id")),
        (EnhancedAuthModule, _build_task("https://example.com/login", method="POST")),
    ],
)
async def test_detection_modules_execute_without_errors(module_factory, task) -> None:
    module = module_factory()
    async with httpx.AsyncClient(transport=_mock_transport()) as client:
        findings = await module.execute_detection(task, client)
    assert isinstance(findings, list)
