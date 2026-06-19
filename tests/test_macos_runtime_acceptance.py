from __future__ import annotations

from pathlib import Path

import quantlab.system.macos_runtime_acceptance as runtime


def test_runtime_acceptance_runs_controlled_start_stop_flow(monkeypatch, tmp_path: Path) -> None:
    state = {"running": False, "started": False, "stopped": False}
    timeouts: dict[tuple[str, str], int] = {}

    def fake_start_process(_root: Path):
        state["running"] = True
        state["started"] = True
        return _FakeProcess(state)

    def fake_healthy_ports():
        return [8501] if state["running"] else []

    def fake_run_script(_root: Path, args: list[str], *, timeout_seconds: int):
        command = args[0]
        key = (command, "dry-run" if "--dry-run" in args else "default")
        timeouts[key] = max(timeouts.get(key, 0), timeout_seconds)
        if command == "scripts/statusQuantLab.sh":
            return {
                "returncode": 0,
                "stdout": "QuantLab running: http://localhost:8501" if state["running"] else "QuantLab is not running on ports 8501-8510.",
                "stderr": "",
            }
        if command == "scripts/cleanCache.sh" and "--dry-run" not in args:
            return {
                "returncode": 2 if state["running"] else 0,
                "stdout": "QuantLab appears to be running. Stop it before cleaning cache." if state["running"] else "{}",
                "stderr": "",
            }
        if command == "scripts/cleanCache.sh" and "--dry-run" in args:
            return {
                "returncode": 0,
                "stdout": '{"schema":"EVACacheCleanupReportV1","candidate_count":2,"candidate_file_count":3,"candidate_kb":4.5}',
                "stderr": "",
            }
        if command == "scripts/stopQuantLab.sh":
            state["running"] = False
            state["stopped"] = True
            return {"returncode": 0, "stdout": "QuantLab stop command completed.", "stderr": ""}
        raise AssertionError(args)

    monkeypatch.setattr(runtime, "_start_process", fake_start_process)
    monkeypatch.setattr(runtime, "_healthy_ports", fake_healthy_ports)
    monkeypatch.setattr(runtime, "_run_script", fake_run_script)
    monkeypatch.setattr(runtime, "_app_acceptance_summary", lambda _root: {"schema": "EVAOSMacOSAppAcceptanceLiteV1", "status": "Pass", "summary": {"fail": 0}})

    payload = runtime.run_macos_runtime_acceptance(project_root=tmp_path, start_timeout_seconds=1, stop_timeout_seconds=1)

    assert payload["schema"] == "EVAOSMacOSRuntimeAcceptanceV1"
    assert payload["status"] == "Pass"
    assert payload["started_by_acceptance"] is True
    assert payload["summary"]["fail"] == 0
    assert state["started"] is True
    assert state["stopped"] is True
    assert any(row["check"] == "CleanCacheRefusesWhileRunning" and row["status"] == "Pass" for row in payload["checks"])
    assert any(row["check"] == "HealthAfterStop" and row["status"] == "Pass" for row in payload["checks"])
    assert timeouts[("scripts/statusQuantLab.sh", "default")] >= runtime.SUPPORT_SCRIPT_TIMEOUT_FLOOR_SECONDS
    assert timeouts[("scripts/cleanCache.sh", "default")] >= runtime.SUPPORT_SCRIPT_TIMEOUT_FLOOR_SECONDS
    assert timeouts[("scripts/cleanCache.sh", "dry-run")] >= runtime.CACHE_DRY_RUN_TIMEOUT_FLOOR_SECONDS
    assert "finalAcceptanceCheck.sh" in payload["heavy_smoke_policy"]


def test_runtime_acceptance_blocks_preexisting_service_by_default(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runtime, "_healthy_ports", lambda: [8501])
    monkeypatch.setattr(runtime, "_app_acceptance_summary", lambda _root: {"schema": "EVAOSMacOSAppAcceptanceLiteV1", "status": "Pass", "summary": {"fail": 0}})

    payload = runtime.run_macos_runtime_acceptance(project_root=tmp_path)

    assert payload["status"] == "Blocked"
    assert payload["started_by_acceptance"] is False
    assert payload["pre_existing_healthy_ports"] == [8501]
    assert any(row["check"] == "NoPreExistingService" and row["status"] == "Fail" for row in payload["checks"])


def test_runtime_acceptance_supports_app_open_launch_method(monkeypatch, tmp_path: Path) -> None:
    state = {"running": False, "launched": False}

    def fake_launch_app(_root: Path, _app_path: Path | str | None):
        state["running"] = True
        state["launched"] = True
        return {"returncode": 0, "stdout": "opened=/tmp/EVA_OS.app", "stderr": ""}

    def fake_healthy_ports():
        return [8501] if state["running"] else []

    def fake_run_script(_root: Path, args: list[str], *, timeout_seconds: int):
        command = args[0]
        if command == "scripts/statusQuantLab.sh":
            stdout = "QuantLab running: http://localhost:8501" if state["running"] else "QuantLab is not running on ports 8501-8510."
            return {"returncode": 0, "stdout": stdout, "stderr": ""}
        if command == "scripts/cleanCache.sh" and "--dry-run" not in args:
            return {"returncode": 2, "stdout": "QuantLab appears to be running. Stop it before cleaning cache.", "stderr": ""}
        if command == "scripts/cleanCache.sh" and "--dry-run" in args:
            return {"returncode": 0, "stdout": '{"schema":"EVACacheCleanupReportV1","candidate_count":0}', "stderr": ""}
        if command == "scripts/stopQuantLab.sh":
            state["running"] = False
            return {"returncode": 0, "stdout": "QuantLab stop command completed.", "stderr": ""}
        raise AssertionError(args)

    monkeypatch.setattr(runtime, "_launch_app", fake_launch_app)
    monkeypatch.setattr(runtime, "_healthy_ports", fake_healthy_ports)
    monkeypatch.setattr(runtime, "_run_script", fake_run_script)
    monkeypatch.setattr(runtime, "_app_acceptance_summary", lambda _root: {"schema": "EVAOSMacOSAppAcceptanceLiteV1", "status": "Pass", "summary": {"fail": 0}})

    payload = runtime.run_macos_runtime_acceptance(
        project_root=tmp_path,
        launch_method="app",
        app_path=tmp_path / "EVA_OS.app",
    )

    assert payload["status"] == "Pass"
    assert payload["launch_method"] == "app"
    assert state["launched"] is True
    assert any(row["check"] == "AppOpenLaunched" and row["status"] == "Pass" for row in payload["checks"])


def test_app_acceptance_summary_retries_transient_failure(monkeypatch, tmp_path: Path) -> None:
    attempts = {"count": 0, "timeouts": []}

    def fake_app_lite(**kwargs):
        attempts["count"] += 1
        attempts["timeouts"].append(kwargs["dry_run_timeout_seconds"])
        if attempts["count"] == 1:
            return {
                "schema": "EVAOSMacOSAppAcceptanceLiteV1",
                "status": "Blocked",
                "summary": {"pass": 28, "fail": 1, "info": 2, "total": 31},
                "checks": [{"target": "Applications", "check": "LauncherDryRun", "status": "Fail", "evidence": "timeout"}],
                "heavy_smoke_policy": "no heavy smoke",
            }
        return {
            "schema": "EVAOSMacOSAppAcceptanceLiteV1",
            "status": "Pass",
            "summary": {"pass": 29, "fail": 0, "info": 2, "total": 31},
            "checks": [],
            "heavy_smoke_policy": "no heavy smoke",
        }

    monkeypatch.setattr(runtime, "build_macos_app_acceptance_lite", fake_app_lite)
    monkeypatch.setattr(runtime.time, "sleep", lambda _seconds: None)

    summary = runtime._app_acceptance_summary(tmp_path)

    assert summary["status"] == "Pass"
    assert summary["attempts"] == 2
    assert summary["failed_checks"] == []
    assert attempts["timeouts"] == [runtime.APP_ACCEPTANCE_DRY_RUN_TIMEOUT_SECONDS, runtime.APP_ACCEPTANCE_DRY_RUN_TIMEOUT_SECONDS]


def test_write_runtime_acceptance_outputs_json_and_latest(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        runtime,
        "run_macos_runtime_acceptance",
        lambda **_kwargs: {
            "schema": "EVAOSMacOSRuntimeAcceptanceV1",
            "status": "Pass",
            "summary": {"pass": 1, "fail": 0, "info": 0, "total": 1},
        },
    )

    payload = runtime.write_macos_runtime_acceptance(project_root=tmp_path, output_dir=tmp_path / "acceptance")

    assert Path(payload["outputs"]["json"]).exists()
    assert Path(payload["outputs"]["latest_json"]).exists()
    assert Path(payload["outputs"]["latest_json"]).name == "MacOSRuntimeAcceptance_latest.json"


def test_run_script_returns_structured_timeout(monkeypatch, tmp_path: Path) -> None:
    def raise_timeout(*_args, **_kwargs):
        raise runtime.subprocess.TimeoutExpired(cmd=["script"], timeout=3, output="", stderr="")

    monkeypatch.setattr(runtime.subprocess, "run", raise_timeout)

    result = runtime._run_script(tmp_path, ["scripts/cleanCache.sh"], timeout_seconds=3)

    assert result["returncode"] == 124
    assert "timeout after 3 seconds" in result["stderr"]


class _FakeProcess:
    def __init__(self, state: dict[str, bool]) -> None:
        self._state = state

    def poll(self):
        return None if self._state["running"] else 0

    def terminate(self) -> None:
        self._state["running"] = False

    def wait(self, timeout=None):
        return 0

    def kill(self) -> None:
        self._state["running"] = False

    def communicate(self, timeout=None):
        return "", ""
