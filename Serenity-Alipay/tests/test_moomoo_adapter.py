from pathlib import Path

from app.adapters.moomoo_adapter import healthcheck
from app.core.moomoo_lifecycle import OpenDLifecycle
from tests.helpers import temp_settings


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_healthcheck_defers_cleanup_until_outer_task_finishes(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)

    lifecycle = OpenDLifecycle(
        socket_was_reachable=False,
        socket_is_reachable=True,
        auto_start_requested=True,
        start_attempted=True,
        started_by_tool=True,
        start_command="/tmp/start_opend.sh",
        cleanup_requested=True,
        cleanup_attempted=False,
        cleanup_result=None,
        before_processes=[],
        after_processes=[],
        started_processes=[],
        detail="fake moomoo_OpenD auto-started",
    )

    def fake_cleanup(*args, **kwargs):
        raise AssertionError("healthcheck must not cleanup immediately")

    monkeypatch.setattr("app.core.moomoo_lifecycle.ensure_opend", lambda *args, **kwargs: lifecycle)
    monkeypatch.setattr("app.core.moomoo_lifecycle.cleanup_started_processes", fake_cleanup)
    monkeypatch.setattr("socket.create_connection", lambda *args, **kwargs: _Connection())

    result = healthcheck(settings=settings, auto_start_opend=True, keep_auto_started_opend=False)

    assert result.available is True
    assert result.cleanup is None
    assert result.cleanup_required is True
    assert result.opend_lifecycle_handle is lifecycle
