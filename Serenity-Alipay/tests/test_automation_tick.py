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
