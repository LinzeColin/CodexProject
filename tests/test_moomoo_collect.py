from datetime import date
from pathlib import Path

from app.core.moomoo_collect import _json_safe, collect_moomoo_data, safe_symbol
from app.core.moomoo_lifecycle import OpenDLifecycle
from app.db import connect
from tests.helpers import temp_settings


def test_safe_symbol_for_file_names():
    assert safe_symbol("US.AAPL") == "US_AAPL"
    assert safe_symbol("HK.00700") == "HK_00700"
    assert safe_symbol("CN/TEST:1") == "CN_TEST_1"


def test_json_safe_handles_dates_and_numpy_like_values():
    class Value:
        def item(self):
            return 3.5

    assert _json_safe(date(2026, 6, 12)) == "2026-06-12"
    assert _json_safe(Value()) == 3.5


def test_collect_moomoo_records_failed_run_when_opend_unreachable(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)

    def fake_ensure(*args, **kwargs):
        return OpenDLifecycle(
            socket_was_reachable=False,
            socket_is_reachable=False,
            auto_start_requested=True,
            start_attempted=True,
            started_by_tool=False,
            start_command="/tmp/start_opend.sh",
            cleanup_requested=True,
            cleanup_attempted=False,
            cleanup_result=None,
            before_processes=[],
            after_processes=[],
            started_processes=[],
            detail="fake OpenD unavailable",
        )

    monkeypatch.setattr("app.core.moomoo_collect.ensure_opend", fake_ensure)

    result = collect_moomoo_data(
        settings,
        ["US.AAPL"],
        start="2026-06-01",
        end="2026-06-12",
        opend_wait_seconds=0.01,
    )

    assert result["status"] == "failed"
    assert result["errors"][0]["scope"] == "opend"
    with connect(settings.db_path) as conn:
        row = conn.execute("SELECT status FROM run_log WHERE run_id=?", (result["run_id"],)).fetchone()
    assert row["status"] == "failed"
