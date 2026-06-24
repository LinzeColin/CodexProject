from pathlib import Path

from app.adapters.moomoo_adapter import MoomooHealth
from app.core.pipeline import run_slot
from app.db import connect
from tests.helpers import copy_sample_data, temp_settings


def test_run_slot_cleans_auto_started_opend_after_outputs_are_written(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    handle = object()
    cleanup_calls = []

    monkeypatch.setattr(
        "app.core.pipeline.moomoo_adapter.healthcheck",
        lambda **kwargs: MoomooHealth(
            available=True,
            status="available",
            detail="fake OpenD available",
            sdk_available=True,
            opend_lifecycle={"started_by_tool": True},
            opend_lifecycle_handle=handle,
            cleanup_required=True,
        ),
    )

    def fake_cleanup(lifecycle_handle):
        cleanup_calls.append(lifecycle_handle)
        assert (settings.reports_dir).exists()
        return {"cleanup_attempted": True, "cleanup_result": "terminated_started_processes:123"}

    monkeypatch.setattr("app.core.moomoo_lifecycle.cleanup_started_processes", fake_cleanup)

    result = run_slot(settings, "R7", dry_run=False)

    assert cleanup_calls == [handle]
    assert Path(result["report_path"]).exists()
    assert result["moomoo_cleanup"]["cleanup_result"] == "terminated_started_processes:123"
    with connect(settings.db_path) as conn:
        row = conn.execute(
            "SELECT message FROM audit_log WHERE run_id=? AND event_type='moomoo_opend_cleanup'",
            (result["run_id"],),
        ).fetchone()
    assert row["message"] == "terminated_started_processes:123"


def test_run_slot_dry_run_does_not_auto_start_opend(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    observed = {}

    def fake_healthcheck(**kwargs):
        observed.update(kwargs)
        return MoomooHealth(
            available=False,
            status="unavailable",
            detail="fake OpenD not used for dry-run",
            sdk_available=True,
        )

    monkeypatch.setattr("app.core.pipeline.moomoo_adapter.healthcheck", fake_healthcheck)

    result = run_slot(settings, "R7", dry_run=True)

    assert observed["auto_start_opend"] is False
    assert result["moomoo_cleanup"] is None
