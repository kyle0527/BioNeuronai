"""
Smoke tests — 驗證核心模組可正常匯入與基本功能。

執行方式:
    python -m pytest tests/ -v
"""
import sys
from pathlib import Path

# 確保 src/ 在路徑中
_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ── 匯入 smoke tests ──────────────────────────────────────────────────────────

def test_bioneuronai_package_importable():
    """bioneuronai 主套件可匯入。"""
    import bioneuronai  # noqa: F401


def test_fastapi_app_importable():
    """FastAPI app 可匯入（不啟動伺服器）。"""
    from bioneuronai.api.app import app
    assert app is not None


def test_schemas_rag_importable():
    """schemas.rag 中的 EventContext 可匯入。"""
    from schemas.rag import EventContext
    ctx = EventContext(event_score=1.0, event_type="MACRO", intensity="HIGH")
    assert ctx.event_type == "MACRO"
    assert ctx.intensity == "HIGH"


def test_plan_controller_importable():
    """TradingPlanController 可匯入。"""
    from bioneuronai.planning.plan_controller import TradingPlanController  # noqa: F401


def test_legacy_model_importable():
    """HundredMillionModel 可從正式路徑匯入（不依賴 archived/）。"""
    from bioneuronai.models.legacy import HundredMillionModel
    model = HundredMillionModel(input_dim=64, hidden_dims=[128], output_dim=32)
    assert model.count_parameters() > 0


def test_cors_config_no_wildcard():
    """CORS 設定在無環境變數時不應包含萬用字元 '*'。"""
    from bioneuronai.api.app import _get_allowed_origins
    origins = _get_allowed_origins()
    assert "*" not in origins, (
        "allow_origins 不應設為 ['*']；"
        "請透過 ALLOWED_ORIGINS 環境變數設定允許的來源"
    )
