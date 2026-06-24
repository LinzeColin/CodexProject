from dataclasses import replace
from pathlib import Path

from app.core.mail_policy import should_send_mail_for_run
from app.core.notification import _severity_for_run, notify_run
from app.core.pipeline import import_alipay_csv, run_slot
from app.db import connect, init_db
from tests.helpers import copy_sample_data, temp_settings


def test_notify_renders_mail_and_local_scripts(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    import_alipay_csv(settings, settings.imports_dir / "alipay_positions.csv")
    result = run_slot(settings, "R7", dry_run=True)
    pipeline_body = Path(result["notification_path"]).read_text(encoding="utf-8")
    pipeline_html_path = Path(result["notification_path"]).with_suffix(".html")
    pipeline_html = pipeline_html_path.read_text(encoding="utf-8")
    assert "## 结论" in pipeline_body
    assert "## 需要你做什么" in pipeline_body
    assert "## 持仓动作清单" in pipeline_body
    assert "## 风控兜底" in pipeline_body
    assert "来源与时间戳" not in pipeline_body
    assert "source chain" not in pipeline_body.lower()
    assert "Manual platform confirmation required" not in pipeline_body
    assert pipeline_html_path.exists()
    assert "<!doctype html>" in pipeline_html
    assert "<h1" in pipeline_html
    assert "一、结论" in pipeline_html
    assert "二、需变化的行为" in pipeline_html
    assert "三、当前持仓建议" in pipeline_html
    assert "需操作行为" in pipeline_html
    assert "<table" in pipeline_html
    assert "background-color" in pipeline_html
    assert "运行 ID" not in pipeline_html

    notified = notify_run(settings, result["run_id"], dry_run=True)
    assert Path(notified["draft_path"]).exists()
    assert Path(notified["html_path"]).exists()
    assert Path(notified["local_script_path"]).exists()
    assert notified["send_status"] == "drafted"
    assert "Serenity自动化" in notified["title"]
    body = Path(notified["draft_path"]).read_text(encoding="utf-8")
    assert "## 结论" in body
    assert "## 需要你做什么" in body
    assert "## 持仓动作清单" in body
    assert "## 风控兜底" in body
    assert "- 本轮运行：" in body
    assert " - " in body
    assert "CST" in body
    assert "来源与时间戳" not in body
    assert "sources_json" not in body
    assert "source chain" not in body.lower()
    assert "Manual platform confirmation required" not in body
    html_body = Path(notified["html_path"]).read_text(encoding="utf-8")
    assert "一、结论" in html_body
    assert "二、需变化的行为" in html_body
    assert "三、当前持仓建议" in html_body
    assert "当前结论" in html_body
    assert "需操作行为" in html_body
    assert "<strong" in html_body
    assert "<em>" in html_body


def test_observation_pool_manual_review_does_not_raise_notification_severity(tmp_path: Path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO run_log (
              run_id, run_time_bj, run_time_au, schedule_slot, model_profile,
              status, data_quality_status, notification_status, notes,
              report_path, offline_html_path, created_at
            )
            VALUES (
              'sda_test', '2026-06-15T12:30:00+08:00', '2026-06-15T14:30:00+10:00',
              'R5', 'test', 'success', 'pass', 'drafted', '',
              NULL, NULL, '2026-06-15T04:30:00+00:00'
            )
            """
        )
        for idx in range(1, 7):
            asset_id = f"FUND{idx}"
            conn.execute(
                """
                INSERT INTO asset_master (
                  asset_id, asset_code, asset_name, asset_type, market,
                  fund_company, risk_level, is_excluded, exclusion_reason
                )
                VALUES (?, ?, ?, 'off_platform_fund', 'CN', 'Manual', 'high', 0, '')
                """,
                (asset_id, asset_id, f"基金{idx}"),
            )
            conn.execute(
                """
                INSERT INTO score_snapshot (
                  run_id, asset_id, total_score, data_score, timeliness_score,
                  source_score, return_score, risk_score, executable_score,
                  evidence_coverage, grade, hard_block_reason
                )
                VALUES ('sda_test', ?, 80, 25, 15, 15, 15, 10, 0, 0.8, 'Watch', NULL)
                """,
                (asset_id,),
            )
            conn.execute(
                """
                INSERT INTO recommendation_snapshot (
                  run_id, asset_id, rank, target_weight, current_weight, deviation,
                  action_label, trigger_reason, next_check_by, manual_review_required
                )
                VALUES ('sda_test', ?, ?, 0, 0, 0, ?, 'fee/redemption/subscription status missing or closed', 'next', ?)
                """,
                (asset_id, idx, "Manual Review" if idx == 6 else "Maintain", 1 if idx == 6 else 0),
            )
        conn.execute(
            """
            INSERT INTO manual_review_queue (
              run_id, asset_id, reason, action_blocked, status, created_at
            )
            VALUES (
              'sda_test', 'FUND6', 'fee/redemption/subscription status missing or closed',
              'No-New-Order', 'open', '2026-06-15T04:30:00+00:00'
            )
            """
        )

        assert _severity_for_run(conn, "sda_test") == "Info"


def test_mail_policy_suppresses_unchanged_info_but_sends_material_changes():
    maintain_rows = [{"action_label": "Maintain"} for _ in range(5)]
    buy_rows = [{"action_label": "Maintain"} for _ in range(4)] + [{"action_label": "Pause New"}]

    assert should_send_mail_for_run("Info", maintain_rows, data_quality_status="pass") is False
    assert should_send_mail_for_run("Alert", maintain_rows, data_quality_status="pass") is False
    assert should_send_mail_for_run("Info", buy_rows, data_quality_status="pass") is True
    assert should_send_mail_for_run("Urgent", maintain_rows, data_quality_status="pass") is True
    assert should_send_mail_for_run("Warn", maintain_rows, data_quality_status="manual_review") is False
    assert should_send_mail_for_run("Info", buy_rows, data_quality_status="manual_review") is False
    assert should_send_mail_for_run("Urgent", maintain_rows, data_quality_status="manual_review") is True


def test_notify_run_suppresses_real_mail_when_top5_unchanged(monkeypatch, tmp_path: Path):
    settings = replace(temp_settings(tmp_path), mail_send_enabled=True)
    init_db(settings.db_path)
    called = {"mail": False}

    def fake_send(*args, **kwargs):
        called["mail"] = True
        return {"status": "sent", "error": ""}

    monkeypatch.setattr("app.core.notification.send_with_apple_mail", fake_send)
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO run_log (
              run_id, run_time_bj, run_time_au, schedule_slot, model_profile,
              status, data_quality_status, notification_status, notes,
              report_path, offline_html_path, created_at
            )
            VALUES (
              'sda_keep', '2026-06-15T12:30:00+08:00', '2026-06-15T14:30:00+10:00',
              'R5', 'test', 'success', 'pass', 'drafted', '',
              NULL, NULL, '2026-06-15T04:30:00+00:00'
            )
            """
        )
        for idx in range(1, 6):
            asset_id = f"FUND{idx}"
            conn.execute(
                """
                INSERT INTO asset_master (
                  asset_id, asset_code, asset_name, asset_type, market,
                  fund_company, risk_level, is_excluded, exclusion_reason
                )
                VALUES (?, ?, ?, 'off_platform_fund', 'CN', 'Manual', 'high', 0, '')
                """,
                (asset_id, asset_id, f"基金{idx}"),
            )
            conn.execute(
                """
                INSERT INTO score_snapshot (
                  run_id, asset_id, total_score, data_score, timeliness_score,
                  source_score, return_score, risk_score, executable_score,
                  evidence_coverage, grade, hard_block_reason
                )
                VALUES ('sda_keep', ?, 90, 25, 15, 15, 15, 10, 10, 0.9, 'Action-Ready', NULL)
                """,
                (asset_id,),
            )
            conn.execute(
                """
                INSERT INTO recommendation_snapshot (
                  run_id, asset_id, rank, target_weight, current_weight, deviation,
                  action_label, trigger_reason, next_check_by, manual_review_required
                )
                VALUES ('sda_keep', ?, ?, 0.2, 0.2, 0, 'Maintain', 'serenity unchanged', 'next', 0)
                """,
                (asset_id, idx),
            )

    result = notify_run(settings, "sda_keep", dry_run=False, send_mail=True)

    assert called["mail"] is False
    assert result["send_status"] == "suppressed_no_material_change"
    with connect(settings.db_path) as conn:
        row = conn.execute(
            "SELECT send_status FROM notification_log WHERE run_id='sda_keep' ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
    assert row["send_status"] == "suppressed_no_material_change"


def test_notify_run_suppresses_real_mail_for_manual_review_lock(monkeypatch, tmp_path: Path):
    settings = replace(temp_settings(tmp_path), mail_send_enabled=True)
    init_db(settings.db_path)
    called = {"mail": False}

    def fake_send(*args, **kwargs):
        called["mail"] = True
        return {"status": "sent", "error": ""}

    monkeypatch.setattr("app.core.notification.send_with_apple_mail", fake_send)
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO run_log (
              run_id, run_time_bj, run_time_au, schedule_slot, model_profile,
              status, data_quality_status, notification_status, notes,
              report_path, offline_html_path, created_at
            )
            VALUES (
              'sda_manual_lock', '2026-06-15T12:30:00+08:00', '2026-06-15T14:30:00+10:00',
              'R5', 'test', 'degraded', 'manual_review', 'drafted', '',
              NULL, NULL, '2026-06-15T04:30:00+00:00'
            )
            """
        )
        for idx in range(1, 6):
            asset_id = f"LOCK{idx}"
            conn.execute(
                """
                INSERT INTO asset_master (
                  asset_id, asset_code, asset_name, asset_type, market,
                  fund_company, risk_level, is_excluded, exclusion_reason
                )
                VALUES (?, ?, ?, 'off_platform_fund', 'CN', 'Manual', 'high', 0, '')
                """,
                (asset_id, asset_id, f"锁定基金{idx}"),
            )
            conn.execute(
                """
                INSERT INTO score_snapshot (
                  run_id, asset_id, total_score, data_score, timeliness_score,
                  source_score, return_score, risk_score, executable_score,
                  evidence_coverage, grade, hard_block_reason
                )
                VALUES ('sda_manual_lock', ?, 72, 10, 10, 10, 15, 17, 10, 0.7, 'Watch', NULL)
                """,
                (asset_id,),
            )
            conn.execute(
                """
                INSERT INTO recommendation_snapshot (
                  run_id, asset_id, rank, target_weight, current_weight, deviation,
                  action_label, trigger_reason, next_check_by, manual_review_required
                )
                VALUES ('sda_manual_lock', ?, ?, 0.2, 0.0, 0.2, 'Pause New',
                        '数据不足，暂停新增', 'next', 1)
                """,
                (asset_id, idx),
            )

    result = notify_run(settings, "sda_manual_lock", dry_run=False, send_mail=True)

    assert called["mail"] is False
    assert result["send_status"] == "suppressed_no_material_change"
    with connect(settings.db_path) as conn:
        row = conn.execute(
            "SELECT send_status, error_message FROM notification_log WHERE run_id='sda_manual_lock' ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
    assert row["send_status"] == "suppressed_no_material_change"
    assert "data-quality locks stay in app/report" in row["error_message"]
