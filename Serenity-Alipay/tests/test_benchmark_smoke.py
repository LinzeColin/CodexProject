import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

from app.core.benchmark_smoke import BenchmarkSourceCandidate, _probe_moomoo_candidates, default_benchmark_window, run_benchmark_smoke
from app.core.moomoo_lifecycle import OpenDLifecycle
from tests.helpers import copy_sample_data, temp_settings


class _FakeFrame:
    def __init__(self, rows):
        self._rows = rows

    def __len__(self):
        return len(self._rows)

    def to_dict(self, orient):
        assert orient == "records"
        return self._rows


def _fake_moomoo_module(rows):
    class FakeQuoteContext:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def request_history_kline(self, *args, **kwargs):
            return 0, _FakeFrame(rows), None

        def close(self):
            return None

    return SimpleNamespace(
        RET_OK=0,
        KLType=SimpleNamespace(K_DAY="K_DAY"),
        OpenQuoteContext=FakeQuoteContext,
    )


def test_benchmark_smoke_blocks_without_exact_sources(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    def fake_ensure(*args, **kwargs):
        return OpenDLifecycle(
            socket_was_reachable=False,
            socket_is_reachable=False,
            auto_start_requested=True,
            start_attempted=False,
            started_by_tool=False,
            start_command=None,
            cleanup_requested=True,
            cleanup_attempted=False,
            cleanup_result=None,
            before_processes=[],
            after_processes=[],
            started_processes=[],
            detail="fake socket closed",
        )

    monkeypatch.setattr("app.core.benchmark_smoke.ensure_opend", fake_ensure)
    monkeypatch.setattr("app.core.benchmark_smoke._probe_yahoo_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr("app.core.benchmark_smoke._probe_eastmoney_candidates", lambda *args, **kwargs: [])
    result = run_benchmark_smoke(settings, write_output=True)

    assert result["production_ready"] is False
    assert result["status"] == "blocked"
    assert result["window"]["source"] == "dynamic_latest_weekday"
    assert result["production_ready_by_benchmark"]["Shanghai Composite"] is False
    assert result["production_ready_by_benchmark"]["S&P 500"] is False
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()


def test_default_benchmark_window_uses_same_weekday(tmp_path: Path):
    settings = temp_settings(tmp_path)

    start, end = default_benchmark_window(settings, today=date(2026, 6, 12))

    assert end == "2026-06-12"
    assert start == "2025-05-12"


def test_default_benchmark_window_rolls_weekend_back_to_friday(tmp_path: Path):
    settings = temp_settings(tmp_path)

    start, end = default_benchmark_window(settings, today=date(2026, 6, 13))

    assert end == "2026-06-12"
    assert start == "2025-05-12"


def test_moomoo_exact_index_requires_full_benchmark_window(monkeypatch):
    candidate = BenchmarkSourceCandidate(
        "Shanghai Composite",
        "000001.SH",
        "SH.000001",
        "moomoo",
        "exact_index",
        "test",
    )
    short_rows = [
        {"time_key": f"2026-06-{day:02d} 00:00:00", "close": 4000 + day}
        for day in range(1, 6)
    ]
    monkeypatch.setitem(sys.modules, "moomoo", _fake_moomoo_module(short_rows))

    rows = _probe_moomoo_candidates((candidate,), start="2025-05-12", end="2026-06-12", host="127.0.0.1", port=11111)

    assert rows[0]["status"] == "pass"
    assert rows[0]["rows"] == 5
    assert rows[0]["sufficient_for_required_windows"] is False
    assert rows[0]["production_eligible"] is False


def test_moomoo_exact_index_is_eligible_only_when_window_is_sufficient(monkeypatch):
    candidate = BenchmarkSourceCandidate(
        "Shanghai Composite",
        "000001.SH",
        "SH.000001",
        "moomoo",
        "exact_index",
        "test",
    )
    start_day = date(2025, 5, 12)
    rows = [
        {"time_key": (start_day + timedelta(days=offset)).isoformat() + " 00:00:00", "close": 4000 + offset}
        for offset in range(0, 397, 2)
    ]
    monkeypatch.setitem(sys.modules, "moomoo", _fake_moomoo_module(rows))

    result = _probe_moomoo_candidates((candidate,), start="2025-05-12", end="2026-06-12", host="127.0.0.1", port=11111)

    assert result[0]["rows"] == 199
    assert result[0]["sufficient_for_required_windows"] is True
    assert result[0]["production_eligible"] is True
    assert result[0]["history"][0]["source_type"] == "moomoo"
    assert result[0]["history"][0]["source_priority"] == 1
