"""Stage 1 post-migration bootstrap gate for target runners."""

from __future__ import annotations

import os
import platform
import shutil
import socket
import sqlite3
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from .stage1_runtime import (
    STAGE1_RUNTIME_REQUIRED_DISABLED_FLAGS,
    build_runtime_audit,
    run_tick,
    run_watchdog,
    validate_stage1_runtime_report,
)
from .stage1_migration import verify_migration_package
from .storage import inspect_database, migrate_database, validate_storage_report


STAGE1_BOOTSTRAP_MODEL_ID = "adp-stage1-post-migration-bootstrap-v1"
STAGE1_BOOTSTRAP_SCHEMA_VERSION = 1
STAGE1_BOOTSTRAP_ACCEPTANCE_ID = "ADP-ACC-S1-10-POST-MIGRATION-BOOTSTRAP"
STAGE1_BOOTSTRAP_SUPPORTED_TARGET_ENVIRONMENTS = (
    "github_actions_cloud_runner",
    "new_machine",
)
STAGE1_BOOTSTRAP_REQUIRED_SECRET_NAMES = (
    "ADP_SMTP_HOST",
    "ADP_SMTP_PORT",
    "ADP_SMTP_USERNAME",
    "ADP_SMTP_PASSWORD",
    "ADP_SMTP_TO",
)
STAGE1_BOOTSTRAP_GITHUB_ENV_NAMES = (
    "GITHUB_ACTIONS",
    "GITHUB_WORKFLOW",
    "GITHUB_RUN_ID",
    "GITHUB_SHA",
    "RUNNER_OS",
    "RUNNER_ARCH",
    "RUNNER_TEMP",
)
STAGE1_BOOTSTRAP_MIN_PYTHON = (3, 11)
STAGE1_BOOTSTRAP_NETWORK_PROBE_URL = "https://export.arxiv.org/api/query?search_query=all:electron&start=0&max_results=1"
STAGE1_BOOTSTRAP_NETWORK_TIMEOUT_SECONDS = 15
STAGE1_BOOTSTRAP_NETWORK_MAX_ATTEMPTS = 3


def build_stage1_bootstrap_report(
    *,
    project_root: str | Path,
    migration_manifest: str | Path,
    state_dir: str | Path,
    db_path: str | Path,
    generated_at: str,
    target_environment: str = "github_actions_cloud_runner",
    workflow_path: str | Path | None = None,
    require_github_actions: bool = False,
    require_network_probe: bool = False,
    network_timeout_seconds: int = STAGE1_BOOTSTRAP_NETWORK_TIMEOUT_SECONDS,
    network_max_attempts: int = STAGE1_BOOTSTRAP_NETWORK_MAX_ATTEMPTS,
    require_secret_presence: bool = False,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Verify target runtime prerequisites without enabling production."""

    env = dict(os.environ if environment is None else environment)
    root = Path(project_root)
    manifest = Path(migration_manifest)
    state = Path(state_dir)
    db = Path(db_path)
    blocking_reasons: list[str] = []

    if target_environment not in STAGE1_BOOTSTRAP_SUPPORTED_TARGET_ENVIRONMENTS:
        blocking_reasons.append("target_environment is not supported")

    enabled_flags = [key for key in STAGE1_RUNTIME_REQUIRED_DISABLED_FLAGS if _truthy(env.get(key))]
    for key in enabled_flags:
        blocking_reasons.append(f"{key} must not be true during S1-10")

    python_check = _python_check()
    if not python_check["passed"]:
        blocking_reasons.append("python version is below Stage 1 bootstrap minimum")

    git_check = _git_check(root)
    if not git_check["passed"]:
        blocking_reasons.append("git checkout check did not pass")

    ssl_check = _ssl_check()
    if not ssl_check["passed"]:
        blocking_reasons.append("ssl default context check did not pass")

    sqlite_check = _sqlite_check(db)
    if not sqlite_check["passed"]:
        blocking_reasons.append("sqlite bootstrap check did not pass")

    workflow_check = _workflow_check(workflow_path)
    if workflow_path and not workflow_check["passed"]:
        blocking_reasons.append("workflow runner contract check did not pass")

    migration_verify_report = verify_migration_package(manifest_path=manifest, generated_at=generated_at)
    if migration_verify_report.get("status") != "pass":
        blocking_reasons.append("migration package verification did not pass")

    github_env_check = _github_env_check(env)
    cloud_runner_verified = (
        target_environment == "github_actions_cloud_runner"
        and github_env_check["passed"]
        and workflow_check.get("uses_github_hosted_runner") is True
    )
    if require_github_actions and not cloud_runner_verified:
        blocking_reasons.append("GitHub-hosted cloud runner evidence is required")

    network_probe = _network_probe(
        require_network_probe,
        timeout_seconds=network_timeout_seconds,
        max_attempts=network_max_attempts,
    )
    if require_network_probe and not network_probe["passed"]:
        blocking_reasons.append("network probe did not pass")

    secret_name_report = _secret_name_report(env)
    if require_secret_presence:
        missing_secrets = [item["name"] for item in secret_name_report if not item["present"]]
        if missing_secrets:
            blocking_reasons.append("required SMTP secret environment names are not present")

    runtime_reports: list[dict[str, Any]] = []
    if sqlite_check["passed"]:
        state.mkdir(parents=True, exist_ok=True)
        runtime_reports = [
            run_tick(state_dir=state, generated_at=generated_at, write=True),
            run_watchdog(state_dir=state, generated_at=generated_at),
            build_runtime_audit(state_dir=state, db_path=db, generated_at=generated_at, environment=env),
        ]
        for runtime_report in runtime_reports:
            errors = validate_stage1_runtime_report(runtime_report)
            if errors or runtime_report.get("status") != "pass":
                blocking_reasons.append(f"runtime {runtime_report.get('action')} did not pass")

    status = "blocked" if blocking_reasons else "pass"
    return {
        "model_id": STAGE1_BOOTSTRAP_MODEL_ID,
        "schema_version": STAGE1_BOOTSTRAP_SCHEMA_VERSION,
        "acceptance_id": STAGE1_BOOTSTRAP_ACCEPTANCE_ID,
        "action": "post_migration_bootstrap",
        "status": status,
        "bootstrap_ready": status == "pass",
        "generated_at": generated_at,
        "project_root": str(root),
        "migration_manifest": str(manifest),
        "state_dir": str(state),
        "db_path": str(db),
        "target_environment": target_environment,
        "cloud_runner_required": require_github_actions,
        "cloud_runner_verified": cloud_runner_verified,
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_schedule_enabled": False,
        "video_generated": False,
        "large_replay_executed": False,
        "python_check": python_check,
        "git_check": git_check,
        "ssl_check": ssl_check,
        "sqlite_check": sqlite_check,
        "workflow_check": workflow_check,
        "migration_verify_report": migration_verify_report,
        "github_env_check": github_env_check,
        "network_probe": network_probe,
        "required_secret_names": list(STAGE1_BOOTSTRAP_REQUIRED_SECRET_NAMES),
        "secret_name_report": secret_name_report,
        "runtime_reports": runtime_reports,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "next_stage1_gates": [
            "S1-11 target environment bootstrap with real SMTP readiness refs",
            "S1-12 real arXiv preflight through report and email preview",
            "S1-13 30 independent historical B1 report and email previews",
            "S1-14 two real natural days of B1 email delivery",
            "S1-15 ARXIV_PRODUCTION_ACCEPTED final audit",
        ],
    }


def validate_stage1_bootstrap_report(report: Mapping[str, Any]) -> list[str]:
    """Return validation errors for an S1-10 bootstrap report."""

    errors: list[str] = []
    if report.get("model_id") != STAGE1_BOOTSTRAP_MODEL_ID:
        errors.append("bootstrap report model_id is invalid")
    if report.get("schema_version") != STAGE1_BOOTSTRAP_SCHEMA_VERSION:
        errors.append("bootstrap report schema_version must be 1")
    if report.get("acceptance_id") != STAGE1_BOOTSTRAP_ACCEPTANCE_ID:
        errors.append("bootstrap report acceptance_id is invalid")
    if report.get("target_environment") not in STAGE1_BOOTSTRAP_SUPPORTED_TARGET_ENVIRONMENTS:
        errors.append("bootstrap target_environment is invalid")
    for key in (
        "production_side_effects_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_schedule_enabled",
        "video_generated",
        "large_replay_executed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    if bool(report.get("bootstrap_ready")) != (report.get("status") == "pass"):
        errors.append("bootstrap_ready must match pass status")
    if report.get("status") == "pass" and report.get("blocking_reasons"):
        errors.append("passing bootstrap report must not contain blocking_reasons")
    if report.get("status") == "pass" and report.get("cloud_runner_required") and report.get("cloud_runner_verified") is not True:
        errors.append("passing bootstrap report requires cloud_runner_verified when cloud runner is required")
    secret_names = report.get("required_secret_names")
    if list(secret_names or []) != list(STAGE1_BOOTSTRAP_REQUIRED_SECRET_NAMES):
        errors.append("bootstrap required_secret_names must match the Stage 1 text-email secret contract")
    return errors


def _python_check() -> dict[str, Any]:
    version = sys.version_info
    return {
        "passed": (version.major, version.minor) >= STAGE1_BOOTSTRAP_MIN_PYTHON,
        "version": platform.python_version(),
        "minimum": ".".join(str(part) for part in STAGE1_BOOTSTRAP_MIN_PYTHON),
        "executable": sys.executable,
    }


def _git_check(project_root: Path) -> dict[str, Any]:
    git = shutil.which("git")
    if not git:
        return {"passed": False, "git_path": "", "version": "", "inside_work_tree": False}
    version = _run([git, "--version"], cwd=project_root)
    inside = _run([git, "rev-parse", "--is-inside-work-tree"], cwd=project_root)
    return {
        "passed": version["returncode"] == 0 and inside["stdout"].strip() == "true",
        "git_path": git,
        "version": version["stdout"].strip(),
        "inside_work_tree": inside["stdout"].strip() == "true",
    }


def _ssl_check() -> dict[str, Any]:
    try:
        context = ssl.create_default_context()
        ca_count = len(context.get_ca_certs())
    except ssl.SSLError as exc:
        return {"passed": False, "openssl_version": ssl.OPENSSL_VERSION, "ca_cert_count": 0, "error": str(exc)}
    return {
        "passed": True,
        "openssl_version": ssl.OPENSSL_VERSION,
        "ca_cert_count": ca_count,
        "ca_cert_count_warning": ca_count == 0,
    }


def _sqlite_check(db_path: Path) -> dict[str, Any]:
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        migrate_database(db_path)
        storage_report = inspect_database(db_path)
        storage_errors = validate_storage_report(storage_report)
        fts_supported = _sqlite_fts5_supported(db_path)
    except sqlite3.Error as exc:
        return {"passed": False, "sqlite_version": sqlite3.sqlite_version, "storage_status": "error", "error": str(exc)}
    passed = not storage_errors and storage_report.get("status") == "pass" and fts_supported
    return {
        "passed": passed,
        "sqlite_version": sqlite3.sqlite_version,
        "storage_status": storage_report.get("status"),
        "fts5_supported": fts_supported,
        "storage_errors": storage_errors,
        "storage_report": storage_report,
    }


def _workflow_check(workflow_path: str | Path | None) -> dict[str, Any]:
    if not workflow_path:
        return {"passed": True, "workflow_path": "", "uses_github_hosted_runner": False, "self_hosted_forbidden": True}
    path = Path(workflow_path)
    if not path.exists():
        return {"passed": False, "workflow_path": str(path), "uses_github_hosted_runner": False, "self_hosted_forbidden": False}
    text = path.read_text(encoding="utf-8")
    uses_github_hosted = "ubuntu-latest" in text or "macos-latest" in text or "windows-latest" in text
    has_self_hosted = "self-hosted" in text
    return {
        "passed": uses_github_hosted and not has_self_hosted,
        "workflow_path": str(path),
        "uses_github_hosted_runner": uses_github_hosted and not has_self_hosted,
        "self_hosted_forbidden": not has_self_hosted,
    }


def _github_env_check(env: Mapping[str, str]) -> dict[str, Any]:
    present = [name for name in STAGE1_BOOTSTRAP_GITHUB_ENV_NAMES if str(env.get(name) or "").strip()]
    missing = [name for name in STAGE1_BOOTSTRAP_GITHUB_ENV_NAMES if name not in present]
    runner_environment = str(env.get("RUNNER_ENVIRONMENT") or "")
    return {
        "passed": env.get("GITHUB_ACTIONS") == "true" and not missing,
        "required_env_names": list(STAGE1_BOOTSTRAP_GITHUB_ENV_NAMES),
        "present_env_names": present,
        "missing_env_names": missing,
        "runner_os": str(env.get("RUNNER_OS") or ""),
        "runner_arch": str(env.get("RUNNER_ARCH") or ""),
        "runner_environment": runner_environment,
        "runner_environment_is_github_hosted": runner_environment in {"", "github-hosted"},
    }


def _network_probe(required: bool, *, timeout_seconds: int, max_attempts: int) -> dict[str, Any]:
    timeout_seconds = max(1, int(timeout_seconds))
    max_attempts = max(1, int(max_attempts))
    if not required:
        return {
            "required": False,
            "passed": True,
            "url": "",
            "timeout_seconds": timeout_seconds,
            "max_attempts": max_attempts,
            "attempt_count": 0,
            "status_code": None,
            "attempts": [],
        }

    attempts: list[dict[str, Any]] = []
    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            STAGE1_BOOTSTRAP_NETWORK_PROBE_URL,
            headers={"User-Agent": "arxiv-daily-push-stage1-bootstrap/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                status_code = int(getattr(response, "status", 0) or 0)
                response.read(1)
        except Exception as exc:
            attempts.append(
                {
                    "attempt": attempt,
                    "passed": False,
                    "status_code": None,
                    "error": exc.__class__.__name__,
                }
            )
            continue
        passed = 200 <= status_code < 500
        attempts.append(
            {
                "attempt": attempt,
                "passed": passed,
                "status_code": status_code,
                "error": "",
            }
        )
        if passed:
            return {
                "required": True,
                "passed": True,
                "url": STAGE1_BOOTSTRAP_NETWORK_PROBE_URL,
                "timeout_seconds": timeout_seconds,
                "max_attempts": max_attempts,
                "attempt_count": attempt,
                "status_code": status_code,
                "attempts": attempts,
            }

    last_attempt = attempts[-1] if attempts else {"status_code": None, "error": "no_attempt"}
    if last_attempt.get("error"):
        return {
            "required": True,
            "passed": False,
            "url": STAGE1_BOOTSTRAP_NETWORK_PROBE_URL,
            "timeout_seconds": timeout_seconds,
            "max_attempts": max_attempts,
            "attempt_count": len(attempts),
            "status_code": None,
            "error": last_attempt["error"],
            "attempts": attempts,
        }
    return {
        "required": True,
        "passed": False,
        "url": STAGE1_BOOTSTRAP_NETWORK_PROBE_URL,
        "timeout_seconds": timeout_seconds,
        "max_attempts": max_attempts,
        "attempt_count": len(attempts),
        "status_code": last_attempt.get("status_code"),
        "error": "",
        "attempts": attempts,
    }


def _secret_name_report(env: Mapping[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "present": bool(str(env.get(name) or "").strip()),
            "value_recorded": False,
        }
        for name in STAGE1_BOOTSTRAP_REQUIRED_SECRET_NAMES
    ]


def _sqlite_fts5_supported(db_path: Path) -> bool:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS bootstrap_fts_probe USING fts5(content)")
        connection.execute("DROP TABLE bootstrap_fts_probe")
        return True
    finally:
        connection.close()


def _run(command: list[str], *, cwd: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=cwd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return {"returncode": 127, "stdout": "", "stderr": exc.__class__.__name__}
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
