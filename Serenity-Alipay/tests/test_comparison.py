from pathlib import Path

from app.core.comparison import persist_comparisons
from app.core.discipline import persist_rebalance_events
from app.db import connect, init_db
from tests.helpers import temp_settings


def _insert_run(conn, run_id: str, when: str, assets: list[str]):
    conn.execute(
        """
        INSERT INTO run_log (
          run_id, run_time_bj, run_time_au, schedule_slot, model_profile, status,
          data_quality_status, notification_status, notes, report_path, offline_html_path, created_at
        )
        VALUES (?, ?, ?, 'R7', 'test', 'success', 'pass', 'drafted', '', 'r.md', 'r.html', ?)
        """,
        (run_id, when, when, when),
    )
    for idx, asset in enumerate(assets, start=1):
        conn.execute(
            """
            INSERT INTO recommendation_snapshot (
              run_id, asset_id, rank, target_weight, current_weight, deviation,
              action_label, trigger_reason, next_check_by, manual_review_required
            )
            VALUES (?, ?, ?, ?, 0, ?, 'Maintain', 'test', 'next', 0)
            """,
            (run_id, asset, idx, 0.2, 0.2),
        )
        conn.execute(
            """
            INSERT INTO score_snapshot (
              run_id, asset_id, total_score, data_score, timeliness_score,
              source_score, return_score, risk_score, executable_score,
              evidence_coverage, grade, hard_block_reason
            )
            VALUES (?, ?, ?, 25, 15, 15, 15, 20, 10, 1, 'Action-Ready', NULL)
            """,
            (run_id, asset, 100 - idx),
        )


def test_persist_comparisons_detects_new_top5_assets(tmp_path: Path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        _insert_run(conn, "base", "2026-06-12T13:30:00+08:00", ["A", "B", "C", "D", "E"])
        _insert_run(conn, "current", "2026-06-12T14:00:00+08:00", ["A", "B", "C", "F", "G"])
        summaries, events = persist_comparisons(conn, "current", "2026-06-12T06:00:00+00:00", settings)
        persist_rebalance_events(conn, "current", "2026-06-12T06:00:00+00:00", events)
        same_day = next(item for item in summaries if item.compare_type == "same_day_previous")
        assert same_day.new_count == 2
        assert same_day.replacement_count == 2
        assert any("replaced 2" in event.trigger_reason for event in events)


def test_persist_comparisons_skips_weekend_base_runs(tmp_path: Path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        _insert_run(conn, "friday", "2026-06-12T14:00:00+08:00", ["A", "B", "C", "D", "E"])
        _insert_run(conn, "weekend", "2026-06-13T14:00:00+08:00", ["V", "W", "X", "Y", "Z"])
        _insert_run(conn, "current", "2026-06-15T14:00:00+08:00", ["A", "B", "C", "D", "E"])

        summaries, events = persist_comparisons(conn, "current", "2026-06-15T06:00:00+00:00", settings)

    previous_day = next(item for item in summaries if item.compare_type == "previous_day")
    assert previous_day.base_run_id == "friday"
    assert previous_day.top5_change_rate == 0.0
    assert events == []
