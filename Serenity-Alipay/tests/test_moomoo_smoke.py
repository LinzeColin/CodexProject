from pathlib import Path

from app.config import Settings
from app.core.moomoo_lifecycle import OpenDLifecycle, ProcessInfo, ensure_opend
from app.core.moomoo_smoke import SdkProbe, SocketProbe, discover_workbenches, run_moomoo_smoke
from tests.helpers import temp_settings


def test_moomoo_smoke_writes_diagnostics(tmp_path: Path):
    settings = temp_settings(tmp_path)
    result = run_moomoo_smoke(
        settings,
        port=1,
        timeout=0.05,
        include_user_codex=False,
    )

    assert result["status"] == "block"
    assert result["production_ready_for_moomoo_data"] is False
    assert result["socket"]["reachable"] is False
    assert "recommended_actions" in result
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()


def test_moomoo_smoke_auto_start_records_lifecycle(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)

    def fake_ensure(*args, **kwargs):
        return OpenDLifecycle(
            socket_was_reachable=False,
            socket_is_reachable=True,
            auto_start_requested=True,
            start_attempted=True,
            started_by_tool=True,
            start_command="/tmp/start_opend.sh",
            cleanup_requested=False,
            cleanup_attempted=False,
            cleanup_result=None,
            before_processes=[],
            after_processes=[],
            started_processes=[],
            detail="fake moomoo_OpenD auto-started",
        )

    monkeypatch.setattr("app.core.moomoo_lifecycle.ensure_opend", fake_ensure)
    monkeypatch.setattr(
        "app.core.moomoo_smoke.probe_socket",
        lambda host, port, timeout: SocketProbe(host, port, True, f"moomoo_OpenD socket reachable at {host}:{port}"),
    )
    monkeypatch.setattr(
        "app.core.moomoo_smoke.probe_sdk",
        lambda: SdkProbe(True, "test", "Python import `moomoo` is available; installed distribution version=test"),
    )

    result = run_moomoo_smoke(settings, write_output=False, auto_start_opend=True)

    assert result["status"] == "pass"
    assert result["production_ready_for_moomoo_data"] is True
    assert result["opend_lifecycle"]["start_attempted"] is True
    assert result["opend_lifecycle"]["started_by_tool"] is True
    assert result["cleanup"]["cleanup_attempted"] is True
    assert result["cleanup"]["cleanup_result"] == "no_started_processes_to_cleanup"


def test_discover_workbenches_prefers_user_applications_moomoo_opend_gui(monkeypatch, tmp_path: Path):
    fake_home = tmp_path / "home"
    gui_app = fake_home / "Applications" / "MoomooOpenD" / "moomoo_OpenD.app"
    gui_app.mkdir(parents=True)
    cli_app = (
        fake_home
        / "Applications"
        / "MoomooOpenD"
        / "moomoo_OpenD_10.6.6608_Mac"
        / "moomoo_OpenD_10.6.6608_Mac"
        / "OpenD.app"
    )
    cli_app.mkdir(parents=True)
    settings = Settings.load(tmp_path / "workspace")

    monkeypatch.setattr(Path, "home", lambda: fake_home)

    probes = discover_workbenches(settings, include_user_codex=False)

    assert probes[0].moomoo_opend_app_path == str(gui_app)


def test_discover_workbenches_finds_system_applications_moomoo_opend(monkeypatch, tmp_path: Path):
    fake_applications = tmp_path / "Applications"
    opend_app = fake_applications / "moomoo_OpenD.app"
    opend_app.mkdir(parents=True)
    fake_home = tmp_path / "home"
    settings = Settings.load(tmp_path / "workspace")

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setattr("app.core.moomoo_smoke.SYSTEM_APPLICATION_DIRS", [fake_applications])

    probes = discover_workbenches(settings, include_user_codex=False)

    assert probes[0].moomoo_opend_app_path == str(opend_app)


def test_moomoo_smoke_reports_latest_login_failure_hint(monkeypatch, tmp_path: Path):
    fake_home = tmp_path / "home"
    log_dir = fake_home / ".com.moomoo.OpenD" / "Log"
    log_dir.mkdir(parents=True)
    (log_dir / "GTWLog_0_2026_06_24_10_07_08.log").write_text(
        "API Listening Address: 127.0.0.1:11111\nLogin failed,Password does not match\n",
        encoding="utf-8",
    )
    settings = temp_settings(tmp_path)

    monkeypatch.setattr(Path, "home", lambda: fake_home)

    result = run_moomoo_smoke(settings, port=1, timeout=0.05, include_user_codex=False, write_output=False)

    assert result["latest_failure_hint"] == (
        "moomoo_OpenD login failed: password does not match; update OpenD credentials or complete GUI login"
    )
    assert result["latest_failure_hint"] in result["recommended_actions"]


def test_ensure_opend_prefers_real_app_over_legacy_script(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    old_workbench = settings.root_dir / "outputs" / "moomoo-api-workbench"
    old_workbench.mkdir(parents=True)
    (old_workbench / "start_opend.sh").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    fake_home = tmp_path / "home"
    opend_app = fake_home / "Applications" / "MoomooOpenD" / "moomoo_OpenD.app"
    opend_app.mkdir(parents=True)
    commands: list[list[str]] = []
    snapshots = iter(
        [
            [],
            [ProcessInfo(pid="123", command=f"{opend_app}/Contents/MacOS/moomoo_OpenD")],
        ]
    )

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setattr("app.core.moomoo_lifecycle.process_snapshot", lambda: next(snapshots))
    monkeypatch.setattr(
        "app.core.moomoo_lifecycle.probe_socket",
        lambda host, port, timeout: SocketProbe(host, port, False, "closed"),
    )
    monkeypatch.setattr("app.core.moomoo_lifecycle._wait_for_socket", lambda *args, **kwargs: True)

    def fake_run(command, **kwargs):
        commands.append(command)

        class Result:
            stdout = ""
            stderr = ""
            returncode = 0

        return Result()

    monkeypatch.setattr("app.core.moomoo_lifecycle.subprocess.run", fake_run)

    lifecycle = ensure_opend(settings, auto_start=True)

    assert lifecycle.start_command == str(opend_app)
    assert commands[0] == ["open", str(opend_app)]
    assert lifecycle.started_by_tool is True


def test_ensure_opend_marks_new_failed_start_for_cleanup(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    fake_home = tmp_path / "home"
    opend_app = fake_home / "Applications" / "MoomooOpenD" / "moomoo_OpenD.app"
    opend_app.mkdir(parents=True)
    started_process = ProcessInfo(pid="456", command=f"{opend_app}/Contents/MacOS/moomoo_OpenD")
    snapshots = iter([[], [started_process]])

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setattr("app.core.moomoo_lifecycle.process_snapshot", lambda: next(snapshots))
    monkeypatch.setattr(
        "app.core.moomoo_lifecycle.probe_socket",
        lambda host, port, timeout: SocketProbe(host, port, False, "closed"),
    )
    monkeypatch.setattr("app.core.moomoo_lifecycle._wait_for_socket", lambda *args, **kwargs: False)
    monkeypatch.setattr("app.core.moomoo_lifecycle.subprocess.run", lambda *args, **kwargs: None)

    lifecycle = ensure_opend(settings, auto_start=True)

    assert lifecycle.start_attempted is True
    assert lifecycle.socket_is_reachable is False
    assert lifecycle.started_by_tool is True
    assert lifecycle.started_processes
