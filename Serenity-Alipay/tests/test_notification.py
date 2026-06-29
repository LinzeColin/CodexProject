from dataclasses import replace
from pathlib import Path
from typing import Iterable

from app.core.mail_policy import should_send_mail_for_run
from app.core.notification import _severity_for_run, notify_run
from app.core.pipeline import import_alipay_csv, run_slot
from app.db import connect, init_db
from tests.helpers import copy_sample_data, temp_settings


def _insert_actionable_run(
    conn,
    *,
    run_id: str,
    run_time_bj: str,
    action_labels: Iterable[str],
    target_weights: Iterable[float] | None = None,
    data_quality_status: str = "pass",
) -> None:
    run_time_au = run_time_bj.replace("+08:00", "+10:00")
    created_at = run_time_bj.replace("+08:00", "+00:00")
    conn.execute(
        """
        INSERT INTO run_log (
          run_id, run_time_bj, run_time_au, schedule_slot, model_profile,
          status, data_quality_status, notification_status, notes,
          report_path, offline_html_path, created_at
        )
        VALUES (?, ?, ?, 'R5', 'test', 'success', ?, 'drafted', '',
          NULL, NULL, ?)
        """,
        (run_id, run_time_bj, run_time_au, data_quality_status, created_at),
    )
    actions = list(action_labels)
    weights = list(target_weights or [0.2 for _ in actions])
    for idx, action in enumerate(actions, start=1):
        asset_id = f"MAIL{idx}"
        asset_code = f"F{idx:03d}"
        conn.execute(
            """
            INSERT OR IGNORE INTO asset_master (
              asset_id, asset_code, asset_name, asset_type, market,
              fund_company, risk_level, is_excluded, exclusion_reason
            )
            VALUES (?, ?, ?, 'off_platform_fund', 'CN', 'Manual', 'high', 0, '')
            """,
            (asset_id, asset_code, f"邮件频控基金{idx}"),
        )
        conn.execute(
            """
            INSERT INTO score_snapshot (
              run_id, asset_id, total_score, data_score, timeliness_score,
              source_score, return_score, risk_score, executable_score,
              evidence_coverage, grade, hard_block_reason
            )
            VALUES (?, ?, 90, 25, 15, 15, 15, 10, 10, 0.9, 'Action-Ready', NULL)
            """,
            (run_id, asset_id),
        )
        conn.execute(
            """
            INSERT INTO recommendation_snapshot (
              run_id, asset_id, rank, target_weight, current_weight, deviation,
              action_label, trigger_reason, next_check_by, manual_review_required
            )
            VALUES (?, ?, ?, ?, 0.0, ?, ?, 'mail policy regression', 'next', 0)
            """,
            (run_id, asset_id, idx, weights[idx - 1], weights[idx - 1], action),
        )


def _last_notification_row(settings, run_id: str):
    with connect(settings.db_path) as conn:
        return conn.execute(
            """
            SELECT send_status, suppress_reason, notification_kind,
                   action_signature_hash, related_run_id, beijing_date
            FROM notification_log
            WHERE run_id=?
            ORDER BY rowid DESC
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()


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
    assert should_send_mail_for_run("Info", buy_rows, data_quality_status="manual_review") is True
    assert should_send_mail_for_run("Urgent", maintain_rows, data_quality_status="manual_review") is True


def test_notify_run_suppresses_duplicate_action_signature_after_first_sent(monkeypatch, tmp_path: Path):
    settings = replace(temp_settings(tmp_path), mail_send_enabled=True)
    init_db(settings.db_path)
    sent_subjects: list[str] = []

    def fake_send(subject, *args, **kwargs):
        sent_subjects.append(subject)
        return {"status": "sent", "error": ""}

    monkeypatch.setattr("app.core.notification.send_with_apple_mail", fake_send)
    with connect(settings.db_path) as conn:
        _insert_actionable_run(
            conn,
            run_id="sda_action_1",
            run_time_bj="2026-06-15T11:30:00+08:00",
            action_labels=["Increase", "Maintain", "Maintain", "Maintain", "Maintain"],
        )
        _insert_actionable_run(
            conn,
            run_id="sda_action_2",
            run_time_bj="2026-06-15T12:30:00+08:00",
            action_labels=["Increase", "Maintain", "Maintain", "Maintain", "Maintain"],
        )

    first = notify_run(settings, "sda_action_1", dry_run=False, send_mail=True)
    second = notify_run(settings, "sda_action_2", dry_run=False, send_mail=True)

    assert first["send_status"] == "sent"
    assert second["send_status"] == "suppressed"
    assert second["suppress_reason"] == "duplicate_action_signature"
    assert len(sent_subjects) == 1
    first_row = _last_notification_row(settings, "sda_action_1")
    second_row = _last_notification_row(settings, "sda_action_2")
    assert first_row["notification_kind"] == "actionable"
    assert second_row["notification_kind"] == "actionable"
    assert second_row["suppress_reason"] == "duplicate_action_signature"
    assert second_row["related_run_id"] == "sda_action_1"
    assert first_row["action_signature_hash"] == second_row["action_signature_hash"]


def test_notify_run_suppresses_cross_day_same_action_signature(monkeypatch, tmp_path: Path):
    settings = replace(temp_settings(tmp_path), mail_send_enabled=True)
    init_db(settings.db_path)
    sent_subjects: list[str] = []

    def fake_send(subject, *args, **kwargs):
        sent_subjects.append(subject)
        return {"status": "sent", "error": ""}

    monkeypatch.setattr("app.core.notification.send_with_apple_mail", fake_send)
    with connect(settings.db_path) as conn:
        _insert_actionable_run(
            conn,
            run_id="sda_yesterday",
            run_time_bj="2026-06-15T16:30:00+08:00",
            action_labels=["Reduce", "Maintain", "Maintain", "Maintain", "Maintain"],
            target_weights=[0.15, 0.20, 0.20, 0.20, 0.20],
        )
        _insert_actionable_run(
            conn,
            run_id="sda_today_same",
            run_time_bj="2026-06-16T08:30:00+08:00",
            action_labels=["Reduce", "Maintain", "Maintain", "Maintain", "Maintain"],
            target_weights=[0.15, 0.20, 0.20, 0.20, 0.20],
        )

    notify_run(settings, "sda_yesterday", dry_run=False, send_mail=True)
    today = notify_run(settings, "sda_today_same", dry_run=False, send_mail=True)

    assert today["send_status"] == "suppressed"
    assert today["suppress_reason"] == "duplicate_action_signature"
    assert len(sent_subjects) == 1
    today_row = _last_notification_row(settings, "sda_today_same")
    assert today_row["beijing_date"] == "2026-06-16"
    assert today_row["related_run_id"] == "sda_yesterday"


def test_notify_run_suppresses_third_different_actionable_mail_same_beijing_date(monkeypatch, tmp_path: Path):
    settings = replace(temp_settings(tmp_path), mail_send_enabled=True)
    init_db(settings.db_path)
    sent_subjects: list[str] = []

    def fake_send(subject, *args, **kwargs):
        sent_subjects.append(subject)
        return {"status": "sent", "error": ""}

    monkeypatch.setattr("app.core.notification.send_with_apple_mail", fake_send)
    with connect(settings.db_path) as conn:
        _insert_actionable_run(
            conn,
            run_id="sda_cap_1",
            run_time_bj="2026-06-15T08:30:00+08:00",
            action_labels=["Increase", "Maintain", "Maintain", "Maintain", "Maintain"],
            target_weights=[0.21, 0.20, 0.20, 0.20, 0.19],
        )
        _insert_actionable_run(
            conn,
            run_id="sda_cap_2",
            run_time_bj="2026-06-15T11:30:00+08:00",
            action_labels=["Reduce", "Maintain", "Maintain", "Maintain", "Maintain"],
            target_weights=[0.16, 0.21, 0.21, 0.21, 0.21],
        )
        _insert_actionable_run(
            conn,
            run_id="sda_cap_3",
            run_time_bj="2026-06-15T14:30:00+08:00",
            action_labels=["Pause New", "Maintain", "Maintain", "Maintain", "Maintain"],
            target_weights=[0.24, 0.19, 0.19, 0.19, 0.19],
        )

    first = notify_run(settings, "sda_cap_1", dry_run=False, send_mail=True)
    second = notify_run(settings, "sda_cap_2", dry_run=False, send_mail=True)
    third = notify_run(settings, "sda_cap_3", dry_run=False, send_mail=True)

    assert first["send_status"] == "sent"
    assert second["send_status"] == "sent"
    assert third["send_status"] == "suppressed"
    assert third["suppress_reason"] == "daily_email_cap_reached"
    assert len(sent_subjects) == 2
    third_row = _last_notification_row(settings, "sda_cap_3")
    assert third_row["suppress_reason"] == "daily_email_cap_reached"
    assert third_row["beijing_date"] == "2026-06-15"


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
    assert result["send_status"] == "suppressed"
    assert result["suppress_reason"] == "non_actionable"
    with connect(settings.db_path) as conn:
        row = conn.execute(
            """
            SELECT send_status, suppress_reason, notification_kind
            FROM notification_log
            WHERE run_id='sda_keep'
            ORDER BY rowid DESC LIMIT 1
            """
        ).fetchone()
    assert row["send_status"] == "suppressed"
    assert row["suppress_reason"] == "non_actionable"
    assert row["notification_kind"] == "info"


def test_notify_run_sends_first_manual_review_lock_when_actionable_changed(monkeypatch, tmp_path: Path):
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

    assert called["mail"] is True
    assert result["send_status"] == "sent"
    assert result["suppress_reason"] is None
    with connect(settings.db_path) as conn:
        row = conn.execute(
            """
            SELECT send_status, suppress_reason, notification_kind
            FROM notification_log
            WHERE run_id='sda_manual_lock'
            ORDER BY rowid DESC LIMIT 1
            """
        ).fetchone()
    assert row["send_status"] == "sent"
    assert row["suppress_reason"] is None
    assert row["notification_kind"] == "actionable"
