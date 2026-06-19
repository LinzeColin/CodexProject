from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core.pipeline import import_alipay_csv
from app.core.scheduler_runner import scheduler_tick
from app.db import connect
from app.scheduler import due_slot_at
from tests.helpers import copy_sample_data, temp_settings


def test_due_slot_at_uses_beijing_time():
    current = datetime(2026, 6, 12, 14, 31, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert due_slot_at(current, tolerance_minutes=3) == "R7"


def test_due_slot_at_skips_beijing_weekends_by_default():
    current = datetime(2026, 6, 13, 14, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert due_slot_at(current, tolerance_minutes=3) is None
    assert due_slot_at(current, tolerance_minutes=3, require_business_day=False) == "R7"


def test_scheduler_tick_runs_for_due_slot(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    import_alipay_csv(settings, settings.imports_dir / "alipay_positions.csv")
    result = scheduler_tick(
        settings,
        now="2026-06-12T14:30:00+08:00",
        dry_run=True,
        allow_duplicate=True,
    )
    assert result["action"] == "ran"
    assert result["due_slot"] == "R7"
    assert result["run_id"]


def test_scheduler_tick_passes_requested_backfill_date_to_run_log(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    result = scheduler_tick(
        settings,
        now="2099-01-05T14:30:00+08:00",
        dry_run=True,
        allow_duplicate=True,
    )

    with connect(settings.db_path) as conn:
        row = conn.execute(
            "SELECT run_time_bj, run_time_au FROM run_log WHERE run_id=?",
            (result["run_id"],),
        ).fetchone()

    assert result["action"] == "ran"
    assert row["run_time_bj"] == "2099-01-05T14:30:00+08:00"
    assert row["run_time_au"].startswith("2099-01-05T")


def test_scheduler_tick_records_non_business_day_without_run(tmp_path: Path):
    settings = temp_settings(tmp_path)
    result = scheduler_tick(
        settings,
        now="2026-06-13T14:30:00+08:00",
        dry_run=True,
        allow_duplicate=True,
    )
    assert result["action"] == "non_business_day"
    assert result["due_slot"] is None
    assert result["run_id"] is None
