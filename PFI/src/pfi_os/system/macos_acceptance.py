from __future__ import annotations

import os
import plistlib
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json


MACOS_ACCEPTANCE_LITE_SCHEMA = "PFIOSMacOSAppAcceptanceLiteV1"
APP_BUNDLE_NAME = "PFI.app"
APP_EXECUTABLE_NAME = "PFI"


@dataclass(frozen=True)
class AppTarget:
    label: str
    path: Path
    requires_binding: bool = True


def default_app_targets(*, home: Path | None = None, applications_dir: Path | None = None, project_root: Path | str = PROJECT_ROOT) -> tuple[AppTarget, ...]:
    home = home or Path.home()
    applications_dir = applications_dir or Path("/Applications")
    root = Path(project_root).expanduser()
    return (
        AppTarget("Source Template", root / "macos" / APP_BUNDLE_NAME, requires_binding=False),
        AppTarget("Desktop", home / "Desktop" / APP_BUNDLE_NAME),
        AppTarget("Downloads", home / "Downloads" / APP_BUNDLE_NAME),
        AppTarget("Applications", applications_dir / APP_BUNDLE_NAME),
    )


def build_macos_app_acceptance_lite(
    *,
    project_root: Path | str = PROJECT_ROOT,
    app_targets: tuple[AppTarget, ...] | None = None,
    skip_codesign: bool = False,
    run_dry_run: bool = True,
    run_status_script: bool = True,
    dry_run_timeout_seconds: int = 5,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    targets = app_targets or default_app_targets(project_root=root)
    checks: list[dict[str, Any]] = []
    for target in targets:
        checks.extend(_app_checks(root, target, skip_codesign=skip_codesign, run_dry_run=run_dry_run, dry_run_timeout_seconds=dry_run_timeout_seconds))
    checks.extend(_project_checks(root))
    runtime_status = _runtime_status(root, run_status_script=run_status_script)
    summary = _summary(checks)
    return {
        "schema": MACOS_ACCEPTANCE_LITE_SCHEMA,
        "system": "PFI",
        "subsystem": "macOS App Acceptance Lite",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": _overall_status(summary),
        "project_root": str(root),
        "target_count": len(targets),
        "summary": summary,
        "runtime_status": runtime_status,
        "checks": checks,
        "heavy_smoke_policy": (
            "Lite acceptance does not run scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, "
            "market-data refresh, or browser automation."
        ),
        "safety_boundary": (
            "Read-only local app-entry verification. It does not start the app unless an explicit launcher dry-run is enabled; "
            "dry-run mode does not open Terminal, browser windows, broker connections, orders, payments, or holdings writes."
        ),
        "next_action": _next_action(summary),
    }


def write_macos_app_acceptance_lite(
    *,
    output_dir: Path | str,
    project_root: Path | str = PROJECT_ROOT,
    app_targets: tuple[AppTarget, ...] | None = None,
    skip_codesign: bool = False,
    run_dry_run: bool = True,
    run_status_script: bool = True,
) -> dict[str, Any]:
    payload = build_macos_app_acceptance_lite(
        project_root=project_root,
        app_targets=app_targets,
        skip_codesign=skip_codesign,
        run_dry_run=run_dry_run,
        run_status_script=run_status_script,
    )
    target = Path(output_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%d%m%Y")
    json_path = target / f"MacOSAppAcceptanceLite_{stamp}.json"
    latest_path = target / "MacOSAppAcceptanceLite_latest.json"
    payload["outputs"] = {
        "json": str(json_path),
        "latest_json": str(latest_path),
    }
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_path, payload)
    return payload


def _app_checks(
    root: Path,
    target: AppTarget,
    *,
    skip_codesign: bool,
    run_dry_run: bool,
    dry_run_timeout_seconds: int,
) -> list[dict[str, Any]]:
    app_path = target.path.expanduser()
    executable = app_path / "Contents" / "MacOS" / APP_EXECUTABLE_NAME
    plist_path = app_path / "Contents" / "Info.plist"
    root_file = app_path / "Contents" / "Resources" / "PFI_PROJECT_ROOT"
    checks = [
        _check(target.label, "AppBundleExists", "Pass" if app_path.is_dir() else "Fail", str(app_path)),
        _check(target.label, "LauncherExecutable", "Pass" if _is_executable(executable) else "Fail", str(executable)),
        _plist_check(target.label, plist_path),
        _github_fallback_check(target.label, executable),
    ]
    if target.requires_binding:
        checks.append(_project_binding_check(target.label, root_file, root))
    else:
        checks.append(_check(target.label, "ProjectBinding", "Info", "source template uses parent checkout discovery"))
    if skip_codesign:
        checks.append(_check(target.label, "CodeSignature", "Info", "skipped by caller"))
    elif not target.requires_binding:
        checks.append(_check(target.label, "CodeSignature", "Info", "source template signature is verified after installation"))
    else:
        checks.append(_codesign_check(target.label, app_path))
    if run_dry_run:
        checks.append(_dry_run_check(target.label, executable, dry_run_timeout_seconds))
    else:
        checks.append(_check(target.label, "LauncherDryRun", "Info", "skipped by caller"))
    return checks


def _project_checks(root: Path) -> list[dict[str, Any]]:
    return [
        _check("Project", "StartCommandExecutable", "Pass" if _is_executable(root / "StartPFI.command") else "Fail", "StartPFI.command"),
        _check("Project", "StatusScriptExecutable", "Pass" if _is_executable(root / "scripts" / "statusPFI.sh") else "Fail", "scripts/statusPFI.sh"),
        _check("Project", "HeavySmokeNotRequired", "Pass", "finalAcceptanceCheck.sh and ciSmoke.sh are intentionally not invoked by lite acceptance"),
    ]


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
    if not _is_executable(script):
        payload["status_script"] = {"returncode": 127, "stdout": "", "stderr": "status script missing or not executable"}
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


def _plist_check(label: str, plist_path: Path) -> dict[str, Any]:
    if not plist_path.is_file():
        return _check(label, "InfoPlist", "Fail", f"missing: {plist_path}")
    try:
        with plist_path.open("rb") as handle:
            payload = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException) as exc:
        return _check(label, "InfoPlist", "Fail", f"{type(exc).__name__}: {exc}")
    display = payload.get("CFBundleDisplayName") or payload.get("CFBundleName")
    executable = payload.get("CFBundleExecutable")
    status = "Pass" if display == "PFI" and executable == APP_EXECUTABLE_NAME else "Fail"
    return _check(label, "InfoPlist", status, f"display={display}; executable={executable}")


def _project_binding_check(label: str, root_file: Path, root: Path) -> dict[str, Any]:
    if not root_file.is_file():
        return _check(label, "ProjectBinding", "Fail", f"missing: {root_file}")
    try:
        binding = root_file.read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError) as exc:
        return _check(label, "ProjectBinding", "Fail", f"{type(exc).__name__}: {exc}")
    try:
        matches = Path(binding).expanduser().resolve() == root
    except OSError:
        matches = False
    return _check(label, "ProjectBinding", "Pass" if matches else "Fail", f"binding={binding}")


def _github_fallback_check(label: str, executable: Path) -> dict[str, Any]:
    if not executable.is_file():
        return _check(label, "NoGitHubFallback", "Fail", f"missing executable: {executable}")
    try:
        content = executable.read_bytes()
    except OSError as exc:
        return _check(label, "NoGitHubFallback", "Fail", f"{type(exc).__name__}: {exc}")
    found = b"github.com/LinzeColin/PFI" in content
    return _check(label, "NoGitHubFallback", "Fail" if found else "Pass", "github fallback absent" if not found else "github fallback present")


def _codesign_check(label: str, app_path: Path) -> dict[str, Any]:
    if not app_path.is_dir():
        return _check(label, "CodeSignature", "Fail", f"missing: {app_path}")
    completed = subprocess.run(
        ["/usr/bin/codesign", "--verify", "--deep", str(app_path)],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    evidence = (completed.stderr or completed.stdout or "codesign verify returned no output").strip()
    return _check(label, "CodeSignature", "Pass" if completed.returncode == 0 else "Fail", evidence)


def _dry_run_check(label: str, executable: Path, timeout_seconds: int) -> dict[str, Any]:
    if not _is_executable(executable):
        return _check(label, "LauncherDryRun", "Fail", f"not executable: {executable}")
    env = dict(os.environ)
    env["PFI_APP_LAUNCH_DRY_RUN"] = "1"
    timeout = max(1, int(timeout_seconds))
    try:
        completed = subprocess.run(
            [str(executable)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        output = f"{exc.stdout or ''} {exc.stderr or ''}".strip()
        return _check(label, "LauncherDryRun", "Fail", output or f"timeout after {timeout} seconds")
    output = f"{completed.stdout.strip()} {completed.stderr.strip()}".strip()
    ok = completed.returncode == 0 and (
        "mode=open-command" in output
        or "mode=spawn-command" in output
    )
    return _check(label, "LauncherDryRun", "Pass" if ok else "Fail", output or f"returncode={completed.returncode}")


def _is_executable(path: Path) -> bool:
    try:
        mode = path.stat().st_mode
    except OSError:
        return False
    return path.is_file() and bool(mode & stat.S_IXUSR)


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


def _overall_status(summary: dict[str, int]) -> str:
    return "Pass" if summary.get("fail", 0) == 0 else "Blocked"


def _next_action(summary: dict[str, int]) -> str:
    if summary.get("fail", 0):
        return "Run scripts/installPFIEntryApps.sh, then rerun scripts/macosAppAcceptanceLite.sh --json."
    return "Use PFI.app for normal launch; reserve finalAcceptanceCheck.sh for deliberate full release gates."
