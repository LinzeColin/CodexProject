from dataclasses import replace
import fcntl
from pathlib import Path

from app.core.automation_tick import automation_tick
from app.core.pipeline import import_alipay_csv
from tests.helpers import copy_sample_data, temp_settings


def test_automation_tick_runs_due_slot_and_forces_dry_run_when_preflight_blocks(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    import_alipay_csv(settings, settings.imports_dir / "alipay_positions.csv")

    def fake_preflight(settings, scan_paths=None):
        return {
            "production_ready": False,
            "shadow_ready": True,
            "status": "blocked",
            "blockers": [{"name": "alipay_positions", "message": "sample"}],
            "warnings": [],
            "json_path": "preflight.json",
            "markdown_path": "preflight.md",
        }

    monkeypatch.setattr("app.core.automation_tick.run_preflight", fake_preflight)

    result = automation_tick(
        settings,
        now="2026-06-12T14:30:00+08:00",
        dry_run=False,
        allow_duplicate=True,
    )

    assert result["action"] == "ran"
    assert result["due_slot"] == "R7"
    assert result["effective_dry_run"] is True
    assert result["dry_run_forced_by_preflight"] is True
    assert result["preflight"]["blockers"][0]["name"] == "alipay_positions"
    assert result["notification"]["send_status"] == "drafted"


def test_automation_tick_skips_preflight_when_no_due_slot(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    called = False

    def fake_preflight(settings, scan_paths=None):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr("app.core.automation_tick.run_preflight", fake_preflight)

    result = automation_tick(settings, now="2026-06-12T14:12:00+08:00")

    assert result["action"] == "no_due_slot"
    assert result["preflight"] is None
    assert called is False


def test_automation_tick_skips_preflight_on_beijing_weekend(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    called = False

    def fake_preflight(settings, scan_paths=None):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr("app.core.automation_tick.run_preflight", fake_preflight)

    result = automation_tick(settings, now="2026-06-13T14:30:00+08:00", dry_run=False)

    assert result["action"] == "non_business_day"
    assert result["due_slot"] is None
    assert result["preflight"] is None
    assert result["effective_dry_run"] is True
    assert called is False


def test_automation_tick_enables_real_mail_for_explicit_send(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    seen = {"preflight": None, "notify": None, "scheduler": None, "portal": None}

    def fake_preflight(runtime_settings, scan_paths=None):
        seen["preflight"] = runtime_settings.mail_send_enabled
        return {
            "production_ready": True,
            "shadow_ready": True,
            "status": "pass",
            "blockers": [],
            "warnings": [],
            "json_path": "preflight.json",
            "markdown_path": "preflight.md",
        }

    def fake_scheduler(runtime_settings, **kwargs):
        seen["scheduler"] = runtime_settings.mail_send_enabled
        return {"action": "ran", "due_slot": "R7", "run_id": "run_123"}

    def fake_notify(runtime_settings, run_id, dry_run, send_mail, local):
        seen["notify"] = runtime_settings.mail_send_enabled
        return {"send_status": "sent", "local_status": "sent"}

    def fake_build_application_portal(runtime_settings, *, install_apps=True):
        seen["portal"] = install_apps
        return {"status": "pass", "current_run_id": "run_123"}

    monkeypatch.setattr("app.core.automation_tick.run_preflight", fake_preflight)
    monkeypatch.setattr("app.core.automation_tick.scheduler_tick", fake_scheduler)
    monkeypatch.setattr("app.core.automation_tick.notify_run", fake_notify)
    monkeypatch.setattr("app.core.automation_tick.build_application_portal", fake_build_application_portal)

    result = automation_tick(
        settings,
        now="2026-06-12T14:30:00+08:00",
        dry_run=False,
        send_mail=True,
        local=True,
        allow_duplicate=True,
    )

    assert result["effective_dry_run"] is False
    assert result["dry_run_forced_by_preflight"] is False
    assert result["notification"]["send_status"] == "sent"
    assert result["application_portal"]["current_run_id"] == "run_123"
    assert seen == {"preflight": True, "notify": True, "scheduler": True, "portal": False}


def test_automation_tick_skips_when_previous_tick_lock_is_held(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    lock_handle = (settings.data_dir / "automation_tick.lock").open("w", encoding="utf-8")
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    called = {"preflight": False, "scheduler": False}

    def fake_preflight(*args, **kwargs):
        called["preflight"] = True
        return {}

    def fake_scheduler(*args, **kwargs):
        called["scheduler"] = True
        return {}

    monkeypatch.setattr("app.core.automation_tick.run_preflight", fake_preflight)
    monkeypatch.setattr("app.core.automation_tick.scheduler_tick", fake_scheduler)

    try:
        result = automation_tick(settings, now="2026-06-12T14:30:00+08:00", dry_run=False)
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()

    assert result["action"] == "skipped_locked"
    assert result["preflight"] is None
    assert called == {"preflight": False, "scheduler": False}
