from __future__ import annotations

import socket
import subprocess
import time
from dataclasses import asdict, dataclass

from app.config import Settings
from app.core.moomoo_smoke import WorkbenchProbe, discover_workbenches, probe_socket


PROCESS_PATTERN = "OpenD|moomoo_OpenD|Moomoo|moomoo_Op"


@dataclass(frozen=True)
class ProcessInfo:
    pid: str
    command: str


@dataclass(frozen=True)
class OpenDLifecycle:
    socket_was_reachable: bool
    socket_is_reachable: bool
    auto_start_requested: bool
    start_attempted: bool
    started_by_tool: bool
    start_command: str | None
    cleanup_requested: bool
    cleanup_attempted: bool
    cleanup_result: str | None
    before_processes: list[ProcessInfo]
    after_processes: list[ProcessInfo]
    started_processes: list[ProcessInfo]
    detail: str


def process_snapshot() -> list[ProcessInfo]:
    try:
        result = subprocess.run(
            ["pgrep", "-af", PROCESS_PATTERN],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    pids: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.strip().split(maxsplit=1)
        if parts and parts[0].isdigit():
            pids.append(parts[0])
    if not pids:
        return []
    ps = subprocess.run(
        ["ps", "-p", ",".join(pids), "-o", "pid=", "-o", "args="],
        capture_output=True,
        text=True,
        check=False,
    )
    processes: list[ProcessInfo] = []
    for line in ps.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        command = parts[1] if len(parts) > 1 else ""
        if "pgrep -af" in command:
            continue
        processes.append(ProcessInfo(pid=parts[0], command=command))
    return processes


def _wait_for_socket(host: str, port: int, timeout: float, wait_seconds: float) -> bool:
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() <= deadline:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def _primary_workbench(workbenches: list[WorkbenchProbe]) -> WorkbenchProbe | None:
    for workbench in workbenches:
        if workbench.start_script:
            return workbench
    return None


def _new_processes(before: list[ProcessInfo], after: list[ProcessInfo]) -> list[ProcessInfo]:
    before_pids = {process.pid for process in before}
    return [process for process in after if process.pid not in before_pids]


def _cleanup_processes(processes: list[ProcessInfo]) -> str:
    targets = [
        process
        for process in processes
        if any(marker in process.command for marker in ["moomoo_OpenD", "OpenD.app", "CrashReporter"])
    ]
    if not targets:
        return "no_started_processes_to_cleanup"
    for process in targets:
        subprocess.run(["kill", "-TERM", process.pid], capture_output=True, text=True, check=False)
    return "terminated_started_processes:" + ",".join(process.pid for process in targets)


def cleanup_started_processes(lifecycle: OpenDLifecycle) -> dict[str, object]:
    if not lifecycle.started_by_tool:
        return {
            "cleanup_attempted": False,
            "cleanup_result": "not_started_by_tool",
            "after_processes": [asdict(process) for process in process_snapshot()],
        }
    result = _cleanup_processes(lifecycle.started_processes)
    return {
        "cleanup_attempted": True,
        "cleanup_result": result,
        "after_processes": [asdict(process) for process in process_snapshot()],
    }


def ensure_opend(
    settings: Settings,
    *,
    host: str = "127.0.0.1",
    port: int = 11111,
    timeout: float = 0.5,
    auto_start: bool = False,
    cleanup_if_started: bool = False,
    wait_seconds: float = 20.0,
    include_user_codex: bool = True,
) -> OpenDLifecycle:
    before = process_snapshot()
    before_probe = probe_socket(host, port, timeout)
    if before_probe.reachable or not auto_start:
        detail = before_probe.detail if before_probe.reachable else "OpenD was not started because auto_start is disabled"
        return OpenDLifecycle(
            socket_was_reachable=before_probe.reachable,
            socket_is_reachable=before_probe.reachable,
            auto_start_requested=auto_start,
            start_attempted=False,
            started_by_tool=False,
            start_command=None,
            cleanup_requested=cleanup_if_started,
            cleanup_attempted=False,
            cleanup_result=None,
            before_processes=before,
            after_processes=before,
            started_processes=[],
            detail=detail,
        )

    workbench = _primary_workbench(discover_workbenches(settings, include_user_codex=include_user_codex))
    if not workbench or not workbench.start_script:
        return OpenDLifecycle(
            socket_was_reachable=False,
            socket_is_reachable=False,
            auto_start_requested=True,
            start_attempted=False,
            started_by_tool=False,
            start_command=None,
            cleanup_requested=cleanup_if_started,
            cleanup_attempted=False,
            cleanup_result=None,
            before_processes=before,
            after_processes=before,
            started_processes=[],
            detail="No OpenD start script found",
        )

    subprocess.run(["bash", workbench.start_script], capture_output=True, text=True, check=False)
    reachable = _wait_for_socket(host, port, timeout, wait_seconds)
    after = process_snapshot()
    started = _new_processes(before, after)
    return OpenDLifecycle(
        socket_was_reachable=False,
        socket_is_reachable=reachable,
        auto_start_requested=True,
        start_attempted=True,
        started_by_tool=reachable,
        start_command=workbench.start_script,
        cleanup_requested=cleanup_if_started,
        cleanup_attempted=False,
        cleanup_result=None,
        before_processes=before,
        after_processes=after,
        started_processes=started,
        detail=(
            f"OpenD auto-started via {workbench.start_script}"
            if reachable
            else f"OpenD start attempted via {workbench.start_script}, but socket did not become reachable"
        ),
    )


def lifecycle_to_dict(lifecycle: OpenDLifecycle) -> dict[str, object]:
    data = asdict(lifecycle)
    return data
