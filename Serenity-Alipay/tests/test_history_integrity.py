from pathlib import Path
import csv
import json

from app.core.history_integrity import _canonical_json, _sha256_text, run_history_integrity
from app.db import connect, init_db, insert_row, record_asset_pool_entries, upsert_asset
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


def test_history_integrity_allows_notification_log_appended_schema_columns(tmp_path: Path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    legacy_columns = [
        "notification_id",
        "run_id",
        "channel",
        "severity",
        "title",
        "body_path",
        "send_status",
        "sent_at",
        "error_message",
    ]
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO notification_log (
              notification_id, run_id, channel, severity, title,
              body_path, send_status, sent_at, error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "n1",
                "r1",
                "macos_mail",
                "Info",
                "Title",
                "data/notifications/n1.md",
                "drafted",
                None,
                None,
            ),
        )
        row = dict(conn.execute("SELECT * FROM notification_log WHERE notification_id='n1'").fetchone())

    baseline = run_history_integrity(settings, write_baseline=True)
    baseline_path = Path(str(baseline["baseline_path"]))
    baseline_data = json.loads(baseline_path.read_text(encoding="utf-8"))
    table = baseline_data["sqlite"]["tables"]["notification_log"]
    table["columns"] = legacy_columns
    table["rows"] = {
        "notification_id=n1": _sha256_text(_canonical_json({column: row.get(column) for column in legacy_columns}))
    }
    baseline_path.write_text(json.dumps(baseline_data, ensure_ascii=False, indent=2), encoding="utf-8")

    appended_schema = run_history_integrity(settings)
    assert appended_schema["status"] == "pass"
    assert appended_schema["violation_count"] == 0

    with connect(settings.db_path) as conn:
        conn.execute("UPDATE notification_log SET created_at='2026-06-12T06:00:00+00:00' WHERE notification_id='n1'")
    extra_column_changed = run_history_integrity(settings)
    assert extra_column_changed["status"] == "pass"
    assert extra_column_changed["violation_count"] == 0

    with connect(settings.db_path) as conn:
        conn.execute("UPDATE notification_log SET send_status='sent' WHERE notification_id='n1'")
    old_column_changed = run_history_integrity(settings)
    assert old_column_changed["status"] == "block"
    assert any(
        violation["area"] == "sqlite"
        and violation["item"] == "notification_log:notification_id=n1"
        and violation["violation_type"] == "row_changed"
        for violation in old_column_changed["violations"]
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


def test_asset_pool_entry_keeps_first_holding_pool_entry(tmp_path: Path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        upsert_asset(
            conn,
            {
                "asset_id": "FUND001",
                "asset_code": "FUND001",
                "asset_name": "基金一号",
                "asset_type": "off_platform_fund",
                "market": "CN",
                "fund_company": "基金公司",
                "risk_level": "high",
                "is_excluded": 0,
                "exclusion_reason": "",
            },
        )
        conn.executemany(
            """
            INSERT INTO run_log (
              run_id, run_time_bj, run_time_au, schedule_slot, model_profile,
              status, data_quality_status, notification_status, notes,
              report_path, offline_html_path, created_at
            )
            VALUES (?, ?, ?, ?, 'model', 'success', 'pass', 'sent', '', NULL, NULL, ?)
            """,
            [
                (
                    "r1",
                    "2026-06-12T08:30:00+08:00",
                    "2026-06-12T10:30:00+10:00",
                    "R1",
                    "2026-06-12T00:30:00+00:00",
                ),
                (
                    "r2",
                    "2026-06-13T08:30:00+08:00",
                    "2026-06-13T10:30:00+10:00",
                    "R1",
                    "2026-06-13T00:30:00+00:00",
                ),
            ],
        )
        conn.executemany(
            """
            INSERT INTO recommendation_snapshot (
              run_id, asset_id, rank, target_weight, current_weight, deviation,
              action_label, trigger_reason, next_check_by, manual_review_required
            )
            VALUES (?, 'FUND001', ?, 0.2, 0.0, 0.2, 'Buy', 'test', 'next', 0)
            """,
            [("r1", 5), ("r2", 1)],
        )

    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        record_asset_pool_entries(
            conn,
            run_id="r2",
            asset_id="FUND001",
            rank=1,
            run_time_bj="2026-06-13T08:30:00+08:00",
            run_time_au="2026-06-13T10:30:00+10:00",
            run_created_at="2026-06-13T00:30:00+00:00",
            created_at="2026-06-13T00:30:00+00:00",
        )
        holding = conn.execute(
            """
            SELECT first_run_id, first_rank, first_run_time_bj, first_run_created_at
            FROM asset_pool_entry
            WHERE asset_id='FUND001' AND pool_kind='holding_pool'
            """
        ).fetchone()
        candidate = conn.execute(
            """
            SELECT first_run_id
            FROM asset_pool_entry
            WHERE asset_id='FUND001' AND pool_kind='candidate_pool'
            """
        ).fetchone()

    assert holding["first_run_id"] == "r1"
    assert holding["first_rank"] == 5
    assert holding["first_run_time_bj"] == "2026-06-12T08:30:00+08:00"
    assert holding["first_run_created_at"] == "2026-06-12T00:30:00+00:00"
    assert candidate["first_run_id"] == "r1"
