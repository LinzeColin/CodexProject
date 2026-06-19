from pathlib import Path

from app.core.preflight import run_preflight
from app.db import connect, init_db, insert_row
from tests.helpers import copy_sample_data, temp_settings


def test_preflight_blocks_sample_data(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    result = run_preflight(settings)
    assert result["production_ready"] is False
    blocker_names = {item["name"] for item in result["blockers"]}
    assert "alipay_positions" not in blocker_names
    assert "fund_rules" not in blocker_names
    assert "candidate_universe" not in blocker_names
    assert "mail_send_config" in blocker_names
    alipay = next(item for item in result["checks"] if item["name"] == "alipay_positions")
    assert alipay["evidence"]["production_dependency"] is False
    mail_send_config = next(item for item in result["checks"] if item["name"] == "mail_send_config")
    assert mail_send_config["evidence"]["mail_send_enabled"] is False
    assert mail_send_config["evidence"]["env_var"] == "SERENITY_MAIL_SEND_ENABLED"
    moomoo = next(item for item in result["checks"] if item["name"] == "moomoo_opend")
    assert "recommended_actions" in moomoo["evidence"]
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()


def test_preflight_latest_shadow_run_ignores_moomoo_collect(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        insert_row(
            conn,
            "run_log",
            {
                "run_id": "strategy_run",
                "run_time_bj": "2026-06-12T14:00:00+08:00",
                "run_time_au": "2026-06-12T16:00:00+10:00",
                "schedule_slot": "R7",
                "model_profile": settings.model_profile,
                "status": "degraded",
                "data_quality_status": "manual_review",
                "notification_status": "drafted",
                "notes": "",
                "report_path": "data/reports/strategy.md",
                "offline_html_path": None,
                "created_at": "2026-06-12T06:00:00+00:00",
            },
        )
        insert_row(
            conn,
            "run_log",
            {
                "run_id": "moomoo_collect",
                "run_time_bj": "2026-06-12T15:00:00+08:00",
                "run_time_au": "2026-06-12T17:00:00+10:00",
                "schedule_slot": "MOOMOO_COLLECT",
                "model_profile": settings.model_profile,
                "status": "success",
                "data_quality_status": "pass",
                "notification_status": "not_applicable",
                "notes": "",
                "report_path": "data/moomoo/snapshot.json",
                "offline_html_path": None,
                "created_at": "2026-06-12T07:00:00+00:00",
            },
        )

    result = run_preflight(settings)
    latest = next(item for item in result["checks"] if item["name"] == "latest_shadow_run")
    assert latest["evidence"]["run_id"] == "strategy_run"
