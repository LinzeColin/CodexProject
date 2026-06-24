from app.core.moomoo_lifecycle import OpenDLifecycle, ProcessInfo, _wait_for_socket, cleanup_started_processes, ensure_opend
from app.core.moomoo_smoke import SocketProbe
from tests.helpers import temp_settings


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_cleanup_does_not_touch_user_owned_opend(monkeypatch):
    monkeypatch.setattr(
        "app.core.moomoo_lifecycle.process_snapshot",
        lambda: [ProcessInfo(pid="100", command="/Applications/OpenD.app/Contents/MacOS/OpenD")],
    )

    lifecycle = OpenDLifecycle(
        socket_was_reachable=True,
        socket_is_reachable=True,
        auto_start_requested=True,
        start_attempted=False,
        started_by_tool=False,
        start_command=None,
        cleanup_requested=True,
        cleanup_attempted=False,
        cleanup_result=None,
        before_processes=[ProcessInfo(pid="100", command="/Applications/OpenD.app/Contents/MacOS/OpenD")],
        after_processes=[ProcessInfo(pid="100", command="/Applications/OpenD.app/Contents/MacOS/OpenD")],
        started_processes=[],
        detail="moomoo_OpenD socket reachable before this run",
    )

    result = cleanup_started_processes(lifecycle)

    assert result["cleanup_attempted"] is False
    assert result["cleanup_result"] == "not_started_by_tool"


def test_cleanup_defers_auto_started_opend_until_socket_ready(monkeypatch):
    started_process = ProcessInfo(pid="200", command="/Applications/MoomooOpenD/moomoo_OpenD.app/Contents/MacOS/moomoo_OpenD")
    monkeypatch.setattr("app.core.moomoo_lifecycle.process_snapshot", lambda: [started_process])

    lifecycle = OpenDLifecycle(
        socket_was_reachable=False,
        socket_is_reachable=False,
        auto_start_requested=True,
        start_attempted=True,
        started_by_tool=True,
        start_command="/Applications/MoomooOpenD/moomoo_OpenD.app",
        cleanup_requested=True,
        cleanup_attempted=False,
        cleanup_result=None,
        before_processes=[],
        after_processes=[started_process],
        started_processes=[started_process],
        detail="moomoo_OpenD start attempted, but socket did not become reachable",
    )

    result = cleanup_started_processes(lifecycle)

    assert result["cleanup_attempted"] is False
    assert result["cleanup_result"] == "deferred_socket_not_ready"


def test_ensure_opend_suppresses_duplicate_start_when_existing_process_is_launching(monkeypatch, tmp_path):
    settings = temp_settings(tmp_path)
    existing_process = ProcessInfo(pid="300", command="/Applications/MoomooOpenD/moomoo_OpenD.app/Contents/MacOS/moomoo_OpenD")
    commands: list[list[str]] = []

    monkeypatch.setattr("app.core.moomoo_lifecycle.process_snapshot", lambda: [existing_process])
    monkeypatch.setattr(
        "app.core.moomoo_lifecycle.probe_socket",
        lambda host, port, timeout: SocketProbe(host, port, False, "closed"),
    )
    monkeypatch.setattr("app.core.moomoo_lifecycle._wait_for_socket", lambda *args, **kwargs: False)
    monkeypatch.setattr("app.core.moomoo_lifecycle.subprocess.run", lambda command, **kwargs: commands.append(command))

    lifecycle = ensure_opend(settings, auto_start=True)

    assert lifecycle.start_attempted is False
    assert lifecycle.started_by_tool is False
    assert lifecycle.socket_is_reachable is False
    assert "duplicate auto-start was suppressed" in lifecycle.detail
    assert commands == []


def test_wait_for_socket_requires_consecutive_stable_connections(monkeypatch):
    state = {"attempts": 0, "time": 0.0}

    def fake_monotonic():
        state["time"] += 0.4
        return state["time"]

    def fake_create_connection(*args, **kwargs):
        state["attempts"] += 1
        if state["attempts"] == 1:
            return _Connection()
        raise OSError("transient listener exited")

    monkeypatch.setattr("app.core.moomoo_lifecycle.time.monotonic", fake_monotonic)
    monkeypatch.setattr("app.core.moomoo_lifecycle.time.sleep", lambda _: None)
    monkeypatch.setattr("app.core.moomoo_lifecycle.socket.create_connection", fake_create_connection)

    assert _wait_for_socket("127.0.0.1", 11111, 0.1, 1.0) is False


def test_wait_for_socket_accepts_stable_connections(monkeypatch):
    state = {"time": 0.0}

    def fake_monotonic():
        state["time"] += 0.2
        return state["time"]

    monkeypatch.setattr("app.core.moomoo_lifecycle.time.monotonic", fake_monotonic)
    monkeypatch.setattr("app.core.moomoo_lifecycle.time.sleep", lambda _: None)
    monkeypatch.setattr("app.core.moomoo_lifecycle.socket.create_connection", lambda *args, **kwargs: _Connection())

    assert _wait_for_socket("127.0.0.1", 11111, 0.1, 1.0) is True
