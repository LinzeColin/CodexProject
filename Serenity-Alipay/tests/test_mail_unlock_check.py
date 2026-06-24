from __future__ import annotations

import plistlib
from pathlib import Path

from app.core.mail_unlock_check import build_mail_unlock_check
from tests.helpers import temp_settings


def _write_launchd_plist(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "Label": "com.serenity.daily-analysis",
        "ProgramArguments": [
            "/opt/anaconda3/bin/python",
            "-m",
            "app.cli",
            "automation-tick",
            "--no-dry-run",
            "--send-mail",
            "--local",
            "--json",
        ],
    }
    with path.open("wb") as handle:
        plistlib.dump(data, handle)


def test_mail_unlock_check_generates_template_without_sending_or_installing(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    _write_launchd_plist(settings.root_dir / "outputs" / "implementation" / "com.serenity.daily-analysis.plist")
    monkeypatch.setattr(
        "app.core.mail_unlock_check.run_mail_smoke",
        lambda settings, send=False: {
            "status": "pass",
            "draft_ready": True,
            "production_send_ready": False,
            "json_path": str(settings.root_dir / "outputs" / "preflight" / "apple_mail_smoke_latest.json"),
            "apple_mail": {"app_scriptable": True},
        },
    )

    result = build_mail_unlock_check(settings)

    assert result["status"] == "pass"
    assert result["workflow_ready"] is True
    assert result["mail_sent"] is False
    assert result["launchd_modified"] is False
    assert result["trades_placed"] is False
    production_plist = Path(str(result["production_plist_path"]))
    assert production_plist.exists()
    with production_plist.open("rb") as handle:
        data = plistlib.load(handle)
    assert data["ProgramArguments"][3:] == ["automation-tick", "--no-dry-run", "--send-mail", "--local", "--json"]
    assert "EnvironmentVariables" not in data or (
        "SERENITY_MAIL_SEND_ENABLED" not in data["EnvironmentVariables"]
        and "SERENITY_DRY_RUN" not in data["EnvironmentVariables"]
    )
    assert Path(str(result["json_path"])).exists()
    assert Path(str(result["markdown_path"])).exists()


def test_mail_unlock_check_blocks_when_launchd_template_missing(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    monkeypatch.setattr(
        "app.core.mail_unlock_check.run_mail_smoke",
        lambda settings, send=False: {
            "status": "pass",
            "draft_ready": True,
            "production_send_ready": False,
            "json_path": "smoke.json",
            "apple_mail": {"app_scriptable": True},
        },
    )

    result = build_mail_unlock_check(settings)

    assert result["status"] == "blocked"
    assert result["workflow_ready"] is False
    assert result["mail_sent"] is False
    assert result["launchd_modified"] is False
