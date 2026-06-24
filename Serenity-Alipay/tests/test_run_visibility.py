from pathlib import Path

from app.core.application_portal import _latest_runs
from app.core.application_server import _latest_holdings
from app.core.pipeline import _write_offline_index
from app.core.run_visibility import display_run_time_with_backfill_note, is_future_controlled_backfill
from app.db import connect, init_db
from tests.helpers import temp_settings


def _insert_visible_test_run(
    conn,
    settings,
    *,
    run_id: str,
    run_time_bj: str,
    created_at: str,
    weight: float,
    slot: str = "R7",
) -> None:
    report_path = settings.reports_dir / f"{run_id}_report.md"
    html_path = settings.reports_dir / f"{run_id}_report.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("report", encoding="utf-8")
    html_path.write_text("<html></html>", encoding="utf-8")
    conn.execute(
        """
        INSERT INTO run_log (
          run_id, run_time_bj, run_time_au, schedule_slot, model_profile, status,
          data_quality_status, notification_status, notes, report_path, offline_html_path, created_at
        )
        VALUES (?, ?, ?, ?, 'test', 'success', 'pass', 'drafted', '', ?, ?, ?)
        """,
        (run_id, run_time_bj, run_time_bj, slot, str(report_path), str(html_path), created_at),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO asset_master (
          asset_id, asset_code, asset_name, asset_type, market, fund_company,
          risk_level, is_excluded, exclusion_reason
        )
        VALUES ('asset_007300', '007300', '国联安中证半导体ETF联接A', 'off_platform_fund',
                'CN', '国联安', 'high', 0, NULL)
        """
    )
    conn.execute(
        """
        INSERT INTO recommendation_snapshot (
          run_id, asset_id, rank, target_weight, current_weight, deviation,
          action_label, trigger_reason, next_check_by, manual_review_required
        )
        VALUES (?, 'asset_007300', 1, ?, ?, 0, 'Maintain', 'test', 'next', 0)
        """,
        (run_id, weight, weight),
    )
    conn.execute(
        """
        INSERT INTO score_snapshot (
          run_id, asset_id, total_score, data_score, timeliness_score,
          source_score, return_score, risk_score, executable_score,
          evidence_coverage, grade, hard_block_reason
        )
        VALUES (?, 'asset_007300', 90, 25, 15, 15, 15, 20, 10, 1, 'Action-Ready', NULL)
        """,
        (run_id,),
    )


def test_future_controlled_backfill_detection_and_plain_user_display():
    assert is_future_controlled_backfill(
        "2026-06-15T14:30:00+08:00",
        "2026-06-13T09:45:39+00:00",
    )
    assert not is_future_controlled_backfill(
        "2026-06-12T14:30:00+08:00",
        "2026-06-12T06:29:00+00:00",
    )
    assert display_run_time_with_backfill_note(
        "2026-06-15T14:30:00+08:00",
        "2026-06-13T09:45:39+00:00",
    ) == "20260615 - 14:30 CST"


def test_latest_surfaces_keep_latest_data_with_plain_run_time(tmp_path: Path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        _insert_visible_test_run(
            conn,
            settings,
            run_id="real_run",
            run_time_bj="2026-06-12T14:30:00+08:00",
            created_at="2026-06-12T06:30:30+00:00",
            weight=0.2,
        )
        _insert_visible_test_run(
            conn,
            settings,
            run_id="future_backfill",
            run_time_bj="2026-06-15T14:30:00+08:00",
            created_at="2026-06-13T09:45:39+00:00",
            weight=0.3,
        )
        _insert_visible_test_run(
            conn,
            settings,
            run_id="delayed_old_slot",
            run_time_bj="2026-06-14T12:30:00+08:00",
            created_at="2026-06-15T05:12:56+00:00",
            weight=0.1,
        )
        latest_runs = _latest_runs(conn, limit=1)
        index_path = _write_offline_index(conn, settings)

    latest_holdings = _latest_holdings(settings)

    assert [run.run_id for run in latest_runs] == ["delayed_old_slot"]
    assert latest_holdings["007300"].weight == 0.1
    index_html = index_path.read_text(encoding="utf-8")
    assert "real_run_report.html" in index_html
    assert "future_backfill_report.html" in index_html
    assert "20260615 - 14:30 CST" in index_html
    assert "验证回填，生成时间" not in index_html
