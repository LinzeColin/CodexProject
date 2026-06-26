from __future__ import annotations

import ast
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json


DEV_READY_CHECK_SCHEMA = "PFIOSDevReadyCheckV1"

SHELL_SYNTAX_TARGETS = (
    "StartPFI.command",
    "StopPFI.command",
    "scripts/statusPFI.sh",
    "scripts/cleanCache.sh",
    "scripts/macosAcceptance.sh",
    "scripts/macosAppAcceptanceLite.sh",
    "scripts/macosLifecycleReadiness.sh",
    "scripts/hotspotRuntimeSummary.sh",
    "scripts/uiVisualAcceptance.sh",
    "scripts/macosPublicAcceptanceSummary.sh",
    "scripts/devReadyCheck.sh",
    "scripts/reportValidation.sh",
)

PYTHON_SYNTAX_TARGETS = (
    "src/pfi_os/app/streamlit_app.py",
    "src/pfi_os/analysis/market_hotspots.py",
    "src/pfi_os/system/cache_cleanup.py",
    "src/pfi_os/system/macos_acceptance_hub.py",
    "src/pfi_os/system/macos_lifecycle.py",
    "src/pfi_os/system/macos_runtime_acceptance.py",
    "src/pfi_os/system/macos_public_acceptance.py",
    "src/pfi_os/system/dev_readiness.py",
    "src/pfi_os/system/report_validation_hub.py",
    "src/pfi_os/examples/hotspot_runtime_summary.py",
    "src/pfi_os/examples/macos_acceptance_hub.py",
    "src/pfi_os/examples/macos_public_acceptance.py",
    "src/pfi_os/examples/dev_ready_check.py",
    "src/pfi_os/examples/report_validation_hub.py",
)

REQUIRED_EXECUTABLES = (
    "scripts/statusPFI.sh",
    "scripts/cleanCache.sh",
    "scripts/macosAcceptance.sh",
    "scripts/macosAppAcceptanceLite.sh",
    "scripts/macosLifecycleReadiness.sh",
    "scripts/hotspotRuntimeSummary.sh",
    "scripts/uiVisualAcceptance.sh",
    "scripts/macosPublicAcceptanceSummary.sh",
    "scripts/devReadyCheck.sh",
    "scripts/reportValidation.sh",
)


def build_dev_ready_check(
    *,
    project_root: Path | str = PROJECT_ROOT,
    run_status_script: bool = True,
    include_cache_preview: bool = True,
    check_git_status: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    checks: list[dict[str, Any]] = []
    checks.extend(_executable_checks(root))
    checks.extend(_shell_syntax_checks(root))
    checks.extend(_python_syntax_checks(root))

    runtime_status = _runtime_status(root, run_status_script=run_status_script)
    checks.append(_runtime_status_check(runtime_status, run_status_script=run_status_script))

    cache_preview = _cache_preview(root) if include_cache_preview else {"status": "Skipped"}
    if include_cache_preview:
        checks.append(_cache_preview_check(cache_preview))

    git_status = _git_status(root) if check_git_status else {"status": "Skipped"}
    if check_git_status:
        checks.append(_git_status_check(git_status))

    checks.append(
        _check(
            "GatePolicy",
            "HeavyReleaseGatesExcluded",
            "Pass",
            "Default development check does not invoke release acceptance, CI smoke, full test suite, or strategy smoke gates.",
        )
    )

    summary = _summary(checks)
    return {
        "schema": DEV_READY_CHECK_SCHEMA,
        "system": "PFI",
        "subsystem": "Development Readiness Check",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "Pass" if summary["fail"] == 0 else "Blocked",
        "project_root": str(root),
        "summary": summary,
        "runtime_status": runtime_status,
        "cache_preview": cache_preview,
        "git_status": git_status,
        "checks": checks,
        "default_gate_policy": {
            "runs_heavy_release_gates": False,
            "runs_full_test_suite": False,
            "runs_browser_automation": False,
            "runs_market_refresh": False,
            "runs_broker_or_order_flow": False,
            "dirty_worktree_is_failure": False,
        },
        "safety_boundary": (
            "Lightweight local development gate. It checks syntax, required entry scripts, runtime status, "
            "git status, and cache dry-run only. It does not start services, stop services, delete cache, "
            "refresh market data, open a browser, connect to brokers, create orders, or run release gates."
        ),
        "next_action": "Use this as the default before commit; reserve release acceptance for deliberate macOS product gates.",
    }


def write_dev_ready_check(
    *,
    output_dir: Path | str,
    project_root: Path | str = PROJECT_ROOT,
    run_status_script: bool = True,
    include_cache_preview: bool = True,
    check_git_status: bool = True,
) -> dict[str, Any]:
    payload = build_dev_ready_check(
        project_root=project_root,
        run_status_script=run_status_script,
        include_cache_preview=include_cache_preview,
        check_git_status=check_git_status,
    )
    target = Path(output_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = target / f"DevReadyCheck_{stamp}.json"
    latest_path = target / "DevReadyCheck_latest.json"
    payload["outputs"] = {
        "json": str(json_path),
        "latest_json": str(latest_path),
    }
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_path, payload)
    return payload


def _executable_checks(root: Path) -> list[dict[str, Any]]:
    return [_executable_check(root / relative) for relative in REQUIRED_EXECUTABLES]


def _shell_syntax_checks(root: Path) -> list[dict[str, Any]]:
    zsh = _command_path("zsh")
    if not zsh:
        return [_check("ShellSyntax", "ZshAvailable", "Info", "zsh not found; shell syntax checks skipped")]
    checks = [_check("ShellSyntax", "ZshAvailable", "Pass", zsh)]
    for relative in SHELL_SYNTAX_TARGETS:
        path = root / relative
        if not path.is_file():
            checks.append(_check("ShellSyntax", relative, "Fail", "missing"))
            continue
        completed = subprocess.run([zsh, "-n", str(path)], cwd=root, capture_output=True, text=True, timeout=8, check=False)
        evidence = completed.stderr.strip() or completed.stdout.strip() or "ok"
        checks.append(_check("ShellSyntax", relative, "Pass" if completed.returncode == 0 else "Fail", evidence))
    return checks


def _python_syntax_checks(root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for relative in PYTHON_SYNTAX_TARGETS:
        path = root / relative
        if not path.is_file():
            checks.append(_check("PythonSyntax", relative, "Fail", "missing"))
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            checks.append(_check("PythonSyntax", relative, "Fail", f"{exc.__class__.__name__}: {exc}"))
        except OSError as exc:
            checks.append(_check("PythonSyntax", relative, "Fail", f"{exc.__class__.__name__}: {exc}"))
        else:
            checks.append(_check("PythonSyntax", relative, "Pass", "ast.parse ok"))
    return checks


def _runtime_status(root: Path, *, run_status_script: bool) -> dict[str, Any]:
    script = root / "scripts" / "statusPFI.sh"
    if not run_status_script:
        return {"status": "Skipped", "returncode": None, "stdout": "", "stderr": "skipped by caller"}
    if not script.is_file():
        return {"status": "Missing", "returncode": 127, "stdout": "", "stderr": "status script missing"}
    completed = subprocess.run([str(script)], cwd=root, capture_output=True, text=True, timeout=8, check=False)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    status = "Running" if ("PFI 正在运行" in stdout or "PFIOS running:" in stdout) else "Stopped"
    if completed.returncode != 0:
        status = "Error"
    return {
        "status": status,
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
    }


def _runtime_status_check(payload: dict[str, Any], *, run_status_script: bool) -> dict[str, Any]:
    if not run_status_script:
        return _check("Runtime", "StatusScript", "Info", "skipped by caller")
    ok = payload.get("returncode") == 0
    evidence = payload.get("stdout") or payload.get("stderr") or str(payload.get("status", ""))
    return _check("Runtime", "StatusScript", "Pass" if ok else "Fail", str(evidence))


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


def _cache_preview_check(payload: dict[str, Any]) -> dict[str, Any]:
    ok = payload.get("schema") == "PFICacheCleanupReportV1" and payload.get("failed_count", 0) == 0
    evidence = (
        f"candidates={payload.get('candidate_count', 0)}; "
        f"files={payload.get('candidate_file_count', 0)}; "
        f"dirs={payload.get('candidate_dir_count', 0)}; "
        f"kb={payload.get('candidate_kb', 0)}; "
        f"failed={payload.get('failed_count', 0)}"
    )
    return _check("Cache", "DryRunPreview", "Pass" if ok else "Fail", evidence)


def _git_status(root: Path) -> dict[str, Any]:
    if not (root / ".git").exists():
        return {"status": "NotGitRepo", "returncode": None, "changed_count": 0, "changed_paths": []}
    completed = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True, timeout=8, check=False)
    changed_paths = [line for line in completed.stdout.splitlines() if line.strip()]
    return {
        "status": "Dirty" if changed_paths else "Clean",
        "returncode": completed.returncode,
        "changed_count": len(changed_paths),
        "changed_paths": changed_paths[:50],
        "stderr": completed.stderr.strip(),
    }


def _git_status_check(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("returncode") not in {0, None}:
        return _check("Git", "WorkingTreeStatus", "Info", str(payload.get("stderr", "git status unavailable")))
    if payload.get("status") == "NotGitRepo":
        return _check("Git", "WorkingTreeStatus", "Info", "not a git repo")
    evidence = f"{payload.get('status')}; changed={payload.get('changed_count', 0)}"
    return _check("Git", "WorkingTreeStatus", "Info", evidence)


def _executable_check(path: Path) -> dict[str, Any]:
    ok = path.is_file() and bool(path.stat().st_mode & 0o100)
    return _check("Executable", str(path.name), "Pass" if ok else "Fail", str(path))


def _command_path(name: str) -> str:
    completed = subprocess.run(["/bin/sh", "-lc", f"command -v {name}"], capture_output=True, text=True, timeout=5, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else ""


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
