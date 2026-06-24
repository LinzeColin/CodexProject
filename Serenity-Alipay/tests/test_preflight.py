from dataclasses import replace
from pathlib import Path

from app.core.preflight import _check_benchmarks, _check_moomoo, run_preflight
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
    assert mail_send_config["evidence"]["activation_hint"] == "--send-mail"
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


def test_check_moomoo_warns_when_live_opend_unavailable(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    observed_kwargs = {}

    def fake_smoke(settings_arg, **kwargs):
        observed_kwargs.update(kwargs)
        return {
            "production_ready_for_moomoo_data": False,
            "socket": {"detail": "socket down"},
            "sdk": {"detail": "sdk ok"},
            "workbenches": [],
            "recommended_actions": ["start OpenD"],
            "json_path": "moomoo.json",
            "markdown_path": "moomoo.md",
        }

    monkeypatch.setattr("app.core.preflight.run_moomoo_smoke", fake_smoke)

    result = _check_moomoo(settings)

    assert result.status == "warn"
    assert observed_kwargs["auto_start_opend"] is False
    assert result.evidence["auto_start_skipped_for_preflight"] is True


def test_check_benchmarks_does_not_autostart_opend(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    observed_kwargs = {}

    def fake_benchmark_smoke(settings_arg, **kwargs):
        observed_kwargs.update(kwargs)
        return {
            "production_ready": True,
            "production_ready_by_benchmark": {"Shanghai Composite": True, "S&P 500": True},
            "proxy_available": {},
            "json_path": "benchmark.json",
            "markdown_path": "benchmark.md",
        }

    monkeypatch.setattr("app.core.preflight.run_benchmark_smoke", fake_benchmark_smoke)

    result = _check_benchmarks(settings)

    assert result.status == "pass"
    assert observed_kwargs["auto_start_opend"] is False
    assert observed_kwargs["cleanup_auto_started"] is False
    assert result.evidence["auto_start_skipped_for_preflight"] is True
    assert result.severity == "info"
