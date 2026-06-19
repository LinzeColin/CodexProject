from pathlib import Path

from app.core.moomoo_smoke import run_moomoo_smoke
from tests.helpers import temp_settings


def test_moomoo_smoke_writes_diagnostics(tmp_path: Path):
    settings = temp_settings(tmp_path)
    result = run_moomoo_smoke(
        settings,
        port=1,
        timeout=0.05,
        include_user_codex=False,
    )

    assert result["status"] == "block"
    assert result["production_ready_for_moomoo_data"] is False
    assert result["socket"]["reachable"] is False
    assert "recommended_actions" in result
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()
