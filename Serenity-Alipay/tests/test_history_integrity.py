from pathlib import Path
import csv

from app.core.history_integrity import run_history_integrity
from app.db import connect, init_db, insert_row, upsert_asset
from tests.helpers import temp_settings


def _run_row(settings, run_id: str, status: str = "success") -> dict[str, object]:
    return {
        "run_id": run_id,
        "run_time_bj": "2026-06-12T14:00:00+08:00",
        "run_time_au": "2026-06-12T16:00:00+10:00",
        "schedule_slot": "R7",
        "model_profile": settings.model_profile,
        "status": status,
        "data_quality_status": "pass",
        "notification_status": "sent",
        "notes": "",
        "report_path": f"data/reports/{run_id}_report.md",
        "offline_html_path": f"data/reports/{run_id}_report.html",
        "created_at": "2026-06-12T06:00:00+00:00",
    }


def test_history_integrity_allows_append_but_blocks_mutation(tmp_path: Path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    (settings.reports_dir / "r1_report.md").write_text("historical report v1", encoding="utf-8")
    (settings.reports_dir / "r1_report.html").write_text("<h1>historical report v1</h1>", encoding="utf-8")
    with connect(settings.db_path) as conn:
        insert_row(conn, "run_log", _run_row(settings, "r1"))

    baseline = run_history_integrity(settings, write_baseline=True)
    assert baseline["status"] == "pass"
    assert baseline["baseline_written"] is True
    artifact_timeline = Path(str(baseline["artifact_timeline_csv_path"]))
    snapshot_timeline = Path(str(baseline["snapshot_timeline_csv_path"]))
    assert artifact_timeline.exists()
    assert snapshot_timeline.exists()
    artifact_rows = list(csv.DictReader(artifact_timeline.open(encoding="utf-8")))
    report_row = next(row for row in artifact_rows if row["path"] == "data/reports/r1_report.md")
    assert report_row["artifact_type"] == "analysis_report_markdown"
    assert report_row["run_id"] == "r1"
    assert report_row["run_created_at"] == "2026-06-12T06:00:00+00:00"
    assert report_row["file_created_at"]
    assert report_row["file_modified_at"]
    assert report_row["sha256"]
    snapshot_rows = list(csv.DictReader(snapshot_timeline.open(encoding="utf-8")))
    assert any(row["table"] == "run_log" and row["row_count"] == "1" for row in snapshot_rows)

    (settings.reports_dir / "r2_report.md").write_text("historical report v2", encoding="utf-8")
    (settings.reports_dir / "r2_report.html").write_text("<h1>historical report v2</h1>", encoding="utf-8")
    with connect(settings.db_path) as conn:
        insert_row(conn, "run_log", _run_row(settings, "r2"))
    appended = run_history_integrity(settings)
    assert appended["status"] == "pass"
    assert appended["violation_count"] == 0

    with connect(settings.db_path) as conn:
        conn.execute("UPDATE run_log SET status='rewritten' WHERE run_id='r1'")
    mutated = run_history_integrity(settings)
    assert mutated["status"] == "block"
    assert any(
        violation["area"] == "sqlite" and violation["violation_type"] == "row_changed"
        for violation in mutated["violations"]
    )


def test_asset_master_keeps_first_seen_identity(tmp_path: Path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        upsert_asset(
            conn,
            {
                "asset_id": "FUND001",
                "asset_code": "FUND001",
                "asset_name": "历史名称",
                "asset_type": "off_platform_fund",
                "market": "CN",
                "fund_company": "历史基金公司",
                "risk_level": "high",
                "is_excluded": 0,
                "exclusion_reason": "",
            },
        )
        upsert_asset(
            conn,
            {
                "asset_id": "FUND001",
                "asset_code": "FUND001",
                "asset_name": "新名称不应覆盖",
                "asset_type": "rewritten_type",
                "market": "US",
                "fund_company": "新基金公司",
                "risk_level": "low",
                "is_excluded": 1,
                "exclusion_reason": "rewritten",
            },
        )
        row = conn.execute("SELECT * FROM asset_master WHERE asset_code='FUND001'").fetchone()

    assert row["asset_name"] == "历史名称"
    assert row["asset_type"] == "off_platform_fund"
    assert row["fund_company"] == "历史基金公司"
    assert row["is_excluded"] == 0
