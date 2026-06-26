from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json
from pfi_os.system.macos_acceptance import build_macos_app_acceptance_lite


MACOS_LIFECYCLE_READINESS_SCHEMA = "PFIOSMacOSLifecycleReadinessV1"


def build_macos_lifecycle_readiness(
    *,
    project_root: Path | str = PROJECT_ROOT,
    run_status_script: bool = True,
    include_cache_preview: bool = True,
    include_app_acceptance: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    checks = _static_lifecycle_checks(root)
    runtime_status = _runtime_status(root, run_status_script=run_status_script)
    if runtime_status["status_script"].get("returncode") not in {0, None}:
        checks.append(_check("Runtime", "StatusScriptRuns", "Fail", str(runtime_status["status_script"].get("stderr", ""))))
    elif run_status_script:
        checks.append(_check("Runtime", "StatusScriptRuns", "Pass", str(runtime_status["status_script"].get("stdout", ""))))
    else:
        checks.append(_check("Runtime", "StatusScriptRuns", "Info", "skipped by caller"))

    cache_preview = _cache_preview(root) if include_cache_preview else {"status": "Skipped"}
    if include_cache_preview:
        checks.append(_cache_preview_check(cache_preview))

    app_acceptance = _app_acceptance_summary(root) if include_app_acceptance else {"status": "Skipped"}
    if include_app_acceptance:
        checks.append(_app_acceptance_check(app_acceptance))

    summary = _summary(checks)
    return {
        "schema": MACOS_LIFECYCLE_READINESS_SCHEMA,
        "system": "PFI",
        "subsystem": "macOS Lifecycle Readiness",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "Pass" if summary["fail"] == 0 else "Blocked",
        "project_root": str(root),
        "summary": summary,
        "runtime_status": runtime_status,
        "cache_preview": cache_preview,
        "app_acceptance": app_acceptance,
        "checks": checks,
        "lifecycle_contract": {
            "start": "StartPFI.command or scripts/startPFI.sh starts local Streamlit on 127.0.0.1 and reuses an existing service.",
            "stop": "scripts/stopPFI.sh only stops Streamlit processes for this checkout.",
            "auto_shutdown": "StartPFI.command runs pfi_os.system.shutdown_monitor; the UI sends sanitized localhost heartbeat requests.",
            "cache_cleanup": "scripts/cleanCache.sh refuses delete mode while Streamlit is running and only removes disposable caches.",
            "app_acceptance": "scripts/macosAppAcceptanceLite.sh checks app entry points without full smoke.",
            "ui_controls": "Streamlit lifecycle panel only runs allowlisted local read-only/confirmed lifecycle scripts.",
        },
        "heavy_smoke_policy": (
            "Lifecycle readiness does not run scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, "
            "browser automation, market-data refresh, broker connections, orders, payments, or holdings writes."
        ),
        "safety_boundary": (
            "Read-only readiness inspection. It may run statusPFI.sh and build dry-run cache/app summaries, "
            "but it does not start, stop, clean, trade, scrape, pay, or mutate holdings."
        ),
        "next_action": "Use macosAppAcceptanceLite.sh for daily app-entry checks; reserve finalAcceptanceCheck.sh for deliberate release gates.",
    }


def write_macos_lifecycle_readiness(
    *,
    output_dir: Path | str,
    project_root: Path | str = PROJECT_ROOT,
    run_status_script: bool = True,
    include_cache_preview: bool = True,
    include_app_acceptance: bool = True,
) -> dict[str, Any]:
    payload = build_macos_lifecycle_readiness(
        project_root=project_root,
        run_status_script=run_status_script,
        include_cache_preview=include_cache_preview,
        include_app_acceptance=include_app_acceptance,
    )
    target = Path(output_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%d%m%Y")
    json_path = target / f"MacOSLifecycleReadiness_{stamp}.json"
    latest_path = target / "MacOSLifecycleReadiness_latest.json"
    payload["outputs"] = {
        "json": str(json_path),
        "latest_json": str(latest_path),
    }
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_path, payload)
    return payload


def _static_lifecycle_checks(root: Path) -> list[dict[str, Any]]:
    start_command = root / "StartPFI.command"
    start_script = root / "scripts" / "startPFI.sh"
    stop_script = root / "scripts" / "stopPFI.sh"
    status_script = root / "scripts" / "statusPFI.sh"
    clean_script = root / "scripts" / "cleanCache.sh"
    dev_ready_script = root / "scripts" / "devReadyCheck.sh"
    lite_script = root / "scripts" / "macosAppAcceptanceLite.sh"
    streamlit_app = root / "src" / "pfi_os" / "app" / "streamlit_app.py"
    shutdown_monitor = root / "src" / "pfi_os" / "system" / "shutdown_monitor.py"
    cache_cleanup = root / "src" / "pfi_os" / "system" / "cache_cleanup.py"
    checks = [
        _executable_check("Command", "StartPFIExecutable", start_command),
        _executable_check("Script", "StartScriptExecutable", start_script),
        _executable_check("Script", "StopScriptExecutable", stop_script),
        _executable_check("Script", "StatusScriptExecutable", status_script),
        _executable_check("Script", "CleanCacheScriptExecutable", clean_script),
        _executable_check("Script", "DevReadyScriptExecutable", dev_ready_script),
        _executable_check("Script", "LiteAcceptanceScriptExecutable", lite_script),
        _text_check("Start", "RuntimeResolver", start_command, ("pfi_os_ensure_app_python",)),
        _text_check("Start", "LocalhostBinding", start_command, ("--server.address", "127.0.0.1")),
        _text_check("Start", "NoFileWatcher", start_command, ("--server.fileWatcherType", "none")),
        _text_check("Start", "NoBrowserStats", start_command, ("--browser.gatherUsageStats", "false")),
        _text_check("Start", "LaunchLock", start_command, ("pfi_os_launch.lockdir", "LOCK_PID_FILE")),
        _text_check("Start", "AutoShutdownMonitor", start_command, ("pfi_os.system.shutdown_monitor", "STREAMLIT_PID")),
        _text_check("Start", "HeartbeatUrl", start_command, ("PFI_HEARTBEAT_URL", "HEARTBEAT_PORT")),
        _text_check("Start", "HeartbeatTimeoutDefault", start_command, ("PFI_HEARTBEAT_TIMEOUT:-120",)),
        _text_check("QuietStart", "RuntimeResolver", start_script, ("pfi_os_ensure_app_python",)),
        _text_check("QuietStart", "LocalhostBinding", start_script, ("--server.address", "127.0.0.1")),
        _text_check("Stop", "ScopedStop", stop_script, ("process_cwd", 'cwd_path" == "$PROJECT_DIR"', "src/pfi_os/app/streamlit_app.py")),
        _text_absent_check("Stop", "NoGlobalKill", stop_script, ("xargs kill", "pkill -f")),
        _text_check("Cache", "RefusesWhileRunning", clean_script, ("Stop it before cleaning cache", "streamlit_app.py")),
        _text_check("Cache", "ScopedRunningDetection", clean_script, ("pfi_os_is_running", "process_cwd", 'cwd_path" == "$PROJECT_DIR"')),
        _text_check("Cache", "DryRunMode", clean_script, ("--dry-run", "pfi_os.system.cache_cleanup")),
        _text_check("Cache", "PreservesArtifacts", cache_cleanup, ("Reports, holdings", "market bar caches are not deleted")),
        _text_check("Heartbeat", "UIHeartbeatInstalled", streamlit_app, ("install_shutdown_heartbeat()", "PFI_HEARTBEAT_URL", "fetch(heartbeatUrl")),
        _text_check("Heartbeat", "HeartbeatUrlSanitized", streamlit_app, ("_safe_heartbeat_url", "127.0.0.1")),
        _text_check("Heartbeat", "MonitorRequiresSeenHeartbeat", shutdown_monitor, ("seen_heartbeat", "should_shutdown", "stable_timeout")),
        _text_check(
            "UI",
            "LifecycleAllowlist",
            streamlit_app,
            ("LIFECYCLE_SCRIPT_ALLOWLIST", "scripts/devReadyCheck.sh", "scripts/macosAppAcceptanceLite.sh", "scripts/macosLifecycleReadiness.sh"),
        ),
    ]
    return checks


def _runtime_status(root: Path, *, run_status_script: bool) -> dict[str, Any]:
    healthy_ports = []
    for port in range(8501, 8511):
        if _streamlit_health_ok(port):
            healthy_ports.append(port)
    payload: dict[str, Any] = {
        "status": "Running" if healthy_ports else "Stopped",
        "healthy_ports": healthy_ports,
        "health_urls": [f"http://127.0.0.1:{port}/_stcore/health" for port in healthy_ports],
    }
    if not run_status_script:
        payload["status_script"] = {"returncode": None, "stdout": "", "stderr": "skipped by caller"}
        return payload
    script = root / "scripts" / "statusPFI.sh"
    if not script.is_file():
        payload["status_script"] = {"returncode": 127, "stdout": "", "stderr": "status script missing"}
        return payload
    completed = subprocess.run([str(script)], cwd=root, capture_output=True, text=True, timeout=8, check=False)
    payload["status_script"] = {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    return payload


def _streamlit_health_ok(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
            return 200 <= int(response.status) < 300
    except (OSError, URLError, TimeoutError, ValueError):
        return False


def _cache_preview(root: Path) -> dict[str, Any]:
    from pfi_os.system.cache_cleanup import build_cache_cleanup_report

    report = build_cache_cleanup_report(root, dry_run=True)
    return {
        "schema": report.get("schema"),
        "mode": report.get("mode"),
        "candidate_count": report.get("candidate_count", 0),
        "candidate_file_count": report.get("candidate_file_count", 0),
        "candidate_dir_count": report.get("candidate_dir_count", 0),
        "candidate_kb": report.get("candidate_kb", 0),
        "failed_count": report.get("failed_count", 0),
        "safety_boundary": report.get("safety_boundary", ""),
    }


def _app_acceptance_summary(root: Path) -> dict[str, Any]:
    payload = build_macos_app_acceptance_lite(project_root=root, run_status_script=False)
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "summary": payload.get("summary", {}),
        "runtime_status": payload.get("runtime_status", {}),
        "heavy_smoke_policy": payload.get("heavy_smoke_policy", ""),
    }


def _cache_preview_check(preview: dict[str, Any]) -> dict[str, Any]:
    ok = preview.get("schema") == "PFICacheCleanupReportV1" and preview.get("failed_count", 0) == 0
    evidence = f"candidates={preview.get('candidate_count', 0)}; failed={preview.get('failed_count', 0)}"
    return _check("Cache", "DryRunPreview", "Pass" if ok else "Fail", evidence)


def _app_acceptance_check(summary: dict[str, Any]) -> dict[str, Any]:
    ok = summary.get("schema") == "PFIOSMacOSAppAcceptanceLiteV1" and summary.get("status") == "Pass"
    evidence = f"status={summary.get('status')}; fail={summary.get('summary', {}).get('fail', 0)}"
    return _check("App", "LiteAcceptancePasses", "Pass" if ok else "Fail", evidence)


def _executable_check(target: str, check: str, path: Path) -> dict[str, Any]:
    ok = path.is_file() and path.stat().st_mode & 0o100
    return _check(target, check, "Pass" if ok else "Fail", str(path))


def _text_check(target: str, check: str, path: Path, needles: tuple[str, ...]) -> dict[str, Any]:
    content = _read_text(path)
    missing = [needle for needle in needles if needle not in content]
    status = "Pass" if not missing else "Fail"
    evidence = "present: " + ", ".join(needles) if not missing else "missing: " + ", ".join(missing)
    return _check(target, check, status, evidence)


def _text_absent_check(target: str, check: str, path: Path, needles: tuple[str, ...]) -> dict[str, Any]:
    content = _read_text(path)
    found = [needle for needle in needles if needle in content]
    status = "Pass" if not found else "Fail"
    evidence = "absent: " + ", ".join(needles) if not found else "found: " + ", ".join(found)
    return _check(target, check, status, evidence)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


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
