from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.application_server import (
    ApplicationAutoScheduler,
    RefreshHolding,
    _select_manual_refresh_slot,
    clear_manual_review_decisions,
    fetch_manual_review_decisions,
    read_autoscheduler_status,
    refresh_application,
    save_manual_review_decision,
    serve_application,
    summarize_refresh_changes,
)
from app.db import connect, init_db
from tests.helpers import temp_settings


def test_summarize_refresh_changes_uses_compact_rebalance_language():
    before = {"ETAX": RefreshHolding(code="ETAX", name="Example Tax Fund", weight=0.18)}
    after = {"ETAX": RefreshHolding(code="ETAX", name="Example Tax Fund", weight=0.15)}

    assert summarize_refresh_changes(before, after) == "减仓ETAX 3%到15%"


def test_summarize_refresh_changes_keeps_current_holding_when_unchanged():
    before = {"007300": RefreshHolding(code="007300", name="国联安中证半导体ETF联接A", weight=0.2093)}
    after = {"007300": RefreshHolding(code="007300", name="国联安中证半导体ETF联接A", weight=0.2093)}

    assert summarize_refresh_changes(before, after) == "保持当前持仓"


def test_summarize_refresh_changes_ignores_sub_threshold_relative_changes():
    before = {
        "008887": RefreshHolding(code="008887", name="华夏国证半导体芯片ETF联接A", weight=0.2876),
        "013171": RefreshHolding(code="013171", name="华夏恒生互联网科技业ETF联接(QDII)A", weight=0.1276),
    }
    after = {
        "008887": RefreshHolding(code="008887", name="华夏国证半导体芯片ETF联接A", weight=0.2872),
        "270042": RefreshHolding(code="270042", name="广发纳指100ETF联接(QDII)人民币A", weight=0.1288),
    }

    assert summarize_refresh_changes(before, after) == "买入270042 到12.88%；卖出013171 到0%"


def test_manual_review_decision_persists_to_sqlite(monkeypatch, tmp_path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO manual_review_queue (
                id, run_id, asset_id, reason, action_blocked, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                65,
                "sda_test_r7",
                None,
                "fee/redemption/subscription status missing or closed",
                "No-New-Order",
                "open",
                "2026-06-13T00:00:00Z",
            ),
        )

    refresh_calls = []

    def fake_refresh(settings_arg):
        refresh_calls.append(settings_arg)
        return {
            "status": "pass",
            "message": "目前更新到最新时间 20260613 - 17:10 AEST 保持当前持仓",
            "run_id": f"sda_manual_refresh_{len(refresh_calls)}",
        }

    monkeypatch.setattr("app.core.application_server.refresh_application", fake_refresh)

    result = save_manual_review_decision(
        settings,
        {
            "review_id": 65,
            "outcome": "observe_pool",
            "note": "已核对支付宝费率页",
            "savedAt": "20260613 - 17:10 AEST",
        },
    )

    assert result["status"] == "pass"
    records = fetch_manual_review_decisions(settings)
    assert records["65"]["run_id"] == "sda_test_r7"
    assert records["65"]["decision"] == "放入观察池继续观察"
    assert records["65"]["outcome"] == "observe_pool"
    assert records["65"]["outcomeLabel"] == "放入观察池继续观察"
    assert records["65"]["refreshTriggered"] is True
    assert records["65"]["refreshRunId"] == "sda_manual_refresh_1"
    assert records["65"]["note"] == "已核对支付宝费率页"
    assert records["65"]["savedAt"] == "20260613 - 17:10 AEST"
    assert records["65"]["source"] == "sqlite"

    save_manual_review_decision(
        settings,
        {
            "review_id": 65,
            "outcome": "exclude_current_observation",
            "note": "已在平台确认暂不新增",
            "savedAt": "20260613 - 17:20 AEST",
        },
    )
    records = fetch_manual_review_decisions(settings)
    assert records["65"]["decision"] == "剔除这一轮观察池"
    assert records["65"]["outcome"] == "exclude_current_observation"
    assert records["65"]["refreshRunId"] == "sda_manual_refresh_2"
    assert records["65"]["note"] == "已在平台确认暂不新增"

    clear_result = clear_manual_review_decisions(settings)
    assert clear_result["deleted"] == 1
    assert fetch_manual_review_decisions(settings) == {}


def test_manual_review_promote_triggers_serenity_refresh(monkeypatch, tmp_path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO manual_review_queue (
                id, run_id, asset_id, reason, action_blocked, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                66,
                "sda_test_r8",
                None,
                "官方级来源少于 2 个，需要确认是否满足 Serenity 证据标准",
                "No-New-Order",
                "open",
                "2026-06-13T00:00:00Z",
            ),
        )

    called = {}

    def fake_refresh(settings_arg):
        called["settings"] = settings_arg
        return {
            "status": "pass",
            "message": "目前更新到最新时间 20260614 - 16:52 AEST 减仓ETAX 3%到15%",
            "run_id": "sda_manual_refresh_r8",
        }

    monkeypatch.setattr("app.core.application_server.refresh_application", fake_refresh)

    result = save_manual_review_decision(
        settings,
        {
            "review_id": 66,
            "outcome": "promote_top5_candidate_pool",
            "note": "已确认可进入候选操作池",
            "savedAt": "20260614 - 16:52 AEST",
        },
    )

    assert called["settings"] is settings
    record = result["record"]
    assert record["decision"] == "进入 Top 5 候选操作池"
    assert record["refreshTriggered"] is True
    assert record["refreshStatus"] == "pass"
    assert record["refreshRunId"] == "sda_manual_refresh_r8"
    assert "减仓ETAX" in record["refreshMessage"]

    records = fetch_manual_review_decisions(settings)
    assert records["66"]["refreshTriggered"] is True
    assert records["66"]["refreshRunId"] == "sda_manual_refresh_r8"


def test_refresh_application_runs_manual_serenity_flow(monkeypatch, tmp_path):
    settings = temp_settings(tmp_path)
    calls = {}
    holdings = [
        {"ETAX": RefreshHolding(code="ETAX", name="Example Tax Fund", weight=0.18)},
        {"ETAX": RefreshHolding(code="ETAX", name="Example Tax Fund", weight=0.15)},
    ]

    def fake_latest_holdings(settings_arg):
        calls.setdefault("latest", 0)
        index = min(calls["latest"], len(holdings) - 1)
        calls["latest"] += 1
        return holdings[index]

    def fake_run_slot(settings_arg, slot, dry_run=True, send_mail=False, run_date=None, run_datetime_bj=None):
        calls["run_slot"] = {
            "slot": slot,
            "dry_run": dry_run,
            "send_mail": send_mail,
            "run_date": run_date.isoformat() if run_date else None,
            "run_datetime_bj": run_datetime_bj.isoformat() if run_datetime_bj else None,
        }
        return {"run_id": "sda_manual_refresh_r10"}

    def fake_build_application_portal(settings_arg, *, install_apps=True):
        calls["portal"] = {"install_apps": install_apps}
        return {"portal_path": "/tmp/index.html"}

    monkeypatch.setattr("app.core.application_server._latest_holdings", fake_latest_holdings)
    monkeypatch.setattr(
        "app.core.application_server._select_manual_refresh_slot",
        lambda settings_arg: ("R10", datetime(2026, 6, 12, 18, 5, tzinfo=ZoneInfo("Asia/Shanghai"))),
    )
    monkeypatch.setattr("app.core.application_server.run_slot", fake_run_slot)
    monkeypatch.setattr("app.core.application_server.build_application_portal", fake_build_application_portal)

    result = refresh_application(settings)

    assert calls["run_slot"] == {
        "slot": "R10",
        "dry_run": False,
        "send_mail": False,
        "run_date": "2026-06-12",
        "run_datetime_bj": "2026-06-12T18:05:00+08:00",
    }
    assert calls["portal"] == {"install_apps": False}
    assert result["tick_action"] == "manual_serenity_run"
    assert result["run_id"] == "sda_manual_refresh_r10"
    assert result["action_summary"] == "减仓ETAX 3%到15%"


def test_manual_refresh_slot_uses_current_beijing_time_on_weekend(tmp_path):
    settings = temp_settings(tmp_path)
    slot, run_datetime = _select_manual_refresh_slot(
        settings,
        datetime(2026, 6, 14, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
    )

    assert slot == "R4"
    assert run_datetime.isoformat() == "2026-06-14T12:00:00+08:00"


def test_application_server_schedules_auto_shutdown(monkeypatch, tmp_path):
    settings = temp_settings(tmp_path)
    events = {}

    class FakeServer:
        def __init__(self, address, handler):
            events["address"] = address
            events["handler"] = handler
            events["shutdown_called"] = False

        def shutdown(self):
            events["shutdown_called"] = True

        def serve_forever(self):
            events["served"] = True

        def server_close(self):
            events["closed"] = True

    class FakeTimer:
        def __init__(self, interval, callback):
            events["timer_interval"] = interval
            events["timer_callback"] = callback
            self.daemon = False

        def start(self):
            events["timer_started"] = True

        def cancel(self):
            events["timer_cancelled"] = True

    monkeypatch.setattr("app.core.application_server.build_application_portal", lambda settings_arg, *, install_apps=True: {})
    monkeypatch.setattr("app.core.application_server.ThreadingHTTPServer", FakeServer)
    monkeypatch.setattr("app.core.application_server.threading.Timer", FakeTimer)

    serve_application(settings, host="127.0.0.1", port=8769, ttl_seconds=60, enable_autoscheduler=False)

    assert events["address"] == ("127.0.0.1", 8769)
    assert events["timer_interval"] == 60
    assert events["timer_started"] is True
    assert events["served"] is True
    assert events["timer_cancelled"] is True
    assert events["closed"] is True


def test_application_autoscheduler_run_once_writes_success_status(monkeypatch, tmp_path):
    settings = temp_settings(tmp_path)

    def fake_automation_tick(settings_arg, *, dry_run, send_mail, local):
        assert settings_arg is settings
        assert dry_run is False
        assert send_mail is True
        assert local is True
        return {
            "action": "no_due_slot",
            "due_slot": None,
            "scheduler": {"action": "no_due_slot", "due_slot": None, "run_id": None},
        }

    monkeypatch.setattr("app.core.application_server.automation_tick", fake_automation_tick)
    scheduler = ApplicationAutoScheduler(settings, interval_seconds=5, initial_delay_seconds=0)

    status = scheduler.run_once()

    assert status["status"] == "success"
    assert status["scheduler_kind"] == "application_server_interval"
    assert status["last_tick_action"] == "no_due_slot"
    assert status["last_exit_code"] == 0
    assert read_autoscheduler_status(settings)["last_tick_action"] == "no_due_slot"


def test_application_server_starts_autoscheduler(monkeypatch, tmp_path):
    settings = temp_settings(tmp_path)
    events = {}

    class FakeServer:
        def __init__(self, address, handler):
            events["address"] = address

        def serve_forever(self):
            events["served"] = True

        def server_close(self):
            events["closed"] = True

    class FakeAutoScheduler:
        def __init__(self, settings_arg, *, interval_seconds, initial_delay_seconds):
            events["autoscheduler_settings"] = settings_arg
            events["autoscheduler_interval"] = interval_seconds
            events["autoscheduler_initial_delay"] = initial_delay_seconds

        def start(self):
            events["autoscheduler_started"] = True

        def stop(self):
            events["autoscheduler_stopped"] = True

    monkeypatch.setattr("app.core.application_server.build_application_portal", lambda settings_arg, *, install_apps=True: {})
    monkeypatch.setattr("app.core.application_server.ThreadingHTTPServer", FakeServer)
    monkeypatch.setattr("app.core.application_server.ApplicationAutoScheduler", FakeAutoScheduler)

    serve_application(
        settings,
        host="127.0.0.1",
        port=8769,
        ttl_seconds=0,
        enable_autoscheduler=True,
        autoscheduler_interval_seconds=45,
        autoscheduler_initial_delay_seconds=1,
    )

    assert events["address"] == ("127.0.0.1", 8769)
    assert events["autoscheduler_settings"] is settings
    assert events["autoscheduler_interval"] == 45
    assert events["autoscheduler_initial_delay"] == 1
    assert events["autoscheduler_started"] is True
    assert events["served"] is True
    assert events["autoscheduler_stopped"] is True
    assert events["closed"] is True
