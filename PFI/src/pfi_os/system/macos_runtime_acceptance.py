from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json
from pfi_os.system.macos_acceptance import AppTarget, build_macos_app_acceptance_lite


MACOS_RUNTIME_ACCEPTANCE_SCHEMA = "PFIOSMacOSRuntimeAcceptanceV1"
SUPPORT_SCRIPT_TIMEOUT_FLOOR_SECONDS = 30
CACHE_DRY_RUN_TIMEOUT_FLOOR_SECONDS = 60
APP_ACCEPTANCE_DRY_RUN_TIMEOUT_SECONDS = 12
APP_ACCEPTANCE_RETRY_COUNT = 1
APP_ACCEPTANCE_RETRY_SLEEP_SECONDS = 1.0


def run_macos_runtime_acceptance(
    *,
    project_root: Path | str = PROJECT_ROOT,
    start_timeout_seconds: int = 90,
    stop_timeout_seconds: int = 45,
    include_app_acceptance: bool = True,
    allow_existing_service: bool = False,
    launch_method: str = "script",
    app_path: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    method = "app" if str(launch_method).lower() == "app" else "script"
    checks: list[dict[str, Any]] = []
    started_process: subprocess.Popen[str] | None = None
    started_by_acceptance = False

    app_acceptance = _app_acceptance_summary(root, app_path=app_path if method == "app" else None) if include_app_acceptance else {"status": "Skipped"}
    if include_app_acceptance:
        checks.append(_app_acceptance_check(app_acceptance))

    pre_ports = _healthy_ports()
    if pre_ports and not allow_existing_service:
        checks.append(_check("Runtime", "NoPreExistingService", "Fail", f"healthy_ports={pre_ports}"))
        return _payload(root, checks, pre_ports, [], app_acceptance, started_by_acceptance=False, launch_method=method)
    checks.append(_check("Runtime", "NoPreExistingService", "Pass" if not pre_ports else "Info", f"healthy_ports={pre_ports}"))

    try:
        if pre_ports:
            healthy_after_start = pre_ports
            checks.append(_check("Start", "StartCommandLaunched", "Info", "using pre-existing service by explicit caller option"))
        else:
            if method == "app":
                app_launch = _launch_app(root, app_path)
                checks.append(_script_check("Start", "AppOpenLaunched", app_launch, expected_text=""))
            else:
                started_process = _start_process(root)
                checks.append(_check("Start", "StartCommandLaunched", "Pass", "scripts/startPFI.sh launched in controlled background mode"))
            started_by_acceptance = True
            healthy_after_start = _wait_for_healthy_ports(start_timeout_seconds)
        checks.append(_check("Start", "HealthAfterStart", "Pass" if healthy_after_start else "Fail", f"healthy_ports={healthy_after_start}"))
        if not healthy_after_start:
            stop_after_failed_start = _run_script(root, ["scripts/stopPFI.sh"], timeout_seconds=max(10, stop_timeout_seconds))
            checks.append(_script_check("Stop", "StopAfterFailedStart", stop_after_failed_start, expected_text="PFI 停止命令已完成。"))
            return _payload(
                root,
                checks,
                pre_ports,
                _healthy_ports(),
                app_acceptance,
                started_by_acceptance=started_by_acceptance,
                launch_method=method,
            )

        support_timeout = _support_script_timeout(stop_timeout_seconds)
        cache_preview_timeout = _cache_preview_timeout(stop_timeout_seconds)

        running_status = _run_script(root, ["scripts/statusPFI.sh"], timeout_seconds=support_timeout)
        checks.append(_script_check("Runtime", "StatusSeesRunning", running_status, expected_text="PFI 正在运行"))

        cache_guard = _run_script(root, ["scripts/cleanCache.sh", "--json"], timeout_seconds=support_timeout)
        cache_guard_output = f"{cache_guard['stdout']} {cache_guard['stderr']}".strip()
        cache_guard_ok = cache_guard["returncode"] == 2 and "Stop it before cleaning cache" in cache_guard_output
        checks.append(
            _check(
                "Cache",
                "CleanCacheRefusesWhileRunning",
                "Pass" if cache_guard_ok else "Fail",
                f"returncode={cache_guard['returncode']}; output={cache_guard_output[:240]}",
            )
        )

        stop_result = _run_script(root, ["scripts/stopPFI.sh"], timeout_seconds=max(10, stop_timeout_seconds))
        checks.append(_script_check("Stop", "StopScriptRuns", stop_result, expected_text="PFI 停止命令已完成。"))

        stopped_ports = _wait_for_stopped(stop_timeout_seconds)
        checks.append(_check("Stop", "HealthAfterStop", "Pass" if not stopped_ports else "Fail", f"healthy_ports={stopped_ports}"))

        stopped_status = _run_script(root, ["scripts/statusPFI.sh"], timeout_seconds=support_timeout)
        checks.append(_script_check("Stop", "StatusSeesStopped", stopped_status, expected_text="未在端口"))

        cache_preview = _run_script(root, ["scripts/cleanCache.sh", "--dry-run", "--json"], timeout_seconds=cache_preview_timeout)
        cache_preview_ok = cache_preview["returncode"] == 0 and "PFICacheCleanupReportV1" in cache_preview["stdout"]
        checks.append(
            _check(
                "Cache",
                "CleanCacheDryRunAfterStop",
                "Pass" if cache_preview_ok else "Fail",
                f"returncode={cache_preview['returncode']}; summary={_cache_preview_summary(cache_preview['stdout'])}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("Runtime", "UnexpectedException", "Fail", f"{type(exc).__name__}: {exc}"))
    finally:
        if started_by_acceptance:
            _run_script(root, ["scripts/stopPFI.sh"], timeout_seconds=max(10, stop_timeout_seconds))
        _finalize_process(started_process)

    return _payload(
        root,
        checks,
        pre_ports,
        _healthy_ports(),
        app_acceptance,
        started_by_acceptance=started_by_acceptance,
        launch_method=method,
    )


def write_macos_runtime_acceptance(
    *,
    output_dir: Path | str,
    project_root: Path | str = PROJECT_ROOT,
    start_timeout_seconds: int = 90,
    stop_timeout_seconds: int = 45,
    include_app_acceptance: bool = True,
    allow_existing_service: bool = False,
    launch_method: str = "script",
    app_path: Path | str | None = None,
) -> dict[str, Any]:
    payload = run_macos_runtime_acceptance(
        project_root=project_root,
        start_timeout_seconds=start_timeout_seconds,
        stop_timeout_seconds=stop_timeout_seconds,
        include_app_acceptance=include_app_acceptance,
        allow_existing_service=allow_existing_service,
        launch_method=launch_method,
        app_path=app_path,
    )
    target = Path(output_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%d%m%Y")
    json_path = target / f"MacOSRuntimeAcceptance_{stamp}.json"
    latest_path = target / "MacOSRuntimeAcceptance_latest.json"
    payload["outputs"] = {
        "json": str(json_path),
        "latest_json": str(latest_path),
    }
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_path, payload)
    return payload


def _payload(
    root: Path,
    checks: list[dict[str, Any]],
    pre_ports: list[int],
    post_ports: list[int],
    app_acceptance: dict[str, Any],
    *,
    started_by_acceptance: bool,
    launch_method: str,
) -> dict[str, Any]:
    summary = _summary(checks)
    return {
        "schema": MACOS_RUNTIME_ACCEPTANCE_SCHEMA,
        "system": "PFI",
        "subsystem": "macOS Runtime Acceptance",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "Pass" if summary["fail"] == 0 else "Blocked",
        "project_root": str(root),
        "summary": summary,
        "pre_existing_healthy_ports": pre_ports,
        "post_healthy_ports": post_ports,
        "started_by_acceptance": started_by_acceptance,
        "launch_method": launch_method,
        "app_acceptance": app_acceptance,
        "checks": checks,
        "runtime_contract": {
            "start": "Launches scripts/startPFI.sh or opens a configured PFI.app in controlled mode when no existing service is running.",
            "health": "Requires a local /_stcore/health response on 127.0.0.1 ports 8501-8510.",
            "cache_guard": "Verifies scripts/cleanCache.sh refuses delete mode while the service is running.",
            "stop": "Runs scripts/stopPFI.sh and verifies local health disappears.",
            "post_stop_cache": "Verifies cleanCache dry-run works after the service is stopped.",
        },
        "heavy_smoke_policy": (
            "Runtime acceptance does not run scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, "
            "browser automation, market-data refresh, broker connections, orders, payments, or holdings writes."
        ),
        "safety_boundary": (
            "Controlled local start/health/stop/cache-guard acceptance. Script mode does not open a browser; app mode uses "
            "the real macOS app entry and may open the default browser. It refuses to proceed by default if a pre-existing "
            "PFI service is already running."
        ),
        "next_action": "If this passes on the Mac, the next acceptance step can be optional visual UI verification or app-click verification.",
    }


def _app_acceptance_summary(root: Path, *, app_path: Path | str | None = None) -> dict[str, Any]:
    attempts = []
    payload: dict[str, Any] = {}
    app_targets = None
    if app_path is not None:
        app_targets = (AppTarget("Requested App", Path(app_path).expanduser()),)
    for attempt in range(APP_ACCEPTANCE_RETRY_COUNT + 1):
        payload = build_macos_app_acceptance_lite(
            project_root=root,
            app_targets=app_targets,
            run_status_script=False,
            dry_run_timeout_seconds=APP_ACCEPTANCE_DRY_RUN_TIMEOUT_SECONDS,
        )
        attempts.append(_compact_app_acceptance_attempt(payload))
        if payload.get("status") == "Pass":
            break
        if attempt < APP_ACCEPTANCE_RETRY_COUNT:
            time.sleep(APP_ACCEPTANCE_RETRY_SLEEP_SECONDS)
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "summary": payload.get("summary", {}),
        "attempts": len(attempts),
        "failed_checks": [
            row
            for row in payload.get("checks", [])
            if isinstance(row, dict) and row.get("status") == "Fail"
        ],
        "attempt_history": attempts,
        "heavy_smoke_policy": payload.get("heavy_smoke_policy", ""),
    }


def _compact_app_acceptance_attempt(payload: dict[str, Any]) -> dict[str, Any]:
    failed = [row for row in payload.get("checks", []) if isinstance(row, dict) and row.get("status") == "Fail"]
    return {
        "status": payload.get("status"),
        "fail": payload.get("summary", {}).get("fail", 0),
        "failed_checks": [
            {
                "target": str(row.get("target", "")),
                "check": str(row.get("check", "")),
                "evidence": str(row.get("evidence", ""))[:240],
            }
            for row in failed[:6]
        ],
    }


def _app_acceptance_check(summary: dict[str, Any]) -> dict[str, Any]:
    ok = summary.get("schema") == "PFIOSMacOSAppAcceptanceLiteV1" and summary.get("status") == "Pass"
    evidence = f"status={summary.get('status')}; fail={summary.get('summary', {}).get('fail', 0)}"
    return _check("App", "LiteAcceptancePasses", "Pass" if ok else "Fail", evidence)


def _start_process(root: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [str(root / "scripts" / "startPFI.sh")],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _launch_app(root: Path, app_path: Path | str | None) -> dict[str, Any]:
    target = Path(app_path).expanduser() if app_path else Path.home() / "Downloads" / "PFI.app"
    if not target.is_dir():
        fallback = root / "macos" / "PFI.app"
        target = fallback if fallback.is_dir() else target
    completed = subprocess.run(
        ["/usr/bin/open", "-n", str(target)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    evidence = [completed.stdout.strip() or f"opened={target}"]
    if completed.stderr.strip():
        evidence.append(completed.stderr.strip())
    if completed.returncode == 0 and not _app_launch_observed(root, wait_seconds=12):
        executable = target / "Contents" / "MacOS" / "PFI"
        if executable.is_file():
            direct = subprocess.run(
                [str(executable)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            evidence.append(f"direct_fallback={executable}; returncode={direct.returncode}")
            if direct.stdout.strip():
                evidence.append(direct.stdout.strip())
            if direct.stderr.strip():
                evidence.append(direct.stderr.strip())
            if completed.returncode == 0 and direct.returncode != 0:
                completed = direct
    return {
        "returncode": completed.returncode,
        "stdout": " | ".join(part for part in evidence if part),
        "stderr": "",
    }


def _app_launch_observed(root: Path, *, wait_seconds: int) -> bool:
    log_path = root / "data" / "cache" / "pfi_os_macos_app.log"
    deadline = time.time() + max(1, int(wait_seconds))
    while time.time() < deadline:
        if _healthy_ports():
            return True
        if log_path.is_file() and log_path.stat().st_size > 0:
            return True
        time.sleep(1)
    return bool(_healthy_ports() or (log_path.is_file() and log_path.stat().st_size > 0))


def _run_script(root: Path, args: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [str(root / args[0]), *args[1:]],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout_seconds)),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = getattr(exc, "stdout", None) or getattr(exc, "output", None) or ""
        stderr = getattr(exc, "stderr", None) or ""
        return {
            "returncode": 124,
            "stdout": stdout.strip() if isinstance(stdout, str) else "",
            "stderr": (stderr.strip() if isinstance(stderr, str) else "") or f"timeout after {timeout_seconds} seconds",
        }
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _support_script_timeout(stop_timeout_seconds: int) -> int:
    return max(SUPPORT_SCRIPT_TIMEOUT_FLOOR_SECONDS, int(stop_timeout_seconds))


def _cache_preview_timeout(stop_timeout_seconds: int) -> int:
    return max(CACHE_DRY_RUN_TIMEOUT_FLOOR_SECONDS, int(stop_timeout_seconds))


def _script_check(target: str, check: str, result: dict[str, Any], *, expected_text: str) -> dict[str, Any]:
    output = f"{result['stdout']} {result['stderr']}".strip()
    ok = result["returncode"] == 0 and (not expected_text or expected_text in output)
    return _check(target, check, "Pass" if ok else "Fail", f"returncode={result['returncode']}; output={output[:240]}")


def _wait_for_healthy_ports(timeout_seconds: int) -> list[int]:
    deadline = time.time() + max(1, int(timeout_seconds))
    while time.time() < deadline:
        ports = _healthy_ports()
        if ports:
            return ports
        time.sleep(1)
    return _healthy_ports()


def _wait_for_stopped(timeout_seconds: int) -> list[int]:
    deadline = time.time() + max(1, int(timeout_seconds))
    ports = _healthy_ports()
    while ports and time.time() < deadline:
        time.sleep(1)
        ports = _healthy_ports()
    return ports


def _healthy_ports() -> list[int]:
    return [port for port in range(8501, 8511) if _streamlit_health_ok(port)]


def _streamlit_health_ok(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
            return 200 <= int(response.status) < 300
    except (OSError, URLError, TimeoutError, ValueError):
        return False


def _cache_preview_summary(stdout: str) -> str:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout[:160]
    return f"candidates={payload.get('candidate_count')}; files={payload.get('candidate_file_count')}; kb={payload.get('candidate_kb')}"


def _finalize_process(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=8)
    try:
        process.communicate(timeout=2)
    except (subprocess.TimeoutExpired, ValueError):
        return


def _check(target: str, check: str, status: str, evidence: str) -> dict[str, Any]:
    return {
        "target": target,
        "check": check,
        "status": status if status in {"Pass", "Fail", "Info"} else "Fail",
        "evidence": evidence,
    }


def _summary(checks: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "pass": sum(1 for row in checks if row["status"] == "Pass"),
        "fail": sum(1 for row in checks if row["status"] == "Fail"),
        "info": sum(1 for row in checks if row["status"] == "Info"),
        "total": len(checks),
    }
