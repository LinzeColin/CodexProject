from app.core.moomoo_lifecycle import OpenDLifecycle, ProcessInfo, _wait_for_socket, cleanup_started_processes


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
