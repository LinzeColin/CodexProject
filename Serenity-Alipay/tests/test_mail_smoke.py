from pathlib import Path

from app.core.mail_smoke import run_mail_smoke
from tests.helpers import temp_settings


class _Completed:
    returncode = 0
    stdout = "com.apple.mail\n"
    stderr = ""


def test_mail_smoke_writes_draft_and_artifacts_without_sending(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    monkeypatch.setattr("app.core.mail_smoke.shutil.which", lambda name: "/usr/bin/osascript")
    monkeypatch.setattr("app.core.mail_smoke.subprocess.run", lambda *args, **kwargs: _Completed())

    result = run_mail_smoke(settings)

    assert result["status"] == "pass"
    assert result["draft_ready"] is True
    assert result["send_requested"] is False
    assert result["send_status"] == "not_requested"
    assert result["production_send_ready"] is False
    assert Path(result["draft_path"]).exists()
    assert Path(result["html_path"]).exists()
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()
    html_body = Path(result["html_path"]).read_text(encoding="utf-8")
    assert "<!doctype html>" in html_body
    assert "<h1" in html_body
    assert "<h2" in html_body
    assert "<h3" in html_body
    assert "<table" in html_body
    assert "HTML + 纯文本兜底" in html_body


def test_mail_smoke_blocks_real_send_when_runtime_send_not_enabled(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    monkeypatch.setattr("app.core.mail_smoke.shutil.which", lambda name: "/usr/bin/osascript")
    monkeypatch.setattr("app.core.mail_smoke.subprocess.run", lambda *args, **kwargs: _Completed())

    result = run_mail_smoke(settings, send=True, confirm_real_send="SEND")

    assert result["status"] == "blocked"
    assert result["send_status"] == "blocked_by_config"
    assert result["send_error"] == "Real sending is not enabled for this runtime"
